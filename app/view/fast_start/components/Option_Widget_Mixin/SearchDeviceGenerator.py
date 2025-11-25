"""
搜索设备/窗口生成器
负责生成搜索ADB设备和Win32窗口的组件
"""

from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel
from PySide6.QtCore import Qt, QObject, QRunnable, QThreadPool, Signal
from qfluentwidgets import ComboBox, PushButton, BodyLabel, ToolTipFilter, ToolButton
from qfluentwidgets import FluentIcon as FIF
from app.utils.logger import logger


class BaseDeviceSearcher(QObject):
    """
    设备搜索器基类
    负责搜索设备/窗口的创建、配置和信号处理
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

        # 创建标题标签 - 硬编码文本
        title_text = self.tr("Device Search")
        title_label = BodyLabel(title_text)

        # 添加标签到容器
        label_container.addWidget(title_label)

        # 将整个标签容器添加到主布局
        container_layout.addLayout(label_container)

        # 为标题添加tooltip - 硬编码文本
        filter = ToolTipFilter(title_label)
        title_label.installEventFilter(filter)
        title_label.setToolTip(self.tr("Search for ADB devices or Win32 windows"))

        # 创建下拉框和按钮的水平布局
        search_container = QHBoxLayout()
        search_container.setSpacing(5)  # 与PathLineEdit一致
        container_layout.addLayout(search_container)
        # 创建结果下拉框（初始为空）
        self.result_combo = ComboBox()
        self.result_combo.setPlaceholderText(self.tr("No devices found"))
        # 创建搜索按钮 - 硬编码文本
        search_button = ToolButton(FIF.SEARCH)

        # 让下拉框占据大部分空间，按钮使用最小尺寸
        self.result_combo.setFixedWidth(242)  # 设置固定宽度
        search_button.setFixedWidth(35)  # 与PathLineEdit的按钮宽度一致

        # 设置下拉框的拉伸因子为1，按钮为0
        search_container.addWidget(self.result_combo, 1)  # 1表示拉伸
        search_container.addWidget(search_button, 0)  # 0表示不拉伸

        # 检查是否需要隐藏整个组件
        if "visible" in config and not config["visible"]:
            # 隐藏所有控件
            title_label.setVisible(False)
            self.result_combo.setVisible(False)
            search_button.setVisible(False)

        # 为控件添加tooltip
        if "description" in config:
            filter = ToolTipFilter(self.result_combo)
            self.result_combo.installEventFilter(filter)
            self.result_combo.setToolTip(config["description"])

            filter = ToolTipFilter(search_button)
            search_button.installEventFilter(filter)
            search_button.setToolTip(self.tr("Click to search devices/windows"))

        # 保存引用到正确的容器
        widget_saved = False

        # 遍历所有子容器，找到与parent_layout匹配的容器
        self._container = None
        self._config = parent_config

        for main_key, container_dict in self.host.all_child_containers.items():
            for option_key, container in container_dict.items():
                if container["layout"] == parent_layout:
                    # 保存到子容器的widgets字典
                    container["widgets"][key] = self.result_combo
                    container["widgets"][f"{key}_button"] = search_button
                    self._container = container
                    self._config = container["config"]
                    widget_saved = True
                    logger.debug(
                        f"Search device widget saved to child container: {main_key} -> {option_key} -> {key}"
                    )
                    break
            if widget_saved:
                break

        # 如果没有找到子容器，保存到host的widgets字典
        if not widget_saved:
            self.host.widgets[key] = self.result_combo
            self.host.widgets[f"{key}_button"] = search_button
            self._config = self.host.current_config
            logger.debug(f"Search device widget saved to host widgets: {key}")

        # 初始化配置
        self._config[key] = ""

        # 连接信号，使用闭包来确保参数正确传递
        def on_click():
            logger.info(f"Button clicked with key: {key}, type: {type(key)}")
            self._on_search_clicked(key, config)

        search_button.clicked.connect(on_click)

        # 连接下拉框选择信号
        self.result_combo.currentTextChanged.connect(
            lambda value, current_key=key, current_config=config: self._on_result_selected(
                current_key, value, current_config
            )
        )

        # 恢复上次选择的设备名称（如果有）
        if key in self.host.current_config and self.host.current_config[key]:
            saved_device_name = self.host.current_config[key]
            self.result_combo.setCurrentText(saved_device_name)

    def _on_search_clicked(self, key, config):
        """搜索按钮点击处理 - 需要在子类中实现"""
        raise NotImplementedError("Subclasses must implement _on_search_clicked method")

    def _on_result_selected(self, key, value, config):
        """选择搜索结果处理 - 需要在子类中实现"""
        # 默认保存当前选中的设备/窗口到配置
        logger.debug(
            f"_on_result_selected called with key: {key}, value: {value}, _config: {self._config}"
        )

        # 打印下拉框更改内容
        print(f"设备下拉框已更改：{value}")

        # 更新所有可能的配置位置
        if hasattr(self, "_config") and self._config is not None:
            self._config[key] = value

        # Also update the host's current_config for consistency
        if key in self.host.current_config:
            self.host.current_config[key] = value

        # Directly ensure the widget displays the correct value
        if hasattr(self, "result_combo"):
            logger.debug(f"Setting result_combo currentText to: {value}")

            combo = self.result_combo

            # 检查值是否实际存在于下拉框中
            index = combo.findText(value)
            if index != -1:
                # 如果值存在，使用索引设置（更可靠）
                combo.setCurrentIndex(index)

                # 再次确认文本正确显示
                combo.setCurrentText(value)

                # 仅使用update()，避免repaint()可能导致的递归问题
                combo.update()

                logger.debug(f"Successfully set dropdown to: {value} at index: {index}")

            else:
                # 如果值不存在，记录日志并暂时不设置
                logger.debug(
                    f"Value '{value}' not found in dropdown, skipping selection"
                )

        # 子类可以覆盖此方法进行其他处理，但必须调用super()或保存值
        # 自动保存选项
        self._auto_save_options()

    def _auto_save_options(self):
        """自动保存当前选项"""
        # 检查是否禁用了自动保存
        if hasattr(self.host, "_disable_auto_save") and self.host._disable_auto_save:
            return
            
        # 检查是否有service_coordinator和option_service
        if hasattr(self.host, "service_coordinator") and hasattr(self.host.service_coordinator, "option_service"):  # type: ignore
            try:
                # 获取当前所有配置
                all_config = self.host.get_config()
                # 调用OptionService的update_options方法保存选项
                self.host.service_coordinator.option_service.update_options(all_config)  # type: ignore
            except Exception as e:
                # 如果保存失败，记录错误但不影响用户操作
                logger.error(f"自动保存选项失败: {e}")

    def _write_result_to_input(self, input_key, data):
        """将搜索结果写入对应的输入框"""
        # 查找对应的输入框控件
        input_widget = None

        # 首先检查直接存储的widgets
        if input_key in self.host.widgets:
            input_widget = self.host.widgets[input_key]
        else:
            # 检查是否存储在all_child_containers中
            logger.debug(
                f"Looking for input widget in all_child_containers: {input_key}"
            )

            for main_key, container_dict in self.host.all_child_containers.items():
                for option_key, container in container_dict.items():
                    if input_key in container["widgets"]:
                        input_widget = container["widgets"][input_key]
                        logger.debug(
                            f"Found input widget in child container: {input_key}"
                        )
                        break
                if input_widget:
                    break

        if input_widget and hasattr(input_widget, "setText"):
            input_widget.setText(str(data))
            
            # 更新配置并保存
            # 查找对应的配置位置并更新
            found = False
            for main_key, container_dict in self.host.all_child_containers.items():
                for option_key, container in container_dict.items():
                    # 直接使用input_key作为配置键更新
                    if input_key in container["config"]:
                        container["config"][input_key] = str(data)
                        found = True
                        break
                if found:
                    break
            
            if not found:
                # 更新host的current_config
                if input_key in self.host.current_config:
                    self.host.current_config[input_key] = str(data)
            
            # 自动保存选项
            self._auto_save_options()


class AdbDeviceSearcher(BaseDeviceSearcher):
    """ADB设备搜索器"""

    def __init__(self, host):
        super().__init__(host)
        from maa.toolkit import Toolkit

        self.Toolkit = Toolkit
        self._device_map = {}  # 保存设备名称到设备结构体的映射

    def _on_search_clicked(self, key, config):
        """搜索ADB设备 - 启动异步任务"""
        # 清空现有选项
        self.result_combo.clear()
        self.result_combo.setPlaceholderText(self.tr("Searching..."))

        # 创建并启动异步搜索任务
        class AdbSearchTask(QRunnable):
            def __init__(self, toolkit, callback):
                super().__init__()
                self.toolkit = toolkit
                self.callback = callback

            def run(self):
                try:
                    devices = self.toolkit.find_adb_devices()
                    print(f"所有设备:\n{devices}")
                    self.callback(devices)
                except Exception as e:
                    self.callback(None, e)

        # 定义搜索结果处理函数
        def handle_search_result(devices, error=None):
            try:
                if error:
                    raise error

                # 将结果添加到下拉框
                if devices and isinstance(devices, list):
                    # 清空设备映射
                    self._device_map = {}
                    device_list = []

                    for device in devices:
                        try:
                            # 从结构体中提取设备名称、adb路径和连接地址
                            device_name = (
                                getattr(device, "name", "") or "Unknown Device"
                            )
                            adb_address = getattr(device, "address", "") or getattr(
                                device, "device_address", ""
                            )

                            # 创建组合显示名称
                            if adb_address:
                                display_name = f"{device_name} ({adb_address})"
                            else:
                                display_name = device_name

                            # 保存设备映射
                            self._device_map[display_name] = device
                            device_list.append(display_name)

                            # 调试：输出设备结构体信息
                            logger.info(
                                f"Found ADB device: {device_name}, struct: {device.__dict__}"
                            )
                        except Exception as e:
                            logger.error(f"Failed to process ADB device: {e}")

                    # 使用addItems一次性添加所有设备
                    self.result_combo.addItems(device_list)

                    # 设置没有选中任何项
                    self.result_combo.setCurrentIndex(-1)

                    # 更新UI
                    self.result_combo.update()

                # 更新占位符
                if self.result_combo and self.result_combo.count() == 0:
                    self.result_combo.setPlaceholderText(
                        self.tr("No ADB devices found")
                    )
                elif self.result_combo:
                    self.result_combo.setPlaceholderText("")

            except Exception as e:
                logger.error(f"搜索ADB设备失败: {e}")

                if self.result_combo:
                    self.result_combo.setPlaceholderText(self.tr("Search failed"))

        # 启动任务
        task = AdbSearchTask(self.Toolkit, handle_search_result)
        QThreadPool.globalInstance().start(task)

    def _on_result_selected(self, key, value, config):
        """选择ADB设备处理"""
        # 解析选择的结果
        if not value:
            return

        # 获取选中的设备结构体
        device = self._device_map.get(value)

        # 确保device存在且具有必要的属性
        if device:
            # 写入ADB连接地址
            adb_address = getattr(device, "address", "") or getattr(
                device, "device_address", ""
            )
            if adb_address:
                self._write_result_to_input("device_address", adb_address)

            # 写入ADB路径
            adb_path = getattr(device, "adb_path", "") or getattr(device, "path", "")
            if adb_path:
                self._write_result_to_input("adb_path", adb_path)

        # 然后在一个地方写入正确的设备名称
        if hasattr(self, "_config") and self._config is not None:
            self._config[key] = value

        # 保存当前选中的设备名称到配置 - 使用在create_search_device中保存的正确配置对象

        super()._on_result_selected(key, value, config)


class Win32WindowSearcher(BaseDeviceSearcher):
    """Win32窗口搜索器"""

    def __init__(self, host):
        super().__init__(host)
        from maa.toolkit import Toolkit
        import re

        self.Toolkit = Toolkit
        self.re = re

    def _on_search_clicked(self, key, config):
        """搜索Win32窗口 - 启动异步任务"""
        # 清空现有选项
        self.result_combo.clear()
        self.result_combo.setPlaceholderText(self.tr("Searching..."))

        # 创建并启动异步搜索任务
        class Win32SearchTask(QRunnable):
            def __init__(self, toolkit, callback):
                super().__init__()
                self.toolkit = toolkit
                self.callback = callback

            def run(self):
                try:
                    windows = self.toolkit.find_desktop_windows()
                    self.callback(windows)
                except Exception as e:
                    self.callback(None, e)

        # 定义搜索结果处理函数
        def handle_search_result(windows, error=None):
            try:
                if error:
                    raise error

                # 将结果添加到下拉框
                if windows and isinstance(windows, list):
                    window_list = []
                    for window in windows:
                        try:
                            # DesktopWindow是对象类型，使用getattr安全访问属性
                            hwnd = getattr(window, "hwnd", "")
                            # 尝试不同的标题属性名
                            window_name = getattr(window, "window_name", "")
                            # 如果标题为空，使用"Unknown Window"
                            if not window_name:
                                window_name = "Unknown Window"
                            if hwnd:
                                item_text = f"{window_name} (HWND: {hwnd})"
                                window_list.append(item_text)
                        except Exception as window_e:
                            # 忽略解析窗口信息时的错误
                            logger.error(f"解析窗口信息失败: {window_e}")

                    # 使用addItems一次性添加所有窗口
                    self.result_combo.addItems(window_list)

                    # 设置没有选中任何项
                    self.result_combo.setCurrentIndex(-1)

                    # 更新UI
                    self.result_combo.update()

                # 更新占位符
                if self.result_combo and self.result_combo.count() == 0:
                    self.result_combo.setPlaceholderText(self.tr("No windows found"))
                elif self.result_combo:
                    self.result_combo.setPlaceholderText("")

            except Exception as e:
                logger.error(f"搜索Win32窗口失败: {e}")
                if self.result_combo:
                    self.result_combo.setPlaceholderText(self.tr("Search failed"))

        # 启动任务
        task = Win32SearchTask(self.Toolkit, handle_search_result)
        QThreadPool.globalInstance().start(task)

    def _on_result_selected(self, key, value, config):
        """选择Win32窗口处理"""
        # 解析选择的结果
        if not value:
            return

        # Win32窗口需要提取hwnd
        match = self.re.search(r"HWND: (\d+)", value)
        if match is not None:
            hwnd = match.group(1)
            self._write_result_to_input("hwnd", hwnd)

        # 然后在一个地方写入正确的窗口名称
        if hasattr(self, "_config") and self._config is not None:
            self._config[key] = value

        # 保存当前选中的设备名称到配置 - 使用在create_search_device中保存的正确配置对象

        super()._on_result_selected(key, value, config)


# 提供一个工厂函数来根据控制器类型创建相应的搜索器
def create_device_searcher(host, controller_type):
    """
    根据控制器类型创建相应的搜索器
    :param host: 宿主组件
    :param controller_type: 控制器类型 (adb/win32)
    :return: 搜索器实例
    """
    if controller_type == "adb":
        return AdbDeviceSearcher(host)
    elif controller_type == "win32":
        return Win32WindowSearcher(host)
    else:
        logger.error(f"Unsupported controller type: {controller_type}")
        return None
