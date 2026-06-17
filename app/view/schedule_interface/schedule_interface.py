from __future__ import annotations

import sys
from datetime import datetime
from functools import partial
from typing import Any
from uuid import uuid4

from PySide6.QtCore import QDateTime, Qt
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QFormLayout,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    BodyLabel,
    CaptionLabel,
    RadioButton,
    CheckBox,
    ComboBox,
    FluentIcon as FIF,
    PrimaryPushButton,
    SimpleCardWidget,
    SpinBox,
    ScrollArea,
    TableWidget,
    TransparentToolButton,
    ZhDatePicker,
    TimePicker,
)

from app.common.fluent_tooltip import apply_fluent_tooltip
from app.common.signal_bus import signalBus
from app.core.core import ServiceCoordinator
from app.core.service.schedule_service import (
    SCHEDULE_DAILY,
    SCHEDULE_MONTHLY,
    SCHEDULE_SINGLE,
    SCHEDULE_WEEKLY,
    ScheduleEntry,
)


class ZhDateTimeInput(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        self.date_picker = ZhDatePicker(self)
        self.date_picker.setSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed
        )

        self.time_picker = TimePicker(self)
        self.time_picker.setSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed
        )

        layout.addWidget(self.date_picker)
        layout.addWidget(self.time_picker)

    def dateTime(self) -> datetime:
        qdate = self.date_picker.getDate()
        qtime = self.time_picker.getTime()
        return datetime(
            qdate.year(),
            qdate.month(),
            qdate.day(),
            qtime.hour(),
            qtime.minute(),
        )

    def setDateTime(self, qdatetime: QDateTime) -> None:
        self.date_picker.setDate(qdatetime.date())
        self.time_picker.setTime(qdatetime.time())


