"""
搜索设备/窗口生成器
负责生成搜索ADB设备和Win32窗口的组件
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtCore import Qt, QObject
from qfluentwidgets import ComboBox, PushButton, BodyLabel, ToolTipFilter
from app.utils.logger import logger
from maa.toolkit import Toolkit


class SearchDeviceGenerator(QObject):
    """
    搜索设备/窗口生成器
    负责搜索ADB设备和Win32窗口的创建、配置和信号处理
    """

    def __init__(self, host):
        """
        初始化搜索设备/窗口生成器
        :param host: 宿主组件，需要包含widgets、child_layouts等属性
        """
        self.host = host

    def create_search_device(self, key, config, parent_layout, parent_config):
        """创建搜索设备/窗口组件"""
        # 创建控件容器布局
        container_layout = QVBoxLayout()
        container_layout.setContentsMargins(5, 5, 5, 5)
        container_layout.setSpacing(5)
        parent_layout.addLayout(container_layout)

        # 创建标签和图标容器
        label_container = QHBoxLayout()
        label_container.setSpacing(5)

        # 创建标题标签 - 硬编码文本，不使用配置中的值
        title_text = self.tr("Device Search")
        title_label = BodyLabel(title_text)

        # 添加标签到容器
        label_container.addWidget(title_label)

        # 将整个标签容器添加到主布局
        container_layout.addLayout(label_container)

        # 为标题添加tooltip - 硬编码文本，不使用配置中的值
        filter = ToolTipFilter(title_label)
        title_label.installEventFilter(filter)
        title_label.setToolTip(self.tr("Search for ADB devices or Win32 windows"))

        # 创建下拉框和按钮的水平布局
        search_container = QHBoxLayout()
        search_container.setSpacing(10)
        container_layout.addLayout(search_container)

        # 创建结果下拉框（初始为空）
        result_combo = ComboBox()
        result_combo.setPlaceholderText(self.tr("No devices found"))

        # 创建搜索按钮 - 硬编码文本，不使用配置中的值
        search_button = PushButton(self.tr("Search"))

        # 将下拉框和按钮添加到水平布局
        search_container.addWidget(result_combo)
        search_container.addWidget(search_button)

        # 检查是否需要隐藏整个组件
        if "visible" in config and not config["visible"]:
            # 隐藏所有控件
            title_label.setVisible(False)
            result_combo.setVisible(False)
            search_button.setVisible(False)

        # 为控件添加tooltip
        if "description" in config:
            filter = ToolTipFilter(result_combo)
            result_combo.installEventFilter(filter)
            result_combo.setToolTip(config["description"])

            filter = ToolTipFilter(search_button)
            search_button.installEventFilter(filter)
            search_button.setToolTip(self.tr("Click to search devices/windows"))

        # 保存引用
        self.host.widgets[key] = result_combo
        self.host.widgets[f"{key}_button"] = search_button

        # 初始化配置
        parent_config[key] = ""

        # 连接信号
        search_button.clicked.connect(
            lambda current_key=key, current_config=config: self._on_search_clicked(
                current_key, current_config
            )
        )

        # 连接下拉框选择信号
        result_combo.currentTextChanged.connect(
            lambda value, current_key=key, current_config=config: self._on_result_selected(
                current_key, value, current_config
            )
        )

    def _on_search_clicked(self, key, config):
        """搜索按钮点击处理"""
        # 获取当前控制器类型（从controller_type中获取）
        controller_type = ""

        # 调试：检查host对象是否有current_config
        logger.info(f"Current config: {self.host.current_config}")

        # 方式1：从current_config中获取（更可靠）
        if "controller_type" in self.host.current_config:
            controller_data = self.host.current_config["controller_type"]
            if isinstance(controller_data, dict) and "value" in controller_data:
                controller_type = controller_data["value"]

        # 方式2：从控制器下拉框中直接获取（备选）
        if not controller_type and "controller_type" in self.host.widgets:
            controller_combo = self.host.widgets["controller_type"]
            if controller_combo:
                # 从选项映射中获取实际值
                if "controller_type" in self.host._option_maps:
                    selected_text = controller_combo.currentText()
                    controller_type = self.host._option_maps["controller_type"].get(
                        selected_text, selected_text
                    )

        logger.info(f"Detected controller type: {controller_type}")

        result_combo = self.host.widgets.get(key)

        if not result_combo:
            logger.error("Result combo box not found")
            return

        try:
            result_combo = self.host.widgets.get(key)
            if not result_combo:
                return

            # 清空现有选项
            result_combo.clear()
            result_combo.setPlaceholderText(self.tr("Searching..."))

            # 根据控制器类型搜索
            if controller_type == "adb":
                # 搜索ADB设备
                devices = Toolkit.find_adb_devices()
                # 将结果添加到下拉框
                if devices and isinstance(devices, list):
                    for device in devices:
                        result_combo.addItem(device)
            elif controller_type == "win32":
                # 搜索Win32窗口
                windows = Toolkit.find_desktop_windows()
                # 将结果添加到下拉框
                if windows and isinstance(windows, list):
                    for window in windows:
                        try:
                            # DesktopWindow是对象类型，使用getattr安全访问属性
                            hwnd = getattr(window, "hwnd", "")
                            # 尝试不同的标题属性名
                            title = getattr(window, "title", "") or getattr(
                                window, "name", ""
                            )
                            if hwnd:
                                item_text = f"{title} (HWND: {hwnd})"
                                result_combo.addItem(item_text)
                        except Exception as window_e:
                            # 忽略解析窗口信息时的错误
                            logger.error(f"解析窗口信息失败: {window_e}")

            # 更新占位符
            if result_combo and result_combo.count() == 0:
                result_combo.setPlaceholderText(self.tr("No devices/windows found"))
            elif result_combo:
                result_combo.setPlaceholderText("")

        except Exception as e:
            logger.error(f"搜索设备/窗口失败: {e}")
            if result_combo:
                result_combo.setPlaceholderText(self.tr("Search failed"))

    def _on_result_selected(self, key, value, config):
        """选择搜索结果处理"""
        # 解析选择的结果
        if not value:
            return

        # 根据控制器类型写入不同的输入框
        controller_type = ""
        if "controller_type" in self.host.widgets:
            controller_combo = self.host.widgets["controller_type"]
            if hasattr(controller_combo, "_value"):
                controller_type = controller_combo._value
            else:
                if "controller_type" in self.host._option_maps:
                    selected_text = controller_combo.currentText()
                    controller_type = self.host._option_maps["controller_type"].get(
                        selected_text, selected_text
                    )

        if controller_type == "adb":
            # ADB设备直接写入device_address
            self._write_result_to_input("device_address", value)
        elif controller_type == "win32":
            # Win32窗口需要提取hwnd
            import re

            match = re.search(r"HWND: (\d+)", value)
            if match:
                hwnd = match.group(1)
                self._write_result_to_input("hwnd", hwnd)

    def _write_result_to_input(self, input_key, data):
        """将搜索结果写入对应的输入框"""
        # 查找对应的输入框控件
        if input_key in self.host.widgets:
            input_widget = self.host.widgets[input_key]
            if hasattr(input_widget, "setText"):
                input_widget.setText(str(data))
