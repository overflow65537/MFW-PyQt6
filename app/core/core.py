from pathlib import Path
from typing import List, Dict, Any, Optional

from ..utils.logger import logger
from ..core.service import (
    JsonConfigRepository,
    ConfigService,
    TaskService,
    OptionService,
    CoreSignalBus,
    FromeServiceCoordinator,
    ConfigItem,
    TaskItem,
)

from ..core.maafw import MaaFW, MaaFWSignal


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

        # 初始化 MaaFW 运行器
        self.maafw = MaaFW()

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

    # MaaFW 运行器控制方法
    async def load_resource(self) -> bool:
        """加载资源

        从当前配置中读取资源名称，然后从 interface 中找到对应的资源路径，
        使用 bundle 中的 path 替换占位符，按顺序依次加载资源。

        Args:
            gpu_index: GPU 索引，-2=CPU，-1=自动，>=0=指定GPU。
                      如果为 -1（默认值），则从配置中读取 GPU 设置。

        Returns:
            bool: 所有资源加载成功返回 True
        """
        # 获取当前配置
        config = self.config_service.get_current_config()
        if not config:
            logger.error("未找到当前配置")
            return False

        # 从任务选项中获取资源名称和 GPU 设置（从资源设置任务 r_ 开头的任务中获取）
        resource_name = None
        gpu_index = -1
        for task in config.tasks:
            if task.item_id.startswith("r_"):
                resource_name = task.task_option.get("resource", "")

                saved_gpu = task.task_option.get("gpu")

                if saved_gpu is not None:
                    try:
                        gpu_index = int(saved_gpu)
                        logger.info(f"从配置读取 GPU 设置: {gpu_index}")
                    except (ValueError, TypeError):
                        logger.warning(f"GPU 配置值无效: {saved_gpu}，使用默认值 -1")
                        gpu_index = -1
                break

        if not resource_name:
            logger.error("配置中未找到资源设置")
            return False

        # 获取 interface 配置
        interface = self.task_service.interface
        if not interface:
            logger.error("Interface 未加载")
            return False

        # 从 interface 中查找对应的资源
        resource_config = None
        for resource in interface.get("resource", []):
            if resource.get("name") == resource_name:
                resource_config = resource
                break

        if not resource_config:
            logger.error(f"在 interface 中未找到资源: {resource_name}")
            return False

        # 获取资源路径列表
        resource_paths = resource_config.get("path", [])
        if not resource_paths:
            logger.error(f"资源 {resource_name} 没有配置路径")
            return False

        # 获取 bundle path 用于替换占位符
        bundle = config.bundle
        bundle_path = bundle.get("path", "./") if isinstance(bundle, dict) else "./"

        # 替换占位符并加载资源
        for path in resource_paths:
            # 替换 {PROJECT_DIR} 占位符
            resolved_path = path.replace("{PROJECT_DIR}", bundle_path)

            logger.info(f"加载资源: {resolved_path}")

            # 调用 MaaFW 加载资源
            success = await self.maafw.load_resource(resolved_path, gpu_index=gpu_index)
            if not success:
                logger.error(f"资源加载失败: {resolved_path}")
                return False

        logger.info(f"所有资源加载成功 ({len(resource_paths)} 个)")
        return True

    def unload_resource(self):
        """删除/卸载资源"""
        self.maafw.resource = None

    async def connect_adb(
        self,
        adb_path: str,
        address: str,
        screencap_method: int,
        input_method: int,
        config: Optional[Dict] = None,
    ) -> bool:
        """连接 ADB 设备

        Args:
            adb_path: ADB 可执行文件路径
            address: 设备地址
            screencap_method: 截图方法
            input_method: 输入方法
            config: 配置字典

        Returns:
            bool: 连接成功返回 True
        """
        if config is None:
            config = {}
        return await self.maafw.connect_adb(
            adb_path, address, screencap_method, input_method, config
        )

    async def connect_win32(
        self, hwnd: int | str, screencap_method: int, input_method: int
    ) -> bool:
        """连接 Win32 窗口

        Args:
            hwnd: 窗口句柄（整数或十六进制字符串）
            screencap_method: 截图方法
            input_method: 输入方法

        Returns:
            bool: 连接成功返回 True
        """
        return await self.maafw.connect_win32hwnd(hwnd, screencap_method, input_method)

    def disconnect(self):
        """断开控制器连接"""
        self.maafw.controller = None

    def start_agent(
        self, child_exec: str, child_args: List[str], resource_path: str
    ) -> bool:
        """启动 Agent

        Args:
            child_exec: Agent 可执行文件路径
            child_args: Agent 启动参数列表
            resource_path: 资源路径

        Returns:
            bool: 启动并连接成功返回 True
        """
        return self.maafw.start_agent(child_exec, child_args, resource_path)

    async def run_task(
        self, entry: str, pipeline_override: Optional[Dict[str, Any]] = None
    ) -> bool:
        """运行任务

        Args:
            entry: 任务入口
            pipeline_override: Pipeline 覆盖参数

        Returns:
            bool: 任务启动成功返回 True
        """
        if pipeline_override is None:
            pipeline_override = {}
        return await self.maafw.run_task(entry, pipeline_override)

    async def run_task_by_id(self, task_id: str) -> bool:
        """通过任务 ID 运行任务

        这是一个便捷方法，自动获取任务的 entry 和 pipeline_override

        Args:
            task_id: 任务 ID

        Returns:
            bool: 任务启动成功返回 True
        """
        # 获取任务执行信息
        exec_info = self.task_service.get_task_execution_info(task_id)
        if not exec_info:
            return False

        # 运行任务
        return await self.run_task(exec_info["entry"], exec_info["pipeline_override"])

    async def stop_task(self):
        """停止任务"""
        await self.maafw.stop_task()

    def set_save_draw(self, save_draw: bool):
        """设置是否保存绘制结果

        Args:
            save_draw: 是否保存
        """
        self.maafw.set_save_draw(save_draw)

    def set_recording(self, recording: bool):
        """设置是否录制

        Args:
            recording: 是否录制
        """
        self.maafw.set_recording(recording)

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

    @property
    def runner(self) -> MaaFW:
        return self.maafw

    @property
    def runner_signals(self) -> MaaFWSignal:
        return self.maafw.signal
