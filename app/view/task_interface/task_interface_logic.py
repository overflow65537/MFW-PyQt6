import asyncio

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QWidget,
    QApplication,
)
from PySide6.QtGui import QShowEvent
from qfluentwidgets import (
    FluentIcon as FIF,
)

from app.view.task_interface.task_interface_ui import UI_TaskInterface
from app.utils.logger import logger


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

        self._timeout_restarting = False

        if self.service_coordinator:
            try:
                run_manager = getattr(self.service_coordinator, "run_manager", None)
                if run_manager:
                    # 监听任务超时需要重启的信号
                    if hasattr(run_manager, "task_timeout_restart_requested"):
                        run_manager.task_timeout_restart_requested.connect(
                            self._on_timeout_restart_requested
                        )
            except (AttributeError, RuntimeError) as e:
                logger.warning(f"无法连接任务超时信号: {e}")

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
            # 立即禁用按钮
            self.start_bar.run_button.setDisabled(True)
            # 强制处理UI事件，确保按钮状态立即更新
            QApplication.processEvents()
            
            self._timeout_restarting = False
            
            def _start_task():
                self.log_output_widget.clear_log()
                asyncio.create_task(self.service_coordinator.run_tasks_flow())
            
            # 使用 QTimer 延迟执行，避免阻塞UI更新
            QTimer.singleShot(0, _start_task)
        else:
            # 立即禁用按钮
            self.start_bar.run_button.setDisabled(True)
            # 强制处理UI事件，确保按钮状态立即更新
            QApplication.processEvents()
            
            def _stop_task():
                asyncio.create_task(self.service_coordinator.stop_task())
            
            # 使用 QTimer 延迟执行
            QTimer.singleShot(0, _stop_task)

    def _on_button_status_changed(self, status):
        """处理按钮状态变化信号"""
        """状态格式: {"text": "STOP", "status": "disabled"}"""
        # 更新启动/停止按钮状态
        if status.get("text") == "STOP":
            self.start_bar.run_button.setText(self.tr("Stop"))
            self.start_bar.run_button.setIcon(FIF.CLOSE)
        else:
            self.start_bar.run_button.setText(self.tr("Start"))
            self.start_bar.run_button.setIcon(FIF.PLAY)
            # 如果正在等待重启且按钮已启用，触发重启
            if self._timeout_restarting and status.get("status") == "enabled":
                QTimer.singleShot(100, lambda: self._trigger_restart_if_ready())

        # 设置按钮是否可用
        self.start_bar.run_button.setEnabled(status.get("status") != "disabled")

    def _on_timeout_restart_requested(self):
        """处理任务超时需要重启的请求"""
        self._timeout_restarting = True
        self.restart_tasks_via_button()

    def _trigger_restart_if_ready(self):
        """如果按钮已准备好，触发重启。"""
        button = self.start_bar.run_button
        if button.text() == self.tr("Start") and button.isEnabled():
            # 超时重启，直接调用 run_tasks_flow 并传递 is_timeout_restart=True
            self._timeout_restarting = False  # 清除标志，准备启动
            asyncio.create_task(
                self.service_coordinator.run_tasks_flow(is_timeout_restart=True)
            )

    def restart_tasks_via_button(self):
        """确保先停止再启动，复用 run_button 的 click 事件。"""
        button = self.start_bar.run_button

        if button.text() == self.tr("Stop"):
            # 设置重启标志，然后点击停止
            # 按钮状态恢复为"Start"并启用时，会在 _on_button_status_changed 中自动触发重启
            self._timeout_restarting = True
            button.click()
        elif button.text() == self.tr("Start") and button.isEnabled():
            # 如果已经是"Start"状态且可用，直接点击
            button.click()

    def showEvent(self, event: QShowEvent):
        """界面显示时自动选中第0个任务"""
        super().showEvent(event)
        # 使用定时器延迟执行，确保任务列表已经加载完成
        QTimer.singleShot(50, lambda: self.option_panel.reset())