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
    ComboBox,
    FluentIcon as FIF,
)


class TaskListItem(QWidget):
    def __init__(self, text, parent=None):
        super(TaskListItem, self).__init__(parent)
        self.text = text
        self.initUI()

    def initUI(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)

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

class ResourceListItem(QWidget):
    def __init__(self, text, parent=None):
        super(ResourceListItem, self).__init__(parent)
        self.text = text
        self.initUI()

    def initUI(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)


        # 下拉框
        self.comboBox = ComboBox()
        self.comboBox.currentTextChanged.connect(self.on_combox_change)

        layout.addWidget(self.comboBox)


    def on_combox_change(self, text):
        print(text)

