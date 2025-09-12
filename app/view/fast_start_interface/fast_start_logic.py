from typing import Dict
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QTableWidgetItem,
    QListWidgetItem,
    QHBoxLayout,
    QSizePolicy,
)
from qfluentwidgets import CheckBox, TransparentToolButton, FluentIcon as FIF


from ..fast_start_interface.fast_start_ui import UI_FastStartInterface



class FastStartInterface(UI_FastStartInterface, QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent=parent)
        self.setupUi(self)
        
        self.task_info.set_title(
            self.tr("任务信息")
        )
        self.config_selection.set_title(
            self.tr("配置选择")
        )
        self.option_panel.set_title(self.tr("选项"))