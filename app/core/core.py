"""
服务协调器 - 核心模块

工作流程：
1. 启动后遍历所有配置，创建配置对象到存储池（ConfigEntry：任务列表来自 ConfigItem，任务流对象 Runner，监控目标即 Runner）
2. current_config_id 仅给前端标记「上次退出前使用的配置」；核心内部运行不读取，由前端在 run/stop 时传入 config_id
"""

from pathlib import Path
from typing import List, Dict, Any, Optional, TYPE_CHECKING
from dataclasses import dataclass
from datetime import datetime
import time
import shutil

import jsonc

from PySide6.QtCore import QTimer

from app.core.Item import (
    CoreSignalBus,
    ConfigItem,
    TaskItem,
)
from app.core.service.Config_Service import ConfigService, JsonConfigRepository
from app.core.service.Schedule_Service import ScheduleService
from app.core.service.Task_Service import TaskService
from app.core.service.Option_Service import OptionService
from app.core.service.Bundle_Service import BundleService
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


# ==================== 配置池条目 ====================
@dataclass
class ConfigEntry:
    """单个配置在核心中的条目：含任务流对象与运行状态，任务列表与配置数据由 ConfigService 按 config_id 提供；监控目标即本条目中的 runner。"""
    config_id: str
    runner: 'TaskFlowRunner'
    state: RunnerState


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
        # 初始化统一的信号总线（合并了 CoreSignalBus 和 FromeServiceCoordinator）
        self.signal_bus = CoreSignalBus()
        # fs_signal_bus 现在指向同一个信号总线（向后兼容）
        self.fs_signal_bus = self.signal_bus
        
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

        # Bundle 服务（从 ServiceCoordinator 分离）
        self.bundle_service = BundleService(
            main_config_path=main_config_path,
            get_main_config=lambda: self.config_service._main_config,
            save_main_config=self.config_service.save_main_config,
        )

        # ==================== 配置池（多开） ====================
        # 每个 config_id 对应一个 ConfigEntry（任务流 + 状态）；任务列表来自 config_service.get_config(config_id).tasks；监控目标即 entry.runner
        self._config_pool: Dict[str, ConfigEntry] = {}

        # 调度服务
        schedule_store = main_config_path.parent / "schedules.json"
        self.schedule_service = ScheduleService(self, schedule_store)

        # 日志处理器
        self.log_processor = CallbackLogProcessor()

        # 连接信号
        self._connect_signals()

        # 清理无效的 bundle 索引
        self._cleanup_invalid_bundles()

        # 应用启动时为所有已加载的配置预建运行器（监控目标）
        self._ensure_runners_for_all_configs()

    def _ensure_runners_for_all_configs(self) -> None:
        """启动时遍历所有配置，创建配置对象到存储池（含任务流与监控目标）"""
        try:
            configs = self.config_service.list_configs()
            for summary in configs:
                config_id = summary.get("item_id") if isinstance(summary, dict) else None
                if not config_id:
                    continue
                if config_id not in self._config_pool:
                    try:
                        self.create_runner_for_config(config_id)
                        logger.debug(f"启动时加入配置池: {config_id}")
                    except Exception as e:
                        logger.warning(f"加入配置池失败 {config_id}: {e}")
        except Exception as e:
            logger.warning(f"配置池初始化异常: {e}")

    # ==================== 运行器管理（多运行器支持） ====================
    
    def get_runner(self, config_id: str | None = None) -> 'TaskFlowRunner':
        """获取指定配置的运行器（池中无则按需创建；仅用于前端按 config_id 取运行器/监控目标）
        
        Args:
            config_id: 配置ID；为 None 时使用 current_config_id（仅用于兼容前端「当前选中」场景）
        """
        if config_id is None:
            config_id = self.current_config_id
        if not config_id:
            raise ValueError("No config_id specified and no current config")
        if config_id not in self._config_pool:
            return self.create_runner_for_config(config_id)
        entry = self._config_pool[config_id]
        entry.state.last_used = datetime.now()
        return entry.runner

    def create_runner_for_config(self, config_id: str) -> 'TaskFlowRunner':
        """为指定配置创建运行器并加入配置池（任务流 + 监控目标）"""
        if config_id in self._config_pool:
            return self._config_pool[config_id].runner
        config = self.config_service.get_config(config_id)
        if not config:
            raise ValueError(f"配置 {config_id} 不存在")
        from app.core.runner.task_flow import TaskFlowRunner
        runner = TaskFlowRunner(
            task_service=self.task_service,
            config_service=self.config_service,
            fs_signal_bus=self.fs_signal_bus,
            config_id=config_id,
            service_coordinator=self,
        )
        state = RunnerState()
        self._config_pool[config_id] = ConfigEntry(config_id=config_id, runner=runner, state=state)
        logger.debug(f"配置池已加入: {config_id}")
        return runner

    def delete_runner(self, config_id: str) -> bool:
        """从配置池移除指定配置的运行器"""
        if config_id not in self._config_pool:
            return False
        entry = self._config_pool.pop(config_id)
        if hasattr(entry.runner, 'cleanup'):
            try:
                entry.runner.cleanup()
            except Exception as e:
                logger.warning(f"清理运行器失败: {e}")
        return True

    def is_running(self, config_id: str) -> bool:
        """检查指定配置是否正在运行（需传入 config_id，核心不读 current_config_id）"""
        if config_id not in self._config_pool:
            return False
        return self._config_pool[config_id].state.is_running

    def get_running_configs(self) -> List[str]:
        """获取所有正在运行的配置ID列表"""
        return [
            cid for cid, entry in self._config_pool.items()
            if entry.state.is_running
        ]

    # ==================== 属性访问接口 ====================
    
    @property
    def current_config_id(self) -> str:
        """当前配置ID：仅给前端标记「上次退出前使用的配置」；核心内部 run/stop 不读取，由前端传入 config_id。"""
        return self.config_service.current_config_id

    @current_config_id.setter
    def current_config_id(self, value: str) -> None:
        """设置当前配置ID（前端切换配置时写入，会落盘）"""
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
        """添加配置，返回新配置ID。
        
        多开模式：配置创建时同步创建该配置的任务流运行器，
        监控界面切换配置时直接绑定对应运行器即可。
        """
        new_id = self.config_service.create_config(config_item)
        if new_id:
            # 静默设置当前配置ID，避免触发回调导致 _check_know_task 被调用两次
            # （init_new_config 会调用 _check_know_task，不需要回调再调用一次）
            self.config_service.set_current_config_id_silent(new_id)
            
            # 初始化新配置的任务（会调用 _check_know_task）
            self.task_service.init_new_config()
            
            # 配置创建时同步创建该配置的运行器（任务流 + 监控目标）
            try:
                self.create_runner_for_config(new_id)
                logger.debug(f"配置 {new_id} 已同步创建运行器")
            except Exception as e:
                logger.warning(f"配置创建时创建运行器失败: {e}")
            
            # 发出配置添加信号，UI会响应并选中新配置
            self.fs_signal_bus.fs_config_added.emit(new_id)
            # 发出配置切换信号，通知其他组件
            self.signal_bus.config_changed.emit(new_id)
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

    def update_task_for_config(self, config_id: str, task: TaskItem) -> bool:
        """更新指定配置的任务（多开模式专用）
        
        Args:
            config_id: 配置ID
            task: 任务对象
            
        Returns:
            bool: 更新是否成功
        """
        if not config_id:
            return False
        
        config = self.config_service.get_config(config_id)
        if not config:
            return False
        
        # 在配置中查找并更新任务
        for i, t in enumerate(config.tasks):
            if t.item_id == task.item_id:
                config.tasks[i] = task
                # 保存配置
                return self.config_service.update_config(config_id, config)
        
        # 如果任务不存在，添加到配置中
        config.tasks.append(task)
        return self.config_service.update_config(config_id, config)

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
    
    def create_task_flow(self, config_id: str) -> List[TaskItem]:
        """创建指定配置的任务流列表（需传入 config_id）"""
        config = self.config_service.get_config(config_id)
        if not config:
            return []
        try:
            self.task_service.refresh_hidden_flags()
        except Exception:
            pass
        return [
            task for task in config.tasks
            if task.is_checked and not task.is_hidden
        ]

    async def run_tasks_flow(
        self,
        config_id: str | None = None,
        task_id: str | None = None,
        start_task_id: str | None = None,
    ):
        """运行指定配置的任务流（多开）。核心不读 current_config_id，必须由前端传入 config_id。"""
        if config_id is None or not config_id:
            raise ValueError("config_id is required for run_tasks_flow (provided by frontend)")
        if config_id not in self._config_pool:
            self.create_runner_for_config(config_id)
        entry = self._config_pool[config_id]
        if entry.state.is_running:
            raise RuntimeError(f"配置 {config_id} 的任务流正在运行中")
        try:
            self.task_service.refresh_hidden_flags()
        except Exception:
            logger.warning("刷新任务隐藏状态失败")
        entry.state.mark_running()
        try:
            return await entry.runner.run_tasks_flow(task_id, start_task_id=start_task_id)
        finally:
            entry.state.mark_stopped()

    async def stop_task_flow(self, config_id: str | None = None):
        """停止指定配置的任务流。必须由前端传入 config_id。"""
        if config_id is None or not config_id:
            raise ValueError("config_id is required for stop_task_flow (provided by frontend)")
        if config_id in self._config_pool:
            return await self._config_pool[config_id].runner.stop_task(manual=True)

    async def stop_task(self, config_id: str | None = None, *, manual: bool = False):
        """停止指定配置的任务流。必须由前端传入 config_id。"""
        if config_id is None or not config_id:
            raise ValueError("config_id is required for stop_task (provided by frontend)")
        if config_id in self._config_pool:
            return await self._config_pool[config_id].runner.stop_task(manual=manual)

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
    def fs_signals(self) -> CoreSignalBus:
        """获取信号总线（已弃用，请使用 signals 属性）
        
        为保持向后兼容，此属性现在返回统一的信号总线。
        fs_ 开头的信号仍然可用。
        """
        return self.signal_bus

    @property
    def signals(self) -> CoreSignalBus:
        """获取统一信号总线"""
        return self.signal_bus

    # ==================== Bundle 管理（委托给 BundleService） ====================
    
    def update_bundle_path(
        self, bundle_name: str, new_path: str, bundle_display_name: str | None = None
    ) -> bool:
        """更新 bundle 路径（委托给 BundleService）"""
        return self.bundle_service.update_bundle_path(bundle_name, new_path, bundle_display_name)

    def delete_bundle(self, bundle_name: str) -> bool:
        """删除 bundle（委托给 BundleService）"""
        return self.bundle_service.delete_bundle(bundle_name)

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
        """清理无效的 bundle（委托给 BundleService）"""
        self.bundle_service.cleanup_invalid_bundles(self._resolve_interface_path_from_bundle)

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
                    except Exception as backup_error:
                        logger.exception("Failed to backup broken config file %s: %s", config_file, backup_error)
            
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
