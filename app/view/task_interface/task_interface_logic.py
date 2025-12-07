import asyncio
from PySide6.QtWidgets import (
    QWidget,
)
from qfluentwidgets import (
    FluentIcon as FIF,
)


from app.view.task_interface.task_interface_ui import UI_TaskInterface
from app.common.signal_bus import signalBus
from app.common.config import cfg


class TaskInterface(UI_TaskInterface, QWidget):
    def __init__(self, service_coordinator=None, parent=None):
        QWidget.__init__(self, parent=parent)
        UI_TaskInterface.__init__(
            self, service_coordinator=service_coordinator, parent=parent
        )
        self.setupUi(self)
        self.service_coordinator = service_coordinator

        self.task_info.set_title(self.tr("Task Information"))
        self.config_selection.set_title(self.tr("Configuration Selection"))

        # 连接启动/停止按钮事件
        self.start_bar.run_button.clicked.connect(self._on_run_button_clicked)

        # 连接服务协调器的信号，用于更新按钮状态
        self.service_coordinator.fs_signals.fs_start_button_status.connect(
            self._on_button_status_changed
        )

    def _on_start_button_clicked(self):
        """处理开始按钮点击事件"""
        # 启动任务流
        asyncio.create_task(self.service_coordinator.run_tasks_flow())

    def _on_stop_button_clicked(self):
        """处理停止按钮点击事件"""
        # 停止任务流
        asyncio.create_task(self.service_coordinator.stop_task())

    def _on_run_button_clicked(self):
        """处理启动/停止按钮点击事件"""
        # 检查按钮当前状态并执行相应操作
        if self.start_bar.run_button.text() == self.tr("Start"):
            self.log_output_widget.clear_log()
            asyncio.create_task(self.service_coordinator.run_tasks_flow())
        else:
            asyncio.create_task(self.service_coordinator.stop_task())

    def _on_button_status_changed(self, status):
        """处理按钮状态变化信号"""
        """状态格式: {"text": "STOP", "status": "disabled"}"""
        # 更新启动/停止按钮状态
        if status.get("text") == "STOP":
            self.start_bar.run_button.setText(self.tr("Stop"))
            self.start_bar.run_button.setIcon(FIF.CLOSE)
        else:
            self.service_coordinator.task_runner.speedrun_mode = cfg.get(
                cfg.speedrun_mode
            )
            self.start_bar.run_button.setText(self.tr("Start"))
            self.start_bar.run_button.setIcon(FIF.PLAY)

        # 设置按钮是否可用
        self.start_bar.run_button.setEnabled(status.get("status") != "disabled")
