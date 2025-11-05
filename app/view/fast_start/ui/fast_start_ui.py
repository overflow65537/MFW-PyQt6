from re import S
from PySide6.QtCore import Qt, QSize, QMetaObject, QCoreApplication

from PySide6.QtWidgets import (
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QGridLayout,
    QSizePolicy,
)

from qfluentwidgets import (
    BodyLabel,
    ComboBox,
    ListWidget,
    ToolButton,
    TextEdit,
    FluentIcon as FIF,
    SimpleCardWidget,
    TransparentPushButton,
    ToolTipFilter,
    ToolTipPosition,
)
from ....core.core import ServiceCoordinator
from ....widget.DashboardCard import DashboardCard
from .components.LogoutputWidget import LogoutputWidget
from .components.ListToolBarWidget import TaskListToolBarWidget,ConfigListToolBarWidget,OptionWidget
from .components.StartBarWidget import StartBarWidget


class UI_FastStartInterface(object):
    def __init__(self, service_coordinator: ServiceCoordinator , parent=None):
        self.service_coordinator = service_coordinator
        self.parent = parent

    def setupUi(self, FastStartInterface):
        FastStartInterface.setObjectName("FastStartInterface")
        # 主窗口
        self.main_layout = QHBoxLayout()
        self.log_output_widget = LogoutputWidget()

        self._init_control_panel()
        self._init_option_panel()

        self.main_layout.addWidget(self.control_panel)
        self.main_layout.addWidget(self.option_panel_widget)
        self.main_layout.addWidget(self.log_output_widget)
        self.main_layout.setStretch(0, 1)
        self.main_layout.setStretch(1, 1)
        self.main_layout.setStretch(2, 99)

        FastStartInterface.setLayout(self.main_layout)
        self.retranslateUi(FastStartInterface)
        QMetaObject.connectSlotsByName(FastStartInterface)

    def _init_option_panel(self):
        """初始化选项面板"""
        self.option_panel_widget = QWidget()
        self.option_panel_layout = QVBoxLayout(self.option_panel_widget)
        self.option_panel = OptionWidget(service_coordinator=self.service_coordinator)
        self.option_panel.setFixedWidth(344)
        self.option_panel_layout.addWidget(self.option_panel)

    def _init_control_panel(self):
        """初始化控制面板"""
        self.config_selection = ConfigListToolBarWidget(service_coordinator=self.service_coordinator)
        self.config_selection.setFixedWidth(344)
        self.config_selection.setFixedHeight(195)

        self.start_bar = StartBarWidget()
        self.start_bar.setFixedWidth(344)

        # 控制面板布局
        self.control_panel = QWidget()
        self.control_panel_layout = QVBoxLayout(self.control_panel)
        # 控制面板总体布局
        self.task_info = TaskListToolBarWidget(service_coordinator=self.service_coordinator)
        self.task_info.setFixedWidth(344)

        self.control_panel_layout.addWidget(self.config_selection)
        self.control_panel_layout.addWidget(self.task_info)
        self.control_panel_layout.addWidget(self.start_bar)

        # 设置比例
        self.control_panel_layout.setStretch(0, 5)
        self.control_panel_layout.setStretch(1, 10)
        self.control_panel_layout.setStretch(2, 1)

    def retranslateUi(self, FastStartInterface):
        _translate = QCoreApplication.translate
        FastStartInterface.setWindowTitle(_translate("FastStartInterface", "Form"))
