import uuid
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional
from abc import ABC, abstractmethod

from PySide6.QtCore import QObject, Signal
from ..utils.logger import logger
from ..utils.i18n_manager import get_interface_i18n


# ==================== 信号总线 ====================
class CoreSignalBus(QObject):
    """核心信号总线，用于组件间通信。"""

    # 配置相关信号 (多数使用 object 以传递 dataclass 对象)
    config_changed = Signal(str)  # 配置ID
    config_loaded = Signal(object)  # ConfigItem 或 dict (向后兼容)
    config_saved = Signal(bool)  # 保存结果

    # 任务相关信号
    tasks_loaded = Signal(object)  # List[TaskItem]
    task_updated = Signal(object)  # TaskItem
    task_selected = Signal(str)  # 任务ID
    task_order_updated = Signal(object)  # List[str]

    # 选项相关信号
    options_loaded = Signal(object)  # 选项字典
    option_updated = Signal(object)  # 选项更新(dict)

    # UI 操作信号
    need_save = Signal()
    # UI 操作信号（仅保留通用保存信号，具体操作通过 ServiceCoordinator 的方法调用）


class FromeServiceCoordinator(QObject):
    """
    从服务协调器发送的信号,用来通知UI层进行更新
    """

    fs_task_modified = Signal(object)  # 文件系统任务修改，载荷为 task
    fs_task_removed = Signal(str)  # 文件系统任务移除，载荷为 task_id
    fs_config_added = Signal(object)  # 文件系统配置新增，载荷为 config
    fs_config_removed = Signal(str)  # 文件系统配置移除，载荷为 config_id


# ==================== 数据模型 ====================
@dataclass
class TaskItem:
    """任务数据模型"""

    name: str
    item_id: str
    is_checked: bool
    task_option: Dict[str, Any]
    is_special: bool = False  # 标记是否为特殊任务

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "item_id": self.item_id,
            "is_checked": self.is_checked,
            "task_option": self.task_option,
            "is_special": self.is_special,
        }

    @staticmethod
    def generate_id(is_special: bool = False) -> str:
        """生成任务ID,特殊任务使用 s_ 前缀,普通任务使用 t_ 前缀"""
        prefix = "s_" if is_special else "t_"
        return f"{prefix}{uuid.uuid4().hex}"

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TaskItem":
        """从字典创建实例，自动生成 item_id"""
        item_id = data.get("item_id", "")
        is_special = data.get("is_special", False)
        if not item_id:
            item_id = cls.generate_id(is_special)
        return cls(
            name=data.get("name", ""),
            item_id=item_id,
            is_checked=data.get("is_checked", False),
            task_option=data.get("task_option", {}),
            is_special=is_special,
        )


