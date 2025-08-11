from PySide6.QtCore import Qt, QSize, QMetaObject, QCoreApplication
from PySide6.QtWidgets import (
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QGridLayout,
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
from ...widget.DashboardCard import DashboardCard
from ...widget.LogoutputWidget import LogoutputWidget
from ...widget.GenericListToolBarWidget import GenericListToolBarWidget
from ...widget.StartBarWidget import StartBarWidget


class UI_FastStartInterface(object):

    def setupUi(self, FastStartInterface):
        FastStartInterface.setObjectName("FastStartInterface")
        FastStartInterface.resize(900, 600)
        FastStartInterface.setMinimumSize(QSize(0, 0))
        # 主窗口
        self.main_layout = QHBoxLayout()
        self.log_output_widget = LogoutputWidget()

        self._init_control_panel()

        self.main_layout.addWidget(self.control_panel)
        self.main_layout.addWidget(self.log_output_widget)
        self.main_layout.setStretch(0, 1)
        self.main_layout.setStretch(1, 9)

        FastStartInterface.setLayout(self.main_layout)
        self.retranslateUi(FastStartInterface)
        QMetaObject.connectSlotsByName(FastStartInterface)

    def _init_control_panel(self):
        """初始化控制面板"""
        self._init_task_info()
        self.config_selection = GenericListToolBarWidget()
        self.config_selection.setFixedWidth(344)

        self.start_bar = StartBarWidget()
        self.start_bar.setFixedWidth(344)

        # 控制面板布局
        self.control_panel = QWidget()
        self.control_panel_layout = QVBoxLayout(self.control_panel)
        # 控制面板总体布局

        self.control_panel_layout.addWidget(self.task_info)
        self.control_panel_layout.addWidget(self.config_selection)
        self.control_panel_layout.addWidget(self.start_bar)

    def _init_task_info(self):
        """初始化任务信息"""
        # 标题
        self.task_info_title = BodyLabel("任务信息")
        self.task_info_title.setStyleSheet("font-size: 20px;")
        self.task_info_title.setAlignment(Qt.AlignmentFlag.AlignLeft)

        # 任务状态
        self.status = DashboardCard(
            title="状态",
            value="未开始",
            unit="",
            icon=FIF.STOP_WATCH,
        )
        self.status.setFixedSize(160, 160)

        # 总节点数量
        self.total_node = DashboardCard(
            title="总节点数量",
            value="0",
            unit="",
            icon=FIF.STOP_WATCH,
        )
        self.total_node.setFixedSize(160, 160)

        # 失败节点数量
        self.fail_node = DashboardCard(
            title="失败节点数量",
            value="0",
            unit="",
            icon=FIF.STOP_WATCH,
        )
        self.fail_node.setFixedSize(160, 160)

        # 下一节点
        self.next_node = DashboardCard(
            title="下一节点",
            value="0",
            unit="",
            icon=FIF.STOP_WATCH,
        )
        self.next_node.setFixedSize(160, 160)

        # 累计时间
        self.cumulative_time = DashboardCard(
            title="累计时间",
            value="--:--",
            unit="",
            icon=FIF.STOP_WATCH,
        )
        self.cumulative_time.setFixedSize(160, 160)

        # 任务信息布局
        self.task_info_layout = QGridLayout()
        self.task_info_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.task_info_layout.addWidget(self.status, 0, 0)
        self.task_info_layout.addWidget(self.total_node, 1, 0)
        self.task_info_layout.addWidget(self.fail_node, 0, 1)
        self.task_info_layout.addWidget(self.cumulative_time, 1, 1)

        # 任务信息总体布局
        self.task_info = QWidget()
        self.task_info.setFixedWidth(350)
        self.task_info_main_layout = QVBoxLayout(self.task_info)
        self.task_info_main_layout.addWidget(self.task_info_title)
        self.task_info_main_layout.addLayout(self.task_info_layout)

    def retranslateUi(self, FastStartInterface):
        _translate = QCoreApplication.translate
        FastStartInterface.setWindowTitle(_translate("FastStartInterface", "Form"))
