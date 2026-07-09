from typing import Any, Dict

from PySide6.QtWidgets import QVBoxLayout
from qfluentwidgets import BodyLabel

from app.core.core import ServiceCoordinator


class PreTaskSettingMixin:
    """
    PreTask 设置 Mixin - 提供预任务选项配置界面
    使用方法：在 OptionWidget 中使用多重继承添加此 mixin
    """

    option_page_layout: QVBoxLayout
    service_coordinator: ServiceCoordinator
    current_config: Dict[str, Any]

    def _init_pretask_settings(self):
        """初始化 PreTask 设置相关属性"""
        pass

    def _apply_pretask_settings_with_animation(self):
        """在动画回调中应用 PreTask 设置"""
        self._clear_options()
        self.option_area_card.show()

        form_structure = self.service_coordinator.option.get_form_structure()
        if not form_structure or form_structure.get("type") != "pretask":
            return

        entries = form_structure.get("entries", [])
        if not entries:
            empty = BodyLabel(self.tr("No pretask configured"))
            empty.setWordWrap(True)
            self.option_page_layout.addWidget(empty)
            self.set_description("", has_options=False)
            return

        flat_form: Dict[str, Any] = {}
        flat_config: Dict[str, Any] = {}
        for entry in entries:
            entry_idx = entry.get("index", 0)
            for opt in entry.get("options", []):
                key = opt["key"]
                flat_form[key] = opt["field"]
                option_name = opt.get("name", "")

        pretask_entries = self.current_config.get("pretask_entries", [])
        if isinstance(pretask_entries, list):
            for idx, entry_data in enumerate(pretask_entries):
                if isinstance(entry_data, dict):
                    entry_options = entry_data.get("options", {})
                    if isinstance(entry_options, dict):
                        for option_name, value in entry_options.items():
                            widget_key = f"entry_{idx}_{option_name}"
                            flat_config[widget_key] = value

        self.option_form_widget.build_from_structure(flat_form, flat_config)
        self._connect_option_signals()
        self._update_options_enabled()
