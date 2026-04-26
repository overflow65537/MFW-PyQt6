from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QProgressBar, QVBoxLayout, QWidget
from qfluentwidgets import (
    BodyLabel,
    CheckBox,
    MessageBoxBase,
    PrimaryPushButton,
    PushButton,
    SimpleCardWidget,
    SubtitleLabel,
)


@dataclass(slots=True)
class LogZipOptions:
    # 运行记录索引（0-based），允许多选
    selected_run_indices: list[int]

    def has_any_selection(self) -> bool:
        return bool(self.selected_run_indices)


@dataclass(slots=True)
class RunRecordEntry:
    """供 UI 展示的运行记录条目（时间由外部解析提供）。"""

    index: int
    start_text: str
    end_text: str
    duration_text: str


@dataclass(slots=True)
class LogZipPreview:
    text_size: int = 0
    images_size: int = 0
    other_size: int = 0
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
        self._run_records: list[RunRecordEntry] = []

        self.buttonGroup.hide()
        self.widget.setMinimumWidth(560)
        self.widget.setMinimumHeight(560)

        self._build_ui()
        self._bind_signals()
        self._set_status(self.tr("Select one or more run records to include in the log package."))
        self._refresh_preview()

    def _build_ui(self) -> None:
        title = SubtitleLabel(self.tr("Package logs"), self)
        desc = BodyLabel(
            self.tr(
                "Log contents will be grouped by run records (task flow start/stop). You can select multiple run records."
            ),
            self,
        )
        desc.setWordWrap(True)

        self.viewLayout.addWidget(title)
        self.viewLayout.addSpacing(6)
        self.viewLayout.addWidget(desc)
        self.viewLayout.addSpacing(12)

        self.viewLayout.addWidget(self._build_run_records_card())
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

    def _build_run_records_card(self) -> SimpleCardWidget:
        card = SimpleCardWidget(self)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)

        title = SubtitleLabel(self.tr("Run records"), card)
        layout.addWidget(title)

        self._run_checkboxes: list[CheckBox] = []
        self._run_empty_hint = BodyLabel(self.tr("No run records found."), card)
        self._run_empty_hint.setWordWrap(True)
        layout.addWidget(self._run_empty_hint)
        return card

    def set_run_records(self, records: Iterable[RunRecordEntry]) -> None:
        """由外部注入运行记录列表。"""
        self._run_records = list(records)
        self._rebuild_run_record_checkboxes()
        self._refresh_preview()

    def _rebuild_run_record_checkboxes(self) -> None:
        card = self._run_empty_hint.parentWidget()
        if card is None:
            return
        layout = card.layout()
        if layout is None:
            return

        # 先移除旧复选框
        for cb in self._run_checkboxes:
            try:
                cb.toggled.disconnect(self._refresh_preview)
            except Exception:
                pass
            cb.setParent(None)
            cb.deleteLater()
        self._run_checkboxes.clear()

        if not self._run_records:
            self._run_empty_hint.show()
            return

        self._run_empty_hint.hide()
        for rec in self._run_records:
            text = (
                self.tr("Run record ")
                + str(rec.index + 1)
                + ": "
                + rec.start_text
                + " ~ "
                + rec.end_text
                + " ("
                + rec.duration_text
                + ")"
            )
            cb = CheckBox(text, card)
            cb.setChecked(False)
            cb.toggled.connect(self._refresh_preview)
            self._run_checkboxes.append(cb)
            layout.addWidget(cb)

        # 只有一条运行记录（常见于兜底“全部日志”）时默认勾选
        if len(self._run_checkboxes) == 1:
            self._run_checkboxes[0].setChecked(True)

    def _refresh_preview(self) -> None:
        preview = LogZipPreview()
        if self._preview_provider is not None:
            try:
                preview = self._preview_provider(self.get_options())
            except Exception:
                preview = LogZipPreview()

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

    def get_options(self) -> LogZipOptions:
        selected: list[int] = []
        for idx, cb in enumerate(self._run_checkboxes):
            if cb.isChecked():
                selected.append(idx)
        return LogZipOptions(selected_run_indices=selected)

    def set_running(self, running: bool) -> None:
        self._running = running
        self._finished = False if running else self._finished
        self._cancel_emitted = False if running else self._cancel_emitted

        for cb in self._run_checkboxes:
            cb.setEnabled(not running)

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
                self.tr("Select at least one run record."),
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

    def _set_status(self, text: str, *, error: bool = False) -> None:
        self.status_label.setText(text)
        color = "#c62828" if error else ""
        self.status_label.setStyleSheet(
            f"color: {color};" if color else "color: palette(window-text);"
        )