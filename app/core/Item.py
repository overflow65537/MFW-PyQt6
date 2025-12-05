import uuid
from dataclasses import dataclass
from typing import Any, Dict, List
from PySide6.QtCore import QObject, Signal
from app.common.constants import PRE_CONFIGURATION, POST_ACTION


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
    options_loaded = Signal()  # 选项加载完成信号，不携带数据
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
    fs_start_button_status = Signal(
        dict
    )  # 控制开始按钮状态和文本，载荷如 {"text": "开始", "status": "enabled"}


# ==================== 数据模型 ====================
@dataclass
class TaskItem:
    """任务数据模型"""

    name: str
    item_id: str
    is_checked: bool
    task_option: Dict[str, Any]
    is_special: bool = False  # 标记是否为特殊任务

    def is_base_task(self) -> bool:
        """判断是否为基础任务（资源或完成后操作）"""
        return self.item_id in (PRE_CONFIGURATION, POST_ACTION)

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
        bundle: Dict[str, Dict[str, str]],
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
