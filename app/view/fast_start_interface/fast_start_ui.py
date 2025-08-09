from PySide6.QtCore import Qt, QSize, QMetaObject, QCoreApplication
from PySide6.QtWidgets import (
    QSizePolicy,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QFrame,
    QLayout,
    QListWidget,
)

from qfluentwidgets import (
    PushButton,
    BodyLabel,
    ComboBox,
    RadioButton,
    CheckBox,
    SpinBox,
    ListWidget,
    ScrollArea,
    FlowLayout,
    ToolButton,
    TextEdit,
    LineEdit,
    ListView,
    PrimarySplitPushButton,
    RoundMenu,
    Action,
    PrimaryPushButton
)
from qfluentwidgets import FlowLayout, FluentIcon as FIF
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
        self.main_layout.setStretch(0, 4)
        self.main_layout.setStretch(1, 6)

        FastStartInterface.setLayout(self.main_layout)
        self.retranslateUi(FastStartInterface)
        QMetaObject.connectSlotsByName(FastStartInterface)

    def _init_log_output(self):
        """初始化日志输出区域"""
        self._log_output_title()

        self.log_output_area = TextEdit()
        self.log_output_area.setReadOnly(True)
        self.log_output_area.setDisabled(True)

        self.log_output_widget = QWidget()
        self.log_output_layout = QVBoxLayout(self.log_output_widget)
        self.log_output_widget.setSizePolicy(
            QSizePolicy.Policy.Preferred,  # 水平策略保持不变
            QSizePolicy.Policy.Minimum,  # 垂直策略根据内容自动调整
        )
        self.log_output_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.log_output_layout.addLayout(self.log_output_title_layout)
        self.log_output_layout.addWidget(self.log_output_area)

    def _log_output_title(self):
        """初始化日志输出标题"""
        # 日志输出标题布局
        self.log_output_title_layout = QHBoxLayout()
        # 设置上边距
        self.log_output_title_layout.setContentsMargins(0, 5, 0, 0)

        # 日志输出标题
        self.log_output_title = BodyLabel("日志输出")

        # 设置字体大小
        self.log_output_title.setStyleSheet("font-size: 20px;")

        # 生成日志压缩包按钮
        self.generate_log_zip_button = ToolButton(FIF.SETTING, self)

        # 日志等级下拉框
        self.log_level_combox = ComboBox(self)
        self.log_level_combox.setObjectName("log_level_combox")
        self.log_level_combox.addItems(
            ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        )
        self.log_level_combox.setFixedWidth(120)

        # 标题左对齐,按钮和下拉框右对齐
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
        self.control_panel_layout.addWidget(self.task_info)
        self.control_panel_layout.addWidget(self.config_selection)
        self.control_panel_layout.addStretch()
        self.control_panel_layout.addWidget(self.start_bar)

    def _init_config_selection(self):
        """初始化配置选择"""
        # 配置选择布局
        self.config_selection = QWidget()
        self.config_selection_main_layout = QVBoxLayout(self.config_selection)

        self.config_selection_layout = FlowLayout()

        # 配置选择标题
        self.config_selection_title = BodyLabel("配置选择")
        self.config_selection_title.setStyleSheet("font-size: 20px;")

        self.config_selection_main_layout.addWidget(self.config_selection_title)
        self.config_selection_main_layout.addLayout(self.config_selection_layout)

        self.config_selection_combox = ListWidget(self)
        #设置长度
        self.config_selection_combox.setFixedWidth(335)

        self.config_selection_combox.setObjectName("config_selection_combox")
        self.config_selection_combox.addItems(["配置1", "配置2", "配置3"])
        # 左对齐

        self.config_selection_layout.addWidget(self.config_selection_combox)

    def _init_start_bar(self):
        """初始化启动栏"""
        # 启动栏布局
        self.start_bar = QWidget()
        # 水平布局
        self.start_bar_layout = QHBoxLayout(self.start_bar)

        # 启动按钮
        self.start_button = PrimaryPushButton("启动")

        self.start_bar_layout.addWidget(self.start_button)

        # 伸缩器
        self.start_bar_layout.addStretch()

        # 完成后运行
        self.run_after_finish = BodyLabel("完成后")
        self.start_bar_layout.addWidget(self.run_after_finish)

        # 下拉框
        self.run_after_finish_combox = ComboBox(self)
        self.run_after_finish_combox.setObjectName("run_after_finish_combox")
        self.run_after_finish_combox.addItems(["配置1", "配置2", "配置3"])
        self.start_bar_layout.addWidget(self.run_after_finish_combox)

    def _init_task_info(self):
        """初始化任务信息"""
        # 任务信息布局
        self.task_info = QWidget()
        self.task_info_main_layout = QVBoxLayout(self.task_info)
        self.task_info_layout = FlowLayout()

        # 设置标题
        self.task_info_title = BodyLabel("任务信息")
        self.task_info_title.setStyleSheet("font-size: 20px;")

        self.task_info_main_layout.addWidget(self.task_info_title)
        self.task_info_main_layout.addLayout(self.task_info_layout)
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
            value="00:00",
            unit="",
            icon=FIF.STOP_WATCH,
        )
        self.cumulative_time.setFixedSize(160, 160)

        # 任务信息布局
        self.task_info_layout.addWidget(self.status)

        self.task_info_layout.addWidget(self.total_node)
        self.task_info_layout.addWidget(self.fail_node)
        self.task_info_layout.addWidget(self.cumulative_time)

    def retranslateUi(self, FastStartInterface):
        _translate = QCoreApplication.translate
        FastStartInterface.setWindowTitle(_translate("FastStartInterface", "Form"))
