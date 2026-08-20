import re

from PySide6.QtCore import QRunnable, QThreadPool, QTimer, Signal, QObject
from PySide6.QtWidgets import QWidget, QHBoxLayout

from qfluentwidgets import ComboBox, ToolButton
from qfluentwidgets import FluentIcon as FIF

from maa.toolkit import Toolkit

from app.utils.logger import logger
from app.utils.controller_utils import (
    ControllerHelper,
    should_search_desktop_windows_on_ui_thread,
)


def collect_controller_devices(controller_type: str) -> dict:
    """按控制器类型收集设备映射，供搜索下拉框使用。"""
    device_mapping: dict = {}
    ctrl_type = controller_type.lower()
    if ctrl_type == "adb":
        devices = Toolkit.find_adb_devices()
        for device in devices:
            # 尝试从设备 config 中携带的 ld pid 反查雷电序号
            ld_pid = (
                (getattr(device, "config", {}) or {})
                .get("extras", {})
                .get("ld", {})
                .get("pid")
            )
            device_index = ControllerHelper.resolve_emulator_index(
                device, ld_pid=ld_pid
            )
            display_name = (
                f"{device.name}[{device_index}]({device.address})"
                if device_index is not None
                else f"{device.name}({device.address})"
            )
            # 自动生成 ADB 控制器（模拟器）运行路径和参数
            adb_path_str = str(device.adb_path) if device.adb_path else None
            emulator_path, emulator_params = (
                ControllerHelper.generate_emulator_launch_info(
                    device.name, device_index, adb_path_str
                )
            )

            device_mapping[display_name] = {
                "name": device.name,
                "adb_path": device.adb_path,
                "address": device.address,
                "screencap_methods": device.screencap_methods,
                "input_methods": device.input_methods,
                "config": device.config,
                "device_index": device_index,
                "emulator_path": emulator_path,
                "emulator_params": emulator_params,
            }

    elif ctrl_type in ("win32", "macos"):
        devices = Toolkit.find_desktop_windows()
        for device in devices:
            entry = {
                "window_name": device.window_name,
                "class_name": device.class_name,
                "hwnd": str(device.hwnd),
            }
            if ctrl_type == "macos":
                entry["window_id"] = str(device.hwnd)
            device_mapping[
                f"{device.window_name or 'Unknow Window'}({device.hwnd})"
            ] = entry

    return _sanitize_device_mapping(device_mapping)


def _sanitize_device_mapping(device_mapping: dict) -> dict:
    # Convert all integer values that might exceed 64-bit signed limits to strings
    safe_mapping = {}
    for key, value in device_mapping.items():
        safe_value = value.copy()

        # Special handling for adb device config which might contain large integers
        if "config" in safe_value and isinstance(safe_value["config"], dict):
            for config_key, config_value in safe_value["config"].items():
                if isinstance(config_value, int) and not (
                    -9223372036854775808 <= config_value <= 9223372036854775807
                ):
                    safe_value["config"][config_key] = str(config_value)

        # Handle any other large integer fields we might have missed
        for field, field_value in list(safe_value.items()):
            if isinstance(field_value, int) and not (
                -9223372036854775808 <= field_value <= 9223372036854775807
            ):
                safe_value[field] = str(field_value)

        safe_mapping[key] = safe_value
    return safe_mapping


class DeviceFinderTask(QRunnable):
    class Signals(QObject):
        finished = Signal(dict, str)  # device_mapping, controller_type

    def __init__(self, controller_type):
        super().__init__()
        self.controller_type = controller_type
        self.signals = DeviceFinderTask.Signals()

    def run(self):
        device_mapping = {}
        try:
            device_mapping = collect_controller_devices(self.controller_type)
        except Exception:
            logger.exception("后台搜索设备失败: %s", self.controller_type)
        finally:
            self.signals.finished.emit(device_mapping, self.controller_type)


