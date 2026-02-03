"""
多开管理界面

功能：
1. 列出所有配置和它们的监控画面
2. 每个监控画面下有一个按钮控制对应配置的启动和停止
3. 支持同时运行多个配置
"""

import asyncio
from typing import Optional, Dict

from PySide6.QtCore import Qt, QTimer, QSize
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QScrollArea,
    QSizePolicy,
    QFrame,
)

from qfluentwidgets import (
    BodyLabel,
    SimpleCardWidget,
    TransparentPushButton,
    PixmapLabel,
    FluentIcon as FIF,
    ScrollArea,
    IndeterminateProgressRing,
)

from PIL import Image
import numpy as np

from app.core.core import ServiceCoordinator
from app.utils.logger import logger
from app.common.signal_bus import signalBus


class ConfigMonitorCard(QWidget):
    """单个配置的监控卡片
    
    包含：
    - 配置名称标题
    - 监控画面预览
    - 启动/停止按钮
    """
    
    def __init__(
        self, 
        service_coordinator: ServiceCoordinator,
        config_id: str,
        config_name: str,
        parent=None
    ):
        super().__init__(parent)
        self.service_coordinator = service_coordinator
        self.config_id = config_id
        self.config_name = config_name
        
        # 监控状态
        self._monitoring_active = False
        self._monitor_timer: Optional[QTimer] = None
        self._is_running = False
        
        # 防抖状态：防止重复点击
        self._button_locked = False
        self._pending_operation: Optional[str] = None  # "start" 或 "stop"
        
        # 预览图像
        self._preview_pixmap: Optional[QPixmap] = None
        
        # 监控尺寸（16:9 比例）
        self._monitor_width = 280
        self._monitor_height = 158
        
        self._setup_ui()
        self._connect_signals()
        
        # 初始化按钮状态
        self._update_button_state()
    
    def _setup_ui(self):
        """设置UI"""
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(8)
        
        # 卡片容器
        self.card = SimpleCardWidget()
        self.card.setClickEnabled(False)
        self.card.setBorderRadius(8)
        
        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(12, 12, 12, 12)
        card_layout.setSpacing(8)
        
        # 配置名称标题
        self.title_label = BodyLabel(self.config_name)
        self.title_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(self.title_label)
        
        # 监控画面容器
        self.preview_container = QWidget()
        self.preview_container.setFixedSize(self._monitor_width, self._monitor_height)
        self.preview_container.setStyleSheet(
            """
            QWidget {
                background-color: rgba(0, 0, 0, 0.3);
                border-radius: 6px;
            }
            """
        )
        
        preview_layout = QVBoxLayout(self.preview_container)
        preview_layout.setContentsMargins(0, 0, 0, 0)
        preview_layout.setSpacing(0)
        
        # 预览标签
        self.preview_label = PixmapLabel()
        self.preview_label.setObjectName("configMonitorPreview")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setFixedSize(self._monitor_width, self._monitor_height)
        self.preview_label.setStyleSheet(
            """
            QLabel#configMonitorPreview {
                border-radius: 6px;
                background-color: transparent;
            }
            """
        )
        preview_layout.addWidget(self.preview_label)
        
        # 加载指示器覆盖层
        self._loading_overlay = QWidget(self.preview_label)
        self._loading_overlay.setStyleSheet(
            "background-color: rgba(0, 0, 0, 60); border-radius: 6px;"
        )
        loading_layout = QHBoxLayout(self._loading_overlay)
        loading_layout.setContentsMargins(0, 0, 0, 0)
        loading_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self._loading_indicator = IndeterminateProgressRing(self._loading_overlay)
        self._loading_indicator.setFixedSize(24, 24)
        loading_layout.addWidget(self._loading_indicator)
        self._loading_overlay.hide()
        
        # 状态标签（未运行时显示）
        self._status_label = BodyLabel(self.tr("Not Running"))
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._status_label.setStyleSheet("color: rgba(255, 255, 255, 0.6);")
        
        card_layout.addWidget(self.preview_container, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # 启动/停止按钮
        self.control_button = TransparentPushButton(self.tr("Start"), self, FIF.PLAY)
        self.control_button.clicked.connect(self._on_control_button_clicked)
        card_layout.addWidget(self.control_button)
        
        self.main_layout.addWidget(self.card)
        
        # 设置卡片固定宽度
        self.card.setFixedWidth(self._monitor_width + 24)
    
    def _connect_signals(self):
        """连接信号"""
        # 监听任务流状态变化
        if hasattr(self.service_coordinator, 'fs_signals'):
            self.service_coordinator.fs_signals.fs_start_button_status.connect(
                self._on_task_status_changed
            )
        
        # 监听任务流结束信号
        signalBus.task_flow_finished.connect(self._on_task_flow_finished)
    
    def _on_task_status_changed(self, status: dict):
        """任务状态变化"""
        status_config_id = status.get("config_id", "")
        if status_config_id != self.config_id:
            return
        
        is_running = status.get("text") == "STOP"
        self._is_running = is_running
        
        # 更新按钮文字和图标
        if self._is_running:
            self.control_button.setText(self.tr("Stop"))
            self.control_button.setIcon(FIF.CLOSE)
        else:
            self.control_button.setText(self.tr("Start"))
            self.control_button.setIcon(FIF.PLAY)
        
        # 只有在启动操作时，收到运行状态信号才解锁按钮
        if self._pending_operation == "start" and is_running:
            self._button_locked = False
            self._pending_operation = None
            self.control_button.setEnabled(True)
        
        # 停止操作时，保持按钮锁定状态，等待 task_flow_finished 信号
        
        if is_running and not self._monitoring_active:
            self._start_monitoring()
        elif not is_running and self._monitoring_active:
            self._stop_monitoring()
    
    def _on_task_flow_finished(self, payload: dict):
        """任务流结束"""
        finished_config_id = payload.get("config_id", "")
        if finished_config_id != self.config_id:
            return
        
        self._is_running = False
        # 解锁按钮并清理操作状态
        self._button_locked = False
        self._pending_operation = None
        
        # 更新按钮状态
        self.control_button.setText(self.tr("Start"))
        self.control_button.setIcon(FIF.PLAY)
        self.control_button.setEnabled(True)
        
        self._stop_monitoring()
    
    def _update_button_state(self):
        """更新按钮状态"""
        # 检查实际运行状态
        self._is_running = self.service_coordinator.is_running(self.config_id)
        
        if self._is_running:
            self.control_button.setText(self.tr("Stop"))
            self.control_button.setIcon(FIF.CLOSE)
        else:
            self.control_button.setText(self.tr("Start"))
            self.control_button.setIcon(FIF.PLAY)
        
        # 只有在未锁定时才启用按钮
        self.control_button.setEnabled(not self._button_locked)
    
    def _on_control_button_clicked(self):
        """控制按钮点击"""
        # 防抖检查：如果按钮已锁定，忽略点击
        if self._button_locked:
            return
        
        # 锁定按钮，等待任务流信号解锁
        self._button_locked = True
        self.control_button.setEnabled(False)
        # 强制更新UI
        self.control_button.repaint()
        
        if self._is_running:
            # 停止任务
            self._pending_operation = "stop"
            asyncio.create_task(
                self.service_coordinator.stop_task_flow(config_id=self.config_id)
            )
        else:
            # 启动任务
            self._pending_operation = "start"
            self._show_loading()
            asyncio.create_task(
                self.service_coordinator.run_tasks_flow(config_id=self.config_id)
            )
    
    def _show_loading(self):
        """显示加载指示器"""
        self._loading_overlay.setGeometry(0, 0, self._monitor_width, self._monitor_height)
        self._loading_overlay.show()
        self._loading_indicator.start()
    
    def _hide_loading(self):
        """隐藏加载指示器"""
        self._loading_overlay.hide()
        self._loading_indicator.stop()
    
    def _start_monitoring(self):
        """开始监控"""
        if self._monitoring_active:
            return
        
        self._monitoring_active = True
        self._hide_loading()
        
        # 使用 QTimer 进行监控刷新（约 10fps）
        self._monitor_timer = QTimer(self)
        self._monitor_timer.timeout.connect(self._refresh_preview)
        self._monitor_timer.start(100)  # 100ms = 10fps
        
        logger.debug(f"[ConfigMonitorCard] 配置 {self.config_id} 开始监控")
    
    def _stop_monitoring(self):
        """停止监控"""
        if not self._monitoring_active:
            return
        
        self._monitoring_active = False
        
        if self._monitor_timer:
            self._monitor_timer.stop()
            self._monitor_timer = None
        
        # 清空预览
        self._clear_preview()
        self._hide_loading()
        
        logger.debug(f"[ConfigMonitorCard] 配置 {self.config_id} 停止监控")
    
    def _refresh_preview(self):
        """刷新预览画面"""
        if not self._monitoring_active:
            return
        
        try:
            # 获取运行器
            runner = self.service_coordinator.get_runner(self.config_id)
            if not runner or not hasattr(runner, 'maafw'):
                return
            
            controller = getattr(runner.maafw, 'controller', None)
            if controller is None:
                return
            
            # 尝试从 cached_image 获取图像
            cached_image = getattr(controller, 'cached_image', None)
            if cached_image is not None:
                self._apply_preview_from_array(cached_image)
            else:
                # 如果没有缓存图像，尝试截图
                try:
                    raw_frame = controller.post_screencap().wait().get()
                    if raw_frame is not None:
                        self._apply_preview_from_array(raw_frame)
                except Exception:
                    # 截图失败是常见情况（设备未连接等），静默忽略
                    pass
        except Exception as e:
            # 只在非常见错误时记录日志
            if "cached image" not in str(e).lower():
                logger.debug(f"[ConfigMonitorCard] 配置 {self.config_id} 刷新预览失败: {e}")
    
    def _apply_preview_from_array(self, image_array):
        """从 numpy 数组应用预览"""
        try:
            if isinstance(image_array, np.ndarray):
                # BGR 转 RGB
                if len(image_array.shape) == 3 and image_array.shape[2] == 3:
                    rgb_array = image_array[..., ::-1]
                else:
                    rgb_array = image_array
                
                pil_image = Image.fromarray(rgb_array)
            elif isinstance(image_array, Image.Image):
                pil_image = image_array
            else:
                return
            
            # 转换为 QPixmap
            image_width, image_height = pil_image.size
            rgb_image = pil_image.convert("RGB")
            bytes_per_line = image_width * 3
            buffer = rgb_image.tobytes("raw", "RGB")
            
            qimage = QImage(
                buffer,
                image_width,
                image_height,
                bytes_per_line,
                QImage.Format.Format_RGB888
            )
            pixmap = QPixmap.fromImage(qimage)
            
            # 缩放到预览尺寸
            scaled = pixmap.scaled(
                QSize(self._monitor_width, self._monitor_height),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            
            self.preview_label.setPixmap(scaled)
        except Exception as e:
            logger.debug(f"[ConfigMonitorCard] 应用预览失败: {e}")
    
    def _clear_preview(self):
        """清空预览"""
        self._preview_pixmap = None
        self.preview_label.clear()
        self.preview_label.setPixmap(QPixmap())
    
    def cleanup(self):
        """清理资源"""
        self._stop_monitoring()


class MultiRunInterface(QWidget):
    """多开管理界面
    
    显示所有配置及其监控画面，每个配置可独立启动/停止
    """
    
    def __init__(self, service_coordinator: ServiceCoordinator, parent=None):
        super().__init__(parent)
        self.setObjectName("MultiRunInterface")
        self.service_coordinator = service_coordinator
        
        # 配置卡片字典
        self._config_cards: Dict[str, ConfigMonitorCard] = {}
        
        self._setup_ui()
        self._load_configs()
        
        # 监听配置变化
        self._connect_signals()
    
    def _setup_ui(self):
        """设置UI"""
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(28, 18, 28, 18)
        self.main_layout.setSpacing(14)
        
        # 标题
        self.title_label = BodyLabel(self.tr("Multi-Run Management"))
        self.title_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        self.main_layout.addWidget(self.title_label)
        
        # 副标题
        self.subtitle_label = BodyLabel(
            self.tr("Manage and monitor multiple configurations simultaneously")
        )
        self.subtitle_label.setStyleSheet("color: rgba(255, 255, 255, 0.6); font-size: 12px;")
        self.main_layout.addWidget(self.subtitle_label)
        
        # 滚动区域
        self.scroll_area = ScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setStyleSheet("background: transparent; border: none;")
        self.scroll_area.viewport().setStyleSheet("background: transparent;")
        
        # 滚动内容容器
        self.scroll_content = QWidget()
        self.scroll_content.setStyleSheet("background: transparent;")
        
        # 网格布局
        self.grid_layout = QGridLayout(self.scroll_content)
        self.grid_layout.setContentsMargins(0, 10, 0, 10)
        self.grid_layout.setSpacing(16)
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        
        self.scroll_area.setWidget(self.scroll_content)
        self.main_layout.addWidget(self.scroll_area, 1)
    
    def _connect_signals(self):
        """连接信号"""
        # 监听配置添加/删除
        if hasattr(self.service_coordinator, 'fs_signal_bus'):
            self.service_coordinator.fs_signal_bus.fs_config_added.connect(
                self._on_config_added
            )
            self.service_coordinator.fs_signal_bus.fs_config_removed.connect(
                self._on_config_deleted
            )
    
    def _load_configs(self):
        """加载所有配置"""
        try:
            configs = self.service_coordinator.list_configs()
            for i, config_summary in enumerate(configs):
                config_id = config_summary.get("item_id", "")
                # 配置名称的键是 "name" 而不是 "config_name"
                config_name = config_summary.get("name", "") or config_id
                
                if config_id and config_id not in self._config_cards:
                    self._add_config_card(config_id, config_name, i)
        except Exception as e:
            logger.error(f"[MultiRunInterface] 加载配置失败: {e}")
    
    def _add_config_card(self, config_id: str, config_name: str, index: int = -1):
        """添加配置卡片"""
        if config_id in self._config_cards:
            return
        
        card = ConfigMonitorCard(
            self.service_coordinator,
            config_id,
            config_name,
            self
        )
        self._config_cards[config_id] = card
        
        # 计算网格位置（每行3个）
        if index < 0:
            index = len(self._config_cards) - 1
        
        row = index // 3
        col = index % 3
        
        self.grid_layout.addWidget(card, row, col, Qt.AlignmentFlag.AlignTop)
        
        logger.debug(f"[MultiRunInterface] 添加配置卡片: {config_id} ({config_name})")
    
    def _remove_config_card(self, config_id: str):
        """移除配置卡片"""
        if config_id not in self._config_cards:
            return
        
        card = self._config_cards.pop(config_id)
        card.cleanup()
        self.grid_layout.removeWidget(card)
        card.deleteLater()
        
        # 重新排列剩余卡片
        self._rearrange_cards()
        
        logger.debug(f"[MultiRunInterface] 移除配置卡片: {config_id}")
    
    def _rearrange_cards(self):
        """重新排列卡片"""
        # 移除所有卡片
        for card in self._config_cards.values():
            self.grid_layout.removeWidget(card)
        
        # 重新添加
        for i, (config_id, card) in enumerate(self._config_cards.items()):
            row = i // 3
            col = i % 3
            self.grid_layout.addWidget(card, row, col, Qt.AlignmentFlag.AlignTop)
    
    def _on_config_added(self, config_id: str):
        """配置添加事件"""
        try:
            config = self.service_coordinator.get_config(config_id)
            if config:
                # ConfigItem 的名称字段是 "name"
                config_name = getattr(config, 'name', '') or config_id
                self._add_config_card(config_id, config_name)
        except Exception as e:
            logger.error(f"[MultiRunInterface] 处理配置添加失败: {e}")
    
    def _on_config_deleted(self, config_id: str):
        """配置删除事件"""
        self._remove_config_card(config_id)
    
    def showEvent(self, event):
        """显示事件"""
        super().showEvent(event)
        # 刷新配置列表
        self._refresh_configs()
    
    def _refresh_configs(self):
        """刷新配置列表"""
        try:
            configs = self.service_coordinator.list_configs()
            current_ids = set(self._config_cards.keys())
            new_ids = set()
            
            for config_summary in configs:
                config_id = config_summary.get("item_id", "")
                if config_id:
                    new_ids.add(config_id)
            
            # 添加新配置
            for i, config_summary in enumerate(configs):
                config_id = config_summary.get("item_id", "")
                # 配置名称的键是 "name" 而不是 "config_name"
                config_name = config_summary.get("name", "") or config_id
                
                if config_id and config_id not in current_ids:
                    self._add_config_card(config_id, config_name, i)
            
            # 移除已删除的配置
            for config_id in current_ids - new_ids:
                self._remove_config_card(config_id)
            
            # 更新所有卡片的按钮状态
            for card in self._config_cards.values():
                card._update_button_state()
        except Exception as e:
            logger.error(f"[MultiRunInterface] 刷新配置失败: {e}")
    
    def cleanup(self):
        """清理资源"""
        for card in self._config_cards.values():
            card.cleanup()
        self._config_cards.clear()
