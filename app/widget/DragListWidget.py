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
from .ListItem import ListItem
from ..core.ItemManager import TaskManager,ConfigManager, TaskItem,ConfigItem





class BaseDragListWidget(ListWidget):
    item_order_changed = Signal(list)
    checkbox_state_changed = Signal(str, bool)

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
            item_widget: ListItem = self.itemWidget(list_item)  # type: ignore

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
        item_list = []
        for i in range(self.count()):
            item = self.item(i)
            tem_widget: ListItem = self.itemWidget(item)  # type: ignore
            item_list.append(tem_widget.item_id)
        print(item_list)
        self.item_order_changed.emit(item_list)

    def update_list(self):
        """从模型更新任务列表UI"""
        pass


class TaskDragListWidget(BaseDragListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.task_manager: TaskManager | None = None  


    def set_task_manager(self, task_manager: TaskManager):
        """设置任务流对象并连接信号槽"""
        if self.task_manager is None:
            self.task_manager = task_manager
            self.item_order_changed.connect(self.task_manager.onItemOrderChanged)
            self.task_manager.items_changed.connect(self.update_list)
        else:
            print("任务流对象已存在，不重复设置")


    def update_list(self):
        print("列表更新")
        """从模型更新任务列表UI"""
        if self.task_manager is None:
            print("任务流对象未设置，无法更新任务列表")
            return

        self.clear()
        task_list: list[TaskItem] = self.task_manager.item_list  # type: ignore

        for task in task_list:  # type: ignore
            print(f"创建任务项:{task.get('item_id')}")

            list_item = QListWidgetItem()
            task_widget = ListItem()
            if task.get("item_id") in ["resource_task","controller_task"]:
                task_widget.checkbox.setChecked(True)
                task_widget.checkbox.setDisabled(True)
                #设置不可拖动
                list_item.setFlags(list_item.flags() & ~Qt.ItemFlag.ItemIsDragEnabled)

            task_widget.set_task_info(task.get("item_id"), task.get("name"), task.get("is_checked"))
            # 连接UI操作到模型更新
            task_widget.checkbox_state_changed.connect(self.task_manager.update_item_status)

            self.addItem(list_item)
            self.setItemWidget(list_item, task_widget)


class ConfigDragListWidget(BaseDragListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.config_manager: ConfigManager | None = None  

    def set_config_manager(self, config_manager: ConfigManager):
        """设置配置流对象并连接信号槽"""
        if self.config_manager is None:
            self.config_manager = config_manager
            self.item_order_changed.connect(self.config_manager.onItemOrderChanged)
            self.config_manager.items_changed.connect(self.update_list)

        else:
            print("配置流对象已存在，不重复设置")
    def update_list(self):
        """从模型更新配置列表UI"""
        if self.config_manager is None:
            print("配置流对象未设置，无法更新配置列表")
            return
        self.clear()
        config_list: list[ConfigItem] = self.config_manager.item_list  # type: ignore

        for config in config_list:  # type: ignore
            print(f"创建任务项:{config.get('item_id')}")

            list_item = QListWidgetItem()
            config_widget = ListItem()

            config_widget.set_task_info(config.get("item_id"), config.get("name"), config.get("is_checked"))
            # 连接UI操作到模型更新
            
            config_widget.checkbox_state_changed.connect(self.config_manager.update_item_status)

            self.addItem(list_item)
            self.setItemWidget(list_item, config_widget)
