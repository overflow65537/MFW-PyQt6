"""多实例模式：监控页同时展示所有配置的实时画面。"""

from __future__ import annotations

from typing import Callable, Dict, List, Optional, Tuple

from PIL import Image
from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from qfluentwidgets import (
    BodyLabel,
    CaptionLabel,
    FluentIcon as FIF,
    IconWidget,
    IndeterminateProgressRing,
    PixmapLabel,
    ScrollArea,
    SimpleCardWidget,
    isDarkTheme,
)

from app.common.config import cfg
from app.view.monitor.recognition_roi_store import RecognitionRoiStore
from app.view.monitor.roi_overlay import draw_roi_on_pixmap


def _pil_to_pixmap(pil_image: Image.Image) -> QPixmap:
    rgb = pil_image.convert("RGB")
    w, h = rgb.size
    buffer = rgb.tobytes("raw", "RGB")
    qimage = QImage(buffer, w, h, w * 3, QImage.Format.Format_RGB888)
    return QPixmap.fromImage(qimage)


class ConfigMonitorTile(SimpleCardWidget):
    """单个配置的监控卡片。"""

    config_selected = Signal(str)

    _PREVIEW_MIN_W = 280
    _PREVIEW_MIN_H = 158

    def __init__(self, config_id: str, config_name: str, parent=None):
        super().__init__(parent)
        self.config_id = config_id
        self._config_name = config_name
        self._running = False
        self._active = False
        self._loading = False
        self._roi_store = RecognitionRoiStore()

        self.setClickEnabled(False)
        self.setBorderRadius(8)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(6)

        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(6)
        self._name_label = BodyLabel(config_name, self)
        self._running_ring = IndeterminateProgressRing(self)
        self._running_ring.setFixedSize(20, 20)
        self._running_ring.setStrokeWidth(2)
        self._running_ring.setToolTip(self.tr("Running"))
        self._running_ring.hide()
        header.addWidget(self._name_label, 1)
        header.addWidget(self._running_ring, 0, Qt.AlignmentFlag.AlignVCenter)
        layout.addLayout(header)

        self._preview_host = QWidget(self)
        self._preview_host.setMinimumSize(self._PREVIEW_MIN_W, self._PREVIEW_MIN_H)
        host_layout = QVBoxLayout(self._preview_host)
        host_layout.setContentsMargins(0, 0, 0, 0)

        self._preview_label = PixmapLabel(self._preview_host)
        self._preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._preview_label.setMinimumSize(self._PREVIEW_MIN_W, self._PREVIEW_MIN_H)
        self._preview_label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        host_layout.addWidget(self._preview_label)

        self._idle_overlay = QWidget(self._preview_host)
        self._idle_overlay.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents, True
        )
        idle_layout = QVBoxLayout(self._idle_overlay)
        idle_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._power_icon = IconWidget(FIF.POWER_BUTTON, self._idle_overlay)
        self._power_icon.setFixedSize(48, 48)
        self._idle_hint = CaptionLabel(self.tr("Not running"), self._idle_overlay)
        self._idle_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        idle_layout.addWidget(self._power_icon, 0, Qt.AlignmentFlag.AlignCenter)
        idle_layout.addWidget(self._idle_hint)

        self._loading_ring = IndeterminateProgressRing(self._preview_host)
        self._loading_ring.setFixedSize(32, 32)
        self._loading_ring.hide()

        layout.addWidget(self._preview_host)

        self._active_border = QFrame(self)
        self._active_border.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents, True
        )
        self._active_border.hide()

        self._apply_styles()
        self._apply_mica_compat()
        self.set_running(False)

    def _apply_mica_compat(self) -> None:
        """与主窗口 Mica 背景兼容：保持 SimpleCardWidget 默认半透明，不覆写卡片底色。"""
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAutoFillBackground(False)
        self._preview_host.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self._preview_host.setAutoFillBackground(False)
        self._preview_host.setStyleSheet("background: transparent;")

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.config_selected.emit(self.config_id)
        # 跳过 SimpleCardWidget.mouseReleaseEvent，避免其无参 clicked 与 config_selected 冲突
        QWidget.mouseReleaseEvent(self, event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._reposition_overlays()
        if hasattr(self, "_active_border"):
            self._active_border.setGeometry(self.rect())

    def _reposition_overlays(self) -> None:
        host = self._preview_host
        if host.width() <= 0 or host.height() <= 0:
            return
        self._idle_overlay.setGeometry(0, 0, host.width(), host.height())
        ring = self._loading_ring
        ring.move(
            max(0, (host.width() - ring.width()) // 2),
            max(0, (host.height() - ring.height()) // 2),
        )

    def _apply_styles(self) -> None:
        muted = (
            "rgba(160, 160, 160, 0.95)"
            if isDarkTheme()
            else "rgba(96, 96, 96, 0.95)"
        )
        self._idle_hint.setStyleSheet(f"color: {muted};")
        preview_bg = (
            "rgba(255, 255, 255, 0.04)"
            if isDarkTheme()
            else "rgba(0, 0, 0, 0.03)"
        )
        self._preview_label.setStyleSheet(
            f"border-radius: 6px; background-color: {preview_bg};"
        )
        self._idle_overlay.setStyleSheet(
            "background-color: rgba(0, 0, 0, 0.42); border-radius: 6px;"
        )
        self._update_active_border()

    def _update_active_border(self) -> None:
        if self._active:
            self._active_border.setStyleSheet(
                "QFrame {"
                "  border: 2px solid #50c878;"
                "  border-radius: 8px;"
                "  background: transparent;"
                "}"
            )
            self._active_border.show()
            self._active_border.raise_()
        else:
            self._active_border.hide()

    def set_config_name(self, name: str) -> None:
        self._config_name = name
        self._name_label.setText(name)

    def set_active(self, active: bool) -> None:
        self._active = bool(active)
        self._update_active_border()

    def set_running(self, running: bool) -> None:
        self._running = bool(running)
        if running:
            self._running_ring.show()
            self._running_ring.start()
            self._idle_overlay.hide()
        else:
            self._running_ring.hide()
            self._running_ring.stop()
            self._preview_label.clear()
            self._idle_overlay.show()
            self._set_loading(False)
        self._reposition_overlays()

    def set_loading(self, loading: bool) -> None:
        self._set_loading(loading)

    def _set_loading(self, loading: bool) -> None:
        self._loading = bool(loading)
        if loading and self._running:
            self._loading_ring.show()
            self._loading_ring.start()
        else:
            self._loading_ring.hide()
            self._loading_ring.stop()
        self._reposition_overlays()

    def clear_preview(self) -> None:
        self._preview_label.clear()

    def update_preview(
        self,
        pil_image: Image.Image,
        *,
        roi_store: Optional[RecognitionRoiStore] = None,
    ) -> None:
        if not self._running:
            return
        store = roi_store or self._roi_store
        pixmap = _pil_to_pixmap(pil_image)
        if bool(cfg.get(cfg.monitor_recognition_roi_enabled)):
            active_roi = store.peek()
            if active_roi and active_roi.get("box"):
                pixmap = draw_roi_on_pixmap(
                    pixmap,
                    active_roi["box"],
                    label=active_roi.get("node", ""),
                    phase=active_roi.get("phase", "hit"),
                )
        target = self._preview_label.size()
        if target.width() > 0 and target.height() > 0:
            pixmap = pixmap.scaled(
                target,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        self._preview_label.setPixmap(pixmap)
        self._set_loading(False)
        self._idle_overlay.hide()

    def apply_theme(self) -> None:
        self._apply_mica_compat()
        self._apply_styles()


def _apply_scroll_mica_compat(scroll: ScrollArea, content: QWidget) -> None:
    """ScrollArea 透明化，使内部 SimpleCardWidget 能透出 Mica 背景。"""
    scroll.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
    scroll.setAutoFillBackground(False)
    scroll.setStyleSheet("ScrollArea { background: transparent; border: none; }")
    viewport = scroll.viewport()
    if viewport is not None:
        viewport.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        viewport.setAutoFillBackground(False)
        viewport.setStyleSheet("background: transparent; border: none;")
    content.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
    content.setAutoFillBackground(False)
    content.setStyleSheet("background: transparent;")


class MultiConfigMonitorGrid(ScrollArea):
    """滚动网格：每个配置一张监控卡片。"""

    tile_clicked = Signal(str)

    def __init__(
        self,
        *,
        is_config_running: Callable[[str], bool],
        parent=None,
    ):
        super().__init__(parent=parent)
        self._is_config_running = is_config_running
        self._tiles: Dict[str, ConfigMonitorTile] = {}
        self._active_config_id: str = ""

        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self._container = QWidget(self)
        self._grid = QGridLayout(self._container)
        self._grid.setContentsMargins(4, 4, 4, 4)
        self._grid.setSpacing(12)
        self.setWidget(self._container)
        _apply_scroll_mica_compat(self, self._container)

    def rebuild(self, configs: List[Tuple[str, str]]) -> None:
        """configs: [(config_id, display_name), ...]"""
        keep_ids = {cid for cid, _ in configs}

        while self._grid.count():
            item = self._grid.takeAt(0)
            if item.widget():
                item.widget().setParent(None)

        for cid in list(self._tiles.keys()):
            if cid not in keep_ids:
                tile = self._tiles.pop(cid)
                tile.deleteLater()

        for idx, (cid, name) in enumerate(configs):
            tile = self._tiles.get(cid)
            if tile is None:
                tile = ConfigMonitorTile(cid, name, self._container)
                tile.config_selected.connect(self.tile_clicked.emit)
                self._tiles[cid] = tile
            else:
                tile.set_config_name(name)

            row, col = divmod(idx, self._column_count(len(configs)))
            self._grid.addWidget(tile, row, col)

        for cid in keep_ids:
            tile = self._tiles.get(cid)
            if tile is None:
                continue
            running = self._is_config_running(cid)
            tile.set_running(running)
            tile.set_active(cid == self._active_config_id)
            if running and (
                tile._preview_label.pixmap() is None
                or tile._preview_label.pixmap().isNull()
            ):
                tile.set_loading(True)

    @staticmethod
    def _column_count(total: int) -> int:
        if total <= 1:
            return 1
        if total <= 4:
            return 2
        return 3

    def set_active_config(self, config_id: str) -> None:
        self._active_config_id = config_id or ""
        for cid, tile in self._tiles.items():
            tile.set_active(cid == self._active_config_id)

    def set_running(self, config_id: str, running: bool) -> None:
        tile = self._tiles.get(config_id)
        if tile is None:
            return
        tile.set_running(running)
        if running:
            tile.set_loading(True)
        else:
            tile.clear_preview()

    def clear_monitor_loading(self, config_id: str) -> None:
        tile = self._tiles.get(config_id)
        if tile is not None:
            tile.set_loading(False)

    def update_frame(
        self,
        config_id: str,
        pil_image: Image.Image,
        *,
        roi_store: Optional[RecognitionRoiStore] = None,
    ) -> None:
        tile = self._tiles.get(config_id)
        if tile is None:
            return
        if roi_store is not None:
            tile._roi_store = roi_store
        tile.update_preview(pil_image, roi_store=roi_store)

    def clear_frame(self, config_id: str) -> None:
        tile = self._tiles.get(config_id)
        if tile is None:
            return
        tile.clear_preview()
        if not self._is_config_running(config_id):
            tile.set_running(False)

    def apply_theme(self) -> None:
        _apply_scroll_mica_compat(self, self._container)
        for tile in self._tiles.values():
            tile.apply_theme()
