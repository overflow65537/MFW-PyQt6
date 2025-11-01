"""资源设置选项模块

提供资源设置页面的完整功能，包括控制器类型选择、设备管理、资源选择等。
"""

import json
from qfluentwidgets import (
    ComboBox, LineEdit, BodyLabel, PrimaryPushButton, ToolTipFilter, ToolTipPosition
)
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout
from app.utils.logger import logger
from app.utils.i18n_manager import get_interface_i18n
from ._mixin_base import MixinBase


class ResourceSettingMixin(MixinBase):
    """资源设置选项 Mixin
    
    提供资源设置页面的完整功能：
    - 控制器类型选择
    - 设备刷新和选择
    - 资源选择（根据控制器过滤）
    - 设备自动填充
    - 控制器特定选项动态切换
    
    继承自 MixinBase，获得通用的类型提示，避免 Pylance 报错。
    运行时 `self` 指向 OptionWidget 实例，可访问其所有属性/方法。
    
    需要配合 OptionWidget 使用，依赖：
    - self.service_coordinator
    - self.option_area_layout
    - self._clear_options
    - self._flatten_controller_options
    - self._get_option_value
    - self._populate_saved_device
    - self._show_adb_options
    - self._show_win32_options
    - self._show_controller_common_options
    - self._save_current_options
    - self._clear_layout
    - self.tr
    """
    
    def _show_resource_setting_option(self, item):
        """显示资源设置选项页面（合并控制器和资源配置）
        
        包含：
        - 控制器类型选择下拉框
        - 刷新设备按钮
        - 资源选择下拉框（根据控制器类型过滤）
        - 设备选择下拉框
        - 控制器特定选项（ADB/Win32，动态切换）
        - 通用选项（GPU、启动前/后程序等）
        
        Args:
            item: TaskItem 对象
        """
        self._clear_options()
        
        # 保存当前任务项供其他方法使用
        self._current_task_item = item
        
        # 获取 interface 配置
        interface = self.service_coordinator.task.interface
        if not interface:
            logger.warning("未找到任务接口配置")
            return
        
        # 获取控制器和资源配置列表
        controllers = interface.get("controller", [])
        resources = interface.get("resource", [])
        
        if not controllers:
            label = BodyLabel(self.tr("No controller configuration found"))
            self.option_area_layout.addWidget(label)
            return
        
        # 保存配置供后续使用
        self.controller_configs = {c.get("name"): c for c in controllers}
        self.resource_configs = resources
        
        # 获取当前保存的选项（展平嵌套的 ADB/Win32 配置）
        saved_options = self._flatten_controller_options(item.task_option)
        current_controller_name = str(self._get_option_value(saved_options, "controller_type", ""))
        
        # 1. 控制器类型选择（水平布局：下拉框 + 按钮）
        controller_h_layout = QHBoxLayout()
        controller_h_layout.setObjectName("controller_type_layout")
        
        # 控制器类型下拉框
        controller_v_layout = QVBoxLayout()
        controller_label = BodyLabel(self.tr("Controller Type"))
        controller_label.setStyleSheet("font-weight: bold;")
        controller_v_layout.addWidget(controller_label)
        
        self.controller_type_combo = ComboBox()
        self.controller_type_combo.setObjectName("controller_type")
        self.controller_type_combo.setMaximumWidth(400)
        
        # 使用 label 作为显示文本，name 作为内部值
        for i, controller in enumerate(controllers):
            name = controller.get("name", "")
            label = controller.get("label", name)
            if label.startswith("$"):
                label = label[1:]
            self.controller_type_combo.addItem(label)
            self.controller_type_combo.setItemData(i, name)
        
        # 设置当前选中项
        if current_controller_name:
            for i in range(self.controller_type_combo.count()):
                if self.controller_type_combo.itemData(i) == current_controller_name:
                    self.controller_type_combo.setCurrentIndex(i)
                    break
        
        controller_v_layout.addWidget(self.controller_type_combo)
        controller_h_layout.addLayout(controller_v_layout, stretch=3)
        
        # 设备刷新按钮
        button_v_layout = QVBoxLayout()
        button_v_layout.addSpacing(24)
        
        self.refresh_devices_button = PrimaryPushButton(self.tr("Refresh Devices"))
        self.refresh_devices_button.setObjectName("refresh_devices_button")
        self.refresh_devices_button.clicked.connect(self._on_refresh_devices_clicked)
        button_v_layout.addWidget(self.refresh_devices_button)
        
        controller_h_layout.addLayout(button_v_layout, stretch=1)
        self.option_area_layout.addLayout(controller_h_layout)
        
        # 2. 资源选择下拉框（根据控制器类型过滤）
        self.resource_combo_layout = QVBoxLayout()
        self.resource_combo_layout.setObjectName("resource_combo_layout")
        self.option_area_layout.addLayout(self.resource_combo_layout)
        
        # 3. 设备选择下拉框
        device_v_layout = QVBoxLayout()
        device_v_layout.setObjectName("device_layout")
        
        device_label = BodyLabel(self.tr("Select Device"))
        device_label.setStyleSheet("font-weight: bold;")
        device_v_layout.addWidget(device_label)
        
        self.device_combo = ComboBox()
        self.device_combo.setObjectName("device")
        self.device_combo.setMaximumWidth(400)
        
        # 从保存的配置中构建设备信息并填充到下拉框（在连接信号之前）
        self._populate_saved_device(saved_options, current_controller_name)
        
        # 连接设备选择改变信号
        self.device_combo.currentIndexChanged.connect(
            lambda: self._on_device_selected_in_resource_setting(item)
        )
        
        device_v_layout.addWidget(self.device_combo)
        self.option_area_layout.addLayout(device_v_layout)
        
        # 4. 创建容器用于存放动态选项（ADB 或 Win32 特定选项）
        self.controller_specific_options_layout = QVBoxLayout()
        self.controller_specific_options_layout.setObjectName("controller_specific_options")
        self.option_area_layout.addLayout(self.controller_specific_options_layout)
        
        # 5. 通用选项容器
        self.controller_common_options_layout = QVBoxLayout()
        self.controller_common_options_layout.setObjectName("controller_common_options")
        self.option_area_layout.addLayout(self.controller_common_options_layout)
        
        # 连接控制器类型变化信号
        self.controller_type_combo.currentIndexChanged.connect(
            lambda: self._on_resource_setting_controller_changed(item, clear_device=True)
        )
        
        # 初始化显示对应的选项
        self._on_resource_setting_controller_changed(item, clear_device=False)
        
        # 如果有保存的设备信息，手动触发一次自动填充
        if self.device_combo.count() > 0 and self.device_combo.currentIndex() >= 0:
            logger.info(f"手动触发设备自动填充")
            self._on_device_selected_in_resource_setting(item)
    
    def _on_resource_setting_controller_changed(self, item, clear_device=True):
        """资源设置页面中控制器类型改变时的回调
        
        Args:
            item: TaskItem 对象
            clear_device: 是否清空设备下拉框
        """
        current_name = self.controller_type_combo.currentData()
        if not current_name or current_name not in self.controller_configs:
            return
        
        controller_config = self.controller_configs[current_name]
        controller_type = controller_config.get("type", "").lower()
        
        # 更新控制器类型下拉框的 tooltip
        description = controller_config.get("description", "")
        if description:
            self.controller_type_combo.setToolTip(description)
            for child in self.controller_type_combo.children():
                if isinstance(child, ToolTipFilter):
                    self.controller_type_combo.removeEventFilter(child)
                    child.deleteLater()
            self.controller_type_combo.installEventFilter(
                ToolTipFilter(self.controller_type_combo, 0, ToolTipPosition.TOP)
            )
        else:
            self.controller_type_combo.setToolTip("")
        
        # 清空设备下拉框
        if clear_device:
            self.device_combo.clear()
            self._populate_saved_device(item.task_option, current_name)
        
        # 更新资源下拉框
        self._update_resource_options(item, current_name)
        
        # 清空并重新创建特定选项
        self._clear_layout(self.controller_specific_options_layout)
        
        saved_options = item.task_option
        flattened_options = self._flatten_controller_options(saved_options)
        
        # 根据类型显示对应选项
        if controller_type == "adb":
            self._show_adb_options(flattened_options)
        elif controller_type == "win32":
            self._show_win32_options(flattened_options)
        
        # 显示通用选项
        self._clear_layout(self.controller_common_options_layout)
        self._show_controller_common_options(flattened_options)
        
        # 触发设备自动填充
        if self.device_combo.count() > 0 and self.device_combo.currentIndex() >= 0:
            if hasattr(self, '_current_task_item'):
                self._on_device_selected_in_resource_setting(self._current_task_item)
    
    def _on_device_selected_in_resource_setting(self, item):
        """资源设置页面中设备选择改变时的回调 - 自动填充相关字段
        
        Args:
            item: TaskItem 对象
        """
        device_data = self.device_combo.currentData()
        
        logger.info(f"设备选择改变，device_data: {device_data}")
        
        if not device_data or not isinstance(device_data, dict):
            logger.warning("设备数据无效")
            self._save_current_options()
            return
        
        current_name = self.controller_type_combo.currentData()
        if not current_name or current_name not in self.controller_configs:
            logger.warning(f"控制器类型无效: {current_name}")
            self._save_current_options()
            return
        
        controller_config = self.controller_configs[current_name]
        controller_type = controller_config.get("type", "").lower()
        device_type = device_data.get("type", "")
        
        logger.info(f"控制器类型: {controller_type}, 设备类型: {device_type}")
        
        # 自动填充字段
        if device_type == "adb" and controller_type == "adb":
            self._autofill_adb_fields(device_data)
        elif device_type == "win32" and controller_type == "win32":
            self._autofill_win32_fields(device_data)
        
        self._save_current_options()
    
    def _autofill_adb_fields(self, device_data):
        """自动填充 ADB 字段
        
        Args:
            device_data: ADB 设备数据字典
        """
        logger.info("开始自动填充 ADB 字段")
        
        # 1. ADB 路径
        adb_path = str(device_data.get("adb_path", ""))
        adb_path_widget = self.findChild(LineEdit, "adb_path")
        if adb_path_widget:
            adb_path_widget.setText(adb_path)
            logger.info(f"✓ 填充 adb_path: {adb_path}")
        
        # 2. 连接地址
        device_address = device_data.get("address", "")
        adb_port_widget = self.findChild(LineEdit, "adb_port")
        if adb_port_widget:
            adb_port_widget.setText(device_address)
            logger.info(f"✓ 填充 adb_port: {device_address}")
        
        # 3. 设备名称
        device_name = device_data.get("name", "")
        if device_name:
            adb_device_name_widget = self.findChild(LineEdit, "adb_device_name")
            if not adb_device_name_widget:
                adb_device_name_widget = LineEdit()
                adb_device_name_widget.setObjectName("adb_device_name")
                adb_device_name_widget.setVisible(False)
                adb_device_name_widget.textChanged.connect(lambda: self._save_current_options())
                self.controller_specific_options_layout.addWidget(adb_device_name_widget)
            adb_device_name_widget.setText(device_name)
            logger.info(f"✓ 填充 adb_device_name: {device_name}")
        
        # 4. 截图方法
        screencap_methods = device_data.get("screencap_methods", 0)
        if screencap_methods:
            adb_screenshot_combo = self.findChild(ComboBox, "adb_screenshot_method")
            if adb_screenshot_combo:
                adb_screenshot_combo.blockSignals(True)
                for i in range(adb_screenshot_combo.count()):
                    if adb_screenshot_combo.itemData(i) == str(screencap_methods):
                        adb_screenshot_combo.setCurrentIndex(i)
                        logger.info(f"✓ 填充 adb_screenshot_method: {screencap_methods}")
                        break
                else:
                    adb_screenshot_combo.setProperty("original_value", str(screencap_methods))
                    adb_screenshot_combo.setCurrentIndex(0)
                adb_screenshot_combo.blockSignals(False)
        
        # 5. 输入方法
        input_methods = device_data.get("input_methods", 0)
        if input_methods:
            adb_input_combo = self.findChild(ComboBox, "adb_input_method")
            if adb_input_combo:
                adb_input_combo.blockSignals(True)
                for i in range(adb_input_combo.count()):
                    if adb_input_combo.itemData(i) == str(input_methods):
                        adb_input_combo.setCurrentIndex(i)
                        logger.info(f"✓ 填充 adb_input_method: {input_methods}")
                        break
                else:
                    adb_input_combo.setProperty("original_value", str(input_methods))
                    adb_input_combo.setCurrentIndex(0)
                adb_input_combo.blockSignals(False)
        
        # 6. Config
        config = device_data.get("config", {})
        if config:
            config_widget = self.findChild(LineEdit, "adb_config")
            if config_widget:
                config_json = json.dumps(config, ensure_ascii=False)
                config_widget.setText(config_json)
                logger.info(f"✓ 填充 adb_config")
    
    def _autofill_win32_fields(self, device_data):
        """自动填充 Win32 字段
        
        Args:
            device_data: Win32 窗口数据字典
        """
        logger.info("开始自动填充 Win32 字段")
        
        # 1. 窗口句柄
        hwnd = device_data.get("hwnd", "")
        if hwnd:
            hwnd_widget = self.findChild(LineEdit, "hwnd")
            if hwnd_widget:
                hwnd_widget.setText(str(hwnd))
                logger.info(f"✓ 填充 hwnd: {hwnd}")
        
        # 2. 窗口名称
        window_name = device_data.get("window_name", "")
        if window_name:
            win32_device_name_widget = self.findChild(LineEdit, "win32_device_name")
            if not win32_device_name_widget:
                win32_device_name_widget = LineEdit()
                win32_device_name_widget.setObjectName("win32_device_name")
                win32_device_name_widget.setVisible(False)
                win32_device_name_widget.textChanged.connect(lambda: self._save_current_options())
                self.controller_specific_options_layout.addWidget(win32_device_name_widget)
            win32_device_name_widget.setText(window_name)
            logger.info(f"✓ 填充 win32_device_name: {window_name}")
    
    def _update_resource_options(self, item, controller_name):
        """更新资源选择下拉框（根据控制器过滤）
        
        Args:
            item: TaskItem 对象
            controller_name: 控制器名称
        """
        self._clear_layout(self.resource_combo_layout)
        
        # 过滤资源列表
        filtered_resources = []
        for resource in self.resource_configs:
            controller_list = resource.get("controller", [])
            if not controller_list or controller_name in controller_list:
                filtered_resources.append(resource)
        
        if not filtered_resources:
            return
        
        saved_options = item.task_option
        current_value = self._get_option_value(saved_options, "resource", "")
        
        # 检查当前资源是否适用
        filtered_resource_names = [r.get("name", "") for r in filtered_resources]
        if current_value and current_value not in filtered_resource_names:
            current_value = ""
        
        # 创建垂直布局
        v_layout = QVBoxLayout()
        v_layout.setObjectName("resource_layout")
        
        label = BodyLabel(self.tr("Resource"))
        label.setStyleSheet("font-weight: bold;")
        v_layout.addWidget(label)
        
        combo = ComboBox()
        combo.setObjectName("resource")
        combo.setMaximumWidth(400)
        
        # 添加资源选项
        for i, resource in enumerate(filtered_resources):
            name = resource.get("name", "")
            display_label = resource.get("label", name)
            if display_label.startswith("$"):
                display_label = display_label[1:]
            combo.addItem(display_label)
            combo.setItemData(i, name)
        
        # 设置当前选中项
        if current_value:
            for i in range(combo.count()):
                if combo.itemData(i) == current_value:
                    combo.setCurrentIndex(i)
                    break
        
        combo.currentIndexChanged.connect(lambda: self._save_current_options())
        
        v_layout.addWidget(combo)
        self.resource_combo_layout.addLayout(v_layout)
    
    def _on_refresh_devices_clicked(self):
        """刷新设备列表按钮点击事件"""
        current_name = self.controller_type_combo.currentData()
        if not current_name or current_name not in self.controller_configs:
            logger.warning("未选择控制器类型")
            return
        
        controller_config = self.controller_configs[current_name]
        controller_type = controller_config.get("type", "").lower()
        
        # 临时断开信号
        try:
            self.device_combo.currentIndexChanged.disconnect()
        except TypeError:
            pass
        
        self.device_combo.clear()
        
        if controller_type == "adb":
            devices = self._get_adb_devices()
            self._populate_device_list(devices)
        elif controller_type == "win32":
            devices = self._get_win32_devices()
            self._populate_device_list(devices)
        else:
            logger.warning(f"未知的控制器类型: {controller_type}")
        
        # 重新连接信号
        if hasattr(self, '_current_task_item'):
            self.device_combo.currentIndexChanged.connect(
                lambda: self._on_device_selected_in_resource_setting(self._current_task_item)
            )
            if self.device_combo.count() > 0 and self.device_combo.currentIndex() >= 0:
                self._on_device_selected_in_resource_setting(self._current_task_item)
