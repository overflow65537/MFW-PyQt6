from typing import Optional

from asyncify import asyncify
import asyncio
from datetime import datetime
from pathlib import Path
from time import time

from PIL import Image
from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QHBoxLayout,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from qfluentwidgets import (
    BodyLabel,
    FluentIcon as FIF,
    IndeterminateProgressBar,
    PixmapLabel,
    PrimaryPushButton,
)

from app.core.core import ServiceCoordinator
from app.core.runner.monitor_task import MonitorTask
from app.utils.logger import (
    logger,
    restore_asyncify_logging,
    restore_qasync_logging,
    suppress_asyncify_logging,
    suppress_qasync_logging,
)
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
    """显示实时画面并提供截图/监控设置入口的子页面。"""

    def __init__(self, service_coordinator: ServiceCoordinator, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("MonitorInterface")
        self.service_coordinator = service_coordinator
        self._preview_pixmap: Optional[QPixmap] = None
        self._current_pil_image: Optional[Image.Image] = None
        self._preview_scaled_size: QSize = QSize(0, 0)
        self._locked = True
        self._lock_overlay: Optional[QWidget] = None
        self._unlock_progress: Optional[IndeterminateProgressBar] = None
        self._setup_ui()
        self._create_lock_overlay()
        self.monitor_task = MonitorTask(
            task_service=self.service_coordinator.task_service,
            config_service=self.service_coordinator.config_service,
        )
        self._monitor_loop_task: Optional[asyncio.Task] = None
        self._monitoring_active = False
        self._target_interval = 1.0 / 30

    def _setup_ui(self) -> None:
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(28, 18, 28, 18)
        self.main_layout.setSpacing(14)

        self.preview_label = _ClickablePreviewLabel(self)
        self.preview_label.setObjectName("monitorPreviewLabel")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setMinimumHeight(360)
        self.preview_label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.preview_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.preview_label.setStyleSheet(
            """
            QLabel#monitorPreviewLabel {
                border-radius: 16px;
                border: 1px solid rgba(255, 255, 255, 0.12);
                background-color: rgba(255, 255, 255, 0.02);
            }
            """
        )
        self.main_layout.addWidget(self.preview_label, 1)
        self.preview_label.clicked.connect(self._on_preview_clicked)
        self.preview_label.setToolTip(self.tr("Click to sync this frame to the device"))
        self._fps_overlay = BodyLabel(self.tr("FPS: --"), self.preview_label)
        self._fps_overlay.setObjectName("monitorFpsOverlay")
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
        self._fps_overlay.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents, True
        )
        self._fps_overlay.adjustSize()
        self._last_frame_timestamp: Optional[float] = None
        self._last_fps_overlay_update: Optional[float] = None

        controls_layout = QHBoxLayout()
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(18)
        controls_layout.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )

        self.save_button = PrimaryPushButton(self.tr("Save Screenshot"), self)
        self.save_button.setIcon(FIF.CAMERA)
        self.save_button.setIconSize(QSize(18, 18))
        self.save_button.clicked.connect(self._on_save_screenshot)
        self.save_button.setToolTip(
            self.tr("Capture the current preview and store it on disk")
        )
        controls_layout.addWidget(self.save_button)

        controls_layout.addStretch()
        self.main_layout.addLayout(controls_layout)
        self.main_layout.setStretch(0, 1)
        self.main_layout.setStretch(1, 0)

    def _load_placeholder_image(self) -> None:
        pixmap = QPixmap("app/assets/icons/logo.png")
        if pixmap.isNull():
            logger.warning("无法加载监控子页面的占位图标，路径可能不存在。")
            return
        self._preview_pixmap = pixmap
        self._refresh_preview_image()
        self._update_fps_overlay(None)

    def _refresh_preview_image(self) -> None:
        if not self._preview_pixmap:
            return
        target_size = self.preview_label.size()
        if target_size.width() <= 0 or target_size.height() <= 0:
            return
        scaled = self._preview_pixmap.scaled(
            target_size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.preview_label.setPixmap(scaled)
        self._preview_scaled_size = scaled.size()
        self._reposition_fps_overlay()

    def set_preview_pixmap(self, pixmap: Optional[QPixmap]) -> None:
        """动态更新监控画面截图。"""
        self._preview_pixmap = pixmap
        self._current_pil_image = None
        self._refresh_preview_image()

    def _apply_preview_from_pil(self, pil_image: Image.Image) -> None:
        rgb_image = pil_image.convert("RGB")
        width, height = rgb_image.size
        bytes_per_line = width * 3
        buffer = rgb_image.tobytes("raw", "RGB")
        qimage = QImage(
            buffer, width, height, bytes_per_line, QImage.Format.Format_RGB888
        )
        self._preview_pixmap = QPixmap.fromImage(qimage)
        self._current_pil_image = rgb_image.copy()
        self._refresh_preview_image()
        current_timestamp = time()
        fps_value: Optional[float] = None
        if self._last_frame_timestamp is not None:
            interval = current_timestamp - self._last_frame_timestamp
            if interval > 0:
                fps_value = 1.0 / interval
        self._last_frame_timestamp = current_timestamp
        self._update_fps_overlay(fps_value)

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
        self._reposition_fps_overlay()

    def _reposition_fps_overlay(self) -> None:
        if not self._fps_overlay:
            return
        preview_size = self.preview_label.size()
        overlay_size = self._fps_overlay.size()
        margin = 12
        x = preview_size.width() - overlay_size.width() - margin
        y = preview_size.height() - overlay_size.height() - margin
        self._fps_overlay.move(max(x, 0), max(y, 0))

    def _capture_frame(self) -> Image.Image:
        controller = self.monitor_task.maafw.controller
        if controller is None:
            raise RuntimeError("控制器尚未初始化，无法抓取画面")
        raw_frame = controller.post_screencap().wait().get()
        if raw_frame is None:
            raise ValueError("采集返回空帧")
        return Image.fromarray(raw_frame[..., ::-1])

    def _get_target_interval(self) -> float:
        return self._target_interval

    def _start_monitor_loop(self) -> None:
        if self._monitor_loop_task and not self._monitor_loop_task.done():
            return
        suppress_asyncify_logging()
        suppress_qasync_logging()
        self._monitoring_active = True
        self._monitor_loop_task = asyncio.create_task(self._monitor_loop())

    def _stop_monitor_loop(self) -> None:
        self._monitoring_active = False
        task = self._monitor_loop_task
        self._monitor_loop_task = None
        if task and not task.done():
            task.cancel()
        restore_asyncify_logging()
        restore_qasync_logging()

    async def _monitor_loop(self) -> None:
        loop = asyncio.get_running_loop()
        try:
            while self._monitoring_active and not self._locked:
                start = loop.time()
                if not self._is_controller_connected():
                    await self._handle_controller_disconnection()
                    return
                try:
                    pil_image = await asyncio.to_thread(self._capture_frame)
                except Exception:
                    pil_image = None
                if pil_image:
                    self._apply_preview_from_pil(pil_image)
                elapsed = loop.time() - start
                wait = max(0, self._get_target_interval() - elapsed)
                await asyncio.sleep(wait)
        except asyncio.CancelledError:
            pass
        finally:
            self._monitor_loop_task = None
            restore_asyncify_logging()
            restore_qasync_logging()

    def _is_controller_connected(self) -> bool:
        controller = getattr(self.monitor_task.maafw, "controller", None)
        if controller is None:
            return False
        connected = getattr(controller, "connected", None)
        return connected is not False

    async def _handle_controller_disconnection(self) -> None:
        if not self._monitoring_active or self._locked:
            return
        logger.warning("监控子页面：检测到控制器断开，停止监控并自动锁定。")
        self._monitoring_active = False
        current_task = asyncio.current_task()
        if current_task is not self._monitor_loop_task:
            self._stop_monitor_loop()
        try:
            await self.monitor_task.maafw.stop_task()
        except Exception as exc:
            logger.exception("监控子页面：停止任务失败：%s", exc)
        self.lock_monitor_page(stop_loop=False)

    def _schedule_controller_disconnection(self) -> None:
        if not self._monitoring_active or self._locked:
            return
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        if loop and loop.is_running():
            loop.create_task(self._handle_controller_disconnection())

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._refresh_preview_image()
        if self._lock_overlay:
            self._lock_overlay.setGeometry(self.rect())

    def _on_save_screenshot(self) -> None:
        logger.info("监控子页面：用户请求保存截图。")
        if not self._current_pil_image:
            logger.warning("监控子页面：当前不存在可保存的截图。")
            return
        save_dir = Path("debug") / "save_screen"
        save_dir.mkdir(parents=True, exist_ok=True)
        filename = datetime.now().strftime("screenshot_%Y%m%d_%H%M%S.png")
        save_path = save_dir / filename
        try:
            self._current_pil_image.save(save_path)
            logger.info("监控子页面：截图已保存至 %s", save_path)
            message = self.tr("Screenshot saved to ")+str(save_path)
            signalBus.info_bar_requested.emit("success", message)
        except Exception as exc:
            logger.exception("监控子页面：保存截图失败：%s", exc)

    def _on_preview_clicked(self, x: int, y: int) -> None:
        logger.info("监控子页面：预览图被点击，开始同步到设备。")
        if not self.service_coordinator:
            return
        if not self._is_controller_connected():
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
            logger.warning("监控子页面：点击未落在画面范围内，忽略此次事件。")
            return
        controller = getattr(self.monitor_task.maafw, "controller", None)
        if controller is None:
            logger.warning("监控子页面：控制器未初始化，无法同步点击。")
            return

        try:
            controller.post_click(*coords).wait()
            logger.debug("监控子页面：已同步点击到设备，坐标 %s。", coords)
        except Exception as exc:
            logger.exception("监控子页面：同步点击失败：%s", exc)

    def _map_visual_click_to_device(self, x: int, y: int) -> tuple[int, int] | None:
        """将 UI 中的点击位置映射为标准 1280×720 的设备坐标。"""
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

    def _show_unlock_loading(self) -> None:
        if self._unlock_progress:
            self._unlock_progress.setVisible(True)
            self._unlock_progress.start()

    def _hide_unlock_loading(self) -> None:
        if self._unlock_progress:
            self._unlock_progress.setVisible(False)
            self._unlock_progress.stop()

    def _create_lock_overlay(self) -> None:
        overlay = QWidget(self)
        overlay.setObjectName("monitorLockOverlay")
        overlay.setStyleSheet(
            """
            QWidget#monitorLockOverlay {
                background-color: rgba(0, 0, 0, 0.65);
                border-radius: 12px;
            }
            """
        )
        layout = QVBoxLayout(overlay)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        label = BodyLabel(self.tr("Monitor page locked"), overlay)
        label.setStyleSheet("color: rgba(255, 255, 255, 0.85);")
        layout.addWidget(label)
        self._unlock_button = PrimaryPushButton(self.tr("Unlock"), overlay)
        self._unlock_button.setToolTip(self.tr("Unlock this page"))
        self._unlock_button.clicked.connect(self._on_unlock_clicked)
        self._unlock_button.setSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed
        )
        self._unlock_button.setFixedWidth(160)
        layout.addWidget(self._unlock_button, alignment=Qt.AlignmentFlag.AlignHCenter)
        progress = IndeterminateProgressBar(overlay, start=False)
        progress.setFixedWidth(160)
        progress.setTextVisible(False)
        progress.setVisible(False)
        container = QWidget(overlay)
        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)
        container_layout.addStretch()
        container_layout.addWidget(progress)
        container_layout.addStretch()
        container.setFixedHeight(24)
        layout.addWidget(container, alignment=Qt.AlignmentFlag.AlignHCenter)
        self._unlock_progress = progress
        overlay.setGeometry(self.rect())
        overlay.raise_()
        overlay.setVisible(self._locked)
        self._lock_overlay = overlay

    def _on_unlock_clicked(self) -> None:
        async def _unlock_sequence():
            try:
                connected = await self.monitor_task._connect()
                if not connected:
                    logger.error("设备连接失败，无法解锁监控页面")
                    signalBus.info_bar_requested.emit(
                        "error", "设备连接失败，无法解锁监控页面"
                    )
                    return
                self._set_locked(False)
                self._start_monitor_loop()
                signalBus.info_bar_requested.emit("success", "监控页面解锁成功")
                try:
                    if not self._is_controller_connected():
                        await self._handle_controller_disconnection()
                        return
                    pil_image = await asyncio.to_thread(self._capture_frame)
                except Exception as exc:
                    logger.exception("监控子页面：解锁后刷新画面失败：%s", exc)
                else:
                    self._apply_preview_from_pil(pil_image)
            finally:
                self._hide_unlock_loading()

        self._show_unlock_loading()

        asyncio.create_task(_unlock_sequence())

    def _set_locked(self, locked: bool) -> None:
        self._locked = locked
        if self._lock_overlay:
            self._lock_overlay.setVisible(locked)

    def lock_monitor_page(self, stop_loop: bool = True) -> None:
        """重新锁定监控页面。"""
        if stop_loop:
            self._stop_monitor_loop()
        else:
            self._monitoring_active = False
        self._set_locked(True)