class DeviceFinderWidget(QWidget):
    # 当未找到任何设备时发出的信号
    # 参数为当前控制器类型字符串，例如 "adb" 或 "win32"
    no_device_found = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        self._win32_class_pattern = None
        self._win32_window_pattern = None
        self._macos_title_pattern = None
        self.current_controller_type = None
        self.device_mapping = {}
        self._finder_task = None

    def _init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        self.combo_box = ComboBox()
        self.combo_box.setFixedWidth(260)
        layout.addWidget(self.combo_box, stretch=1)

        self.search_button = ToolButton(FIF.SEARCH)
        self.search_button.setFixedWidth(35)
        self.search_button.clicked.connect(self._on_search_clicked)

        layout.addWidget(self.search_button)

    def change_controller_type(self, new_type: str):
        self.current_controller_type = new_type
        self.combo_box.clear()
        self.device_mapping = {}

    def _on_search_clicked(self):
        if self.current_controller_type is None:
            raise ValueError("Controller type not set")

        self.search_button.setDisabled(True)
        controller_type = self.current_controller_type
        logger.info("开始搜索设备: %s", controller_type)

        if should_search_desktop_windows_on_ui_thread(controller_type):
            # find_desktop_windows 内部 GetWindowText/SendMessage。
            # 放到 QThreadPool 会持有 GIL 并向本进程 Qt 窗口发消息，造成死锁卡死。
            QTimer.singleShot(
                0, lambda: self._run_desktop_window_search(controller_type)
            )
            return

        task = DeviceFinderTask(controller_type)
        task.signals.finished.connect(self._on_device_found)
        self._finder_task = task
        QThreadPool.globalInstance().start(task)

    def _run_desktop_window_search(self, controller_type: str):
        try:
            mapping = collect_controller_devices(controller_type)
        except Exception:
            logger.exception("搜索桌面窗口失败: %s", controller_type)
            mapping = {}
        self._on_device_found(mapping, controller_type)

    def _on_device_found(self, device_mapping, controller_type):
        try:
            # 确保当前控制器类型与查找结果一致
            if controller_type != self.current_controller_type:
                return

            if controller_type.lower() == "win32":
                filtered = {}
                for key, device in device_mapping.items():
                    if self._matches_win32_filters(device):
                        filtered[key] = device
                device_mapping = filtered
            elif controller_type.lower() == "macos":
                filtered = {}
                for key, device in device_mapping.items():
                    if self._matches_macos_filters(device):
                        filtered[key] = device
                device_mapping = filtered

            # 如果没有找到任何设备，仅发出信号，不清空已有下拉框内容
            if not device_mapping:
                logger.info("未搜索到匹配设备: %s", controller_type)
                self.no_device_found.emit(controller_type)
                return

            logger.info("搜索到 %s 个设备: %s", len(device_mapping), controller_type)
            # 更新设备映射和下拉框
            self.device_mapping = device_mapping
            self.combo_box.clear()
            self.combo_box.addItems(list(device_mapping.keys()))
        finally:
            self.search_button.setEnabled(True)

    def _matches_win32_filters(self, device: dict) -> bool:
        if not (self._win32_class_pattern or self._win32_window_pattern):
            return True

        class_name = str(device.get("class_name") or "")
        window_name = str(device.get("window_name") or "")
        class_match = (
            bool(self._win32_class_pattern.search(class_name))
            if self._win32_class_pattern
            else True
        )
        window_match = (
            bool(self._win32_window_pattern.search(window_name))
            if self._win32_window_pattern
            else True
        )

        if self._win32_class_pattern and self._win32_window_pattern:
            return class_match and window_match
        return class_match and window_match

    def set_win32_filters(self, class_regex: str | None, window_regex: str | None):
        self._win32_class_pattern = self._compile_regex(class_regex, "class")
        self._win32_window_pattern = self._compile_regex(window_regex, "window")

    def set_macos_filters(self, title_regex: str | None):
        self._macos_title_pattern = self._compile_regex(title_regex, "title")

    def _matches_macos_filters(self, device: dict) -> bool:
        if not self._macos_title_pattern:
            return True
        window_name = str(device.get("window_name") or "")
        return bool(self._macos_title_pattern.search(window_name))

    def _compile_regex(self, pattern: str | None, label: str):
        if not pattern:
            return None
        try:
            return re.compile(pattern)
        except re.error as exc:
            logger.warning(f"正则过滤器 [{label}] 编译失败: {exc}")
            return None
