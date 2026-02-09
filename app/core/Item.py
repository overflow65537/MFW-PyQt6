import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator
from PySide6.QtCore import QObject, Signal
from app.common.constants import POST_ACTION, _CONTROLLER_, _RESOURCE_, SPECIAL_TASK_TYPES


# ==================== 信号总线 ====================
class CoreSignalBus(QObject):
    """核心信号总线，用于组件间通信。
    
    重构后：信号仅用于通知UI刷新，不再传递数据。
    前端通过属性访问获取数据。
    
    信号命名约定：
    - 原 CoreSignalBus 信号：无前缀
    - 原 FromeServiceCoordinator 信号：带 fs_ 前缀（保持向后兼容）
    """

    # 配置相关信号 - 仅通知，不传递数据
    config_changed = Signal(str)  # 配置ID，通知配置已切换
    config_saved = Signal(bool)  # 保存结果

    # 任务相关信号 - 仅通知
    tasks_loaded = Signal()  # 任务列表已加载/更新，前端重新读取
    task_updated = Signal(str)  # 任务ID，通知任务已更新
    task_selected = Signal(str)  # 任务ID，通知任务已选中

    # 选项相关信号
    options_loaded = Signal()  # 选项加载完成信号
    option_updated = Signal(object)  # 选项字典，通知选项已更新

    # UI 操作信号
    need_save = Signal()

    # ==================== 原 FromeServiceCoordinator 信号（已合并） ====================
    # 从服务协调器发送的信号，用于通知UI层进行更新
    fs_task_modified = Signal(str)  # 任务ID，通知任务已修改
    fs_task_removed = Signal(str)  # 任务ID，通知任务已移除
    fs_config_added = Signal(str)  # 配置ID，通知配置已添加
    fs_config_removed = Signal(str)  # 配置ID，通知配置已移除
    fs_start_button_status = Signal(dict)  # 控制开始按钮状态


# 向后兼容别名：FromeServiceCoordinator 现在是 CoreSignalBus 的别名
# 新代码应该直接使用 CoreSignalBus
FromeServiceCoordinator = CoreSignalBus


