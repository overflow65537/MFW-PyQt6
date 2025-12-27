from re import S
from PySide6.QtCore import QMetaObject, QCoreApplication

from PySide6.QtWidgets import (
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QSizePolicy,
)


from app.core.core import ServiceCoordinator
from app.view.task_interface.components.LogoutputWidget import LogoutputWidget
from app.view.task_interface.components.ListToolBarWidget import (
    TaskListToolBarWidget,
    ConfigListToolBarWidget,
)
from app.view.task_interface.components.OptionWidget import OptionWidget
from app.view.task_interface.components.DescriptionWidget import DescriptionWidget
from app.view.task_interface.components.StartBarWidget import StartBarWidget


class UI_TaskInterface(object):
    def __init__(self, service_coordinator: ServiceCoordinator, parent=None):
        self.service_coordinator = service_coordinator
        self.parent = parent

    def setupUi(self, TaskInterface):
        TaskInterface.setObjectName("TaskInterface")
        # 主窗口
        self.main_layout = QHBoxLayout()
        # 设置间距，确保组件间距保持不变
        self.main_layout.setSpacing(8)  # 可以根据需要调整间距值
        self.log_output_widget = LogoutputWidget(service_coordinator=self.service_coordinator)

        self._init_control_panel()
        self._init_description_panel()
        self._init_option_panel()

        self.main_layout.addWidget(self.control_panel)
        self.main_layout.addWidget(self.description_panel_widget)
        self.main_layout.addWidget(self.option_panel_widget)
        # 设置拉伸因子：任务列表和日志/选项区域不拉伸（0），公告区域拉伸（1）
        self.main_layout.setStretch(0, 0)  # 任务列表：固定宽度
        self.main_layout.setStretch(1, 1)  # 公告区域：可拉伸
        self.main_layout.setStretch(2, 0)  # 日志/选项区域：固定宽度

        TaskInterface.setLayout(self.main_layout)
        self.retranslateUi(TaskInterface)
        QMetaObject.connectSlotsByName(TaskInterface)

    def _init_description_panel(self):
        """初始化说明面板"""
        self.description_panel_widget = QWidget()
        self.description_panel_layout = QVBoxLayout(self.description_panel_widget)
        # 设置最小宽度，允许拉伸
        self.description_panel_widget.setMinimumWidth(344)
        # 设置大小策略：水平方向可拉伸，垂直方向可拉伸
        description_policy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.description_panel_widget.setSizePolicy(description_policy)

        # 设置边距：左右各30px，上22px，下0px
        self.description_panel_layout.setContentsMargins(20, 22, 20, 0)
        
        # 创建说明组件
        self.description_widget = DescriptionWidget()
        self.description_panel_layout.addWidget(self.description_widget)
        
    def _init_option_panel(self):
        """初始化选项面板"""
        self.option_panel_widget = QWidget()
        # 设置固定宽度，垂直方向可拉伸
        self.option_panel_widget.setFixedWidth(344)
        option_panel_policy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        self.option_panel_widget.setSizePolicy(option_panel_policy)
        self.option_panel_layout = QVBoxLayout(self.option_panel_widget)

        self.option_panel_layout.setContentsMargins(0, 8, 0, 0)
        self.option_panel_layout.setSpacing(0)
        
        # 创建堆叠窗口，用于在选项和日志之间切换
        from PySide6.QtWidgets import QStackedWidget
        self.option_stack = QStackedWidget()
        # 设置大小策略，确保占据全部空间
        stack_policy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.option_stack.setSizePolicy(stack_policy)
        self.option_panel_layout.addWidget(self.option_stack)
        
        # 选项面板（传入说明组件引用）
        self.option_panel = OptionWidget(
            service_coordinator=self.service_coordinator,
            description_widget=self.description_widget
        )
        self.option_panel.setFixedWidth(344)
        # 设置大小策略，确保占据全部空间
        option_policy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.option_panel.setSizePolicy(option_policy)
        self.option_stack.addWidget(self.option_panel)
        
        # 日志面板
        self.log_output_widget.setFixedWidth(344)
        # 设置大小策略，确保占据全部空间
        log_policy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.log_output_widget.setSizePolicy(log_policy)
        self.option_stack.addWidget(self.log_output_widget)
        
        # 创建动画器
        from app.view.task_interface.animations.stacked_widget_transition import StackedWidgetTransitionAnimator
        self.option_stack_animator = StackedWidgetTransitionAnimator(
            self.option_stack,
            duration=250
        )
        
        # 默认显示选项面板
        self.option_stack.setCurrentIndex(0)

    def _init_control_panel(self):
        """初始化控制面板"""
        self.config_selection = ConfigListToolBarWidget(
            service_coordinator=self.service_coordinator
        )
        self.config_selection.setFixedWidth(344)
        self.config_selection.setFixedHeight(195)

        self.start_bar = StartBarWidget()
        self.start_bar.setFixedWidth(344)

        # 控制面板布局
        self.control_panel = QWidget()
        self.control_panel_layout = QVBoxLayout(self.control_panel)
        # 控制面板总体布局
        self.task_info = TaskListToolBarWidget(
            service_coordinator=self.service_coordinator,
            task_filter_mode="normal",
        )
        self.task_info.setFixedWidth(344)
        
        # 设置控制面板固定宽度，垂直方向可拉伸
        self.control_panel.setFixedWidth(344)
        control_policy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        self.control_panel.setSizePolicy(control_policy)

        self.control_panel_layout.addWidget(self.config_selection)
        self.control_panel_layout.addWidget(self.task_info)
        self.control_panel_layout.addWidget(self.start_bar)

        # 设置比例
        self.control_panel_layout.setStretch(0, 5)
        self.control_panel_layout.setStretch(1, 10)
        self.control_panel_layout.setStretch(2, 1)

    def retranslateUi(self, TaskInterface):
        _translate = QCoreApplication.translate
        TaskInterface.setWindowTitle(_translate("TaskInterface", "Form"))
