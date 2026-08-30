import ast
import inspect
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

from PySide6.QtCore import QCoreApplication

from app.core.core import _CoreUiSignalBridge, ServiceCoordinator
from app.core.facade.config_facade import ConfigFacade
from app.core.facade.runtime_facade import RuntimeFacade
from app.core.item import RunnerEvents, ViewSignalBus
from app.core.service.schedule_service import ScheduleEntry, ScheduleService


PROJECT_ROOT = Path(__file__).resolve().parents[1]
VIEW_ROOT = PROJECT_ROOT / "app" / "view"
SERVICE_ROOT = PROJECT_ROOT / "app" / "core" / "service"


class Stage5ArchitectureGuardTests(unittest.TestCase):
    def test_services_do_not_import_global_ui_signal_bus(self):
        violations: list[str] = []
        for file_path in SERVICE_ROOT.rglob("*.py"):
            tree = ast.parse(file_path.read_text(encoding="utf-8"), str(file_path))
            for node in ast.walk(tree):
                if (
                    isinstance(node, ast.ImportFrom)
                    and node.module == "app.common.signal_bus"
                ):
                    violations.append(
                        f"{file_path.relative_to(PROJECT_ROOT).as_posix()}:{node.lineno}"
                    )
        self.assertEqual([], violations)

    def test_views_do_not_access_internal_services_or_runners(self):
        forbidden = {
            "config_service",
            "task_service",
            "schedule_service",
            "task_runner",
            "config_repo",
            "run_manager",
            "maafw",
            "_connect",
        }
        violations: list[str] = []
        for file_path in VIEW_ROOT.rglob("*.py"):
            tree = ast.parse(file_path.read_text(encoding="utf-8"), str(file_path))
            relative = file_path.relative_to(PROJECT_ROOT).as_posix()
            for node in ast.walk(tree):
                if isinstance(node, ast.Attribute) and node.attr in forbidden:
                    violations.append(f"{relative}:{node.lineno}: .{node.attr}")
                if isinstance(node, ast.ImportFrom) and node.module:
                    if node.module.startswith(
                        ("app.core.service", "app.core.runner")
                    ):
                        violations.append(
                            f"{relative}:{node.lineno}: {node.module}"
                        )
                    tail = node.module.rsplit(".", 1)[-1]
                    if tail in forbidden:
                        violations.append(f"{relative}:{node.lineno}: {node.module}")
        self.assertEqual([], violations)

    def test_coordinator_transition_properties_are_removed(self):
        tree = ast.parse(inspect.getsource(ServiceCoordinator))
        method_names = {
            node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)
        }
        self.assertTrue(
            {
                "config_service",
                "task_service",
                "schedule_service",
                "task_runner",
            }.isdisjoint(method_names)
        )


class ScheduleBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QCoreApplication.instance() or QCoreApplication([])

    def test_schedule_notifications_are_structured_service_signals(self):
        backend = SimpleNamespace(is_supported=False)
        with patch(
            "app.core.service.schedule_service.get_system_scheduler_backend",
            return_value=backend,
        ):
            service = ScheduleService()
        received: list[tuple[str, str]] = []
        service.notification_requested.connect(
            lambda level, message: received.append((level, message))
        )

        service._log_info("saved")
        service._log_warning("failed")

        self.assertEqual([("info", "saved"), ("warning", "failed")], received)

    def test_schedule_changes_are_copied_to_view_signal_bus(self):
        view_signals = ViewSignalBus()
        bridge = _CoreUiSignalBridge(view_signals)
        received: list[list[ScheduleEntry]] = []
        view_signals.schedules_changed.connect(received.append)
        entry = ScheduleEntry.from_dict(
            {
                "entry_id": "schedule-1",
                "config_id": "config-1",
                "name": "demo",
                "schedule_type": "single",
                "params": {},
                "force_start": False,
                "enabled": True,
                "created_at": "2026-08-13T12:00:00",
            }
        )

        bridge.forward_schedules_changed([entry])

        self.assertEqual("schedule-1", received[0][0].entry_id)
        self.assertIsNot(entry, received[0][0])