# ==================== 数据模型 (Pydantic) ====================
class TaskItem(BaseModel):
    """任务数据模型（使用 Pydantic）"""
    
    name: str = Field(..., min_length=1)
    item_id: str = Field(default="")
    is_checked: bool = False
    task_option: Dict[str, Any] = Field(default_factory=dict)
    is_special: bool = False  # 标记是否为特殊任务（来自 interface.json 的 spt 字段）
    special_type: str = Field(default="")  # 特殊任务类型（等待/启动程序/通知）
    is_hidden: bool = False  # 运行时字段，不序列化到 JSON

    model_config = {
        "validate_assignment": True,  # 允许赋值时验证
        "extra": "ignore",  # 忽略额外字段
    }

    @model_validator(mode='before')
    @classmethod
    def validate_and_clean(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """验证和清理数据"""
        if not isinstance(values, dict):
            return values
            
        # 生成 item_id（如果缺失）
        item_id = values.get('item_id', '')
        is_special = values.get('is_special', False)
        special_type = values.get('special_type', '')
        if not item_id:
            values['item_id'] = cls.generate_id(is_special, special_type)
        
        # 获取 task_option
        task_option = values.get('task_option', {})
        if not isinstance(task_option, dict):
            task_option = {}
        
        item_id = values.get('item_id', '')
        
        # 基础任务清理逻辑
        if item_id in (_CONTROLLER_, _RESOURCE_, POST_ACTION):
            # 基础任务不应该包含 speedrun_config
            if '_speedrun_config' in task_option:
                task_option = dict(task_option)  # 创建副本
                del task_option['_speedrun_config']
            
            # Resource 任务不应该包含控制器相关字段
            if item_id == _RESOURCE_:
                fields_to_remove = ["gpu", "agent_timeout", "custom", "controller_type", "adb", "win32"]
                task_option = dict(task_option)  # 确保是副本
                for field in fields_to_remove:
                    task_option.pop(field, None)
            
            # Controller 任务不应该包含 resource 字段
            elif item_id == _CONTROLLER_:
                task_option = dict(task_option)  # 确保是副本
                task_option.pop("resource", None)
        
        values['task_option'] = task_option
        return values

    def is_base_task(self) -> bool:
        """判断是否为基础任务（控制器/资源/完成后操作）"""
        return self.item_id in (_CONTROLLER_, _RESOURCE_, POST_ACTION)
    
    def is_special_task(self) -> bool:
        """判断是否为用户可自由操作的特殊任务（等待/启动程序/通知）"""
        return self.special_type in SPECIAL_TASK_TYPES

    @staticmethod
    def generate_id(is_special: bool = False, special_type: str = "") -> str:
        """生成任务ID
        
        Args:
            is_special: 是否为 interface.json 中的特殊任务
            special_type: 特殊任务类型（等待/启动程序/通知）
        """
        if special_type:
            # 特殊任务使用 sp_ 前缀
            prefix = "sp_"
        elif is_special:
            prefix = "s_"
        else:
            prefix = "t_"
        return f"{prefix}{uuid.uuid4().hex}"

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典（不包含 is_hidden）"""
        result = {
            "name": self.name,
            "item_id": self.item_id,
            "is_checked": self.is_checked,
            "task_option": self.task_option,
            "is_special": self.is_special,
        }
        # 只有当 special_type 有值时才序列化
        if self.special_type:
            result["special_type"] = self.special_type
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TaskItem":
        """从字典创建实例（兼容旧代码）"""
        return cls.model_validate(data)


class ConfigItem(BaseModel):
    """配置数据模型（使用 Pydantic）"""
    
    name: str = Field(..., min_length=1)
    item_id: str = Field(default="")
    tasks: List[TaskItem] = Field(default_factory=list)
    know_task: List[str] = Field(default_factory=list)
    bundle: str = Field(default="Default Bundle")

    model_config = {
        "validate_assignment": True,
        "extra": "ignore",
    }

    @model_validator(mode='before')
    @classmethod
    def validate_config(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """验证配置数据"""
        if not isinstance(values, dict):
            return values
            
        # 生成 item_id（如果缺失）
        if not values.get('item_id'):
            values['item_id'] = cls.generate_id()
        
        # 兼容旧数据格式的 bundle 字段
        raw_bundle = values.get('bundle', '')
        if isinstance(raw_bundle, str):
            bundle_name = raw_bundle or "Default Bundle"
        elif isinstance(raw_bundle, dict):
            if raw_bundle:
                first_key = next(iter(raw_bundle.keys()))
                first_val = raw_bundle[first_key]
                # 旧格式1：{"MPA": {...}}
                if isinstance(first_val, dict) and "path" in first_val:
                    bundle_name = first_key
                else:
                    # 旧格式2：{"path": "./"} 或 {"name": "...", "path": "..."}
                    bundle_name = str(raw_bundle.get("name") or "Default Bundle")
            else:
                bundle_name = "Default Bundle"
        else:
            bundle_name = "Default Bundle"
        
        values['bundle'] = bundle_name
        return values

    @field_validator('tasks', mode='before')
    @classmethod
    def validate_tasks(cls, v: Any) -> List[TaskItem]:
        """验证任务列表，自动将字典转换为 TaskItem 对象"""
        if not isinstance(v, list):
            return []
        
        validated_tasks = []
        for task_data in v:
            if isinstance(task_data, dict):
                validated_tasks.append(TaskItem.model_validate(task_data))
            elif isinstance(task_data, TaskItem):
                validated_tasks.append(task_data)
        return validated_tasks

    def get_task(self, task_id: str) -> Optional[TaskItem]:
        """获取指定任务"""
        for task in self.tasks:
            if task.item_id == task_id:
                return task
        return None

    def add_task(self, task: TaskItem, idx: int = -2) -> None:
        """添加任务到配置"""
        if idx >= 0:
            self.tasks.insert(idx, task)
        else:
            # 负数索引：插入到倒数第 |idx| 个位置之前
            insert_pos = len(self.tasks) + idx + 1
            insert_pos = max(0, min(insert_pos, len(self.tasks)))
            self.tasks.insert(insert_pos, task)

    def remove_task(self, task_id: str) -> bool:
        """从配置中移除任务"""
        original_len = len(self.tasks)
        self.tasks = [t for t in self.tasks if t.item_id != task_id]
        return len(self.tasks) < original_len

    def update_task(self, task: TaskItem) -> bool:
        """更新配置中的任务"""
        for i, t in enumerate(self.tasks):
            if t.item_id == task.item_id:
                self.tasks[i] = task
                return True
        return False

    @staticmethod
    def generate_id() -> str:
        """生成配置ID"""
        return f"c_{uuid.uuid4().hex}"

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "item_id": self.item_id,
            "tasks": [task.to_dict() for task in self.tasks],
            "know_task": self.know_task,
            "bundle": self.bundle,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConfigItem":
        """从字典创建实例（兼容旧代码）"""
        return cls.model_validate(data)
