import asyncio

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QWidget,
    QApplication,
)
from PySide6.QtGui import QHideEvent, QShowEvent
from qfluentwidgets import (
    FluentIcon as FIF,
)

from app.common.signal_bus import signalBus
from app.view.task_interface.task_interface_ui import UI_TaskInterface
class TaskInterface(UI_TaskInterface, QWidget):

    def __init__(self, service_coordinator=None, monitor_interface=None, parent=None):
        QWidget.__init__(self, parent=parent)
        UI_TaskInterface.__init__(
            self,
            service_coordinator=service_coordinator,
            monitor_interface=monitor_interface,
            parent=parent,
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

        # 进入任务页后的 UI 重置需避开主窗口 StackedWidget 的入场位移动画（约 300ms），否则内外纵向变化叠加会抖动
        self._show_reset_timer = QTimer(self)
        self._show_reset_timer.setSingleShot(True)
        self._show_reset_timer.timeout.connect(self._on_deferred_show_reset)

        self._restore_layout_timer = QTimer(self)
        self._restore_layout_timer.setSingleShot(True)
        self._restore_layout_timer.timeout.connect(self._restore_panel_layout)

        self.main_splitter.panel_geometry_changed.connect(
            self._on_panel_geometry_changed
        )
        signalBus.task_interface_layout_reset_requested.connect(
            self._reset_panel_layout
        )

    def _show_reset_delay_ms(self) -> int:
        win = self.window()
        stacked = getattr(win, "stackedWidget", None) if win is not None else None
        if stacked is not None and stacked.isAnimationEnabled():
            return 330
        return 50

    def _restore_panel_layout(self) -> None:
        if not self.isVisible():
            return
        if hasattr(self, "main_splitter"):
            if not self.main_splitter.restore_layout_from_config():
                self.main_splitter.apply_default_layout()
        QTimer.singleShot(0, self._sync_log_panel_geometry)

    def _reset_panel_layout(self) -> None:
        if not hasattr(self, "main_splitter"):
            return
        self.main_splitter.reset_saved_layout()
        QTimer.singleShot(0, self._sync_log_panel_geometry)

    def _on_panel_geometry_changed(self) -> None:
        QTimer.singleShot(0, self._sync_log_panel_geometry)

    def _sync_log_panel_geometry(self) -> None:
        log_panel = getattr(self, "log_output_widget", None)
        if log_panel is not None and hasattr(log_panel, "sync_panel_geometry"):
            log_panel.sync_panel_geometry()

    def _on_deferred_show_reset(self) -> None:
        if not self.isVisible():
            return
        self.option_panel.reset()
        if self.service_coordinator and self.service_coordinator.run_manager.is_running:
            self._set_task_list_editable(False)
        if hasattr(self, "task_info") and hasattr(self.task_info, "task_list"):
            task_list = self.task_info.task_list
            if self.service_coordinator and hasattr(self.service_coordinator, "option"):
                option_service = self.service_coordinator.option
                if hasattr(option_service, "clear_selection"):
                    option_service.clear_selection()
            task_list.setCurrentRow(-1)
            task_list.update()

    def _on_start_button_clicked(self):
        """处理开始按钮点击事件"""
        # 启动任务流
        asyncio.create_task(self.service_coordinator.run_tasks_flow())

    def _on_stop_button_clicked(self):
        """处理停止按钮点击事件"""
        # 停止任务流
        asyncio.create_task(self.service_coordinator.stop_task_flow())

    def _on_run_button_clicked(self):
        """处理启动/停止按钮点击事件"""
        # 检查按钮当前状态并执行相应操作
        if self.start_bar.run_button.text() == self.tr("Start"):
            # 立即禁用按钮
            self.start_bar.run_button.setDisabled(True)
            # 强制处理UI事件，确保按钮状态立即更新
            QApplication.processEvents()

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
                asyncio.create_task(self.service_coordinator.stop_task_flow())

            # 使用 QTimer 延迟执行
            QTimer.singleShot(0, _stop_task)

    def _on_button_status_changed(self, status):
        """处理按钮状态变化信号"""
        """状态格式: {"text": "STOP", "status": "disabled"}"""
        # 更新启动/停止按钮状态
        is_running = status.get("text") == "STOP"
        if is_running:
            self.start_bar.run_button.setText(self.tr("Stop"))
            self.start_bar.run_button.setIcon(FIF.CLOSE)
            # 任务流运行时，禁用任务列表的编辑功能
            self._set_task_list_editable(False)
        else:
            self.start_bar.run_button.setText(self.tr("Start"))
            self.start_bar.run_button.setIcon(FIF.PLAY)
            # 任务流停止时，启用任务列表的编辑功能
            self._set_task_list_editable(True)

        # 设置按钮是否可用
        self.start_bar.run_button.setEnabled(status.get("status") != "disabled")
    
    def _set_task_list_editable(self, enabled: bool):
        """设置任务列表的编辑功能是否可用
        
        Args:
            enabled: True 表示启用编辑功能，False 表示禁用
        """
        if not hasattr(self, 'task_info') or not self.task_info:
            return
        
        task_list = getattr(self.task_info, 'task_list', None)
        if not task_list:
            return
        
        # 禁用/启用拖动功能
        task_list.setDragEnabled(enabled)
        task_list.setAcceptDrops(enabled)
        
        # 禁用/启用工具栏按钮
        if hasattr(self.task_info, 'add_button'):
            self.task_info.add_button.setEnabled(enabled)
        if hasattr(self.task_info, 'delete_button'):
            self.task_info.delete_button.setEnabled(enabled)
        if hasattr(self.task_info, 'select_all_button'):
            self.task_info.select_all_button.setEnabled(enabled)
        if hasattr(self.task_info, 'deselect_all_button'):
            self.task_info.deselect_all_button.setEnabled(enabled)
        
        # 禁用/启用所有任务项的 checkbox 和删除按钮
        for i in range(task_list.count()):
            item = task_list.item(i)
            if not item:
                continue
            widget = task_list.itemWidget(item)
            if not widget:
                continue
            # 禁用/启用 checkbox（基础任务始终保持禁用）
            if hasattr(widget, 'checkbox') and hasattr(widget, 'task'):
                # 基础任务的 checkbox 始终保持禁用状态
                if not widget.task.is_base_task():
                    widget.checkbox.setEnabled(enabled)
            # 禁用/启用删除按钮（基础任务的删除按钮始终保持禁用）
            if hasattr(widget, 'setting_button') and hasattr(widget, 'task'):
                # 基础任务的删除按钮始终保持禁用状态
                if not widget.task.is_base_task():
                    widget.setting_button.setEnabled(enabled)
    
    def showEvent(self, event: QShowEvent):
        """界面显示时延迟重置选项区与任务选中（与主窗口页面切换动画错开）。"""
        super().showEvent(event)
        self._restore_layout_timer.stop()
        self._restore_layout_timer.start(0)
        self._show_reset_timer.stop()
        self._show_reset_timer.start(self._show_reset_delay_ms())

    def hideEvent(self, event: QHideEvent):
        self._show_reset_timer.stop()
        self._restore_layout_timer.stop()
        if hasattr(self, "main_splitter"):
            self.main_splitter.save_layout_to_config()
        super().hideEvent(event)
