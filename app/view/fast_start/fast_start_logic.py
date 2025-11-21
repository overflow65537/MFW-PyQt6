from typing import Dict
from PySide6.QtCore import Qt
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


    



    