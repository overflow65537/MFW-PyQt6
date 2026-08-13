import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from PySide6.QtCore import QCoreApplication

from app.core.runner.runtime_context import RuntimeLogStore, RuntimeMonitorState
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


if __name__ == "__main__":
    unittest.main()
