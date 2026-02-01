"""
任务界面逻辑层

多开模式重构：
1. 允许运行时切换配置
2. 切换配置时更新按钮状态
3. 每个配置独立管理运行状态
4. 监控跟随当前配置
"""

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
from app.common.config import cfg, Config


class TaskInterface(UI_TaskInterface, QWidget):

    def __init__(self, service_coordinator=None, parent=None):
        QWidget.__init__(self, parent=parent)
        UI_TaskInterface.__init__(
            self, service_coordinator=service_coordinator, parent=parent
        )
        self.setupUi(self)
        self.service_coordinator = service_coordinator
        
        # 当前配置ID（用于多开模式）
        self._current_config_id: str = ""

        self.task_info.set_title(self.tr("Task Information"))
        self.config_selection.set_title(self.tr("Configuration Selection"))

        # 连接启动/停止按钮事件
        self.start_bar.run_button.clicked.connect(self._on_run_button_clicked)
        
        # 连接切换按钮事件（如果存在）
        if hasattr(self.task_info, 'switch_button'):
            self.task_info.switch_button.clicked.connect(self._on_switch_button_clicked)

        # 连接服务协调器的信号，用于更新按钮状态
        self.service_coordinator.fs_signals.fs_start_button_status.connect(
            self._on_button_status_changed
        )
        
        # 多开模式：监听配置切换信号
        self.service_coordinator.signal_bus.config_changed.connect(
            self._on_config_switched
        )
        
        # 初始化当前配置
        self._current_config_id = self.service_coordinator.current_config_id
        self.start_bar.set_current_config(self._current_config_id)
        
        # 多开模式：初始化日志组件的当前配置
        if hasattr(self, 'log_output_widget') and hasattr(self.log_output_widget, 'set_current_config'):
            self.log_output_widget.set_current_config(self._current_config_id)

    def _on_config_switched(self, config_id: str):
        """配置切换时的处理
        
        多开模式：切换配置后更新按钮状态、日志和监控显示
        """
        logger.debug(f"配置切换: {self._current_config_id} -> {config_id}")
        old_config_id = self._current_config_id
        self._current_config_id = config_id
        
        # 更新开始按钮状态
        self.start_bar.set_current_config(config_id)
        
        # 检查新配置是否正在运行
        is_running = self.service_coordinator.is_running(config_id)
        self.start_bar.set_config_running(config_id, is_running)
        
        # 更新任务列表的编辑状态
        self._set_task_list_editable(not is_running)
        
        # 多开模式：切换日志显示
        self._switch_log_for_config(config_id)
        
        # 多开模式：切换监控显示
        self._switch_monitor_for_config(config_id, is_running)

    def _switch_log_for_config(self, config_id: str):
        """切换日志显示为指定配置
        
        多开模式：保存当前日志，加载目标配置日志
        """
        if not hasattr(self, 'log_output_widget'):
            return
        
        if hasattr(self.log_output_widget, 'switch_config'):
            self.log_output_widget.switch_config(config_id)

    def _switch_monitor_for_config(self, config_id: str, is_running: bool):
        """切换监控显示为指定配置
        
        多开模式：
        - 如果配置正在运行，切换到该配置的运行器
        - 如果配置未运行，停止监控并清空画面
        """
        if not hasattr(self, 'log_output_widget'):
            return
        
        monitor_widget = getattr(self.log_output_widget, 'monitor_widget', None)
        if monitor_widget is None:
            return
        
        if is_running:
            # 配置正在运行，切换监控到该配置的运行器
            try:
                runner = self.service_coordinator.get_runner(config_id)
                if hasattr(monitor_widget, 'set_target_runner'):
                    monitor_widget.set_target_runner(runner, config_id)
                    logger.debug(f"监控已切换到配置 {config_id} 的运行器")
            except Exception as e:
                logger.warning(f"切换监控目标运行器失败: {e}")
        else:
            # 配置未运行，设置目标配置（监控会自动清空）
            if hasattr(monitor_widget, 'set_target_config'):
                monitor_widget.set_target_config(config_id)
                logger.debug(f"监控已设置目标配置 {config_id}（未运行）")

    def _on_start_button_clicked(self):
        """处理开始按钮点击事件"""
        # 启动任务流（使用当前配置）
        asyncio.create_task(self.service_coordinator.run_tasks_flow())

    def _on_stop_button_clicked(self):
        """处理停止按钮点击事件"""
        # 停止任务流（使用当前配置）
        asyncio.create_task(self.service_coordinator.stop_task_flow())

    def _on_run_button_clicked(self):
        """处理启动/停止按钮点击事件
        
        多开模式：操作当前选中的配置
        """
        config_id = self._current_config_id
        is_running = self.service_coordinator.is_running(config_id)
        
        if not is_running:
            # 开始任务
            self.start_bar.run_button.setDisabled(True)
            QApplication.processEvents()

            # 检查当前是否为特殊任务模式
            is_special_mode = (
                hasattr(self.task_info, '_task_filter_mode') 
                and self.task_info._task_filter_mode == "special"
            )
            
            if is_special_mode:
                # 特殊任务模式
                self.log_output_widget.clear_log()
                target_task = self._get_selected_special_task()
                if not target_task:
                    from app.common.signal_bus import signalBus
                    signalBus.info_bar_requested.emit(
                        "warning", self.tr("Please select a special task to run.")
                    )
                    self.start_bar.run_button.setEnabled(True)
                    return

                # 同步内存态
                try:
                    for task in self.service_coordinator.task.get_tasks():
                        if task.is_special:
                            task.is_checked = task.item_id == target_task.item_id
                except Exception:
                    pass

                def _start_special_task():
                    asyncio.create_task(
                        self.service_coordinator.run_tasks_flow(
                            config_id=config_id,
                            task_id=target_task.item_id
                        )
                    )
                QTimer.singleShot(0, _start_special_task)
            else:
                # 普通任务模式
                def _start_task():
                    self.log_output_widget.clear_log()
                    asyncio.create_task(
                        self.service_coordinator.run_tasks_flow(config_id=config_id)
                    )
                QTimer.singleShot(0, _start_task)
        else:
            # 停止任务
            self.start_bar.run_button.setDisabled(True)
            QApplication.processEvents()

            def _stop_task():
                asyncio.create_task(
                    self.service_coordinator.stop_task_flow(config_id=config_id)
                )
            QTimer.singleShot(0, _stop_task)

    def _on_button_status_changed(self, status):
        """处理按钮状态变化信号
        
        多开模式：只更新当前配置的按钮状态
        """
        # 获取信号携带的配置ID（如果有）
        config_id = status.get("config_id", self._current_config_id)
        
        # 更新运行状态
        is_running = status.get("text") == "STOP"
        self.start_bar.set_config_running(config_id, is_running)
        
        # 只有当前配置的状态变更才更新UI
        if config_id == self._current_config_id:
            if is_running:
                self.start_bar.run_button.setText(self.tr("Stop"))
                self.start_bar.run_button.setIcon(FIF.CLOSE)
                self._set_task_list_editable(False)
            else:
                self.start_bar.run_button.setText(self.tr("Start"))
                self.start_bar.run_button.setIcon(FIF.PLAY)
                self._set_task_list_editable(True)

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
                if not widget.task.is_base_task():
                    widget.checkbox.setEnabled(enabled)
            # 禁用/启用删除按钮
            if hasattr(widget, 'setting_button') and hasattr(widget, 'task'):
                if not widget.task.is_base_task():
                    widget.setting_button.setEnabled(enabled)
    
    def showEvent(self, event: QShowEvent):
        """界面显示时自动选中第0个任务"""
        super().showEvent(event)
        
        # 同步当前配置ID
        self._current_config_id = self.service_coordinator.current_config_id
        self.start_bar.set_current_config(self._current_config_id)
        
        # 检查当前配置是否在运行
        is_running = self.service_coordinator.is_running(self._current_config_id)
        self.start_bar.set_config_running(self._current_config_id, is_running)
        
        def _reset_ui():
            self.option_panel.reset()
            if hasattr(self, 'task_info') and hasattr(self.task_info, 'task_list'):
                task_list = self.task_info.task_list
                if hasattr(task_list, '_filter_mode') and task_list._filter_mode != "special":
                    if self.service_coordinator and hasattr(self.service_coordinator, 'option'):
                        option_service = self.service_coordinator.option
                        if hasattr(option_service, 'clear_selection'):
                            option_service.clear_selection()
                    task_list.setCurrentRow(-1)
                    task_list.update()
        QTimer.singleShot(50, _reset_ui)
    
    def _on_switch_button_clicked(self):
        """处理切换按钮点击事件"""
        try:
            if hasattr(self.task_info, 'switch_filter_mode'):
                self.task_info.switch_filter_mode()
                logger.info(f"已切换任务列表过滤模式为: {self.task_info._task_filter_mode}")
                if hasattr(self, 'option_panel'):
                    self.option_panel.reset()
        except Exception as exc:
            logger.error(f"切换任务列表过滤模式失败: {exc}", exc_info=True)
    
    def _get_selected_special_task(self):
        """从特殊任务列表中获取当前选中的任务"""
        task_list_widget = getattr(self.task_info, "task_list", None)
        if not task_list_widget:
            return None
        try:
            for row in range(task_list_widget.count()):
                item = task_list_widget.item(row)
                widget = task_list_widget.itemWidget(item)
                if isinstance(widget, type(None)):
                    continue
                task = getattr(widget, "task", None)
                if task and task.is_special and task.is_checked:
                    return task
        except Exception:
            pass
        return None
