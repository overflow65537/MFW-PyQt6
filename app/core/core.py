import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional
from abc import ABC, abstractmethod

from PySide6.QtCore import QObject, Signal


# ==================== 信号总线 ====================
class CoreSignalBus(QObject):
    """核心信号总线，用于组件间通信"""

    # 配置相关信号
    config_changed = Signal(str)  # 配置ID
    config_loaded = Signal(dict)  # 配置数据
    config_saved = Signal(bool)  # 保存结果

    # 任务相关信号
    tasks_loaded = Signal(list)  # 任务列表
    task_updated = Signal(dict)  # 任务数据
    task_selected = Signal(str)  # 任务ID
    task_order_updated = Signal(list)  # 任务顺序

    # 选项相关信号
    options_loaded = Signal(dict)  # 选项字典
    option_updated = Signal(dict)  # 选项更新

    # UI 操作信号
    need_save = Signal()
    create_config = Signal(object)  # 配置名称
    delete_config = Signal(str)  # 配置ID
    select_config = Signal(str)  # 配置ID
    create_task = Signal(object)  # 任务类型
    delete_task = Signal(str)  # 任务ID
    select_task = Signal(str)  # 任务ID
    toggle_task_check = Signal(str, bool)  # 任务ID, 是否启用

# ==================== 数据模型 ====================
@dataclass
class TaskItem:
    """任务数据模型"""

    name: str
    item_id: str
    is_checked: bool
    task_option: Dict[str, Any]
    task_type: str

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "item_id": self.item_id,
            "is_checked": self.is_checked,
            "task_option": self.task_option,
            "task_type": self.task_type,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TaskItem":
        """从字典创建实例"""
        return cls(
            name=data.get("name", ""),
            item_id=data.get("item_id", ""),
            is_checked=data.get("is_checked", False),
            task_option=data.get("task_option", {}),
            task_type=data.get("task_type", ""),
        )


@dataclass
class ConfigItem:
    """配置数据模型"""

    name: str
    item_id: str
    is_checked: bool
    tasks: List[TaskItem]
    know_task: List[str]
    bundle: Dict[str, str]
    task_type: str

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "item_id": self.item_id,
            "is_checked": self.is_checked,
            "tasks": [task.to_dict() for task in self.tasks],
            "know_task": self.know_task,
            "bundle": self.bundle,
            "task_type": self.task_type,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConfigItem":
        """从字典创建实例"""
        return cls(
            name=data.get("name", ""),
            item_id=data.get("item_id", ""),
            is_checked=data.get("is_checked", False),
            tasks=[TaskItem.from_dict(task) for task in data.get("tasks", [])],
            know_task=data.get("know_task", []),
            bundle=data.get("bundle", {}),
            task_type=data.get("task_type", ""),
        )


