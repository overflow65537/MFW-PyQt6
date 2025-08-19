from PySide6.QtWidgets import QWidget, QListWidgetItem, QHBoxLayout, QApplication
from PySide6.QtCore import Signal, Qt, QMimeData, QPoint, QEvent


from PySide6.QtGui import QWheelEvent, QMouseEvent, QDrag, QPixmap, QPainter
from qfluentwidgets import (
    CheckBox,
    TransparentToolButton,
    BodyLabel,
    SimpleCardWidget,
    ToolTipFilter,
    ToolTipPosition,
    FluentIcon as FIF,
)


class ListItem(QWidget):
    def __init__(self, text, parent=None):
        super(ListItem, self).__init__(parent)
        self.text = text
        self.initUI()

    def initUI(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)

        """#拖动按钮
        self.drag_button = TransparentToolButton(FIF.SCROLL)
        layout.addWidget(self.drag_button)"""


        # 复选框
        self.checkbox = CheckBox(self.text)
        layout.addWidget(self.checkbox)

        # 按钮
        self.setting_button = TransparentToolButton(FIF.SETTING)
        self.setting_button.clicked.connect(self.on_button_clicked)
        layout.addWidget(self.setting_button)

        # 复选框状态变化信号
        self.checkbox.stateChanged.connect(self.on_checkbox_changed)

    def on_button_clicked(self):
        print(f"按钮被点击: {self.text}")

    def on_checkbox_changed(self, state):
        status = "选中" if state == 2 else "未选中"
        print(f"{self.text} {status}")
