from typing import Dict, Any
from PySide6.QtWidgets import QVBoxLayout
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtCore import Qt
from qfluentwidgets import BodyLabel, ComboBox, LineEdit, ToolTipPosition, ToolTipFilter
from pathlib import WindowsPath

import jsonc
from app.utils.logger import logger
from app.core.core import ServiceCoordinator
from app.core.service.interface_manager import get_interface_manager
from app.widget.PathLineEdit import PathLineEdit
from app.view.fast_start.components.Option_Widget_Mixin.DeviceFinderWidget import (
    DeviceFinderWidget,
)


class ResourceSettingMixin:
    """
    资源设置生成的Mixin组件 - 固定UI实现
    """

    service_coordinator: ServiceCoordinator
    parent_layout: QVBoxLayout

    resource_setting_widgets: Dict[str, Any]
    CHILD = [300, 300]

    def _toggle_description(self, visible: bool) -> None: ...
    def tr(
        self, sourceText: str, /, disambiguation: str | None = ..., n: int = ...
    ) -> str: ...

    def _value_to_index(self, value: int) -> int:
        """将值转换为下拉框的索引"""
        value_mapping = {
            1: 1,
            2: 2,
            4: 3,
            8: 4,
            16: 5,
            32: 6,
            64: 7,
            128: 8,
        }
        return value_mapping.get(value, 0)  # 默认返回0如果值不存在

    def __init__(self):
        """初始化资源设置Mixin"""
        self.show_hide_option = False
        self.resource_setting_widgets = {}

        # 构建控制器类型映射
        interface = get_interface_manager().get_interface()
        self.controller_type_mapping = {
            ctrl.get("label", ctrl.get("name", "")): {
                "name": ctrl.get("name", ""),
                "type": ctrl.get("type", ""),
                "icon": ctrl.get("icon", ""),
                "description": ctrl.get("description", ""),
            }
            for ctrl in interface.get("controller", [])
        }
        self.current_config = self.service_coordinator.option_service.current_options

        # 构建资源映射表
        self.resource_mapping = {
            ctrl.get("label", ctrl.get("name", "")): []
            for ctrl in interface.get("controller", [])
        }
        # 遍历每个资源，确定它支持哪些控制器
        for resource in interface.get("resource", []):
            # 获取资源指定的支持控制器列表（如果有）
            for controller in interface.get("controller", []):
                if controller.get("name", "") in resource.get("controller", []):
                    self.resource_mapping[
                        controller.get("label", controller.get("name", ""))
                    ].append(resource)
                    break
                else:
                    for key, value in self.resource_mapping.items():
                        self.resource_mapping[key] = value + [resource]
                    break

    def create_resource_settings(self):
        """创建固定的资源设置UI"""
        logger.info("Creating resource settings UI...")
        self._clear_options()
        self._toggle_description(False)

        # 创建控制器选择下拉框
        self._create_controller_combobox()
        # 创建资源选择下拉框
        self._create_resource_option()
        # 创建搜索设备下拉框
        self._create_search_option()
        # 创建ADB和Win32子选项
        self._create_adb_children_option()
        self._create_win32_children_option()
        # 默认隐藏所有子选项
        self._toggle_win32_children_option(False)
        self._toggle_adb_children_option(False)
        # 设置初始值为当前配置中的控制器类型
        if self.current_config == {}:
            for key, value in self.controller_type_mapping.items():
                self.current_config["controller_type"] = value["name"]
                break

        for idx, label in enumerate(list(self.controller_type_mapping)):
            if self.controller_type_mapping[label]["name"] == self.current_config.get(
                "controller_type", ""
            ):
                # 填充信息
                ctrl_combo: ComboBox = self.resource_setting_widgets["ctrl_combo"]
                ctrl_combo.setCurrentIndex(idx)
                self._on_controller_type_changed(label)  # 立即显示对应的子选项

                # 更换搜索设备类型
                search_option: DeviceFinderWidget = self.resource_setting_widgets[
                    "search_combo"
                ]
                # controller = self.service_coordinator.option.current_options.get

                search_option.change_controller_type(
                    self.controller_type_mapping[label]["type"].lower()
                )
                device_name = self.current_config[
                    self.current_config["controller_type"]
                ].get("device_name", self.tr("Unknown Device"))
                # 阻断下拉框信号发送
                search_option.combo_box.blockSignals(True)
                search_option.combo_box.addItem(device_name)
                search_option.combo_box.blockSignals(False)
                break

    def _create_controller_combobox(self):
        """创建控制器类型下拉框"""
        ctrl_label = BodyLabel(self.tr("Controller Type"))
        self.parent_layout.addWidget(ctrl_label)

        ctrl_combo = ComboBox()
        self.resource_setting_widgets["ctrl_combo"] = ctrl_combo
        controller_list = list(self.controller_type_mapping)
        for label in controller_list:
            icon = ""
            if self.controller_type_mapping[label]["icon"]:
                icon = self.controller_type_mapping[label]["icon"]

            ctrl_combo.addItem(label, icon)

        self.parent_layout.addWidget(ctrl_combo)
        ctrl_combo.currentTextChanged.connect(self._on_controller_type_changed)

    def _create_resource_option(self):
        resource_label = BodyLabel(self.tr("Resource"))
        self.parent_layout.addWidget(resource_label)

        resource_combox = ComboBox()
        self.parent_layout.addWidget(resource_combox)
        self.resource_setting_widgets["resource_combo"] = resource_combox
        resource_combox.currentTextChanged.connect(self._on_resource_combox_changed)

    def _create_search_option(self):
        """创建搜索设备下拉框"""
        search_label = BodyLabel(self.tr("Search Device"))
        self.parent_layout.addWidget(search_label)

        search_combo = DeviceFinderWidget()
        self.resource_setting_widgets["search_combo"] = search_combo

        search_combo.combo_box.addItems(list(self.controller_type_mapping))

        self.parent_layout.addWidget(search_combo)
        search_combo.combo_box.currentTextChanged.connect(self._on_search_combo_changed)

    def _create_resource_line_edit(
        self,
        label_text: str,
        config_key: str,
        change_callback,
        path_lineedit: bool = False,
    ):
        """创建LineEdit组件的通用方法"""
        label = BodyLabel(label_text)
        self.parent_layout.addWidget(label)
        if path_lineedit:
            edit = PathLineEdit()
        else:
            edit = LineEdit()
        self.parent_layout.addWidget(edit)

        # 存储控件到字典 - 注意这里的键名保持不变，以便在_toggle方法中使用
        self.resource_setting_widgets[f"{config_key}_label"] = label
        self.resource_setting_widgets[config_key] = edit

        # 连接信号
        edit.textChanged.connect(change_callback)

    def _create_resource_combobox(
        self,
        label_text: str,
        config_key: str,
        options: dict,
        change_callback,
    ):
        """创建ComboBox组件的通用方法"""
        label = BodyLabel(label_text)
        self.parent_layout.addWidget(label)

        combo = ComboBox()

        for display, value in options.items():
            combo.addItem(f"{display} {value}", userData=value)

        self.parent_layout.addWidget(combo)

        # 存储控件到字典 - 注意这里的键名保持不变，以便在_toggle方法中使用
        self.resource_setting_widgets[f"{config_key}_label"] = label
        self.resource_setting_widgets[config_key] = combo

        # 连接信号
        combo.currentIndexChanged.connect(
            lambda index: change_callback(config_key, combo.itemData(index))
        )

    def _create_adb_children_option(self):
        """创建ADB子选项"""
        # ADB路径
        self._create_resource_line_edit(
            self.tr("ADB Path"),
            "adb_path",
            lambda text: self._on_child_option_changed("adb_path", text),
            True,
        )
        # ADB连接地址
        self._create_resource_line_edit(
            self.tr("ADB Address"),
            "address",
            lambda text: self._on_child_option_changed("address", text),
        )
        # 模拟器路径
        self._create_resource_line_edit(
            self.tr("Emulator Path"),
            "emulator_path",
            lambda text: self._on_child_option_changed("emulator_path", text),
            True,
        )
        # 模拟器参数
        self._create_resource_line_edit(
            self.tr("Emulator Params"),
            "emulator_params",
            lambda text: self._on_child_option_changed("emulator_params", text),
        )
        # 等待模拟器启动时间
        self._create_resource_line_edit(
            self.tr("Wait for Emulator StartUp Time"),
            "wait_time",
            lambda text: self._on_child_option_changed("wait_time", text),
        )

        # 截图方式
        screencap_options = {
            "Auto": 0,
            "EncodeToFileAndPull": 1,
            "Encode": 2,
            "RawWithGzip": 4,
            "RawByNetcat": 8,
            "MinicapDirect": 16,
            "MinicapStream": 32,
            "EmulatorExtras": 64,
        }
        self._create_resource_combobox(
            self.tr("Screencap Method"),
            "screencap_methods",
            screencap_options,
            self._on_child_option_changed,
        )

        # 输入方式
        input_options = {
            "Auto": 0,
            "AdbShell": 1,
            "MinitouchAndAdbKey": 2,
            "Maatouch": 4,
            "EmulatorExtras": 8,
        }
        self._create_resource_combobox(
            self.tr("Input Method"),
            "input_methods",
            input_options,
            self._on_child_option_changed,
        )

        # 特殊配置
        self._create_resource_line_edit(
            self.tr("Special Config"),
            "config",
            lambda text: self._on_child_option_changed("config", text),
        )

    def _create_win32_children_option(self):
        """创建Win32子选项"""
        # HWND
        self._create_resource_line_edit(
            "HWND",
            "hwnd",
            lambda text: self._on_child_option_changed("hwnd", text),
        )
        # 程序路径
        self._create_resource_line_edit(
            self.tr("Program Path"),
            "program_path",
            lambda text: self._on_child_option_changed("program_path", text),
            True,
        )
        # 程序参数
        self._create_resource_line_edit(
            self.tr("Program Params"),
            "program_params",
            lambda text: self._on_child_option_changed("program_params", text),
        )
        # 等待启动时间
        self._create_resource_line_edit(
            self.tr("Wait for Launch Time"),
            "wait_launch_time",
            lambda text: self._on_child_option_changed("wait_launch_time", text),
        )

        # 鼠标和键盘输入方式选项
        mouse_keyboard_options = {
            "Auto": 0,
            "Seize": 1,
            "SendMessage": 2,
            "PostMessage": 4,
            "LegacyEvent": 8,
            "PostThreadMessage": 16,
        }

        # 鼠标输入方式
        self._create_resource_combobox(
            self.tr("Mouse Input Method"),
            "mouse_input_methods",
            mouse_keyboard_options,
            self._on_child_option_changed,
        )
        # 键盘输入方式
        self._create_resource_combobox(
            self.tr("Keyboard Input Method"),
            "keyboard_input_methods",
            mouse_keyboard_options,
            self._on_child_option_changed,
        )

        # 截图方式
        screencap_options = {
            "Auto": 0,
            "GDI": 1,
            "FramePool": 2,
            "DXGI_DesktopDup": 4,
            "DXGI_DesktopDup_Window": 8,
            "PrintWindow": 16,
            "ScreenDC": 32,
        }
        self._create_resource_combobox(
            self.tr("Screencap Method"),
            "win32_screencap_methods",
            screencap_options,
            self._on_child_option_changed,
        )

    def _on_child_option_changed(self, key: str, value: Any):
        """子选项变化处理"""
        current_controller_name = self.controller_type_mapping[
            self.resource_setting_widgets["ctrl_combo"].currentText()
        ]["name"]
        current_controller_type = self.controller_type_mapping[
            self.resource_setting_widgets["ctrl_combo"].currentText()
        ]["type"].lower()
        if current_controller_type == "adb":
            self.current_config[current_controller_name] = self.current_config.get(
                current_controller_name,
                {
                    "adb_path": "",
                    "address": "",
                    "emulator_path": "",
                    "emulator_params": "",
                    "wait_time": "",
                    "screencap_methods": 1,
                    "input_methods": 1,
                    "config": "{}",
                },
            )

        elif current_controller_type == "win32":
            self.current_config[current_controller_name] = self.current_config.get(
                current_controller_name,
                {
                    "hwnd": "",
                    "program_path": "",
                    "program_params": "",
                    "wait_launch_time": "",
                    "mouse_input_methods": 0,
                    "keyboard_input_methods": 0,
                    "win32_screencap_methods": 0,
                },
            )
        # Parse JSON string back to dict for "config" key
        if key == "config":
            try:
                self.current_config[current_controller_name][key] = jsonc.loads(value)
            except (jsonc.JSONDecodeError, ValueError):
                # If parsing fails, keep the string as-is or use an empty dict
                self.current_config[current_controller_name][key] = value
        else:
            self.current_config[current_controller_name][key] = value
        self._auto_save_options()

    def _auto_save_options(self):
        """自动保存当前选项"""
        try:
            self.service_coordinator.option_service.update_options(self.current_config)
            logger.info(f"选项自动保存成功: {self.current_config}")
        except Exception as e:
            logger.error(f"自动保存选项失败: {e}")

    def _toggle_adb_children_option(self, visible: bool):
        """控制ADB子选项的隐藏和显示"""
        adb_widgets = [
            "adb_path",
            "address",
            "emulator_path",
            "emulator_params",
            "wait_time",
        ]
        adb_hide_widgets = [
            "screencap_methods",
            "input_methods",
            "config",
        ]
        self._toggle_children_visible(adb_widgets, visible)
        self._toggle_children_visible(
            adb_hide_widgets, (visible and self.show_hide_option)
        )

    # 填充新的子选项信息
    def _fill_children_option(self, controller_name):
        controller_type = None
        for controller_info in self.controller_type_mapping.values():
            if controller_info["name"] == controller_name:
                controller_type = controller_info["type"].lower()
                break
        if controller_type == "adb":
            self.current_config[controller_name] = self.current_config.get(
                controller_name,
                {
                    "adb_path": "",
                    "address": "",
                    "emulator_path": "",
                    "emulator_params": "",
                    "wait_time": "",
                    "screencap_methods": 0,
                    "input_methods": 0,
                    "config": "{}",
                },
            )

        elif controller_type == "win32":
            self.current_config[controller_name] = self.current_config.get(
                controller_name,
                {
                    "hwnd": "",
                    "program_path": "",
                    "program_params": "",
                    "wait_launch_time": "",
                    "mouse_input_methods": 1,
                    "keyboard_input_methods": 1,
                    "win32_screencap_methods": 1,
                },
            )
        else:
            raise
        for name, widget in self.resource_setting_widgets.items():
            if name.endswith("_label"):
                continue
            elif name in self.current_config[controller_name]:
                if isinstance(widget, (LineEdit, PathLineEdit)):
                    value = self.current_config[controller_name][name]
                    # Convert dict to JSON string
                    widget.setText(
                        jsonc.dumps(value) if isinstance(value, dict) else str(value)
                    )
                elif isinstance(widget, ComboBox):
                    target = self.current_config[controller_name][name]
                    widget.setCurrentIndex(self._value_to_index(target))
        # 填充设备名称
        device_name = self.current_config[controller_name].get(
            "device_name", self.tr("Unknown Device")
        )
        # 阻断下拉框信号发送
        search_option: DeviceFinderWidget = self.resource_setting_widgets[
            "search_combo"
        ]
        search_option.combo_box.blockSignals(True)
        search_option.combo_box.addItem(device_name)
        search_option.combo_box.blockSignals(False)

    def _toggle_win32_children_option(self, visible: bool):
        """控制Win32子选项的隐藏和显示"""
        win32_widgets = [
            "hwnd",
            "program_path",
            "program_params",
            "wait_launch_time",
        ]
        win32_hide_widgets = [
            "mouse_input_methods",
            "keyboard_input_methods",
            "win32_screencap_methods",
        ]
        self._toggle_children_visible(win32_widgets, visible)
        self._toggle_children_visible(
            win32_hide_widgets, (visible and self.show_hide_option)
        )

    def _on_controller_type_changed(self, label: str):
        """控制器类型变化时的处理函数"""
        ctrl_info = self.controller_type_mapping[label]
        new_type = ctrl_info["type"].lower()

        # 更新当前配置
        self.current_config["controller_type"] = ctrl_info["name"]
        self._auto_save_options()

        # 更换搜索设备类型
        search_option: DeviceFinderWidget = self.resource_setting_widgets[
            "search_combo"
        ]
        search_option.change_controller_type(new_type)

        # 填充新的信息
        self._fill_children_option(ctrl_info["name"])

        # 更换控制器描述
        ctrl_combox: ComboBox = self.resource_setting_widgets["ctrl_combo"]
        ctrl_combox.installEventFilter(ToolTipFilter(ctrl_combox))
        ctrl_combox.setToolTip(ctrl_info["description"])

        self._fill_resource_option()

        # 显示/隐藏对应的子选项
        if new_type == "adb":
            self._toggle_adb_children_option(True)
            self._toggle_win32_children_option(False)
        elif new_type == "win32":
            self._toggle_adb_children_option(False)
            self._toggle_win32_children_option(True)

    def _on_resource_combox_changed(self, new_resource):
        controller_label = None
        for key, controller in self.controller_type_mapping.items():
            if controller.get("name", "") == self.current_config["controller_type"]:
                controller_label = key
                break
        if controller_label is None:
            return

        for resource in self.resource_mapping[controller_label]:
            if resource.get("label", resource.get("name", "")) == new_resource:
                self.current_config["resource"] = resource["name"]
                self._auto_save_options()

    def _on_search_combo_changed(self, device_name):
        current_controller_name = self.current_config["controller_type"]
        current_controller_config = self.current_config[current_controller_name]
        find_device_info = self.resource_setting_widgets[
            "search_combo"
        ].device_mapping.get(device_name)
        if find_device_info is None:
            return
        for key, value in find_device_info.items():
            if isinstance(value, WindowsPath):
                value = str(value)
            current_controller_config[key] = value
        current_controller_config["device_name"] = device_name
        self._auto_save_options()
        self._fill_children_option(current_controller_name)

    def _toggle_children_visible(self, option_list: list, visible: bool):
        for widget_name in option_list:
            # 显示/隐藏标签和控件
            for suffix in ["_label", ""]:
                full_name = f"{widget_name}{suffix}"
                if full_name in self.resource_setting_widgets:
                    self.resource_setting_widgets[full_name].setVisible(visible)

    def _clear_options(self):
        """清空选项区域"""
        for widget in self.resource_setting_widgets.values():
            widget.deleteLater()
        self.resource_setting_widgets.clear()
        self.current_controller_type = None

    def _fill_resource_option(self):

        resource_combo: ComboBox = self.resource_setting_widgets["resource_combo"]
        resource_combo.clear()
        current_config_name = self.current_config["controller_type"]
        for controller in self.controller_type_mapping:
            if self.controller_type_mapping[controller]["name"] == current_config_name:
                curren_config = self.resource_mapping[controller]

                for resource in curren_config:
                    icon = resource.get("icon", "")
                    resource_label = resource.get("label", resource.get("name", ""))
                    resource_combo.addItem(resource_label, icon)
