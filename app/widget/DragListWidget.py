
from typing import Dict, Any, List
from PySide6.QtWidgets import QApplication, QListWidgetItem, QAbstractItemView
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDropEvent, QDragEnterEvent, QDragMoveEvent

from qfluentwidgets import ListWidget
from ..core.core import TaskItem, ConfigItem, CoreSignalBus, ServiceCoordinator
from .ListItem import BaseListItem, TaskListItem, ConfigListItem


class BaseDragListWidget(ListWidget):
    """基础可拖拽列表组件 - 提供通用的拖拽功能"""

    item_order_changed = Signal(list)  # 列表项顺序变更信号
    item_selected = Signal(str)  # 列表项选择信号

    def __init__(self, service_coordinator: ServiceCoordinator, parent=None):
        super().__init__(parent)
        self.service_coordinator = service_coordinator
        self.signal_bus: CoreSignalBus = service_coordinator.signal_bus

        # 设置拖拽相关属性
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)

        # 连接信号
        self.currentItemChanged.connect(self._on_item_selected)
        self.item_order_changed.connect(self._on_order_changed)

    def dropEvent(self, event: QDropEvent) -> None:
        """处理拖放事件，并发出顺序变更信号"""
        # 保存原始选择状态
        current_item = self.currentItem()

        # 执行默认的拖放操作
        super().dropEvent(event)

        # 收集所有项并发出顺序变更信号
        self._emit_order_changed_signal()

        # 恢复选择状态
        if current_item and self.findItems(
            current_item.text(), Qt.MatchFlag.MatchExactly
        ):
            self.setCurrentItem(current_item)

    def _emit_order_changed_signal(self):
        """收集所有项并发出顺序变更信号"""
        item_list = []
        for i in range(self.count()):
            item = self.item(i)
            widget = self.itemWidget(item)

            # 根据widget类型获取对应的数据项
            if isinstance(widget, TaskListItem):
                item_list.append(widget.task)
            elif isinstance(widget, ConfigListItem):
                item_list.append(widget.config)

        self.item_order_changed.emit(item_list)

    def _on_item_selected(self, current, previous):
        """当选中项变化时的处理"""
        if current:
            widget = self.itemWidget(current)
            if widget and isinstance(widget, (TaskListItem, ConfigListItem)):
                self.item_selected.emit(widget.item_id)

    def _on_order_changed(self, item_list):
        """当列表项顺序变化时的处理（子类可以重写）"""
        pass

    def select_item(self, item_id: str):
        """选择指定ID的项"""
        for i in range(self.count()):
            item = self.item(i)
            if not item:
                continue

            widget = self.itemWidget(item)
            if (
                widget
                and isinstance(widget, (TaskListItem, ConfigListItem))
                and widget.item_id == item_id
            ):
                self.setCurrentItem(item)
                break

    def clear(self):
        """清空列表"""
        while self.count() > 0:
            item = self.takeItem(0)
            widget = self.itemWidget(item)
            if widget:
                widget.deleteLater()
            del item


