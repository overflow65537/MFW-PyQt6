from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QMouseEvent
from qfluentwidgets import PushButton, PrimaryPushButton


class RightCheckButton(PushButton):
    rightClicked = Signal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.RightButton:
            self.rightClicked.emit()
        super().mousePressEvent(event)


class RightCheckPrimaryPushButton(PrimaryPushButton):
    rightClicked = Signal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.RightButton:
            self.rightClicked.emit()
        super().mousePressEvent(event)
