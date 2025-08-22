from PySide6.QtWidgets import (
    QWidget,
    QListWidgetItem,
    QHBoxLayout,
    QApplication,
    QSizePolicy,
)

from PySide6.QtCore import Signal, Qt, QMimeData, QPoint, QEvent


from PySide6.QtGui import QWheelEvent, QMouseEvent, QDrag, QPixmap, QPainter
import click
from fastapi import Body
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


class ClickableLabel(BodyLabel):
    clicked = Signal()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class TaskListItem(QWidget):
    show_option = Signal(dict)

    def __init__(self, config, parent=None):
        super(TaskListItem, self).__init__(parent)
        self.config = config
        print(self.config)
        self.initUI()

    def initUI(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)

        # 复选框
        self.checkbox = CheckBox()
        self.checkbox.setFixedHeight(10)

        layout.addWidget(self.checkbox)

        # 占位label
        self.placeholder_label = ClickableLabel(self.config["name"])

        self.placeholder_label.setFixedHeight(34)
        self.placeholder_label.clicked.connect(self.on_button_clicked)
        # 左对齐,上下居中
        self.placeholder_label.setAlignment(
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft
        )

        # 设置占用所有剩余空间
        self.placeholder_label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )

        layout.addWidget(self.placeholder_label)

        # 按钮
        self.setting_button = TransparentToolButton(FIF.SETTING)
        self.setting_button.clicked.connect(self.on_button_clicked)

        layout.addWidget(self.setting_button)

        # 复选框状态变化信号
        self.checkbox.stateChanged.connect(self.on_checkbox_changed)

    def on_button_clicked(self):
        print("点击按钮")
        self.show_option.emit(self.config)

    def on_checkbox_changed(self, state):
        status = "选中" if state == 2 else "未选中"
        print(f"{self.config['name']} {status}")

    def hiden_setting_button(self):
        self.setting_button.hide()
