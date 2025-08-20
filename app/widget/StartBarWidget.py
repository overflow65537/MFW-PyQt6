from PySide6.QtCore import QPoint
from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout

from qfluentwidgets import (
    BodyLabel,
    ComboBox,
    SimpleCardWidget,
    TransparentPushButton,
    TransparentDropDownPushButton,
    RoundMenu,
    Action,
    ToolButton,
    FluentIcon as FIF,
)



class StartBarWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_start_bar()
        self.start_bar_main_layout = QVBoxLayout(self)

        self.title = BodyLabel("启动栏")

        self.setting = ToolButton(FIF.SETTING)

        self.title_layout = QHBoxLayout()
        self.title_layout.addWidget(self.title)
        self.title_layout.addWidget(self.setting)

        self.start_bar_main_layout.addLayout(self.title_layout)

        self.start_bar_main_layout.addWidget(self.main_widget)

    def setRunAfterFinishVisible(self, visible: bool):
        """设置完成后运行是否显示"""
        if not visible:
            self.run_after_finish_combox.hide()
            self.run_after_finish.hide()

    def _init_start_bar(self):
        """初始化启动栏"""
        # 启动按钮
        self.start_button = TransparentPushButton("启动", self, FIF.PLAY)

        # 停止按钮
        # self.stop_button = TransparentPushButton("停止", self, FIF.CLOSE)
        # self.stop_button.setDisabled(True)

        # 完成后运行
        self.run_after_finish = BodyLabel("完成后")

        # 完成后运行下拉框
        self.action_do_noting = Action("无动作")
        self.action_shutdown = Action("关机")
        self.action_close_software = Action("关闭软件")
        self.action_close_emulator = Action("关闭模拟器")
        self.action_close_software_and_emulator = Action("关闭软件和模拟器")
        self.action_run_tool_task = Action("运行工具任务")

        self.action_do_noting.triggered.connect(self._do_noting)
        self.action_shutdown.triggered.connect(self._shutdown)
        self.action_close_software.triggered.connect(self._close_software)
        self.action_close_emulator.triggered.connect(self._close_emulator)
        self.action_close_software_and_emulator.triggered.connect(
            self._close_software_and_emulator
        )
        self.action_run_tool_task.triggered.connect(self._run_tool_task)

        menu = RoundMenu(parent=self)
        menu.addAction(self.action_do_noting)
        menu.addAction(self.action_shutdown)
        menu.addAction(self.action_close_software)
        menu.addAction(self.action_close_emulator)
        menu.addAction(self.action_close_software_and_emulator)
        menu.addAction(self.action_run_tool_task)
        self.run_after_finish_combox = TransparentDropDownPushButton(self)
        self.run_after_finish_combox.setMenu(menu)

        self.auto_search_button = TransparentPushButton("搜索", self, FIF.SEARCH)

        self.controller_select = TransparentDropDownPushButton(self)

        self.controller = QWidget()

        self.controller_layout = QHBoxLayout(self.controller)
        self.controller_layout.addWidget(self.auto_search_button)
        self.controller_layout.addWidget(self.controller_select)

        self.start_bar = QWidget()

        self.start_bar_layout = QHBoxLayout(self.start_bar)
        self.start_bar_layout.addWidget(self.start_button)

        # 增加一条竖线
        line = BodyLabel("|")
        self.start_bar_layout.addWidget(line)
        self.start_bar_layout.addWidget(self.run_after_finish)
        self.start_bar_layout.addStretch()
        self.start_bar_layout.addWidget(self.run_after_finish_combox)

        self.controller_type = ComboBox()
        self.resource_type = ComboBox()

        self.top_widget = QWidget()

        self.top_widget_layout = QHBoxLayout(self.top_widget)
        self.top_widget_layout.addWidget(self.controller_type)
        self.top_widget_layout.addWidget(self.resource_type)



        # 启动栏总体布局
        self.main_widget = SimpleCardWidget()
        self.main_widget.setClickEnabled(False)
        self.main_widget.setBorderRadius(8)

        self.main_widget_layout = QVBoxLayout(self.main_widget)
        self.main_widget_layout.addWidget(self.top_widget)

        self.main_widget_layout.addWidget(self.controller)
        self.main_widget_layout.addWidget(self.start_bar)

    def _do_noting(self):
        """无动作"""
        self.run_after_finish_combox.setText("无动作")

    def _shutdown(self):
        """关机"""
        self.run_after_finish_combox.setText("关机")

    def _close_software(self):
        """关闭软件"""
        self.run_after_finish_combox.setText("关闭软件")

    def _close_emulator(self):
        """关闭模拟器"""
        self.run_after_finish_combox.setText("关闭模拟器")

    def _close_software_and_emulator(self):
        """关闭软件和模拟器"""
        self.run_after_finish_combox.setText("关闭软件和模拟器")

    def _run_tool_task(self):
        """运行工具任务"""
        self.run_after_finish_combox.setText("运行工具任务")
