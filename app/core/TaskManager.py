import signal
from PySide6.QtCore import QObject, Signal, Property, Slot
from dataclasses import dataclass
from typing import List, Dict
from ..common.config import cfg
from ..utils.tool import Read_Config
from ..core.ConfigManager import TaskItem, ConfigManager


class TaskManager(QObject):
    """任务数据模型，管理所有任务数据"""

    tasks_changed = Signal()  # 任务列表变化信号
    save_task_list = Signal()

    def __init__(self, config_manager: ConfigManager):

        super().__init__()
        self.__task_list: List[TaskItem] = config_manager.curr_config.get("task", [])
        self.__config = config_manager.curr_config
        self.save_task_list.connect(config_manager.update_task_list)

        self.load__task_list()

    @Property(list)
    def task_list(self) -> list[TaskItem]:
        return self.__task_list

    @task_list.setter
    def task_list_setter(self, task_list: List[TaskItem]):
        self.__task_list = task_list
        self.tasks_changed.emit()

    def add_task(self, task: TaskItem):
        """添加任务"""
        self.__task_list.append(task)
        # 保存到配置文件
        self.save_task_list.emit(self.__task_list)

    def remove_task(self, task_id: str):
        """删除任务"""
        self.__task_list = [
            task for task in self.__task_list if task.task_id != task_id
        ]
        # 保存到配置文件
        self.save_task_list.emit(self.__task_list)

    def update_task_status(self, task_id: str, is_checked: bool):
        """更新任务状态"""
        for task in self.__task_list:
            if task.task_id == task_id:
                task.is_checked = is_checked
                break
        print(f"更新任务状态：{task_id}，{is_checked}")
        self.save_task_list.emit(self.__task_list)

    @Slot(list)
    def onTaskOrderChanged(self, new_order):
        # 根据新顺序重新排列任务数据
        self.__task_list = [self.get_task_by_id(id) for id in new_order]
        print(f"更新任务顺序：{new_order}")
        # 保存到配置文件
        self.save_task_list.emit(self.__task_list)

    # 随机生成task_id
    @staticmethod
    def generate_task_id() -> str:
        """随机生成任务id"""
        import random
        import string

        return "".join(random.choices(string.ascii_letters + string.digits, k=10))

    def load__task_list(self):
        """从配置文件加载任务"""
        config = self.__config

        for item in config.get("task", []):

            self.__task_list.append(item)

        self.tasks_changed.emit()

    def get_task_by_id(self, task_id: str) -> TaskItem:
        """根据任务id获取任务数据"""
        for task in self.__task_list:
            if task.task_id == task_id:
                return task
        raise ValueError(f"Task with id {task_id} not found")
