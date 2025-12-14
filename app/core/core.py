from pathlib import Path
from typing import List, Dict, Any

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
from app.core.runner.task_flow import TaskFlowRunner
from app.utils.logger import logger
from app.common.signal_bus import signalBus


class ServiceCoordinator:
    """服务协调器，整合配置、任务和选项服务"""

    def __init__(
        self,
        main_config_path: Path,
        configs_dir: Path | None = None,
        interface_path: Path | str | None = None,
    ):
        # 初始化信号总线
        self.signal_bus = CoreSignalBus()
        self.fs_signal_bus = FromeServiceCoordinator()
        self._interface_path = Path(interface_path) if interface_path else None

        # 确定配置目录
        if configs_dir is None:
            configs_dir = main_config_path.parent / "configs"

        # 生成 interface 并传递给服务
        self.interface_manager: InterfaceManager = get_interface_manager(
            interface_path=self._interface_path
        )
        self._interface: Dict = self.interface_manager.get_interface()

        # 初始化存储库和服务
        self.config_repo = JsonConfigRepository(
            main_config_path, configs_dir, interface=self._interface
        )
        self.config_service = ConfigService(self.config_repo, self.signal_bus)
        self.task_service = TaskService(
            self.config_service, self.signal_bus, self._interface
        )
        self.option_service = OptionService(self.task_service, self.signal_bus)
        self.config_service.register_on_change(self._on_config_changed)

        # 运行器

        self.task_runner = TaskFlowRunner(
            task_service=self.task_service,
            config_service=self.config_service,
            fs_signal_bus=self.fs_signal_bus,
        )
        schedule_store = main_config_path.parent / "schedules.json"
        self.schedule_service = ScheduleService(self, schedule_store)

        # 连接信号
        self._connect_signals()

    def _connect_signals(self):
        """连接所有信号"""
        # UI请求保存配置
        self.signal_bus.need_save.connect(self._on_need_save)
        # 热更新完成后重新初始化
        signalBus.fs_reinit_requested.connect(self.reinit)

    def _on_config_changed(self, config_id: str):
        """配置变化后刷新内部服务状态"""
        if not config_id:
            return
        self.task_service.on_config_changed(config_id)
        self.option_service.clear_selection()

    # region 配置相关方法
    def add_config(self, config_item: ConfigItem) -> str:
        """添加配置，传入 ConfigItem 对象，返回新配置ID"""
        new_id = self.config_service.create_config(config_item)
        if new_id:
            # Select the new config
            self.config_service.current_config_id = new_id

            # Initialize the new config with tasks from interface
            self.task_service.init_new_config()

            # Notify UI incrementally
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
        if not self.config_service.get_config(config_id):
            return False

        # 使用 ConfigService setter，回调将同步任务和选项
        self.config_service.current_config_id = config_id
        return self.config_service.current_config_id == config_id

    # endregion

    # region 任务相关方法

    def modify_task(self, task: TaskItem) -> bool:
        """修改或添加任务：传入 TaskItem，如果列表中没有对应 id 的任务，添加到倒数第2位，否则更新对应任务"""
        ok = self.task_service.update_task(task)
        if ok:
            self.fs_signal_bus.fs_task_modified.emit(task)
        return ok

    def update_task_checked(self, task_id: str, is_checked: bool) -> bool:
        """更新任务选中状态并处理特殊任务互斥"""
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
                # UI 通知：保持与旧行为兼容
                self.signal_bus.task_updated.emit(task)
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

    def select_task(self, task_id: str) -> bool:
        """选中任务，传入 task id，并自动检查已知任务"""
        selected = self.option_service.select_task(task_id)
        self.task_service._check_know_task()
        return selected

    def reorder_tasks(self, new_order: List[str]) -> bool:
        """任务顺序更改，new_order 为 task_id 列表（新顺序）"""
        return self.task_service.reorder_tasks(new_order)

    # endregion
    def _on_need_save(self):
        """当UI请求保存时保存所有配置"""
        self.config_service.save_main_config()
        self.signal_bus.config_saved.emit(True)

    def reinit(self):
        """重新初始化服务协调器，用于热更新完成后刷新资源"""
        logger.info("开始重新初始化服务协调器...")
        try:
            # 重新加载主配置
            self.config_repo.load_main_config()

            # 刷新 interface 数据
            self.interface_manager.reload(self._interface_path)
            self._interface = self.interface_manager.get_interface()
            self.config_repo.interface = self._interface

            # 重新初始化任务服务（刷新 interface 数据）
            self.task_service.reload_interface(self._interface)

            # 通知 UI 配置已更新
            current_config_id = self.config_service.current_config_id
            if current_config_id:
                self.signal_bus.config_changed.emit(current_config_id)

            logger.info("服务协调器重新初始化完成")
        except Exception as e:
            logger.error(f"重新初始化服务协调器失败: {e}")

    async def run_tasks_flow(self, task_id: str | None = None, is_timeout_restart: bool = False):
        return await self.task_runner.run_tasks_flow(task_id, is_timeout_restart=is_timeout_restart)

    async def stop_task(self):
        return await self.task_runner.stop_task()

    @property
    def run_manager(self) -> TaskFlowRunner:
        return self.task_runner

    # 提供获取服务的属性，以便UI层访问
    @property
    def interface_obj(self) -> InterfaceManager:
        return self.interface_manager

    @property
    def interface(self) -> Dict[str, Any]:
        """返回当前加载的 interface 字典"""
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
    def fs_signals(self) -> FromeServiceCoordinator:
        return self.fs_signal_bus

    @property
    def signals(self) -> CoreSignalBus:
        return self.signal_bus
