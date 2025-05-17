from PySide6.QtWidgets import QWidget
from .UI_continuous_task_interface import Ui_ContinuousTaskInterface

class continuousTaskInterface(Ui_ContinuousTaskInterface):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setupUi(self)