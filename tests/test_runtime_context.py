import asyncio
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

from PySide6.QtCore import QCoreApplication

from app.core.core import ServiceCoordinator
from app.core.item import RunnerEvents
from app.core.runner.runtime_context import RuntimeContext
from app.core.runner.task_flow import TaskFlowRunner
from app.core.service.telemetry_service import TelemetryService


class RuntimeContextIsolationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QCoreApplication.instance() or QCoreApplication([])

    def _create_contexts(self):
        with (
            patch("app.core.runner.runtime_context.TaskFlowRunner") as runner_cls,
            patch("app.core.runner.runtime_context.MonitorTask") as monitor_cls,
        ):
            runners = []
            monitors = []

            def make_runner(**_kwargs):
                runner = SimpleNamespace(
                    _current_running_task_id=None,
                    is_running=False,
                    maafw=SimpleNamespace(has_active_runtime=lambda: False),
                    runner_events=_kwargs["runner_events"],
                    setParent=Mock(),
                )
                runners.append(runner)
                return runner

            def make_monitor(**_kwargs):
                monitor = SimpleNamespace(
                    runner_events=_kwargs["runner_events"],
                    setParent=Mock(),
                )
                monitors.append(monitor)
                return monitor

            runner_cls.side_effect = make_runner
            monitor_cls.side_effect = make_monitor
            context_a = RuntimeContext("config-a", Mock(), Mock())
            context_b = RuntimeContext("config-b", Mock(), Mock())

        return context_a, context_b, runners, monitors

    def test_runtime_objects_are_owned_per_configuration(self):
        context_a, context_b, runners, monitors = self._create_contexts()

        self.assertIsNot(context_a.events, context_b.events)
        self.assertIsNot(context_a.task_runner, context_b.task_runner)
        self.assertIsNot(context_a.monitor_task, context_b.monitor_task)
        self.assertIsNot(context_a.logs, context_b.logs)
        self.assertIsNot(context_a.monitor, context_b.monitor)
        self.assertIs(context_a.task_runner, runners[0])
        self.assertIs(context_b.task_runner, runners[1])
        self.assertIs(context_a.monitor_task, monitors[0])
        self.assertIs(context_b.monitor_task, monitors[1])
        self.assertIs(context_a.events, context_a.task_runner.runner_events)
        self.assertIs(context_a.events, context_a.monitor_task.runner_events)
        self.assertIs(context_b.events, context_b.task_runner.runner_events)
        self.assertIs(context_b.events, context_b.monitor_task.runner_events)

    def test_shutdown_cleans_task_and_monitor_runtimes(self):
        context_a, _, runners, monitors = self._create_contexts()
        runners[0].shutdown_runtime_sync = Mock(side_effect=RuntimeError("main failed"))
        monitors[0].shutdown_runtime_sync = Mock()

        with self.assertRaisesRegex(RuntimeError, "main failed"):
            context_a.shutdown_runtime_sync()

        runners[0].shutdown_runtime_sync.assert_called_once_with()
        monitors[0].shutdown_runtime_sync.assert_called_once_with()

    def test_logs_and_clear_requests_do_not_cross_contexts(self):
        context_a, context_b, _, _ = self._create_contexts()
        context_a.task_runner._current_running_task_id = "task-a"
        context_b.task_runner._current_running_task_id = "task-b"

        context_a.events.log_output.emit("INFO", "from a")
        context_b.events.log_output.emit("WARNING", "from b")

        self.assertEqual(["from a"], [entry.text for entry in context_a.logs.entries])
        self.assertEqual("task-a", context_a.logs.entries[0].task_id)
        self.assertEqual(["from b"], [entry.text for entry in context_b.logs.entries])
        self.assertEqual("task-b", context_b.logs.entries[0].task_id)

        context_a.events.log_clear_requested.emit()

        self.assertEqual((), context_a.logs.entries)
        self.assertEqual(["from b"], [entry.text for entry in context_b.logs.entries])

    def test_monitor_frame_and_roi_do_not_cross_contexts(self):
        context_a, context_b, _, _ = self._create_contexts()
        frame_a = {"frame": "a"}
        roi_a = {"x": 1, "y": 2, "width": 3, "height": 4}
        roi_b = {"x": 10, "y": 20, "width": 30, "height": 40}

        context_a.monitor.update_frame(frame_a)
        context_a.events.monitor_recognition_roi.emit(roi_a)
        context_b.events.monitor_recognition_roi.emit(roi_b)

        self.assertEqual(frame_a, context_a.monitor.latest_frame)
        self.assertIsNone(context_b.monitor.latest_frame)
        self.assertEqual(roi_a, context_a.monitor.latest_roi)
        self.assertEqual(roi_b, context_b.monitor.latest_roi)

        context_a.events.task_flow_finished.emit({"status": "completed"})

        self.assertIsNone(context_a.monitor.latest_roi)
        self.assertEqual(roi_b, context_b.monitor.latest_roi)


