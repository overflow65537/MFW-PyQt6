from tokenize import Special
from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import QWidget, QStackedWidget, QVBoxLayout, QLabel

from qfluentwidgets import SegmentedWidget,Pivot

from typing import List, Dict, Any, TypedDict, Optional

from ..common.config import cfg
from ..common.signal_bus import signalBus

from ..utils.logger import logger
from ..common.maa_config_data import maa_config_data

class ContinuousTaskInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("Continuous_Task_Interface")
        # 主窗口

        """self.pivot = Pivot(self)
        self.stackedWidget = QStackedWidget(self)
        self.Layout = QVBoxLayout(self)

        self.script_list: List =[]

        self.Layout.addWidget(self.pivot, 0, Qt.AlignmentFlag.AlignHCenter)
        self.Layout.addWidget(self.stackedWidget)
        self.Layout.setContentsMargins(0, 0, 0, 0)


        self.pivot.currentItemChanged.connect(
            lambda index: self.switch_SettingBox(
                int(index[3:]), if_chang_pivot=False
            )
        )

        self.show_SettingBox(1)"""
#    def get_task_list(self) -> List[str]:
#        """获取任务列表"""
#
#        task_list = []
#        for task in maa_config_data.interface_config.get("task", []):
#            if task == "Special":
#                task_list.append(task)
#        return task_list
#    
#    def show_SettingBox(self, index) -> None:
#        """加载所有子界面"""
#        task_list = self.get_task_list()
#        for name, info in task_list:
#            self.add_MaaSettingBox(int(name[3:]))
#
#        self.switch_SettingBox(index)
#
#    def switch_SettingBox(self, index: int, if_chang_pivot: bool = True) -> None:
#        """切换到指定的子界面"""
#
#        if len(maa_config_data.interface_config.get("task", [])) == 0:
#            return None
#
#        elif index > len(maa_config_data.interface_config.get("task", [])):
#            return None
#
#        if if_chang_pivot:
#            self.pivot.setCurrentItem(self.script_list[index - 1].objectName())
#        self.stackedWidget.setCurrentWidget(self.script_list[index - 1])
#        self.script_list[index - 1].user_setting.user_manager.switch_SettingBox(
#            "用户仪表盘"
#        )
#
#    
#    def add_MaaSettingBox(self, task:str,pipeline_override:dict) -> None:
#        """添加一个MAA设置界面"""
#
#        maa_setting_box = self.ScriptSettingBox(task,pipeline_override, self)
#
#        self.script_list.append(maa_setting_box)
#
#        self.stackedWidget.addWidget(self.script_list[-1])
#
#        self.pivot.addItem(routeKey=f"脚本_{task}", text=f"脚本 {task}")
#
#    class ScriptSettingBox(QWidget):
#        """特殊脚本设置界面"""
#
#        def __init__(self, task:str,pipeline_override:dict, parent=None):
#            super().__init__(parent)
#
#            self.setObjectName(f"脚本_{task},{pipeline_override}")
#            self.Layout = QVBoxLayout(self)
#            self.Layout.setContentsMargins(0, 0, 0, 0)
#            laybel1 = QLabel(self)
#            laybel1.setText(f"脚本_{task},{pipeline_override}")
#
#            self.Layout.addWidget(laybel1)