from typing import Any, Dict, List, Tuple

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QVBoxLayout
from qfluentwidgets import BodyLabel, CheckBox, ComboBox, LineEdit

from app.core.core import ServiceCoordinator
from app.utils.logger import logger
from app.widget.PathLineEdit import PathLineEdit


class PostActionSettingMixin:
    """
    完成后操作设置 Mixin，提供固定 UI 与互斥逻辑。
    依赖宿主提供 service_coordinator、parent_layout、current_config、
    以及 _clear_options / _toggle_description 方法。
    """

    service_coordinator: ServiceCoordinator
    parent_layout: QVBoxLayout
    current_config: Dict[str, Any]

    def _clear_options(self) -> None: ...
    def _toggle_description(self, visible: bool | None = None) -> None: ...
    def tr(
        self, sourceText: str, /, disambiguation: str | None = ..., n: int = ...
    ) -> str: ...

    _CONFIG_KEY = "post_action"
    _ACTION_ORDER: List[str] = [
        "none",
        "shutdown",
        "close_emulator",
        "close_software",
        "run_other",
        "run_program",
    ]
    _PRIMARY_ACTIONS = {"none", "shutdown", "run_other"}
    _SECONDARY_ACTIONS = {"close_emulator", "close_software"}
    _OPTIONAL_ACTIONS = {"run_program"}
    _DEFAULT_STATE: Dict[str, Any] = {
        "none": True,
        "shutdown": False,
        "close_emulator": False,
        "close_software": False,
        "run_other": False,
        "run_program": False,
        "target_config": "",
        "program_path": "",
        "program_args": "",
    }

    def __init__(self):
        self.post_action_widgets: Dict[str, Any] = {}
        self._post_action_state: Dict[str, Any] = {}
        self._syncing = False

    def _get_action_label(self, action_key: str) -> str:
        """返回动作对应的可翻译文案"""
        mapping = {
            "none": self.tr("Do nothing"),
            "shutdown": self.tr("Shutdown"),
            "close_emulator": self.tr("Close emulator"),
            "close_software": self.tr("Close software"),
            "run_other": self.tr("Run other configuration"),
            "run_program": self.tr("Run other program"),
        }
        return mapping.get(action_key, action_key)

    # region UI 构建
    def create_post_action_setting(self) -> None:
        """创建完成后操作设置界面"""
        if not isinstance(self.parent_layout, QVBoxLayout):
            raise ValueError(
                self.tr("Parent layout is not set, cannot render post action options")
            )

        self._clear_options()
        self._toggle_description(False)
        self._ensure_state()

        self.post_action_widgets.clear()

        title = BodyLabel(self.tr("Finish"))
        self.parent_layout.addWidget(title)
        self.parent_layout.addSpacing(8)

        for action_key in self._ACTION_ORDER:
            checkbox = CheckBox(self._get_action_label(action_key))
            checkbox.toggled.connect(
                lambda checked, key=action_key: self._on_checkbox_changed(key, checked)
            )
            self.parent_layout.addWidget(checkbox)
            self.post_action_widgets[action_key] = checkbox

        self.parent_layout.addSpacing(12)
        combo_label = BodyLabel(self.tr("Select the configuration to run"))
        self.parent_layout.addWidget(combo_label)

        combo = ComboBox()
        for config_id, display_name in self._load_available_configs():
            combo.addItem(display_name, userData=config_id)
        combo.currentIndexChanged.connect(
            lambda index: self._on_other_config_changed(combo, index)
        )
        self.parent_layout.addWidget(combo)
        self.post_action_widgets["target_config"] = combo

        self._create_program_input_fields()
        self._apply_state_to_widgets()

    # endregion

    # region 状态 & 互斥逻辑
    def _ensure_state(self) -> None:
        """确保配置中存在完成后操作状态"""
        if not isinstance(self.current_config, dict):
            self.current_config = {}

        raw_state = self.current_config.get(self._CONFIG_KEY)
        if not isinstance(raw_state, dict):
            raw_state = {}

        merged = dict(self._DEFAULT_STATE)
        merged.update(raw_state)
        if merged.get("run_program"):
            merged["none"] = False
            merged["run_other"] = False
        if merged.get("none") or merged.get("run_other"):
            merged["run_program"] = False
        self.current_config[self._CONFIG_KEY] = merged
        self._post_action_state = merged

    def _apply_state_to_widgets(self) -> None:
        """同步状态到控件"""
        self._syncing = True
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
        self._syncing = False

    def _on_checkbox_changed(self, key: str, checked: bool) -> None:
        if self._syncing:
            return

        self._syncing = True
        self._post_action_state[key] = checked

        if checked:
            if key in self._PRIMARY_ACTIONS:
                self._set_allowed_actions({key})
                if key in {"run_other", "none"}:
                    self._deactivate_run_program_option()
            elif key in self._SECONDARY_ACTIONS:
                self._set_allowed_actions(self._SECONDARY_ACTIONS)
            elif key == "run_program":
                self._deactivate_conflicting_primary_for_program()

        self._update_combo_enabled_state()
        self._update_program_inputs_enabled()
        self._syncing = False
        self._save_state()

    def _set_allowed_actions(self, allowed: set[str]) -> None:
        """根据互斥规则重置复选框"""
        for action_key in self._PRIMARY_ACTIONS.union(self._SECONDARY_ACTIONS):
            if action_key in allowed:
                continue
            widget = self.post_action_widgets.get(action_key)
            if isinstance(widget, CheckBox):
                widget.setChecked(False)
            self._post_action_state[action_key] = False

    def _on_other_config_changed(self, combo: ComboBox, index: int) -> None:
        if self._syncing:
            return
        self._post_action_state["target_config"] = combo.itemData(index) or ""
        self._save_state()

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

    def _deactivate_conflicting_primary_for_program(self) -> None:
        """运行其他程序被选中时，关闭与其互斥的主动作（运行其他配置 / 无动作）"""
        for key in ("run_other", "none"):
            widget = self.post_action_widgets.get(key)
            if isinstance(widget, CheckBox):
                widget.setChecked(False)
            self._post_action_state[key] = False
        self._update_combo_enabled_state()

    def _deactivate_run_program_option(self) -> None:
        """主动作（运行其他配置 / 无动作）被选中时，关闭运行其他程序"""
        run_program_widget = self.post_action_widgets.get("run_program")
        if isinstance(run_program_widget, CheckBox):
            run_program_widget.setChecked(False)
        self._post_action_state["run_program"] = False
        self._update_program_inputs_enabled()

    def _create_program_input_fields(self) -> None:
        """创建运行其他程序的路径与参数输入框"""
        path_label = BodyLabel(self.tr("Program path"))
        self.parent_layout.addWidget(path_label)

        path_input = PathLineEdit()
        path_input.setPlaceholderText(self.tr("Select executable path"))
        path_input.textChanged.connect(
            lambda text: self._on_program_input_changed("program_path", text)
        )
        self.parent_layout.addWidget(path_input)

        args_label = BodyLabel(self.tr("Program arguments"))
        self.parent_layout.addWidget(args_label)

        args_input = LineEdit()
        args_input.setPlaceholderText(self.tr("Extra startup arguments"))
        args_input.textChanged.connect(
            lambda text: self._on_program_input_changed("program_args", text)
        )
        self.parent_layout.addWidget(args_input)

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
        if self._syncing:
            return
        self._post_action_state[key] = value
        self._save_state()

    # endregion

    # region 数据 & 持久化
    def _load_available_configs(self) -> List[Tuple[str, str]]:
        configs: List[Tuple[str, str]] = []
        config_service = getattr(self.service_coordinator, "config_service", None)
        if not config_service:
            return configs

        try:
            for info in config_service.list_configs():
                configs.append(
                    (
                        info.get("item_id", ""),
                        info.get("name", "") or self.tr("Unnamed Configuration"),
                    )
                )
        except Exception as exc:
            logger.error(f"加载配置列表失败: {exc}")
        return configs

    def _save_state(self) -> None:
        try:
            self.service_coordinator.option_service.update_options(self.current_config)
        except Exception as exc:
            logger.error(f"保存完成后操作配置失败: {exc}")

    # endregion
