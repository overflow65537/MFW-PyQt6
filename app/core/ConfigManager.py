from typing import Dict, List, Self, TypedDict, Optional, Any
from pathlib import Path
from dataclasses import dataclass, asdict
import json


from PySide6.QtCore import QObject, Signal, Property, Slot
from funkify import T


class TaskItem(TypedDict, total=True):
    name: str
    task_id: str
    is_checked: bool
    task_option: dict
    task_type: str


class Config(TypedDict, total=True):
    is_enabled: bool
    task: List[TaskItem]
    gpu: int
    finish_option: int
    run_before_start: str
    run_before_start_args: str
    run_after_finish: str
    run_after_finish_args: str
    emu_path: str
    emu_args: str
    emu_wait_time: int
    exe_path: str
    exe_args: str
    exe_wait_time: int
    know_task: list
    start_time: str


class MultiConfig(TypedDict, total=True):
    curr_config_name: str
    config_data: dict[str, Config]


class ConfigManager(QObject):
    """配置数据模型，管理所有配置数据"""

    def __init__(self, multi_config_path: Path | str):
        super().__init__()
        self.multi_config_path = Path(multi_config_path)

        self.load_config()

        self.__curr_config_name: str = self.__config.get("curr_config_name", "")

        self.__config_data: dict[str, Config] = self.__config.get("config_data", {})

        __curr_config = self.__config_data.get(self.__curr_config_name)
        if not __curr_config:
            raise ValueError("当前配置不存在")
        self.__curr_config = __curr_config
        self.__task_list: List[TaskItem] = self.__curr_config.get("task", [])

    @property
    def curr_config_name(self) -> str:
        return self.__curr_config_name

    @curr_config_name.setter
    def curr_config_name(self, config_name: str) -> None:
        if config_name not in self.__config_data:
            self.__config_data[config_name] = self.create_empty_config()

        self.__curr_config_name = config_name
        self.__curr_config = self.__config_data[config_name]
        self.__task_list = self.__curr_config.get("task", [])
        self.save_config()

    @property
    def curr_config(self) -> Config:
        return self.__curr_config

    @curr_config.setter
    def set_curr_config(self, config: Config) -> None:
        self.__curr_config = config
        self.__task_list = self.__curr_config.get("task", [])
        self.save_config()

    def load_config(self) -> None:
        """加载配置文件，初始化多配置字典"""
        if not self.multi_config_path.exists():
            self.__config: MultiConfig = {
                "curr_config_name": "default",
                "config_data": {"default": self.create_empty_config()},
            }
            self.save_config()

            return

        try:
            with open(self.multi_config_path, "r", encoding="utf-8") as f:

                self.__config: MultiConfig = json.load(f)
                if not self.__config or not self.__config.get("config_data"):
                    raise ValueError("配置数据无效")
        except Exception as e:
            print(f"加载配置失败：{e}")
            self.__config: MultiConfig = {
                "curr_config_name": "default",
                "config_data": {"default": self.create_empty_config()},
            }
            self.save_config()

    def save_config(self) -> None:
        """保存主配置文件"""
        print(f"保存配置：{self.__curr_config_name}")

        try:
            with open(self.multi_config_path, "w", encoding="utf-8") as f:
                json.dump(self.__config, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"保存配置失败：{e}")

    def get_config(self, config_name: str) -> Config:
        """获取指定名称的子配置（不存在则返回空字典）"""
        return self.__config["config_data"][config_name]

    def set_config(self, config_name: str, config_data: Config) -> None:
        """添加或更新子配置，并自动保存主配置"""
        self.__config["config_data"][config_name] = config_data
        self.save_config()

    def change_config(self, config_name: str) -> None:
        """切换当前配置"""
        self.__curr_config_name = config_name
        self.__curr_config = self.__config_data[config_name]
        self.__task_list = self.__curr_config.get("task", [])

        self.save_config()

    def update_task_list(self, task_list: List[TaskItem]) -> None:
        self.__task_list = task_list
        self.__curr_config["task"] = self.__task_list
        self.save_config()

    # 生成一份空配置
    def create_empty_config(self) -> Config:
        resource_task: TaskItem = {
            "name": "资源",
            "task_id": "resource_task",
            "is_checked": True,
            "task_option": {},
            "task_type": "resource",
        }
        controller_task: TaskItem = {
            "name": "控制器",
            "task_id": "controller_task",
            "is_checked": True,
            "task_option": {},
            "task_type": "controller",
        }
        """创建一个空配置"""
        empty_config: Config = {
            "is_enabled": True,
            "task": [resource_task, controller_task],
            "gpu": -1,
            "finish_option": 0,
            "run_before_start": "",
            "run_before_start_args": "",
            "run_after_finish": "",
            "run_after_finish_args": "",
            "emu_path": "",
            "emu_args": "",
            "emu_wait_time": 5,
            "exe_path": "",
            "exe_args": "",
            "exe_wait_time": 5,
            "know_task": [],
            "start_time": "",
        }
        return empty_config
