from PySide6.QtWidgets import  QVBoxLayout,QWidget
from PySide6.QtCore import Qt
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QDragMoveEvent


from qfluentwidgets import ScrollArea
from .TaskWidgetItem import TaskWidgetItem




class DragListWidget(ScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: transparent; border: none;")

        self.content_widget = QWidget()
        self.setWidget(self.content_widget)
        
        self.main_layout = QVBoxLayout(self.content_widget)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.setWidgetResizable(True)
        self.setAcceptDrops(True)
        

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasText() and event.source() is not None:
            event.acceptProposedAction()

    def dragMoveEvent(self, event:QDragMoveEvent):
        if event.mimeData().hasText():
            event.setDropAction(Qt.DropAction.MoveAction)
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        if event.mimeData().hasText():
            # 获取拖动源部件
            source_widget = event.source()
            if not source_widget or not isinstance(source_widget, TaskWidgetItem):
                return

            # 计算目标位置
            target_index = self._get_drop_index(event.pos())
            print(f"目标位置: {target_index}")

            if 0 <= target_index <= self.main_layout.count():
                self.main_layout.removeWidget(source_widget)
                self.main_layout.insertWidget(target_index, source_widget)
                print(f"选中的任务对象: {source_widget.text}, 放置的序号: {target_index}")
                event.acceptProposedAction()

                pos = event.pos()
                print(f"目标位置 x: {pos.x()}, y: {pos.y()}")

    def _get_drop_index(self, pos):
        mapped_pos = self.content_widget.mapFrom(self, pos)
        
        for i in range(self.main_layout.count()):
            item = self.main_layout.itemAt(i)
            widget = item.widget()
            if widget:
                # 检查鼠标位置是否在部件范围内
                if widget.geometry().contains(mapped_pos):
                    print("鼠标位置在部件范围内")

                    # 根据鼠标在部件中的垂直位置决定插入索引
                    if mapped_pos.y() < widget.geometry().center().y():
                        print("放在上方")
                        return i
                    else:
                        print("放在下方")
                        if i + 1 >= self.main_layout.count():
                            return i
                        return i + 1
        # 收集所有组件的索引和Y坐标
        components = []
        for i in range(self.main_layout.count()):
            item = self.main_layout.itemAt(i)
            widget = item.widget()
            if widget:
                components.append( (i, widget.geometry().y()) )
        
        # 按Y坐标排序组件
        components.sort(key=lambda x: x[1])
        
        insert_index = self.main_layout.count()  # 默认插入到末尾
        mouse_y = mapped_pos.y()
        
        for i, y in components:
            if mouse_y < y:
                # 鼠标在当前组件上方，插入到当前组件之前
                insert_index = i
                break
            else:
                # 鼠标在当前组件下方，继续检查下一个组件
                if i + 1 >= self.main_layout.count():
                    return i

                insert_index = i + 1
        
        print(f"空白区域插入索引: {insert_index}")
        return insert_index