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
    order_changed = Signal()

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

    def select_all(self):
        """全选所有复选框"""
        self.toggle_all_checkboxes(True)

    def deselect_all(self):
        """取消全选所有复选框"""
        self.toggle_all_checkboxes(False)
