from copy import deepcopy
from typing import Any, Dict, List, Optional

from app.utils.logger import logger
from app.core.service.Config_Service import ConfigService
from app.core.Item import TaskItem, CoreSignalBus

# 速通配置默认值
DEFAULT_SPEEDRUN_CONFIG: Dict[str, Any] = {
    "enabled": False,
    "force": False,
    "mode": "daily",
    "trigger": {
        "daily": {"hour_start": 0},
        "weekly": {"weekday": [1], "hour_start": 0},
        "monthly": {"day": [1], "hour_start": 0},
    },
    "run": {"count": 1, "min_interval_hours": 0},
}


class TaskService:
    """任务服务实现"""

    def __init__(
        self,
        config_service: ConfigService,
        signal_bus: CoreSignalBus,
        interface: Dict[str, Any],
    ):
        self.config_service = config_service
        self.signal_bus = signal_bus
        self.current_tasks = []
        self.know_task = []
        self.interface = interface or {}
        self.default_option = {}
        self.on_config_changed(self.config_service.current_config_id)
        # UI 的任务勾选切换事件现在通过 ServiceCoordinator.modify_task 路径处理

    def on_config_changed(self, config_id: str):
        """当配置变化时加载对应任务（由协调器直接调用）"""
        if config_id:
            config = self.config_service.get_config(config_id)
            if config:
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
        if not self.interface:
            raise ValueError("Interface not loaded")
        # Regenerate default options
        self.default_option = self.gen_default_option()

        # 重置任务列表，仅保留基础任务，防止重复追加
        config_id = self.config_service.current_config_id
        if not config_id:
            return
        config = self.config_service.get_config(config_id)
        if not config:
            return
        base_tasks = [t for t in config.tasks if t.is_base_task()]
        config.tasks = base_tasks
        self.config_service.update_config(config_id, config)
        self.current_tasks = base_tasks

        # Reset know_task and add all tasks from interface
        self.know_task = []
        self._check_know_task()

    def reload_interface(self, interface: Dict[str, Any]):
        """刷新 interface 数据，用于热更新后同步"""
        logger.info("重新加载 interface 数据...")
        if not interface:
            raise ValueError("Interface not loaded")
        self.interface = interface

        # 重新生成默认选项
        self.default_option = self.gen_default_option()

        # 检查是否有新任务
        self._check_know_task()

        logger.info("interface 数据重新加载完成")

    def _get_interface_speedrun(self, task_name: str) -> Dict[str, Any]:
        """从 interface 中获取任务的 speedrun 配置"""
        if not self.interface:
            return {}
        for task in self.interface.get("task", []):
            if task.get("name") == task_name:
                speedrun_cfg = task.get("speedrun")
                return deepcopy(speedrun_cfg) if isinstance(speedrun_cfg, dict) else {}
        return {}

    def build_speedrun_config(
        self, task_name: str, existing: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        合成 speedrun 配置：默认值 <- interface 配置 <- 已保存配置
        """
        config: Dict[str, Any] = deepcopy(DEFAULT_SPEEDRUN_CONFIG)
        interface_cfg = self._get_interface_speedrun(task_name)
        if interface_cfg:
            self._deep_merge_dict(config, interface_cfg)
        if isinstance(existing, dict):
            self._deep_merge_dict(config, deepcopy(existing))
        return config

    def ensure_speedrun_config_for_task(
        self, task: TaskItem, persist: bool = False
    ) -> Dict[str, Any]:
        """
        确保任务包含标准化的 speedrun 配置；可选持久化
        """
        if not isinstance(task.task_option, dict):
            task.task_option = {}

        existing = task.task_option.get("_speedrun_config")
        normalized = self.build_speedrun_config(task.name, existing)
        if existing != normalized:
            task.task_option["_speedrun_config"] = normalized
            if persist:
                self.update_task(task)
        return normalized

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

                # 任务是否默认选中
                default_check = False
                for task in self.interface.get("task", []):
                    if task["name"] == task_name:
                        default_check = task.get("default_check", False)
                        break

                new_task = TaskItem(
                    name=task["name"],
                    item_id=TaskItem.generate_id(is_special=task_is_special),
                    is_checked=default_check,
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

        interface_options = self.interface.get("option", {})

        def _select_default_case(option_def: dict) -> Optional[dict]:
            cases = option_def.get("cases", [])
            if not cases:
                return None
            target_case_name = option_def.get("default_case")
            if target_case_name:
                for case in cases:
                    if case.get("name") == target_case_name:
                        return case
            return cases[0]

        def _normalize_child_payload(payload: Any) -> dict[str, Any]:
            if isinstance(payload, dict):
                if "value" in payload:
                    return deepcopy(payload)
                return {"value": deepcopy(payload)}
            return {"value": deepcopy(payload)}

        def _gen_option_defaults_recursive(
            option_key: str, option_template: dict
        ) -> Any:
            """递归生成选项默认值"""
            inputs = option_template.get("inputs")
            if isinstance(inputs, list) and inputs:
                nested_values: dict[str, Any] = {}
                for input_config in inputs:
                    input_name = input_config.get("name")
                    default_value = input_config.get("default", "")
                    pipeline_type = input_config.get("pipeline_type", "string")

                    if pipeline_type == "int":
                        try:
                            default_value = int(default_value) if default_value else 0
                        except (ValueError, TypeError):
                            pass

                    if input_name:
                        nested_values[input_name] = default_value
                return {"value": nested_values}

            cases = option_template.get("cases", [])
            if cases:
                selected_case = _select_default_case(option_template)
                if not selected_case:
                    return {}
                selected_case_name = selected_case.get("name", "")
                option_result: dict[str, Any] = {"value": selected_case_name}

                children: dict[str, Any] = {}
                for case in cases:
                    case_name = case.get("name", "")
                    option_values = case.get("option")
                    if not option_values:
                        continue

                    if isinstance(option_values, str):
                        child_keys = [option_values]
                    elif isinstance(option_values, list):
                        child_keys = [
                            value for value in option_values if isinstance(value, str)
                        ]
                    else:
                        continue

                    for index, child_option_key in enumerate(child_keys):
                        child_template = interface_options.get(child_option_key)
                        if not child_template:
                            continue

                        child_default = _gen_option_defaults_recursive(
                            child_option_key, child_template
                        )
                        child_entry = _normalize_child_payload(child_default)

                        if case_name != selected_case_name:
                            child_entry["hidden"] = True
                        else:
                            child_entry.pop("hidden", None)

                        child_key = (
                            f"{option_key}_child_{case_name}_{child_option_key}_{index}"
                        )
                        children[child_key] = child_entry

                if children:
                    option_result["children"] = children

                return option_result

            return {}

        task_name = task["name"]
        task_default_option = {}

        # Iterate through options defined for this task
        for option in task.get("option", []):
            option_template = interface_options.get(option)
            if option_template:
                option_defaults = _gen_option_defaults_recursive(
                    option, option_template
                )
                task_default_option[option] = option_defaults

        # 追加速通配置（使用 interface 或默认值）
        task_default_option["_speedrun_config"] = self.build_speedrun_config(task_name)

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

    def apply_task_update(self, task_data: TaskItem) -> bool:
        """当任务更新时保存到当前配置（接收 TaskItem 或 dict）"""
        config_id = self.config_service.current_config_id
        if not config_id:
            return False

        config = self.config_service.get_config(config_id)
        if not config:
            return False

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
            return True
        return False

    def apply_task_order(self, task_order: List[str]) -> bool:
        """同步最新任务顺序到当前配置并持久化，但不强制刷新UI列表。"""
        config_id = self.config_service.current_config_id
        if not config_id:
            return False

        config = self.config_service.get_config(config_id)
        if not config:
            return False

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
            return False

        config.tasks = ordered_tasks

        if self.config_service.update_config(config_id, config):
            self.current_tasks = ordered_tasks
            return True
        return False

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

        return self.apply_task_update(task)

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
        return self.apply_task_order(task_order)

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

        from app.core.utils.pipeline_helper import (
            get_pipeline_override_from_task_option,
        )

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
