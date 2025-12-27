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

        self.task_info.set_title(self.tr("Task Information"))
        self.config_selection.set_title(self.tr("Configuration Selection"))

        # 连接启动/停止按钮事件
        self.start_bar.run_button.clicked.connect(self._on_run_button_clicked)

        # 连接服务协调器的信号，用于更新按钮状态
        self.service_coordinator.fs_signals.fs_start_button_status.connect(
            self._on_button_status_changed
        )

        self._timeout_restarting = False
        self._timeout_restart_entry = None
        self._timeout_restart_attempts = 0

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
        asyncio.create_task(self.service_coordinator.stop_task_flow())

    def _on_run_button_clicked(self):
        """处理启动/停止按钮点击事件"""
        # 检查按钮当前状态并执行相应操作
        if self.start_bar.run_button.text() == self.tr("Start"):
            # 立即禁用按钮
            self.start_bar.run_button.setDisabled(True)
            # 强制处理UI事件，确保按钮状态立即更新
            QApplication.processEvents()

            self._timeout_restarting = False
            self._timeout_restart_entry = None
            self._timeout_restart_attempts = 0
            # 清除超时重启状态（正常启动时）
            self._clear_timeout_restart_state()

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
            # 如果正在等待重启且按钮已启用，触发重启
            if self._timeout_restarting and status.get("status") == "enabled":
                QTimer.singleShot(100, lambda: self._trigger_restart_if_ready())
            elif status.get("status") == "enabled" and not self._timeout_restarting:
                # 如果不是超时重启且按钮已启用（任务正常完成），清除状态
                self._clear_timeout_restart_state()
                self._timeout_restart_entry = None
                self._timeout_restart_attempts = 0

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
            # 禁用/启用 checkbox
            if hasattr(widget, 'checkbox'):
                widget.checkbox.setEnabled(enabled)
            # 禁用/启用删除按钮
            if hasattr(widget, 'setting_button'):
                widget.setting_button.setEnabled(enabled)

    def _on_timeout_restart_requested(self, entry: str, attempts: int):
        """处理任务超时需要重启的请求

        Args:
            entry: 超时的任务entry
            attempts: 当前重启次数
        """
        self._timeout_restart_entry = entry
        self._timeout_restart_attempts = attempts
        # 保存状态到配置
        self._save_timeout_restart_state(entry, attempts)
        self._timeout_restarting = True
        self.restart_tasks_via_button()

    def _trigger_restart_if_ready(self):
        """如果按钮已准备好，触发重启。"""
        button = self.start_bar.run_button
        if button.text() == self.tr("Start") and button.isEnabled():
            # 超时重启，恢复状态并传递给 run_tasks_flow
            entry = self._timeout_restart_entry
            attempts = self._timeout_restart_attempts
            # 如果内存中没有状态，从配置中恢复
            if not entry or attempts == 0:
                entry, attempts = self._restore_timeout_restart_state()

            self._timeout_restarting = False  # 清除标志，准备启动
            asyncio.create_task(
                self._run_timeout_restart_flow(entry, attempts)
            )

    async def _run_timeout_restart_flow(self, entry: str | None, attempts: int) -> None:
        """根据配置执行超时重启流程。

        - 直接重启：保持现有行为，仅执行超时重启任务流；
        - 运行最后一项任务后重启：先运行列表中最后一项启用的普通任务，再执行超时重启任务流。

        “最后一项任务”定义为：
        - 不属于基础任务（_RESOURCE_ / _CONTROLLER_ / POST_ACTION）；
        - 不是特殊任务（task.is_special 为 False）；
        - 勾选状态为 True（task.is_checked 为 True）。
        """
        if not self.service_coordinator:
            return

        # 读取重启模式配置
        try:
            mode_value = cfg.get(cfg.task_timeout_restart_mode)
            restart_mode = Config.TaskTimeoutRestartMode(mode_value)
        except Exception:
            # 配置缺失或非法时，退回为“直接重启”
            restart_mode = Config.TaskTimeoutRestartMode.DIRECT_RESTART

        # 如果是“运行最后一项任务后重启”模式，先尝试执行最后一项任务
        if restart_mode == Config.TaskTimeoutRestartMode.RUN_LAST_ENTRY_THEN_RESTART:
            try:
                last_task = self._find_last_normal_checked_task()
                if last_task is not None:
                    logger.info(
                        f"超时重启模式: 先执行列表中最后一项任务再重启 -> {last_task.name}"
                    )
                    await self.service_coordinator.run_tasks_flow(
                        task_id=last_task.item_id
                    )
                else:
                    logger.info(
                        "超时重启模式为“运行最后一项任务后重启”，但未找到符合条件的任务，直接进入重启流程"
                    )
            except Exception as exc:
                logger.warning(f"执行最后一项任务失败，将直接进入重启流程: {exc}")

        # 执行原有的超时重启任务流
        await self.service_coordinator.run_tasks_flow(
            is_timeout_restart=True,
            timeout_restart_entry=entry,
            timeout_restart_attempts=attempts,
        )

    def _find_last_normal_checked_task(self):
        """查找当前任务列表中“最后一项启用的普通任务”。

        普通任务定义：
        - 不是基础任务（名称不为 _RESOURCE_ / _CONTROLLER_ / POST_ACTION）；
        - 不是特殊任务（is_special 为 False）；
        - 被勾选（is_checked 为 True）。
        """
        try:
            task_service = getattr(self.service_coordinator, "task", None)
            if not task_service:
                return None

            # 获取当前配置下的任务顺序，与任务流中的执行顺序保持一致
            tasks = list(task_service.current_tasks)
            if not tasks:
                # 兼容性兜底：某些版本可能没有 current_tasks 属性
                tasks = list(task_service.get_tasks())

            from app.core.runner.task_flow import _RESOURCE_, _CONTROLLER_, POST_ACTION

            last_task = None
            for task in tasks:
                # 跳过基础任务
                if task.name in [_RESOURCE_, _CONTROLLER_, POST_ACTION]:
                    continue
                # 跳过未勾选的任务
                if not getattr(task, "is_checked", False):
                    continue
                # 跳过特殊任务
                if getattr(task, "is_special", False):
                    continue

                last_task = task

            return last_task
        except Exception as exc:
            logger.warning(f"查找最后一项任务失败: {exc}")
            return None

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

    def _save_timeout_restart_state(self, entry: str, attempts: int):
        """保存超时重启状态到配置"""
        if not self.service_coordinator:
            return
        try:
            config_service = self.service_coordinator.config_service
            if config_service:
                success = config_service.save_timeout_restart_state(entry, attempts)
                if success:
                    logger.debug(
                        f"已保存超时重启状态: entry={entry}, attempts={attempts}"
                    )
                else:
                    logger.warning(
                        f"保存超时重启状态失败: entry={entry}, attempts={attempts}"
                    )
        except Exception as exc:
            logger.warning(f"保存超时重启状态时出错: {exc}")

    def _restore_timeout_restart_state(self) -> tuple[str | None, int]:
        """从配置中恢复超时重启状态

        Returns:
            (entry, attempts) 元组，如果配置中没有状态则返回 (None, 0)
        """
        if not self.service_coordinator:
            return None, 0
        try:
            config_service = self.service_coordinator.config_service
            if config_service:
                saved_state = config_service.get_timeout_restart_state()
                if saved_state:
                    # 如果有多个entry，选择次数最多的（通常是当前正在处理的）
                    max_entry = max(saved_state.items(), key=lambda x: x[1])
                    if max_entry:
                        entry, attempts = max_entry
                        logger.info(
                            f"从配置恢复超时重启状态: entry={entry}, attempts={attempts}"
                        )
                        return entry, attempts
            return None, 0
        except Exception as exc:
            logger.warning(f"恢复超时重启状态时出错: {exc}")
            return None, 0

    def _clear_timeout_restart_state(self, entry: str | None = None):
        """清除超时重启状态"""
        if not self.service_coordinator:
            return
        try:
            config_service = self.service_coordinator.config_service
            if config_service:
                config_service.clear_timeout_restart_state(entry)
                logger.debug(f"已清除超时重启状态: entry={entry or 'all'}")
        except Exception as exc:
            logger.warning(f"清除超时重启状态时出错: {exc}")

    def showEvent(self, event: QShowEvent):
        """界面显示时自动选中第0个任务"""
        super().showEvent(event)
        # 使用定时器延迟执行，确保任务列表已经加载完成
        def _reset_ui():
            # 清除选项面板
            self.option_panel.reset()
            # 清除普通任务列表的选中状态（特殊任务列表保持原样）
            if hasattr(self, 'task_info') and hasattr(self.task_info, 'task_list'):
                task_list = self.task_info.task_list
                # 只对普通任务列表清除选中状态
                if hasattr(task_list, '_filter_mode') and task_list._filter_mode != "special":
                    # 先清除选项服务的状态，避免状态不一致
                    if self.service_coordinator and hasattr(self.service_coordinator, 'option'):
                        option_service = self.service_coordinator.option
                        if hasattr(option_service, 'clear_selection'):
                            option_service.clear_selection()
                    # 使用 setCurrentRow(-1) 完全清除选中状态
                    # 这会触发 currentItemChanged 信号（current 为 None），确保状态完全清除
                    task_list.setCurrentRow(-1)
                    # 强制更新UI，确保选中状态完全清除
                    task_list.update()
        QTimer.singleShot(50, _reset_ui)
