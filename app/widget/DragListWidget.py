from PySide6.QtWidgets import QApplication, QListWidgetItem, QAbstractItemView

from PySide6.QtCore import Qt, Signal, QPoint, QMimeData, QThread

from PySide6.QtGui import (
    QDragEnterEvent,
    QDropEvent,
    QDragMoveEvent,
    QDrag,
    QPixmap,
    QPainter,
    QColor,
    QCursor,
    QMouseEvent,
)


from qfluentwidgets import ListWidget
from .TaskWidgetItem import TaskListItem
from ..core.TaskManager import TaskManager, TaskItem


class DragListWidget(ListWidget):
    task_order_changed = Signal(list)
    checkbox_state_changed = Signal(str, bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.task_manager: TaskManager | None = None  


    def set_task_manager(self, task_manager: TaskManager):
        """设置任务流对象并连接信号槽"""
        if self.task_manager is None:
            self.task_manager = task_manager
            self.task_order_changed.connect(self.task_manager.onTaskOrderChanged)
            self.task_manager.tasks_changed.connect(self.update_task_list)
        else:
            print("任务流对象已存在，不重复设置")


    def update_task_list(self):
        print("列表更新")
        """从模型更新任务列表UI"""
        if self.task_manager is None:
            print("任务流对象未设置，无法更新任务列表")
            return

        self.clear()
        task_list: list[TaskItem] = self.task_manager.task_list  # type: ignore

        for task in task_list:  # type: ignore
            print(f"创建任务项:{task.get('task_id')}")

            list_item = QListWidgetItem()
            task_widget = TaskListItem()
            if task.get("task_id") in ["resource_task","controller_task"]:
                task_widget.checkbox.setChecked(True)
                task_widget.checkbox.setDisabled(True)
                #设置不可拖动
                list_item.setFlags(list_item.flags() & ~Qt.ItemFlag.ItemIsDragEnabled)

            task_widget.set_task_info(task.get("task_id"), task.get("name"), task.get("is_checked"))
            # 连接UI操作到模型更新
            task_widget.checkbox_state_changed.connect(self.task_manager.update_task_status)

            self.addItem(list_item)
            self.setItemWidget(list_item, task_widget)


    def toggle_all_checkboxes(self, checked):
        """批量设置所有项的复选框状态
        Args:
            checked: True表示全选, False表示取消全选
        """
        for i in range(self.count()):
            list_item = self.item(i)
            if not list_item:
                continue

            # 获取列表项对应的widget实例
            item_widget: TaskListItem = self.itemWidget(list_item)  # type: ignore

            if hasattr(item_widget, "checkbox"):
                item_widget.checkbox.setChecked(checked)

    def select_all(self):
        """全选所有复选框"""
        self.toggle_all_checkboxes(True)

    def deselect_all(self):
        """取消全选所有复选框"""
        self.toggle_all_checkboxes(False)

    def startDrag(self, supportedActions):
        # 获取当前选中的项
        index = self.currentIndex()
        if not index.isValid():
            return

        item = self.itemFromIndex(index)
        # 检查项是否允许拖动（通过标志判断）
        if not (item.flags() & Qt.ItemFlag.ItemIsDragEnabled):
            return

        # 调用父类方法执行拖动
        super().startDrag(supportedActions)

    def dropEvent(self, event: QDropEvent) -> None:
        drop_pos = event.pos()
        target_item = self.itemAt(drop_pos)

        # 检查目标项是否为不可拖动项，如果是则调整放置位置到其下方

        if target_item and not (target_item.flags() & Qt.ItemFlag.ItemIsDragEnabled):

            return

        super().dropEvent(event)
        drop_pos = event.pos()
        target_item = self.itemAt(drop_pos)
        if target_item:
            # 获取目标项的视觉矩形
            item_rect = self.visualItemRect(target_item)
            # 计算矩形中点的y坐标
            mid_y = item_rect.top() + item_rect.height() / 2
            new_row = self.row(target_item)
            # 根据鼠标位置判断是上半部分还是下半部分
            if drop_pos.y() > mid_y:
                new_row += 1  # 下半部分，插入到目标项下方
            self.setCurrentRow(new_row)
        task_list = []
        for i in range(self.count()):
            item = self.item(i)
            tem_widget: TaskListItem = self.itemWidget(item)  # type: ignore
            task_list.append(tem_widget.item_id)
        print(task_list)
        self.task_order_changed.emit(task_list)
