from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QProgressBar, QVBoxLayout, QWidget
from qfluentwidgets import (
    BodyLabel,
    CheckBox,
    ComboBox,
    MessageBoxBase,
    PrimaryPushButton,
    PushButton,
    SimpleCardWidget,
    SubtitleLabel,
)


@dataclass(slots=True)
class LogZipOptions:
    include_maa_logs: bool = True
    include_gui_logs: bool = True
    include_custom_logs: bool = True
    include_other_files: bool = True
    include_on_error_images: bool = True
    include_vision_images: bool = True
    include_other_images: bool = True
    on_error_days: int | None = None
    vision_days: int | None = None
    other_images_days: int | None = None

    def has_any_selection(self) -> bool:
        return any(
            (
                self.include_maa_logs,
                self.include_gui_logs,
                self.include_custom_logs,
                self.include_other_files,
                self.include_on_error_images,
                self.include_vision_images,
                self.include_other_images,
            )
        )


@dataclass(slots=True)
class LogZipPreview:
    maa_logs_size: int = 0
    gui_logs_size: int = 0
    custom_logs_size: int = 0
    other_files_size: int = 0
    on_error_images_size: int = 0
    vision_images_size: int = 0
    other_images_size: int = 0
    total_size: int = 0


class LogZipDialog(MessageBoxBase):
    startRequested = Signal(object)
    cancelRequested = Signal()

    def __init__(
        self,
        parent=None,
        preview_provider: Callable[[LogZipOptions], LogZipPreview] | None = None,
    ):
        super().__init__(parent)
        self._running = False
        self._finished = False
        self._cancel_emitted = False
        self._preview_provider = preview_provider

        self.buttonGroup.hide()
        self.widget.setMinimumWidth(560)
        self.widget.setMinimumHeight(580)

        self._build_ui()
        self._bind_signals()
        self._set_status(self.tr("Select the content to include in the log package."))
        self._refresh_preview()

    def _build_ui(self) -> None:
        title = SubtitleLabel(self.tr("Package logs"), self)
        desc = BodyLabel(
            self.tr(
                "Choose the log files and image folders to include. Image items can be filtered by time range."
            ),
            self,
        )
        desc.setWordWrap(True)

        self.viewLayout.addWidget(title)
        self.viewLayout.addSpacing(6)
        self.viewLayout.addWidget(desc)
        self.viewLayout.addSpacing(12)

        self.viewLayout.addWidget(self._build_logs_card())
        self.viewLayout.addWidget(self._build_images_card())
        self.viewLayout.addSpacing(8)

        self.status_label = BodyLabel(self)
        self.status_label.setWordWrap(True)
        self.viewLayout.addWidget(self.status_label)

        self.total_size_label = BodyLabel(self)
        self.total_size_label.setStyleSheet("font-weight: 600;")
        self.viewLayout.addWidget(self.total_size_label)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.viewLayout.addWidget(self.progress_bar)

        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 8, 0, 0)
        button_layout.addStretch(1)

        self.start_button = PrimaryPushButton(self.tr("Start packaging"), self)
        self.cancel_button = PushButton(self.tr("Close"), self)

        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.cancel_button)
        self.viewLayout.addLayout(button_layout)

    def _build_logs_card(self) -> SimpleCardWidget:
        card = SimpleCardWidget(self)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)

        title = SubtitleLabel(self.tr("Logs"), card)
        layout.addWidget(title)

        self.maa_log_checkbox = CheckBox(self.tr("maa.log (including .bak)"), card)
        self.maa_log_checkbox.setChecked(True)
        self.gui_log_checkbox = CheckBox(self.tr("gui.log"), card)
        self.gui_log_checkbox.setChecked(True)
        self.custom_log_checkbox = CheckBox(self.tr("custom.log"), card)
        self.custom_log_checkbox.setChecked(True)
        self.other_files_checkbox = CheckBox(self.tr("other files"), card)
        self.other_files_checkbox.setChecked(True)

        layout.addWidget(self.maa_log_checkbox)
        layout.addWidget(self.gui_log_checkbox)
        layout.addWidget(self.custom_log_checkbox)
        layout.addWidget(self.other_files_checkbox)
        return card

    def _build_images_card(self) -> SimpleCardWidget:
        card = SimpleCardWidget(self)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)

        title = SubtitleLabel(self.tr("Images"), card)
        desc = BodyLabel(
            self.tr("Default is all image categories with time range set to all."),
            card,
        )
        desc.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(desc)

        self.on_error_checkbox, self.on_error_combo = self._create_image_row(
            self.tr("on_error folder"), card
        )
        self.vision_checkbox, self.vision_combo = self._create_image_row(
            self.tr("vision folder"), card
        )
        self.other_images_checkbox, self.other_images_combo = self._create_image_row(
            self.tr("other images"), card
        )

        for checkbox, combo in (
            (self.on_error_checkbox, self.on_error_combo),
            (self.vision_checkbox, self.vision_combo),
            (self.other_images_checkbox, self.other_images_combo),
        ):
            row = QHBoxLayout()
            row.setContentsMargins(0, 0, 0, 0)
            row.setSpacing(10)
            row.addWidget(checkbox, 1)
            row.addWidget(combo, 0)
            layout.addLayout(row)

        return card

    def _create_image_row(self, text: str, parent: QWidget) -> tuple[CheckBox, ComboBox]:
        checkbox = CheckBox(text, parent)
        checkbox.setChecked(True)

        combo = ComboBox(parent)
        self._populate_time_range_combo(combo)
        combo.setCurrentIndex(0)
        combo.setMinimumWidth(150)
        return checkbox, combo

    def _populate_time_range_combo(self, combo: ComboBox) -> None:
        combo.addItem(self.tr("all"), userData=None)
        combo.addItem(self.tr("today"), userData=1)
        combo.addItem(self.tr("within 2 days"), userData=2)
        combo.addItem(self.tr("within 3 days"), userData=3)

    def _refresh_preview(self) -> None:
        preview = LogZipPreview()
        if self._preview_provider is not None:
            try:
                preview = self._preview_provider(self.get_options())
            except Exception:
                preview = LogZipPreview()

        self.maa_log_checkbox.setText(
            f"{self.tr('maa.log (including .bak)')} ({self._format_size(preview.maa_logs_size)})"
        )
        self.gui_log_checkbox.setText(
            f"{self.tr('gui.log')} ({self._format_size(preview.gui_logs_size)})"
        )
        self.custom_log_checkbox.setText(
            f"{self.tr('custom.log')} ({self._format_size(preview.custom_logs_size)})"
        )
        self.other_files_checkbox.setText(
            f"{self.tr('other files')} ({self._format_size(preview.other_files_size)})"
        )
        self.on_error_checkbox.setText(
            f"{self.tr('on_error folder')} ({self._format_size(preview.on_error_images_size)})"
        )
        self.vision_checkbox.setText(
            f"{self.tr('vision folder')} ({self._format_size(preview.vision_images_size)})"
        )
        self.other_images_checkbox.setText(
            f"{self.tr('other images')} ({self._format_size(preview.other_images_size)})"
        )
        self.total_size_label.setText(
            self.tr("Selected total size:") + self._format_size(preview.total_size)
        )

    def _format_size(self, size: int) -> str:
        if size < 1024:
            return f"{size} B"
        if size < 1024 * 1024:
            return f"{size / 1024:.1f} KB"
        if size < 1024 * 1024 * 1024:
            return f"{size / (1024 * 1024):.2f} MB"
        return f"{size / (1024 * 1024 * 1024):.2f} GB"

    def _bind_signals(self) -> None:
        self.start_button.clicked.connect(self._on_start_clicked)
        self.cancel_button.clicked.connect(self._on_cancel_clicked)

        for checkbox in (
            self.maa_log_checkbox,
            self.gui_log_checkbox,
            self.custom_log_checkbox,
            self.other_files_checkbox,
        ):
            checkbox.toggled.connect(self._refresh_preview)

        for checkbox, combo in (
            (self.on_error_checkbox, self.on_error_combo),
            (self.vision_checkbox, self.vision_combo),
            (self.other_images_checkbox, self.other_images_combo),
        ):
            checkbox.toggled.connect(combo.setEnabled)
            checkbox.toggled.connect(self._refresh_preview)
            combo.currentIndexChanged.connect(self._refresh_preview)

    def get_options(self) -> LogZipOptions:
        return LogZipOptions(
            include_maa_logs=self.maa_log_checkbox.isChecked(),
            include_gui_logs=self.gui_log_checkbox.isChecked(),
            include_custom_logs=self.custom_log_checkbox.isChecked(),
            include_other_files=self.other_files_checkbox.isChecked(),
            include_on_error_images=self.on_error_checkbox.isChecked(),
            include_vision_images=self.vision_checkbox.isChecked(),
            include_other_images=self.other_images_checkbox.isChecked(),
            on_error_days=self._combo_to_days(self.on_error_combo),
            vision_days=self._combo_to_days(self.vision_combo),
            other_images_days=self._combo_to_days(self.other_images_combo),
        )

    def set_running(self, running: bool) -> None:
        self._running = running
        self._finished = False if running else self._finished
        self._cancel_emitted = False if running else self._cancel_emitted

        for widget in (
            self.maa_log_checkbox,
            self.gui_log_checkbox,
            self.custom_log_checkbox,
            self.other_files_checkbox,
            self.on_error_checkbox,
            self.vision_checkbox,
            self.other_images_checkbox,
            self.on_error_combo,
            self.vision_combo,
            self.other_images_combo,
        ):
            widget.setEnabled(not running)

        self.start_button.setEnabled(not running)
        self.cancel_button.setEnabled(True)
        self.cancel_button.setText(
            self.tr("Cancel packaging") if running else self.tr("Close")
        )

    def update_progress(self, current: int, total: int, message: str = "") -> None:
        total = max(total, 1)
        self.progress_bar.setRange(0, total)
        self.progress_bar.setValue(max(0, min(current, total)))
        if message:
            self._set_status(message)

    def set_finished(self, message: str, *, error: bool = False) -> None:
        self._running = False
        self._finished = True
        self._cancel_emitted = False
        self.start_button.setEnabled(False)
        self.cancel_button.setEnabled(True)
        self.cancel_button.setText(self.tr("Close"))
        self._set_status(message, error=error)

    def mark_cancelling(self) -> None:
        if not self._running:
            return
        self._set_status(self.tr("Cancelling log packaging, please wait..."))
        self.cancel_button.setEnabled(False)

    def _on_start_clicked(self) -> None:
        options = self.get_options()
        if not options.has_any_selection():
            self._set_status(
                self.tr("Select at least one log or image category."),
                error=True,
            )
            return
        self.progress_bar.setValue(0)
        self.cancel_button.setEnabled(True)
        self.startRequested.emit(options)

    def _on_cancel_clicked(self) -> None:
        if self._running:
            if not self._cancel_emitted:
                self._cancel_emitted = True
                self.cancelRequested.emit()
            self.mark_cancelling()
            return
        self.close()

    def closeEvent(self, event) -> None:
        if self._running:
            if not self._cancel_emitted:
                self._cancel_emitted = True
                self.cancelRequested.emit()
            self.mark_cancelling()
            event.ignore()
            return
        super().closeEvent(event)

    def _combo_to_days(self, combo: ComboBox) -> int | None:
        return combo.currentData()

    def _set_status(self, text: str, *, error: bool = False) -> None:
        self.status_label.setText(text)
        color = "#c62828" if error else ""
        self.status_label.setStyleSheet(
            f"color: {color};" if color else "color: palette(window-text);"
        )