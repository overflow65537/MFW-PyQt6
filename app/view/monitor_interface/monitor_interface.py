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
from app.view.monitor.config_monitor_pool import ConfigMonitorPool
from app.view.monitor.recognition_roi_store import RecognitionRoiStore
from app.view.monitor.roi_overlay import draw_roi_on_pixmap
from app.view.task_interface.components.panel_splitter import (
    PANEL_SECTION_SPACING,
    panel_outer_margins,
)
from app.view.monitor_interface.multi_config_monitor_grid import MultiConfigMonitorGrid
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
        self._bound_config_id: Optional[str] = None
        self._last_config_switch_id: Optional[str] = None
        self._config_switch_seq: int = 0
        self._pool: Optional[ConfigMonitorPool] = None
        self._multi_grid: Optional[MultiConfigMonitorGrid] = None

        self._starting_monitoring = False
        self._stopping_monitoring = False
        self._pending_stop_config_id: Optional[str] = None
        self._control_debounce_ms = 150
        self._stop_debounce_timer = QTimer(self)
        self._stop_debounce_timer.setSingleShot(True)
        self._stop_debounce_timer.timeout.connect(self._stop_monitoring_now)
        self._start_debounce_timer = QTimer(self)
        self._start_debounce_timer.setSingleShot(True)
        self._start_debounce_timer.timeout.connect(self._start_monitoring_now)

        self._setup_ui()

        self._legacy_monitor_task = MonitorTask(
            task_service=self.service_coordinator.task_service,
            config_service=self.service_coordinator.config_service,
        )
        self._legacy_session = MonitorSession(
            self._legacy_monitor_task, log_prefix="Monitor"
        )
        self._legacy_session.set_callbacks(
            on_frame=self._enqueue_preview_frame,
            on_capture_failure_clear=self._emit_preview_cleared,
            on_controller_disconnected=self._on_session_controller_disconnected,
        )
        self._init_monitor_pool()
        self._bind_auto_task_monitoring()
        self._bind_roi_signals()
        self._apply_layout_mode()
        self._update_monitor_status()
        self._update_empty_state()
        self._reposition_preview_overlays()

    def _use_pooled_monitors(self) -> bool:
        """多实例模式下为每个配置维持独立监控连接，切换时仅换显示。"""
        try:
            return bool(cfg.get(cfg.multi_instance_mode))
        except Exception:
            return False

    def _init_monitor_pool(self) -> None:
        if not self._use_pooled_monitors():
            self._pool = None
            return
        if self._pool is not None:
            return
        self._pool = ConfigMonitorPool(
            self.service_coordinator,
            on_frame=self._on_pooled_frame,
            on_capture_failure_clear=self._on_pooled_capture_cleared,
            on_controller_disconnected=self._on_pooled_controller_disconnected,
        )
        initial_id = self._current_config_id()
        if initial_id:
            self._pool.set_display_config(initial_id)
            self._bound_config_id = initial_id
            self._roi_store = self._pool.get_display_roi_store()
        # 已为运行中的配置补建后台监控连接
        try:
            for cid in self.service_coordinator.running_config_ids():
                self._schedule_pool_monitoring(cid, auto=True)
        except Exception as exc:
            logger.debug("初始化多配置监控池时同步运行中配置失败: %s", exc)

    def _schedule_pool_monitoring(self, config_id: str, *, auto: bool = True) -> None:
        """异步启动池化监控，并在失败时清除加载态。"""
        if self._pool is None or not config_id:
            return

        async def _run() -> None:
            started = await self._pool.ensure_monitoring_when_ready(
                config_id, auto=auto
            )
            if (
                not started
                and self.service_coordinator.is_config_running(config_id)
            ):
                await asyncio.sleep(2.0)
                if self.service_coordinator.is_config_running(config_id):
                    started = await self._pool.ensure_monitoring_when_ready(
                        config_id, auto=auto, timeout_s=30.0
                    )
            if self._multi_grid is not None:
                if started:
                    slot = self._pool.get_slot(config_id)
                    if slot and slot.last_pil_image is not None:
                        self._multi_grid.update_frame(
                            config_id,
                            slot.last_pil_image,
                            roi_store=slot.roi_store,
                        )
                elif self.service_coordinator.is_config_running(config_id):
                    self._multi_grid.clear_monitor_loading(config_id)
            if config_id == self._current_config_id():
                if started:
                    self.sync_task_preview()
                self._set_loading(False)
                self._set_monitor_control_running(
                    self._pool.is_display_monitoring()
                )
            self._update_monitor_status()

        asyncio.create_task(_run())

    def _enqueue_preview_frame(
        self, pil_image: Image.Image, *, config_id: str | None = None
    ) -> None:
        """将帧投递到 Qt 主线程，避免异步循环直接改 UI。"""
        try:
            frame = pil_image.copy()
        except Exception:
            frame = pil_image
        cid = config_id or self._bound_config_id or self._current_config_id() or ""
        QTimer.singleShot(
            0, lambda c=cid, f=frame: self._deliver_preview_frame(c, f)
        )

    def _deliver_preview_frame(self, config_id: str, pil_image: Image.Image) -> None:
        if self._pool is not None:
            slot = self._pool.get_slot(config_id) if config_id else None
            roi_store = slot.roi_store if slot else None
            if self._multi_grid is not None and config_id:
                self._multi_grid.update_frame(
                    config_id, pil_image, roi_store=roi_store
                )
            current_id = self._current_config_id()
            if config_id and config_id == current_id:
                self._bound_config_id = current_id
                self._apply_preview_from_pil(pil_image, config_id=config_id)
            return
        self._apply_preview_from_pil(pil_image, config_id=config_id or None)

    def _on_pooled_frame(self, config_id: str, pil_image: Image.Image) -> None:
        self._enqueue_preview_frame(pil_image, config_id=config_id)

    def _on_pooled_capture_cleared(self, config_id: str) -> None:
        if self._multi_grid is not None:
            self._multi_grid.clear_frame(config_id)
        if config_id == self._bound_config_id:
            self._emit_preview_cleared()

    def _on_pooled_controller_disconnected(self, config_id: str) -> None:
        if config_id != self._bound_config_id:
            return
        if not (self._active_session().monitoring_active or self._starting_monitoring):
            return
        logger.warning("[Monitor] 配置 %s 控制器断开，请求停止监控", config_id)
        self._request_stop_monitoring(reason="controller_disconnected", config_id=config_id)

    @property
    def _session(self) -> MonitorSession:
        if self._pool is not None:
            session = self._pool.get_display_session()
            if session is not None:
                return session
        return self._legacy_session

    @property
    def monitor_task(self) -> MonitorTask:
        if self._pool is not None:
            task = self._pool.get_display_monitor_task()
            if task is not None:
                return task
        return self._legacy_monitor_task

    def _active_session(self) -> MonitorSession:
        return self._session

    def _bind_roi_signals(self) -> None:
        signalBus.monitor_recognition_roi.connect(self._on_recognition_roi)
        signalBus.monitor_recognition_roi_at.connect(self._on_recognition_roi_at)
        cfg.monitor_recognition_roi_enabled.valueChanged.connect(
            self._on_recognition_roi_setting_changed
        )

    def _on_recognition_roi_at(self, config_id: str, payload: dict) -> None:
        """多实例：按配置缓存 ROI，当前显示配置即时重绘。"""
        if not self._is_recognition_roi_enabled():
            return
        if self._pool is not None:
            slot = self._pool.get_slot(config_id)
            if slot is not None:
                slot.roi_store.update(payload)
            if self._multi_grid is not None and slot and slot.last_pil_image:
                self._multi_grid.update_frame(
                    config_id, slot.last_pil_image, roi_store=slot.roi_store
                )
            if config_id == self._bound_config_id:
                if slot is not None:
                    self._roi_store = slot.roi_store
                self._on_recognition_roi(payload)
            return
        if config_id != self._bound_config_id:
            return
        self._on_recognition_roi(payload)

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

    def sync_task_preview(self) -> None:
        """任务页监控预览：仅使用监控池自身采集到的最后一帧。"""
        current_id = self._current_config_id()
        if not current_id:
            return
        self._bound_config_id = current_id
        if self._pool is None:
            return
        slot = self._pool.get_slot(current_id)
        if slot is not None and slot.last_pil_image is not None:
            self._apply_preview_from_pil(
                slot.last_pil_image, config_id=current_id
            )

    @property
    def source_preview_pixmap(self) -> Optional[QPixmap]:
        return self._preview_pixmap

    @property
    def is_starting(self) -> bool:
        if self._pool is not None:
            return self._pool.is_display_starting() or self._starting_monitoring
        return self._starting_monitoring

    @property
    def is_monitoring(self) -> bool:
        if self._pool is not None:
            return self._pool.is_display_monitoring()
        return self._legacy_session.monitoring_active

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

        self._subtitle_label = CaptionLabel("", self)
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

        self._multi_panel = QWidget(self)
        self._multi_panel.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self._multi_panel.setAutoFillBackground(False)
        self._multi_panel.setStyleSheet("background: transparent;")
        multi_panel_layout = QVBoxLayout(self._multi_panel)
        multi_panel_layout.setContentsMargins(0, 0, 0, 0)
        multi_panel_layout.setSpacing(0)
        self._multi_grid = MultiConfigMonitorGrid(
            is_config_running=lambda cid: self.service_coordinator.is_config_running(
                cid
            ),
            parent=self._multi_panel,
        )
        self._multi_grid.tile_clicked.connect(self._on_grid_tile_clicked)
        multi_panel_layout.addWidget(self._multi_grid)
        self._multi_panel.hide()
        self.main_layout.addWidget(self._multi_panel, 1)

        self._single_subtitle_text = self.tr(
            "Live device preview via an independent controller connection. "
            "Click the preview to sync taps to the device."
        )
        self._multi_subtitle_text = self.tr(
            "Multi-instance mode: all configurations are shown below. "
            "Stopped configurations display a power-off indicator. "
            "Click a card to switch the active configuration."
        )

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
        self.main_layout.setStretch(3, 1)
        self.main_layout.setStretch(4, 0)
        self.main_layout.setStretch(5, 0)

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
        if self._multi_grid is not None:
            self._multi_grid.apply_theme()
        self._update_monitor_status()

    def _collect_config_entries(self) -> list[tuple[str, str]]:
        entries: list[tuple[str, str]] = []
        try:
            summaries = self.service_coordinator.config.list_configs()
        except Exception:
            summaries = []
        for summary in summaries:
            if isinstance(summary, dict):
                config_id = summary.get("item_id")
            else:
                config_id = getattr(summary, "item_id", None)
            if not config_id:
                continue
            item = self.service_coordinator.config.get_config(config_id)
            name = item.name if item else str(config_id)
            entries.append((str(config_id), name))
        return entries

    def _rebuild_multi_grid(self) -> None:
        if self._multi_grid is None or self._pool is None:
            return
        self._multi_grid.rebuild(self._collect_config_entries())
        self._multi_grid.set_active_config(self._current_config_id())
        for config_id, _ in self._collect_config_entries():
            slot = self._pool.get_slot(config_id)
            if slot and slot.last_pil_image is not None:
                self._multi_grid.update_frame(
                    config_id, slot.last_pil_image, roi_store=slot.roi_store
                )

    def _apply_layout_mode(self) -> None:
        """单画面 / 多配置网格布局切换。"""
        self._init_monitor_pool()
        multi = self._use_pooled_monitors() and self._pool is not None
        self.preview_card.setVisible(not multi)
        self._multi_panel.setVisible(multi)
        self._resolution_label.setVisible(not multi)
        self.control_card.setVisible(not multi)
        self._subtitle_label.setText(
            self._multi_subtitle_text if multi else self._single_subtitle_text
        )
        if multi:
            self._rebuild_multi_grid()
        self._update_monitor_status()

    def _on_grid_tile_clicked(self, config_id: str) -> None:
        if not config_id:
            return
        try:
            self.service_coordinator.select_config(config_id)
        except Exception as exc:
            logger.warning("切换配置失败: %s", exc)

    def _on_multi_instance_mode_changed(self, _enabled: bool) -> None:
        self._apply_layout_mode()
        if self._pool is not None:
            try:
                for cid in self.service_coordinator.running_config_ids():
                    self._schedule_pool_monitoring(cid, auto=True)
            except Exception:
                pass

    def _on_mica_setting_changed(self, _enabled: bool) -> None:
        if self._multi_grid is not None:
            self._multi_grid.apply_theme()

    def _on_config_list_changed(self, *_args) -> None:
        if self._multi_panel.isVisible():
            self._rebuild_multi_grid()

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
        if self._multi_panel.isVisible():
            try:
                running = len(self.service_coordinator.running_config_ids())
                total = len(self._collect_config_entries())
            except Exception:
                running, total = 0, 0
            if running > 0:
                self._status_badge.setText(
                    self.tr("{0} / {1} running").format(running, total)
                )
                self._apply_status_badge_style("running")
            else:
                self._status_badge.setText(self.tr("Idle"))
                self._apply_status_badge_style("idle")
            return

        if self._pool is not None:
            monitoring_active = self._pool.is_display_monitoring()
        else:
            session = getattr(self, "_legacy_session", None)
            monitoring_active = session is not None and session.monitoring_active
        if self._starting_monitoring or (
            self._pool is not None and self._pool.is_display_starting()
        ):
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
        self.service_coordinator.fs_signal_bus.fs_start_button_status.connect(
            self._on_task_status_changed
        )
        self.service_coordinator.fs_signal_bus.fs_start_button_status_at.connect(
            self._on_task_status_changed_at
        )
        signalBus.task_flow_finished.connect(self._on_task_flow_finished)
        signalBus.task_flow_finished_at.connect(self._on_task_flow_finished_at)
        # 配置切换：优先订阅 Core 信号总线（select_config 必经路径）
        self.service_coordinator.signal_bus.config_changed.connect(
            self._on_active_config_changed
        )
        signalBus.config_run_state_changed.connect(self._on_config_run_state_changed)
        signalBus.multi_instance_mode_changed.connect(
            self._on_multi_instance_mode_changed
        )
        signalBus.micaEnableChanged.connect(self._on_mica_setting_changed)
        self.service_coordinator.fs_signal_bus.fs_config_added.connect(
            self._on_config_list_changed
        )
        self.service_coordinator.fs_signal_bus.fs_config_removed.connect(
            self._on_config_list_changed
        )

    def _on_config_run_state_changed(self, config_id: str, running: bool) -> None:
        """多实例：各配置任务启停时维护对应后台监控连接。"""
        if self._pool is None:
            return
        if self._multi_grid is not None:
            self._multi_grid.set_running(config_id, running)
        if running:
            current_id = self._current_config_id()
            if config_id == current_id:
                self._bound_config_id = current_id
                self._emit_preview_cleared(clear_roi=False)
            self._schedule_pool_monitoring(config_id, auto=True)
            self._update_monitor_status()
            return

        async def _stop_config_monitor() -> None:
            await self._pool.stop_monitoring(config_id, clear_cache=True)
            if self._multi_grid is not None:
                self._multi_grid.clear_frame(config_id)
            if config_id == self._bound_config_id:
                self._emit_preview_cleared()
                self._set_monitor_control_running(False)
            self._update_monitor_status()

        asyncio.create_task(_stop_config_monitor())

    def _current_config_id(self) -> str:
        try:
            return str(self.service_coordinator.config_service.current_config_id or "")
        except Exception:
            return ""

    def _on_task_status_changed_at(self, config_id: str, status: dict) -> None:
        """多实例：后台配置由 config_run_state_changed 维护；此处仅同步当前配置 UI。"""
        if self._pool is not None:
            if config_id != self._current_config_id():
                return
            is_running = status.get("text") == "STOP"
            self._set_monitor_control_running(
                self._pool.is_display_monitoring() if is_running else False
            )
            return
        if config_id != self._current_config_id():
            return
        self._on_task_status_changed(status)

    def _on_task_flow_finished_at(self, config_id: str, payload: dict) -> None:
        """多实例：停止对应配置的监控；单实例走旧逻辑。"""
        if self._pool is not None:
            if config_id == self._bound_config_id:
                self._clear_recognition_roi()
            asyncio.create_task(
                self._pool.stop_monitoring(config_id, clear_cache=True)
            )
            if config_id == self._bound_config_id:
                self._emit_preview_cleared()
                self._set_monitor_control_running(False)
            return
        if config_id != self._bound_config_id:
            return
        self._on_task_flow_finished(payload)

    def _force_clear_monitor_area(self, *, clear_roi: bool = True) -> None:
        """切换配置时强制清空监控区域，避免上一配置最后一帧残留。"""
        self._config_switch_seq += 1
        self._last_frame_timestamp = None
        self._emit_preview_cleared(clear_roi=clear_roi)
        if hasattr(self, "preview_label"):
            self.preview_label.clear()
        if hasattr(self, "preview_container"):
            self.preview_container.update()
        self._reposition_preview_overlays()

    def _on_active_config_changed(self, config_id: str) -> None:
        """当前激活配置变化：多实例先强制清空再按需恢复；单实例仍重连。"""
        target_id = config_id or self._current_config_id()

        if self._pool is not None:
            if target_id == self._last_config_switch_id:
                return
            self._last_config_switch_id = target_id
            self._force_clear_monitor_area(clear_roi=False)

            self._bound_config_id = target_id
            self._pool.set_display_config(target_id)
            self._roi_store = self._pool.get_display_roi_store()
            if self._multi_grid is not None:
                self._multi_grid.set_active_config(target_id)

            switch_seq = self._config_switch_seq

            def _maybe_restore_target_preview() -> None:
                if switch_seq != self._config_switch_seq:
                    return
                if self._bound_config_id != target_id:
                    return
                self.sync_task_preview()

            QTimer.singleShot(0, _maybe_restore_target_preview)
            self._set_monitor_control_running(self._pool.is_display_monitoring())
            self._update_monitor_status()
            return

        self._force_clear_monitor_area()

        if target_id == self._bound_config_id and not (
            self._legacy_session.monitoring_active or self._starting_monitoring
        ):
            return

        was_active = self._legacy_session.monitoring_active or self._starting_monitoring
        if was_active or self._bound_config_id:
            self._request_stop_monitoring(reason="config_changed")
        self._bound_config_id = None
        self._clear_recognition_roi()

        def _maybe_restart() -> None:
            if target_id != self._current_config_id():
                return
            try:
                should_run = bool(
                    self.service_coordinator.is_current_config_running()
                )
            except Exception:
                should_run = False
            if should_run and not (
                self._legacy_session.monitoring_active or self._starting_monitoring
            ):
                self._start_monitoring(auto=True)

        QTimer.singleShot(2 * self._control_debounce_ms + 50, _maybe_restart)

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

    def _emit_preview_cleared(self, *, clear_roi: bool = True) -> None:
        self._preview_pixmap = None
        self._current_pil_image = None
        self._image_width = None
        self._image_height = None
        if clear_roi:
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

    def _apply_preview_from_pil(
        self, pil_image: Image.Image, *, config_id: str | None = None
    ) -> None:
        if config_id is not None and config_id != self._bound_config_id:
            return
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
        if self._pool is not None:
            return
        self._clear_recognition_roi()
        if self._legacy_session.monitoring_active or self._starting_monitoring:
            logger.debug(f"[Monitor] 收到 task_flow_finished: {payload}，请求停止监控")
            self._request_stop_monitoring(reason="task_flow_finished")

    def _on_task_status_changed(self, status: dict) -> None:
        if self._pool is not None:
            return
        is_running = status.get("text") == "STOP"
        current_id = self._current_config_id()
        if is_running:
            if (
                self._legacy_session.monitoring_active
                and self._bound_config_id != current_id
            ):
                self._request_stop_monitoring(reason="config_switch_while_running")
                self._emit_preview_cleared()
                self._bound_config_id = None
                QTimer.singleShot(
                    2 * self._control_debounce_ms + 50,
                    lambda: self._start_monitoring(auto=True),
                )
                return
            if (
                not self._legacy_session.monitoring_active
                and not self._starting_monitoring
            ):
                self._start_monitoring(auto=True)
        elif not is_running and self._legacy_session.monitoring_active:
            if self._bound_config_id in (None, "", current_id):
                self._request_stop_monitoring(reason="task_stopped")

    def _request_stop_monitoring(
        self, *, reason: str = "", config_id: str | None = None
    ) -> None:
        target_id = config_id or self._bound_config_id or self._current_config_id()
        if self._pool is not None:
            slot = self._pool.get_slot(target_id)
            if slot is None or not (
                slot.session.monitoring_active or slot.starting
            ):
                return
            if self._stopping_monitoring:
                logger.debug("[Monitor] stop 已在进行中，忽略: %s", reason)
                return
            if self._stop_debounce_timer.isActive():
                self._stop_debounce_timer.stop()
            self._set_loading(False)
            slot.session.stop_loop()
            self._pending_stop_config_id = target_id
            self._stop_debounce_timer.start(self._control_debounce_ms)
            return

        if not (
            self._legacy_session.monitoring_active or self._starting_monitoring
        ):
            return
        if self._stopping_monitoring:
            logger.debug(f"[Monitor] stop 已在进行中，忽略: {reason}")
            return
        if self._stop_debounce_timer.isActive():
            self._stop_debounce_timer.stop()
        self._set_loading(False)
        self._legacy_session.stop_loop()
        self._pending_stop_config_id = None
        self._stop_debounce_timer.start(self._control_debounce_ms)

    def _is_control_busy(self) -> bool:
        pool_busy = False
        if self._pool is not None:
            pool_busy = self._pool.is_display_starting() or self._pool.is_display_stopping()
        return (
            self._starting_monitoring
            or self._stopping_monitoring
            or pool_busy
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
        if self._multi_grid is not None and self._multi_panel.isVisible():
            self._multi_grid.refresh_all_previews()
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
        if self.is_monitoring:
            self._set_control_button_enabled(False)
            self._request_stop_monitoring(reason="manual_or_ui")
        else:
            self._set_control_button_enabled(False)
            self._request_start_monitoring(manual=True)

    def _request_start_monitoring(self, *, manual: bool = False) -> None:
        if manual:
            if (
                self.is_monitoring
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
        target_id = self._current_config_id()
        self._bound_config_id = target_id

        if self._pool is not None:
            if self._pool.is_display_monitoring():
                if not auto:
                    self._set_control_button_enabled(True)
                return
            self._pool.set_display_config(target_id)
            self._roi_store = self._pool.get_display_roi_store()
            logger.info(
                "[Monitor] 开始启动监控（%s），配置=%s",
                "自动" if auto else "手动",
                target_id or "?",
            )
            self._starting_monitoring = True
            self._set_loading(True)

            async def _start_sequence() -> None:
                try:
                    if self.service_coordinator.is_config_running(target_id):
                        started = await self._pool.ensure_monitoring_when_ready(
                            target_id, auto=auto
                        )
                    else:
                        started = await self._pool.ensure_monitoring(
                            target_id, auto=auto
                        )
                    if not started:
                        if not auto:
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
                    logger.error("[Monitor] 启动监控失败: %s", exc, exc_info=True)
                    if not auto:
                        signalBus.info_bar_requested.emit(
                            "error",
                            self.tr("Failed to start monitoring: ") + str(exc),
                        )
                finally:
                    self._starting_monitoring = False
                    self._set_loading(False)
                    self._set_control_button_enabled(True)

            QTimer.singleShot(0, lambda: asyncio.create_task(_start_sequence()))
            return

        if self._legacy_session.monitoring_active or self._starting_monitoring:
            if not auto:
                self._set_control_button_enabled(True)
            return

        logger.info(
            f"[Monitor] 开始启动监控（{'自动' if auto else '手动'}）"
            f"，配置={target_id or '?'}"
        )
        self._set_loading(True)

        async def _start_sequence() -> None:
            try:
                started = await self._legacy_session.run_startup_sequence(
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
                if self._legacy_session.monitoring_active:
                    self._legacy_session.stop_loop()
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
        stop_id = (
            self._pending_stop_config_id
            or self._bound_config_id
            or self._current_config_id()
        )

        async def _stop_sequence() -> None:
            try:
                if self._pool is not None:
                    await self._pool.stop_monitoring(stop_id, clear_cache=False)
                    if stop_id == self._bound_config_id:
                        self._emit_preview_cleared()
                        self._set_monitor_control_running(False)
                else:
                    await self._legacy_session.stop()
                    self._emit_preview_cleared()
                    self._bound_config_id = None
                    self._set_monitor_control_running(False)
                logger.info("[Monitor] 监控已停止")
            except Exception as exc:
                logger.error(f"[Monitor] 停止监控失败: {exc}", exc_info=True)
            finally:
                self._stopping_monitoring = False
                self._pending_stop_config_id = None
                self._set_control_button_enabled(True)

        QTimer.singleShot(0, lambda: asyncio.create_task(_stop_sequence()))

    def lock_monitor_page(self, stop_loop: bool = True) -> None:
        if self._pool is not None:
            self._pool.shutdown_sync()
        elif stop_loop:
            self._legacy_session.stop_loop()
        else:
            self._legacy_session.deactivate()
        self._set_monitor_control_running(False)
