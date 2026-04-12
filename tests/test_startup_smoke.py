import os
import tempfile
import unittest
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_OPENGL", "software")

from PySide6.QtWidgets import QApplication, QWidget


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SMOKE_INTERFACE_PATH = (
    PROJECT_ROOT / "tests" / "fixtures" / "smoke_bundle" / "interface.json"
)


def _make_dummy_interface_class(object_name: str):
    class _DummyInterface(QWidget):
        def __init__(self, *args, **kwargs):
            super().__init__()
            self.setObjectName(object_name)

        def run_multi_resource_post_enable_tasks(self):
            return None

    return _DummyInterface


class _DummyHotkeyManager:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def setup(self, *args, **kwargs):
        return None


class StartupSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self._temp_dir = tempfile.TemporaryDirectory()
        self.temp_root = Path(self._temp_dir.name)
        (self.temp_root / "config").mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        for widget in QApplication.topLevelWidgets():
            widget.close()
        QApplication.processEvents()
        self._temp_dir.cleanup()

    def test_main_window_opens_with_minimal_interface(self):
        from app.core.core import ServiceCoordinator
        from app.view.main_window import main_window as main_window_module

        def build_service_coordinator(*args, **kwargs):
            coordinator = ServiceCoordinator(
                self.temp_root / "config" / "multi_config.json",
                interface_path=SMOKE_INTERFACE_PATH,
            )
            coordinator.schedule_service.start = lambda: None
            return coordinator

        patchers = [
            patch.object(
                main_window_module,
                "DashboardInterface",
                _make_dummy_interface_class("DashboardInterface"),
            ),
            patch.object(
                main_window_module,
                "TaskInterface",
                _make_dummy_interface_class("TaskInterface"),
            ),
            patch.object(
                main_window_module,
                "MonitorInterface",
                _make_dummy_interface_class("MonitorInterface"),
            ),
            patch.object(
                main_window_module,
                "ScheduleInterface",
                _make_dummy_interface_class("ScheduleInterface"),
            ),
            patch.object(
                main_window_module,
                "SettingInterface",
                _make_dummy_interface_class("SettingInterface"),
            ),
            patch.object(
                main_window_module,
                "BundleInterface",
                _make_dummy_interface_class("BundleInterface"),
            ),
            patch.object(main_window_module, "GlobalHotkeyManager", _DummyHotkeyManager),
            patch.object(main_window_module, "ServiceCoordinator", build_service_coordinator),
            patch.object(main_window_module.CustomSystemThemeListener, "start", lambda self: None),
            patch.object(main_window_module.MainWindow, "_init_announcement", lambda self: None),
            patch.object(
                main_window_module.MainWindow,
                "_maybe_show_pending_announcement",
                lambda self: None,
            ),
            patch.object(
                main_window_module.MainWindow,
                "_insert_announcement_nav_item",
                lambda self: None,
            ),
            patch.object(main_window_module.MainWindow, "_apply_v5_shell_style", lambda self: None),
            patch.object(main_window_module.MainWindow, "connectSignalToSlot", lambda self: None),
            patch.object(
                main_window_module.MainWindow,
                "_check_hotkey_permission",
                lambda self: None,
            ),
            patch.object(main_window_module.MainWindow, "_reload_global_hotkeys", lambda self: None),
            patch.object(
                main_window_module.MainWindow,
                "_bootstrap_auto_update_and_run",
                lambda self: None,
            ),
            patch.object(
                main_window_module.MainWindow,
                "_apply_auto_minimize_on_startup",
                lambda self: None,
            ),
            patch.object(
                main_window_module.MainWindow,
                "_schedule_startup_cleanup_old_debug_files",
                lambda self: None,
            ),
        ]

        with ExitStack() as stack:
            for patcher in patchers:
                stack.enter_context(patcher)

            window = main_window_module.MainWindow()
            window.show()
            QApplication.processEvents()
            QApplication.processEvents()

            self.assertTrue(window.isVisible())
            self.assertEqual("Smoke Bundle", window.service_coordinator.interface.get("name"))

            window.close()
            QApplication.processEvents()


if __name__ == "__main__":
    unittest.main()