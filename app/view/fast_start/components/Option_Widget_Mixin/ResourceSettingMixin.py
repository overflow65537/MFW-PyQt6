from __future__ import annotations
from errno import EIDRM
from typing import Dict, Any
from PySide6.QtWidgets import QVBoxLayout
from anyio import Path
from qfluentwidgets import BodyLabel, ComboBox, LineEdit

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

    def __init__(self):
        """初始化资源设置Mixin"""
        self.resource_setting_widgets = {}
        # 构建控制器类型映射
        interface = get_interface_manager().get_interface()
        self.controller_type_mapping = {
            ctrl.get("label", ctrl.get("name", "")): {
                "name": ctrl.get("name", ""),
                "type": ctrl.get("type", ""),
            }
            for ctrl in interface.get("controller", [])
        }
        self.current_config = self.service_coordinator.option_service.current_options

    def create_resource_settings(self):
        """创建固定的资源设置UI"""
        logger.info("Creating resource settings UI...")
        self._clear_options()
        self._toggle_description(False)

        # 创建控制器选择下拉框
        self._create_controller_combobox()
        # 创建搜索设备下拉框
        self._create_search_option()
        # 创建ADB和Win32子选项
        self._create_adb_children_option()
        self._create_win32_children_option()
        # 默认隐藏所有子选项
        self._toggle_win32_children_option(False)
        self._toggle_adb_children_option(False)
        # 设置初始值为当前配置中的控制器类型
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
                # 阻断下拉框信号发送
                search_option.combo_box.blockSignals(True)
                search_option.combo_box.addItem("测试")
                search_option.combo_box.blockSignals(False)

                break

    def _create_controller_combobox(self):
        """创建控制器类型下拉框"""
        ctrl_label = BodyLabel(self.tr("Controller Type"))
        self.parent_layout.addWidget(ctrl_label)

        ctrl_combo = ComboBox()
        self.resource_setting_widgets["ctrl_combo"] = ctrl_combo
        ctrl_combo.addItems(list(self.controller_type_mapping))

        self.parent_layout.addWidget(ctrl_combo)
        ctrl_combo.currentTextChanged.connect(self._on_controller_type_changed)

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
            "adb_address",
            lambda text: self._on_child_option_changed("adb_address", text),
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
            "screencap_method",
            screencap_options,
            self._on_child_option_changed,
        )

        # 输入方式
        input_options = {
            "AdbShell": 1,
            "MinitouchAndAdbKey": 2,
            "Maatouch": 4,
            "EmulatorExtras": 8,
        }
        self._create_resource_combobox(
            self.tr("Input Method"),
            "input_method",
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
            "Seize": 1,
            "SendMessage": 2,
            "PostMessage": 4,
            "LegacyEvent": 8,
            "PostThreadMessage": 16,
        }

        # 鼠标输入方式
        self._create_resource_combobox(
            self.tr("Mouse Input Method"),
            "mouse_input_method",
            mouse_keyboard_options,
            self._on_child_option_changed,
        )
        # 键盘输入方式
        self._create_resource_combobox(
            self.tr("Keyboard Input Method"),
            "keyboard_input_method",
            mouse_keyboard_options,
            self._on_child_option_changed,
        )

        # 截图方式
        screencap_options = {
            "GDI": 1,
            "FramePool": 2,
            "DXGI_DesktopDup": 4,
            "DXGI_DesktopDup_Window": 8,
            "PrintWindow": 16,
            "ScreenDC": 32,
        }
        self._create_resource_combobox(
            self.tr("Screencap Method"),
            "win32_screencap_method",
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
                    "adb_address": "",
                    "emulator_path": "",
                    "emulator_params": "",
                    "wait_time": "",
                    "screencap_method": 1,
                    "input_method": 1,
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
                    "mouse_input_method": 1,
                    "keyboard_input_method": 1,
                    "win32_screencap_method": 1,
                },
            )
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
            "adb_address",
            "emulator_path",
            "emulator_params",
            "wait_time",
            "screencap_method",
            "input_method",
            "config",
        ]
        for widget_name in adb_widgets:
            # 显示/隐藏标签和控件
            for suffix in ["_label", ""]:
                full_name = f"{widget_name}{suffix}"
                if full_name in self.resource_setting_widgets:
                    self.resource_setting_widgets[full_name].setVisible(visible)

    # 填充新的子选项信息
    def _fill_children_option(self, controller_name):

        current_config = self.current_config[controller_name]
        for name, widget in self.resource_setting_widgets.items():
            if name.endswith("_label"):
                continue
            elif name in current_config:
                if isinstance(widget, (LineEdit, PathLineEdit)):
                    widget.setText(current_config[name])
                elif isinstance(widget, ComboBox):
                    VALUE_TO_INDEX = {1: 0, 2: 1, 4: 2, 8: 3, 16: 4, 32: 5, 64: 6}
                    widget.setCurrentIndex(VALUE_TO_INDEX[current_config[name]])

    def _toggle_win32_children_option(self, visible: bool):
        """控制Win32子选项的隐藏和显示"""
        win32_widgets = [
            "hwnd",
            "program_path",
            "program_params",
            "wait_launch_time",
            "mouse_input_method",
            "keyboard_input_method",
            "win32_screencap_method",
        ]
        for widget_name in win32_widgets:
            # 显示/隐藏标签和控件
            for suffix in ["_label", ""]:
                full_name = f"{widget_name}{suffix}"
                if full_name in self.resource_setting_widgets:
                    self.resource_setting_widgets[full_name].setVisible(visible)

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

        # 显示/隐藏对应的子选项
        if new_type == "adb":
            self._toggle_adb_children_option(True)
            self._toggle_win32_children_option(False)
        elif new_type == "win32":
            self._toggle_adb_children_option(False)
            self._toggle_win32_children_option(True)

    def _on_search_combo_changed(self, device_name):
        pass

    def _clear_options(self):
        """清空选项区域"""
        for widget in self.resource_setting_widgets.values():
            widget.deleteLater()
        self.resource_setting_widgets.clear()
        self.current_controller_type = None
