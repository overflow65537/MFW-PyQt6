from typing import Optional
import asyncio
from datetime import datetime
from pathlib import Path
from time import time

from PIL import Image
from PySide6.QtCore import QSize, Qt, QTimer, Signal, QPoint
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
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
    PrimaryPushButton,
    PushButton,
    SimpleCardWidget,
    isDarkTheme,
    qconfig,
)

from app.common.fluent_tooltip import apply_fluent_tooltip
from app.common.config import cfg
from app.core.core import ServiceCoordinator
from app.core.runner.monitor_task import MonitorTask
from app.view.monitor import MonitorSession
from app.view.monitor.recognition_roi_store import RecognitionRoiStore
from app.view.monitor.roi_overlay import draw_roi_on_pixmap
from app.view.task_interface.components.panel_splitter import (
    PANEL_SECTION_SPACING,
    panel_outer_margins,
)
from app.utils.logger import logger
from app.common.signal_bus import signalBus


class _ClickablePreviewLabel(PixmapLabel):
    clicked = Signal(int, int)

    def __init__(self, parent=None):
        super().__init__(parent=parent)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.position()
            self.clicked.emit(int(pos.x()), int(pos.y()))
        super().mouseReleaseEvent(event)


class MonitorInterface(QWidget):
    """唯一监控实例：提供截图会话，任务页预览与其共享画面。"""

    preview_pixmap_changed = Signal(QPixmap)
    preview_cleared = Signal()
    loading_changed = Signal(bool)

    def __init__(self, service_coordinator: ServiceCoordinator, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("MonitorInterface")
        self.service_coordinator = service_coordinator
        self._preview_pixmap: Optional[QPixmap] = None
        self._current_pil_image: Optional[Image.Image] = None
        self._preview_scaled_size: QSize = QSize(0, 0)
        self._image_width: Optional[int] = None
        self._image_height: Optional[int] = None
        self._is_landscape: Optional[bool] = None
        self._roi_store = RecognitionRoiStore()

        self._starting_monitoring = False
        self._stopping_monitoring = False
        self._control_debounce_ms = 150
        self._stop_debounce_timer = QTimer(self)
        self._stop_debounce_timer.setSingleShot(True)
        self._stop_debounce_timer.timeout.connect(self._stop_monitoring_now)
        self._start_debounce_timer = QTimer(self)
        self._start_debounce_timer.setSingleShot(True)
        self._start_debounce_timer.timeout.connect(self._start_monitoring_now)

        self._setup_ui()

        self.monitor_task = MonitorTask(
            task_service=self.service_coordinator.task_service,
            config_service=self.service_coordinator.config_service,
        )
        self._session = MonitorSession(self.monitor_task, log_prefix="Monitor")
        self._session.set_callbacks(
            on_frame=self._apply_preview_from_pil,
            on_capture_failure_clear=self._emit_preview_cleared,
            on_controller_disconnected=self._on_session_controller_disconnected,
        )
        self._bind_auto_task_monitoring()
        self._bind_roi_signals()
        self._update_monitor_status()
        self._update_empty_state()
        self._reposition_preview_overlays()

    def _bind_roi_signals(self) -> None:
        signalBus.monitor_recognition_roi.connect(self._on_recognition_roi)
        cfg.monitor_recognition_roi_enabled.valueChanged.connect(
            self._on_recognition_roi_setting_changed
        )

    def _is_recognition_roi_enabled(self) -> bool:
        return bool(cfg.get(cfg.monitor_recognition_roi_enabled))

    def _on_recognition_roi_setting_changed(self, enabled: bool) -> None:
        if enabled:
            return
        self._roi_store.clear()
        if self._current_pil_image is not None:
            self._render_preview_from_current_frame()

    def _clear_recognition_roi(self) -> None:
        self._roi_store.clear()

    def _on_recognition_roi(self, payload: dict) -> None:
        """仅缓存最新 ROI，不在此处触发重绘；出图时由 _render_preview_from_current_frame 读取。"""
        if not self._is_recognition_roi_enabled():
            return
        self._roi_store.update(payload)

    @property
    def source_preview_pixmap(self) -> Optional[QPixmap]:
        return self._preview_pixmap

    @property
    def is_starting(self) -> bool:
        return self._starting_monitoring

    @property
    def is_monitoring(self) -> bool:
        return self._session.monitoring_active

    def _setup_ui(self) -> None:
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(*panel_outer_margins())
        self.main_layout.setSpacing(PANEL_SECTION_SPACING)

        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(8)

        self._title_icon = IconWidget(FIF.VIDEO, self)
        self._title_icon.setFixedSize(QSize(22, 22))
        self._title_label = BodyLabel(self.tr("Monitor"))
        self._title_label.setStyleSheet("font-size: 20px;")
        self._status_badge = CaptionLabel(self.tr("Idle"), self)
        header_layout.addWidget(self._title_icon, 0, Qt.AlignmentFlag.AlignVCenter)
        header_layout.addWidget(self._title_label, 1, Qt.AlignmentFlag.AlignVCenter)
        header_layout.addWidget(self._status_badge, 0, Qt.AlignmentFlag.AlignVCenter)
        self.main_layout.addLayout(header_layout)

        self._subtitle_label = CaptionLabel(
            self.tr(
                "Live device preview via an independent controller connection. "
                "Click the preview to sync taps to the device."
            ),
            self,
        )
        self.main_layout.addWidget(self._subtitle_label)

        self.preview_card = SimpleCardWidget(self)
        self.preview_card.setClickEnabled(False)
        self.preview_card.setBorderRadius(8)
        self.preview_card.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )

        preview_card_layout = QVBoxLayout(self.preview_card)
        preview_card_layout.setContentsMargins(12, 12, 12, 12)
        preview_card_layout.setSpacing(0)

        self.preview_container = QWidget(self.preview_card)
        self.preview_container.setObjectName("monitorPreviewContainer")
        self.preview_container.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        container_layout = QVBoxLayout(self.preview_container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)
        container_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.preview_label = _ClickablePreviewLabel(self.preview_container)
        self.preview_label.setObjectName("monitorPreviewLabel")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setMinimumHeight(360)
        self.preview_label.setMinimumWidth(640)
        self.preview_label.setSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed
        )
        self.preview_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.preview_label.clicked.connect(self._on_preview_clicked)
        apply_fluent_tooltip(
            self.preview_label,
            self.tr("Click to sync this frame to the device"),
        )
        container_layout.addWidget(
            self.preview_label, 0, Qt.AlignmentFlag.AlignCenter
        )
        preview_card_layout.addWidget(self.preview_container, 1)
        self.main_layout.addWidget(self.preview_card, 1)

        self._empty_hint = CaptionLabel(
            self.tr("Preview will appear when monitoring starts"),
            self.preview_container,
        )
        self._empty_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_hint.setWordWrap(True)
        self._empty_hint.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents, True
        )

        self._fps_overlay = BodyLabel(self.tr("FPS: --"), self.preview_container)
        self._fps_overlay.setObjectName("monitorFpsOverlay")
        self._fps_overlay.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents, True
        )
        self._fps_overlay.setWordWrap(False)

        self._loading_overlay = QWidget(self.preview_container)
        self._loading_overlay.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents
        )
        loading_layout = QHBoxLayout(self._loading_overlay)
        loading_layout.setContentsMargins(0, 0, 0, 0)
        loading_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._loading_indicator = IndeterminateProgressRing(self._loading_overlay)
        self._loading_indicator.setFixedSize(36, 36)
        loading_layout.addWidget(self._loading_indicator)
        self._loading_overlay.hide()

        info_layout = QHBoxLayout()
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(12)
        self._resolution_label = CaptionLabel(self.tr("Resolution: --"), self)
        self._capture_rate_label = CaptionLabel("", self)
        self._update_capture_rate_label()
        cfg.monitor_capture_fps.valueChanged.connect(
            lambda *_: self._update_capture_rate_label()
        )
        info_layout.addWidget(self._resolution_label)
        info_layout.addStretch(1)
        info_layout.addWidget(self._capture_rate_label)
        self.main_layout.addLayout(info_layout)

        self.control_card = SimpleCardWidget(self)
        self.control_card.setClickEnabled(False)
        self.control_card.setBorderRadius(8)
        control_layout = QHBoxLayout(self.control_card)
        control_layout.setContentsMargins(12, 10, 12, 10)
        control_layout.setSpacing(12)

        self.monitor_control_button = PrimaryPushButton(
            self.tr("Start Monitoring"), self.control_card
        )
        self.monitor_control_button.setIcon(FIF.PLAY)
        self.monitor_control_button.setIconSize(QSize(18, 18))
        self.monitor_control_button.clicked.connect(self._on_monitor_control_clicked)
        apply_fluent_tooltip(
            self.monitor_control_button,
            self.tr("Start monitoring task"),
        )

        self.save_button = PushButton(self.tr("Save Screenshot"), self.control_card)
        self.save_button.setIcon(FIF.CAMERA)
        self.save_button.setIconSize(QSize(18, 18))
        self.save_button.clicked.connect(self._on_save_screenshot)
        apply_fluent_tooltip(
            self.save_button,
            self.tr("Capture the current preview and store it on disk"),
        )

        self._control_hint_label = CaptionLabel(
            self.tr("Monitoring starts automatically when a task runs"),
            self.control_card,
        )
        control_layout.addWidget(self.monitor_control_button)
        control_layout.addWidget(self.save_button)
        control_layout.addStretch(1)
        control_layout.addWidget(self._control_hint_label)
        self.main_layout.addWidget(self.control_card, 0)

        self.main_layout.setStretch(0, 0)
        self.main_layout.setStretch(1, 0)
        self.main_layout.setStretch(2, 1)
        self.main_layout.setStretch(3, 0)
        self.main_layout.setStretch(4, 0)

        self._last_frame_timestamp: Optional[float] = None
        self._last_fps_overlay_update: Optional[float] = None

        qconfig.themeChanged.connect(self._apply_theme_styles)
        self._apply_theme_styles()

    def _apply_theme_styles(self, *_args) -> None:
        muted = "rgba(128, 128, 128, 0.92)" if isDarkTheme() else "rgba(96, 96, 96, 0.95)"
        for label in (
            self._subtitle_label,
            self._resolution_label,
            self._capture_rate_label,
            self._control_hint_label,
            self._empty_hint,
        ):
            label.setStyleSheet(f"color: {muted};")

        preview_bg = (
            "rgba(255, 255, 255, 0.04)"
            if isDarkTheme()
            else "rgba(0, 0, 0, 0.03)"
        )
        self.preview_label.setStyleSheet(
            f"""
            QLabel#monitorPreviewLabel {{
                border-radius: 8px;
                background-color: {preview_bg};
            }}
            """
        )
        self.preview_container.setStyleSheet(
            "QWidget#monitorPreviewContainer { background: transparent; }"
        )
        self._fps_overlay.setStyleSheet(
            """
            QLabel#monitorFpsOverlay {
                background-color: rgba(0, 0, 0, 0.55);
                color: #ffffff;
                border-radius: 6px;
                padding: 2px 8px;
                font-size: 12px;
            }
            """
        )
        self._loading_overlay.setStyleSheet(
            "background-color: rgba(0, 0, 0, 0.35); border-radius: 8px;"
        )
        self._update_monitor_status()

    def _apply_status_badge_style(self, state: str) -> None:
        styles = {
            "idle": ("rgba(128, 128, 128, 0.22)", "rgba(160, 160, 160, 0.95)"),
            "connecting": ("rgba(227, 179, 65, 0.22)", "#e3b341"),
            "running": ("rgba(80, 200, 120, 0.22)", "#50c878"),
        }
        bg, fg = styles.get(state, styles["idle"])
        self._status_badge.setStyleSheet(
            f"background-color: {bg}; color: {fg}; "
            "border-radius: 10px; padding: 4px 10px;"
        )

    def _update_monitor_status(self) -> None:
        session = getattr(self, "_session", None)
        monitoring_active = session is not None and session.monitoring_active
        if self._starting_monitoring:
            self._status_badge.setText(self.tr("Connecting"))
            self._apply_status_badge_style("connecting")
        elif monitoring_active:
            self._status_badge.setText(self.tr("Running"))
            self._apply_status_badge_style("running")
        else:
            self._status_badge.setText(self.tr("Idle"))
            self._apply_status_badge_style("idle")

    def _update_capture_rate_label(self) -> None:
        fps = max(1, int(cfg.get(cfg.monitor_capture_fps)))
        self._capture_rate_label.setText(
            self.tr("Capture rate: {} FPS").format(fps)
        )

    def _update_resolution_label(self) -> None:
        if self._image_width and self._image_height:
            self._resolution_label.setText(
                self.tr("Resolution: {} × {}").format(
                    self._image_width, self._image_height
                )
            )
        else:
            self._resolution_label.setText(self.tr("Resolution: --"))

    def _update_empty_state(self) -> None:
        visible = self._preview_pixmap is None or self._preview_pixmap.isNull()
        self._empty_hint.setVisible(visible)
        if visible:
            self._reposition_preview_overlays()

    def _reposition_preview_overlays(self) -> None:
        if not hasattr(self, "preview_container"):
            return
        container_size = self.preview_container.size()
        if container_size.width() <= 0 or container_size.height() <= 0:
            return

        if self._empty_hint.isVisible():
            hint_width = min(container_size.width() - 48, 360)
            self._empty_hint.setFixedWidth(max(hint_width, 120))
            hint_height = self._empty_hint.sizeHint().height()
            self._empty_hint.move(
                max(0, (container_size.width() - self._empty_hint.width()) // 2),
                max(0, (container_size.height() - hint_height) // 2),
            )

        if self._loading_overlay.isVisible():
            self._loading_overlay.setGeometry(
                0, 0, container_size.width(), container_size.height()
            )

        if self._fps_overlay and self.preview_label.width() > 0:
            preview_pos = self.preview_label.mapTo(self.preview_container, QPoint(0, 0))
            margin = 12
            self._fps_overlay.adjustSize()
            overlay_size = self._fps_overlay.size()
            x = preview_pos.x() + self.preview_label.width() - overlay_size.width() - margin
            y = preview_pos.y() + margin
            if x < preview_pos.x():
                x = preview_pos.x()
            self._fps_overlay.move(x, y)

    def _bind_auto_task_monitoring(self) -> None:
        if hasattr(self.service_coordinator, "fs_signals"):
            self.service_coordinator.fs_signals.fs_start_button_status.connect(
                self._on_task_status_changed
            )
        signalBus.task_flow_finished.connect(self._on_task_flow_finished)

    def _set_loading(self, loading: bool) -> None:
        if self._starting_monitoring == loading:
            return
        self._starting_monitoring = loading
        self.loading_changed.emit(loading)
        if loading:
            self._loading_overlay.show()
            self._loading_indicator.start()
        else:
            self._loading_overlay.hide()
            self._loading_indicator.stop()
        self._update_monitor_status()
        self._reposition_preview_overlays()

    def _emit_preview_cleared(self) -> None:
        self._preview_pixmap = None
        self._current_pil_image = None
        self._image_width = None
        self._image_height = None
        self._roi_store.clear()
        self.preview_label.clear()
        self._update_fps_overlay(None)
        self._update_resolution_label()
        self._update_empty_state()
        self.preview_cleared.emit()

    def _load_placeholder_image(self) -> None:
        pixmap = QPixmap("app/assets/icons/logo.png")
        if pixmap.isNull():
            logger.warning("无法加载监控子页面的占位图标，路径可能不存在。")
            return
        self._preview_pixmap = pixmap
        self._refresh_preview_image()
        self._update_fps_overlay(None)
        self.preview_pixmap_changed.emit(self._preview_pixmap)

    def _refresh_preview_image(self) -> None:
        if not self._preview_pixmap:
            self._update_empty_state()
            self._reposition_preview_overlays()
            return
        target_size = self.preview_label.size()
        if target_size.width() <= 0 or target_size.height() <= 0:
            self._reposition_preview_overlays()
            return
        scaled = self._preview_pixmap.scaled(
            target_size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.preview_label.setPixmap(scaled)
        self._preview_scaled_size = scaled.size()
        self._update_empty_state()
        self._reposition_preview_overlays()

    def set_preview_pixmap(self, pixmap: Optional[QPixmap]) -> None:
        self._preview_pixmap = pixmap
        self._current_pil_image = None
        self._refresh_preview_image()
        if pixmap is not None and not pixmap.isNull():
            self.preview_pixmap_changed.emit(pixmap)
        else:
            self.preview_cleared.emit()

    def _update_preview_size_policy(
        self, image_width: int, image_height: int, force_update: bool = False
    ) -> None:
        is_landscape = image_width >= image_height
        if (
            not force_update
            and self._is_landscape == is_landscape
            and self._image_width == image_width
            and self._image_height == image_height
        ):
            current_size = self.preview_label.size()
            if current_size.width() > 0 and current_size.height() > 0:
                return

        self._image_width = image_width
        self._image_height = image_height
        self._is_landscape = is_landscape

        aspect_ratio = image_width / image_height if image_height > 0 else 1.0
        container_width = max(self.preview_container.width() - 24, 640)
        container_height = max(self.preview_container.height() - 24, 360)
        available_width = container_width if container_width > 0 else self.width() - 56
        available_height = (
            container_height if container_height > 0 else self.height() - 260
        )

        if is_landscape:
            target_width = min(available_width, 1280)
            target_height = int(target_width / aspect_ratio)
            if target_height > available_height:
                target_height = available_height
                target_width = int(target_height * aspect_ratio)
        else:
            target_height = min(available_height, 1280)
            target_width = int(target_height * aspect_ratio)
            if target_width > available_width:
                target_width = available_width
                target_height = int(target_width / aspect_ratio)

        min_width = 640 if is_landscape else 360
        min_height = 360 if is_landscape else 640
        target_width = max(target_width, min_width)
        target_height = max(target_height, min_height)

        self.preview_label.setFixedSize(target_width, target_height)
        self.preview_label.setSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed
        )

    def _apply_preview_from_pil(self, pil_image: Image.Image) -> None:
        image_width, image_height = pil_image.size
        self._update_preview_size_policy(image_width, image_height)

        rgb_image = pil_image.convert("RGB")
        self._current_pil_image = rgb_image.copy()
        self._render_preview_from_current_frame()

        current_timestamp = time()
        fps_value: Optional[float] = None
        if self._last_frame_timestamp is not None:
            interval = current_timestamp - self._last_frame_timestamp
            if interval > 0:
                fps_value = 1.0 / interval
        self._last_frame_timestamp = current_timestamp
        self._update_fps_overlay(fps_value)
        self._update_resolution_label()
        self._update_empty_state()

    def _render_preview_from_current_frame(self) -> None:
        if self._current_pil_image is None:
            return
        image_width, image_height = self._current_pil_image.size
        bytes_per_line = image_width * 3
        buffer = self._current_pil_image.tobytes("raw", "RGB")
        qimage = QImage(
            buffer,
            image_width,
            image_height,
            bytes_per_line,
            QImage.Format.Format_RGB888,
        )
        pixmap = QPixmap.fromImage(qimage)
        if self._is_recognition_roi_enabled():
            active_roi = self._roi_store.peek()
            if active_roi and active_roi.get("box"):
                label = active_roi.get("node", "")
                phase = active_roi.get("phase", "hit")
                pixmap = draw_roi_on_pixmap(
                    pixmap, active_roi["box"], label=label, phase=phase
                )
        self._preview_pixmap = pixmap
        self._refresh_preview_image()
        self.preview_pixmap_changed.emit(self._preview_pixmap)

    def _update_fps_overlay(self, fps_value: Optional[float]) -> None:
        if fps_value is None:
            text = f"{self.tr('FPS')}: --"
            self._last_fps_overlay_update = None
        else:
            now = time()
            if (
                self._last_fps_overlay_update is not None
                and now - self._last_fps_overlay_update < 0.5
            ):
                return
            self._last_fps_overlay_update = now
            text = f"{self.tr('FPS')}: {fps_value:.1f}"
        self._fps_overlay.setText(text)
        self._fps_overlay.adjustSize()
        self._reposition_preview_overlays()

    def _set_monitor_control_running(self, running: bool) -> None:
        if not hasattr(self, "monitor_control_button"):
            return
        if running:
            self.monitor_control_button.setText(self.tr("Stop Monitoring"))
            self.monitor_control_button.setIcon(FIF.CLOSE)
            self.monitor_control_button.setToolTip(self.tr("Stop monitoring task"))
        else:
            self.monitor_control_button.setText(self.tr("Start Monitoring"))
            self.monitor_control_button.setIcon(FIF.PLAY)
            self.monitor_control_button.setToolTip(self.tr("Start monitoring task"))
        self._update_monitor_status()

    async def _on_session_controller_disconnected(self) -> None:
        if not (self._session.monitoring_active or self._starting_monitoring):
            return
        logger.warning("[Monitor] 检测到控制器断开，请求停止监控")
        self._request_stop_monitoring(reason="controller_disconnected")

    def _schedule_controller_disconnection(self) -> None:
        if not self._session.monitoring_active:
            return
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        if loop and loop.is_running():
            loop.create_task(self._on_session_controller_disconnected())

    def _on_task_flow_finished(self, payload: dict) -> None:
        self._clear_recognition_roi()
        if self._session.monitoring_active or self._starting_monitoring:
            logger.debug(f"[Monitor] 收到 task_flow_finished: {payload}，请求停止监控")
            self._request_stop_monitoring(reason="task_flow_finished")

    def _on_task_status_changed(self, status: dict) -> None:
        is_running = status.get("text") == "STOP"
        if (
            is_running
            and not self._session.monitoring_active
            and not self._starting_monitoring
        ):
            self._start_monitoring(auto=True)
        elif not is_running and self._session.monitoring_active:
            self._request_stop_monitoring(reason="task_stopped")

    def _request_stop_monitoring(self, *, reason: str = "") -> None:
        if not (self._session.monitoring_active or self._starting_monitoring):
            return
        if self._stopping_monitoring:
            logger.debug(f"[Monitor] stop 已在进行中，忽略: {reason}")
            return
        if self._stop_debounce_timer.isActive():
            self._stop_debounce_timer.stop()
        self._set_loading(False)
        self._session.stop_loop()
        self._stop_debounce_timer.start(self._control_debounce_ms)

    def _is_control_busy(self) -> bool:
        return (
            self._starting_monitoring
            or self._stopping_monitoring
            or self._stop_debounce_timer.isActive()
            or self._start_debounce_timer.isActive()
        )

    def _set_control_button_enabled(self, enabled: bool) -> None:
        if hasattr(self, "monitor_control_button"):
            self.monitor_control_button.setEnabled(enabled)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if self._image_width is not None and self._image_height is not None:
            self._update_preview_size_policy(
                self._image_width, self._image_height, force_update=True
            )
        self._refresh_preview_image()
        self._reposition_preview_overlays()

    def showEvent(self, event) -> None:
        super().showEvent(event)
        QTimer.singleShot(0, self._reposition_preview_overlays)

    def _on_save_screenshot(self) -> None:
        if not self._current_pil_image:
            logger.warning("监控子页面：当前不存在可保存的截图。")
            return
        save_dir = Path("debug") / "save_screen"
        save_dir.mkdir(parents=True, exist_ok=True)
        filename = datetime.now().strftime("screenshot_%Y%m%d_%H%M%S.png")
        save_path = save_dir / filename
        try:
            self._current_pil_image.save(save_path)
            message = self.tr("Screenshot saved to ") + str(save_path)
            signalBus.info_bar_requested.emit("success", message)
        except Exception as exc:
            logger.exception("监控子页面：保存截图失败：%s", exc)

    def _on_preview_clicked(self, x: int, y: int) -> None:
        if not self.service_coordinator:
            return
        if not self._session.is_controller_connected():
            self._schedule_controller_disconnection()
            return
        handler = getattr(self.service_coordinator, "sync_monitor_preview_click", None)
        if callable(handler):
            try:
                handler()
            except Exception as exc:
                logger.exception(f"同步预览点击至设备失败：{exc}")

        coords = self._map_visual_click_to_device(x, y)
        if not coords:
            return
        controller = getattr(self.monitor_task.maafw, "controller", None)
        if controller is None:
            return
        try:
            controller.post_click(*coords).wait()
        except Exception as exc:
            logger.exception("监控子页面：同步点击失败：%s", exc)

    def _map_visual_click_to_device(self, x: int, y: int) -> tuple[int, int] | None:
        if (
            not self._preview_scaled_size
            or self._preview_scaled_size.width() <= 0
            or self._preview_scaled_size.height() <= 0
        ):
            return None

        label_width = self.preview_label.width()
        label_height = self.preview_label.height()
        scaled_width = self._preview_scaled_size.width()
        scaled_height = self._preview_scaled_size.height()

        x_offset = max(0, (label_width - scaled_width) // 2)
        y_offset = max(0, (label_height - scaled_height) // 2)

        rel_x = x - x_offset
        rel_y = y - y_offset
        if rel_x < 0 or rel_y < 0 or rel_x >= scaled_width or rel_y >= scaled_height:
            return None

        normalized_x = rel_x / scaled_width
        normalized_y = rel_y / scaled_height

        target_width = 1280
        target_height = 720
        device_x = int(round(normalized_x * target_width))
        device_y = int(round(normalized_y * target_height))
        device_x = max(0, min(device_x, target_width - 1))
        device_y = max(0, min(device_y, target_height - 1))
        return device_x, device_y

    def _on_monitor_control_clicked(self) -> None:
        if self._is_control_busy():
            return
        if self._session.monitoring_active:
            self._set_control_button_enabled(False)
            self._request_stop_monitoring(reason="manual_or_ui")
        else:
            self._set_control_button_enabled(False)
            self._request_start_monitoring(manual=True)

    def _request_start_monitoring(self, *, manual: bool = False) -> None:
        if manual:
            if (
                self._session.monitoring_active
                or self._starting_monitoring
                or self._stopping_monitoring
            ):
                self._set_control_button_enabled(True)
                return
            if self._start_debounce_timer.isActive():
                self._start_debounce_timer.stop()
            self._start_debounce_timer.start(self._control_debounce_ms)
            return
        self._start_monitoring_impl(auto=True)

    def _start_monitoring_now(self) -> None:
        self._start_monitoring_impl(auto=False)

    def _start_monitoring(self, *, auto: bool = False) -> None:
        """任务流自动启动入口。"""
        self._start_monitoring_impl(auto=auto)

    def _start_monitoring_impl(self, *, auto: bool = False) -> None:
        if self._session.monitoring_active or self._starting_monitoring:
            if not auto:
                self._set_control_button_enabled(True)
            return

        logger.info(f"[Monitor] 开始启动监控（{'自动' if auto else '手动'}）")
        self._set_loading(True)

        async def _start_sequence() -> None:
            try:
                started = await self._session.run_startup_sequence(
                    should_abort=lambda: not self._starting_monitoring,
                )
                if not started:
                    if self._starting_monitoring and not auto:
                        signalBus.info_bar_requested.emit(
                            "error",
                            self.tr(
                                "Device connection failed, cannot start monitoring"
                            ),
                        )
                    return

                self._set_monitor_control_running(True)
                if not auto:
                    signalBus.info_bar_requested.emit(
                        "success", self.tr("Monitoring started")
                    )
            except Exception as exc:
                logger.error(f"[Monitor] 启动监控失败: {exc}", exc_info=True)
                if self._starting_monitoring and not auto:
                    signalBus.info_bar_requested.emit(
                        "error", self.tr("Failed to start monitoring: ") + str(exc)
                    )
                if self._session.monitoring_active:
                    self._session.stop_loop()
            finally:
                self._set_loading(False)
                self._set_control_button_enabled(True)

        QTimer.singleShot(0, lambda: asyncio.create_task(_start_sequence()))

    def _stop_monitoring(self) -> None:
        self._request_stop_monitoring(reason="manual_or_ui")

    def _stop_monitoring_now(self) -> None:
        if self._stopping_monitoring:
            self._set_control_button_enabled(True)
            return

        self._stopping_monitoring = True
        self._set_loading(False)

        async def _stop_sequence() -> None:
            try:
                await self._session.stop()
                self._emit_preview_cleared()
                self._set_monitor_control_running(False)
                logger.info("[Monitor] 监控已停止")
            except Exception as exc:
                logger.error(f"[Monitor] 停止监控失败: {exc}", exc_info=True)
            finally:
                self._stopping_monitoring = False
                self._set_control_button_enabled(True)

        QTimer.singleShot(0, lambda: asyncio.create_task(_stop_sequence()))

    def lock_monitor_page(self, stop_loop: bool = True) -> None:
        if stop_loop:
            self._session.stop_loop()
        else:
            self._session.deactivate()
        self._set_monitor_control_running(False)
