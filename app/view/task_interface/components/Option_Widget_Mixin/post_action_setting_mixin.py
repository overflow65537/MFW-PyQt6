from typing import Any, Dict, List, Tuple

from qfluentwidgets import (
    BodyLabel,
    CheckBox,
    ComboBox,
    LineEdit,
    ToolTipFilter,
    ToolTipPosition,
)
from PySide6.QtWidgets import QVBoxLayout


from app.utils.logger import logger
from app.widget.path_line_edit import PathLineEdit

from app.core.core import ServiceCoordinator


class PostActionSettingMixin:
    """
    完成后操作设置 Mixin - 提供完成后操作设置功能
    使用方法：在 OptionWidget 中使用多重继承添加此 mixin
    """

    option_page_layout: QVBoxLayout
    service_coordinator: ServiceCoordinator

    _CONFIG_KEY = "post_action"
    _ALWAYS_RUN_KEY = "always_run"
    _ACTION_ORDER: List[str] = [
        "none",
        "close_controller",
        "run_program",
        # 一组互斥：切换其他配置 / 退出软件 / 关机
        "run_other",
        "close_software",
        "shutdown",
    ]
    _PRIMARY_ACTIONS = {"none", "shutdown", "run_other"}
    _SECONDARY_ACTIONS = {"close_controller", "close_software"}
    _OPTIONAL_ACTIONS = {"run_program"}
    _DEFAULT_STATE: Dict[str, Any] = {
        "none": True,
        "shutdown": False,
        "close_controller": False,
        "close_software": False,
        "run_other": False,
        "run_program": False,
        "always_run": False,
        "target_config": "",
        "program_path": "",
        "program_args": "",
    }

    _EXCLUSIVE_EXIT_GROUP = {"run_other", "close_software", "shutdown"}

    def tr(
        self, sourceText: str, /, disambiguation: str | None = None, n: int = -1
    ) -> str: ...

    def _init_post_action_settings(self):
        """初始化完成后操作设置相关属性"""
        if not hasattr(self, "post_action_widgets"):
            self.post_action_widgets: Dict[str, Any] = {}
        self._post_action_syncing = False
        if not hasattr(self, "_post_action_state"):
            self._post_action_state: Dict[str, Any] = {}

    def _get_action_label(self, action_key: str) -> str:
        """返回动作对应的可翻译文案"""
        mapping = {
            "none": self.tr("Do nothing"),
            "shutdown": self.tr("Shutdown"),
            "close_controller": self.tr("Close controller"),
            "close_software": self.tr("Close software"),
            "run_other": self.tr("Run other configuration"),
            "run_program": self.tr("Run other program"),
        }
        return mapping.get(action_key, action_key)

    # region UI 构建
    def create_post_action_settings(self) -> None:
        """创建完成后操作设置界面"""
        if not hasattr(self, "option_page_layout"):
            raise ValueError(
                self.tr(
                    "option_page_layout is not set, cannot render post action options"
                )
            )

        # 注意：_clear_options() 和 _toggle_description(False) 已经在 _apply_post_action_settings_with_animation 中调用
        # 这里不再重复调用，避免重复清理导致问题
        self._ensure_post_action_state()

        self.post_action_widgets.clear()

        title = BodyLabel(self.tr("Finish"))
        self.option_page_layout.addWidget(title)
        self.option_page_layout.addSpacing(8)

        # 独立开关：不参与任何互斥逻辑
        always_run = CheckBox(self.tr("always run"))
        always_run.toggled.connect(self._on_post_action_always_run_changed)
        always_run.installEventFilter(
            ToolTipFilter(always_run, 0, ToolTipPosition.TOP)
        )
        always_run.setToolTip(self.tr("Whether to run the post-action regardless of success or failure"))
        self.option_page_layout.addWidget(always_run)
        self.post_action_widgets[self._ALWAYS_RUN_KEY] = always_run
        self.option_page_layout.addSpacing(8)

        for action_key in self._ACTION_ORDER:
            checkbox = CheckBox(self._get_action_label(action_key))
            checkbox.toggled.connect(
                lambda checked, key=action_key: self._on_post_action_checkbox_changed(
                    key, checked
                )
            )
            self.option_page_layout.addWidget(checkbox)
            self.post_action_widgets[action_key] = checkbox

        self.option_page_layout.addSpacing(12)
        combo_label = BodyLabel(self.tr("Select the configuration to run"))
        self.option_page_layout.addWidget(combo_label)

        combo = ComboBox()
        for config_id, display_name in self._load_available_configs():
            combo.addItem(display_name, userData=config_id)
        combo.currentIndexChanged.connect(
            lambda index: self._on_other_config_changed(combo, index)
        )
        self.option_page_layout.addWidget(combo)
        self.post_action_widgets["target_config"] = combo

        self._create_program_input_fields()
        self._apply_post_action_state_to_widgets()

    # endregion

    # region 状态 & 互斥逻辑
    def _ensure_post_action_state(self) -> None:
        """确保配置中存在完成后操作状态"""
        if not isinstance(self.current_config, dict):
            self.current_config = {}

        raw_state = self.current_config.get(self._CONFIG_KEY)
        merged = self.service_coordinator.normalize_post_action_state(raw_state)

        self.current_config[self._CONFIG_KEY] = merged
        self._post_action_state = merged

    def _apply_post_action_state_to_widgets(self) -> None:
        """同步状态到控件"""
        self._post_action_syncing = True
        always_run = self.post_action_widgets.get(self._ALWAYS_RUN_KEY)
        if isinstance(always_run, CheckBox):
            always_run.setChecked(
                bool(self._post_action_state.get(self._ALWAYS_RUN_KEY))
            )

        for action_key in self._PRIMARY_ACTIONS.union(self._SECONDARY_ACTIONS).union(
            self._OPTIONAL_ACTIONS
        ):
            widget = self.post_action_widgets.get(action_key)
            if isinstance(widget, CheckBox):
                widget.setChecked(bool(self._post_action_state.get(action_key)))

        combo = self.post_action_widgets.get("target_config")
        if isinstance(combo, ComboBox):
            target = self._post_action_state.get("target_config", "")
            target_index = combo.findData(target)
            if target_index < 0 and target:
                combo.addItem(self.tr("Unknown config"), userData=target)
                target_index = combo.findData(target)

            combo.blockSignals(True)
            combo.setCurrentIndex(target_index if target_index >= 0 else 0)
            combo.blockSignals(False)
            combo.setEnabled(bool(self._post_action_state.get("run_other")))

        self._apply_program_inputs_state()
        self._update_program_inputs_enabled()
        self._post_action_syncing = False

    def _on_post_action_always_run_changed(self, checked: bool) -> None:
        """独立开关：始终运行完成后动作（不参与互斥）"""
        if self._post_action_syncing:
            return
        self._post_action_state[self._ALWAYS_RUN_KEY] = checked
        self._save_post_action_state()

    def _on_post_action_checkbox_changed(self, key: str, checked: bool) -> None:
        if self._post_action_syncing:
            return

        self._post_action_state = self.service_coordinator.apply_post_action_toggle(
            self._post_action_state,
            key,
            checked,
        )
        self.current_config[self._CONFIG_KEY] = dict(self._post_action_state)
        self._apply_post_action_state_to_widgets()
        self._save_post_action_state()

    def _on_other_config_changed(self, combo: ComboBox, index: int) -> None:
        if self._post_action_syncing:
            return
        self._post_action_state["target_config"] = combo.itemData(index) or ""
        self._save_post_action_state()

    def _update_combo_enabled_state(self) -> None:
        combo = self.post_action_widgets.get("target_config")
        if not isinstance(combo, ComboBox):
            return

        enabled = bool(self._post_action_state.get("run_other"))
        combo.setEnabled(enabled)
        if enabled and not self._post_action_state.get("target_config"):
            # 自动选择第一个有效配置
            for idx in range(combo.count()):
                data = combo.itemData(idx)
                if data:
                    combo.blockSignals(True)
                    combo.setCurrentIndex(idx)
                    combo.blockSignals(False)
                    self._post_action_state["target_config"] = data
                    break
        elif not enabled:
            combo.blockSignals(True)
            if combo.count() > 0:
                combo.setCurrentIndex(0)
            combo.blockSignals(False)
            self._post_action_state["target_config"] = ""

    def _create_program_input_fields(self) -> None:
        """创建运行其他程序的路径与参数输入框"""
        path_label = BodyLabel(self.tr("Program path"))
        self.option_page_layout.addWidget(path_label)

        # PathLineEdit 未传 file_filter 时使用内置跨平台默认（Windows: .exe+全部，macOS/Linux: 全部）
        path_input = PathLineEdit()
        path_input.setPlaceholderText(self.tr("Select executable path"))
        path_input.textChanged.connect(
            lambda text: self._on_program_input_changed("program_path", text)
        )
        self.option_page_layout.addWidget(path_input)

        args_label = BodyLabel(self.tr("Program arguments"))
        self.option_page_layout.addWidget(args_label)

        args_input = LineEdit()
        args_input.setPlaceholderText(self.tr("Extra startup arguments"))
        args_input.textChanged.connect(
            lambda text: self._on_program_input_changed("program_args", text)
        )
        self.option_page_layout.addWidget(args_input)

        self.post_action_widgets["program_path_label"] = path_label
        self.post_action_widgets["program_path"] = path_input
        self.post_action_widgets["program_args_label"] = args_label
        self.post_action_widgets["program_args"] = args_input

    def _apply_program_inputs_state(self) -> None:
        """根据状态填充程序路径与参数"""
        path_widget = self.post_action_widgets.get("program_path")
        if isinstance(path_widget, PathLineEdit):
            path_widget.blockSignals(True)
            path_widget.setText(self._post_action_state.get("program_path", ""))
            path_widget.blockSignals(False)

        args_widget = self.post_action_widgets.get("program_args")
        if isinstance(args_widget, LineEdit):
            args_widget.blockSignals(True)
            args_widget.setText(self._post_action_state.get("program_args", ""))
            args_widget.blockSignals(False)

    def _update_program_inputs_enabled(self) -> None:
        """根据开关控制输入框可用状态"""
        enabled = bool(self._post_action_state.get("run_program"))
        for key in (
            "program_path_label",
            "program_path",
            "program_args_label",
            "program_args",
        ):
            widget = self.post_action_widgets.get(key)
            if widget:
                widget.setEnabled(enabled)

    def _on_program_input_changed(self, key: str, value: str) -> None:
        if self._post_action_syncing:
            return
        self._post_action_state[key] = value
        self._save_post_action_state()

    # endregion

    # region 数据 & 持久化
    def _load_available_configs(self) -> List[Tuple[str, str]]:
        try:
            configs: List[Tuple[str, str]] = []
            for config_id, display_name in self.service_coordinator.config_query.get_available_config_choices():
                configs.append(
                    (
                        config_id,
                        display_name or self.tr("Unnamed Configuration"),
                    )
                )
            return configs
        except Exception as exc:
            logger.error(f"加载配置列表失败: {exc}")
        return []

    def _save_post_action_state(self) -> None:
        try:
            # 仅写入 post_action 片段，避免携带无关字段导致覆盖
            payload = dict(self._post_action_state)
            self.current_config[self._CONFIG_KEY] = payload
            ok = self.service_coordinator.update_selected_option(self._CONFIG_KEY, payload)
            if not ok:
                if not self.service_coordinator.save_post_action_option(
                    self._CONFIG_KEY, payload
                ):
                    logger.warning("未找到 Post-Action 任务，无法保存完成后操作配置")
        except Exception as exc:
            logger.error(f"保存完成后操作配置失败: {exc}")

    # endregion

