import asyncio
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

from PySide6.QtCore import QCoreApplication

from app.core.runner.runtime_context import (
    RuntimeLogStore,
    RuntimeMonitorState,
    RuntimeState,
)
from app.view.monitor_interface.monitor_interface import MonitorInterface
from app.view.task_interface.components.logoutput_widget import LogoutputWidget


class RuntimeUiReplayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QCoreApplication.instance() or QCoreApplication([])

    def test_log_binding_disconnects_old_store_and_replays_new_history(self):
        store_a = RuntimeLogStore()
        store_b = RuntimeLogStore()
        store_a.append("INFO", "from-a")
        store_b.append("WARNING", "from-b")
        active = {"store": store_a}
        rendered = []
        widget = SimpleNamespace(
            service_coordinator=SimpleNamespace(
                runtime=SimpleNamespace(logs=store_a),
            ),
            _bound_log_store=None,
            _max_log_entries=50,
            _on_runtime_log_entry=Mock(),
            _clear_log_widgets=Mock(side_effect=lambda: rendered.clear()),
            _render_runtime_log_entry=Mock(
                side_effect=lambda entry, capture_image=False: rendered.append(entry.text)
            ),
        )
        widget._reload_runtime_logs = lambda: LogoutputWidget._reload_runtime_logs(widget)

        LogoutputWidget._bind_runtime_log_store(widget)
        self.assertEqual(["from-a"], rendered)

        widget.service_coordinator.runtime.logs = store_b
        LogoutputWidget._bind_runtime_log_store(widget)
        self.assertEqual(["from-b"], rendered)

        store_a.append("INFO", "stale-a")
        widget._on_runtime_log_entry.assert_not_called()
        store_b.append("INFO", "live-b")
        widget._on_runtime_log_entry.assert_called_once()
        self.assertEqual("live-b", widget._on_runtime_log_entry.call_args.args[0].text)

    def test_monitor_binding_disconnects_old_state_and_restores_new_state(self):
        state_a = RuntimeMonitorState()
        state_b = RuntimeMonitorState()
        state_a.update_roi({"x": 1})
        state_b.update_roi({"x": 2})
        state_b.update_frame("frame-b")
        applied_rois = []
        applied_frames = []
        monitor = SimpleNamespace(
            service_coordinator=SimpleNamespace(
                runtime=SimpleNamespace(monitor=state_b),
            ),
            _runtime_monitor_state=state_a,
            _on_recognition_roi=Mock(side_effect=lambda roi: applied_rois.append(roi)),
            _create_monitor_session=Mock(),
            _clear_preview_widgets=Mock(),
            _roi_store=SimpleNamespace(update=Mock(side_effect=lambda roi: applied_rois.append(roi))),
            _apply_preview_from_pil=Mock(
                side_effect=lambda frame, persist=False: applied_frames.append(frame)
            ),
        )
        monitor._restore_runtime_monitor_state = lambda: MonitorInterface._restore_runtime_monitor_state(monitor)
        state_a.roi_changed.connect(monitor._on_recognition_roi)

        MonitorInterface._bind_runtime_context(monitor)

        self.assertIs(state_b, monitor._runtime_monitor_state)
        self.assertEqual([{"x": 2}], applied_rois)
        self.assertEqual(["frame-b"], applied_frames)

        state_a.update_roi({"x": 3})
        monitor._on_recognition_roi.assert_not_called()
        state_b.update_roi({"x": 4})
        monitor._on_recognition_roi.assert_called_once_with({"x": 4})

    def test_switching_away_from_running_config_detaches_preview_only(self):
        old_session = SimpleNamespace(
            stop_loop=Mock(),
            monitor_task=SimpleNamespace(config_id="config-a"),
        )
        monitor = SimpleNamespace(
            _session=old_session,
            service_coordinator=SimpleNamespace(
                get_runtime_state=Mock(return_value=RuntimeState.RUNNING),
            ),
            _schedule_session_detach=Mock(),
            _schedule_session_teardown=Mock(),
            _starting_monitoring=True,
            _stopping_monitoring=True,
            _set_monitor_control_running=Mock(),
            _bind_runtime_context=Mock(),
            _resume_monitoring_for_active_runtime=Mock(),
        )

        MonitorInterface._on_runtime_config_changed(monitor, "config-b")

        old_session.stop_loop.assert_called_once_with()
        monitor._schedule_session_detach.assert_called_once_with(old_session)
        monitor._schedule_session_teardown.assert_not_called()
        monitor._bind_runtime_context.assert_called_once_with()
        monitor._resume_monitoring_for_active_runtime.assert_called_once_with(
            "config-b"
        )

    def test_switching_away_from_idle_config_releases_monitor_controller(self):
        old_session = SimpleNamespace(
            stop_loop=Mock(),
            monitor_task=SimpleNamespace(config_id="config-a"),
        )
        monitor = SimpleNamespace(
            _session=old_session,
            service_coordinator=SimpleNamespace(
                get_runtime_state=Mock(return_value=RuntimeState.IDLE),
            ),
            _schedule_session_detach=Mock(),
            _schedule_session_teardown=Mock(),
            _starting_monitoring=False,
            _stopping_monitoring=False,
            _set_monitor_control_running=Mock(),
            _bind_runtime_context=Mock(),
            _resume_monitoring_for_active_runtime=Mock(),
        )

        MonitorInterface._on_runtime_config_changed(monitor, "config-b")

        old_session.stop_loop.assert_called_once_with()
        monitor._schedule_session_detach.assert_not_called()
        monitor._schedule_session_teardown.assert_called_once_with(old_session)
        monitor._bind_runtime_context.assert_called_once_with()
        monitor._resume_monitoring_for_active_runtime.assert_called_once_with(
            "config-b"
        )


