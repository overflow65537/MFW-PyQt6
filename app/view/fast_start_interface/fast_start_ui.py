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


class UI_FastStartInterface(object):

    def setupUi(self, FastStartInterface):
        FastStartInterface.setObjectName("FastStartInterface")
        FastStartInterface.resize(900, 600)
        FastStartInterface.setMinimumSize(QSize(0, 0))
        # 主窗口
        self.main_layout = QHBoxLayout()
        self._init_log_output()
        self._init_control_panel()

        self.main_layout.addWidget(self.control_panel)
        self.main_layout.addWidget(self.log_output_widget)
        self.main_layout.setStretch(0, 1)
        self.main_layout.setStretch(1, 9)

        FastStartInterface.setLayout(self.main_layout)
        self.retranslateUi(FastStartInterface)
        QMetaObject.connectSlotsByName(FastStartInterface)

    def _init_log_output(self):
        """初始化日志输出区域"""
        self._log_output_title()
        # 日志输出区域
        self.log_output_area = TextEdit()
        self.log_output_area.setReadOnly(True)
        self.log_output_area.setDisabled(True)

        # 日志输出区域总体布局
        self.log_output_widget = QWidget()
        self.log_output_layout = QVBoxLayout(self.log_output_widget)
        self.log_output_layout.setContentsMargins(0, 15, 0, 20)
        self.log_output_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.log_output_layout.addLayout(self.log_output_title_layout)
        self.log_output_layout.addWidget(self.log_output_area)

    def _log_output_title(self):
        """初始化日志输出标题"""

        # 日志输出标题
        self.log_output_title = BodyLabel("日志输出")

        # 设置字体大小
        self.log_output_title.setStyleSheet("font-size: 20px;")

        # 生成日志压缩包按钮
        self.generate_log_zip_button = ToolButton(FIF.FEEDBACK, self)
        # 悬浮提示
        self.generate_log_zip_button.installEventFilter(
            ToolTipFilter(self.generate_log_zip_button, 0, ToolTipPosition.TOP)
        )
        # 日志等级下拉框
        self.log_level_combox = ComboBox(self)
        self.log_level_combox.installEventFilter(
            ToolTipFilter(self.log_level_combox, 0, ToolTipPosition.TOP)
        )
        self.log_level_combox.setObjectName("log_level_combox")
        self.log_level_combox.addItems(
            ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        )
        self.log_level_combox.setFixedWidth(120)

        # 日志输出区域标题栏总体布局
        self.log_output_title_layout = QHBoxLayout()
        self.log_output_title_layout.addWidget(self.log_output_title)
        self.log_output_title_layout.addWidget(self.generate_log_zip_button)
        self.log_output_title_layout.addWidget(self.log_level_combox)

    def _init_control_panel(self):
        """初始化控制面板"""
        self._init_task_info()
        self._init_config_selection()
        self._init_start_bar()

        # 控制面板布局
        self.control_panel = QWidget()
        self.control_panel_layout = QVBoxLayout(self.control_panel)
        # 控制面板总体布局

        self.control_panel_layout.addWidget(self.task_info)
        self.control_panel_layout.addWidget(self.config_selection)
        self.control_panel_layout.addWidget(self.start_bar_main)

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

    def _init_config_selection(self):
        """初始化配置选择"""
        # 配置选择标题
        self.config_selection_title = BodyLabel("配置选择")
        self.config_selection_title.setStyleSheet("font-size: 20px;")
        self.config_selection_title.setAlignment(Qt.AlignmentFlag.AlignLeft)

        # 配置选择列表
        self.config_selection_list = ListWidget(self)
        self.config_selection_list.setObjectName("config_selection_list")

        # 配置选择列表布局
        self.config_selection_widget = SimpleCardWidget()
        self.config_selection_widget.setClickEnabled(False)
        self.config_selection_widget.setBorderRadius(8)
        self.config_selection_widget.setFixedWidth(330)

        self.config_selection_layout = QVBoxLayout(self.config_selection_widget)
        self.config_selection_layout.addWidget(self.config_selection_list)

        # 配置选择总体布局
        self.config_selection = QWidget()
        self.config_selection_main_layout = QVBoxLayout(self.config_selection)
        self.config_selection_main_layout.addWidget(self.config_selection_title)
        self.config_selection_main_layout.addWidget(self.config_selection_widget)

    def _init_start_bar(self):
        """初始化启动栏"""
        # 启动按钮
        self.start_button = TransparentPushButton("启动", self, FIF.PLAY)

        # 停止按钮
        self.stop_button = TransparentPushButton("停止", self, FIF.CLOSE)
        self.stop_button.setDisabled(True)

        # 完成后运行
        self.run_after_finish = BodyLabel("完成后")

        # 下拉框
        self.run_after_finish_combox = ComboBox(self)
        self.run_after_finish_combox.setObjectName("run_after_finish_combox")
        self.run_after_finish_combox.addItems(["配置1", "配置2", "配置3"])
        #
        self.start_bar_main = QWidget()
        self.start_bar_main.setFixedWidth(350)

        self.start_bar_main_layout = QHBoxLayout(self.start_bar_main)

        # 启动栏总体布局
        self.start_bar = SimpleCardWidget()
        self.start_bar.setClickEnabled(False)
        self.start_bar.setBorderRadius(8)

        self.start_bar_layout = QHBoxLayout(self.start_bar)
        self.start_bar_layout.addWidget(self.start_button)
        self.start_bar_layout.addWidget(self.stop_button)

        self.start_bar_layout.addStretch()
        self.start_bar_layout.addWidget(self.run_after_finish)
        self.start_bar_layout.addWidget(self.run_after_finish_combox)

        self.start_bar_main_layout.addWidget(self.start_bar)

    def retranslateUi(self, FastStartInterface):
        _translate = QCoreApplication.translate
        FastStartInterface.setWindowTitle(_translate("FastStartInterface", "Form"))
