from typing import TYPE_CHECKING, Optional

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QHBoxLayout,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from qfluentwidgets import (
    IndeterminateProgressRing,
    PixmapLabel,
)

from app.common.fluent_tooltip import apply_fluent_tooltip
from app.common.signal_bus import signalBus

if TYPE_CHECKING:
    from app.view.monitor_interface.monitor_interface import MonitorInterface


class _ClickablePreviewLabel(PixmapLabel):
    clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mouseReleaseEvent(event)


class MonitorWidget(QWidget):
    """任务页监控预览：镜像 MonitorInterface 画面，点击跳转监控页。"""

    def __init__(self, monitor: "MonitorInterface", parent=None):
        super().__init__(parent=parent)
        self.setObjectName("MonitorWidget")
        self._monitor = monitor
        self._preview_pixmap: Optional[QPixmap] = None

        self._setup_ui()
        self._connect_monitor_signals()
        self._sync_from_monitor()

    def _setup_ui(self) -> None:
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAutoFillBackground(False)

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        self._layout_width = 344
        self._layout_height = 194
        self._monitor_width = 344
        self._monitor_height = 194

        self.preview_card = QWidget(self)
        self.preview_card.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.preview_card.setAutoFillBackground(False)
        self.preview_card.setStyleSheet("background-color: transparent;")
        self.preview_card.setFixedSize(self._monitor_width, self._monitor_height)
        card_policy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.preview_card.setSizePolicy(card_policy)

        card_layout = QVBoxLayout(self.preview_card)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.setSpacing(0)

        self.preview_label = _ClickablePreviewLabel(self.preview_card)
        self.preview_label.setObjectName("monitorPreviewLabel")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.preview_label.setAutoFillBackground(False)
        self.preview_label.setFixedSize(self._monitor_width, self._monitor_height)
        self.preview_label.setSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed
        )
        self.preview_label.setScaledContents(False)
        self.preview_label.setStyleSheet(
            """
            QLabel#monitorPreviewLabel {
                border-radius: 8px;
                border: 1px solid rgba(255, 255, 255, 0.12);
                background-color: transparent;
            }
            """
        )
        self.preview_label.clicked.connect(self._on_preview_clicked)
        apply_fluent_tooltip(
            self.preview_label,
            self.tr("Click to open the monitor page"),
        )

        card_layout.addWidget(self.preview_label)
        self.main_layout.addWidget(self.preview_card, 0)
        self.setFixedSize(self._monitor_width, self._monitor_height)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        self._init_loading_overlay()

    def _init_loading_overlay(self) -> None:
        self._loading_overlay = QWidget(self.preview_label)
        self._loading_overlay.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents
        )
        self._loading_overlay.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        self._loading_overlay.setStyleSheet(
            "background-color: rgba(0, 0, 0, 60); border-radius: 8px;"
        )
        layout = QHBoxLayout(self._loading_overlay)
        layout.setContentsMargins(24, 16, 24, 16)
        layout.setSpacing(0)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._loading_indicator = IndeterminateProgressRing(self._loading_overlay)
        self._loading_indicator.setFixedSize(28, 28)
        layout.addWidget(self._loading_indicator)
        self._loading_overlay.hide()

    def _connect_monitor_signals(self) -> None:
        self._monitor.preview_pixmap_changed.connect(self._on_preview_pixmap_changed)
        self._monitor.preview_cleared.connect(self._clear_preview)
        self._monitor.loading_changed.connect(self._on_loading_changed)

    def _sync_from_monitor(self) -> None:
        pixmap = self._monitor.source_preview_pixmap
        if pixmap is not None and not pixmap.isNull():
            self._on_preview_pixmap_changed(pixmap)
        else:
            self._clear_preview()
        self._on_loading_changed(self._monitor.is_starting)

    def set_preview_bounds(self, width: int, height: int) -> None:
        if width <= 0 or height <= 0:
            return
        self._layout_width = width
        self._layout_height = height
        if self._monitor_width == width and self._monitor_height == height:
            return
        self._monitor_width = width
        self._monitor_height = height
        self.preview_card.setFixedSize(width, height)
        self.preview_label.setFixedSize(width, height)
        self.setFixedSize(width, height)
        self._refresh_preview_image()
        if self._loading_overlay.isVisible():
            self._loading_overlay.setGeometry(0, 0, width, height)

    def _on_preview_pixmap_changed(self, pixmap: QPixmap) -> None:
        self._preview_pixmap = pixmap
        self._refresh_preview_image()

    def _clear_preview(self) -> None:
        self._preview_pixmap = None
        self.preview_label.clear()

    def _refresh_preview_image(self) -> None:
        if not self._preview_pixmap or self._preview_pixmap.isNull():
            self._clear_preview()
            return
        target_size = QSize(self._monitor_width, self._monitor_height)
        scaled = self._preview_pixmap.scaled(
            target_size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.preview_label.setPixmap(scaled)

    def _on_loading_changed(self, loading: bool) -> None:
        if loading:
            preview_size = self.preview_label.size()
            self._loading_overlay.setGeometry(
                0, 0, preview_size.width(), preview_size.height()
            )
            self._loading_overlay.show()
            self._loading_indicator.start()
        else:
            self._loading_overlay.hide()
            self._loading_indicator.stop()

    def _on_preview_clicked(self) -> None:
        signalBus.monitor_page_requested.emit()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._refresh_preview_image()
        if self._loading_overlay.isVisible():
            preview_size = self.preview_label.size()
            self._loading_overlay.setGeometry(
                0, 0, preview_size.width(), preview_size.height()
            )
