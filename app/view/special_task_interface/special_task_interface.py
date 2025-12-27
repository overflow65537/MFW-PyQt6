import asyncio

from PySide6.QtCore import QMetaObject, QCoreApplication, QTimer
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QWidget
from PySide6.QtGui import QShowEvent
from qfluentwidgets import FluentIcon as FIF

from app.core.core import ServiceCoordinator
from app.common.config import cfg
from app.common.signal_bus import signalBus
from app.view.task_interface.components.LogoutputWidget import LogoutputWidget
from app.view.task_interface.components.ListToolBarWidget import TaskListToolBarWidget
from app.view.task_interface.components.OptionWidget import OptionWidget
from app.view.task_interface.components.StartBarWidget import StartBarWidget


class UI_SpecialTaskInterface(object):
    def __init__(self, service_coordinator: ServiceCoordinator, parent=None):
        self.service_coordinator = service_coordinator
        self.parent = parent

    def setupUi(self, SpecialTaskInterface):
        SpecialTaskInterface.setObjectName("SpecialTaskInterface")
        # 主窗口
        self.main_layout = QHBoxLayout()
        self.log_output_widget = LogoutputWidget()

        self._init_control_panel()
        self._init_option_panel()

        self.main_layout.addWidget(self.control_panel)
        self.main_layout.addWidget(self.option_panel_widget)
        self.main_layout.addWidget(self.log_output_widget)
        self.main_layout.setStretch(0, 1)
        self.main_layout.setStretch(1, 1)
        self.main_layout.setStretch(2, 99)

        SpecialTaskInterface.setLayout(self.main_layout)
        self.retranslateUi(SpecialTaskInterface)
        QMetaObject.connectSlotsByName(SpecialTaskInterface)

    def _init_option_panel(self):
        """初始化选项面板"""
        self.option_panel_widget = QWidget()
        self.option_panel_layout = QVBoxLayout(self.option_panel_widget)
        self.option_panel = OptionWidget(service_coordinator=self.service_coordinator)
        self.option_panel.setFixedWidth(344)
        self.option_panel_layout.addWidget(self.option_panel)

    def _init_control_panel(self):
        """初始化控制面板"""
        self.task_info = TaskListToolBarWidget(
            service_coordinator=self.service_coordinator,
            task_filter_mode="special",
        )
        self.task_info.setFixedWidth(344)

        self.start_bar = StartBarWidget()
        self.start_bar.setFixedWidth(344)

        # 控制面板布局
        self.control_panel = QWidget()
        self.control_panel_layout = QVBoxLayout(self.control_panel)

        self.control_panel_layout.addWidget(self.task_info)
        self.control_panel_layout.addWidget(self.start_bar)

        # 设置比例
        self.control_panel_layout.setStretch(0, 10)
        self.control_panel_layout.setStretch(1, 1)

    def retranslateUi(self, SpecialTaskInterface):
        _translate = QCoreApplication.translate
        SpecialTaskInterface.setWindowTitle(_translate("SpecialTaskInterface", "Form"))


class SpecialTaskInterface(UI_SpecialTaskInterface, QWidget):
    def __init__(self, service_coordinator=None, parent=None):
        QWidget.__init__(self, parent=parent)
        UI_SpecialTaskInterface.__init__(
            self, service_coordinator=service_coordinator, parent=parent
        )
        self.setupUi(self)
        self.service_coordinator = service_coordinator

        self.task_info.set_title(self.tr("Special Tasks"))
        # 连接启动/停止按钮事件
        self.start_bar.run_button.clicked.connect(self._on_run_button_clicked)

        # 连接服务协调器的信号，用于更新按钮状态
        self.service_coordinator.fs_signals.fs_start_button_status.connect(
            self._on_button_status_changed
        )

    def _on_run_button_clicked(self):
        """处理启动/停止按钮点击事件"""
        if self.start_bar.run_button.text() == self.tr("Start"):
            self.log_output_widget.clear_log()
            target_task = self._get_selected_special_task()
            if not target_task:
                signalBus.info_bar_requested.emit(
                    "warning", self.tr("Please select a special task to run.")
                )
                return

            # 同步内存态：确保服务层当前任务列表中只有该特殊任务被视为选中，但不落盘
            try:
                for task in self.service_coordinator.task.get_tasks():
                    if task.is_special:
                        task.is_checked = task.item_id == target_task.item_id
            except Exception:
                pass

            asyncio.create_task(
                self.service_coordinator.run_tasks_flow(task_id=target_task.item_id)
            )
        else:
            asyncio.create_task(self.service_coordinator.stop_task_flow())

    def _get_selected_special_task(self):
        """从特殊任务列表中获取当前选中的任务（仅内存态）。"""
        task_list_widget = getattr(self.task_info, "task_list", None)
        if not task_list_widget:
            return None
        try:
            for row in range(task_list_widget.count()):
                item = task_list_widget.item(row)
                widget = task_list_widget.itemWidget(item)
                if (
                    isinstance(widget, type(None))
                ):  # 防御性，避免 None
                    continue
                task = getattr(widget, "task", None)
                # 直接检查task.is_checked，不依赖checkbox的可见性
                if task and task.is_special and task.is_checked:
                    return task
        except Exception:
            pass
        return None

    def _on_button_status_changed(self, status):
        """处理按钮状态变化信号"""
        """状态格式: {"text": "STOP", "status": "disabled"}"""
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
        
        # 禁用/启用工具栏按钮（特殊任务界面可能隐藏了这些按钮，但为了安全还是设置）
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
            # 禁用/启用删除按钮
            if hasattr(widget, 'setting_button'):
                widget.setting_button.setEnabled(enabled)

    def showEvent(self, event: QShowEvent):
        """界面显示时自动选中第0个任务"""
        super().showEvent(event)
        # 使用定时器延迟执行，确保任务列表已经加载完成
        QTimer.singleShot(50, self._auto_select_first_task)

    def _auto_select_first_task(self):
        """自动选中第0个任务"""
        task_list_widget = getattr(self.task_info, "task_list", None)
        if not task_list_widget:
            return
        
        # 检查任务列表是否有任务，如果没有任务就跳过
        if task_list_widget.count() == 0:
            return
        
        try:
            # 获取第0个任务项
            first_item = task_list_widget.item(0)
            if not first_item:
                return
            
            widget = task_list_widget.itemWidget(first_item)
            if not widget:
                return
            
            # 检查是否是SpecialTaskListItem
            from app.view.task_interface.components.ListItem import SpecialTaskListItem
            if isinstance(widget, SpecialTaskListItem):
                # 如果任务未选中，则触发点击逻辑（相当于点击item）
                if not widget.task.is_checked:
                    widget._on_item_clicked()
                else:
                    # 如果已经选中，仍然切换到任务设置
                    if self.service_coordinator:
                        self.service_coordinator.select_task(widget.task.item_id)
                    widget._select_in_parent_list()
        except Exception:
            pass

