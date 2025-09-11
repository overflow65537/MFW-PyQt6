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
from ..core.CoreSignalBus import CoreSignalBus
from ..core.ItemManager import TaskItem, ConfigItem


class ClickableLabel(BodyLabel):
    clicked = Signal()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class ListItem(QWidget):
    def __init__(
        self, item: TaskItem | ConfigItem, coresignalbus: CoreSignalBus, parent=None
    ):
        super(ListItem, self).__init__(parent)
        self.initUI()
        self.item = item
        self.coresignalbus = coresignalbus
        self.show_option = self.coresignalbus.show_option
        self.checkbox.setChecked(self.item.is_checked)
        self.placeholder_label.setText(self.item.name)

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
        print(f"{self.item.name}点击按钮")
        self.show_option.emit(self.item)

    def on_checkbox_changed(self, state):
        self.item.is_checked = state == 2
        self.coresignalbus.need_save.emit()

    def hiden_setting_button(self):
        self.setting_button.hide()
