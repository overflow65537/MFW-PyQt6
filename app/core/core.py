"""
服务协调器 - 核心模块

重构目标：
1. 全局单实例模式
2. 多运行器支持（每个配置独立运行器，支持并行运行）
3. 按需创建运行器（懒加载）
4. 属性访问模式，移除信号传递数据
"""

from pathlib import Path
from typing import List, Dict, Any, Optional, TYPE_CHECKING
from datetime import datetime
import time
import shutil

import jsonc

from PySide6.QtCore import QTimer

from app.core.Item import (
    CoreSignalBus,
    FromeServiceCoordinator,
    ConfigItem,
    TaskItem,
)
from app.core.service.Config_Service import ConfigService, JsonConfigRepository
from app.core.service.Schedule_Service import ScheduleService
from app.core.service.Task_Service import TaskService
from app.core.service.Option_Service import OptionService
from app.core.service.interface_manager import get_interface_manager, InterfaceManager
from app.core.log_processor import CallbackLogProcessor
from app.utils.logger import logger
from app.common.signal_bus import signalBus

if TYPE_CHECKING:
    from app.core.runner.task_flow import TaskFlowRunner


# ==================== 全局单实例管理 ====================
_instance: Optional['ServiceCoordinator'] = None


def get_service_coordinator() -> 'ServiceCoordinator':
    """获取全局单实例服务协调器
    
    Returns:
        ServiceCoordinator: 全局服务协调器实例
        
    Raises:
        RuntimeError: 如果服务协调器尚未初始化
    """
    global _instance
    if _instance is None:
        raise RuntimeError("ServiceCoordinator not initialized. Call init_service_coordinator first.")
    return _instance


def init_service_coordinator(
    main_config_path: Path,
    configs_dir: Path | None = None,
    interface_path: Path | str | None = None,
) -> 'ServiceCoordinator':
    """初始化全局单实例服务协调器
    
    Args:
        main_config_path: 主配置文件路径
        configs_dir: 配置目录路径（可选）
        interface_path: interface 文件路径（可选）
        
    Returns:
        ServiceCoordinator: 初始化后的服务协调器实例
        
    Raises:
        RuntimeError: 如果服务协调器已初始化
    """
    global _instance
    if _instance is not None:
        raise RuntimeError("ServiceCoordinator already initialized")
    _instance = ServiceCoordinator(main_config_path, configs_dir, interface_path)
    return _instance


def reset_service_coordinator() -> None:
    """重置全局单实例（仅用于测试或热重载）"""
    global _instance
    _instance = None


# ==================== 运行器状态 ====================
class RunnerState:
    """运行器状态管理"""
    def __init__(self):
        self.is_running: bool = False
        self.created_at: datetime = datetime.now()
        self.last_used: datetime = datetime.now()
    
    def mark_running(self):
        self.is_running = True
        self.last_used = datetime.now()
    
    def mark_stopped(self):
        self.is_running = False
        self.last_used = datetime.now()


# ==================== 配置实例 ====================
class ConfigInstance:
    """单个配置的实例
    
    提供对特定配置的所有操作：
    - item: 配置数据（ConfigItem）
    - tasks: 任务列表
    - runner: 运行器（懒加载）
    - is_running: 运行状态
    """
    
    def __init__(self, config_id: str, coordinator: 'ServiceCoordinator'):
        self._config_id = config_id
        self._coordinator = coordinator
    
    @property
    def id(self) -> str:
        """配置ID"""
        return self._config_id
    
    @property
    def item(self) -> ConfigItem | None:
        """配置数据"""
        return self._coordinator.config_service.get_config(self._config_id)
    
    @property
    def tasks(self) -> List[TaskItem]:
        """任务列表"""
        config = self.item
        return config.tasks if config else []
    
    def get_task(self, task_id: str) -> TaskItem | None:
        """获取指定任务"""
        config = self.item
        return config.get_task(task_id) if config else None
    
    @property
    def runner(self) -> 'TaskFlowRunner':
        """运行器（懒加载）"""
        return self._coordinator.get_runner(self._config_id)
    
    @property
    def is_running(self) -> bool:
        """是否正在运行"""
        return self._coordinator.is_running(self._config_id)
    
    @property
    def runner_state(self) -> RunnerState | None:
        """运行器状态"""
        return self._coordinator._runner_states.get(self._config_id)
    
    def start(self, task_id: str | None = None):
        """启动任务流"""
        import asyncio
        asyncio.create_task(
            self._coordinator.run_tasks_flow(config_id=self._config_id, task_id=task_id)
        )
    
    def stop(self):
        """停止任务流"""
        import asyncio
        asyncio.create_task(
            self._coordinator.stop_task_flow(config_id=self._config_id)
        )
    
    def save(self) -> bool:
        """保存配置"""
        return self._coordinator.save_config(self._config_id)
    
    def delete(self) -> bool:
        """删除配置"""
        return self._coordinator.delete_config(self._config_id)
    
    def __repr__(self):
        config = self.item
        name = config.name if config else "Unknown"
        return f"<ConfigInstance id={self._config_id} name={name} running={self.is_running}>"


