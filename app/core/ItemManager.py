from pathlib import Path
import json
from dataclasses import dataclass
from PySide6.QtCore import QObject, Signal

from ..utils.logger import logger


class CoreSignalBus(QObject):

    change_task_flow = Signal()  # 切换任务列表
    show_option = Signal(dict)  # 显示选项
    need_save = Signal()  # 配置文件需要保存
    task_update = Signal(list)  # 任务列表更新


core_signalBus = CoreSignalBus()


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
    know_task: list
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

    def __init__(self, config: dict):
        super().__init__()
        logger.debug(f"接收到的配置：{config}")
        self.load(config)

    def load(self, config: dict) -> bool:
        """加载配置"""
        self.curr_config_id = config["curr_config_id"]
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
                config_item["task_type"],
            )
            self.config_list.append(config_item)
        return True

    def save(self, path: Path) -> bool:
        """保存配置"""
        try:
            with open(path, "w", encoding="utf-8") as f:
                config = {"curr_config_id": self.curr_config_id, "config_list": []}
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


class ConfigManager(BaseItemManager):
    """配置数据模型，管理所有配置数据"""

    def __init__(self, multi_config_path: Path | str, signal_bus: CoreSignalBus):
        super().__init__()
        self.signal_bus = signal_bus
        self.need_save = self.signal_bus.need_save
        self.change_task_flow = self.signal_bus.change_task_flow
        self.task_update = self.signal_bus.task_update
        self.need_save.connect(self.save_config)
        self.task_update.connect(self.update_current_config_tasks)

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
        self.change_task_flow.emit()
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

    def get_current_config_tasks(self) -> list[TaskItem]:
        """获取当前配置的任务列表"""
        return self.config.task.copy()

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
            logger.warning(f"配置文件不存在，创建新文件：{self.multi_config_path}")

            self.__config = self.create_empty_config()
            logger.info(
                f"{json.dumps(self.__config.show(), indent=4, ensure_ascii=False)}"
            )
            self.save_config()
            return True

        try:
            with open(self.multi_config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
                if (
                    config.get("curr_config_id") is None
                    or config.get("config_list") is None
                ):
                    raise ValueError("配置文件格式错误")

                self.__config = MultiConfig(config)
                logger.info(
                    f"加载配置成功：\n{json.dumps(self.__config.show(), indent=4, ensure_ascii=False)}"
                )
                return True
        except Exception as e:
            logger.error(f"加载配置失败：{e}\n使用新配置")
            self.__config = self.create_empty_config()
            logger.info(
                f"{json.dumps(self.__config.show(), indent=4, ensure_ascii=False)}"
            )
            self.save_config()
            return True

    def create_empty_config(self, name: str = "New Config") -> MultiConfig:
        resource_task: dict = {
            "name": "resource",
            "item_id": self.generate_id("task"),
            "is_checked": True,
            "task_option": {},
            "task_type": "resource",
        }
        controller_task: dict = {
            "name": "controller",
            "item_id": self.generate_id("task"),
            "is_checked": True,
            "task_option": {},
            "task_type": "controller",
        }

        """创建一个空配置"""
        empty_config: dict = {
            "name": name,
            "item_id": self.generate_id("config"),
            "is_checked": True,
            "task": [resource_task, controller_task],
            "gpu": -1,
            "finish_option": 0,
            "know_task": [],
            "task_type": "config",
        }

        empty_muit_config_dict: dict = {
            "curr_config_id": empty_config["item_id"],
            "config_list": [empty_config],
        }
        return MultiConfig(empty_muit_config_dict)

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
            if result:
                logger.info(f"配置保存成功：{self.multi_config_path}")
            return result
        except Exception as e:
            logger.error(f"保存配置时发生异常：{e}")
            return False


class TaskManager(BaseItemManager):

    def __init__(
        self, config_manager: ConfigManager, signal_bus: CoreSignalBus
    ) -> None:
        super().__init__()

        self.signal_bus = signal_bus
        self.need_save = self.signal_bus.need_save
        self.change_task_flow = self.signal_bus.change_task_flow
        self.task_update = self.signal_bus.task_update

        self.config_manager = config_manager
        self.task_list = []
        self.change_task_flow.connect(self.init_list)
        self.init_list()

    def init_list(self) -> None:
        self.task_list = self.config_manager.get_current_config_tasks()

    def add_task(self, task: TaskItem) -> bool:
        try:
            self.task_list.append(task)
            self.task_update.emit(self.task_list)
            self.need_save.emit()

            return True
        except Exception as e:
            logger.error(f"添加任务失败：{e}")
            return False

    def remove_task(self, task_id: str) -> bool:
        for i, task in enumerate(self.task_list):
            if task.item_id == task_id:
                self.task_list.pop(i)
                self.task_update.emit(self.task_list)
                self.need_save.emit()
                return True
        return False

    def update_task(self, task_id: str, task: TaskItem) -> bool:
        for i, t in enumerate(self.task_list):
            if t.item_id == task_id:
                self.task_list[i] = task
                self.task_update.emit(self.task_list)
                self.need_save.emit()
                return True
        return False

    def task_checkbox_state_changed(self, task_id: str, checked: bool) -> bool:
        for task in self.task_list:
            if task.item_id == task_id:
                task.is_checked = checked
                self.task_update.emit(self.task_list)
                self.need_save.emit()
                return True
        return False
