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
from ..core.core import CoreSignalBus
from ..core.core import TaskItem, ConfigItem


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
        # 发出显示选项的信号
        self.coresignalbus.show_option.emit(self.item)
        

        parent = self.parent()
        while parent is not None:
           
            if hasattr(parent, 'findItems'):
    
                for i in range(parent.count()):# type: ignore 
                    list_item = parent.item(i) # type: ignore 
                
                    widget = parent.itemWidget(list_item) # type: ignore 
                    
                    if widget == self:
            
                        parent.setCurrentItem(list_item) # type: ignore 
                        break
                break
           
            parent = parent.parent()
    def on_checkbox_changed(self, state):
        self.item.is_checked = state == 2
        self.coresignalbus.need_save.emit()

    def hide_setting_button(self):
        self.setting_button.hide()