class RuntimeUiMonitorResumeTests(unittest.TestCase):
    def test_running_target_with_connected_controller_resumes_preview(self):
        session = SimpleNamespace(
            monitoring_active=False,
            is_controller_connected=Mock(return_value=True),
            start_loop=Mock(),
        )
        monitor = SimpleNamespace(
            service_coordinator=SimpleNamespace(
                get_runtime_state=Mock(return_value=RuntimeState.RUNNING),
            ),
            _session=session,
            _starting_monitoring=False,
            _set_monitor_control_running=Mock(),
        )

        MonitorInterface._resume_monitoring_for_active_runtime(
            monitor,
            "config-b",
        )

        session.start_loop.assert_called_once_with()
        monitor._set_monitor_control_running.assert_called_once_with(True)

    def test_disconnected_target_does_not_attempt_monitor_reconnect(self):
        session = SimpleNamespace(
            monitoring_active=False,
            is_controller_connected=Mock(return_value=False),
            start_loop=Mock(),
        )
        monitor = SimpleNamespace(
            service_coordinator=SimpleNamespace(
                get_runtime_state=Mock(return_value=RuntimeState.RUNNING),
            ),
            _session=session,
            _starting_monitoring=False,
            _set_monitor_control_running=Mock(),
        )

        MonitorInterface._resume_monitoring_for_active_runtime(
            monitor,
            "config-b",
        )

        session.start_loop.assert_not_called()
        monitor._set_monitor_control_running.assert_not_called()


class RuntimeUiDetachTests(unittest.IsolatedAsyncioTestCase):
    async def test_detach_finishes_preview_processing_without_stopping_session(self):
        session = SimpleNamespace(
            wait_for_image_processing_complete=AsyncMock(),
            stop=AsyncMock(),
        )

        MonitorInterface._schedule_session_detach(session)
        await asyncio.sleep(0)

        session.wait_for_image_processing_complete.assert_awaited_once_with(
            timeout=1.0
        )
        session.stop.assert_not_awaited()


if __name__ == "__main__":
    unittest.main()
