import asyncio
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, call, patch

from PySide6.QtCore import QCoreApplication, QObject, Signal

from app.core.core import ServiceCoordinator
from app.core.item import RunnerEvents
from app.core.runner.runtime_context import RuntimeContext, RuntimeState
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
                    need_stop=False,
                    _manual_stop=False,
                    _is_running=False,
                    maafw=SimpleNamespace(has_active_runtime=lambda: False),
                    runner_events=_kwargs["runner_events"],
                    run_tasks_flow=AsyncMock(),
                    stop_task=AsyncMock(),
                    shutdown_runtime_sync=Mock(),
                    setParent=Mock(),
                )
                runners.append(runner)
                return runner

            def make_monitor(**_kwargs):
                monitor = SimpleNamespace(
                    maafw=_kwargs["maafw"],
                    runner_events=_kwargs["runner_events"],
                    shutdown_runtime_sync=Mock(),
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

    def test_task_and_monitor_share_maafw_and_shutdown_it_once(self):
        context_a, context_b, runners, monitors = self._create_contexts()

        self.assertIs(context_a.task_runner.maafw, context_a.monitor_task.maafw)
        self.assertIs(context_b.task_runner.maafw, context_b.monitor_task.maafw)
        self.assertIsNot(context_a.task_runner.maafw, context_b.task_runner.maafw)

        context_a.shutdown_runtime_sync()

        runners[0].shutdown_runtime_sync.assert_called_once_with()
        monitors[0].shutdown_runtime_sync.assert_not_called()

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


class RuntimeContextLifecycleTests(unittest.IsolatedAsyncioTestCase):
    def _create_context(self, config_id: str, run_side_effect=None):
        maafw = SimpleNamespace(has_active_runtime=lambda: False)
        runner = SimpleNamespace(
            _current_running_task_id=None,
            is_running=False,
            need_stop=False,
            _manual_stop=False,
            _is_running=False,
            maafw=maafw,
            runner_events=None,
            run_tasks_flow=AsyncMock(side_effect=run_side_effect),
            stop_task=AsyncMock(),
            shutdown_runtime_sync=Mock(),
            setParent=Mock(),
        )
        monitor = SimpleNamespace(
            maafw=maafw,
            runner_events=None,
            shutdown_runtime_sync=Mock(),
            setParent=Mock(),
        )
        with (
            patch(
                "app.core.runner.runtime_context.TaskFlowRunner",
                return_value=runner,
            ),
            patch(
                "app.core.runner.runtime_context.MonitorTask",
                return_value=monitor,
            ),
        ):
            context = RuntimeContext(config_id, Mock(), Mock())
        runner.runner_events = context.events
        monitor.runner_events = context.events
        return context, runner, monitor

    async def _finish_context(self, context: RuntimeContext):
        task = context.run_task
        if task is not None:
            await asyncio.wait_for(asyncio.shield(task), timeout=1)

    async def test_two_contexts_can_start_concurrently(self):
        gate_a = asyncio.Event()
        gate_b = asyncio.Event()

        async def run_a(*_args, **_kwargs):
            await gate_a.wait()

        async def run_b(*_args, **_kwargs):
            await gate_b.wait()

        context_a, runner_a, _ = self._create_context("config-a", run_a)
        context_b, runner_b, _ = self._create_context("config-b", run_b)

        self.assertTrue(await context_a.start())
        self.assertTrue(await context_b.start())
        await asyncio.sleep(0)

        self.assertTrue(context_a.is_running)
        self.assertTrue(context_b.is_running)
        runner_a.run_tasks_flow.assert_awaited_once()
        runner_b.run_tasks_flow.assert_awaited_once()

        gate_a.set()
        gate_b.set()
        await asyncio.gather(self._finish_context(context_a), self._finish_context(context_b))

    async def test_duplicate_start_does_not_create_second_task(self):
        gate = asyncio.Event()

        async def run(*_args, **_kwargs):
            await gate.wait()

        context, runner, _ = self._create_context("config-a", run)
        self.assertTrue(await context.start())
        first_task = context.run_task
        self.assertFalse(await context.start())
        self.assertIs(first_task, context.run_task)

        gate.set()
        await self._finish_context(context)
        runner.run_tasks_flow.assert_awaited_once()

    async def test_immediate_starting_stop_keeps_event_loop_responsive(self):
        context, runner, _ = self._create_context("config-a")
        heartbeat = asyncio.Event()
        button_statuses = []
        context.events.start_button_status.connect(button_statuses.append)

        self.assertTrue(await context.start())
        asyncio.get_running_loop().call_soon(heartbeat.set)
        self.assertTrue(await context.stop(manual=True))
        await asyncio.wait_for(heartbeat.wait(), timeout=0.2)
        await self._finish_context(context)

        self.assertTrue(runner.need_stop)
        self.assertTrue(runner._manual_stop)
        runner.stop_task.assert_not_awaited()
        runner.run_tasks_flow.assert_not_awaited()
        self.assertEqual(RuntimeState.IDLE, context.state)
        self.assertEqual(
            {"text": "START", "status": "enabled"}, button_statuses[-1]
        )

    async def test_stop_during_controller_initialization_is_non_blocking(self):
        entered = asyncio.Event()
        release = asyncio.Event()

        async def delayed_start(*_args, **_kwargs):
            entered.set()
            await release.wait()

        context, runner, _ = self._create_context("config-a", delayed_start)
        self.assertTrue(await context.start())
        await asyncio.wait_for(entered.wait(), timeout=0.2)

        await asyncio.wait_for(context.stop(manual=True), timeout=0.2)
        self.assertEqual(RuntimeState.STOPPING, context.state)
        runner.stop_task.assert_not_awaited()

        release.set()
        await self._finish_context(context)
        self.assertEqual(RuntimeState.IDLE, context.state)

    async def test_starting_stop_is_idempotent(self):
        entered = asyncio.Event()
        release = asyncio.Event()

        async def delayed_start(*_args, **_kwargs):
            entered.set()
            await release.wait()

        context, runner, _ = self._create_context("config-a", delayed_start)
        await context.start()
        await entered.wait()

        self.assertTrue(await context.stop(manual=True))
        self.assertTrue(await context.stop(manual=True))
        runner.stop_task.assert_not_awaited()

        release.set()
        await self._finish_context(context)

    async def test_stopping_b_does_not_stop_a(self):
        gate_a = asyncio.Event()
        gate_b = asyncio.Event()

        async def run_a(*_args, **_kwargs):
            await gate_a.wait()

        async def run_b(*_args, **_kwargs):
            await gate_b.wait()

        context_a, runner_a, _ = self._create_context("config-a", run_a)
        context_b, runner_b, _ = self._create_context("config-b", run_b)

        async def stop_b(*, manual=False):
            gate_b.set()

        runner_b.stop_task.side_effect = stop_b
        await context_a.start()
        await context_b.start()
        await asyncio.sleep(0)
        context_a.events.start_button_status.emit({"text": "STOP", "status": "enabled"})
        context_b.events.start_button_status.emit({"text": "STOP", "status": "enabled"})

        self.assertTrue(await context_b.stop(manual=True))
        await self._finish_context(context_b)

        self.assertTrue(context_a.is_running)
        runner_a.stop_task.assert_not_awaited()
        runner_b.stop_task.assert_awaited_once_with(manual=True)

        gate_a.set()
        await self._finish_context(context_a)


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
            start=AsyncMock(return_value=True),
        )
        coordinator = ServiceCoordinator.__new__(ServiceCoordinator)
        coordinator._config_service = SimpleNamespace(
            current_config_id="config-a",
            get_config=lambda config_id: object() if config_id == "config-b" else None,
        )
        coordinator._runtime_contexts = {
            "config-a": SimpleNamespace(is_running=True),
            "config-b": target_context,
        }

        def select_config(config_id):
            coordinator._config_service.current_config_id = config_id
            return True

        coordinator.select_config = Mock(side_effect=select_config)
        coordinator._activate_runtime_context = Mock(return_value=target_context)

        await ServiceCoordinator._run_configuration_from_post_action(
            coordinator, "config-b"
        )

        self.assertEqual("config-b", coordinator._config_service.current_config_id)
        coordinator.select_config.assert_called_once_with("config-b")
        coordinator._activate_runtime_context.assert_not_called()
        target_context.logs.clear.assert_called_once_with()
        target_context.start.assert_awaited_once_with()

    async def test_coordinator_allows_run_while_another_context_is_running(self):
        target_context = SimpleNamespace(
            is_running=False,
            start=AsyncMock(return_value=True),
            logs=SimpleNamespace(clear=Mock()),
        )
        coordinator = ServiceCoordinator.__new__(ServiceCoordinator)
        coordinator._config_service = SimpleNamespace(
            current_config_id="config-a",
            get_config=lambda config_id: object() if config_id == "config-b" else None,
        )
        coordinator._runtime_contexts = {
            "config-a": SimpleNamespace(is_running=True),
            "config-b": target_context,
        }
        coordinator.select_config = Mock()
        coordinator._activate_runtime_context = Mock()

        started = await ServiceCoordinator.run_configuration(coordinator, "config-b")

        self.assertTrue(started)
        target_context.start.assert_awaited_once_with()
        coordinator.select_config.assert_not_called()
        coordinator._activate_runtime_context.assert_not_called()
        self.assertEqual("config-a", coordinator._config_service.current_config_id)

    async def test_stop_targets_only_the_requested_configuration(self):
        stop_a = AsyncMock()
        running_context = SimpleNamespace(
            is_running=True,
            stop=stop_a,
        )
        coordinator = ServiceCoordinator.__new__(ServiceCoordinator)
        coordinator._config_service = SimpleNamespace(current_config_id="config-b")
        coordinator._runtime_contexts = {
            "config-a": running_context,
            "config-b": SimpleNamespace(is_running=False),
        }

        self.assertFalse(
            await ServiceCoordinator.stop_running_configuration(
                coordinator, config_id="config-b", manual=True
            )
        )
        stop_a.assert_not_awaited()

        self.assertTrue(
            await ServiceCoordinator.stop_configuration(
                coordinator, "config-a", manual=True
            )
        )
        stop_a.assert_awaited_once_with(manual=True)

    async def test_stop_all_continues_when_one_context_fails(self):
        stop_a = AsyncMock(side_effect=RuntimeError("a failed"))
        stop_b = AsyncMock(return_value=True)
        coordinator = ServiceCoordinator.__new__(ServiceCoordinator)
        coordinator._runtime_contexts = {
            "config-a": SimpleNamespace(is_running=True, stop=stop_a),
            "config-b": SimpleNamespace(is_running=True, stop=stop_b),
        }

        await ServiceCoordinator.stop_all_configurations(coordinator, manual=False)

        stop_a.assert_awaited_once_with(manual=False)
        stop_b.assert_awaited_once_with(manual=False)

    async def test_graceful_shutdown_waits_for_runtime_tasks(self):
        release = asyncio.Event()

        async def run_until_stopped():
            await release.wait()

        run_task = asyncio.create_task(run_until_stopped())

        async def stop_runtime(*, manual=False):
            self.assertFalse(manual)
            release.set()

        stop = AsyncMock(side_effect=stop_runtime)
        coordinator = ServiceCoordinator.__new__(ServiceCoordinator)
        coordinator._runtime_contexts = {
            "config-a": SimpleNamespace(
                is_running=True,
                stop=stop,
                run_task=run_task,
            )
        }

        pending = await ServiceCoordinator.shutdown_all_configurations(
            coordinator, timeout=0.2
        )

        self.assertEqual([], pending)
        stop.assert_awaited_once_with(manual=False)
        self.assertTrue(run_task.done())

    async def test_graceful_shutdown_reports_runtime_tasks_that_time_out(self):
        release = asyncio.Event()
        run_task = asyncio.create_task(release.wait())
        stop = AsyncMock(return_value=True)
        coordinator = ServiceCoordinator.__new__(ServiceCoordinator)
        coordinator._runtime_contexts = {
            "config-a": SimpleNamespace(
                is_running=True,
                stop=stop,
                run_task=run_task,
            )
        }

        try:
            pending = await ServiceCoordinator.shutdown_all_configurations(
                coordinator, timeout=0.01
            )
        finally:
            run_task.cancel()
            with self.assertRaises(asyncio.CancelledError):
                await run_task

        self.assertEqual(["config-a"], pending)
        stop.assert_awaited_once_with(manual=False)
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


