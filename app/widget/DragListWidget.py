from asyncio import new_event_loop
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


class DragListWidget(ListWidget):
    order_changed = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)

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

    def get_checkbox_text_order(self):
        """获取所有复选框的文本顺序"""
        text_order = []
        for i in range(self.count()):
            list_item = self.item(i)
            if not list_item:
                continue

            item_widget: TaskListItem = self.itemWidget(list_item)  # type: ignore
            if hasattr(item_widget, "checkbox"):
                text_order.append(item_widget.config)
                item_widget.checkbox.isPressed = False
                item_widget.checkbox.isHover = False
                item_widget.checkbox.update()

        return text_order

    def select_all(self):
        """全选所有复选框"""
        self.toggle_all_checkboxes(True)

    def deselect_all(self):
        """取消全选所有复选框"""
        self.toggle_all_checkboxes(False)

    def on_item_changed(self):
        """列表项状态改变时触发"""
        self.order_changed.emit(self.get_checkbox_text_order())

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
            print("无法移动控制器")
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
        self.on_item_changed()