@dataclass
class ConfigItem:
    """配置数据模型"""

    def __init__(
        self,
        name: str,
        item_id: str,
        tasks: List[TaskItem],
        know_task: List[str],
        bundle: Dict[str, Dict[str, Any]],
    ):
        self.name = name
        self.item_id = item_id

        self.tasks = tasks
        self.know_task = know_task
        self.bundle = bundle

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "item_id": self.item_id,
            "tasks": [task.to_dict() for task in self.tasks],
            "know_task": self.know_task,
            "bundle": self.bundle,
        }

    @staticmethod
    def generate_id() -> str:
        return f"c_{uuid.uuid4().hex}"

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConfigItem":
        item_id = data.get("item_id", "")
        if not item_id:
            item_id = cls.generate_id()
        bundle = data.get("bundle", {})
        return cls(
            name=data.get("name", ""),
            item_id=item_id,
            tasks=[TaskItem.from_dict(task) for task in data.get("tasks", [])],
            know_task=data.get("know_task", []),
            bundle=bundle,
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
    def create_config(self, config: ConfigItem) -> str:
        pass

    @abstractmethod
    def update_config(self, config_id: str, config_data: ConfigItem) -> bool:
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
    def update_task(self, task: TaskItem) -> bool:
        pass

    @abstractmethod
    def update_tasks(self, tasks: List[TaskItem]) -> bool:
        """批量更新任务（减少多次持久化开销）"""
        pass

    @abstractmethod
    def delete_task(self, task_id: str) -> bool:
        pass

    @abstractmethod
    def reorder_tasks(self, task_order: List[str]) -> bool:
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

        if not self.main_config_path.exists():
            # 优先使用翻译后的 interface.json
            try:
                i18n = get_interface_i18n()
                interface = i18n.get_translated_interface()
                logger.debug("使用翻译后的 interface.json 创建默认配置")
            except Exception as e:
                logger.warning(f"获取翻译后的 interface.json 失败，使用原始文件: {e}")
                interface_path = Path.cwd() / "interface.json"
                if not interface_path.exists():
                    raise FileNotFoundError(f"无有效资源 {interface_path}")
                with open(interface_path, "r", encoding="utf-8") as f:
                    interface = json.load(f)

            default_main_config = {
                "curr_config_id": "",
                "config_list": [],
                "bundle": [
                    {
                        "name": interface.get("name", "Default Bundle"),
                        "path": "./",
                    }
                ],
            }
            self.save_main_config(default_main_config)

    def load_main_config(self) -> Dict[str, Any]:
        """加载主配置"""
        try:
            with open(self.main_config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            raise

    def save_main_config(self, config_data: Dict[str, Any]) -> bool:
        """保存主配置"""
        try:
            with open(self.main_config_path, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            raise

    def load_config(self, config_id: str) -> Dict[str, Any]:
        """加载子配置"""
        config_file = self.configs_dir / f"{config_id}.json"
        if not config_file.exists():
            raise FileNotFoundError(f"配置文件 {config_file} 不存在")
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            raise

    def save_config(self, config_id: str, config_data: Dict[str, Any]) -> bool:
        """保存子配置"""
        try:
            config_file = self.configs_dir / f"{config_id}.json"
            with open(config_file, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            raise

    def delete_config(self, config_id: str) -> bool:
        """删除子配置"""
        config_file = self.configs_dir / f"{config_id}.json"
        if not config_file.exists():
            raise FileNotFoundError(f"配置文件 {config_file} 不存在")
        try:
            config_file.unlink()
            return True
        except Exception as e:
            raise

    def list_configs(self) -> List[str]:
        """列出所有子配置ID"""
        try:
            return [f.stem for f in self.configs_dir.glob("*.json") if f.is_file()]
        except Exception as e:
            raise


class ConfigService(IConfigService):
    """配置服务实现"""

    def __init__(self, config_repo: IConfigRepository, signal_bus: CoreSignalBus):
        self.repo = config_repo
        self.signal_bus = signal_bus
        self._main_config: Optional[Dict[str, Any]] = None

        # 加载主配置
        self.load_main_config()
        if self._main_config and not self._main_config.get("curr_config_id"):

            bundle = self._main_config.get("bundle", [])[0]
            default_tasks = [
                TaskItem(
                    name="资源",
                    item_id="r_" + TaskItem.generate_id()[2:],
                    is_checked=True,
                    task_option={},
                ),
                TaskItem(
                    name="完成后操作",
                    item_id="f_" + TaskItem.generate_id()[2:],
                    is_checked=True,
                    task_option={},
                ),
            ]
            default_config_item = ConfigItem(
                name="Default Config",
                item_id=ConfigItem.generate_id(),
                tasks=default_tasks,
                know_task=[],
                bundle=bundle,
            )
            
            self._main_config["config_list"].append(default_config_item.item_id)
            self._main_config["curr_config_id"] = default_config_item.item_id
            self.current_config_id = self.create_config(default_config_item)

            
            

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

    def save_config(self, config_id: str, config_data: ConfigItem) -> bool:
        """保存指定配置"""
        if self._main_config is None:
            return False

        # 如果配置ID不在主配置列表中，添加到主配置
        if config_id not in self._main_config.get("config_list", []):
            self._main_config["config_list"].append(config_id)
            self.save_main_config()

        # config_data 应为 ConfigItem，直接转换为 dict 保存
        return self.repo.save_config(config_id, config_data.to_dict())

    def create_config(self, config: ConfigItem) -> str:
        """创建新配置，统一使用 uuid 生成 id"""
        if not config.item_id:
            config.item_id = ConfigItem.generate_id()
        if self.save_config(config.item_id, config):
            return config.item_id
        return ""

    def update_config(self, config_id: str, config_data: ConfigItem) -> bool:
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
                summary = {"item_id": config_id, "name": config_data.get("name", "")}
                configs.append(summary)
        return configs

    def get_bundle(self, bundle_name: str) -> dict:
        """获取bundle数据（新格式：bundle为dict，key为名字）"""
        if self._main_config and "bundle" in self._main_config:
            bundle = self._main_config["bundle"]
            if isinstance(bundle, dict) and bundle_name in bundle:
                return bundle[bundle_name]
        raise FileNotFoundError(f"Bundle {bundle_name} not found")

    def list_bundles(self) -> List[str]:
        """列出所有bundle名称（新格式：bundle为dict，key为名字）"""
        if self._main_config and "bundle" in self._main_config:
            bundle = self._main_config["bundle"]
            if isinstance(bundle, dict):
                return list(bundle.keys())
        return []



class TaskService(ITaskService):
    """任务服务实现"""

    def __init__(self, config_service: ConfigService, signal_bus: CoreSignalBus):
        self.config_service = config_service
        self.signal_bus = signal_bus
        self.current_tasks = []
        self.know_task = []
        self.interface = {}
        self.default_option = {}
        self._on_config_changed(self.config_service.current_config_id)

        # 连接信号
        self.signal_bus.config_changed.connect(self._on_config_changed)
        self.signal_bus.task_updated.connect(self._on_task_updated)
        self.signal_bus.task_order_updated.connect(self._on_task_order_updated)
        # UI 的任务勾选切换事件现在通过 ServiceCoordinator.modify_task 路径处理

    def _on_config_changed(self, config_id: str):
        """当配置变化时加载对应任务"""
        if config_id:
            config = self.config_service.get_config(config_id)
            if config:
                # 优先使用翻译后的 interface.json
                try:
                    i18n = get_interface_i18n()
                    self.interface = i18n.get_translated_interface()
                    logger.debug("使用翻译后的 interface.json")
                except Exception as e:
                    logger.warning(f"获取翻译后的 interface.json 失败，使用原始文件: {e}")
                    # 降级方案：加载原始 interface.json
                    interface_path = Path.cwd() / "interface.json"
                    if not interface_path.exists():
                        raise FileNotFoundError(f"无有效资源 {interface_path}")
                    with open(interface_path, "r", encoding="utf-8") as f:
                        self.interface = json.load(f)
                self.current_tasks = config.tasks
                self.know_task = config.know_task
                self.default_option = self.gen_default_option()

                # 发出 TaskItem 列表，UI 层可以选择转换为 dict 显示
                self.signal_bus.tasks_loaded.emit(self.current_tasks)
                self._check_know_task()

    def _check_know_task(self) -> bool:
        unknown_tasks = []
        if not self.interface:
            raise ValueError("Interface not loaded")

        interface_tasks = [t["name"] for t in self.interface.get("task", [])]
        for task in interface_tasks:
            if task not in self.know_task:
                unknown_tasks.append(task)
        for unknown_task in unknown_tasks:
            self.know_task.append(unknown_task)
            self.add_task(unknown_task)

        # 同步到当前配置对象并持久化
        config = self.config_service.get_config(self.config_service.current_config_id)
        if config:
            config.know_task = self.know_task.copy()
            self.config_service.update_config(config.item_id, config)

        return True

    def add_task(self, task_name: str, is_special: bool = False) -> bool:
        """添加任务
        
        Args:
            task_name: 任务名称
            is_special: 是否为特殊任务,默认为 False
        """
        if not self.interface:
            raise ValueError("Interface not loaded")
        for task in self.interface.get("task", []):
            if task["name"] == task_name:
                # 检查 interface.json 中是否标记为特殊任务(spt字段)
                task_is_special = task.get("spt", is_special)
                
                new_task = TaskItem(
                    name=task["name"],
                    item_id=TaskItem.generate_id(is_special=task_is_special),
                    is_checked=not task_is_special,  # 特殊任务默认不选中
                    task_option=self.default_option.get(task["name"], {}),
                    is_special=task_is_special,
                )
                self.update_task(new_task)
                return True
        return False

    def gen_default_option(self) -> dict[str, dict[str, dict]]:
        """生成默认的任务选项映射"""
        if not self.interface:
            raise ValueError("Interface not loaded")
        default_option = {}
        for task in self.interface.get("task", []):
            default_option[task["name"]] = {}
            for option in task.get("option", []):
                for option_name, option_template in self.interface.get(
                    "option", {}
                ).items():
                    if option == option_name:
                        # 检查是否有 inputs 数组（多输入项类型，如自定义关卡）
                        if "inputs" in option_template and isinstance(option_template.get("inputs"), list):
                            # 为每个 input 生成默认值（直接值格式）
                            nested_values = {}
                            for input_config in option_template["inputs"]:
                                input_name = input_config.get("name")
                                default_value = input_config.get("default", "")
                                pipeline_type = input_config.get("pipeline_type", "string")
                                
                                # 根据 pipeline_type 转换默认值类型
                                if pipeline_type == "int":
                                    try:
                                        default_value = int(default_value) if default_value else 0
                                    except (ValueError, TypeError):
                                        logger.warning(f"无法将默认值 '{default_value}' 转换为整数,保持原值")
                                
                                # 直接保存值，不包装在字典中
                                nested_values[input_name] = default_value
                            default_option[task["name"]].update({option_name: nested_values})
                        # 检查是否有 default_case（直接保存值）
                        elif option_template.get("default_case"):
                            default_option[task["name"]].update(
                                {
                                    option_name: option_template.get("default_case")
                                }
                            )
                        # 检查是否有 cases 且不为空（直接保存值）
                        elif option_template.get("cases") and len(option_template.get("cases", [])) > 0:
                            default_option[task["name"]].update(
                                {
                                    option_name: option_template.get("cases", [])[0]["name"]
                                }
                            )
        return default_option

    def _on_task_updated(self, task_data: TaskItem):
        """当任务更新时保存到当前配置（接收 TaskItem 或 dict）"""
        config_id = self.config_service.current_config_id
        if not config_id:
            return

        config = self.config_service.get_config(config_id)
        if not config:
            return

        # Normalize incoming to TaskItem
        if isinstance(task_data, TaskItem):
            incoming = task_data
        else:
            incoming = TaskItem.from_dict(task_data)

        # 查找并更新任务
        task_updated = False
        for i, task in enumerate(config.tasks):
            if task.item_id == incoming.item_id:
                config.tasks[i] = incoming
                task_updated = True
                break

        # 如果是新任务，添加到列表倒数第二个，确保完成后操作在最后
        if not task_updated:
            config.tasks.insert(-1, incoming)

        # 保存配置（直接传入 ConfigItem，由底层处理转换）
        if self.config_service.update_config(config_id, config):
            # 更新本地任务列表并发出对象列表
            self.current_tasks = config.tasks
            self.signal_bus.tasks_loaded.emit(self.current_tasks)

    def _on_task_order_updated(self, task_order: List[str]):
        """同步最新任务顺序到当前配置并持久化，但不强制刷新UI列表。"""
        config_id = self.config_service.current_config_id
        if not config_id:
            return

        config = self.config_service.get_config(config_id)
        if not config:
            return

        tasks_by_id = {task.item_id: task for task in config.tasks}
        ordered_tasks: list[TaskItem] = []
        for task_id in task_order:
            task = tasks_by_id.pop(task_id, None)
            if task is not None:
                ordered_tasks.append(task)

        # 追加未在拖拽序列中的任务，确保列表完整
        if tasks_by_id:
            ordered_tasks.extend(tasks_by_id.values())

        if not ordered_tasks:
            return

        config.tasks = ordered_tasks

        if self.config_service.update_config(config_id, config):
            self.current_tasks = ordered_tasks

    def get_tasks(self) -> List[TaskItem]:
        """获取当前配置的任务列表"""
        return self.current_tasks

    def get_task(self, task_id: str) -> Optional[TaskItem]:
        """获取特定任务"""
        for task in self.current_tasks:
            if task.item_id == task_id:
                return task
        return None

    def update_task(self, task: TaskItem) -> bool:
        """更新任务"""

        # 发出任务更新信号
        self._on_task_updated(task)
        return True

    def update_tasks(self, tasks: List[TaskItem]) -> bool:
        """批量更新任务：在当前配置中按 tasks 中的 item_id 替换或添加，最后一次性保存并发送 tasks_loaded 或逐项 task_updated。"""
        if not tasks:
            return True

        config_id = self.config_service.current_config_id
        if not config_id:
            return False

        config = self.config_service.get_config(config_id)
        if not config:
            return False

        # build a map for quick replace
        id_to_task = {t.item_id: t for t in tasks}

        replaced = set()
        for i, t in enumerate(config.tasks):
            if t.item_id in id_to_task:
                config.tasks[i] = id_to_task[t.item_id]
                replaced.add(t.item_id)

        # add tasks that are new (not replaced)
        for t in tasks:
            if t.item_id not in replaced:
                # 插入到倒数第二位,确保"完成后操作"始终在最后
                config.tasks.insert(-1, t)

        # 保存配置一次
        ok = self.config_service.update_config(config_id, config)
        if ok:
            # 更新本地任务列表并发送整体 loaded 信号（UI 会进行 diff）
            self.current_tasks = config.tasks
            # 优先发送 tasks_loaded 以便视图基于完整列表做最小更新
            self.signal_bus.tasks_loaded.emit(self.current_tasks)
        return ok

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
        if self.config_service.update_config(config_id, config):
            # 更新本地任务列表
            self.current_tasks = config.tasks
            self.signal_bus.tasks_loaded.emit(self.current_tasks)
            return True

        return False

    def reorder_tasks(self, task_order: List[str]) -> bool:
        """重新排序任务"""
        self._on_task_order_updated(task_order)
        return True


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
        # 发出任务更新信号（对象形式）
        self.signal_bus.task_updated.emit(task)

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
        self.fs_signal_bus = FromeServiceCoordinator()

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

    def _connect_signals(self):
        """连接所有信号"""
        # UI请求保存配置
        self.signal_bus.need_save.connect(self._on_need_save)

    def add_config(self, config_item: ConfigItem) -> str:
        """添加配置，传入 ConfigItem 对象，返回新配置ID"""
        new_id = self.config_service.create_config(config_item)
        if new_id:
            # notify UI incrementally
            self.fs_signal_bus.fs_config_added.emit(
                self.config_service.get_config(new_id)
            )
        return new_id

    def delete_config(self, config_id: str) -> bool:
        """删除配置，传入 config id"""
        ok = self.config_service.delete_config(config_id)
        if ok:
            # notify UI incremental removal
            self.fs_signal_bus.fs_config_removed.emit(config_id)
        return ok

    def select_config(self, config_id: str) -> bool:
        """选择配置，传入 config id"""
        # 验证配置存在
        config = self.config_service.get_config(config_id)
        if not config:
            return False

        # 设置并保存主配置
        if self.config_service._main_config is None:
            return False

        self.config_service._main_config["curr_config_id"] = config_id
        if self.config_service.save_main_config():
            self.signal_bus.config_changed.emit(config_id)
            return True

        return False

    def modify_task(self, task: TaskItem) -> bool:
        """修改或添加任务：传入 TaskItem，如果列表中没有对应 id 的任务，添加到倒数第2位，否则更新对应任务"""
        config_id = self.config_service.current_config_id
        if not config_id:
            return False

        config = self.config_service.get_config(config_id)
        if not config:
            return False

        # 查找并更新
        found = False
        old_task = None
        for i, t in enumerate(config.tasks):
            if t.item_id == task.item_id:
                old_task = t
                config.tasks[i] = task
                found = True
                break

        if not found:
            # 插入到倒数第二位,确保"完成后操作"始终在最后
            config.tasks.insert(-1, task)

        # 保存配置
        ok = self.config_service.update_config(config_id, config)
        if ok:
            self.fs_signal_bus.fs_task_modified.emit(task)
        return ok

    def update_task_checked(self, task_id: str, is_checked: bool) -> bool:
        """仅更新任务的选中状态，不发射信号
        
        特殊任务互斥规则:
        - 如果选中的是特殊任务,则自动取消其他特殊任务的选中
        """
        config_id = self.config_service.current_config_id
        if not config_id:
            return False

        config = self.config_service.get_config(config_id)
        if not config:
            return False

        # 查找目标任务
        target_task = None
        for i, t in enumerate(config.tasks):
            if t.item_id == task_id:
                config.tasks[i].is_checked = is_checked
                target_task = config.tasks[i]
                break
        else:
            return False

        # 特殊任务互斥逻辑:如果选中的是特殊任务,取消其他特殊任务
        unchecked_tasks = []
        if target_task and target_task.is_special and is_checked:
            for i, t in enumerate(config.tasks):
                if t.item_id != task_id and t.is_special and t.is_checked:
                    config.tasks[i].is_checked = False
                    unchecked_tasks.append(config.tasks[i])

        # 保存配置
        ok = self.config_service.update_config(config_id, config)
        if ok:
            # 如果有其他特殊任务被取消选中,发射信号通知UI更新
            for task in unchecked_tasks:
                self.fs_signal_bus.fs_task_modified.emit(task)
                
        return ok

    def modify_tasks(self, tasks: List[TaskItem]) -> bool:
        """批量修改/新增任务，减少多次磁盘写入。成功后发出 fs_task_updated（逐项或 tasks_loaded 已由 service 发出）。"""
        if not tasks:
            return True

        ok = self.task_service.update_tasks(tasks)
        if ok:
            # 兼容：对于希望逐项更新的监听者，仍发出逐项 task_updated 信号
            try:
                for t in tasks:
                    self.fs_signal_bus.fs_task_modified.emit(t)
            except Exception:
                pass
        return ok

    def delete_task(self, task_id: str) -> bool:
        """删除任务，传入 task id，基础任务不可删除（通过特殊 id 区分）"""
        config = self.config_service.get_current_config()
        if not config:
            return False
        # 基础任务 id 以 r_ f_ 开头（资源和完成后操作）
        base_prefix = ("r_", "f_")
        for t in config.tasks:
            if t.item_id == task_id and t.item_id.startswith(base_prefix):
                return False
        ok = self.task_service.delete_task(task_id)
        if ok:
            self.fs_signal_bus.fs_task_removed.emit(task_id)
        return ok

    def select_task(self, task_id: str):
        """选中任务，传入 task id，并自动检查已知任务"""
        self.signal_bus.task_selected.emit(task_id)
        self.task._check_know_task()

    def reorder_tasks(self, new_order: List[str]) -> bool:
        """任务顺序更改，new_order 为 task_id 列表（新顺序）"""
        return self.task_service.reorder_tasks(new_order)

    def _on_need_save(self):
        """当UI请求保存时保存所有配置"""
        self.config_service.save_main_config()
        self.signal_bus.config_saved.emit(True)

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

    @property
    def fs_signals(self) -> FromeServiceCoordinator:
        return self.fs_signal_bus

    @property
    def signals(self) -> CoreSignalBus:
        return self.signal_bus