class _FakeConfigStore:
    def __init__(self):
        self.loaded = False
        self.bundles = {
            "old": {"name": "old", "path": "./"},
            "valid": {"name": "valid", "path": "./bundle/valid"},
        }

    def load_main_config(self):
        self.loaded = True
        return True

    def list_bundles(self):
        return list(self.bundles)

    def get_bundle(self, name):
        if name not in self.bundles:
            raise FileNotFoundError(name)
        return self.bundles[name]

    def update_bundle(self, name, path, display_name=None):
        self.bundles[name] = {
            "name": display_name or self.bundles.get(name, {}).get("name", name),
            "path": path,
        }
        return True

    def delete_bundle(self, name):
        self.bundles.pop(name, None)
        return True


class ConfigFacadeBundleTests(unittest.TestCase):
    def test_load_and_bundle_path_repair_stay_behind_facade(self):
        original_cwd = Path.cwd()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "bundle" / "valid").mkdir(parents=True)
            (root / "bundle" / "valid" / "interface.json").write_text(
                "{}", encoding="utf-8"
            )
            (root / "bundle" / "new").mkdir(parents=True)
            store = _FakeConfigStore()
            facade = ConfigFacade(
                store,  # type: ignore[arg-type]
                SimpleNamespace(main_config_path=root / "multi_config.json"),  # type: ignore[arg-type]
                lambda directory: (
                    directory / "interface.json"
                    if (directory / "interface.json").is_file()
                    else None
                ),
            )
            try:
                os.chdir(root)
                self.assertTrue(facade.load_main_config())
                results = facade.repair_bundle_paths("new", root / "bundle" / "new")
            finally:
                os.chdir(original_cwd)

        self.assertTrue(store.loaded)
        self.assertEqual({"new": True, "old": True}, results)
        self.assertEqual("./bundle/new", store.bundles["new"]["path"])
        self.assertEqual("./bundle/valid", store.bundles["valid"]["path"])


class _FakeRuntimeRunner:
    def __init__(self):
        self.current_running_task_id = "task-1"
        self.maafw = SimpleNamespace(controller=None)
        self.send_thread = SimpleNamespace(stop=Mock())
        self.submit_resource_run_confirmation = Mock()


def _make_runtime_context(runner):
    return SimpleNamespace(
        config_id="config-a",
        task_runner=runner,
        events=RunnerEvents(),
        logs=SimpleNamespace(clear=Mock()),
        monitor=object(),
        monitor_task=object(),
        is_running=True,
        start=AsyncMock(return_value=True),
        stop=AsyncMock(return_value=True),
        shutdown_runtime_sync=Mock(),
    )


class RuntimeFacadeTests(unittest.IsolatedAsyncioTestCase):
    async def test_runtime_operations_delegate_to_context(self):
        runner = _FakeRuntimeRunner()
        context = _make_runtime_context(runner)
        runtime = RuntimeFacade(lambda: context)

        self.assertEqual("config-a", runtime.config_id)
        self.assertTrue(runtime.is_running)
        self.assertEqual("task-1", runtime.current_running_task_id)
        self.assertTrue(await runtime.run("task-1", start_task_id="task-0"))
        context.start.assert_awaited_once_with(
            "task-1", start_task_id="task-0"
        )

        self.assertTrue(await runtime.stop())
        context.stop.assert_awaited_once_with(manual=True)

        runtime.clear_logs()
        context.logs.clear.assert_called_once_with()
        runtime.submit_resource_run_confirmation(True)
        runner.submit_resource_run_confirmation.assert_called_once_with(True)

        runtime.shutdown_runtime_sync()
        context.shutdown_runtime_sync.assert_called_once_with()
        runtime.stop_notification_thread()
        runner.send_thread.stop.assert_called_once_with(5000)

    def test_context_lookup_and_monitor_are_explicit(self):
        runner = _FakeRuntimeRunner()
        context = _make_runtime_context(runner)
        runtime = RuntimeFacade(lambda: context)

        self.assertIs(context, runtime.get_context())
        self.assertIs(context, runtime.get_context("config-a"))
        with self.assertRaises(ValueError):
            runtime.get_context("config-b")
        self.assertIs(context.monitor_task, runtime.create_monitor_task())


if __name__ == "__main__":
    unittest.main()
