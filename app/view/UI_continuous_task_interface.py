from PyQt6.QtCore import Qt, QSize, QMetaObject, QCoreApplication
from PyQt6.QtWidgets import (
    QSizePolicy,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,QFrame
)

from qfluentwidgets import (
    PushButton,
    BodyLabel,
    ComboBox,
    RadioButton,
    CheckBox,
    SpinBox,ListWidget,
)


class Ui_ContinuousTaskInterface(object):
    def setupUi(self, Continuous_Task_Interface):
        Continuous_Task_Interface.setObjectName("Continuous_Task_Interface")
        Continuous_Task_Interface.resize(900, 600)
        Continuous_Task_Interface.setMinimumSize(QSize(0, 0))
        # 主窗口
        self.List_layout = QVBoxLayout()
        self.List_widget = ListWidget(Continuous_Task_Interface     )