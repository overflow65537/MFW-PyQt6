from PyQt6.QtCore import Qt
from qfluentwidgets import BodyLabel
from ..common.signal_bus import signalBus


class ClickableLabel(BodyLabel):

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            signalBus.dragging_finished.emit()
        super().mousePressEvent(event)
