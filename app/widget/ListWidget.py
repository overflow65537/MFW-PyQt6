from PySide6.QtWidgets import QListWidgetItem, QAbstractItemView
from PySide6.QtCore import Qt, Signal
from qfluentwidgets import ListWidget
from ..core.core import TaskItem, ConfigItem, ServiceCoordinator
from .ListItem import TaskListItem, ConfigListItem


class BaseListWidget(ListWidget):
    """基础列表组件，所有子类通用拖拽功能"""

    item_selected = Signal(str)  # 列表项选择信号

    def __init__(self, service_coordinator: ServiceCoordinator, parent=None):
        super().__init__(parent)
        self.service_coordinator = service_coordinator
        self.currentItemChanged.connect(self._on_item_selected)

    def _on_item_selected(self, current, previous):
        """选中项变化时发出 item_id 信号"""
        if current:
            widget = self.itemWidget(current)
            if widget and isinstance(widget, (TaskListItem, ConfigListItem)):
                self.item_selected.emit(widget.item.item_id)

    def select_item(self, item_id: str):
        """在列表中查找并选中指定 item_id 的项（通用方法）"""
        for i in range(self.count()):
            li = self.item(i)
            widget = self.itemWidget(li)
            if (
                widget
                and isinstance(widget, (TaskListItem, ConfigListItem))
                and widget.item.item_id == item_id
            ):
                self.setCurrentItem(li)
                break


class TaskDragListWidget(BaseListWidget):
    """任务拖拽列表组件：支持拖动排序、添加、修改、删除任务（基础任务禁止删除/拖动）"""

    def __init__(self, service_coordinator: ServiceCoordinator, parent=None):
        super().__init__(service_coordinator, parent)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)

        self.item_selected.connect(self._on_item_selected_to_service)
        service_coordinator.fs_signal_bus.fs_task_modified.connect(self.modify_task)
        service_coordinator.fs_signal_bus.fs_task_removed.connect(self.remove_task)
        self.update_list()

    def _on_item_selected_to_service(self, item_id: str):
        self.service_coordinator.select_task(item_id)

    def dropEvent(self, event):
        previous_tasks = self._collect_task_items()
        protected = self._protected_positions(previous_tasks)
        super().dropEvent(event)
        current_tasks = self._collect_task_items()
        if not self._base_positions_intact(current_tasks, protected):
            self._restore_order([task.item_id for task in previous_tasks])
            event.ignore()
            return
        self.service_coordinator.reorder_tasks(
            [task.item_id for task in current_tasks]
        )

    def update_list(self):
        """刷新任务列表UI"""
        self.clear()
        task_list = self.service_coordinator.task.get_tasks()
        for task in task_list:
            self.modify_task(task)

    def modify_task(self, task: TaskItem):
        """添加或更新任务项到列表（如果存在同 id 的任务则更新，否则新增）。"""
        # 先尝试查找是否已有同 id 的项，若有则进行更新
        for i in range(self.count()):
            item = self.item(i)
            widget = self.itemWidget(item)
            if (
                isinstance(widget, TaskListItem)
                and getattr(widget, "task", None) is not None
            ):
                if widget.task.item_id == task.item_id:
                    # 更新已有 widget 的数据并返回
                    print(f"任务拖拽列表组件: 更新现有任务 {task.item_id} 为 is_checked={task.is_checked}")
                    widget.task = task
                    widget.name_label.setText(task.name)
                    widget.checkbox.setChecked(task.is_checked)
                    return

        # 否则按原有逻辑新增项
        list_item = QListWidgetItem()
        task_widget = TaskListItem(task)
        # 复选框状态变更信号
        task_widget.checkbox_changed.connect(self._on_task_checkbox_changed)
        # 基础任务禁止拖动
        if task.item_id.startswith(("c_", "r_", "f_")):
            list_item.setFlags(list_item.flags() & ~Qt.ItemFlag.ItemIsDragEnabled)
        self.addItem(list_item)
        self.setItemWidget(list_item, task_widget)

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

    def _collect_task_items(self) -> list[TaskItem]:
        """Collect TaskItem instances from current widgets for ordering checks."""
        tasks: list[TaskItem] = []
        for i in range(self.count()):
            item = self.item(i)
            widget = self.itemWidget(item)
            if isinstance(widget, TaskListItem):
                tasks.append(widget.task)
        return tasks

    def _protected_positions(self, tasks: list[TaskItem]) -> dict[int, str]:
        """Remember base task ids that must stay in reserved slots."""
        prefixes = ("c_", "r_", "f_")
        if not tasks:
            return {}
        positions = {0, 1, len(tasks) - 1}
        protected: dict[int, str] = {}
        for idx in positions:
            if 0 <= idx < len(tasks):
                task = tasks[idx]
                if task.item_id.startswith(prefixes):
                    protected[idx] = task.item_id
        return protected

    def _base_positions_intact(
        self, tasks: list[TaskItem], protected: dict[int, str]
    ) -> bool:
        """Verify base tasks in reserved slots keep their original ids."""
        for idx, expected_id in protected.items():
            if idx < 0 or idx >= len(tasks):
                return False
            if tasks[idx].item_id != expected_id:
                return False
        return True

    def _restore_order(self, order: list[str]) -> None:
        """Restore original order if a drop violates base task constraints."""
        for target_index, task_id in enumerate(order):
            current_index = self._find_row_by_task_id(task_id)
            if current_index == -1 or current_index == target_index:
                continue
            list_item = self.item(current_index)
            widget = self.itemWidget(list_item)
            list_item = self.takeItem(current_index)
            if list_item is None:
                continue
            self.insertItem(target_index, list_item)
            if widget is not None:
                self.setItemWidget(list_item, widget)

    def _find_row_by_task_id(self, task_id: str) -> int:
        for row in range(self.count()):
            widget = self.itemWidget(self.item(row))
            if isinstance(widget, TaskListItem) and widget.task.item_id == task_id:
                return row
        return -1

    def _on_task_checkbox_changed(self, task: TaskItem):
        """复选框状态变更信号转发"""
        print(f"任务拖拽列表组件: 收到复选框更改 {task.item_id}, is_checked={task.is_checked}")
        if task.item_id.startswith(("c_", "r_", "f_")):
            return
        self.service_coordinator.update_task_checked(task.item_id, task.is_checked)

    def select_all(self) -> None:
        """选择全部任务"""
        task_list = []
        for i in range(self.count()):
            item = self.item(i)
            widget = self.itemWidget(item)
            if isinstance(widget, TaskListItem):
                widget.checkbox.setChecked(True)
                widget.task.is_checked = True
                task_list.append(widget.task)
        self.service_coordinator.modify_tasks(task_list)

    def deselect_all(self) -> None:
        """取消选择全部任务"""
        task_list = []
        for i in range(self.count()):
            item = self.item(i)
            widget = self.itemWidget(item)
            if isinstance(widget, TaskListItem):
                if not widget.task.item_id.startswith(("c_", "r_", "f_")):
                    widget.checkbox.setChecked(False)
                    widget.task.is_checked = False
                task_list.append(widget.task)
        self.service_coordinator.modify_tasks(task_list)


