from typing import TypedDict
from pathlib import Path
import json
import queue
import asyncio
import aiofiles
import json
from PySide6.QtCore import QObject
from PySide6.QtCore import QObject, Signal, Property, Slot

from ..utils.logger import logger
from ..core.CoreSignalBus import core_signalBus


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
    task: list[TaskItem]
    gpu: int
    finish_option: int
    know_task: list
    task_type: str


class MultiConfig(TypedDict, total=True):
    curr_config_id: str
    config_list: list[ConfigItem]


class BaseItemManaget(QObject):

    @staticmethod
    def generate_id(t: str) -> str:
        """随机生成config id"""
        import random
        import string

        if t[0].lower() == "c":  # 配置
            key = "c_" + "".join(
                random.choices(string.ascii_letters + string.digits, k=10)
            )
        elif t[0].lower() == "t":  # 任务
            key = "t_" + "".join(
                random.choices(string.ascii_letters + string.digits, k=10)
            )
        else:
            raise ValueError(f"type:{t} must be config or task")
        return key


class ConfigManager(BaseItemManaget):
    """配置数据模型，管理所有配置数据"""

    need_save = core_signalBus.need_save  # 配置文件需要保存
    change_task_flow = core_signalBus.change_task_flow  # 任务流改变

    def __init__(self, multi_config_path: Path | str):

        self.multi_config_path = Path(multi_config_path)
        logger.info(f"加载配置文件：{self.multi_config_path}")
        self.load_config()
        self.save_queue = queue.Queue()
        self.is_saving = False
        self.loop = asyncio.get_event_loop()

        # 连接信号到队列处理函数
        self.need_save.connect(self.add_to_save_queue)

    @property
    def curr_config_id(self) -> str:
        return self.__config["curr_config_id"]

    @curr_config_id.setter
    def curr_config_id(self, value: str) -> None:
        logger.info(f"手动修改当前配置为{value}")
        self.__config["curr_config_id"] = value
        self.need_save.emit()
        self.change_task_flow.emit()

    @property
    def config_list(self) -> list[ConfigItem]:
        return self.__config["config_list"]

    @property
    def config(self) -> MultiConfig:
        return self.__config

    @config.setter
    def config(self, value: MultiConfig) -> None:
        self.__config = value
        logger.info("手动修改配置")
        self.need_save.emit()
        self.change_task_flow.emit()

    def add_config(self, config: ConfigItem) -> None:
        """添加配置"""
        self.config_list.append(config)
        logger.info("手动添加配置")
        self.need_save.emit()

    def remove_config(self, config_id: str) -> None:
        """删除配置"""
        for config in self.config_list:
            if config["item_id"] == config_id:
                self.config_list.remove(config)
                break
            else:
                logger.error(f"未找到配置{config_id}")
        else:
            logger.error(f"未找到配置{config_id}")
        self.need_save.emit()

    def config_checkbox_state_changed(self, config_id: str, checked: bool) -> None:
        """配置复选框状态改变"""
        for config in self.config_list:
            if config["item_id"] == config_id:
                config["is_checked"] = checked
                break
            else:
                logger.error(f"未找到配置{config_id}")
        logger.info(f"配置{config_id}复选框状态改变为{checked}")
        self.need_save.emit()

    def load_config(self) -> None:
        """加载配置文件，初始化多配置字典"""
        if not self.multi_config_path.exists():
            logger.warning(f"配置文件不存在，创建新文件：")
            empty_config = self.create_empty_config()
            self.__config: MultiConfig = {
                "curr_config_id": empty_config["item_id"],
                "config_list": [empty_config],
            }
            logger.info(f"{json.dumps(empty_config, indent=4, ensure_ascii=False)}")
            self.need_save.emit()

            return

        try:
            with open(self.multi_config_path, "r", encoding="utf-8") as f:
                self.__config: MultiConfig = json.load(f)
                if not self.__config or not self.__config.get("config_list"):
                    raise ValueError("配置数据无效")
                logger.info(
                    f"加载配置成功：\n{json.dumps(self.__config, indent=4, ensure_ascii=False)}"
                )
        except Exception as e:
            logger.error(f"加载配置失败：{e}\n使用新配置")
            empty_config = self.create_empty_config()
            self.__config: MultiConfig = {
                "curr_config_id": empty_config["item_id"],
                "config_list": [empty_config],
            }
            logger.info(f"{json.dumps(empty_config, indent=4, ensure_ascii=False)}")
            self.need_save.emit()

    def create_empty_config(self) -> ConfigItem:
        resource_task: TaskItem = {
            "name": "资源",
            "item_id": self.generate_id("task"),
            "is_checked": True,
            "task_option": {},
            "task_type": "resource",
        }
        controller_task: TaskItem = {
            "name": "控制器",
            "item_id": self.generate_id("task"),
            "is_checked": True,
            "task_option": {},
            "task_type": "controller",
        }
        """创建一个空配置"""
        empty_config: ConfigItem = {
            "name": "新配置",
            "item_id": self.generate_id("config"),
            "is_checked": True,
            "task": [resource_task, controller_task],
            "gpu": -1,
            "finish_option": 0,
            "know_task": [],
            "task_type": "config",
        }
        return empty_config

    @Slot(dict)
    def add_to_save_queue(self, data):
        """将需要保存的数据添加到队列"""
        self.save_queue.put(data)
        if not self.is_saving:
            self.loop.create_task(self.async_save_data())

    async def async_save_data(self):
        """异步处理保存队列中的数据"""
        self.is_saving = True
        while not self.save_queue.empty():
            data = self.save_queue.get()
            try:
                await self._save_to_file(data)
                logger.info(f"配置数据保存成功: {json.dumps(data, ensure_ascii=False)}")
            except Exception as e:
                logger.error(f"配置数据保存失败: {str(e)}")
            finally:
                self.save_queue.task_done()
        self.is_saving = False

    async def _save_to_file(self, data):
        """实际保存数据到文件的异步方法"""
        # 根据实际需求修改文件路径
        file_path = self.multi_config_path
        async with aiofiles.open(file_path, "w", encoding="utf-8") as f:
            await f.write(json.dumps(data, indent=4, ensure_ascii=False))


class TaskManager(BaseItemManaget):
    """任务数据模型，管理所有任务数据"""

    def __init__(self, config_manager: ConfigManager):

        self.config_manager = config_manager
