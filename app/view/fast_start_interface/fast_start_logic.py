from PySide6.QtWidgets import (

    QWidget,QTableWidgetItem

)


from ..fast_start_interface.fast_start_ui import UI_FastStartInterface
from ...widget.TaskWidgetItem import TaskWidgetItem




class FastStartInterface(UI_FastStartInterface, QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setupUi(self)
        self.config_selection.task_list.main_layout.addWidget(TaskWidgetItem("配置1", {}))
        self.config_selection.task_list.main_layout.addWidget(TaskWidgetItem("配置2", {}))
        self.config_selection.task_list.main_layout.addWidget(TaskWidgetItem("配置3", {}))
        self.config_selection.task_list.main_layout.addWidget(TaskWidgetItem("配置4", {}))