class ConfigListWidget(BaseListWidget):
    """配置拖拽列表组件：只支持添加/删除配置项，无复选框"""

    def __init__(self, service_coordinator: ServiceCoordinator, parent=None):
        super().__init__(service_coordinator, parent)
        self.item_selected.connect(self._on_item_selected_to_service)

        self.service_coordinator.fs_signal_bus.fs_config_added.connect(self.add_config)
        self.service_coordinator.fs_signal_bus.fs_config_removed.connect(
            self.remove_config
        )
        self.update_list()

    def _on_item_selected_to_service(self, item_id: str):
        self.service_coordinator.select_config(item_id)

    def update_list(self):
        """刷新配置列表UI"""
        self.clear()
        config_summaries = self.service_coordinator.config.list_configs()
        for summary in config_summaries:
            config_id = (
                summary.get("item_id")
                if isinstance(summary, dict)
                else getattr(summary, "item_id", None)
            )
            if config_id:
                cfg = self.service_coordinator.config.get_config(config_id)
                if cfg:
                    self._add_config_to_list(cfg)

    def _add_config_to_list(self, config: ConfigItem):
        """添加单个配置项到列表"""
        list_item = QListWidgetItem()
        config_widget = ConfigListItem(config)
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
            if isinstance(widget, ConfigListItem) and widget.item.item_id == config_id:
                self.takeItem(i)
                widget.deleteLater()
                break

    def set_current_config(self, config_id: str):
        """设置当前选中配置项"""
        self.select_item(config_id)
