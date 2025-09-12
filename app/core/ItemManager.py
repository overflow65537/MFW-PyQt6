from pathlib import Path
import json
from dataclasses import dataclass

from PySide6.QtCore import QObject

from ..utils.logger import logger
from .CoreSignalBus import CoreSignalBus


@dataclass
class TaskItem:
    name: str
    item_id: str
    is_checked: bool
    task_option: dict
    task_type: str

    def __init__(
        self,
        name: str,
        item_id: str,
        is_checked: bool,
        task_option: dict,
        task_type: str,
    ):
        super().__init__()
        self.name = name
        self.item_id = item_id
        self.is_checked = is_checked
        self.task_option = task_option
        self.task_type = task_type

    def save(self) -> dict:
        """保存任务"""
        return self.__dict__.copy()


@dataclass
class ConfigItem:
    name: str
    item_id: str
    is_checked: bool
    task: list[TaskItem]
    gpu: int
    finish_option: int
    know_task: list[str]
    bundle_path: str
    task_type: str

    def __init__(
        self,
        name: str,
        item_id: str,
        is_checked: bool,
        task: list[TaskItem],
        gpu: int,
        finish_option: int,
        know_task: list,
        bundle: dict[str, str],
        task_type: str,
    ):
        super().__init__()
        self.name = name
        self.item_id = item_id
        self.is_checked = is_checked
        self.task = task
        self.gpu = gpu
        self.finish_option = finish_option
        self.know_task = know_task
        self.bundle = bundle
        self.task_type = task_type

    def save(self) -> dict:
        """保存配置"""
        task_list = []
        for task in self.task:
            task_list.append(task.save())
        return_dict = self.__dict__.copy()
        return_dict["task"] = task_list
        return return_dict


@dataclass
class MultiConfig:
    curr_config_id: str
    config_list: list[ConfigItem]
    bundle: list[dict[str, str]]

    def __init__(self, config: dict):
        super().__init__()
        logger.debug(f"接收到的配置：{config}")
        self.load(config)

    def load(self, config: dict) -> bool:
        """加载配置"""
        self.curr_config_id = config["curr_config_id"]
        self.bundle = config["bundle"]
        self.config_list = []
        for config_item in config["config_list"]:
            task_list = []
            for task_item in config_item["task"]:
                task = TaskItem(
                    task_item["name"],
                    task_item["item_id"],
                    task_item["is_checked"],
                    task_item["task_option"],
                    task_item["task_type"],
                )
                task_list.append(task)
            config_item = ConfigItem(
                config_item["name"],
                config_item["item_id"],
                config_item["is_checked"],
                task_list,
                config_item["gpu"],
                config_item["finish_option"],
                config_item["know_task"],
                config_item["bundle"],
                config_item["task_type"],
            )
            self.config_list.append(config_item)
        return True

    def save(self, path: Path) -> bool:
        """保存配置"""
        # 如果路径不存在，创建路径
        if not path.parent.exists():
            path.parent.mkdir(parents=True)
        try:
            with open(path, "w", encoding="utf-8") as f:
                config = {
                    "curr_config_id": self.curr_config_id,
                    "config_list": [],
                    "bundle": self.bundle,
                }
                for config_item in self.config_list:
                    config_item_dict = config_item.save()
                    config["config_list"].append(config_item_dict)
                json.dump(config, f, ensure_ascii=False, indent=4)
            return True
        except Exception as e:
            logger.error(f"保存配置失败：{e}")
            return False

    def show(self) -> dict:
        """显示配置"""
        config = {"curr_config_id": self.curr_config_id, "config_list": []}
        for config_item in self.config_list:
            config_item_dict = config_item.save()
            config["config_list"].append(config_item_dict)
        return config


