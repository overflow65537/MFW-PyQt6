from typing import Any

from qfluentwidgets import ListWidget, RoundMenu, Action, MenuAnimationType
from qfluentwidgets import FluentIcon as FIF
from ..utils.tool import (
    Get_Values_list_Option,
    Save_Config,
    Get_Values_list2,
)
from PyQt6.QtCore import Qt
from ..common.signal_bus import signalBus
from ..common.maa_config_data import maa_config_data


class ListWidge_Menu_Draggable(ListWidget):
    def __init__(self, parent=None):
        super(ListWidge_Menu_Draggable, self).__init__(parent)

    def get_task_list_widget(self) -> list[Any]:
        items = []
        for i in range(self.count()):
            item = self.item(i)
            if item is not None:
                items.append(item.text())
        return items

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.RightButton:
            item = self.itemAt(e.pos())
            if item:
                self.setCurrentItem(item)
        super(ListWidge_Menu_Draggable, self).mousePressEvent(e)

    def contextMenuEvent(self, e):  # type: ignore
        menu = RoundMenu(parent=self)

        selected_row = self.currentRow()

        action_move_up = Action(FIF.UP, self.tr("Move Up"))
        action_move_down = Action(FIF.DOWN, self.tr("Move Down"))
        action_delete = Action(FIF.DELETE, self.tr("Delete"))

        if selected_row == -1:
            action_move_up.setEnabled(False)
            action_move_down.setEnabled(False)
            action_delete.setEnabled(False)

        action_move_up.triggered.connect(self.Move_Up)
        action_move_down.triggered.connect(self.Move_Down)
        action_delete.triggered.connect(self.Delete_Task)

        menu.addAction(action_move_up)
        menu.addAction(action_move_down)
        menu.addAction(action_delete)

        menu.exec(e.globalPos(), aniType=MenuAnimationType.DROP_DOWN)

    def Delete_Task(self):
        Select_Target = self.currentRow()

        if Select_Target == -1:
            return

        self.takeItem(Select_Target)
        Task_List = Get_Values_list2(maa_config_data.config_path, "task")

        # 只有在有效索引时更新任务配置
        if 0 <= Select_Target < len(Task_List):
            del Task_List[Select_Target]
            self.update_task_config(Task_List)

        self.update_selection(Select_Target)

        signalBus.update_task_list.emit()

    def Move_Up(self):
        Select_Target = self.currentRow()
        self.move_task(Select_Target, Select_Target - 1)

    def Move_Down(self):
        Select_Target = self.currentRow()
        self.move_task(Select_Target, Select_Target + 1)

    def move_task(self, from_index, to_index):
        if (
            from_index < 0
            or from_index >= self.count()
            or to_index < 0
            or to_index >= self.count()
        ):
            return  # 索引无效，直接返回

        # 执行移动操作
        Select_Task = maa_config_data.config["task"].pop(from_index)
        maa_config_data.config["task"].insert(to_index, Select_Task)
        Save_Config(maa_config_data.config_path, maa_config_data.config)

        self.clear()
        self.addItems(Get_Values_list_Option(maa_config_data.config_path, "task"))
        self.setCurrentRow(to_index)

        signalBus.update_task_list.emit()

    def update_task_config(self, Task_List):
        maa_config_data.config["task"] = Task_List
        Save_Config(maa_config_data.config_path, maa_config_data.config)

    def update_selection(self, Select_Target):
        if Select_Target == 0 and self.count() > 0:
            self.setCurrentRow(Select_Target)
        elif Select_Target != -1 and self.count() > 1:
            self.setCurrentRow(Select_Target - 1)

    def dropEvent(self, event):
        begin = self.currentRow()
        super(ListWidge_Menu_Draggable, self).dropEvent(event)
        end = self.currentRow()
        need_to_move = maa_config_data.config["task"].pop(begin)
        maa_config_data.config["task"].insert(end, need_to_move)
        Save_Config(maa_config_data.config_path, maa_config_data.config)

        signalBus.update_task_list.emit()
        self.setCurrentRow(end)
        signalBus.dragging_finished.emit()
