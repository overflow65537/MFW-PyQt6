"""
多开管理界面

显示所有配置的监控画面和控制按钮，支持同时运行多个配置。
"""

import asyncio
from typing import Dict, Optional, Any

from PySide6.QtCore import Qt, QTimer, QSize
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QScrollArea,
    QFrame,
    QSizePolicy,
)
from PySide6.QtGui import QPixmap, QImage

from qfluentwidgets import (
    ScrollArea,
    SimpleCardWidget,
    BodyLabel,
    CaptionLabel,
    TransparentPushButton,
    FluentIcon as FIF,
    isDarkTheme,
    PillPushButton,
)

from app.core.core import get_service_coordinator, ServiceCoordinator, ConfigInstance
from app.utils.logger import logger


class ConfigMonitorCard(SimpleCardWidget):
    """单个配置的监控卡片
    
    包含：
    - 配置名称和状态指示
    - 监控画面预览
    - 开始/停止按钮
    """
    
    # 卡片尺寸配置
    CARD_WIDTH = 280
    MONITOR_WIDTH = 260
    MONITOR_HEIGHT = 146  # 16:9 比例
    
    def __init__(self, config_instance: ConfigInstance, parent=None):
        super().__init__(parent)
        self._config = config_instance
        self._coordinator = get_service_coordinator()
        self._preview_pixmap: Optional[QPixmap] = None
        self._refresh_timer: Optional[QTimer] = None
        
        self.setFixedWidth(self.CARD_WIDTH)
        self.setClickEnabled(False)
        self.setBorderRadius(12)
        
        self._setup_ui()
        self._connect_signals()
        self._start_preview_refresh()
    
    def _setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        
        # 标题栏：配置名称 + 状态指示
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)
        
        self.name_label = BodyLabel(self._get_config_name())
        self.name_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        header_layout.addWidget(self.name_label)
        
        header_layout.addStretch()
        
        self.status_label_badge = CaptionLabel()
        self._update_status_badge()
        header_layout.addWidget(self.status_label_badge)
        
        layout.addLayout(header_layout)
        
        # 监控画面预览区域
        self.preview_frame = QFrame()
        self.preview_frame.setFixedSize(self.MONITOR_WIDTH, self.MONITOR_HEIGHT)
        self.preview_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(0, 0, 0, 0.3);
                border-radius: 8px;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }
        """)
        
        preview_layout = QVBoxLayout(self.preview_frame)
        preview_layout.setContentsMargins(0, 0, 0, 0)
        preview_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.preview_label = BodyLabel()
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setStyleSheet("color: rgba(255, 255, 255, 0.5);")
        self.preview_label.setText(self.tr("No Preview"))
        preview_layout.addWidget(self.preview_label)
        
        layout.addWidget(self.preview_frame)
        
        # Bundle 信息
        bundle_name = self._get_bundle_name()
        self.bundle_label = CaptionLabel(bundle_name)
        self.bundle_label.setStyleSheet("color: rgba(128, 128, 128, 0.8);")
        layout.addWidget(self.bundle_label)
        
        # 控制按钮
        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)
        
        self.run_button = TransparentPushButton()
        self._update_button_state()
        self.run_button.clicked.connect(self._on_run_button_clicked)
        button_layout.addWidget(self.run_button)
        
        layout.addLayout(button_layout)
    
    def _connect_signals(self):
        """连接信号"""
        # 监听任务状态变化
        self._coordinator.fs_signal_bus.fs_start_button_status.connect(
            self._on_status_changed
        )
    
    def _get_config_name(self) -> str:
        """获取配置名称"""
        item = self._config.item
        return item.name if item else "Unknown"
    
    def _get_bundle_name(self) -> str:
        """获取 Bundle 名称"""
        item = self._config.item
        return item.bundle if item else ""
    
    def _update_status_badge(self):
        """更新状态指示"""
        if self._config.is_running:
            self.status_label_badge.setText("● " + self.tr("Running"))
            self.status_label_badge.setStyleSheet("color: #4CAF50; font-weight: bold;")
        else:
            self.status_label_badge.setText("○ " + self.tr("Stopped"))
            self.status_label_badge.setStyleSheet("color: #9E9E9E;")
    
    def _update_button_state(self):
        """更新按钮状态"""
        if self._config.is_running:
            self.run_button.setText(self.tr("Stop"))
            self.run_button.setIcon(FIF.CLOSE)
        else:
            self.run_button.setText(self.tr("Start"))
            self.run_button.setIcon(FIF.PLAY)
    
    def _on_run_button_clicked(self):
        """处理按钮点击"""
        self.run_button.setEnabled(False)
        
        if self._config.is_running:
            self._config.stop()
        else:
            self._config.start()
        
        # 延迟恢复按钮
        QTimer.singleShot(500, lambda: self.run_button.setEnabled(True))
    
    def _on_status_changed(self, status: dict):
        """处理状态变化"""
        config_id = status.get("config_id", "")
        if config_id == self._config.id:
            self._update_status_badge()
            self._update_button_state()
    
    def _start_preview_refresh(self):
        """开始预览刷新"""
        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(self._refresh_preview)
        self._refresh_timer.start(1000)  # 每秒刷新一次
    
    def _refresh_preview(self):
        """刷新预览画面"""
        if not self._config.is_running:
            self.preview_label.setText(self.tr("No Preview"))
            self.preview_label.setPixmap(QPixmap())
            return
        
        try:
            # 尝试获取运行器的控制器
            runner = self._coordinator._runners.get(self._config.id)
            if not runner:
                return
            
            maafw = getattr(runner, 'maafw', None)
            if not maafw:
                return
            
            controller = getattr(maafw, 'controller', None)
            if not controller:
                return
            
            # 获取缓存的图像
            cached_image = getattr(controller, 'cached_image', None)
            if cached_image is None:
                return
            
            # 转换为 QPixmap
            import numpy as np
            if isinstance(cached_image, np.ndarray):
                if cached_image.ndim == 3 and cached_image.shape[2] >= 3:
                    h, w = cached_image.shape[:2]
                    rgb = cached_image[:, :, :3]
                    if cached_image.shape[2] == 4:
                        rgb = cached_image[:, :, :3]
                    # BGR to RGB
                    rgb = rgb[..., ::-1].copy()
                    
                    qimg = QImage(
                        rgb.data, w, h, w * 3,
                        QImage.Format.Format_RGB888
                    )
                    pixmap = QPixmap.fromImage(qimg)
                    
                    # 缩放到预览尺寸
                    scaled = pixmap.scaled(
                        QSize(self.MONITOR_WIDTH, self.MONITOR_HEIGHT),
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    )
                    
                    self.preview_label.setPixmap(scaled)
                    self.preview_label.setText("")
        except Exception as e:
            logger.debug(f"刷新预览失败: {e}")
    
    def cleanup(self):
        """清理资源"""
        if self._refresh_timer:
            self._refresh_timer.stop()
            self._refresh_timer = None


class MultiRunInterface(QWidget):
    """多开管理界面
    
    以网格形式显示所有配置的监控卡片，支持同时运行多个配置。
    """
    
    def __init__(self, service_coordinator: ServiceCoordinator | None = None, parent=None):
        super().__init__(parent)
        self.setObjectName("MultiRunInterface")
        
        if service_coordinator is None:
            service_coordinator = get_service_coordinator()
        self._coordinator = service_coordinator
        
        self._config_cards: Dict[str, ConfigMonitorCard] = {}
        
        self._setup_ui()
        self._load_config_cards()
        self._connect_signals()
    
    def _setup_ui(self):
        """设置UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(16)
        
        # 标题栏
        header_layout = QHBoxLayout()
        header_layout.setSpacing(12)
        
        title_label = BodyLabel(self.tr("Multi-Run Manager"))
        title_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # 全部停止按钮
        self.stop_all_button = TransparentPushButton(self.tr("Stop All"), self, FIF.CLOSE)
        self.stop_all_button.clicked.connect(self._on_stop_all_clicked)
        header_layout.addWidget(self.stop_all_button)
        
        # 刷新按钮
        self.refresh_button = TransparentPushButton(self.tr("Refresh"), self, FIF.SYNC)
        self.refresh_button.clicked.connect(self._refresh_cards)
        header_layout.addWidget(self.refresh_button)
        
        main_layout.addLayout(header_layout)
        
        # 运行状态摘要
        self.status_label = CaptionLabel()
        self._update_status_summary()
        main_layout.addWidget(self.status_label)
        
        # 滚动区域
        scroll_area = ScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setStyleSheet("background: transparent; border: none;")
        
        # 配置卡片容器
        self.cards_container = QWidget()
        self.cards_layout = QGridLayout(self.cards_container)
        self.cards_layout.setSpacing(16)
        self.cards_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        
        scroll_area.setWidget(self.cards_container)
        main_layout.addWidget(scroll_area)
    
    def _connect_signals(self):
        """连接信号"""
        # 监听配置变化
        self._coordinator.fs_signal_bus.fs_config_added.connect(self._on_config_added)
        self._coordinator.fs_signal_bus.fs_config_removed.connect(self._on_config_removed)
        
        # 监听状态变化
        self._coordinator.fs_signal_bus.fs_start_button_status.connect(
            self._on_status_changed
        )
    
    def _load_config_cards(self):
        """加载配置卡片"""
        # 清除现有卡片
        for card in self._config_cards.values():
            card.cleanup()
            card.deleteLater()
        self._config_cards.clear()
        
        # 清除布局
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            widget = item.widget() if item else None
            if widget:
                widget.deleteLater()
        
        # 创建新卡片
        row, col = 0, 0
        max_cols = 4  # 每行最多4个卡片
        
        for config_instance in self._coordinator.config:
            card = ConfigMonitorCard(config_instance, self.cards_container)
            self._config_cards[config_instance.id] = card
            self.cards_layout.addWidget(card, row, col)
            
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
        
        self._update_status_summary()
    
    def _refresh_cards(self):
        """刷新卡片"""
        self._coordinator.config.refresh()
        self._load_config_cards()
    
    def _on_config_added(self, config_id: str):
        """处理配置添加"""
        self._refresh_cards()
    
    def _on_config_removed(self, config_id: str):
        """处理配置删除"""
        if config_id in self._config_cards:
            card = self._config_cards.pop(config_id)
            card.cleanup()
            card.deleteLater()
        self._refresh_cards()
    
    def _on_status_changed(self, status: dict):
        """处理状态变化"""
        self._update_status_summary()
    
    def _update_status_summary(self):
        """更新状态摘要"""
        total = len(self._coordinator.config)
        running = len(self._coordinator.config.running())
        self.status_label.setText(
            self.tr("Total: {total} configurations, {running} running").format(
                total=total, running=running
            )
        )
    
    def _on_stop_all_clicked(self):
        """停止所有运行中的配置"""
        self.stop_all_button.setEnabled(False)
        self._coordinator.config.stop_all()
        QTimer.singleShot(1000, lambda: self.stop_all_button.setEnabled(True))
    
    def showEvent(self, event):
        """显示事件"""
        super().showEvent(event)
        self._refresh_cards()
    
    def hideEvent(self, event):
        """隐藏事件"""
        super().hideEvent(event)
        # 停止所有卡片的预览刷新（可选，节省资源）
        # for card in self._config_cards.values():
        #     card.cleanup()