class ScheduleInterface(QWidget):
    def __init__(self, service_coordinator: ServiceCoordinator, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("ScheduleInterface")
        self.service_coordinator = service_coordinator
        self.schedule_service = service_coordinator.schedule_service
        self._config_map: dict[str, str] = {}
        self._schedule_entries: list[ScheduleEntry] = []
        self._setup_ui()
        self._connect_signals()
        self._refresh_config_selector()
        self._refresh_schedule_table(self.schedule_service.get_schedules())

    def _setup_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.scroll_area = ScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setStyleSheet("background: transparent; border: none;")

        self.scroll_content = QWidget()
        self.scroll_content.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.scroll_content.setStyleSheet("background: transparent;")
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setContentsMargins(24, 24, 24, 24)
        self.scroll_layout.setSpacing(16)
        self.scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.scroll_layout.addWidget(self._create_schedule_form_card())
        self.scroll_layout.addWidget(self._create_schedule_list_card())

        self.scroll_area.setWidget(self.scroll_content)
        main_layout.addWidget(self.scroll_area)

    def _connect_signals(self) -> None:
        self.schedule_service.schedules_changed.connect(self._refresh_schedule_table)
        self.service_coordinator.signals.config_changed.connect(
            lambda _: self._refresh_config_selector()
        )
        self.trigger_group.buttonClicked.connect(self._on_trigger_button_clicked)
        self.add_button.clicked.connect(self._on_add_schedule)

    def _make_form_layout(self) -> QFormLayout:
        form = QFormLayout()
        form.setLabelAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        form.setFormAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop
        )
        form.setFieldGrowthPolicy(
            QFormLayout.FieldGrowthPolicy.FieldsStayAtSizeHint
        )
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(10)
        return form

    def _schedule_info_text(self) -> str:
        if sys.platform == "win32":
            return self.tr("schedule_interface_info_windows")
        if sys.platform == "darwin":
            return self.tr("schedule_interface_info_macos")
        if sys.platform.startswith("linux"):
            return self.tr("schedule_interface_info_linux")
        return self.tr("schedule_interface_info")

    def _create_schedule_form_card(self) -> SimpleCardWidget:
        card = SimpleCardWidget()
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(16)

        title = BodyLabel(self.tr("Add schedule"))
        title.setStyleSheet("font-weight: 600; font-size: 16px;")
        card_layout.addWidget(title)

        info_label = CaptionLabel(self._schedule_info_text())
        info_label.setWordWrap(True)
        card_layout.addWidget(info_label)

        config_form = self._make_form_layout()
        self.config_selector = ComboBox()
        self.config_selector.setPlaceholderText(self.tr("Select configuration"))
        self.config_selector.setMinimumWidth(280)
        config_form.addRow(self.tr("Configuration"), self.config_selector)
        card_layout.addLayout(config_form)

        type_label = BodyLabel(self.tr("Trigger type"))
        type_label.setStyleSheet("font-weight: 600;")
        card_layout.addWidget(type_label)

        self.trigger_group = QButtonGroup(self)
        self._trigger_types = (
            (self.tr("Single"), SCHEDULE_SINGLE),
            (self.tr("Daily"), SCHEDULE_DAILY),
            (self.tr("Weekly"), SCHEDULE_WEEKLY),
            (self.tr("Monthly"), SCHEDULE_MONTHLY),
        )
        trigger_row = QHBoxLayout()
        trigger_row.setSpacing(16)
        for idx, (label, _) in enumerate(self._trigger_types):
            radio = RadioButton(label)
            self.trigger_group.addButton(radio, idx)
            trigger_row.addWidget(radio)
        trigger_row.addStretch()
        card_layout.addLayout(trigger_row)

        timing_label = BodyLabel(self.tr("Timing"))
        timing_label.setStyleSheet("font-weight: 600;")
        card_layout.addWidget(timing_label)

        self.detail_container = QWidget()
        self.detail_layout = QVBoxLayout(self.detail_container)
        self.detail_layout.setContentsMargins(0, 0, 0, 0)
        self.detail_layout.setSpacing(0)
        self._detail_pages = [
            self._build_single_trigger_widget(),
            self._build_daily_trigger_widget(),
            self._build_weekly_trigger_widget(),
            self._build_monthly_trigger_widget(),
        ]
        for page in self._detail_pages:
            self.detail_layout.addWidget(page)
            page.hide()
        card_layout.addWidget(self.detail_container)

        button = self.trigger_group.button(0)
        if button:
            button.setChecked(True)
        self._switch_schedule_detail()

        control_layout = QHBoxLayout()
        control_layout.setSpacing(24)
        self.force_checkbox = CheckBox(self.tr("Force start"))
        self.enabled_checkbox = CheckBox(self.tr("Enabled"))
        self.enabled_checkbox.setChecked(True)
        control_layout.addWidget(self.force_checkbox)
        control_layout.addWidget(self.enabled_checkbox)
        control_layout.addStretch()
        card_layout.addLayout(control_layout)

        self.add_button = PrimaryPushButton(self.tr("Add schedule"))
        self.add_button.setFixedHeight(36)
        card_layout.addWidget(self.add_button)

        return card

    def _build_datetime_control(self) -> ZhDateTimeInput:
        datetime_input = ZhDateTimeInput()
        datetime_input.setDateTime(self._default_qdatetime())
        return datetime_input

    def _default_qdatetime(self) -> QDateTime:
        return QDateTime.currentDateTime().addSecs(60)

    def _build_single_trigger_widget(self) -> QWidget:
        widget = QWidget()
        layout = self._make_form_layout()
        widget.setLayout(layout)

        self.single_datetime = self._build_datetime_control()
        layout.addRow(self.tr("Start"), self.single_datetime)
        return widget

    def _build_daily_trigger_widget(self) -> QWidget:
        widget = QWidget()
        layout = self._make_form_layout()
        widget.setLayout(layout)

        self.daily_datetime = self._build_datetime_control()
        self.daily_interval_spin = SpinBox()
        self.daily_interval_spin.setRange(1, 365)
        self.daily_interval_spin.setValue(1)
        self.daily_interval_spin.setFixedWidth(96)

        interval_row = QHBoxLayout()
        interval_row.setContentsMargins(0, 0, 0, 0)
        interval_row.setSpacing(8)
        interval_row.addWidget(self.daily_interval_spin)
        interval_row.addWidget(BodyLabel(self.tr("days")))
        interval_row.addStretch()

        interval_widget = QWidget()
        interval_widget.setLayout(interval_row)

        layout.addRow(self.tr("Start"), self.daily_datetime)
        layout.addRow(self.tr("Every"), interval_widget)
        return widget

    def _build_weekly_trigger_widget(self) -> QWidget:
        widget = QWidget()
        outer = QVBoxLayout(widget)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(12)

        form = self._make_form_layout()
        self.weekly_datetime = self._build_datetime_control()
        self.weekly_interval_spin = SpinBox()
        self.weekly_interval_spin.setRange(1, 52)
        self.weekly_interval_spin.setValue(1)
        self.weekly_interval_spin.setFixedWidth(96)

        interval_row = QHBoxLayout()
        interval_row.setContentsMargins(0, 0, 0, 0)
        interval_row.setSpacing(8)
        interval_row.addWidget(self.weekly_interval_spin)
        interval_row.addWidget(BodyLabel(self.tr("weeks")))
        interval_row.addStretch()
        interval_widget = QWidget()
        interval_widget.setLayout(interval_row)

        form.addRow(self.tr("Start"), self.weekly_datetime)
        form.addRow(self.tr("Every"), interval_widget)
        outer.addLayout(form)

        weekday_label = BodyLabel(self.tr("Weekdays"))
        weekday_label.setStyleSheet("font-weight: 600;")
        outer.addWidget(weekday_label)
        outer.addLayout(self._build_weekday_grid())
        return widget

    def _build_monthly_trigger_widget(self) -> QWidget:
        widget = QWidget()
        outer = QVBoxLayout(widget)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(12)

        form = self._make_form_layout()
        self.monthly_datetime = self._build_datetime_control()
        form.addRow(self.tr("Start"), self.monthly_datetime)

        self.monthly_month_combo = ComboBox()
        self.monthly_month_combo.addItem(self.tr("Every month"), userData=0)
        for month in range(1, 13):
            self.monthly_month_combo.addItem(
                self.tr(
                    (
                        "January",
                        "February",
                        "March",
                        "April",
                        "May",
                        "June",
                        "July",
                        "August",
                        "September",
                        "October",
                        "November",
                        "December",
                    )[month - 1]
                ),
                userData=month,
            )
        form.addRow(self.tr("Month"), self.monthly_month_combo)

        self.monthly_day_combo = ComboBox()
        for day in range(1, 32):
            self.monthly_day_combo.addItem(str(day), userData=day)
        form.addRow(self.tr("Day"), self.monthly_day_combo)
        outer.addLayout(form)

        self.monthly_use_ordinal_checkbox = CheckBox(self.tr("Use ordinal weekday"))
        self.monthly_use_ordinal_checkbox.setChecked(False)
        outer.addWidget(self.monthly_use_ordinal_checkbox)

        ordinal_form = self._make_form_layout()
        self.monthly_ordinal_combo = ComboBox()
        for label, idx in (
            (self.tr("First"), 0),
            (self.tr("Second"), 1),
            (self.tr("Third"), 2),
            (self.tr("Fourth"), 3),
            (self.tr("Last"), 4),
        ):
            self.monthly_ordinal_combo.addItem(label, userData=idx)
        self.monthly_weekday_combo = ComboBox()
        for idx, label in enumerate(
            (
                self.tr("Monday"),
                self.tr("Tuesday"),
                self.tr("Wednesday"),
                self.tr("Thursday"),
                self.tr("Friday"),
                self.tr("Saturday"),
                self.tr("Sunday"),
            )
        ):
            self.monthly_weekday_combo.addItem(label, userData=idx)
        self.monthly_ordinal_combo.setEnabled(False)
        self.monthly_weekday_combo.setEnabled(False)

        self._ordinal_form_widget = QWidget()
        self._ordinal_form_widget.setLayout(ordinal_form)
        ordinal_form.addRow(self.tr("Ordinal"), self.monthly_ordinal_combo)
        ordinal_form.addRow(self.tr("Weekday"), self.monthly_weekday_combo)
        self._ordinal_form_widget.setVisible(False)
        outer.addWidget(self._ordinal_form_widget)

        self.monthly_use_ordinal_checkbox.stateChanged.connect(
            self._on_monthly_ordinal_toggled
        )
        self._on_monthly_ordinal_toggled(self.monthly_use_ordinal_checkbox.checkState())
        return widget

    def _build_weekday_grid(self) -> QGridLayout:
        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(8)
        self.weekday_checkboxes: list[CheckBox] = []
        weekdays = (
            self.tr("Monday"),
            self.tr("Tuesday"),
            self.tr("Wednesday"),
            self.tr("Thursday"),
            self.tr("Friday"),
            self.tr("Saturday"),
            self.tr("Sunday"),
        )
        for idx, label in enumerate(weekdays):
            cb = CheckBox(label)
            if idx == 0:
                cb.setChecked(True)
            self.weekday_checkboxes.append(cb)
            row = idx // 4
            col = idx % 4
            grid.addWidget(cb, row, col)
        return grid

    def _on_monthly_ordinal_toggled(self, _: Qt.CheckState) -> None:
        use_ordinal = self.monthly_use_ordinal_checkbox.isChecked()
        self.monthly_ordinal_combo.setEnabled(use_ordinal)
        self.monthly_weekday_combo.setEnabled(use_ordinal)
        self.monthly_day_combo.setEnabled(not use_ordinal)
        self._ordinal_form_widget.setVisible(use_ordinal)
        if use_ordinal:
            self.monthly_day_combo.setCurrentIndex(0)
        else:
            self.monthly_ordinal_combo.setCurrentIndex(0)
            self.monthly_weekday_combo.setCurrentIndex(0)

    def _switch_schedule_detail(self) -> None:
        index = self.trigger_group.checkedId()
        if index < 0:
            index = 0
        for page_index, page in enumerate(self._detail_pages):
            page.setVisible(page_index == index)

    def _on_trigger_button_clicked(self, _: Any) -> None:
        self._switch_schedule_detail()

    def _create_schedule_list_card(self) -> SimpleCardWidget:
        card = SimpleCardWidget()
        card.setSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum
        )
        layout = QVBoxLayout(card)
        layout.setSpacing(12)

        title = BodyLabel(self.tr("Scheduled tasks"))
        title.setStyleSheet("font-weight: 600; font-size: 16px;")
        layout.addWidget(title)

        self.schedule_table = TableWidget(self)
        self.schedule_table.setColumnCount(7)
        self.schedule_table.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        header_labels = [
            self.tr("Config"),
            self.tr("Type"),
            self.tr("Pattern"),
            self.tr("Next run"),
            self.tr("Force"),
            self.tr("Enabled"),
            self.tr("Action"),
        ]
        for col, label in enumerate(header_labels):
            header_item = QTableWidgetItem(label)
            if col in (4, 5, 6):
                header_item.setTextAlignment(
                    Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter
                )
            self.schedule_table.setHorizontalHeaderItem(col, header_item)
        header = self.schedule_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)
        header.setStretchLastSection(False)
        self.schedule_table.setColumnWidth(5, 56)
        self.schedule_table.setColumnWidth(6, 56)
        self.schedule_table.verticalHeader().setDefaultSectionSize(40)
        self.schedule_table.verticalHeader().setVisible(False)
        self.schedule_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.schedule_table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)

        self.empty_label = CaptionLabel(self.tr("No schedules yet."))
        empty_page = QWidget()
        empty_layout = QVBoxLayout(empty_page)
        empty_layout.setContentsMargins(0, 4, 0, 4)
        empty_layout.setSpacing(0)
        empty_layout.addWidget(self.empty_label)

        table_page = QWidget()
        table_layout = QVBoxLayout(table_page)
        table_layout.setContentsMargins(0, 0, 0, 0)
        table_layout.setSpacing(0)
        table_layout.addWidget(self.schedule_table)

        self.list_body = QWidget()
        self.list_body.setSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum
        )
        list_layout = QVBoxLayout(self.list_body)
        list_layout.setContentsMargins(0, 0, 0, 0)
        list_layout.setSpacing(0)
        list_layout.addWidget(empty_page)
        list_layout.addWidget(table_page)
        table_page.hide()
        self._list_empty_page = empty_page
        self._list_table_page = table_page
        layout.addWidget(self.list_body)

        return card

    def _refresh_config_selector(self) -> None:
        configs = self.service_coordinator.config.list_configs()

        self.config_selector.blockSignals(True)
        self.config_selector.clear()
        self._config_map.clear()
        for config in configs:
            name = str(config.get("name") or config.get("item_id") or "")
            raw_id = config.get("item_id", "")
            if not raw_id:
                continue
            config_id = str(raw_id)
            self.config_selector.addItem(name, userData=config_id)
            self._config_map[config_id] = name
        self.config_selector.blockSignals(False)

    def _resize_schedule_table(self, row_count: int) -> None:
        header_height = self.schedule_table.horizontalHeader().height()
        if header_height <= 0:
            header_height = 36
        row_height = self.schedule_table.verticalHeader().defaultSectionSize()
        frame = self.schedule_table.frameWidth() * 2
        self.schedule_table.setFixedHeight(
            header_height + row_count * row_height + frame + 2
        )

    def _refresh_schedule_table(self, entries: list[ScheduleEntry]) -> None:
        self._schedule_entries = entries
        self.schedule_table.setRowCount(len(entries))
        for row, entry in enumerate(entries):
            self._write_schedule_row(row, entry)
        has_entries = bool(entries)
        self._list_empty_page.setVisible(not has_entries)
        self._list_table_page.setVisible(has_entries)
        if has_entries:
            self._resize_schedule_table(len(entries))

    def _write_schedule_row(self, row: int, entry: ScheduleEntry) -> None:
        def _item(text: str) -> QTableWidgetItem:
            item = QTableWidgetItem(text)
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            return item

        self.schedule_table.setItem(
            row, 0, _item(entry.name or self.tr("Unknown"))
        )
        self.schedule_table.setItem(
            row,
            1,
            _item(self.schedule_service.format_entry_type(entry)),
        )
        self.schedule_table.setItem(
            row,
            2,
            _item(self.schedule_service.format_entry_pattern(entry)),
        )

        next_run = (
            entry.next_run.strftime("%Y-%m-%d %H:%M")
            if entry.next_run
            else self.tr("Pending")
        )
        self.schedule_table.setItem(row, 3, _item(next_run))

        self.schedule_table.setItem(
            row,
            4,
            _item(self.tr("Yes") if entry.force_start else self.tr("No")),
        )
        force_item = self.schedule_table.item(row, 4)
        if force_item is not None:
            force_item.setTextAlignment(
                Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter
            )

        enabled_check = CheckBox()
        enabled_check.setChecked(entry.enabled)
        enabled_check.stateChanged.connect(
            partial(self._on_enabled_toggled, entry.entry_id)
        )
        self.schedule_table.setCellWidget(
            row, 5, self._centered_cell_widget(enabled_check)
        )

        remove_button = TransparentToolButton(FIF.DELETE, self)
        remove_button.setFixedSize(32, 32)
        apply_fluent_tooltip(remove_button, self.tr("Delete schedule"))
        remove_button.clicked.connect(partial(self._on_remove_schedule, entry.entry_id))
        self.schedule_table.setCellWidget(
            row, 6, self._centered_cell_widget(remove_button)
        )

    def _centered_cell_widget(self, child: QWidget) -> QWidget:
        wrapper = QWidget(self.schedule_table)
        wrapper.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        layout = QHBoxLayout(wrapper)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addStretch(1)
        layout.addWidget(child, 0, Qt.AlignmentFlag.AlignCenter)
        layout.addStretch(1)
        return wrapper

    def _on_enabled_toggled(self, entry_id: str, state: int) -> None:
        self.schedule_service.set_schedule_enabled(entry_id, state != 0)

    def _on_remove_schedule(self, entry_id: str) -> None:
        self.schedule_service.remove_schedule(entry_id)

    def _on_add_schedule(self) -> None:
        current_index = self.config_selector.currentIndex()
        if current_index < 0:
            self._info_with_log(
                "warning", self.tr("Please select a configuration to schedule.")
            )
            return

        config_id = str(self.config_selector.itemData(current_index) or "")
        config_name = self.config_selector.currentText()
        checked_id = self.trigger_group.checkedId()
        if checked_id < 0 or checked_id >= len(self._trigger_types):
            checked_id = 0
        schedule_type = self._trigger_types[checked_id][1]
        params: dict[str, Any] = {}

        if schedule_type == SCHEDULE_SINGLE:
            run_at = self._compose_datetime(self.single_datetime)
            if run_at <= datetime.now():
                self._info_with_log(
                    "warning", self.tr("Please choose a future date and time.")
                )
                return
            params["run_at"] = run_at.isoformat()
        else:
            if schedule_type == SCHEDULE_DAILY:
                start_at = self._compose_datetime(self.daily_datetime)
                params["interval_days"] = self.daily_interval_spin.value()
            elif schedule_type == SCHEDULE_WEEKLY:
                start_at = self._compose_datetime(self.weekly_datetime)
                params["interval_weeks"] = max(1, self.weekly_interval_spin.value())
                weekdays = [
                    idx
                    for idx, cb in enumerate(self.weekday_checkboxes)
                    if cb.isChecked()
                ]
                if not weekdays:
                    self._info_with_log(
                        "warning", self.tr("Please select at least one weekday.")
                    )
                    return
                params["weekdays"] = weekdays
            else:
                start_at = self._compose_datetime(self.monthly_datetime)
                month_value = int(self.monthly_month_combo.currentData() or 0)
                params["month"] = month_value
                if self.monthly_use_ordinal_checkbox.isChecked():
                    ordinal = self.monthly_ordinal_combo.currentData()
                    weekday = self.monthly_weekday_combo.currentData()
                    if ordinal is None or weekday is None:
                        self._info_with_log(
                            "warning", self.tr("Please select ordinal and weekday.")
                        )
                        return
                    params["ordinal"] = int(ordinal)
                    params["weekday"] = int(weekday)
                else:
                    day_value = int(self.monthly_day_combo.currentData() or 1)
                    params["month_day"] = day_value
            params["start_at"] = start_at.isoformat()
            params["hour"] = start_at.hour
            params["minute"] = start_at.minute

        entry = ScheduleEntry(
            entry_id=f"sched_{uuid4().hex}",
            config_id=config_id,
            name=config_name,
            schedule_type=schedule_type,
            params=params,
            force_start=self.force_checkbox.isChecked(),
            enabled=self.enabled_checkbox.isChecked(),
            created_at=datetime.now(),
        )
        if not self.schedule_service.add_schedule(entry):
            self._info_with_log(
                "warning", self.tr("Failed to persist the schedule.")
            )
            return

        self._info_with_log("info", self.tr("Schedule saved."))
        self.single_datetime.setDateTime(self._default_qdatetime())

    def _compose_datetime(self, datetime_input: ZhDateTimeInput) -> datetime:
        return datetime_input.dateTime()

    def _info_with_log(self, level: str, message: str) -> None:
        normalized_level = (level or "info").lower()
        signalBus.info_bar_requested.emit(normalized_level, message)
        signalBus.log_output.emit(normalized_level.upper(), message)
