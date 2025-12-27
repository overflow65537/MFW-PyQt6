from typing import Optional
from asyncify import asyncify
import asyncio
from datetime import datetime
from pathlib import Path
from time import time

from PIL import Image
from PySide6.QtCore import QSize, Qt, QTimer, Signal
from PySide6.QtGui import QImage, QPixmap, QIcon
from PySide6.QtWidgets import (
    QHBoxLayout,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from qfluentwidgets import (
    BodyLabel,
    FluentIcon as FIF,
    PixmapLabel,
    PrimaryPushButton,
    SimpleCardWidget,
    MessageBoxBase,
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


class MonitorWidget(QWidget):
    """简化的监控组件，用于嵌入到日志输出组件中"""

    def __init__(self, service_coordinator: ServiceCoordinator, parent=None, button=None):
        super().__init__(parent=parent)
        self.setObjectName("MonitorWidget")
        self.service_coordinator = service_coordinator
        self.external_button = button  # 外部按钮引用（如果提供）
        self._preview_pixmap: Optional[QPixmap] = None
        self._current_pil_image: Optional[Image.Image] = None
        self._preview_scaled_size: QSize = QSize(0, 0)
        self._monitoring_active = False
        self._monitor_loop_task: Optional[asyncio.Task] = None
        self._starting_monitoring = False  # 防止重复启动
        self._target_interval = 1.0 / 30
        self._last_frame_timestamp: Optional[float] = None
        self._last_fps_overlay_update: Optional[float] = None
        
        self.monitor_task = MonitorTask(
            task_service=self.service_coordinator.task_service,
            config_service=self.service_coordinator.config_service,
        )
        
        self._setup_ui()
        self._connect_signals()
        self._load_placeholder_image()

    def _setup_ui(self) -> None:
        """设置UI（标题和按钮由外部管理，这里只包含预览区域）"""
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # 预览区域（保留 SimpleCardWidget 作为内部包裹）
        # 16:9比例，宽度344px，高度 = 344 * 9 / 16 = 194px
        self._monitor_width = 344
        self._monitor_height = 194
        
        self.preview_card = SimpleCardWidget()
        self.preview_card.setClickEnabled(False)
        self.preview_card.setBorderRadius(8)
        # 设置固定尺寸（16:9比例）：宽度344px，高度194px
        self.preview_card.setFixedSize(self._monitor_width, self._monitor_height)
        # 设置大小策略为固定，不影响其他组件
        card_policy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.preview_card.setSizePolicy(card_policy)
        
        card_layout = QVBoxLayout(self.preview_card)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.setSpacing(0)
        
        self.preview_label = _ClickablePreviewLabel(self)
        self.preview_label.setObjectName("monitorPreviewLabel")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # 设置固定尺寸（16:9比例）：宽度344px，高度194px
        self.preview_label.setFixedSize(self._monitor_width, self._monitor_height)
        # 使用固定大小策略，不影响其他组件
        self.preview_label.setSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed
        )
        # 设置缩放模式：不自动缩放，使用精确尺寸
        self.preview_label.setScaledContents(False)  # 禁用自动缩放，我们手动控制
        self.preview_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.preview_label.setStyleSheet(
            """
            QLabel#monitorPreviewLabel {
                border-radius: 8px;
                border: 1px solid rgba(255, 255, 255, 0.12);
                background-color: rgba(255, 255, 255, 0.02);
            }
            """
        )
        self.preview_label.clicked.connect(self._on_preview_clicked)
        self.preview_label.setToolTip(self.tr("Click to sync this frame to the device"))
        
        card_layout.addWidget(self.preview_label)
        # 不使用拉伸因子，使用固定尺寸
        self.main_layout.addWidget(self.preview_card, 0)
        
        # 设置整个组件为固定大小
        self.setFixedSize(self._monitor_width, self._monitor_height)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        
        # FPS 覆盖层
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

    def _connect_signals(self):
        """连接信号"""
        # 监听任务开始/停止信号
        if hasattr(self.service_coordinator, 'fs_signals'):
            self.service_coordinator.fs_signals.fs_start_button_status.connect(
                self._on_task_status_changed
            )

    def _on_task_status_changed(self, status: dict):
        """处理任务状态变化"""
        from app.common.config import cfg
        is_running = status.get("text") == "STOP"
        if is_running and not self._monitoring_active and not self._starting_monitoring:
            # 任务开始，根据配置决定是否自动开始监控
            if cfg.get(cfg.auto_start_monitoring):
                self._start_monitoring()
        elif not is_running and self._monitoring_active:
            # 任务停止，自动停止监控
            self._stop_monitoring()

    def _load_placeholder_image(self) -> None:
        """加载占位图像（创建一个简单的灰色占位图，固定大小 1280x720）"""
        # 监控图片固定大小：1280x720（16:9比例）
        self._monitor_image_width = 1280
        self._monitor_image_height = 720
        
        # 使用PIL创建一个灰色占位图
        placeholder_image = Image.new(
            'RGB', 
            (self._monitor_image_width, self._monitor_image_height), 
            color=(40, 40, 40)
        )
        
        # 转换为QPixmap
        rgb_image = placeholder_image.convert("RGB")
        bytes_per_line = self._monitor_image_width * 3
        buffer = rgb_image.tobytes("raw", "RGB")
        qimage = QImage(
            buffer, 
            self._monitor_image_width, 
            self._monitor_image_height, 
            bytes_per_line, 
            QImage.Format.Format_RGB888
        )
        pixmap = QPixmap.fromImage(qimage)
        
        if pixmap.isNull():
            return
        
        self._preview_pixmap = pixmap
        # 占位图也需要缩放到预览标签大小
        self._refresh_preview_image()
        self._update_fps_overlay(None)

    def _refresh_preview_image(self) -> None:
        """刷新预览图像（将1280x720的图片缩放到344x194的预览标签）"""
        if not self._preview_pixmap:
            return
        
        # 使用固定的目标尺寸（344x194），而不是从标签获取（可能标签还没正确初始化）
        target_width = getattr(self, '_monitor_width', 344)
        target_height = getattr(self, '_monitor_height', 194)
        target_size = QSize(target_width, target_height)
        
        # 直接将图片缩放到预览标签的精确大小（344x194）
        # 使用 SmoothTransformation 保证缩放质量
        scaled = self._preview_pixmap.scaled(
            target_size,
            Qt.AspectRatioMode.IgnoreAspectRatio,  # 忽略宽高比，精确填充
            Qt.TransformationMode.SmoothTransformation,
        )
        
        self.preview_label.setPixmap(scaled)
        self._preview_scaled_size = scaled.size()
        self._reposition_fps_overlay()

    def _apply_preview_from_pil(self, pil_image: Image.Image) -> None:
        """从 PIL 图像应用预览（确保图片固定为 1280x720）"""
        # 确保监控图片固定大小：1280x720
        if not hasattr(self, '_monitor_image_width'):
            self._monitor_image_width = 1280
            self._monitor_image_height = 720
        
        # 将图片调整为固定大小（如果尺寸不匹配则进行缩放）
        if pil_image.size != (self._monitor_image_width, self._monitor_image_height):
            pil_image = pil_image.resize(
                (self._monitor_image_width, self._monitor_image_height),
                Image.Resampling.LANCZOS
            )
        
        rgb_image = pil_image.convert("RGB")
        bytes_per_line = self._monitor_image_width * 3
        buffer = rgb_image.tobytes("raw", "RGB")
        qimage = QImage(
            buffer, 
            self._monitor_image_width, 
            self._monitor_image_height, 
            bytes_per_line, 
            QImage.Format.Format_RGB888
        )
        self._preview_pixmap = QPixmap.fromImage(qimage)
        self._current_pil_image = rgb_image.copy()
        # 第一张真实监控图片到达后，进行正确的缩放（固定尺寸，无需更新高度）
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
        """更新 FPS 覆盖层"""
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
        """重新定位 FPS 覆盖层"""
        if not self._fps_overlay:
            return
        preview_size = self.preview_label.size()
        overlay_size = self._fps_overlay.size()
        margin = 12
        x = preview_size.width() - overlay_size.width() - margin
        y = preview_size.height() - overlay_size.height() - margin
        self._fps_overlay.move(max(x, 0), max(y, 0))

    def _capture_frame(self) -> Image.Image:
        """捕获一帧"""
        controller = self.monitor_task.maafw.controller
        if controller is None:
            raise RuntimeError("控制器尚未初始化，无法抓取画面")
        raw_frame = controller.post_screencap().wait().get()
        if raw_frame is None:
            raise ValueError("采集返回空帧")
        return Image.fromarray(raw_frame[..., ::-1])

    def _start_monitor_loop(self) -> None:
        """启动监控循环"""
        if self._monitor_loop_task and not self._monitor_loop_task.done():
            return
        if self._monitoring_active:
            return
        suppress_asyncify_logging()
        suppress_qasync_logging()
        self._monitoring_active = True
        try:
            self._monitor_loop_task = asyncio.create_task(self._monitor_loop())
        except Exception:
            # 如果创建任务失败，重置状态
            self._monitoring_active = False
            restore_asyncify_logging()
            restore_qasync_logging()
            raise

    def _stop_monitor_loop(self) -> None:
        """停止监控循环"""
        self._monitoring_active = False
        task = self._monitor_loop_task
        self._monitor_loop_task = None
        if task and not task.done():
            task.cancel()
        restore_asyncify_logging()
        restore_qasync_logging()

    async def _monitor_loop(self) -> None:
        """监控循环"""
        loop = asyncio.get_running_loop()
        try:
            while self._monitoring_active:
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

    def _get_target_interval(self) -> float:
        """获取目标间隔"""
        return self._target_interval

    def _is_controller_connected(self) -> bool:
        """检查控制器是否连接"""
        controller = getattr(self.monitor_task.maafw, "controller", None)
        if controller is None:
            return False
        connected = getattr(controller, "connected", None)
        return connected is not False

    async def _handle_controller_disconnection(self) -> None:
        """处理控制器断开"""
        if not self._monitoring_active:
            return
        self._monitoring_active = False
        current_task = asyncio.current_task()
        if current_task is not self._monitor_loop_task:
            self._stop_monitor_loop()
        try:
            await self.monitor_task.maafw.stop_task()
        except Exception:
            # 静默处理错误，不输出到日志组件
            pass
        try:
            if self.monitor_task.maafw.controller:
                self.monitor_task.maafw.controller = None
        except Exception:
            # 静默处理错误，不输出到日志组件
            pass
        self._update_button_state()

    def _update_button_state(self):
        """更新按钮状态（更新外部按钮，如果存在）"""
        if self.external_button:
            if self._monitoring_active:
                self.external_button.setIcon(FIF.CLOSE)
                self.external_button.setToolTip(self.tr("Stop monitoring task"))
            else:
                self.external_button.setIcon(FIF.PLAY)
                self.external_button.setToolTip(self.tr("Start monitoring task"))

    def resizeEvent(self, event) -> None:
        """处理尺寸变化（固定尺寸，只刷新图像）"""
        super().resizeEvent(event)
        self._refresh_preview_image()

    def _on_save_screenshot(self) -> None:
        """保存截图"""
        if not self._current_pil_image:
            signalBus.info_bar_requested.emit("warning", self.tr("No screenshot available to save"))
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
            signalBus.info_bar_requested.emit("error", self.tr("Failed to save screenshot: ") + str(exc))

    def _on_preview_clicked(self, x: int, y: int) -> None:
        """处理预览点击"""
        if not self.service_coordinator:
            return
        if not self._is_controller_connected():
            self._schedule_controller_disconnection()
            return
        handler = getattr(self.service_coordinator, "sync_monitor_preview_click", None)
        if callable(handler):
            try:
                handler()
            except Exception:
                # 静默处理错误，不输出到日志组件
                pass

        coords = self._map_visual_click_to_device(x, y)
        if not coords:
            return
        controller = getattr(self.monitor_task.maafw, "controller", None)
        if controller is None:
            return

        try:
            controller.post_click(*coords).wait()
        except Exception:
            # 静默处理错误，不输出到日志组件
            pass

    def _map_visual_click_to_device(self, x: int, y: int) -> tuple[int, int] | None:
        """将 UI 中的点击位置映射为标准 1280×720 的设备坐标"""
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

        # 使用固定的监控图片尺寸：1280x720
        target_width = getattr(self, '_monitor_image_width', 1280)
        target_height = getattr(self, '_monitor_image_height', 720)
        device_x = int(round(normalized_x * target_width))
        device_y = int(round(normalized_y * target_height))
        device_x = max(0, min(device_x, target_width - 1))
        device_y = max(0, min(device_y, target_height - 1))

        return device_x, device_y

    def _on_monitor_control_clicked(self) -> None:
        """处理开始/停止监控按钮点击"""
        if self._monitoring_active:
            self._stop_monitoring()
        else:
            self._start_monitoring()

    def _start_monitoring(self) -> None:
        """开始监控"""
        # 防止重复启动
        if self._monitoring_active or self._starting_monitoring:
            return
        
        self._starting_monitoring = True
        if self.external_button:
            self.external_button.setEnabled(False)
        
        # 先显示占位图
        self._load_placeholder_image()
        
        async def _start_sequence():
            try:
                if not self._is_controller_connected():
                    connected = await self.monitor_task._connect()
                    if not connected:
                        signalBus.info_bar_requested.emit(
                            "error", self.tr("Device connection failed, cannot start monitoring")
                        )
                        self._starting_monitoring = False
                        if self.external_button:
                            self.external_button.setEnabled(True)
                        return
                
                # 启动监控循环
                self._start_monitor_loop()
                
                # 等待一小段时间确保循环已启动
                await asyncio.sleep(0.1)
                
                # 检查监控是否真的启动了
                if not self._monitoring_active:
                    signalBus.info_bar_requested.emit(
                        "error", self.tr("Failed to start monitoring loop")
                    )
                    self._starting_monitoring = False
                    if self.external_button:
                        self.external_button.setEnabled(True)
                    return
                
                self._update_button_state()
                signalBus.info_bar_requested.emit("success", self.tr("Monitoring started"))
                
                # 尝试捕获第一帧
                try:
                    if not self._is_controller_connected():
                        await self._handle_controller_disconnection()
                        return
                    pil_image = await asyncio.to_thread(self._capture_frame)
                except Exception:
                    # 静默处理错误，不输出到日志组件
                    pass
                else:
                    if pil_image:
                        self._apply_preview_from_pil(pil_image)
            except Exception as exc:
                signalBus.info_bar_requested.emit(
                    "error", self.tr("Failed to start monitoring: ") + str(exc)
                )
                self._starting_monitoring = False
                if self._monitoring_active:
                    self._stop_monitor_loop()
            finally:
                self._starting_monitoring = False
                if self.external_button:
                    self.external_button.setEnabled(True)

        QTimer.singleShot(0, lambda: asyncio.create_task(_start_sequence()))

    def _stop_monitoring(self) -> None:
        """停止监控"""
        if self.external_button:
            self.external_button.setEnabled(False)
        
        async def _stop_sequence():
            try:
                self._stop_monitor_loop()
                
                try:
                    await self.monitor_task.maafw.stop_task()
                except Exception:
                    # 静默处理错误，不输出到日志组件
                    pass
                
                try:
                    if self.monitor_task.maafw.controller:
                        self.monitor_task.maafw.controller = None
                except Exception:
                    # 静默处理错误，不输出到日志组件
                    pass
                
                # 停止监控后显示占位图
                self._load_placeholder_image()
                
                self._update_button_state()
                signalBus.info_bar_requested.emit("success", self.tr("Monitoring stopped"))
            except Exception as exc:
                signalBus.info_bar_requested.emit(
                    "error", self.tr("Failed to stop monitoring: ") + str(exc)
                )
            finally:
                if self.external_button:
                    self.external_button.setEnabled(True)
        
        QTimer.singleShot(0, lambda: asyncio.create_task(_stop_sequence()))

    def _on_open_monitor_dialog(self) -> None:
        """打开监控对话框"""
        from app.view.monitor_interface.monitor_interface import MonitorInterface
        from qfluentwidgets import MessageBoxBase
        from PySide6.QtWidgets import QApplication
        
        # 保存当前监控状态
        was_monitoring = self._monitoring_active
        
        class MonitorDialog(MessageBoxBase):
            """监控对话框"""
            def __init__(self, service_coordinator: ServiceCoordinator, was_monitoring: bool, parent=None):
                super().__init__(parent)
                self.setWindowTitle(self.tr("Monitor"))
                self.setMinimumSize(800, 600)
                
                # 获取屏幕大小，设置合理的初始窗口大小
                screen = QApplication.primaryScreen()
                if screen:
                    screen_size = screen.availableGeometry()
                    # 初始大小为屏幕的 70%
                    self.resize(
                        int(screen_size.width() * 0.7),
                        int(screen_size.height() * 0.7)
                    )
                
                # 创建监控界面
                self.monitor_interface = MonitorInterface(service_coordinator, self)
                
                # 设置布局
                layout = QVBoxLayout(self.widget)
                layout.setContentsMargins(0, 0, 0, 0)
                layout.addWidget(self.monitor_interface)
                
                # 如果之前正在监控，同步状态到对话框中的监控界面
                if was_monitoring:
                    # 延迟启动监控，确保对话框已显示
                    QTimer.singleShot(100, lambda: self.monitor_interface._start_monitoring())
        
        dialog = MonitorDialog(self.service_coordinator, was_monitoring, self)
        dialog.exec()


    def _schedule_controller_disconnection(self) -> None:
        """安排控制器断开处理"""
        if not self._monitoring_active:
            return
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        if loop and loop.is_running():
            loop.create_task(self._handle_controller_disconnection())

