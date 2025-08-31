from abc import ABC
from logging import config
from PySide6.QtCore import QObject, Signal, Property, Slot
from dataclasses import dataclass
from typing import List, Dict
from typing import Dict, List, TypedDict, Optional, Any
from pathlib import Path
import json
from PySide6.QtCore import QObject


class TaskItem(TypedDict, total=True):
    name: str
    item_id: str
    is_checked: bool
    task_option: dict
    task_type: str


class ConfigItem(TypedDict, total=True):
    name: str
    item_id: str
    is_checked: bool
    task: List[TaskItem]
    gpu: int
    finish_option: int
    know_task: list


class MultiConfig(TypedDict, total=True):
    curr_config_id: str
    config_list: list[ConfigItem]


class BaseItemManaget(QObject):

    items_changed = Signal()  # 元素列表变化信号
    save_item_list = Signal(list)  # 保存元素列表信号

    def __init__(self) -> None:
        super().__init__()
        self._item_list: List = []

    @property
    def item_list(self) -> List:
        """获取元素列表"""
        return self._item_list

    def add_item(self, item) -> None:
        """添加任务"""
        self._item_list.append(item)
        # 保存到配置文件
        self.save_item_list.emit(self._item_list)

    def remove_item(self, item_id: str):
        """删除任务"""
        self._item_list = [
            item for item in self._item_list if item.get("item_id") != item_id
        ]
        # 保存到配置文件
        self.save_item_list.emit(self._item_list)

    def update_item_status(self, item_id: str, is_checked: bool):
        """更新任务状态"""
        for item in self._item_list:
            if item.get("item_id") == item_id:
                item["is_checked"] = is_checked
                print(f"更新任务状态：{item_id}，{is_checked}")
                self.save_item_list.emit(self._item_list)
                return True
        raise ValueError(f"task with id {item_id} not found")

    @Slot(list)
    def onItemOrderChanged(self, new_order):
        # 根据新顺序重新排列元素数据
        print(f"接收新列表{new_order}")
        self._item_list = [self.get_item_by_id(id) for id in new_order]
        print(f"更新任务顺序：{new_order}")
        # 保存到配置文件
        self.save_item_list.emit(self._item_list)

    def get_item_by_id(self, item_id: str):
        """根据任务id获取任务数据"""
        for item in self._item_list:
            if item.get("item_id") == item_id:
                return item
        raise ValueError(f"task with id {item_id} not found")

    @staticmethod
    def generate_id() -> str:
        """随机生成id"""
        import random
        import string

        return "".join(random.choices(string.ascii_letters + string.digits, k=10))


class ConfigManager(BaseItemManaget):
    """配置数据模型，管理所有配置数据"""

    task_items_changed = Signal()

    def __init__(self, multi_config_path: Path | str):
        super().__init__()
        self.multi_config_path = Path(multi_config_path)

        self.load_config()
        self._item_list: list[ConfigItem] = self.__config["config_list"]

        self.__curr_config_id = self.__config["curr_config_id"]

        self.__curr_config = self.get_item_by_id(self.__curr_config_id)
        self.save_item_list.connect(self.save_config)

    @property
    def curr_config_id(self) -> str:
        return self.__curr_config_id

    @curr_config_id.setter
    def curr_config_id(self, value: str):
        self.__curr_config_id = value
        self.__curr_config = self.get_item_by_id(value)
        self._item_list = self.__config["config_list"]
        self.task_items_changed.emit()

    @property
    def curr_config(self) -> ConfigItem:

        return self.__curr_config
    
    @curr_config.setter
    def curr_config(self, value: list[TaskItem]):
        self.__curr_config["task"] = value
        #self.task_items_changed.emit()
    
    def save_list(self, item_list: list[TaskItem]):
        self.curr_config = item_list
        self.save_config()

    @Slot(list)
    def onItemOrderChanged(self, new_order):
        # 根据新顺序重新排列元素数据
        print(f"接收新列表{new_order}")
        self._item_list = [self.get_item_by_id(id) for id in new_order]
        print(f"更新任务顺序：{new_order}")
        # 保存到配置文件
        self.__config["config_list"] = self._item_list
        self.save_config()

    def load_config(self) -> None:
        """加载配置文件，初始化多配置字典"""
        if not self.multi_config_path.exists():
            empty_config = self.create_empty_config()
            self.__config: MultiConfig = {
                "curr_config_id": empty_config["item_id"],
                "config_list": [empty_config],
            }
            self.save_config()

            return

        try:
            with open(self.multi_config_path, "r", encoding="utf-8") as f:

                self.__config: MultiConfig = json.load(f)
                if not self.__config or not self.__config.get("config_list"):
                    raise ValueError("配置数据无效")
        except Exception as e:
            print(f"加载配置失败：{e}")
            empty_config = self.create_empty_config()
            self.__config: MultiConfig = {
                "curr_config_id": empty_config["item_id"],
                "config_list": [empty_config],
            }
            self.save_config()


    def save_config(self) -> None:
        """保存主配置文件"""
        try:
            print(f"保存配置：{self.__curr_config['name']}")
        except Exception as e:
            print(f"新建配置")

        try:
            with open(self.multi_config_path, "w", encoding="utf-8") as f:
                json.dump(self.__config, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"保存配置失败：{e}")

    def create_empty_config(self) -> ConfigItem:
        resource_task: TaskItem = {
            "name": "资源",
            "item_id": "resource_task",
            "is_checked": True,
            "task_option": {},
            "task_type": "resource",
        }
        controller_task: TaskItem = {
            "name": "控制器",
            "item_id": "controller_task",
            "is_checked": True,
            "task_option": {},
            "task_type": "controller",
        }
        """创建一个空配置"""
        empty_config: ConfigItem = {
            "name": "新配置",
            "item_id": self.generate_id(),
            "is_checked": True,
            "task": [resource_task, controller_task],
            "gpu": -1,
            "finish_option": 0,
            "know_task": [],
        }
        return empty_config

    def get_item_by_id(self, item_id: str):
        """根据任务id获取任务数据"""
        for item in self._item_list:
            if item.get("item_id") == item_id:
                return item
        raise ValueError(f"task with id {item_id} not found")


class TaskManager(BaseItemManaget):
    """任务数据模型，管理所有任务数据"""

    def __init__(self, config_manager: ConfigManager):

        super().__init__()
        self.config_manager = config_manager
        self.__config = config_manager.curr_config
        self._item_list: List[TaskItem] = self.__config.get("task", [])
        self.save_item_list.connect(config_manager.save_list)
        self.config_manager.task_items_changed.connect(self.update_item)

    def get_item_by_id(self, item_id: str):
        """根据任务id获取任务数据"""
        for item in self._item_list:
            if item.get("item_id") == item_id:
                return item
        raise ValueError(f"task with id {item_id} not found")

    def update_item(self):
        print("更新任务")
        self.__config = self.config_manager.curr_config
        self._item_list: List[TaskItem] = self.__config.get("task", [])
        self.items_changed.emit()
