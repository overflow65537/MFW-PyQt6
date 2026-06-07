from PySide6.QtCore import QMetaObject, QCoreApplication, Qt

from PySide6.QtWidgets import (
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QSizePolicy,
)


from app.core.core import ServiceCoordinator
from app.view.task_interface.components.logoutput_widget import LogoutputWidget
from app.view.task_interface.components.list_tool_bar_widget import (
    TaskListToolBarWidget,
    ConfigListToolBarWidget,
)
from app.view.task_interface.components.option_widget import OptionWidget
from app.view.task_interface.components.panel_splitter import (
    LOG_PANEL_MIN_WIDTH,
    PANEL_SECTION_SPACING,
    TaskInterfacePanelSplitter,
    panel_column_margins,
    panel_outer_margins,
)
from app.view.task_interface.components.start_bar_widget import StartBarWidget


class UI_TaskInterface(object):
    def __init__(self, service_coordinator: ServiceCoordinator, parent=None):
        self.service_coordinator = service_coordinator
        self.parent = parent

    def setupUi(self, TaskInterface):
        TaskInterface.setObjectName("TaskInterface")
        self.main_layout = QHBoxLayout()
        self.main_layout.setContentsMargins(*panel_outer_margins())
        self.main_layout.setSpacing(0)

        self.log_output_widget = LogoutputWidget(service_coordinator=self.service_coordinator)
        log_policy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.log_output_widget.setSizePolicy(log_policy)
        self.log_output_widget.setMinimumWidth(LOG_PANEL_MIN_WIDTH)

        self._init_control_panel()
        self._init_option_panel()

        self.main_splitter = TaskInterfacePanelSplitter()
        self.main_splitter.addWidget(self.control_panel)
        self.main_splitter.addWidget(self.option_panel_widget)
        self.main_splitter.addWidget(self.log_output_widget)
        self.main_splitter.setCollapsible(0, True)
        self.main_splitter.setCollapsible(1, False)
        self.main_splitter.setCollapsible(2, True)
        self.main_splitter.setStretchFactor(0, 1)
        self.main_splitter.setStretchFactor(1, 1)
        self.main_splitter.setStretchFactor(2, 1)
        self.main_splitter.setSizes([1, 1, 1])

        self.main_layout.addWidget(self.main_splitter)
        TaskInterface.setLayout(self.main_layout)
        self.retranslateUi(TaskInterface)
        QMetaObject.connectSlotsByName(TaskInterface)

    def _init_option_panel(self):
        """初始化选项面板"""
        self.option_panel_widget = QWidget()
        self.option_panel_layout = QVBoxLayout(self.option_panel_widget)
        self.option_panel = OptionWidget(service_coordinator=self.service_coordinator)
        option_policy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.option_panel.setSizePolicy(option_policy)
        self.option_panel.setMinimumWidth(0)
        self.option_panel_layout.setContentsMargins(0, 0, 0, 0)
        self.option_panel_layout.addWidget(self.option_panel)
        self.option_panel_widget.setMinimumWidth(0)

    def _init_control_panel(self):
        """初始化控制面板"""
        self.config_selection = ConfigListToolBarWidget(
            service_coordinator=self.service_coordinator
        )
        self.config_selection.setSizePolicy(
            QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        )
        self.config_selection.selection_widget.setMinimumHeight(155)

        self.start_bar = StartBarWidget()
        self.start_bar.setSizePolicy(
            QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        )

        self.control_panel = QWidget()
        self.control_panel_layout = QVBoxLayout(self.control_panel)
        self.control_panel_layout.setContentsMargins(*panel_column_margins("task"))
        self.control_panel_layout.setSpacing(PANEL_SECTION_SPACING)
        self.control_panel_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.task_info = TaskListToolBarWidget(
            service_coordinator=self.service_coordinator,
        )
        self.task_info.setSizePolicy(
            QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        )

        self.control_panel.setMinimumWidth(0)
        control_policy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        self.control_panel.setSizePolicy(control_policy)

        self.control_panel_layout.addWidget(self.config_selection)
        self.control_panel_layout.addWidget(self.task_info)
        self.control_panel_layout.addWidget(self.start_bar)

        self.control_panel_layout.setStretch(0, 0)
        self.control_panel_layout.setStretch(1, 1)
        self.control_panel_layout.setStretch(2, 0)

    def retranslateUi(self, TaskInterface):
        _translate = QCoreApplication.translate
        TaskInterface.setWindowTitle(_translate("TaskInterface", "Form"))

