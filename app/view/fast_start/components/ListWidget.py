from PySide6.QtWidgets import (
    QListWidgetItem,
    QAbstractItemView,
    QGraphicsOpacityEffect,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QSizePolicy,
)
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve, QTimer, QSize
from qfluentwidgets import ListWidget, IndeterminateProgressRing, SimpleCardWidget

from app.core.core import  ServiceCoordinator
from app.core.Item import TaskItem, ConfigItem
from .ListItem import TaskListItem, ConfigListItem
from app.utils.logger import logger
from app.common.signal_bus import signalBus


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


class SkeletonBar(QWidget):
    """用于模拟骨架占位的矩形条"""

    def __init__(self, parent=None, height: int = 10):
        super().__init__(parent)
        self.setFixedHeight(height)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setStyleSheet(
            "background-color: rgba(255, 255, 255, 0.25); border-radius: 5px;"
        )


class TaskSkeletonWidget(SimpleCardWidget):
    """qfluentwidgets 风格的骨架占位器，用于在大量任务加载时缓解卡顿"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setBorderRadius(8)
        layout = QVBoxLayout(self)
        layout.setSpacing(6)
        layout.setContentsMargins(12, 12, 12, 12)

        layout.addWidget(SkeletonBar(self, height=12))
        layout.addWidget(SkeletonBar(self, height=12))


class TaskDragListWidget(BaseListWidget):
    """任务拖拽列表组件：支持拖动排序、添加、修改、删除任务（基础任务禁止删除/拖动）"""

    _TASK_ITEM_HEIGHT = 44

    def __init__(self, service_coordinator: ServiceCoordinator, parent=None):
        super().__init__(service_coordinator, parent)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)
        # 标记是否处于批量刷新阶段，用于保持服务端给出的顺序
        self._bulk_updating: bool = False

        self._fade_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._fade_effect)
        self._fade_effect.setOpacity(1.0)
        self._fade_out = QPropertyAnimation(self._fade_effect, b"opacity", self)
        self._fade_out.setDuration(80)
        self._fade_out.setStartValue(1.0)
        self._fade_out.setEndValue(0.0)
        self._fade_out.setEasingCurve(QEasingCurve.Type.InQuad)
        self._fade_in = QPropertyAnimation(self._fade_effect, b"opacity", self)
        self._fade_in.setDuration(100)
        self._fade_in.setStartValue(0.0)
        self._fade_in.setEndValue(1.0)
        self._fade_in.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._fade_out.finished.connect(self._on_fade_out_finished)
        self._fade_in.finished.connect(self._on_fade_in_finished)
        self._pending_refresh = False

        # 维护 task_id -> widget 的映射，避免重复遍历列表
        self._task_widgets: dict[str, TaskListItem] = {}
        self._skeleton_items: list[QListWidgetItem] = []
        self._pending_tasks: list[TaskItem] = []
        self._render_index: int = 0
        self._loading_tasks: bool = False

        self._init_loading_overlay()

        self.item_selected.connect(self._on_item_selected_to_service)
        self.service_coordinator.signal_bus.config_changed.connect(
            self._on_config_changed
        )
        service_coordinator.fs_signal_bus.fs_task_modified.connect(self.modify_task)
        service_coordinator.fs_signal_bus.fs_task_removed.connect(self.remove_task)
        self.update_list()

    def _on_item_selected_to_service(self, item_id: str):
        self.service_coordinator.select_task(item_id)

    def dropEvent(self, event):
        # 拖动前收集任务和保护位置
        previous_tasks = self._collect_task_items()
        protected = self._protected_positions(previous_tasks)

        # 获取拖动目标位置
        pos = event.pos()
        target_row = self.indexAt(pos).row()
        # 如果拖动目标是基础任务位置（如0/1/最后），直接放弃操作
        if target_row in protected:
            event.ignore()
            return

        super().dropEvent(event)
        current_tasks = self._collect_task_items()
        if not self._base_positions_intact(current_tasks, protected):
            self._restore_order([task.item_id for task in previous_tasks])
            event.ignore()
            return
        self.service_coordinator.reorder_tasks([task.item_id for task in current_tasks])

    def _on_config_changed(self, config_id: str) -> None:
        """Reload tasks when user switches configuration."""
        if self._fade_out.state() == QPropertyAnimation.State.Running:
            self._pending_refresh = True
            return
        if self._fade_in.state() == QPropertyAnimation.State.Running:
            self._fade_in.stop()
        self._pending_refresh = True
        self._show_loading_overlay()
        self._fade_out.start()

    def _on_fade_out_finished(self) -> None:
        if not self._pending_refresh:
            self._fade_in.start()
            return
        pending = self._pending_refresh
        self._pending_refresh = False

        if pending:
            self.update_list()
        self._fade_in.start()

    def _on_fade_in_finished(self) -> None:
        self._hide_loading_overlay()

    def update_list(self):
        """刷新任务列表UI（先显示骨架占位，再逐项渲染）"""
        self.clear()
        self.setCurrentRow(-1)
        self._task_widgets.clear()
        self._skeleton_items.clear()
        task_list = self.service_coordinator.task.get_tasks()
        self._pending_tasks = task_list
        self._render_index = 0
        self._loading_tasks = bool(task_list)
        self._add_task_skeletons(len(task_list))
        if self._pending_tasks:
            QTimer.singleShot(5, self._render_pending_task)
        else:
            self._loading_tasks = False

    def _add_task_skeletons(self, count: int):
        """根据任务数量先添加骨架占位，避免一次性渲染卡顿"""
        for _ in range(count):
            list_item = QListWidgetItem()
            list_item.setSizeHint(QSize(0, self._TASK_ITEM_HEIGHT))
            list_item.setFlags(Qt.ItemFlag.NoItemFlags)
            skeleton = TaskSkeletonWidget(self)
            self.addItem(list_item)
            self.setItemWidget(list_item, skeleton)
            self._skeleton_items.append(list_item)

    def _render_pending_task(self):
        """逐项替换骨架为真实任务组件，确保 UI 不被阻塞"""
        if self._render_index >= len(self._pending_tasks):
            self._loading_tasks = False
            self._pending_tasks = []
            return

        task = self._pending_tasks[self._render_index]
        self._render_task_at_index(self._render_index, task)
        self._render_index += 1
        QTimer.singleShot(5, self._render_pending_task)

    def _render_task_at_index(self, index: int, task: TaskItem):
        """将指定位置的骨架替换为实际的 `TaskListItem`"""
        interface = getattr(self.service_coordinator.task, "interface", None)
        if index < len(self._skeleton_items):
            list_item = self._skeleton_items[index]
        else:
            list_item = QListWidgetItem()
            list_item.setSizeHint(QSize(0, self._TASK_ITEM_HEIGHT))
            self.addItem(list_item)
            self._skeleton_items.append(list_item)

        placeholder = self.itemWidget(list_item)
        if isinstance(placeholder, TaskSkeletonWidget):
            placeholder.deleteLater()

        task_widget = TaskListItem(task, interface=interface)
        task_widget.checkbox_changed.connect(self._on_task_checkbox_changed)

        flags = Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled
        if not task.is_base_task():
            flags |= Qt.ItemFlag.ItemIsDragEnabled
        else:
            flags &= ~Qt.ItemFlag.ItemIsDragEnabled

        list_item.setFlags(flags)
        self.setItemWidget(list_item, task_widget)
        self._task_widgets[task.item_id] = task_widget

    def modify_task(self, task: TaskItem):
        """添加或更新任务项到列表（如果存在同 id 的任务则更新，否则新增）。"""
        # 获取 interface 配置
        interface = getattr(self.service_coordinator.task, "interface", None)
        # 先尝试查找是否已有同 id 的项，若有则进行更新
        existing_widget = self._task_widgets.get(task.item_id)
        if existing_widget:
            existing_widget.task = task
            existing_widget.interface = interface or {}
            existing_widget.name_label.setText(existing_widget._get_display_name())
            existing_widget.checkbox.setChecked(task.is_checked)
            return

        if self._loading_tasks:
            # 正在依次渲染骨架，不需要重复插入
            return

        # 否则按原有逻辑新增项
        list_item = QListWidgetItem()
        task_widget = TaskListItem(task, interface=interface)
        # 复选框状态变更信号
        task_widget.checkbox_changed.connect(self._on_task_checkbox_changed)
        # 基础任务禁止拖动
        if task.is_base_task():
            list_item.setFlags(list_item.flags() & ~Qt.ItemFlag.ItemIsDragEnabled)
        
        # 批量刷新时严格按传入顺序追加；单项新增时插入到倒数第二位
        if getattr(self, "_bulk_updating", False):
            self.addItem(list_item)
        else:
            # 插入到倒数第二位,确保"完成后操作"始终在最后
            insert_index = max(0, self.count() - 1)
            self.insertItem(insert_index, list_item)
        self.setItemWidget(list_item, task_widget)
        self._task_widgets[task.item_id] = task_widget

    def remove_task(self, task_id: str):
        """移除任务项，基础任务不可移除"""
        # 检查是否为基础任务
        for i in range(self.count()):
            item = self.item(i)
            widget = self.itemWidget(item)
            if isinstance(widget, TaskListItem) and widget.task.item_id == task_id:
                if widget.task.is_base_task():
                    # 基础任务不可删除，记录日志并显示提示
                    signalBus.info_bar_requested.emit(
                        "warning", "基础任务（资源、完成后操作）不可删除"
                    )
                    return
                self.takeItem(i)
                widget.deleteLater()
                self._task_widgets.pop(task_id, None)
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
        if not tasks:
            return {}
        positions = {0, 1, len(tasks) - 1}
        protected: dict[int, str] = {}
        for idx in positions:
            if 0 <= idx < len(tasks):
                task = tasks[idx]
                if task.is_base_task():
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

    def _init_loading_overlay(self) -> None:
        self._loading_overlay = QWidget(self)
        self._loading_overlay.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents
        )
        self._loading_overlay.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        self._loading_overlay.setStyleSheet(
            "background-color: rgba(0, 0, 0, 60); border-radius: 8px;"
        )
        layout = QHBoxLayout(self._loading_overlay)
        layout.setContentsMargins(24, 16, 24, 16)
        layout.setSpacing(0)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._loading_indicator = IndeterminateProgressRing(self._loading_overlay)
        self._loading_indicator.setFixedSize(28, 28)
        layout.addWidget(self._loading_indicator)

        self._loading_overlay.hide()

    def _show_loading_overlay(self) -> None:
        self._loading_overlay.setGeometry(self.viewport().geometry())
        self._loading_overlay.show()
        self._loading_indicator.start()

    def _hide_loading_overlay(self) -> None:
        self._loading_overlay.hide()
        self._loading_indicator.stop()

    def resizeEvent(self, e):
        super().resizeEvent(e)
        if hasattr(self, "_loading_overlay"):
            self._loading_overlay.setGeometry(self.viewport().geometry())

    def _on_task_checkbox_changed(self, task: TaskItem):
        """复选框状态变更信号转发"""
        if task.is_base_task():
            return
        self.service_coordinator.update_task_checked(task.item_id, task.is_checked)

    def select_all(self) -> None:
        """选择全部任务(排除基础任务和特殊任务)"""
        task_list = []
        for i in range(self.count()):
            item = self.item(i)
            widget = self.itemWidget(item)
            if isinstance(widget, TaskListItem):
                # 排除基础任务和特殊任务
                if not widget.task.is_base_task() and not widget.task.is_special:
                    widget.checkbox.setChecked(True)
                    widget.task.is_checked = True
                    task_list.append(widget.task)
        self.service_coordinator.modify_tasks(task_list)

    def deselect_all(self) -> None:
        """取消选择全部任务(排除基础任务,但包含特殊任务)"""
        task_list = []
        for i in range(self.count()):
            item = self.item(i)
            widget = self.itemWidget(item)
            if isinstance(widget, TaskListItem):
                # 只排除基础任务
                if not widget.task.is_base_task():
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
        
        # 选中当前配置
        current_config_id = self.service_coordinator.config.current_config_id
        if current_config_id:
            self._select_config_by_id(current_config_id)

    def _add_config_to_list(self, config: ConfigItem):
        """添加单个配置项到列表"""
        list_item = QListWidgetItem()
        config_widget = ConfigListItem(config)
        self.addItem(list_item)
        self.setItemWidget(list_item, config_widget)

    def _select_config_by_id(self, config_id: str):
        """根据配置ID选中对应的列表项"""
        for i in range(self.count()):
            item = self.item(i)
            widget = self.itemWidget(item)
            if isinstance(widget, ConfigListItem) and widget.item.item_id == config_id:
                self.setCurrentRow(i)
                # 直接触发 config_changed 信号以更新任务列表标题
                self.service_coordinator.signal_bus.config_changed.emit(config_id)
                break

    def add_config(self, config: ConfigItem):
        """添加配置项到列表"""
        self._add_config_to_list(config)
        # 新增时尝试选中它，保持UI当前配置与服务一致
        self._select_config_by_id(config.item_id)

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
