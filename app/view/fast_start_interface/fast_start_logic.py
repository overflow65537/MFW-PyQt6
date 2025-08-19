from PySide6.QtWidgets import (

    QWidget,QTableWidgetItem,QListWidgetItem


)


from ..fast_start_interface.fast_start_ui import UI_FastStartInterface
from ...widget.TaskWidgetItem import ListItem




class FastStartInterface(UI_FastStartInterface, QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setupUi(self)

        self.config_selection.add_item("配置1")
        self.config_selection.add_item("配置2")

