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
                    setParent=Mock(),
                )
                runners.append(runner)
                return runner

            def make_monitor(**_kwargs):
                monitor = SimpleNamespace(setParent=Mock())
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
        target_runner = SimpleNamespace(run_tasks_flow=AsyncMock())
        target_context = SimpleNamespace(
            logs=SimpleNamespace(clear=Mock()),
            task_runner=target_runner,
        )
        coordinator = ServiceCoordinator.__new__(ServiceCoordinator)
        coordinator._config_service = SimpleNamespace(
            current_config_id="config-a",
            get_config=lambda config_id: object() if config_id == "config-b" else None,
        )
        coordinator._activate_runtime_context = Mock(return_value=target_context)

        await ServiceCoordinator._run_configuration_from_post_action(
            coordinator, "config-b"
        )

        self.assertEqual("config-b", coordinator._config_service.current_config_id)
        coordinator._activate_runtime_context.assert_called_once_with("config-b")
        target_context.logs.clear.assert_called_once_with()
        target_runner.run_tasks_flow.assert_awaited_once_with()


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
