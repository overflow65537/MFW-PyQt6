import jsonc
from pathlib import Path
from typing import Any, Dict, List, Optional

from ...utils.logger import logger
from .interface_manager import get_interface_manager
from .Config_Service import ConfigService
from app.core.Item import TaskItem, CoreSignalBus


class TaskService:
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
                # 直接使用 interface manager 获取配置
                interface_manager = get_interface_manager()
                self.interface = interface_manager.get_interface()
                
                # 如果 interface 为空，说明加载失败
                if not self.interface:
                    interface_path_jsonc = Path.cwd() / "interface.jsonc"
                    interface_path_json = Path.cwd() / "interface.json"
                    
                    # 检查配置文件是否存在
                    if not interface_path_jsonc.exists() and not interface_path_json.exists():
                        raise FileNotFoundError(f"无有效资源配置文件: {interface_path_jsonc} 或 {interface_path_json}")
                
                logger.debug("使用 interface 配置")
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
        
    def init_new_config(self):
        """初始化新配置的任务"""
        # Re-load interface to get the latest configuration
        interface_manager = get_interface_manager()
        self.interface = interface_manager.get_interface()
        
        # Regenerate default options
        self.default_option = self.gen_default_option()
        
        # Reset know_task and add all tasks from interface
        self.know_task = []
        self._check_know_task()

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

                # 为当前任务动态生成默认选项
                task_default_option = self.gen_single_task_default_option(task)

                new_task = TaskItem(
                    name=task["name"],
                    item_id=TaskItem.generate_id(is_special=task_is_special),
                    is_checked=not task_is_special,  # 特殊任务默认不选中
                    task_option=task_default_option,
                    is_special=task_is_special,
                )
                self.update_task(new_task)
                return True
        return False

    def gen_single_task_default_option(self, task: dict) -> dict[str, dict]:
        """生成单个任务的默认选项"""
        if not self.interface:
            raise ValueError("Interface not loaded")
            
        def _gen_option_defaults_recursive(option_template):
            """递归生成选项默认值"""
            if "inputs" in option_template and isinstance(option_template["inputs"], list):
                # Input type with multiple inputs
                nested_values = {}
                for input_config in option_template["inputs"]:
                    input_name = input_config.get("name")
                    default_value = input_config.get("default", "")
                    pipeline_type = input_config.get("pipeline_type", "string")
                    
                    # Convert to appropriate type
                    if pipeline_type == "int":
                        try:
                            default_value = int(default_value) if default_value else 0
                        except (ValueError, TypeError):
                            pass
                    
                    nested_values[input_name] = default_value
                
                return nested_values
            
            elif option_template.get("cases") and len(option_template["cases"]) > 0:
                # Select type with cases
                selected_case = option_template["cases"][0]
                case_name = selected_case["name"]
                
                # Process child options recursively
                child_option_defaults = {}
                if "option" in selected_case:
                    for child_option_name in selected_case["option"]:
                        child_option_template = self.interface.get("option", {}).get(child_option_name)
                        if child_option_template:
                            child_option_defaults[child_option_name] = _gen_option_defaults_recursive(child_option_template)
                
                # Return appropriate structure based on whether there are child options
                if child_option_defaults:
                    return {case_name: child_option_defaults}
                else:
                    return case_name
            
            return {}
        
        task_name = task["name"]
        task_default_option = {}
        
        # Iterate through options defined for this task
        for option in task.get("option", []):
            option_template = self.interface.get("option", {}).get(option)
            if option_template:
                # Generate defaults for this option recursively
                option_defaults = _gen_option_defaults_recursive(option_template)
                task_default_option[option] = option_defaults
        
        return task_default_option
        
    def gen_default_option(self) -> dict[str, dict[str, dict]]:
        """生成所有任务的默认选项映射"""
        if not self.interface:
            raise ValueError("Interface not loaded")
        
        default_option = {}
        
        # Iterate through all tasks
        for task in self.interface.get("task", []):
            default_option[task["name"]] = self.gen_single_task_default_option(task)
        
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
        """删除任务（基础任务不可删除）"""
        config_id = self.config_service.current_config_id
        if not config_id:
            return False

        config = self.config_service.get_config(config_id)
        if not config:
            return False

        # 查找目标任务
        target_task = None
        for task in config.tasks:
            if task.item_id == task_id:
                target_task = task
                break
        if (
            target_task
            and hasattr(target_task, "is_base_task")
            and target_task.is_base_task()
        ):
            return False

        # 从配置中移除任务（非基础任务）
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

    def get_task_execution_info(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务的执行信息（entry 和 pipeline_override）

        Args:
            task_id: 任务ID

        Returns:
            Dict: 包含 entry 和 pipeline_override，格式为：
                {
                    "entry": "任务入口名称",
                    "pipeline_override": {...}
                }
            如果任务不存在或 interface 未加载，返回 None
        """
        # 获取任务
        task = self.get_task(task_id)
        if not task:
            logger.warning(f"任务 {task_id} 不存在")
            return None

        if not self.interface:
            logger.error("Interface 未加载")
            return None

        # 从 interface 中查找任务的 entry
        entry = None
        task_pipeline_override = {}

        for interface_task in self.interface.get("task", []):
            if interface_task.get("name") == task.name:
                entry = interface_task.get("entry", "")
                # 获取任务级别的 pipeline_override
                task_pipeline_override = interface_task.get("pipeline_override", {})
                break

        if not entry:
            logger.warning(f"任务 '{task.name}' 在 interface 中未找到 entry")
            return None

        from ..utils.pipeline_helper import get_pipeline_override_from_task_option

        option_pipeline_override = get_pipeline_override_from_task_option(
            self.interface, task.task_option
        )

        # 深度合并：任务级 pipeline_override + 选项级 pipeline_override
        merged_override = {}

        # 先添加任务级的
        self._deep_merge_dict(merged_override, task_pipeline_override)

        # 再添加选项级的（选项级优先级更高）
        self._deep_merge_dict(merged_override, option_pipeline_override)

        return {"entry": entry, "pipeline_override": merged_override}

    def _deep_merge_dict(self, target: Dict, source: Dict) -> None:
        """深度合并两个字典

        Args:
            target: 目标字典（会被修改）
            source: 源字典
        """
        for key, value in source.items():
            if (
                key in target
                and isinstance(target[key], dict)
                and isinstance(value, dict)
            ):
                # 递归合并
                self._deep_merge_dict(target[key], value)
            else:
                # 直接覆盖
                target[key] = value