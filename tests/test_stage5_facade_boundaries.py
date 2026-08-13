import ast
import asyncio
import inspect
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

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


class _FakeTaskApi:
    def __init__(self):
        self.task = SimpleNamespace(is_checked=False)
        self.checked_calls: list[tuple[str, bool]] = []
        self.refresh_calls = 0

    def get_task(self, task_id):
        return self.task if task_id == "task-1" else None

    def update_task_checked(self, task_id, checked):
        self.checked_calls.append((task_id, checked))
        self.task.is_checked = checked
        return True

    def refresh_hidden_flags(self):
        self.refresh_calls += 1


class _FakeRuntimeRunner:
    def __init__(self):
        self.is_running = False
        self.maafw = SimpleNamespace(has_active_runtime=lambda: True)
        self.task_service = _FakeTaskApi()
        self.config_service = object()
        self.run_calls: list[tuple[str | None, str | None]] = []
        self.stop_calls: list[bool] = []
        self.shutdown_calls = 0
        self.send_thread = SimpleNamespace(stop_calls=0)
        self.send_thread.stop = lambda: setattr(
            self.send_thread,
            "stop_calls",
            self.send_thread.stop_calls + 1,
        )

    async def run_tasks_flow(self, task_id=None, *, start_task_id=None):
        self.run_calls.append((task_id, start_task_id))
        await asyncio.sleep(0)
        return "done"

    async def stop_task(self, *, manual=False):
        self.stop_calls.append(manual)
        return "stopped"

    def shutdown_runtime_sync(self):
        self.shutdown_calls += 1


class RuntimeFacadeTests(unittest.IsolatedAsyncioTestCase):
    async def test_runtime_operations_hide_runner_internals(self):
        runner = _FakeRuntimeRunner()
        runtime = RuntimeFacade(runner)  # type: ignore[arg-type]

        self.assertTrue(runtime.is_running)
        self.assertEqual(
            "done",
            await runtime.run("task-1", start_task_id="task-0"),
        )
        self.assertEqual(
            [("task-1", True), ("task-1", False)],
            runner.task_service.checked_calls,
        )
        self.assertEqual("stopped", await runtime.stop())
        self.assertEqual([True], runner.stop_calls)

        runtime.shutdown_runtime_sync()
        runtime.stop_notification_thread()
        self.assertEqual(1, runner.shutdown_calls)
        self.assertEqual(1, runner.send_thread.stop_calls)

    def test_monitor_factory_uses_independent_runner_events(self):
        runner = _FakeRuntimeRunner()
        runtime = RuntimeFacade(runner)  # type: ignore[arg-type]
        captured: dict[str, object] = {}

        class _Monitor:
            def __init__(self, **kwargs):
                captured.update(kwargs)

        with patch("app.core.facade.runtime_facade.MonitorTask", _Monitor):
            monitor = runtime.create_monitor_task()

        self.assertIsInstance(captured["runner_events"], RunnerEvents)
        self.assertIsNot(captured["runner_events"], getattr(runner, "runner_events", None))
        self.assertIsNotNone(monitor)


if __name__ == "__main__":
    unittest.main()