class PostActionRuntimeRoutingTests(unittest.IsolatedAsyncioTestCase):
    async def test_runner_delegates_next_configuration_to_callback(self):
        routed = []
        runner = SimpleNamespace(
            _run_config_callback=lambda config_id: routed.append(config_id),
        )

        TaskFlowRunner._schedule_configuration_run(runner, "config-b")

        self.assertEqual(["config-b"], routed)

    async def test_coordinator_runs_and_clears_target_context(self):
        target_context = SimpleNamespace(
            is_running=False,
            logs=SimpleNamespace(clear=Mock()),
        )
        coordinator = ServiceCoordinator.__new__(ServiceCoordinator)
        coordinator._config_service = SimpleNamespace(
            current_config_id="config-a",
            get_config=lambda config_id: object() if config_id == "config-b" else None,
        )
        coordinator._runtime_contexts = {"config-b": target_context}
        coordinator.select_config = Mock(
            side_effect=lambda config_id: setattr(
                coordinator._config_service, "current_config_id", config_id
            )
            or True
        )
        coordinator._activate_runtime_context = Mock(return_value=target_context)

        with patch("app.core.core.RuntimeFacade") as facade_cls:
            facade_cls.return_value.run = AsyncMock()
            await ServiceCoordinator._run_configuration_from_post_action(
                coordinator, "config-b"
            )

        self.assertEqual("config-b", coordinator._config_service.current_config_id)
        coordinator._activate_runtime_context.assert_called_once_with("config-b")
        target_context.logs.clear.assert_called_once_with()
        facade_cls.return_value.run.assert_awaited_once_with()
        context_provider = facade_cls.call_args.args[0]
        self.assertIs(target_context, context_provider())

    async def test_coordinator_rejects_run_while_another_context_is_running(self):
        coordinator = ServiceCoordinator.__new__(ServiceCoordinator)
        coordinator._config_service = SimpleNamespace(
            current_config_id="config-a",
            get_config=lambda config_id: object() if config_id == "config-b" else None,
        )
        coordinator._runtime_contexts = {
            "config-a": SimpleNamespace(is_running=True),
            "config-b": SimpleNamespace(is_running=False),
        }
        coordinator.select_config = Mock()
        coordinator._activate_runtime_context = Mock()

        started = await ServiceCoordinator.run_configuration(coordinator, "config-b")

        self.assertFalse(started)
        coordinator.select_config.assert_not_called()
        coordinator._activate_runtime_context.assert_not_called()

    async def test_stop_targets_the_only_running_context_without_switching(self):
        stop_task = AsyncMock()
        running_context = SimpleNamespace(
            is_running=True,
            task_runner=SimpleNamespace(stop_task=stop_task),
        )
        coordinator = ServiceCoordinator.__new__(ServiceCoordinator)
        coordinator._runtime_contexts = {
            "config-a": running_context,
            "config-b": SimpleNamespace(is_running=False),
        }

        stopped = await ServiceCoordinator.stop_running_configuration(
            coordinator,
            config_id="config-b",
            manual=True,
        )

        self.assertTrue(stopped)
        stop_task.assert_awaited_once_with(manual=True)

    async def test_explicit_configuration_run_rejects_missing_target(self):
        coordinator = ServiceCoordinator.__new__(ServiceCoordinator)
        coordinator._config_service = SimpleNamespace(
            current_config_id="config-a",
            get_config=lambda _config_id: None,
        )
        coordinator.select_config = Mock()
        coordinator._activate_runtime_context = Mock()
        coordinator._runtime = SimpleNamespace(run=AsyncMock())

        started = await ServiceCoordinator.run_configuration(
            coordinator, "missing-config"
        )

        self.assertFalse(started)
        coordinator.select_config.assert_not_called()
        coordinator._activate_runtime_context.assert_not_called()
        coordinator._runtime.run.assert_not_awaited()


class RuntimeContextRegistryTests(unittest.TestCase):
    def test_deleting_inactive_configuration_releases_its_context(self):
        active_context = SimpleNamespace(is_running=False)
        removed_context = SimpleNamespace(
            is_running=False,
            deleteLater=Mock(),
        )
        config_removed = Mock()
        coordinator = ServiceCoordinator.__new__(ServiceCoordinator)
        coordinator._runtime_contexts = {
            "config-a": active_context,
            "config-b": removed_context,
        }
        coordinator._active_runtime_context = active_context
        coordinator._config_service = SimpleNamespace(
            delete_config=Mock(return_value=True),
        )
        coordinator._view_signals = SimpleNamespace(
            config_removed=SimpleNamespace(emit=config_removed),
        )

        deleted = ServiceCoordinator.delete_config(coordinator, "config-b")

        self.assertTrue(deleted)
        self.assertNotIn("config-b", coordinator._runtime_contexts)
        removed_context.deleteLater.assert_called_once_with()
        config_removed.assert_called_once_with("config-b")

    def test_running_configuration_cannot_be_deleted(self):
        running_context = SimpleNamespace(is_running=True)
        coordinator = ServiceCoordinator.__new__(ServiceCoordinator)
        coordinator._runtime_contexts = {"config-a": running_context}
        coordinator._config_service = SimpleNamespace(
            delete_config=Mock(return_value=True),
        )

        deleted = ServiceCoordinator.delete_config(coordinator, "config-a")

        self.assertFalse(deleted)
        coordinator._config_service.delete_config.assert_not_called()


class TelemetryRuntimeBindingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QCoreApplication.instance() or QCoreApplication([])

    def test_switching_events_disconnects_previous_context(self):
        events_a = RunnerEvents()
        events_b = RunnerEvents()
        service = TelemetryService(events_a, {}, debug_override=False)

        events_a.telemetry.emit(
            {"event": "configure", "interface": {"name": "context-a"}}
        )
        self.assertEqual("context-a", service._interface.get("name"))

        service.set_runner_events(events_b)
        events_a.telemetry.emit(
            {"event": "configure", "interface": {"name": "stale-a"}}
        )
        self.assertEqual("context-a", service._interface.get("name"))

        events_b.telemetry.emit(
            {"event": "configure", "interface": {"name": "context-b"}}
        )
        self.assertEqual("context-b", service._interface.get("name"))


if __name__ == "__main__":
    unittest.main()