class TaskDragListWidget(BaseDragListWidget):
    """任务拖拽列表组件 - 专门用于显示和管理TaskItem，包含复选框逻辑"""

    def __init__(self, service_coordinator: ServiceCoordinator, parent=None):
        super().__init__(service_coordinator, parent)
        # 连接任务相关信号
        self.signal_bus.task_created.connect(self.add_task)
        self.signal_bus.task_deleted.connect(self.remove_task)
        self.signal_bus.task_updated.connect(self.update_task)

        # 初始化列表
        self.update_list()

    def update_list(self):
        """从服务协调器更新任务列表UI"""
        self.clear()
        task_list = self.service_coordinator.task.get_tasks()

        for task in task_list:
            self._add_task_to_list(task)

    def _add_task_to_list(self, task: TaskItem):
        """将单个任务添加到列表中"""
        list_item = QListWidgetItem()
        task_widget = TaskListItem(task, self.signal_bus)

        # 连接任务项的信号
        task_widget.checkbox.stateChanged.connect(
            lambda state, t=task: self._on_task_checkbox_changed(t.item_id, state)
        )

        # 根据任务类型设置特殊属性
        if task.task_type in ["resource", "controller", "finish"]:
            list_item.setFlags(list_item.flags() & ~Qt.ItemFlag.ItemIsDragEnabled)
        if task.task_type == "resource":
            # 资源在第一位
            self.insertItem(0, list_item)
        elif task.task_type == "controller":
            # 控制器在第二位
            self.insertItem(1, list_item)
        elif task.task_type == "finish":
            # finish在最后
            self.insertItem(self.count() - 1, list_item)
        else:
            # task和其他插入倒数第二个位置
            self.insertItem(self.count() - 2, list_item)

        self.setItemWidget(list_item, task_widget)

    def add_task(self, task: TaskItem):
        """添加任务项"""
        self._add_task_to_list(task)

    def remove_task(self, task_id: str):
        """移除任务项"""
        for i in range(self.count()):
            item = self.item(i)
            widget = self.itemWidget(item)
            if isinstance(widget, TaskListItem) and widget.task.item_id == task_id:
                self.takeItem(i)
                widget.deleteLater()
                break

    def update_task(self, task: TaskItem):
        """更新任务项"""
        for i in range(self.count()):
            item = self.item(i)
            widget = self.itemWidget(item)
            if isinstance(widget, TaskListItem) and widget.task.item_id == task.item_id:
                # 更新现有任务信息
                widget.task = task
                widget.name_label.setText(task.name)
                widget.checkbox.setChecked(task.is_checked)
                return

    def _on_task_checkbox_changed(self, task_id: str, state):
        """处理任务复选框状态变化"""
        is_checked = state == Qt.CheckState.Checked
        self.signal_bus.toggle_task_check.emit(task_id, is_checked)

    def _on_order_changed(self, item_list: list[TaskItem]):
        """当任务顺序变化时，更新服务协调器中的任务顺序"""
        self.service_coordinator.task.reorder_tasks(
            [task.item_id for task in item_list]
        )

    def toggle_all_checkboxes(self, checked):
        """批量设置所有任务项的复选框状态"""
        for i in range(self.count()):
            list_item = self.item(i)
            if not list_item:
                continue

            # 获取列表项对应的widget实例
            item_widget = self.itemWidget(list_item)
            if isinstance(item_widget, TaskListItem):
                # 检查是否为不可修改的项
                if item_widget.task.task_type in [
                    "controller",
                    "resource",
                    "finish",
                ]:
                    continue

                item_widget.checkbox.setChecked(checked)
            else:
                continue

    def select_all(self):
        """全选所有任务复选框"""
        self.toggle_all_checkboxes(True)

    def deselect_all(self):
        """取消全选所有任务复选框"""
        self.toggle_all_checkboxes(False)


class ConfigDragListWidget(BaseDragListWidget):
    """配置拖拽列表组件 - 专门用于显示和管理ConfigItem，不包含复选框逻辑"""

    def __init__(self, service_coordinator: ServiceCoordinator, parent=None):
        super().__init__(service_coordinator, parent)

        # 连接配置相关信号
        self.signal_bus.config_created.connect(self.add_config)
        self.signal_bus.config_deleted.connect(self.remove_config)

        # 初始化列表
        self.update_list()

    def update_list(self):
        """从服务协调器更新配置列表UI"""
        self.clear()
        config_list = self.service_coordinator.config.list_configs()

        for config in config_list:
            self._add_config_to_list(config)

    def _add_config_to_list(self, config: ConfigItem):
        """将单个配置添加到列表中"""
        list_item = QListWidgetItem()
        config_widget = ConfigListItem(config, self.signal_bus)

        self.addItem(list_item)
        self.setItemWidget(list_item, config_widget)

    def add_config(self, config: ConfigItem):
        """添加配置项"""
        # 添加新配置到列表
        self._add_config_to_list(config)


    def remove_config(self, config_id: str):
        """移除配置项"""
        for i in range(self.count()):
            item = self.item(i)
            widget = self.itemWidget(item)
            if (
                isinstance(widget, ConfigListItem)
                and widget.config.item_id == config_id
            ):
                self.takeItem(i)
                widget.deleteLater()
                break

    def _on_order_changed(self, item_list: list[ConfigItem]):
        """当配置顺序变化时，更新服务协调器中的配置顺序"""
        self.service_coordinator.config.reorder_configs(item_list)

    def set_current_config(self, config_id: str):
        """设置当前配置项"""
        self.select_item(config_id)