class RuntimeCoordinatorStateTests(unittest.TestCase):
    def test_runtime_state_is_forwarded_with_owning_config_id(self):
        class FakeRuntimeContext(QObject):
            state_changed = Signal(str)

            def __init__(self, config_id, **_kwargs):
                super().__init__()
                self.config_id = config_id
                self.events = RunnerEvents()

        emitted = Mock()
        coordinator = ServiceCoordinator.__new__(ServiceCoordinator)
        coordinator._runtime_contexts = {}
        coordinator._runtime_state_slots = {}
        coordinator._task_service = Mock()
        coordinator._config_service = Mock()
        coordinator._view_signals = SimpleNamespace(
            runtime_state_changed=SimpleNamespace(emit=emitted),
        )

        with patch(
            "app.core.core.RuntimeContext",
            FakeRuntimeContext,
        ):
            context = ServiceCoordinator._get_or_create_runtime_context(
                coordinator,
                "config-a",
            )

        context.state_changed.emit("running")

        emitted.assert_called_once_with("config-a", "running")
        self.assertIn("config-a", coordinator._runtime_state_slots)

    def test_active_config_and_running_config_ids_are_independent(self):
        coordinator = ServiceCoordinator.__new__(ServiceCoordinator)
        coordinator._config_service = SimpleNamespace(current_config_id="config-b")
        coordinator._runtime_contexts = {
            "config-a": SimpleNamespace(is_running=True),
            "config-b": SimpleNamespace(is_running=False),
        }

        self.assertEqual(["config-a"], coordinator.get_running_config_ids())
        self.assertTrue(coordinator.is_configuration_running("config-a"))
        self.assertFalse(coordinator.is_configuration_running("config-b"))
        self.assertEqual("config-b", coordinator._config_service.current_config_id)

    def test_switch_is_allowed_while_another_runtime_is_active(self):
        coordinator = ServiceCoordinator.__new__(ServiceCoordinator)
        coordinator._config_service = SimpleNamespace(
            current_config_id="config-a",
            get_config=lambda config_id: (
                object() if config_id in {"config-a", "config-b"} else None
            ),
        )
        coordinator._runtime_contexts = {
            "config-a": SimpleNamespace(is_running=True),
        }

        switched = ServiceCoordinator.select_config(coordinator, "config-b")

        self.assertTrue(switched)
        self.assertEqual("config-b", coordinator._config_service.current_config_id)

    def test_selecting_current_config_is_allowed_while_running(self):
        coordinator = ServiceCoordinator.__new__(ServiceCoordinator)
        coordinator._config_service = SimpleNamespace(
            current_config_id="config-a",
            get_config=lambda config_id: object() if config_id == "config-a" else None,
        )
        coordinator._runtime_contexts = {
            "config-a": SimpleNamespace(is_running=True),
        }

        switched = ServiceCoordinator.select_config(coordinator, "config-a")

        self.assertTrue(switched)
        self.assertEqual("config-a", coordinator._config_service.current_config_id)

    def test_switching_active_context_replays_target_button_state_only(self):
        context_a = SimpleNamespace(
            config_id="config-a",
            button_status={"text": "STOP", "status": "enabled"},
        )
        context_b = SimpleNamespace(
            config_id="config-b",
            button_status={"text": "START", "status": "enabled"},
        )
        coordinator = ServiceCoordinator.__new__(ServiceCoordinator)
        coordinator._runtime_contexts = {
            "config-a": context_a,
            "config-b": context_b,
        }
        coordinator._active_runtime_context = context_a
        coordinator._runner_ui_bridge = SimpleNamespace(
            forward_start_button_status=Mock()
        )
        coordinator._disconnect_runtime_context = Mock()
        coordinator._connect_runtime_context = Mock()

        ServiceCoordinator._activate_runtime_context(coordinator, "config-b")
        ServiceCoordinator._activate_runtime_context(coordinator, "config-a")

        self.assertIs(context_a, coordinator._active_runtime_context)
        self.assertEqual(
            [call(context_a), call(context_b)],
            coordinator._disconnect_runtime_context.call_args_list,
        )
        self.assertEqual(
            [call(context_b), call(context_a)],
            coordinator._connect_runtime_context.call_args_list,
        )
        self.assertEqual(
            [
                call({"text": "START", "status": "enabled"}),
                call({"text": "STOP", "status": "enabled"}),
            ],
            coordinator._runner_ui_bridge.forward_start_button_status.call_args_list,
        )

    def test_sync_shutdown_continues_after_one_runtime_fails(self):
        shutdown_a = Mock(side_effect=RuntimeError("a failed"))
        shutdown_b = Mock()
        coordinator = ServiceCoordinator.__new__(ServiceCoordinator)
        coordinator._runtime_contexts = {
            "config-a": SimpleNamespace(shutdown_runtime_sync=shutdown_a),
            "config-b": SimpleNamespace(shutdown_runtime_sync=shutdown_b),
        }

        ServiceCoordinator.shutdown_all_runtimes_sync(coordinator)

        shutdown_a.assert_called_once_with()
        shutdown_b.assert_called_once_with()

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
        coordinator.telemetry_service = SimpleNamespace(
            remove_runner_events=Mock()
        )
        removed_context.events = RunnerEvents()

        deleted = ServiceCoordinator.delete_config(coordinator, "config-b")

        self.assertTrue(deleted)
        self.assertNotIn("config-b", coordinator._runtime_contexts)
        removed_context.deleteLater.assert_called_once_with()
        coordinator.telemetry_service.remove_runner_events.assert_called_once_with(
            removed_context.events
        )
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
