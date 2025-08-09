from PySide6.QtWidgets import (

    QWidget,

)


from ..fast_start_interface.fast_start_ui import UI_FastStartInterface



class FastStartInterface(UI_FastStartInterface, QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setupUi(self)