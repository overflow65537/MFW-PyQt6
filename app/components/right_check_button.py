from PyQt6.QtCore import Qt, pyqtSignal
from qfluentwidgets import PushButton


class RightCheckButton(PushButton):
    rightClicked = pyqtSignal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton:
            self.rightClicked.emit()
        super().mousePressEvent(event)