# ==================== 接口定义 ====================
class IConfigRepository(ABC):
    """配置存储库接口"""

    @abstractmethod
    def load_main_config(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    def save_main_config(self, config_data: Dict[str, Any]) -> bool:
        pass

    @abstractmethod
    def load_config(self, config_id: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    def save_config(self, config_id: str, config_data: Dict[str, Any]) -> bool:
        pass

    @abstractmethod
    def delete_config(self, config_id: str) -> bool:
        pass

    @abstractmethod
    def list_configs(self) -> List[str]:
        pass


class IConfigService(ABC):
    """配置服务接口"""

    @abstractmethod
    def get_current_config(self) -> Optional[ConfigItem]:
        pass

    @abstractmethod
    def create_config(self, config_data: Dict[str, Any]) -> str:
        pass

    @abstractmethod
    def update_config(self, config_id: str, config_data: Dict[str, Any]) -> bool:
        pass

    @abstractmethod
    def delete_config(self, config_id: str) -> bool:
        pass

    @abstractmethod
    def list_configs(self) -> List[Dict[str, Any]]:
        pass


class ITaskService(ABC):
    """任务服务接口"""

    @abstractmethod
    def get_tasks(self) -> List[TaskItem]:
        pass

    @abstractmethod
    def get_task(self, task_id: str) -> Optional[TaskItem]:
        pass

    @abstractmethod
    def add_task(self, task_data: Dict[str, Any]) -> bool:
        pass

    @abstractmethod
    def update_task(self, task_data: Dict[str, Any]) -> bool:
        pass

    @abstractmethod
    def delete_task(self, task_id: str) -> bool:
        pass

    @abstractmethod
    def reorder_tasks(self, task_order: List[str]) -> bool:
        pass
        
    @abstractmethod
    def toggle_task_check(self, task_id: str, is_checked: bool) -> bool:
        """切换任务的启用状态"""
        pass

class IOptionService(ABC):
    """选项服务接口"""

    @abstractmethod
    def get_options(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_option(self, option_key: str) -> Any:
        pass

    @abstractmethod
    def update_option(self, option_key: str, option_value: Any) -> bool:
        pass

    @abstractmethod
    def update_options(self, options: Dict[str, Any]) -> bool:
        pass


# ==================== 实现类 ====================
class JsonConfigRepository(IConfigRepository):
    """JSON配置存储库实现"""

    def __init__(self, main_config_path: Path, configs_dir: Path):
        self.main_config_path = main_config_path
        self.configs_dir = configs_dir

        # 确保目录存在
        if not self.configs_dir.exists():
            self.configs_dir.mkdir(parents=True)

    def load_main_config(self) -> Dict[str, Any]:
        """加载主配置"""
        if not self.main_config_path.exists():
            # 如果工作目录目录下没有interfere.json
            if not (Path.cwd() / "interface.json").exists():
                raise FileNotFoundError(f"{Path.cwd() / 'interface.json'} 无可用资源")

            with open(Path.cwd() / "interface.json", "r", encoding="utf-8") as f:
                interface = json.load(f)

            # 如果主配置不存在，创建默认主配置
            default_config = {
                "curr_config_id": "",
                "config_list": [],
                "bundle": [
                    {"name": interface.get("name", "Default Bundle"), "path": "./"}
                ],
            }
            self.save_main_config(default_config)
            return default_config

        try:
            with open(self.main_config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"加载主配置失败: {e}")
            return {}

    def save_main_config(self, config_data: Dict[str, Any]) -> bool:
        """保存主配置"""
        try:
            with open(self.main_config_path, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"保存主配置失败: {e}")
            return False

    def load_config(self, config_id: str) -> Dict[str, Any]:
        """加载子配置"""
        config_file = self.configs_dir / f"{config_id}.json"
        if not config_file.exists():
            return {}

        try:
            with open(config_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"加载子配置 {config_id} 失败: {e}")
            return {}

    def save_config(self, config_id: str, config_data: Dict[str, Any]) -> bool:
        """保存子配置"""
        try:
            config_file = self.configs_dir / f"{config_id}.json"
            with open(config_file, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"保存子配置 {config_id} 失败: {e}")
            return False

    def delete_config(self, config_id: str) -> bool:
        """删除子配置"""
        config_file = self.configs_dir / f"{config_id}.json"
        if config_file.exists():
            try:
                config_file.unlink()
                return True
            except Exception as e:
                print(f"删除子配置 {config_id} 失败: {e}")
        return False

    def list_configs(self) -> List[str]:
        """列出所有子配置ID"""
        return [f.stem for f in self.configs_dir.glob("*.json") if f.is_file()]


class ConfigService(IConfigService):
    """配置服务实现"""

    def __init__(self, config_repo: IConfigRepository, signal_bus: CoreSignalBus):
        self.repo = config_repo
        self.signal_bus = signal_bus
        self._main_config: Optional[Dict[str, Any]] = None

        # 加载主配置
        self.load_main_config()

    def load_main_config(self) -> bool:
        """加载主配置"""
        try:
            self._main_config = self.repo.load_main_config()
            return True
        except Exception as e:
            print(f"加载主配置失败: {e}")
            return False

    def save_main_config(self) -> bool:
        """保存主配置"""
        if self._main_config is None:
            print("没有主配置可保存")
            return False

        return self.repo.save_main_config(self._main_config)

    @property
    def current_config_id(self) -> str:
        """获取当前配置ID"""
        return self._main_config.get("curr_config_id", "") if self._main_config else ""

    @current_config_id.setter
    def current_config_id(self, value: str) -> bool:
        """设置当前配置ID"""
        if self._main_config is None:
            return False

        # 验证配置ID是否存在
        if value and value not in self._main_config.get("config_list", []):
            print(f"配置ID {value} 不存在")
            return False

        self._main_config["curr_config_id"] = value

        # 保存主配置并发出信号
        if self.save_main_config():
            self.signal_bus.config_changed.emit(value)
            return True

        return False

    def get_config(self, config_id: str) -> Optional[ConfigItem]:
        """获取指定配置"""
        config_data = self.repo.load_config(config_id)
        if not config_data:
            return None

        return ConfigItem.from_dict(config_data)

    def get_current_config(self) -> Optional[ConfigItem]:
        """获取当前配置"""
        if not self.current_config_id:
            return None

        return self.get_config(self.current_config_id)

    def save_config(self, config_id: str, config_data: Dict[str, Any]) -> bool:
        """保存指定配置"""
        if self._main_config is None:
            return False

        # 如果配置ID不在主配置列表中，添加到主配置
        if config_id not in self._main_config.get("config_list", []):
            self._main_config["config_list"].append(config_id)
            self.save_main_config()

        return self.repo.save_config(config_id, config_data)

    def create_config(self, config_data: Dict[str, Any]) -> str:
        """创建新配置"""
        # 生成唯一ID
        import random
        import string

        config_id = "c_" + "".join(
            random.choices(string.ascii_letters + string.digits, k=10)
        )
        config_data["item_id"] = config_id

        # 保存配置
        if self.save_config(config_id, config_data):
            return config_id

        return ""

    def update_config(self, config_id: str, config_data: Dict[str, Any]) -> bool:
        """更新配置"""
        return self.save_config(config_id, config_data)

    def delete_config(self, config_id: str) -> bool:
        """删除配置"""
        if self._main_config is None:
            return False

        # 从主配置列表中移除
        if config_id in self._main_config.get("config_list", []):
            self._main_config["config_list"].remove(config_id)

            # 如果删除的是当前配置，需要更新当前配置
            if self.current_config_id == config_id:
                if self._main_config["config_list"]:
                    self.current_config_id = self._main_config["config_list"][0]
                else:
                    self.current_config_id = ""

            # 保存主配置
            self.save_main_config()

        # 删除子配置文件
        return self.repo.delete_config(config_id)

    def list_configs(self) -> List[Dict[str, Any]]:
        """列出所有配置的概要信息"""
        if self._main_config is None:
            return []
        configs = []
        for config_id in self._main_config.get("config_list", []):
            config_data = self.repo.load_config(config_id)
            if config_data:
                # 只返回概要信息，不包含任务详情
                summary = {
                    "item_id": config_id,
                    "name": config_data.get("name", ""),
                    "is_checked": config_data.get("is_checked", False),
                    "task_type": config_data.get("task_type", ""),
                }
                configs.append(summary)
        return configs

    def get_bundle(self, bundle_name: str) -> dict:
        """获取bundle数据"""
        if self._main_config:
            for bundle in self._main_config["bundle"]:
                if bundle["name"] == bundle_name:
                    return bundle
        raise FileNotFoundError(f"Bundle {bundle_name} not found")

    def list_bundles(self) -> List[str]:
        """列出所有bundle名称"""
        if self._main_config:
            return list(map(lambda x: x["name"], self._main_config["bundle"]))
        return []

class TaskService(ITaskService):
    """任务服务实现"""

    def __init__(self, config_service: ConfigService, signal_bus: CoreSignalBus):
        self.config_service = config_service
        self.signal_bus = signal_bus
        self.current_tasks = []
        self.__interface_config = None
        self._on_config_changed(self.config_service.current_config_id)

        # 连接信号
        self.signal_bus.config_changed.connect(self._on_config_changed)
        self.signal_bus.task_updated.connect(self._on_task_updated)
        self.signal_bus.task_order_updated.connect(self._on_task_order_updated)
    def _load_interface_config(self):
        """加载interface.json配置文件"""
        try:
            # 从配置服务获取当前激活的bundle路径
            current_config = self.config_service.get_current_config()
            if current_config and hasattr(current_config, 'bundle') and current_config.bundle:
                # 构建interface.json路径
                import os
                interface_path = os.path.join(current_config.bundle.get('path', ''), "interface.json")
                
                # 检查文件是否存在
                if os.path.exists(interface_path):
                    # 读取interface.json内容
                    import json
                    with open(interface_path, 'r', encoding='utf-8') as f:
                        self.__interface_config = json.load(f)
                else:
                    print(f"Warning: interface.json not found at {interface_path}")
            else:
                print("Warning: No active bundle configuration found")
        except Exception as e:
            print(f"Error loading interface.json: {e}")
            self.__interface_config = None

    def get_interface(self) -> Optional[Dict[str, Any]]:
        """返回当前激活的bundle内容
        
        Returns:
            Optional[Dict[str, Any]]: interface.json内容，如果加载失败则为None
        """
        return self.__interface_config

    def _on_config_changed(self, config_id: str):
        """当配置变化时加载对应任务"""
        if config_id:
            config = self.config_service.get_config(config_id)
            if config:
                self.current_tasks = config.tasks
                self.signal_bus.tasks_loaded.emit(
                    [task.to_dict() for task in self.current_tasks]
                )
                self._load_interface_config()

    def _on_task_updated(self, task_data: Dict[str, Any]):
        """当任务更新时保存到当前配置"""
        config_id = self.config_service.current_config_id
        if not config_id:
            return

        config = self.config_service.get_config(config_id)
        if not config:
            return

        # 查找并更新任务
        task_updated = False
        for i, task in enumerate(config.tasks):
            if task.item_id == task_data.get("item_id"):
                config.tasks[i] = TaskItem.from_dict(task_data)
                task_updated = True
                break

        # 如果是新任务，添加到列表倒数第二个，确保完成后操作在最后
        if not task_updated:
            config.tasks.insert(-1, TaskItem.from_dict(task_data))

        # 保存配置
        if self.config_service.update_config(config_id, config.to_dict()):
            # 更新本地任务列表
            self.current_tasks = config.tasks
            self.signal_bus.tasks_loaded.emit(
                [task.to_dict() for task in self.current_tasks]
            )

    def _on_task_order_updated(self, task_order: List[str]):
        """当任务顺序更新时重新排序任务"""
        config_id = self.config_service.current_config_id
        if not config_id:
            return

        config = self.config_service.get_config(config_id)
        if not config:
            return

        # 根据新的顺序重新排列任务
        ordered_tasks = []
        for task_id in task_order:
            for task in config.tasks:
                if task.item_id == task_id:
                    ordered_tasks.append(task)
                    break

        # 更新配置中的任务顺序
        config.tasks = ordered_tasks

        # 保存配置
        if self.config_service.update_config(config_id, config.to_dict()):
            # 更新本地任务列表
            self.current_tasks = ordered_tasks
            self.signal_bus.tasks_loaded.emit(
                [task.to_dict() for task in self.current_tasks]
            )

    def get_tasks(self) -> List[TaskItem]:
        """获取当前配置的任务列表"""
        return self.current_tasks

    def get_task(self, task_id: str) -> Optional[TaskItem]:
        """获取特定任务"""
        for task in self.current_tasks:
            if task.item_id == task_id:
                return task
        return None

    def add_task(self, task_data: Dict[str, Any]) -> bool:
        """添加新任务"""
        # 生成任务ID
        if "item_id" not in task_data:
            import random
            import string

            task_data["item_id"] = "t_" + "".join(
                random.choices(string.ascii_letters + string.digits, k=10)
            )

        # 发出任务更新信号
        self.signal_bus.task_updated.emit(task_data)
        return True

    def update_task(self, task_data: Dict[str, Any]) -> bool:
        """更新任务"""
        # 发出任务更新信号
        self.signal_bus.task_updated.emit(task_data)
        return True

    def delete_task(self, task_id: str) -> bool:
        """删除任务"""
        config_id = self.config_service.current_config_id
        if not config_id:
            return False

        config = self.config_service.get_config(config_id)
        if not config:
            return False

        # 从配置中移除任务
        config.tasks = [task for task in config.tasks if task.item_id != task_id]

        # 保存配置
        if self.config_service.update_config(config_id, config.to_dict()):
            # 更新本地任务列表
            self.current_tasks = config.tasks
            self.signal_bus.tasks_loaded.emit(
                [task.to_dict() for task in self.current_tasks]
            )
            return True

        return False

    def reorder_tasks(self, task_order: List[str]) -> bool:
        """重新排序任务"""
        # 发出任务顺序更新信号
        self.signal_bus.task_order_updated.emit(task_order)
        return True
    
    def toggle_task_check(self, task_id: str, is_checked: bool) -> bool:
        """切换任务的启用状态"""
        task = self.get_task(task_id)
        if task:
            task.is_checked = is_checked
            # 通过任务更新信号来保存更改
            self.signal_bus.task_updated.emit(task.to_dict())
            return True
        return False

class OptionService(IOptionService):
    """选项服务实现"""

    def __init__(self, task_service: ITaskService, signal_bus: CoreSignalBus):
        self.task_service = task_service
        self.signal_bus = signal_bus
        self.current_task_id = None
        self.current_options = {}

        # 连接信号
        self.signal_bus.task_selected.connect(self._on_task_selected)
        self.signal_bus.option_updated.connect(self._on_option_updated)

    def _on_task_selected(self, task_id: str):
        """当任务被选中时加载选项"""
        self.current_task_id = task_id
        task = self.task_service.get_task(task_id)
        if task:
            self.current_options = task.task_option
            self.signal_bus.options_loaded.emit(self.current_options)

    def _on_option_updated(self, option_data: Dict[str, Any]):
        """当选项更新时保存到当前任务"""
        if not self.current_task_id:
            return

        task = self.task_service.get_task(self.current_task_id)
        if not task:
            return

        # 更新任务中的选项
        task.task_option.update(option_data)

        # 发出任务更新信号
        self.signal_bus.task_updated.emit(task.to_dict())

    def get_options(self) -> Dict[str, Any]:
        """获取当前任务的选项"""
        return self.current_options

    def get_option(self, option_key: str) -> Any:
        """获取特定选项"""
        return self.current_options.get(option_key)

    def update_option(self, option_key: str, option_value: Any) -> bool:
        """更新选项"""
        # 发出选项更新信号
        self.signal_bus.option_updated.emit({option_key: option_value})
        return True

    def update_options(self, options: Dict[str, Any]) -> bool:
        """批量更新选项"""
        # 发出选项更新信号
        self.signal_bus.option_updated.emit(options)
        return True


# ==================== 服务协调器 ====================
class ServiceCoordinator:
    """服务协调器，整合配置、任务和选项服务"""

    def __init__(self, main_config_path: Path, configs_dir: Path | None = None):
        # 初始化信号总线
        self.signal_bus = CoreSignalBus()

        # 确定配置目录
        if configs_dir is None:
            configs_dir = main_config_path.parent / "configs"

        # 初始化存储库和服务
        self.config_repo = JsonConfigRepository(main_config_path, configs_dir)
        self.config_service = ConfigService(self.config_repo, self.signal_bus)
        self.task_service = TaskService(self.config_service, self.signal_bus)
        self.option_service = OptionService(self.task_service, self.signal_bus)

        # 连接信号
        self._connect_signals()
        if (
            not self.config_service.current_config_id
            and not self.config_service.list_configs()
        ):
            bundle_name = self.config_service.list_bundles()[0]
            bundle_data = self.config_service.get_bundle(bundle_name)
            # 没有当前配置时，创建默认配置
            self._on_create_config("Default Config", bundle_data)

    def _connect_signals(self):
        """连接所有信号"""
        # UI请求保存配置
        self.signal_bus.need_save.connect(self._on_need_save)

        # UI请求创建新配置
        self.signal_bus.create_config.connect(self._on_create_config)

        # UI请求删除配置
        self.signal_bus.delete_config.connect(self._on_delete_config)

        # UI请求选择配置
        self.signal_bus.select_config.connect(self._on_select_config)

        # UI请求创建新任务
        self.signal_bus.create_task.connect(self._on_create_task)

        # UI请求删除任务
        self.signal_bus.delete_task.connect(self._on_delete_task)

        # UI请求选择任务
        self.signal_bus.select_task.connect(self._on_select_task)
        
        # 连接任务启用状态切换信号
        self.signal_bus.toggle_task_check.connect(self._on_toggle_task_check)
    
    def _on_need_save(self):
        """当UI请求保存时保存所有配置"""
        self.config_service.save_main_config()
        self.signal_bus.config_saved.emit(True)

    def _on_create_config(self, config_name: str, bundle: dict):
        """创建新配置"""
        import random
        import string

        default_config = {
            "name": config_name,
            "tasks": [
                {
                    "name":"controller",
                    "item_id": "c_" + "".join(
                        random.choices(string.ascii_letters + string.digits, k=10)
                    ),
                    "is_checked": True,
                    "task_option": {},
                    "task_type": "controller",
                },
                {
                    "name": "resource",
                    "item_id": "r_" + "".join(
                        random.choices(string.ascii_letters + string.digits, k=10)
                    ),
                    "is_checked": True,
                    "task_option": {},
                    "task_type": "resource",
                },
                {
                    "name": "finish",
                    "item_id": "f_" + "".join(
                        random.choices(string.ascii_letters + string.digits, k=10)
                    ),
                    "is_checked": True,
                    "task_option": {},
                    "task_type": "finish",
                },
            ],
            "know_task": [],
            "bundle": bundle,
            "task_type": "config",
        }

        config_id = self.config_service.create_config(default_config)

        if config_id:
            # 设置为当前配置
            self.config_service.current_config_id = config_id

    def _on_delete_config(self, config_id: str):
        """删除配置"""
        self.config_service.delete_config(config_id)

    def _on_select_config(self, config_id: str):
        """选择配置"""
        self.config_service.current_config_id = config_id

    def _on_create_task(self, name: str, options: Dict[str, Any], task_type: str="task"):
        """创建新任务"""
        default_task = {
            "name": name,
            "is_checked": True,
            "task_option": options,
            "task_type": task_type,
        }

        self.task_service.add_task(default_task)

    def _on_delete_task(self, task_id: str):
        """删除任务"""
        self.task_service.delete_task(task_id)

    def _on_select_task(self, task_id: str):
        """选择任务"""
        self.signal_bus.task_selected.emit(task_id)
    
    def _on_toggle_task_check(self, task_id: str, is_checked: bool):
        """切换任务的启用状态"""
        self.task_service.toggle_task_check(task_id, is_checked)

    # 提供获取服务的属性，以便UI层访问
    @property
    def config(self) -> ConfigService:
        return self.config_service

    @property
    def task(self) -> TaskService:
        return self.task_service

    @property
    def option(self) -> OptionService:
        return self.option_service


if __name__ == "__main__":
    # 测试代码
    main_config_path = Path("main_config.json")
    service_coordinator = ServiceCoordinator(main_config_path)
    print(service_coordinator.config.current_config_id)
    print(service_coordinator.task.current_tasks)
    print(service_coordinator.config.current_config_id)
    print(service_coordinator.task.current_tasks)
    print(service_coordinator.task.get_interface())