class ConfigInstanceManager:
    """配置实例管理器
    
    支持字典式访问：config["配置id"]
    支持当前配置属性：config.current
    
    用法：
        coordinator.config["c_xxx"]  # 获取特定配置实例
        coordinator.config.current   # 获取当前配置实例
        coordinator.config.current = "c_xxx"  # 设置当前配置
        "c_xxx" in coordinator.config  # 检查配置是否存在
        for cfg in coordinator.config:  # 遍历所有配置
    """
    
    def __init__(self, coordinator: 'ServiceCoordinator'):
        self._coordinator = coordinator
        self._instances: Dict[str, ConfigInstance] = {}
        self._init_instances()
    
    def _init_instances(self):
        """初始化所有配置实例"""
        for config_info in self._coordinator.config_service.list_configs():
            # list_configs 返回 {"item_id": ..., "name": ...}
            config_id = config_info.get("item_id") or config_info.get("config_id") or config_info.get("id")
            if config_id:
                self._instances[config_id] = ConfigInstance(config_id, self._coordinator)
        logger.debug(f"已初始化 {len(self._instances)} 个配置实例")
    
    def refresh(self):
        """刷新配置实例（添加新配置、移除已删除的配置）"""
        current_ids = set(self._instances.keys())
        actual_ids = set()
        
        for config_info in self._coordinator.config_service.list_configs():
            # list_configs 返回 {"item_id": ..., "name": ...}
            config_id = config_info.get("item_id") or config_info.get("config_id") or config_info.get("id")
            if config_id:
                actual_ids.add(config_id)
                if config_id not in self._instances:
                    self._instances[config_id] = ConfigInstance(config_id, self._coordinator)
        
        # 移除已删除的配置
        for config_id in current_ids - actual_ids:
            del self._instances[config_id]
    
    def __getitem__(self, config_id: str) -> ConfigInstance:
        """获取配置实例"""
        if config_id not in self._instances:
            # 尝试刷新
            self.refresh()
            if config_id not in self._instances:
                raise KeyError(f"配置 {config_id} 不存在")
        return self._instances[config_id]
    
    def __contains__(self, config_id: str) -> bool:
        """检查配置是否存在"""
        return config_id in self._instances
    
    def __iter__(self):
        """遍历所有配置实例"""
        return iter(self._instances.values())
    
    def __len__(self):
        """配置数量"""
        return len(self._instances)
    
    def keys(self):
        """所有配置ID"""
        return self._instances.keys()
    
    def values(self):
        """所有配置实例"""
        return self._instances.values()
    
    def items(self):
        """配置ID和实例的键值对"""
        return self._instances.items()
    
    def get(self, config_id: str, default=None) -> ConfigInstance | None:
        """获取配置实例（不存在返回默认值）"""
        return self._instances.get(config_id, default)
    
    @property
    def current(self) -> ConfigInstance | None:
        """当前配置实例"""
        current_id = self._coordinator.current_config_id
        if not current_id:
            return None
        return self.get(current_id)
    
    @current.setter
    def current(self, config_id: str):
        """设置当前配置"""
        if config_id not in self._instances:
            raise KeyError(f"配置 {config_id} 不存在")
        self._coordinator.current_config_id = config_id
    
    @property
    def current_id(self) -> str:
        """当前配置ID"""
        return self._coordinator.current_config_id

    @current_id.setter
    def current_id(self, value: str):
        """设置当前配置ID"""
        self.current = value
    
    # 别名：保持向后兼容
    @property
    def current_config_id(self) -> str:
        """当前配置ID（current_id 的别名）"""
        return self.current_id
    
    @current_config_id.setter
    def current_config_id(self, value: str):
        """设置当前配置ID"""
        self.current_id = value
    
    def add(self, config_item: ConfigItem) -> ConfigInstance:
        """添加新配置，返回配置实例"""
        new_id = self._coordinator.add_config(config_item)
        if new_id:
            self._instances[new_id] = ConfigInstance(new_id, self._coordinator)
            return self._instances[new_id]
        raise ValueError("添加配置失败")
    
    def remove(self, config_id: str) -> bool:
        """删除配置"""
        ok = self._coordinator.delete_config(config_id)
        if ok and config_id in self._instances:
            del self._instances[config_id]
        return ok
    
    def running(self) -> List[ConfigInstance]:
        """获取所有正在运行的配置实例"""
        return [inst for inst in self._instances.values() if inst.is_running]
    
    # ==================== 便捷运行方法 ====================
    
    def run(self, config_id: str, task_id: str | None = None) -> ConfigInstance:
        """运行指定配置
        
        Args:
            config_id: 配置ID
            task_id: 指定任务ID（可选，默认运行所有选中任务）
            
        Returns:
            ConfigInstance: 启动的配置实例
            
        用法:
            coordinator.config.run("c_xxx")  # 运行配置
            coordinator.config.run("c_xxx", "task_123")  # 运行配置中的指定任务
        """
        instance = self[config_id]
        instance.start(task_id)
        return instance
    
    def stop(self, config_id: str) -> ConfigInstance:
        """停止指定配置
        
        Args:
            config_id: 配置ID
            
        Returns:
            ConfigInstance: 停止的配置实例
        """
        instance = self[config_id]
        instance.stop()
        return instance
    
    def stop_all(self):
        """停止所有运行中的配置"""
        for instance in self.running():
            instance.stop()
    
    # ==================== 向后兼容的代理方法 ====================
    # 这些方法代理到底层 ConfigService，保持旧代码兼容
    
    def list_configs(self) -> List[Dict[str, Any]]:
        """列出所有配置（代理到 ConfigService）"""
        return self._coordinator.config_service.list_configs()
    
    def get_config(self, config_id: str) -> ConfigItem | None:
        """获取配置（代理到 ConfigService）"""
        return self._coordinator.config_service.get_config(config_id)
    
    def save_config(self, config_id: str, config: ConfigItem | None = None) -> bool:
        """保存配置（代理到 ConfigService）"""
        if config is None:
            config = self.get_config(config_id)
        if config:
            return self._coordinator.config_service.save_config(config_id, config)
        return False
    
    def list_bundles(self) -> List[str]:
        """列出所有 bundles（代理到 ConfigService）"""
        return self._coordinator.config_service.list_bundles()
    
    def get_bundle(self, bundle_name: str) -> Dict[str, Any]:
        """获取 bundle 信息（代理到 ConfigService）"""
        return self._coordinator.config_service.get_bundle(bundle_name)
    
    def __repr__(self):
        return f"<ConfigInstanceManager count={len(self)} current={self.current_id}>"


