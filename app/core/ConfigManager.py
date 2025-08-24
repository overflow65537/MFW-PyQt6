from turtle import st
from typing import Dict, List, TypedDict, Optional, Any
from pathlib import Path
from dataclasses import dataclass
import json


from PySide6.QtCore import QObject, Signal, Property, Slot


@dataclass
class TaskItem:
    name: str
    task_id: str
    is_checked: bool
    task_option: dict
    task_type: str


@dataclass
class Config:
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


@dataclass
class MultiConfig:
    curr_config_name: str
    config_data: dict[str, Config]


class ConfigManager(QObject):
    """配置数据模型，管理所有配置数据"""

    def __init__(self, multi_config_path: Path | str):
        super().__init__()
        self.multi_config_path = Path(multi_config_path)

        self.load_config()

        self.__curr_config_name: str = self.__config.curr_config_name

        self.__config_data: dict[str, Config] = self.__config.config_data

        self.__curr_config = self.__config_data[self.__curr_config_name]
        self.__task_list: List[TaskItem] = []

        for item in self.__curr_config.task:
            self.__task_list.append(item)

    @property
    def curr_config_name(self) -> str:
        return self.__curr_config_name

    @curr_config_name.setter
    def curr_config_name(self, config_name: str) -> None:
        if config_name not in self.__config_data:
            self.__config_data[config_name] = self.create_empty_config()

        self.__curr_config_name = config_name
        self.__curr_config = self.__config_data[config_name]
        self.__task_list = []
        for item in self.__curr_config.task:
            self.__task_list.append(item)

        self.save_config()

    @property
    def curr_config(self) -> Config:
        return self.__curr_config

    @curr_config.setter
    def set_curr_config(self, config: Config) -> None:
        self.__curr_config = config
        self.__task_list = []
        for item in self.__curr_config.task:
            self.__task_list.append(item)
        self.save_config()

    def load_config(self) -> None:
        """加载主配置文件，初始化多配置字典"""
        if not self.multi_config_path.exists():
            self.__config: MultiConfig = MultiConfig(
                curr_config_name="default",
                config_data={"default": self.create_empty_config()},
            )

            return

        try:
            with open(self.multi_config_path, "r", encoding="utf-8") as f:
                self.__config: MultiConfig = json.load(
                    f
                )  # 读取所有子配置到__config_dict
        except Exception as e:
            print(f"加载主配置失败：{e}")
            self.__config: MultiConfig = MultiConfig(
                curr_config_name="default", config_data={}
            )

    def save_config(self) -> None:
        """保存主配置文件"""
        try:
            with open(self.multi_config_path, "w", encoding="utf-8") as f:
                json.dump(self.__config, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"保存主配置失败：{e}")

    def get_config(self, config_name: str) -> Config:
        """获取指定名称的子配置（不存在则返回空字典）"""
        return self.__config.config_data[config_name]

    def set_config(self, config_name: str, config_data: Config) -> None:
        """添加或更新子配置，并自动保存主配置"""
        self.__config.config_data[config_name] = config_data
        self.save_config()

    def change_config(self, config_name: str) -> None:
        """切换当前配置"""
        self.__curr_config_name = config_name
        self.__curr_config = self.__config_data[config_name]
        self.__task_list = []
        for item in self.__curr_config.task:
            self.__task_list.append(item)

        self.save_config()

    def update_task_list(self, task_list: List[TaskItem]) -> None:
        self.__task_list = task_list
        self.__curr_config.task = self.__task_list
        self.save_config()

    # 生成一份空配置
    def create_empty_config(self) -> Config:
        """创建一个空配置"""
        empty_config = Config(
            is_enabled=True,
            task=[],
            gpu=0,
            finish_option=0,
            run_before_start="",
            run_before_start_args="",
            run_after_finish="",
            run_after_finish_args="",
            emu_path="",
            emu_args="",
            emu_wait_time=0,
            exe_path="",
            exe_args="",
            exe_wait_time=0,
            know_task=[],
            start_time="",
        )
        return empty_config
