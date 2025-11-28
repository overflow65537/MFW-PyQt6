import asyncio
from typing import Dict
from PySide6.QtCore import Qt
from PySide6.QtCore import QThread
from PySide6.QtWidgets import (
    QWidget,
    QTableWidgetItem,
    QListWidgetItem,
    QHBoxLayout,
    QSizePolicy,
)
from qfluentwidgets import (
    CheckBox,
    TransparentToolButton,
    FluentIcon as FIF,
    InfoBar,
    InfoBarPosition,
)


from .fast_start_ui import UI_FastStartInterface
from app.common.signal_bus import signalBus



class FastStartInterface(UI_FastStartInterface, QWidget):
    def __init__(self,service_coordinator=None ,parent=None ):
        QWidget.__init__(self, parent=parent)
        UI_FastStartInterface.__init__(self,service_coordinator=service_coordinator,parent=parent)
        self.setupUi(self)
        self.service_coordinator = service_coordinator
        
        self.task_info.set_title(
            self.tr("任务信息")
        )
        self.config_selection.set_title(
            self.tr("配置选择")
        )
        
        # 连接日志事件信号以显示 InfoBar
        signalBus.log_event.connect(self._on_log_event)
        signalBus.infobar_signal.connect(self._on_infobar_signal)
        
        # 连接启动/停止按钮事件
        self.start_bar.run_button.clicked.connect(self._on_run_button_clicked)
        
        # 连接服务协调器的信号，用于更新按钮状态
        self.service_coordinator.fs_signals.fs_start_button_status.connect(self._on_button_status_changed)

    def _on_infobar_signal(self, text: str, infobar_type: str):
        """处理 infobar_signal 信号，显示 InfoBar 通知"""
        duration = max(3, min(10, len(text) // 20 + 3)) * 1000
        infobar_type = str(infobar_type).lower()
        if infobar_type == "succeed":
            InfoBar.success(
                title="",
                content=text,
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=duration,
                parent=self
            )
        elif infobar_type == "warning":
            InfoBar.warning(
                title="",
                content=text,
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=duration,
                parent=self
            )
        elif infobar_type == "error":
            InfoBar.error(
                title="",
                content=text,
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=duration,
                parent=self
            )
        else:
            InfoBar.info(
                title="",
                content=text,
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=duration,
                parent=self
            )
    
    def _on_log_event(self, payload: dict):
        """处理日志事件,显示 InfoBar 通知
        
        Args:
            payload: 日志事件载荷,包含 {text, level, color, output, infobar, infobar_type}
        """
        if not isinstance(payload, dict):
            return
        
        # 只处理需要显示 InfoBar 的事件
        if not payload.get("infobar", False):
            return
        
        text = str(payload.get("text", ""))
        infobar_type = str(payload.get("infobar_type", "info")).lower()
        
        # 计算停留时间:根据文字数量,最少3秒,最多10秒
        duration = max(3, min(10, len(text) // 20 + 3)) * 1000  # 转换为毫秒
        
        # 根据类型显示不同的 InfoBar
        if infobar_type == "succeed":
            InfoBar.success(
                title="",
                content=text,
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=duration,
                parent=self
            )
        elif infobar_type == "warning":
            InfoBar.warning(
                title="",
                content=text,
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=duration,
                parent=self
            )
        elif infobar_type == "error":
            InfoBar.error(
                title="",
                content=text,
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=duration,
                parent=self
            )
        else:  # info
            InfoBar.info(
                title="",
                content=text,
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=duration,
                parent=self
            )


    



    

    def _on_start_button_clicked(self):
        """处理开始按钮点击事件"""
        # 启动任务流
        asyncio.create_task(self.service_coordinator.run_tasks_flow())

    def _on_stop_button_clicked(self):
        """处理停止按钮点击事件"""
        # 停止任务流
        asyncio.create_task(self.service_coordinator.stop_task())
    
    def _on_run_button_clicked(self):
        """处理启动/停止按钮点击事件"""
        # 检查按钮当前状态并执行相应操作
        if self.start_bar.run_button.text() == "启动":
            asyncio.create_task(self.service_coordinator.run_tasks_flow())
        else:
            asyncio.create_task(self.service_coordinator.stop_task())
        
    def _on_button_status_changed(self, status):
        """处理按钮状态变化信号"""
        """状态格式: {"text": "STOP", "status": "disabled"}"""
        # 更新启动/停止按钮状态
        if status.get("text") == "STOP":
            self.start_bar.run_button.setText("停止")
            self.start_bar.run_button.setIcon(FIF.CLOSE)
        else:
            self.start_bar.run_button.setText("启动")
            self.start_bar.run_button.setIcon(FIF.PLAY)
        
        # 设置按钮是否可用
        self.start_bar.run_button.setEnabled(status.get("status") != "disabled")