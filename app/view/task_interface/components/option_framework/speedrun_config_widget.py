from copy import deepcopy
from typing import Any, Dict, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFormLayout, QFrame, QHBoxLayout, QVBoxLayout, QWidget
from qfluentwidgets import (
    BodyLabel,
    ComboBox,
    SpinBox,
    SwitchButton,
    isDarkTheme,
    qconfig,
)

from app.core.service.task_service import DEFAULT_SPEEDRUN_CONFIG
from app.core.speedrun.config import normalize_speedrun_config
from app.view.task_interface.components.option_framework.animations import HeightAnimator


class SpeedrunConfigWidget(QWidget):
    """条件执行配置页"""

    config_changed = Signal(dict)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._config: Dict[str, Any] = deepcopy(DEFAULT_SPEEDRUN_CONFIG)
        self._updating = False
        self._init_ui()
        self.set_config(self._config, emit=False)

    def _init_ui(self) -> None:
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(12)

        title = BodyLabel(self.tr("Condition Execution"))
        title.setAlignment(Qt.AlignmentFlag.AlignLeft)
        title.setStyleSheet("font-size: 16px; font-weight: 600;")
        self.main_layout.addWidget(title)

        self._init_condition_section()
        self._init_run_count_section()
        self._init_weekday_section()
        self._init_month_day_section()
        self._init_after_time_section()
        self._init_execution_section()
        self._bind_signals()
        self._init_animators()
        self._hide_all_condition_sections()

    def _init_condition_section(self) -> None:
        condition_title = BodyLabel(self.tr("Condition"))
        condition_title.setStyleSheet("font-weight: 600;")
        self.main_layout.addWidget(condition_title)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        form.setFormAlignment(Qt.AlignmentFlag.AlignLeft)

        self.condition_combo = ComboBox(self)
        self.condition_combo.addItem(self.tr("Always"), userData="always")
        self.condition_combo.addItem(self.tr("Run Count"), userData="run_count")
        self.condition_combo.addItem(self.tr("Weekday"), userData="weekday")
        self.condition_combo.addItem(self.tr("Month Day"), userData="month_day")
        self.condition_combo.addItem(self.tr("After Time"), userData="after_time")
        form.addRow(self.tr("Condition Type"), self.condition_combo)
        self.main_layout.addLayout(form)

        config_title = BodyLabel(self.tr("Condition Configuration"))
        config_title.setStyleSheet("font-weight: 600;")
        self.main_layout.addWidget(config_title)

    def _init_run_count_section(self) -> None:
        container = QWidget(self)
        layout = QFormLayout(container)

        self.period_combo = ComboBox(self)
        self.period_combo.addItem(self.tr("Daily"), userData="daily")
        self.period_combo.addItem(self.tr("Weekly"), userData="weekly")
        self.period_combo.addItem(self.tr("Monthly"), userData="monthly")
        layout.addRow(self.tr("Period"), self.period_combo)

        self.count_spin = SpinBox(self)
        self.count_spin.setRange(1, 9999)
        self.count_spin.setValue(1)
        layout.addRow(self.tr("Run Count"), self.count_spin)

        self.refresh_hour_combo = self._build_hour_combo()
        layout.addRow(self.tr("Refresh Timeline"), self.refresh_hour_combo)

        self.run_count_section, self.run_count_line = self._wrap_with_indicator(container)
        self.main_layout.addWidget(self.run_count_section)

    def _init_weekday_section(self) -> None:
        container = QWidget(self)
        layout = QFormLayout(container)
        self.weekday_combo = ComboBox(self)
        weekdays = [
            (self.tr("Monday"), 1),
            (self.tr("Tuesday"), 2),
            (self.tr("Wednesday"), 3),
            (self.tr("Thursday"), 4),
            (self.tr("Friday"), 5),
            (self.tr("Saturday"), 6),
            (self.tr("Sunday"), 7),
        ]
        for label, value in weekdays:
            self.weekday_combo.addItem(label, userData=value)
        layout.addRow(self.tr("Weekday"), self.weekday_combo)
        self.weekday_section, self.weekday_line = self._wrap_with_indicator(container)
        self.main_layout.addWidget(self.weekday_section)

    def _init_month_day_section(self) -> None:
        container = QWidget(self)
        layout = QFormLayout(container)
        self.month_day_combo = ComboBox(self)
        for day in range(1, 32):
            self.month_day_combo.addItem(str(day), userData=day)
        layout.addRow(self.tr("Day"), self.month_day_combo)
        self.month_day_section, self.month_day_line = self._wrap_with_indicator(container)
        self.main_layout.addWidget(self.month_day_section)

    def _init_after_time_section(self) -> None:
        container = QWidget(self)
        layout = QFormLayout(container)
        self.after_hour_combo = self._build_hour_combo()
        layout.addRow(self.tr("Hour"), self.after_hour_combo)
        self.after_time_section, self.after_time_line = self._wrap_with_indicator(
            container
        )
        self.main_layout.addWidget(self.after_time_section)

    def _init_execution_section(self) -> None:
        execution_title = BodyLabel(self.tr("Execution"))
        execution_title.setStyleSheet("font-weight: 600;")
        self.main_layout.addWidget(execution_title)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        form.setFormAlignment(Qt.AlignmentFlag.AlignLeft)

        self.action_combo = ComboBox(self)
        self.action_combo.addItem(self.tr("Run"), userData="normal_run")
        self.action_combo.addItem(self.tr("Skip"), userData="skip")
        form.addRow(self.tr("Execution Type"), self.action_combo)
        self.main_layout.addLayout(form)

        config_title = BodyLabel(self.tr("Execution Configuration"))
        config_title.setStyleSheet("font-weight: 600;")
        self.main_layout.addWidget(config_title)

        config_form = QFormLayout()
        self.notify_switch = SwitchButton(self)
        self.notify_switch.setOnText(self.tr("Enabled"))
        self.notify_switch.setOffText(self.tr("Disabled"))
        config_form.addRow(self.tr("Notify"), self.notify_switch)

        self.external_notify_switch = SwitchButton(self)
        self.external_notify_switch.setOnText(self.tr("Enabled"))
        self.external_notify_switch.setOffText(self.tr("Disabled"))
        config_form.addRow(self.tr("External Notify"), self.external_notify_switch)
        self.main_layout.addLayout(config_form)

    def _build_hour_combo(self) -> ComboBox:
        combo = ComboBox(self)
        for hour in range(24):
            combo.addItem(f"{hour:02d}:00", userData=hour)
        return combo

    def _bind_signals(self) -> None:
        self.condition_combo.currentIndexChanged.connect(self._on_condition_changed)
        self.action_combo.currentIndexChanged.connect(self._on_value_changed)
        self.notify_switch.checkedChanged.connect(self._on_value_changed)
        self.external_notify_switch.checkedChanged.connect(self._on_value_changed)
        self.period_combo.currentIndexChanged.connect(self._on_value_changed)
        self.count_spin.valueChanged.connect(self._on_value_changed)
        self.refresh_hour_combo.currentIndexChanged.connect(self._on_value_changed)
        self.weekday_combo.currentIndexChanged.connect(self._on_value_changed)
        self.month_day_combo.currentIndexChanged.connect(self._on_value_changed)
        self.after_hour_combo.currentIndexChanged.connect(self._on_value_changed)
        qconfig.themeChanged.connect(self._on_theme_changed)

    def set_config(self, config: Optional[Dict[str, Any]], emit: bool = True) -> None:
        merged = deepcopy(DEFAULT_SPEEDRUN_CONFIG)
        if isinstance(config, dict):
            self._deep_merge(merged, config)
        merged = normalize_speedrun_config(merged)

        self._updating = True
        self._config = merged

        condition = merged.get("condition", {})
        if not isinstance(condition, dict):
            condition = {}
        action = merged.get("action", {})
        if not isinstance(action, dict):
            action = {}

        condition_type = str(condition.get("type", "run_count") or "run_count")
        self._set_combo_value(self.condition_combo, condition_type, 0)
        self._set_combo_value(self.action_combo, action.get("type", "normal_run"), 0)
        self.notify_switch.setChecked(bool(action.get("notify", False)))
        self.external_notify_switch.setChecked(
            bool(action.get("external_notify", False))
        )

        self._set_combo_value(self.period_combo, condition.get("period", "daily"), 0)
        self.count_spin.setValue(self._to_int(condition.get("count"), 1, 1))
        self._set_combo_value(
            self.refresh_hour_combo, self._to_hour(condition.get("refresh_hour")), 0
        )

        weekdays = condition.get("weekdays", [1])
        weekday = weekdays[0] if isinstance(weekdays, list) and weekdays else 1
        self._set_combo_value(self.weekday_combo, self._to_int(weekday, 1, 1), 0)

        days = condition.get("days", [1])
        day = days[0] if isinstance(days, list) and days else 1
        self._set_combo_value(self.month_day_combo, self._to_int(day, 1, 1), 0)
        self._set_combo_value(self.after_hour_combo, self._to_hour(condition.get("hour")), 0)

        self._update_condition_visibility(condition_type)
        self._updating = False

        if emit:
            self._emit_change()

    def get_config(self) -> Dict[str, Any]:
        return deepcopy(self._config)

    def set_runtime_state(
        self, state: Optional[Dict[str, Any]], speedrun_cfg: Optional[Dict[str, Any]]
    ) -> None:
        return

    def _collect_config(self) -> Dict[str, Any]:
        config = deepcopy(DEFAULT_SPEEDRUN_CONFIG)
        condition_type = str(self._get_combo_value(self.condition_combo, "run_count"))
        action_type = str(self._get_combo_value(self.action_combo, "skip"))
        period = str(self._get_combo_value(self.period_combo, "daily"))
        count = int(self.count_spin.value())
        refresh_hour = int(self._get_combo_value(self.refresh_hour_combo, 0))
        weekday = int(self._get_combo_value(self.weekday_combo, 1))
        day = int(self._get_combo_value(self.month_day_combo, 1))
        after_hour = int(self._get_combo_value(self.after_hour_combo, 0))

        config["enabled"] = True
        config["condition"].update(
            {
                "type": condition_type,
                "period": period,
                "count": count,
                "refresh_hour": refresh_hour,
                "weekdays": [weekday],
                "days": [day],
                "hour": after_hour,
            }
        )
        config["action"]["type"] = action_type
        config["action"]["notify"] = self.notify_switch.isChecked()
        config["action"]["external_notify"] = self.external_notify_switch.isChecked()

        config["mode"] = period
        config["run"]["count"] = count
        config["run"]["min_interval_hours"] = 0
        config["trigger"]["daily"]["hour_start"] = refresh_hour
        config["trigger"]["weekly"]["weekday"] = [weekday]
        config["trigger"]["weekly"]["hour_start"] = refresh_hour
        config["trigger"]["monthly"]["day"] = [day]
        config["trigger"]["monthly"]["hour_start"] = refresh_hour
        return config

    def _on_condition_changed(self, _: int) -> None:
        condition_type = str(self._get_combo_value(self.condition_combo, "run_count"))
        self._update_condition_visibility(condition_type)
        self._on_value_changed()

    def _on_value_changed(self, *args, **kwargs) -> None:  # type: ignore[override]
        if self._updating:
            return
        self._emit_change()

    def _emit_change(self) -> None:
        self._config = self._collect_config()
        self.config_changed.emit(deepcopy(self._config))

    def _update_condition_visibility(self, condition_type: str, animate: bool = True) -> None:
        targets = {
            "run_count": self.run_count_section,
            "weekday": self.weekday_section,
            "month_day": self.month_day_section,
            "after_time": self.after_time_section,
        }
        if condition_type not in targets:
            self._hide_all_condition_sections()
            return

        animators = getattr(self, "_condition_animators", {})
        for key, section in targets.items():
            is_target = key == condition_type
            animator = animators.get(key)
            if animate and animator:
                if is_target:
                    animator.expand()
                else:
                    animator.collapse()
            else:
                section.setVisible(is_target)
                section.setMaximumHeight(16777215 if is_target else 0)

    def _hide_all_condition_sections(self) -> None:
        sections = [
            self.run_count_section,
            self.weekday_section,
            self.month_day_section,
            self.after_time_section,
        ]
        for section in sections:
            section.setMaximumHeight(0)
            section.setVisible(False)

    def _init_animators(self) -> None:
        self._condition_animators = {
            "run_count": HeightAnimator(self.run_count_section, duration=200, parent=self),
            "weekday": HeightAnimator(self.weekday_section, duration=200, parent=self),
            "month_day": HeightAnimator(self.month_day_section, duration=200, parent=self),
            "after_time": HeightAnimator(self.after_time_section, duration=200, parent=self),
        }

    def _wrap_with_indicator(self, inner: QWidget) -> tuple[QWidget, QFrame]:
        wrapper = QWidget(self)
        layout = QHBoxLayout(wrapper)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        line = QFrame(wrapper)
        line.setFrameShape(QFrame.Shape.VLine)
        line.setFrameShadow(QFrame.Shadow.Plain)
        line.setFixedWidth(3)
        self._set_indicator_color(line)
        layout.addWidget(line)
        layout.addWidget(inner, 1)
        wrapper.setVisible(False)
        wrapper.setMaximumHeight(0)
        return wrapper, line

    def _set_indicator_color(self, line: QFrame) -> None:
        if isDarkTheme():
            line.setStyleSheet(
                "QFrame { background-color: rgba(255, 255, 255, 0.3); border: none; border-radius: 1px; }"
            )
        else:
            line.setStyleSheet(
                "QFrame { background-color: rgba(0, 0, 0, 0.2); border: none; border-radius: 1px; }"
            )

    def _on_theme_changed(self):
        for line in [
            self.run_count_line,
            self.weekday_line,
            self.month_day_line,
            self.after_time_line,
        ]:
            self._set_indicator_color(line)

    def _deep_merge(self, target: Dict[str, Any], source: Dict[str, Any]) -> None:
        for key, value in source.items():
            if (
                key in target
                and isinstance(target[key], dict)
                and isinstance(value, dict)
            ):
                self._deep_merge(target[key], value)
            else:
                target[key] = deepcopy(value)

    def _set_combo_value(self, combo: ComboBox, value: Any, fallback_index: int = 0):
        matched = False
        for idx in range(combo.count()):
            if combo.itemData(idx) == value:
                combo.setCurrentIndex(idx)
                matched = True
                break
        if not matched:
            combo.setCurrentIndex(fallback_index if combo.count() else -1)

    def _get_combo_value(self, combo: ComboBox, default: Any = None) -> Any:
        idx = combo.currentIndex()
        if idx < 0:
            return default
        data = combo.itemData(idx)
        return data if data is not None else default

    def _to_int(self, value: Any, default: int, minimum: int = 0) -> int:
        try:
            number = int(value)
        except (TypeError, ValueError):
            number = default
        return max(minimum, number)

    def _to_hour(self, value: Any) -> int:
        try:
            hour = int(value)
        except (TypeError, ValueError):
            return 0
        return max(0, hour) % 24

