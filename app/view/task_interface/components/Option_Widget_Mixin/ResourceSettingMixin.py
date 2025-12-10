from typing import Dict, Any
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout
from PySide6.QtGui import QIcon, QPixmap, QIntValidator
from PySide6.QtCore import Qt
from qfluentwidgets import (
    BodyLabel,
    ComboBox,
    LineEdit,
    ToolTipFilter,
)
from pathlib import WindowsPath

import jsonc
from app.utils.gpu_cache import gpu_cache
from app.utils.logger import logger
from app.common.config import cfg
from app.core.core import ServiceCoordinator
from app.widget.PathLineEdit import PathLineEdit
from app.view.task_interface.components.Option_Widget_Mixin.DeviceFinderWidget import (
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
    WIN32_INPUT_METHOD_ALIAS_VALUES: Dict[str, int] = {
        "Seize": 1,
        "SendMessage": 2,
        "SendMessageWithCursorPos": 2,
        "PostMessage": 4,
        "PostMessageWithCursorPos": 4,
        "LegacyEvent": 8,
        "PostThreadMessage": 16,
    }
    WIN32_SCREENCAP_METHOD_ALIAS_VALUES: Dict[str, int] = {
        "GDI": 1,
        "FramePool": 2,
        "DXGI_DesktopDup": 4,
        "DXGI_DesktopDup_Window": 8,
        "PrintWindow": 16,
        "ScreenDC": 32,
    }

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

    def _coerce_int(self, value: Any) -> int | None:
        """尝试将值转换为整数，失败则返回 None"""
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _normalize_method_name(value: str) -> str:
        """将方法名标准化以便查找别名"""
        return "".join(ch.lower() for ch in value if ch.isalnum())

    def _normalize_alias_map(self, alias_map: Dict[str, int]) -> Dict[str, int]:
        """用标准化的键创建别名映射"""
        normalized_map: Dict[str, int] = {}
        for name, mapped_value in alias_map.items():
            normalized_key = self._normalize_method_name(name)
            if normalized_key:
                normalized_map[normalized_key] = mapped_value
        return normalized_map

    def _build_win32_method_alias_map(self) -> Dict[str, Dict[str, int]]:
        """构建 Win32 输入/截图方法别名映射"""
        input_aliases = self._normalize_alias_map(
            self.WIN32_INPUT_METHOD_ALIAS_VALUES
        )
        screencap_aliases = self._normalize_alias_map(
            self.WIN32_SCREENCAP_METHOD_ALIAS_VALUES
        )

        return {
            "input": input_aliases,
            "mouse": input_aliases,
            "keyboard": input_aliases,
            "screencap": screencap_aliases,
        }

    def _resolve_win32_setting_value(
        self, value: Any, method_type: str | None = None
    ) -> int | None:
        """尝试解析 controller 配置中的输入/截图方法值"""
        int_value = self._coerce_int(value)
        if int_value is not None:
            return int_value

        if method_type is None or not isinstance(value, str):
            return None

        alias_map = self.win32_method_alias_map.get(method_type.lower())
        if not alias_map:
            return None

        normalized_value = self._normalize_method_name(value)
        if not normalized_value:
            return None

        if (mapped := alias_map.get(normalized_value)) is not None:
            return mapped

        # 兜底：包含关键字的情况也能命中
        if method_type.lower() in {"input", "mouse", "keyboard"}:
            fallback_rules = (
                ("sendmessage", "sendmessage"),
                ("postmessage", "postmessage"),
                ("legacyevent", "legacyevent"),
                ("postthreadmessage", "postthreadmessage"),
                ("seize", "seize"),
            )
            for keyword, alias_key in fallback_rules:
                if keyword in normalized_value and alias_key in alias_map:
                    return alias_map[alias_key]

        return None

    def _find_win32_candidate_value(
        self,
        normalized: dict[str, Any],
        candidates: list[str],
        method_type: str | None = None,
    ) -> int | None:
        """从一组候选键中获取并转换整型值"""
        for candidate in candidates:
            candidate_key = candidate.lower()
            if candidate_key in normalized:
                value = self._resolve_win32_setting_value(
                    normalized[candidate_key], method_type
                )
                if value is not None:
                    return value
        return None

    def _build_win32_default_mapping(
        self, controllers: list[dict[str, Any]]
    ) -> dict[str, dict[str, Any]]:
        """构建 Win32 控制器的默认输入/截图映射"""
        win32_mapping: dict[str, dict[str, Any]] = {}
        for controller in controllers:
            if controller.get("type", "").lower() != "win32":
                continue
            controller_name = controller.get("name", "")
            if not controller_name:
                continue

            win32_config = controller.get("win32")
            if not isinstance(win32_config, dict):
                continue

            normalized = {
                str(key).lower(): value
                for key, value in win32_config.items()
                if isinstance(key, str)
            }

            mouse_value = self._find_win32_candidate_value(
                normalized, ["mouse_input", "mouse"], "mouse"
            )
            keyboard_value = self._find_win32_candidate_value(
                normalized, ["keyboard_input", "keyboard"], "keyboard"
            )
            general_input = self._find_win32_candidate_value(
                normalized, ["input", "input_method", "input_methods"], "input"
            )
            if mouse_value is None:
                mouse_value = general_input
            if keyboard_value is None:
                keyboard_value = general_input

            defaults: dict[str, int] = {}
            if mouse_value is not None:
                defaults["mouse_input_methods"] = mouse_value
            if keyboard_value is not None:
                defaults["keyboard_input_methods"] = keyboard_value

            screencap_value = self._find_win32_candidate_value(
                normalized,
                [
                    "screencap",
                    "screencap_method",
                    "screencap_methods",
                    "screenshot",
                    "screen_cap",
                ],
                "screencap",
            )
            if screencap_value is not None:
                defaults["win32_screencap_methods"] = screencap_value

            mapping_entry: dict[str, Any] = {"defaults": defaults}
            class_regex = normalized.get("class_regex")
            window_regex = normalized.get("window_regex")
            if class_regex:
                mapping_entry["class_regex"] = str(class_regex)
            if window_regex:
                mapping_entry["window_regex"] = str(window_regex)

            if defaults or "class_regex" in mapping_entry or "window_regex" in mapping_entry:
                win32_mapping[controller_name] = mapping_entry

        return win32_mapping

    def _ensure_defaults(self, controller_cfg: dict, defaults: dict):
        """确保指定键存在于控制器配置里"""
        for key, value in defaults.items():
            controller_cfg.setdefault(key, value)

    def _ensure_win32_input_defaults(self, controller_cfg: dict, controller_name: str):
        """为 Win32 控制器设置输入/截图默认值"""
        win32_defaults = self.win32_default_mapping.get(controller_name, {}).get(
            "defaults", {}
        )
        for key in [
            "mouse_input_methods",
            "keyboard_input_methods",
            "win32_screencap_methods",
        ]:
            controller_cfg.setdefault(key, win32_defaults.get(key, 0))

    def _get_win32_regex_filters(self, controller_name: str) -> tuple[str | None, str | None]:
        """获取 Win32 控制器的 class/window regex"""
        mapping_data = self.win32_default_mapping.get(controller_name, {})
        return (
            mapping_data.get("class_regex"),
            mapping_data.get("window_regex"),
        )

    def __init__(self):
        """初始化资源设置Mixin"""
        self._syncing = False  # 初始化/填充时屏蔽自动保存
        self.show_hide_option = bool(cfg.get(cfg.show_advanced_startup_options))
        self.resource_setting_widgets = {}

        # 当前控制器信息变量
        self.current_controller_label = None
        self.current_controller_name = None
        self.current_controller_type = None
        self.current_controller_info = None
        self.current_resource = None

        # 构建控制器类型映射
        interface = self.service_coordinator.interface
        self.controller_type_mapping = {
            ctrl.get("label", ctrl.get("name", "")): {
                "name": ctrl.get("name", ""),
                "type": ctrl.get("type", ""),
                "icon": ctrl.get("icon", ""),
                "description": ctrl.get("description", ""),
            }
            for ctrl in interface.get("controller", [])
        }
        self.win32_method_alias_map = self._build_win32_method_alias_map()
        self.win32_default_mapping = self._build_win32_default_mapping(
            interface.get("controller", [])
        )
        agent_interface_config = interface.get("agent", {})
        interface_custom = interface.get("custom")
        self.interface_custom_default = interface_custom if isinstance(interface_custom, str) else ""
        self.current_config = self.service_coordinator.option_service.current_options
        self.current_config.setdefault("gpu", -1)
        agent_timeout_default = self._coerce_int(agent_interface_config.get("timeout"))
        if agent_timeout_default is None:
            agent_timeout_default = 30
        self.agent_timeout_default = agent_timeout_default
        self.current_config.setdefault("agent_timeout", self.agent_timeout_default)
        self.current_config.setdefault("gpu", -1)
        if not isinstance(self.current_config.get("custom"), str):
            self.current_config["custom"] = self.interface_custom_default

        # 构建资源映射表
        self.resource_mapping = {
            ctrl.get("label", ctrl.get("name", "")): []
            for ctrl in interface.get("controller", [])
        }
        # 遍历每个资源，确定它支持哪些控制器
        for resource in interface.get("resource", []):
            supported_controllers = resource.get("controller")
            if not supported_controllers:
                # 未指定支持的控制器则默认对所有控制器生效
                for key in self.resource_mapping:
                    self.resource_mapping[key].append(resource)
                continue

            for controller in interface.get("controller", []):
                if controller.get("name", "") in supported_controllers:
                    label = controller.get("label", controller.get("name", ""))
                    self.resource_mapping[label].append(resource)

    def create_resource_settings(self):
        """创建固定的资源设置UI"""
        logger.info("Creating resource settings UI...")
        self._syncing = True
        try:
            self._clear_options()
            self._toggle_description(False)
            self.show_hide_option = bool(cfg.get(cfg.show_advanced_startup_options))

            # 创建控制器选择下拉框
            self._create_controller_combobox()
            # 创建资源选择下拉框
            self._create_resource_option()
            # 创建搜索设备下拉框
            self._create_search_option()
            # 创建GPU加速下拉框
            self._create_gpu_option()
            # 创建 agent 启动超时时间选项
            self._create_agent_timeout_option()
            # 创建自定义模块路径输入（隐藏选项）
            self._create_custom_option()
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
                    # 更新当前控制器信息变量
                    self.current_controller_label = label
                    self.current_controller_info = self.controller_type_mapping[label]
                    self.current_controller_name = self.current_controller_info["name"]
                    self.current_controller_type = self.current_controller_info[
                        "type"
                    ].lower()

                    # 填充信息
                    ctrl_combo: ComboBox = self.resource_setting_widgets["ctrl_combo"]
                    ctrl_combo.setCurrentIndex(idx)
                    self._on_controller_type_changed(label)  # 立即显示对应的子选项

                    # 更换搜索设备类型
        finally:
            self._syncing = False

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

    def _create_agent_timeout_option(self):
        """创建 Agent 启动超时时间输入"""
        timeout_label = BodyLabel(self.tr("Agent Timeout"))
        timeout_edit = LineEdit()
        timeout_validator = QIntValidator(-1, 2147483647, timeout_edit)
        timeout_edit.setValidator(timeout_validator)
        timeout_edit.setPlaceholderText(self.tr("-1 means infinite"))

        timeout_layout = QHBoxLayout()
        timeout_layout.addWidget(timeout_label)
        timeout_layout.addStretch()
        timeout_layout.addWidget(timeout_edit)
        self.parent_layout.addLayout(timeout_layout)

        self.resource_setting_widgets["agent_timeout_label"] = timeout_label
        self.resource_setting_widgets["agent_timeout"] = timeout_edit
        timeout_edit.textChanged.connect(self._on_agent_timeout_changed)

        self._toggle_children_visible(["agent_timeout"], self.show_hide_option)

    def _create_custom_option(self):
        """创建自定义模块路径输入"""
        self._create_resource_line_edit(
            self.tr("Custom Module Path"),
            "custom",
            self._on_custom_path_changed,
            True,
        )
        self._toggle_children_visible(["custom"], self.show_hide_option)

    def _create_gpu_option(self):
        """创建GPU加速下拉框"""
        gpu_label = BodyLabel(self.tr("GPU Acceleration"))
        self.parent_layout.addWidget(gpu_label)

        gpu_combo = ComboBox()
        self.parent_layout.addWidget(gpu_combo)

        self.resource_setting_widgets["gpu_combo_label"] = gpu_label
        self.resource_setting_widgets["gpu_combo"] = gpu_combo

        gpu_combo.currentIndexChanged.connect(self._on_gpu_option_changed)
        self._populate_gpu_combo_options()
        self._toggle_children_visible(["gpu_combo"], self.show_hide_option)

    def _populate_gpu_combo_options(self):
        combo: ComboBox | None = self.resource_setting_widgets.get("gpu_combo")
        if combo is None:
            return

        combo.blockSignals(True)
        combo.clear()
        combo.addItem(self.tr("Auto"), userData=-1)
        combo.addItem(self.tr("CPU"), userData=-2)

        gpu_info = gpu_cache.get_gpu_info()
        for gpu_id in sorted(gpu_info):
            gpu_name = gpu_info[gpu_id]
            combo.addItem(f"GPU {gpu_id}: {gpu_name}", userData=gpu_id)

        combo.blockSignals(False)

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
            "default": -1,
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
            "default": -1,
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
            "default": -1,
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
            "default": -1,
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
        if self._syncing:
            return
        # 确保当前控制器信息已初始化
        if not self.current_controller_name or not self.current_controller_type:
            # 从配置中重新获取控制器信息作为 fallback
            controller_name = self.current_config.get("controller_type", "")
            for key_ctrl, ctrl_info in self.controller_type_mapping.items():
                if ctrl_info["name"] == controller_name:
                    # 更新当前控制器信息变量
                    self.current_controller_label = key_ctrl
                    self.current_controller_info = ctrl_info
                    self.current_controller_name = ctrl_info["name"]
                    self.current_controller_type = ctrl_info["type"].lower()
                    break
            else:
                # 如果没有找到匹配的控制器，返回
                return

        # 使用当前控制器信息变量
        current_controller_name = self.current_controller_name
        current_controller_type = self.current_controller_type
        if current_controller_type == "adb":
            self.current_config[current_controller_name] = self.current_config.get(
                current_controller_name,
                {
                    "adb_path": "",
                    "address": "",
                    "emulator_path": "",
                    "emulator_params": "",
                    "wait_time": "30",  # 默认等待模拟器启动 30s
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
                    "wait_launch_time": "30",  # 默认等待程序启动 30s
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
        if self._syncing:
            return
        try:
            option_service = self.service_coordinator.option_service
            ok = option_service.update_options(self.current_config)
            # 强制同步到预配置任务，确保落盘
            from app.common.constants import PRE_CONFIGURATION

            task = option_service.task_service.get_task(PRE_CONFIGURATION)
            if task:
                task.task_option = self.current_config
                if not option_service.task_service.update_task(task):
                    logger.warning("资源设置强制保存失败")
            else:
                logger.warning("未找到 Pre-Configuration 任务，无法保存资源设置")

            if not ok:
                logger.warning("资源设置保存返回 False（已尝试强制保存）")
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
        """填充新的子选项信息"""
        controller_type = None
        self.current_config.setdefault("gpu", -1)
        for controller_info in self.controller_type_mapping.values():
            if controller_info["name"] == controller_name:
                controller_type = controller_info["type"].lower()
                break
        controller_cfg = self.current_config.setdefault(controller_name, {})
        if controller_type == "adb":
            adb_defaults = {
                "adb_path": "",
                "address": "",
                "emulator_path": "",
                "emulator_params": "",
                "wait_time": "30",  # 默认等待模拟器启动 30s
                "screencap_methods": 0,
                "input_methods": 0,
                "config": "{}",
            }
            self._ensure_defaults(controller_cfg, adb_defaults)
        elif controller_type == "win32":
            win32_defaults = {
                "hwnd": "",
                "program_path": "",
                "program_params": "",
                "wait_launch_time": "30",  # 默认等待程序启动 30s
            }
            self._ensure_defaults(controller_cfg, win32_defaults)
            self._ensure_win32_input_defaults(controller_cfg, controller_name)
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
        self._fill_custom_option()
        self._fill_gpu_option()
        self._fill_agent_timeout_option()
        # 填充设备名称
        device_name = self.current_config[controller_name].get(
            "device_name", self.tr("Unknown Device")
        )
        # 阻断下拉框信号发送
        search_option: DeviceFinderWidget = self.resource_setting_widgets[
            "search_combo"
        ]
        combo_box = search_option.combo_box
        combo_box.blockSignals(True)
        # 先尝试定位已有的设备项，避免重复添加
        target_index = next(
            (i for i in range(combo_box.count()) if combo_box.itemText(i) == device_name),
            -1,
        )
        if target_index == -1:
            combo_box.addItem(device_name)
            target_index = combo_box.count() - 1
        combo_box.setCurrentIndex(target_index)
        combo_box.blockSignals(False)

    def _fill_custom_option(self):
        custom_edit = self.resource_setting_widgets.get("custom")
        if isinstance(custom_edit, (LineEdit, PathLineEdit)):
            custom_edit.blockSignals(True)
            default_value = self.interface_custom_default
            current_value = self.current_config.get("custom", default_value)
            if current_value is None:
                current_value = default_value
            normalized_value = str(current_value) if current_value is not None else ""
            custom_edit.setText(normalized_value)
            custom_edit.blockSignals(False)
            self.current_config["custom"] = normalized_value

    def _fill_gpu_option(self):
        combo = self.resource_setting_widgets.get("gpu_combo")
        if combo is None:
            return
        self._populate_gpu_combo_options()

        combo.blockSignals(True)
        value = self.current_config.get("gpu", -1)
        try:
            value = int(value)
        except (TypeError, ValueError):
            value = -1

        target_index = 0
        for idx in range(combo.count()):
            if combo.itemData(idx) == value:
                target_index = idx
                break

        combo.setCurrentIndex(target_index)
        combo.blockSignals(False)

    def _fill_agent_timeout_option(self):
        timeout_edit = self.resource_setting_widgets.get("agent_timeout")
        if isinstance(timeout_edit, LineEdit):
            timeout_edit.blockSignals(True)
            timeout_value = self.current_config.get(
                "agent_timeout", self.agent_timeout_default
            )
            timeout_int = self._coerce_int(timeout_value)
            timeout_text = (
                str(timeout_int)
                if timeout_int is not None
                else str(self.agent_timeout_default)
            )
            timeout_edit.setText(timeout_text)
            timeout_edit.blockSignals(False)

    def _on_custom_path_changed(self, text: str):
        self.current_config["custom"] = text
        self._auto_save_options()

    def _on_agent_timeout_changed(self, text: str):
        if not text:
            return
        try:
            timeout_value = int(text)
        except ValueError:
            return
        self.current_config["agent_timeout"] = timeout_value
        self._auto_save_options()

    def _on_gpu_option_changed(self, index: int):
        combo = self.resource_setting_widgets.get("gpu_combo")
        if combo is None:
            return

        value = combo.itemData(index)
        try:
            value = int(value)
        except (TypeError, ValueError):
            value = -1

        self.current_config["gpu"] = value
        self._auto_save_options()

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
        self._toggle_children_visible(win32_hide_widgets, visible)

    def _on_controller_type_changed(self, label: str):
        """控制器类型变化时的处理函数"""
        # 更新当前控制器信息变量
        self.current_controller_label = label
        self.current_controller_info = self.controller_type_mapping[label]
        self.current_controller_name = self.current_controller_info["name"]
        self.current_controller_type = self.current_controller_info["type"].lower()

        ctrl_info = self.current_controller_info
        new_type = self.current_controller_type

        # 更新当前配置
        self.current_config["controller_type"] = ctrl_info["name"]
        self._auto_save_options()

        # 更换搜索设备类型
        search_option: DeviceFinderWidget = self.resource_setting_widgets[
            "search_combo"
        ]
        search_option.change_controller_type(new_type)
        if new_type == "win32":
            class_regex, window_regex = self._get_win32_regex_filters(
                ctrl_info["name"]
            )
            search_option.set_win32_filters(class_regex, window_regex)
        else:
            search_option.set_win32_filters(None, None)

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
        """资源变化时的处理函数"""
        if self._syncing:
            return
        # 更新当前资源信息变量
        self.current_resource = new_resource

        for resource in self.resource_mapping[self.current_controller_label]:
            if resource.get("label", resource.get("name", "")) == self.current_resource:
                self.current_config["resource"] = resource["name"]
                res_combo: ComboBox = self.resource_setting_widgets["resource_combo"]
                if description := resource.get("description"):
                    res_combo.installEventFilter(ToolTipFilter(res_combo))
                    res_combo.setToolTip(description)
                self._auto_save_options()
                break

    def _on_search_combo_changed(self, device_name):
        if self._syncing:
            return
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
        # 从布局中移除所有控件
        widgets_to_remove = list(self.resource_setting_widgets.values())
        
        # 遍历布局，找到并移除这些控件
        if hasattr(self, 'parent_layout'):
            items_to_remove = []
            for i in range(self.parent_layout.count()):
                item = self.parent_layout.itemAt(i)
                if item and item.widget() and item.widget() in widgets_to_remove:
                    items_to_remove.append(i)
            
            # 从后往前移除，避免索引问题
            for i in reversed(items_to_remove):
                item = self.parent_layout.takeAt(i)
                if item and item.widget():
                    widget = item.widget()
                    widget.hide()
                    widget.setParent(None)
                    widget.deleteLater()
        
        # 清理字典
        self.resource_setting_widgets.clear()
        self.current_controller_type = None

    def _fill_resource_option(self):
        """填充资源选项"""
        resource_combo: ComboBox = self.resource_setting_widgets["resource_combo"]
        resource_combo.clear()

        # 使用当前控制器信息变量
        curren_config = self.resource_mapping[self.current_controller_label]
        for resource in curren_config:
            icon = resource.get("icon", "")
            resource_label = resource.get("label", resource.get("name", ""))
            resource_combo.addItem(resource_label, icon)

        # 根据 current_config 中的 resource 选择对应项
        target = self.current_config.get("resource", "")
        target_label = None
        for resource in curren_config:
            name = resource.get("name", "")
            label = resource.get("label", name)
            if target and target in (name, label):
                target_label = label
                break
        resource_combo.blockSignals(True)
        if target_label:
            idx = resource_combo.findText(target_label)
            if idx >= 0:
                resource_combo.setCurrentIndex(idx)
        resource_combo.blockSignals(False)