# ==================== 服务协调器 ====================
class ServiceCoordinator:
    """服务协调器，整合配置、任务和选项服务
    
    重构后的核心特性：
    1. 全局单实例模式
    2. 多运行器支持（每个配置独立运行器）
    3. 按需创建运行器（懒加载）
    4. 属性访问模式
    """

    def __init__(
        self,
        main_config_path: Path,
        configs_dir: Path | None = None,
        interface_path: Path | str | None = None,
    ):
        # 初始化信号总线（仅用于通知，不传递数据）
        self.signal_bus = CoreSignalBus()
        self.fs_signal_bus = FromeServiceCoordinator()
        
        # 存储待显示的错误信息
        self._pending_error_message: tuple[str, str] | None = None
        self._main_config_path = main_config_path

        # 解析 interface 路径
        self._interface_path = self._resolve_interface_path(
            main_config_path, interface_path
        )

        # 确定配置目录
        if configs_dir is None:
            configs_dir = main_config_path.parent / "configs"

        # 初始化 interface 管理器
        self.interface_manager: InterfaceManager = get_interface_manager(
            interface_path=self._interface_path
        )
        self._interface: Dict = self.interface_manager.get_interface()

        # 初始化存储库
        self.config_repo = JsonConfigRepository(
            main_config_path, configs_dir, interface=self._interface
        )
        
        # 初始化服务
        try:
            self.config_service = ConfigService(self.config_repo, self.signal_bus)
            self.task_service = TaskService(
                self.config_service, self.signal_bus, self._interface
            )
        except (IndexError, ValueError, jsonc.JSONDecodeError, FileNotFoundError, Exception) as e:
            logger.error(f"配置加载失败: {e}")
            if self._handle_config_load_error(main_config_path, configs_dir, e):
                try:
                    self.config_service = ConfigService(self.config_repo, self.signal_bus)
                    self.task_service = TaskService(
                        self.config_service, self.signal_bus, self._interface
                    )
                except Exception as retry_error:
                    logger.error(f"重置配置后重新初始化失败: {retry_error}")
                    raise
            else:
                raise
        
        self.option_service = OptionService(self.task_service, self.signal_bus)
        self.config_service.register_on_change(self._on_config_changed)

        # ==================== 多运行器支持 ====================
        # 运行器字典（懒加载，按需创建）
        # 设计：每个配置都有独立的运行器，支持多个配置同时运行
        self._runners: Dict[str, 'TaskFlowRunner'] = {}
        self._runner_states: Dict[str, RunnerState] = {}

        # 调度服务
        schedule_store = main_config_path.parent / "schedules.json"
        self.schedule_service = ScheduleService(self, schedule_store)

        # 日志处理器
        self.log_processor = CallbackLogProcessor()

        # 连接信号
        self._connect_signals()

        # 清理无效的 bundle 索引
        self._cleanup_invalid_bundles()
        
        # ==================== 配置实例管理器 ====================
        # 启动时创建所有配置的实例，支持 config["配置id"] 访问
        self.config = ConfigInstanceManager(self)

    # ==================== 运行器管理（多运行器支持） ====================
    
    def get_runner(self, config_id: str | None = None) -> 'TaskFlowRunner':
        """获取指定配置的运行器（懒加载，按需创建）
        
        Args:
            config_id: 配置ID，如果为 None 则使用当前配置
            
        Returns:
            TaskFlowRunner: 配置对应的运行器
        """
        if config_id is None:
            config_id = self.current_config_id
        
        if not config_id:
            raise ValueError("No config_id specified and no current config")
        
        # 如果运行器不存在，现场创建
        if config_id not in self._runners:
            return self.create_runner_for_config(config_id)
        
        # 更新最后使用时间
        if config_id in self._runner_states:
            self._runner_states[config_id].last_used = datetime.now()
        
        return self._runners[config_id]

    def create_runner_for_config(self, config_id: str) -> 'TaskFlowRunner':
        """为指定配置创建运行器（现场创建，可传给前端）
        
        Args:
            config_id: 配置ID
            
        Returns:
            TaskFlowRunner: 新创建的运行器
        """
        # 如果已存在，直接返回
        if config_id in self._runners:
            return self._runners[config_id]
        
        # 验证配置存在
        config = self.config_service.get_config(config_id)
        if not config:
            raise ValueError(f"配置 {config_id} 不存在")
        
        # 延迟导入避免循环依赖
        from app.core.runner.task_flow import TaskFlowRunner
        
        # 创建运行器
        runner = TaskFlowRunner(
            task_service=self.task_service,
            config_service=self.config_service,
            fs_signal_bus=self.fs_signal_bus,
            config_id=config_id,  # 传入配置ID
            service_coordinator=self,  # 传入服务协调器
        )
        
        # 缓存运行器
        self._runners[config_id] = runner
        self._runner_states[config_id] = RunnerState()
        
        logger.debug(f"为配置 {config_id} 创建运行器")
        return runner

    def delete_runner(self, config_id: str) -> bool:
        """删除指定配置的运行器
        
        Args:
            config_id: 配置ID
            
        Returns:
            bool: 是否删除成功
        """
        if config_id in self._runners:
            runner = self._runners.pop(config_id)
            if hasattr(runner, 'cleanup'):
                try:
                    runner.cleanup()
                except Exception as e:
                    logger.warning(f"清理运行器失败: {e}")
            self._runner_states.pop(config_id, None)
            return True
        return False

    def is_running(self, config_id: str | None = None) -> bool:
        """检查配置是否正在运行
        
        Args:
            config_id: 配置ID，如果为 None 则使用当前配置
        """
        if config_id is None:
            config_id = self.current_config_id
        
        if config_id in self._runner_states:
            return self._runner_states[config_id].is_running
        return False

    def get_running_configs(self) -> List[str]:
        """获取所有正在运行的配置ID列表"""
        return [
            config_id for config_id, state in self._runner_states.items()
            if state.is_running
        ]

    # ==================== 属性访问接口 ====================
    
    @property
    def current_config_id(self) -> str:
        """获取当前激活配置ID"""
        return self.config_service.current_config_id

    @current_config_id.setter
    def current_config_id(self, value: str) -> None:
        """设置当前激活配置ID（自动保存）"""
        self.config_service.current_config_id = value

    @property
    def current_config(self) -> ConfigItem | None:
        """获取当前激活配置对象（只读）"""
        config_id = self.current_config_id
        if not config_id:
            return None
        return self.config_service.get_config(config_id)

    @property
    def current_tasks(self) -> List[TaskItem]:
        """获取当前配置的任务列表（只读）"""
        return self.task_service.get_tasks()

    @property
    def current_task_id(self) -> str | None:
        """获取当前选中的任务ID"""
        return self.option_service.current_task_id

    @current_task_id.setter
    def current_task_id(self, value: str) -> None:
        """设置当前选中的任务ID"""
        self.option_service.select_task(value)

    @property
    def current_options(self) -> Dict[str, Any]:
        """获取当前任务的选项（只读）"""
        return self.option_service.get_options()

    # ==================== 配置管理 ====================
    
    def get_config(self, config_id: str) -> ConfigItem | None:
        """获取指定配置"""
        return self.config_service.get_config(config_id)

    def list_configs(self) -> List[Dict[str, Any]]:
        """列出所有配置的概要信息"""
        return self.config_service.list_configs()

    def add_config(self, config_item: ConfigItem) -> str:
        """添加配置，返回新配置ID"""
        new_id = self.config_service.create_config(config_item)
        if new_id:
            self.config_service.current_config_id = new_id
            self.task_service.init_new_config()
            self.fs_signal_bus.fs_config_added.emit(new_id)
        return new_id

    def delete_config(self, config_id: str) -> bool:
        """删除配置"""
        # 如果该配置有运行器，先删除
        self.delete_runner(config_id)
        
        ok = self.config_service.delete_config(config_id)
        if ok:
            self.fs_signal_bus.fs_config_removed.emit(config_id)
        return ok

    def select_config(self, config_id: str) -> bool:
        """选择配置"""
        if not self.config_service.get_config(config_id):
            return False
        self.config_service.current_config_id = config_id
        return self.config_service.current_config_id == config_id

    def save_config(self, config_id: str) -> bool:
        """保存指定配置"""
        config = self.config_service.get_config(config_id)
        if config:
            return self.config_service.save_config(config_id, config)
        return False

    # ==================== 任务管理 ====================
    
    def get_tasks(self, config_id: str | None = None) -> List[TaskItem]:
        """获取指定配置的任务列表"""
        if config_id is None:
            return self.task_service.get_tasks()
        config = self.config_service.get_config(config_id)
        return config.tasks if config else []

    def get_task(self, task_id: str, config_id: str | None = None) -> TaskItem | None:
        """获取指定任务"""
        if config_id is None:
            return self.task_service.get_task(task_id)
        config = self.config_service.get_config(config_id)
        return config.get_task(task_id) if config else None

    def modify_task(self, task: TaskItem, idx: int = -2, save: bool = True) -> bool:
        """修改或添加任务
        
        Args:
            task: 任务对象
            idx: 插入位置索引
            save: 是否立即保存
        """
        ok = self.task_service.update_task(task, idx)
        if ok:
            self.fs_signal_bus.fs_task_modified.emit(task.item_id)
        return ok

    def update_task_checked(self, task_id: str, is_checked: bool) -> bool:
        """更新任务选中状态"""
        tasks = self.task_service.get_tasks()
        target_task = None
        for t in tasks:
            if t.item_id == task_id:
                t.is_checked = is_checked
                target_task = t
                break
        else:
            return False

        unchecked_tasks = []
        if target_task.is_special and is_checked:
            for t in tasks:
                if t.item_id != task_id and t.is_special and t.is_checked:
                    t.is_checked = False
                    unchecked_tasks.append(t)

        changed_tasks = [target_task] + unchecked_tasks
        ok = self.task_service.update_tasks(changed_tasks)
        if ok:
            for task in changed_tasks:
                self.signal_bus.task_updated.emit(task.item_id)
                self.fs_signal_bus.fs_task_modified.emit(task.item_id)
        return ok

    def modify_tasks(self, tasks: List[TaskItem]) -> bool:
        """批量修改任务"""
        if not tasks:
            return True
        ok = self.task_service.update_tasks(tasks)
        if ok:
            for t in tasks:
                self.fs_signal_bus.fs_task_modified.emit(t.item_id)
        return ok

    def delete_task(self, task_id: str) -> bool:
        """删除任务"""
        config = self.config_service.get_current_config()
        if not config:
            return False
        base_prefix = ("r_", "f_")
        for t in config.tasks:
            if t.item_id == task_id and t.item_id.startswith(base_prefix):
                return False
        ok = self.task_service.delete_task(task_id)
        if ok:
            self.fs_signal_bus.fs_task_removed.emit(task_id)
        return ok

    def select_task(self, task_id: str) -> bool:
        """选中任务"""
        selected = self.option_service.select_task(task_id)
        self.task_service._check_know_task()
        return selected

    def reorder_tasks(self, new_order: List[str]) -> bool:
        """重排任务顺序"""
        return self.task_service.reorder_tasks(new_order)

    # ==================== 选项管理 ====================
    
    def get_options(self, config_id: str | None = None, task_id: str | None = None) -> Dict[str, Any]:
        """获取指定任务的选项"""
        if config_id is None and task_id is None:
            return self.option_service.get_options()
        
        task = self.get_task(task_id, config_id) if task_id else None
        return task.task_option if task else {}

    def update_option(self, option_key: str, option_value: Any, save: bool = True) -> bool:
        """更新当前任务的选项"""
        return self.option_service.update_option(option_key, option_value)

    def update_options(self, options: Dict[str, Any], save: bool = True) -> bool:
        """批量更新当前任务的选项"""
        return self.option_service.update_options(options)

    def get_form_structure(self, task_id: str | None = None) -> Dict[str, Any] | None:
        """获取任务的表单结构"""
        if task_id is None:
            return self.option_service.get_form_structure()
        task = self.task_service.get_task(task_id)
        if task:
            return self.option_service.get_form_structure_by_task_name(
                task.name, self.task_service.interface
            )
        return None

    # ==================== 任务流执行（多运行器） ====================
    
    def create_task_flow(self, config_id: str | None = None) -> List[TaskItem]:
        """创建任务流，返回任务对象列表"""
        if config_id is None:
            config_id = self.current_config_id
        
        config = self.config_service.get_config(config_id)
        if not config:
            return []
        
        # 刷新隐藏标记
        self.task_service.refresh_hidden_flags()
        
        # 过滤出已选中且未隐藏的任务
        flow_tasks = [
            task for task in config.tasks
            if task.is_checked and not task.is_hidden
        ]
        
        return flow_tasks

    async def run_tasks_flow(
        self, 
        config_id: str | None = None, 
        task_id: str | None = None,
        start_task_id: str | None = None,
    ):
        """运行指定配置的任务流（支持多开）
        
        Args:
            config_id: 配置ID，如果为 None 则使用当前配置
            task_id: 指定只运行某个任务（可选）
            start_task_id: 从某个任务开始执行（可选）
        """
        if config_id is None:
            config_id = self.current_config_id
        
        if not config_id:
            raise ValueError("No config specified")
        
        # 获取运行器（自动创建如果不存在）
        runner = self.get_runner(config_id)
        state = self._runner_states[config_id]
        
        # 检查是否已经在运行
        if state.is_running:
            raise RuntimeError(f"配置 {config_id} 的任务流正在运行中")
        
        # 刷新隐藏标记
        try:
            self.task_service.refresh_hidden_flags()
        except Exception:
            pass
        
        # 标记为运行中
        state.mark_running()
        
        try:
            return await runner.run_tasks_flow(task_id, start_task_id=start_task_id)
        finally:
            state.mark_stopped()

    async def stop_task_flow(self, config_id: str | None = None):
        """停止指定配置的任务流"""
        if config_id is None:
            config_id = self.current_config_id
        
        if config_id in self._runners:
            runner = self._runners[config_id]
            return await runner.stop_task(manual=True)

    async def stop_task(self, config_id: str | None = None, *, manual: bool = False):
        """停止任务流"""
        if config_id is None:
            config_id = self.current_config_id
        
        if config_id in self._runners:
            runner = self._runners[config_id]
            return await runner.stop_task(manual=manual)

    # ==================== 兼容性属性（保持向后兼容） ====================
    
    @property
    def run_manager(self) -> 'TaskFlowRunner':
        """获取当前配置的运行器（向后兼容）"""
        return self.get_runner()

    @property
    def task_runner(self) -> 'TaskFlowRunner':
        """获取当前配置的运行器（向后兼容）"""
        return self.get_runner()

    @property
    def interface_obj(self) -> InterfaceManager:
        return self.interface_manager

    @property
    def interface(self) -> Dict[str, Any]:
        return self._interface

    # 注意：config 属性已重构为 ConfigInstanceManager（见 __init__）
    # 如需访问底层 ConfigService，请使用 config_service 属性

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

    # ==================== Bundle 管理 ====================
    
    def update_bundle_path(
        self, bundle_name: str, new_path: str, bundle_display_name: str | None = None
    ) -> bool:
        """更新 bundle 路径"""
        main_config_path = self.config_repo.main_config_path
        if not main_config_path.exists():
            logger.error(f"主配置文件不存在: {main_config_path}")
            return False

        try:
            with open(main_config_path, "r", encoding="utf-8") as f:
                config_data: Dict[str, Any] = jsonc.load(f)

            if "bundle" not in config_data:
                config_data["bundle"] = {}
            if not isinstance(config_data["bundle"], dict):
                config_data["bundle"] = {}

            if bundle_name not in config_data["bundle"]:
                config_data["bundle"][bundle_name] = {}

            bundle_info = config_data["bundle"][bundle_name]
            if not isinstance(bundle_info, dict):
                bundle_info = {}

            bundle_info["path"] = new_path
            if bundle_display_name is not None:
                bundle_info["name"] = bundle_display_name
            elif "name" not in bundle_info:
                bundle_info["name"] = bundle_name

            config_data["bundle"][bundle_name] = bundle_info

            with open(main_config_path, "w", encoding="utf-8") as f:
                jsonc.dump(config_data, f, indent=4, ensure_ascii=False)

            logger.info(f"已更新 bundle '{bundle_name}' 的路径为: {new_path}")
            return True

        except Exception as e:
            logger.error(f"更新 bundle 路径失败: {e}")
            return False

    def delete_bundle(self, bundle_name: str) -> bool:
        """删除 bundle"""
        try:
            main_config = self.config_service._main_config
        except AttributeError:
            logger.error("ConfigService 缺少 _main_config")
            return False

        if not isinstance(main_config, dict):
            return False

        bundle_dict = main_config.get("bundle")
        if not isinstance(bundle_dict, dict):
            return True

        if bundle_name not in bundle_dict:
            return True

        bundle_dict.pop(bundle_name, None)
        main_config["bundle"] = bundle_dict
        success = self.config_service.save_main_config()
        if success:
            logger.info(f"已从主配置中移除 bundle: {bundle_name}")
        return success

    # ==================== 内部方法 ====================
    
    def _connect_signals(self):
        """连接信号"""
        self.signal_bus.need_save.connect(self._on_need_save)
        signalBus.fs_reinit_requested.connect(self.reinit)

    def _on_config_changed(self, config_id: str):
        """配置变化回调"""
        if not config_id:
            return
        self._update_interface_path_for_config(config_id)
        self.task_service.on_config_changed(config_id)
        self.option_service.clear_selection()

    def _on_need_save(self):
        """保存请求回调"""
        self.config_service.save_main_config()
        self.signal_bus.config_saved.emit(True)

    def reinit(self):
        """重新初始化"""
        logger.info("开始重新初始化服务协调器...")
        try:
            self.config_repo.load_main_config()
            self.interface_manager.reload(self._interface_path)
            self._interface = self.interface_manager.get_interface()
            self.config_repo.interface = self._interface
            self.task_service.reload_interface(self._interface)

            current_config_id = self.config_service.current_config_id
            if current_config_id:
                self.signal_bus.config_changed.emit(current_config_id)

            logger.info("服务协调器重新初始化完成")
        except Exception as e:
            logger.error(f"重新初始化服务协调器失败: {e}")

    def get_pending_error_message(self) -> tuple[str, str] | None:
        """获取并清除待显示的错误信息"""
        if self._pending_error_message:
            msg = self._pending_error_message
            self._pending_error_message = None
            return msg
        return None

    # ==================== Interface 路径解析 ====================
    
    def _resolve_interface_path(
        self, main_config_path: Path, interface_path: Path | str | None
    ) -> Path | None:
        """解析 interface 路径"""
        if interface_path:
            return Path(interface_path)

        try:
            if not main_config_path.exists():
                return None

            with open(main_config_path, "r", encoding="utf-8") as f:
                main_cfg: Dict[str, Any] = jsonc.load(f)

            curr_config_id = main_cfg.get("curr_config_id")
            if curr_config_id:
                configs_dir = main_config_path.parent / "configs"
                curr_config_path = configs_dir / f"{curr_config_id}.json"
                if curr_config_path.exists():
                    try:
                        with open(curr_config_path, "r", encoding="utf-8") as cf:
                            curr_cfg: Dict[str, Any] = jsonc.load(cf)
                        raw_bundle = curr_cfg.get("bundle")
                        bundle_name = self._normalize_bundle_name(raw_bundle)
                        candidate = self._resolve_interface_path_from_bundle(bundle_name)
                        if candidate:
                            return candidate
                    except Exception as e:
                        logger.warning(f"解析 interface 路径失败: {e}")

            bundle = main_cfg.get("bundle")
            if isinstance(bundle, dict) and bundle:
                first_bundle_name = next(iter(bundle.keys()))
                bundle_info = bundle.get(first_bundle_name, {})
                bundle_path_str = bundle_info.get("path")
                if bundle_path_str:
                    base_dir = Path(bundle_path_str)
                    if not base_dir.is_absolute():
                        base_dir = Path.cwd() / base_dir

                    candidate = base_dir / "interface.jsonc"
                    if not candidate.exists():
                        candidate = base_dir / "interface.json"

                    if candidate.exists():
                        return candidate

            return None
        except Exception as e:
            logger.warning(f"解析 interface 路径失败: {e}")
            return None

    def _normalize_bundle_name(self, raw_bundle: Any) -> str | None:
        """标准化 bundle 名称"""
        if isinstance(raw_bundle, str):
            return raw_bundle or None
        if isinstance(raw_bundle, dict):
            if not raw_bundle:
                return None
            first_key = next(iter(raw_bundle.keys()))
            first_val = raw_bundle[first_key]
            if isinstance(first_val, dict) and "path" in first_val:
                return first_key
            return str(raw_bundle.get("name") or first_key)
        return None

    def _resolve_interface_path_from_bundle(self, bundle_name: str | None) -> Path | None:
        """从 bundle 解析 interface 路径"""
        if not bundle_name:
            return None

        try:
            bundle_info = None
            if hasattr(self, "config_service") and self.config_service:
                bundle_info = self.config_service.get_bundle(bundle_name)
            else:
                bundle_path_str = self._get_bundle_path_from_main_config(bundle_name)
                if not bundle_path_str:
                    return None
                bundle_info = {"path": bundle_path_str}
        except FileNotFoundError:
            return None

        bundle_path_str = str(bundle_info.get("path", ""))
        if not bundle_path_str:
            return None

        base_dir = Path(bundle_path_str)
        if not base_dir.is_absolute():
            base_dir = Path.cwd() / base_dir

        candidate = base_dir / "interface.jsonc"
        if not candidate.exists():
            candidate = base_dir / "interface.json"

        if candidate.exists():
            return candidate
        return None

    def _get_bundle_path_from_main_config(self, bundle_name: str) -> str | None:
        """从主配置获取 bundle 路径"""
        try:
            main_config_path = self._main_config_path
        except AttributeError:
            return None

        if not main_config_path or not main_config_path.exists():
            return None

        try:
            with open(main_config_path, "r", encoding="utf-8") as mf:
                main_cfg: Dict[str, Any] = jsonc.load(mf)
        except Exception:
            return None

        bundle_dict = main_cfg.get("bundle") or {}
        if not isinstance(bundle_dict, dict):
            return None

        bundle_info = bundle_dict.get(bundle_name)
        if isinstance(bundle_info, dict):
            return bundle_info.get("path")

        return None

    def _update_interface_path_for_config(self, config_id: str):
        """根据配置更新 interface 路径"""
        if not config_id:
            return

        config = self.config_service.get_config(config_id)
        if not config:
            return

        bundle_name = config.bundle
        if not bundle_name:
            return

        new_interface_path = self._resolve_interface_path_from_bundle(bundle_name)

        if new_interface_path and new_interface_path != self._interface_path:
            logger.info(f"切换 interface 路径: {self._interface_path} -> {new_interface_path}")
            self._reload_interface(new_interface_path)

    def _reload_interface(self, interface_path: Path | str | None):
        """重新加载 interface"""
        self._interface_path = interface_path
        self.interface_manager.reload(interface_path=self._interface_path)
        self._interface = self.interface_manager.get_interface()
        self.config_repo.interface = self._interface
        self.task_service.reload_interface(self._interface)

    def _cleanup_invalid_bundles(self) -> None:
        """清理无效的 bundle"""
        try:
            bundle_names = self.config_service.list_bundles()
        except Exception:
            return

        if not bundle_names:
            return

        invalid_bundles: list[str] = []
        for name in bundle_names:
            iface_path = self._resolve_interface_path_from_bundle(name)
            if iface_path is None:
                invalid_bundles.append(name)

        if not invalid_bundles:
            return

        try:
            main_cfg = self.config_service._main_config
        except AttributeError:
            return

        if not isinstance(main_cfg, dict):
            return

        bundle_dict = main_cfg.get("bundle") or {}
        if not isinstance(bundle_dict, dict):
            bundle_dict = {}

        for name in invalid_bundles:
            if name in bundle_dict:
                logger.info(f"移除无效 bundle: {name}")
                bundle_dict.pop(name, None)

        main_cfg["bundle"] = bundle_dict
        try:
            self.config_service.save_main_config()
        except Exception:
            pass

    def _handle_config_load_error(
        self, main_config_path: Path, configs_dir: Path, error: Exception
    ) -> bool:
        """处理配置加载错误"""
        try:
            logger.warning(f"检测到配置加载错误，开始重置: {error}")
            
            current_config_id = None
            bundle_name = None
            config_name = "Default Config"
            
            try:
                if hasattr(self, 'config_service') and self.config_service:
                    current_config_id = self.config_service.current_config_id
            except Exception:
                pass
            
            if not current_config_id:
                try:
                    if main_config_path.exists():
                        with open(main_config_path, "r", encoding="utf-8") as f:
                            main_config_data = jsonc.load(f)
                            current_config_id = main_config_data.get("curr_config_id")
                            if not bundle_name:
                                bundle_dict = main_config_data.get("bundle", {}) or {}
                                if bundle_dict:
                                    bundle_name = next(iter(bundle_dict.keys()), None)
                except Exception:
                    pass
            
            if current_config_id:
                config_file = configs_dir / f"{current_config_id}.json"
                if config_file.exists():
                    try:
                        with open(config_file, "r", encoding="utf-8") as cf:
                            try:
                                broken_config_data = jsonc.load(cf)
                                config_name = broken_config_data.get("name", "Default Config")
                                if not bundle_name:
                                    bundle_name = broken_config_data.get("bundle")
                            except:
                                pass
                    except:
                        pass
            
            if not bundle_name:
                bundle_name = self._interface.get("name", "Default Bundle")
            
            timestamp = int(time.time())
            backup_success = False
            broken_config_file = None
            
            if current_config_id:
                config_file = configs_dir / f"{current_config_id}.json"
                if config_file.exists():
                    try:
                        backup_path = config_file.with_suffix(f".broken.{timestamp}.json")
                        shutil.copy2(config_file, backup_path)
                        broken_config_file = config_file
                        backup_success = True
                    except Exception:
                        pass
            
            if not broken_config_file or not broken_config_file.exists():
                self._pending_error_message = ("error", f"Config load failed: {str(error)}")
                return False
            
            if not current_config_id:
                config_id_from_file = broken_config_file.stem
                if config_id_from_file.startswith("c_"):
                    current_config_id = config_id_from_file
                else:
                    current_config_id = ConfigItem.generate_id()
            
            if not bundle_name:
                bundle_name = self._interface.get("name", "Default Bundle")
            
            from app.common.constants import _RESOURCE_, _CONTROLLER_, POST_ACTION
            
            init_controller = self._interface.get("controller", [{}])[0].get("name", "")
            init_resource = self._interface.get("resource", [{}])[0].get("name", "")
            
            default_tasks = [
                TaskItem(
                    name="Controller",
                    item_id=_CONTROLLER_,
                    is_checked=True,
                    task_option={"controller_type": init_controller},
                    is_special=False,
                ),
                TaskItem(
                    name="Resource",
                    item_id=_RESOURCE_,
                    is_checked=True,
                    task_option={"resource": init_resource},
                    is_special=False,
                ),
                TaskItem(
                    name="Post-Action",
                    item_id=POST_ACTION,
                    is_checked=True,
                    task_option={},
                    is_special=False,
                ),
            ]
            
            default_config_item = ConfigItem(
                name=config_name,
                item_id=current_config_id,
                tasks=default_tasks,
                know_task=[],
                bundle=bundle_name,
            )
            
            try:
                config_data = default_config_item.to_dict()
                with open(broken_config_file, "w", encoding="utf-8") as f:
                    jsonc.dump(config_data, f, indent=4, ensure_ascii=False)
            except Exception:
                return False
            
            self.config_repo = JsonConfigRepository(
                main_config_path, configs_dir, interface=self._interface
            )
            
            if backup_success:
                self._pending_error_message = ("error", f"Config reset. Backup created. Error: {str(error)}")
            else:
                self._pending_error_message = ("error", f"Config reset. Error: {str(error)}")
            
            return True
            
        except Exception as e:
            self._pending_error_message = ("error", f"Config error handling failed: {str(e)}")
            return False
