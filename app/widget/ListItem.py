from PySide6.QtWidgets import (
    QWidget,
    QListWidgetItem,
    QHBoxLayout,
    QApplication,
    QSizePolicy,
)

from PySide6.QtCore import Signal, Qt, QMimeData, QPoint, QEvent


from PySide6.QtGui import QWheelEvent, QMouseEvent, QDrag, QPixmap, QPainter, QColor
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

from ..core.ItemManager import TaskItem,ConfigItem


class ClickableLabel(BodyLabel):
    clicked = Signal()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class ListItem(QWidget):
    show_option = Signal(str)
    # 信号：复选框状态变化
    checkbox_state_changed = Signal(str, bool)

    is_checked: bool = False
    name: str = ""
    item_id: str = ""

    def __init__(self, parent=None):
        super(ListItem, self).__init__(parent)
        self.initUI()

    def set_task_info(self, item:TaskItem|ConfigItem):
        self.item = item
        self.name = item.get("name")
        self.is_checked = item.get("is_checked")
        self.item_id = item.get("item_id")
        self.checkbox.setChecked(self.is_checked)
        self.placeholder_label.setText(self.name)

    def initUI(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)

        # 复选框
        self.checkbox = CheckBox()

        self.checkbox.setFixedSize(34, 34)

        layout.addWidget(self.checkbox)

        # 占位label
        self.placeholder_label = ClickableLabel()
        self.placeholder_label.setFixedHeight(34)

        self.placeholder_label.clicked.connect(self.on_button_clicked)

        # 设置占用所有剩余空间
        self.placeholder_label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )

        layout.addWidget(self.placeholder_label)

        # 按钮
        self.setting_button = TransparentToolButton(FIF.SETTING)
        self.setting_button.setFixedSize(34, 34)

        self.setting_button.clicked.connect(self.on_button_clicked)

        layout.addWidget(self.setting_button)

        # 复选框状态变化信号
        self.checkbox.stateChanged.connect(self.on_checkbox_changed)

    def on_button_clicked(self):
        print(f"{self.name}点击按钮")
        self.show_option.emit(self.item_id)

    def on_checkbox_changed(self, state):
        self.checkbox_state_changed.emit(self.item_id, state == 2)

    def hiden_setting_button(self):
        self.setting_button.hide()
