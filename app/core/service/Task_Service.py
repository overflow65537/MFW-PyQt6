
import json

from pathlib import Path
from typing import Any, Dict, List, Optional


from ...utils.logger import logger
from ...utils.i18n_manager import get_interface_i18n
from .config_service import ConfigService
from app.core.Item import TaskItem,  CoreSignalBus



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
                # 优先使用翻译后的 interface.json
                try:
                    i18n = get_interface_i18n()
                    self.interface = i18n.get_translated_interface()
                    logger.debug("使用翻译后的 interface.json")
                except Exception as e:
                    logger.warning(
                        f"获取翻译后的 interface.json 失败，使用原始文件: {e}"
                    )
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
                        if "inputs" in option_template and isinstance(
                            option_template.get("inputs"), list
                        ):
                            # 为每个 input 生成默认值（直接值格式）
                            nested_values = {}
                            for input_config in option_template["inputs"]:
                                input_name = input_config.get("name")
                                default_value = input_config.get("default", "")
                                pipeline_type = input_config.get(
                                    "pipeline_type", "string"
                                )

                                # 根据 pipeline_type 转换默认值类型
                                if pipeline_type == "int":
                                    try:
                                        default_value = (
                                            int(default_value) if default_value else 0
                                        )
                                    except (ValueError, TypeError):
                                        logger.warning(
                                            f"无法将默认值 '{default_value}' 转换为整数,保持原值"
                                        )

                                # 直接保存值，不包装在字典中
                                nested_values[input_name] = default_value
                            default_option[task["name"]].update(
                                {option_name: nested_values}
                            )
                        # 检查是否有 default_case（直接保存值）
                        elif option_template.get("default_case"):
                            default_option[task["name"]].update(
                                {option_name: option_template.get("default_case")}
                            )
                        # 检查是否有 cases 且不为空（直接保存值）
                        elif (
                            option_template.get("cases")
                            and len(option_template.get("cases", [])) > 0
                        ):
                            default_option[task["name"]].update(
                                {
                                    option_name: option_template.get("cases", [])[0][
                                        "name"
                                    ]
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
        if target_task and hasattr(target_task, 'is_base_task') and target_task.is_base_task():
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
        
        # 从 task_option 中提取 pipeline_override
        from ...utils.pipeline_helper import get_pipeline_override_from_task_option
        
        option_pipeline_override = get_pipeline_override_from_task_option(
            self.interface,
            task.task_option
        )
        
        # 深度合并：任务级 pipeline_override + 选项级 pipeline_override
        merged_override = {}
        
        # 先添加任务级的
        self._deep_merge_dict(merged_override, task_pipeline_override)
        
        # 再添加选项级的（选项级优先级更高）
        self._deep_merge_dict(merged_override, option_pipeline_override)
        
        return {
            "entry": entry,
            "pipeline_override": merged_override
        }
    
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
