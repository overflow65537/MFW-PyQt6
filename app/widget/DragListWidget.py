from PySide6.QtWidgets import QListWidgetItem, QAbstractItemView
from PySide6.QtCore import Qt, Signal
from qfluentwidgets import ListWidget
from ..core.core import TaskItem, ConfigItem, CoreSignalBus, ServiceCoordinator
from .ListItem import TaskListItem, ConfigListItem

class BaseDragListWidget(ListWidget):
    """基础可拖拽列表组件，所有子类通用拖拽功能"""
    item_order_changed = Signal(list)  # 列表项顺序变更信号
    item_selected = Signal(str)        # 列表项选择信号

    def __init__(self, service_coordinator: ServiceCoordinator, parent=None):
        super().__init__(parent)
        self.service_coordinator = service_coordinator
        self.signal_bus: CoreSignalBus = service_coordinator.signal_bus
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.currentItemChanged.connect(self._on_item_selected)
        self.item_order_changed.connect(self._on_order_changed)

    def _on_item_selected(self, current, previous):
        """选中项变化时发出 item_id 信号"""
        if current:
            widget = self.itemWidget(current)
            if widget and hasattr(widget, 'item_id'):
                self.item_selected.emit(widget.item_id)

    def _on_order_changed(self, item_list):
        """拖拽顺序变更时，子类实现同步逻辑"""
        pass

class TaskDragListWidget(BaseDragListWidget):
    """任务拖拽列表组件：支持拖动排序、添加、修改、删除任务（基础任务禁止删除/拖动）"""
    def update_list(self):
        """刷新任务列表UI"""
        self.clear()
        task_list = self.service_coordinator.task.get_tasks()
        for task in task_list:
            self.add_task(task)

    def add_task(self, task: TaskItem):
        """添加任务项到列表"""
        list_item = QListWidgetItem()
        task_widget = TaskListItem(task, self.signal_bus)
        # 复选框状态变更信号
        task_widget.checkbox.stateChanged.connect(
            lambda state, t=task: self._on_task_checkbox_changed(t.item_id, state)
        )
        # 基础任务禁止拖动
        if task.item_id.startswith(("c_", "r_", "f_")):
            list_item.setFlags(list_item.flags() & ~Qt.ItemFlag.ItemIsDragEnabled)
        self.addItem(list_item)
        self.setItemWidget(list_item, task_widget)

    def change_task(self, task: TaskItem):
        """根据 item_id 修改任务内容"""
        for i in range(self.count()):
            item = self.item(i)
            widget = self.itemWidget(item)
            if isinstance(widget, TaskListItem) and widget.task.item_id == task.item_id:
                widget.task = task
                widget.name_label.setText(task.name)
                widget.checkbox.setChecked(task.is_checked)
                break

    def remove_task(self, task_id: str):
        """移除任务项，基础任务不可移除"""
        if task_id.startswith(("c_", "r_", "f_")):
            return
        for i in range(self.count()):
            item = self.item(i)
            widget = self.itemWidget(item)
            if isinstance(widget, TaskListItem) and widget.task.item_id == task_id:
                self.takeItem(i)
                widget.deleteLater()
                break

    def _on_order_changed(self, item_list: list[TaskItem]):
        """拖拽顺序变更时同步到服务层"""
        self.service_coordinator.task.reorder_tasks([task.item_id for task in item_list])

    def _on_task_checkbox_changed(self, task_id: str, state):
        """复选框状态变更信号转发"""
        is_checked = state == Qt.CheckState.Checked
        self.signal_bus.toggle_task_check.emit(task_id, is_checked)

class ConfigDragListWidget(BaseDragListWidget):
    """配置拖拽列表组件：只支持添加/删除配置项，无复选框"""
    def update_list(self):
        """刷新配置列表UI"""
        self.clear()
        config_list = self.service_coordinator.config.list_configs()
        for config in config_list:
            self._add_config_to_list(config)

    def _add_config_to_list(self, config: ConfigItem):
        """添加单个配置项到列表"""
        list_item = QListWidgetItem()
        config_widget = ConfigListItem(config, self.signal_bus)
        self.addItem(list_item)
        self.setItemWidget(list_item, config_widget)

    def add_config(self, config: ConfigItem):
        """添加配置项到列表"""
        self._add_config_to_list(config)

    def remove_config(self, config_id: str):
        """移除配置项"""
        for i in range(self.count()):
            item = self.item(i)
            widget = self.itemWidget(item)
            if isinstance(widget, ConfigListItem) and widget.config.item_id == config_id:
                self.takeItem(i)
                widget.deleteLater()
                break

    def _on_order_changed(self, item_list: list[ConfigItem]):
        """拖拽顺序变更时同步到服务层"""
        self.service_coordinator.config.reorder_configs(item_list)

    def set_current_config(self, config_id: str):
        """设置当前选中配置项"""
        self.select_item(config_id)