class BaseItemManager(QObject):

    @staticmethod
    def generate_id(t: str) -> str:
        """随机生成config id"""
        import random
        import string

        if t[0].lower() == "c":  # 配置(config)
            key = "c_" + "".join(
                random.choices(string.ascii_letters + string.digits, k=10)
            )
        elif t[0].lower() == "t":  # 任务(task)
            key = "t_" + "".join(
                random.choices(string.ascii_letters + string.digits, k=10)
            )
        else:
            raise ValueError(f"type:{t} must be config or task")
        return key

    @staticmethod
    def generate_task() -> list[TaskItem]:
        """随机生成任务id"""
        resource_task = TaskItem(
            name="资源任务",
            item_id=BaseItemManager.generate_id("task"),
            is_checked=True,
            task_option={},
            task_type="resource",
        )
        controller_task = TaskItem(
            name="控制器任务",
            item_id=BaseItemManager.generate_id("task"),
            is_checked=True,
            task_option={},
            task_type="controller",
        )
        return [resource_task, controller_task]


class ConfigManager(BaseItemManager):
    """配置数据模型，管理所有配置数据"""

    def __init__(self, multi_config_path: Path | str, signal_bus: CoreSignalBus):
        super().__init__()
        self.signal_bus = signal_bus
        self.signal_bus.need_save.connect(self.save_config)
        self.signal_bus.task_update.connect(self.update_current_config_tasks)
        self.signal_bus.show_option.connect(self.show_option)

        self.multi_config_path = Path(multi_config_path)
        logger.info(f"加载配置文件：{self.multi_config_path}")
        self.load_config()

    @property
    def curr_config_id(self) -> str:
        """获取当前配置id"""
        return self.__config.curr_config_id

    @curr_config_id.setter
    def curr_config_id(self, value: str) -> bool:
        """设置当前配置id"""
        self.__config.curr_config_id = value
        self.save_config()
        return True

    @property
    def config_list(self) -> list[ConfigItem]:
        """获取配置列表"""
        return self.__config.config_list

    @property
    def all_config(self) -> MultiConfig:
        """获取所有配置"""
        return self.__config

    @all_config.setter
    def all_config(self, value: MultiConfig) -> bool:
        """设置所有配置"""
        self.__config = value
        logger.info("手动修改配置")
        self.save_config()
        self.signal_bus.change_task_flow.emit()
        return True

    @property
    def config(self) -> ConfigItem:
        """获取当前配置"""
        return self.from_id_get_config(self.curr_config_id)

    @config.setter
    def config(self, value: ConfigItem) -> bool:
        """设置当前配置"""
        self.from_id_set_config(self.curr_config_id, value)
        return True

    def update_config_order(self, config_list: list[ConfigItem]) -> bool:
        """更新配置列表顺序"""
        # 传入列表,列表中的元素是item_id,根据id更新配置列表顺序

        self.__config.config_list = config_list
        self.save_config()
        return True

    def update_current_config_tasks(self, tasks: list[TaskItem]) -> bool:
        """更新当前配置的任务列表"""
        try:
            current_config = self.config
            current_config.task = tasks
            self.config = current_config
            return True
        except Exception as e:
            logger.error(f"更新任务列表失败：{e}")
            return False

    def add_config(self, config: ConfigItem) -> bool:
        """添加配置"""
        self.config_list.append(config)
        logger.info("手动添加配置")
        self.save_config()
        return True

    def remove_config(self, config_id: str) -> bool:
        """删除配置"""
        found = False
        for i, config in enumerate(self.config_list):
            if config.item_id == config_id:
                # 找到配置，执行删除
                self.config_list.pop(i)
                found = True
                # 如果删除的是当前配置，则更新当前配置
                if config_id == self.curr_config_id and self.config_list:
                    self.curr_config_id = self.config_list[0].item_id
                break

        if not found:
            logger.error(f"未找到配置{config_id}")
            return False
        else:
            # 只有成功删除配置后才保存
            self.save_config()
            return True

    def config_checkbox_state_changed(self, config_id: str, checked: bool) -> bool:
        """配置复选框状态改变"""
        found = False
        for config in self.config_list:
            if config.item_id == config_id:
                config.is_checked = checked
                found = True
                break

        if not found:
            logger.error(f"未找到配置{config_id}")
            return False

        logger.info(f"配置{config_id}复选框状态改变为{checked}")
        self.save_config()
        return True

    def load_config(self) -> bool:
        """加载配置文件，初始化多配置字典"""
        if not self.multi_config_path.exists():
            raise FileNotFoundError(f"配置文件不存在：{self.multi_config_path}")
        with open(self.multi_config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
            if config.get("curr_config_id") is None:
                raise ValueError("配置ID不能为空")
            elif config.get("config_list") is None:
                raise ValueError("配置列表不能为空")
            elif config.get("bundle") is None:
                raise ValueError("bundle不能为空")

            self.__config = MultiConfig(config)
            logger.info(
                f"加载配置成功：\n{json.dumps(self.__config.show(), indent=4, ensure_ascii=False)}"
            )
            return True

    def from_id_get_config(self, config_id: str) -> ConfigItem:
        """根据配置id获取配置"""
        for config in self.config_list:
            if config.item_id == config_id:
                return config
        raise ValueError(f"未找到配置{config_id}")

    def from_id_set_config(self, config_id: str, config: ConfigItem) -> bool:
        """根据配置id设置配置"""
        for i, item in enumerate(self.config_list):
            if item.item_id == config_id:
                self.config_list[i] = config
                self.save_config()
                return True

        logger.error(f"未找到配置{config_id}")
        return False

    def save_config(self) -> bool:
        """保存配置"""
        try:
            result = self.__config.save(self.multi_config_path)
            return result
        except Exception as e:
            logger.error(f"保存配置时发生异常：{e}")
            return False
        
    def show_option(self, item: TaskItem | ConfigItem) -> None:
        """接受ListItem的点击来来切换配置"""
        if isinstance(item, ConfigItem):
            logger.info(f"点击了配置{item.name}")
            self.curr_config_id = item.item_id
            self.signal_bus.change_task_flow.emit()

class TaskManager(BaseItemManager):

    def __init__(
        self, config_manager: ConfigManager, signal_bus: CoreSignalBus
    ) -> None:
        super().__init__()

        self.signal_bus = signal_bus
        self.config_manager = config_manager
        self.__task_list = []
        self.signal_bus.change_task_flow.connect(self.init_list)
        self.init_list()

    def init_list(self) -> None:
        self.__task_list = self.config_manager.config.task.copy()
        with open(
            Path(self.config_manager.config.bundle.get("path", "")) / "interface.json",
            "r",
            encoding="utf-8",
        ) as f:
            self.interface = json.load(f)

    @property
    def task_list(self) -> list[TaskItem]:
        return self.__task_list

    def add_task(self, task: TaskItem) -> bool:
        try:
            self.__task_list.append(task)
            self.signal_bus.task_update.emit(self.__task_list)
            return True
        except Exception as e:
            logger.error(f"添加任务失败：{e}")
            return False

    def remove_task(self, task_id: str) -> bool:
        for i, task in enumerate(self.__task_list):
            if task.item_id == task_id:
                self.__task_list.pop(i)
                self.signal_bus.task_update.emit(self.__task_list)
                return True
        return False

    def update_task(self, task_id: str, task: TaskItem) -> bool:
        for i, t in enumerate(self.__task_list):
            if t.item_id == task_id:
                self.__task_list[i] = task
                self.signal_bus.task_update.emit(self.__task_list)
                return True
        return False
    
    def update_task_order(self, task_list: list[TaskItem]) -> bool:
        """更新任务列表顺序"""
        self.__task_list =  task_list
        self.signal_bus.task_update.emit(self.__task_list)
        return True

    def task_checkbox_state_changed(self, task_id: str, checked: bool) -> bool:
        for task in self.__task_list:
            if task.item_id == task_id:
                task.is_checked = checked
                self.signal_bus.task_update.emit(self.__task_list)
                return True
        return False

    def get_task(self, task_id: str) -> TaskItem | None:
        for task in self.__task_list:
            if task.item_id == task_id:
                return task
        return None

    def from_id_get_task(self, task_id: str) -> TaskItem | None:
        for task in self.__task_list:
            if task.item_id == task_id:
                return task
        return None