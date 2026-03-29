from PySide6.QtCore import QObject, Signal


class CoreSignalBus(QObject):
    """核心信号总线，用于组件间通信。"""

    config_changed = Signal(str)
    config_loaded = Signal(object)
    config_saved = Signal(bool)

    tasks_loaded = Signal(object)
    task_updated = Signal(object)
    task_selected = Signal(str)
    task_order_updated = Signal(object)

    options_loaded = Signal()
    option_updated = Signal(object)

    need_save = Signal()


class FromServiceCoordinator(QObject):
    """服务协调器发往 View 层的单向通知总线。"""

    fs_task_modified = Signal(object)
    fs_task_removed = Signal(str)
    fs_config_added = Signal(object)
    fs_config_removed = Signal(str)
    fs_config_changed = Signal(str)
    fs_start_button_status = Signal(dict)
    fs_log_clear_requested = Signal()
    fs_info_bar_requested = Signal(str, str)
    fs_callback = Signal(dict)
    fs_log_output = Signal(str, str)
    fs_focus_toast = Signal(str)
    fs_focus_notification = Signal(str)
    fs_focus_dialog = Signal(str)
    fs_focus_modal = Signal(str)
    fs_task_status_changed = Signal(str, str)
    fs_task_flow_finished = Signal(dict)
    fs_set_window_title = Signal(str)


__all__ = ["CoreSignalBus", "FromServiceCoordinator"]