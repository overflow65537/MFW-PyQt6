from pathlib import Path
from typing import List, Dict, Any

from qasync import asyncSlot

from .Item import (
    CoreSignalBus,
    FromeServiceCoordinator,
    ConfigItem,
    TaskItem,
)
from .service.Config_Service import ConfigService, JsonConfigRepository
from .service.Task_Service import TaskService
from .service.Option_Service import OptionService
from .runner.maafw import MaaFW
from .runner.maasink import (
    MaaContextSink,
    MaaControllerEventSink,
    MaaResourceEventSink,
    MaaTaskerEventSink,
)

from app.common.constants import PRE_CONFIGURATION

from ..utils.logger import logger


class ServiceCoordinator:
    """服务协调器，整合配置、任务和选项服务"""

    def __init__(self, main_config_path: Path, configs_dir: Path | None = None):
        # 初始化停止标志
        self.need_stop = False

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

        # 运行器
        self.maafw = MaaFW(
            maa_context_sink=MaaContextSink,
            maa_controller_sink=MaaControllerEventSink,
            maa_resource_sink=MaaResourceEventSink,
            maa_tasker_sink=MaaTaskerEventSink,
        )
        # 连接信号
        self._connect_signals()

    def _connect_signals(self):
        """连接所有信号"""
        # UI请求保存配置
        self.signal_bus.need_save.connect(self._on_need_save)

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

    # endregion

    # region 任务相关方法

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
        for i, t in enumerate(config.tasks):
            if t.item_id == task.item_id:
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
        self.task_service._check_know_task()

    def reorder_tasks(self, new_order: List[str]) -> bool:
        """任务顺序更改，new_order 为 task_id 列表（新顺序）"""
        return self.task_service.reorder_tasks(new_order)

    # endregion
    def _on_need_save(self):
        """当UI请求保存时保存所有配置"""
        self.config_service.save_main_config()
        self.signal_bus.config_saved.emit(True)

    # region 运行相关方法

    async def run_tasks_flow(self):
        """
        任务完整流程：启动子进程、加载资源、连接设备、启动模拟器、批量运行任务
        """
        self.need_stop = False  # 重置停止标志
        try:
            self.fs_signal_bus.fs_start_button_status.emit(
                {"text": "STOP", "status": "disabled"}
            )

            # 1. 获取并处理预配置任务
            from app.common.constants import PRE_CONFIGURATION, POST_ACTION

            pre_cfg = self.task_service.get_task(PRE_CONFIGURATION)
            if not pre_cfg:
                raise ValueError("未找到基础预配置任务")

            # 2. 连接设备
            logger.info("开始连接设备...")
            # 控制器配置包含在 Pre-Configuration 任务中
            connected = await self.connect_device(pre_cfg.task_option)
            if not connected:
                logger.error("设备连接失败，流程终止")
                return
            logger.info("设备连接成功")

            # 3. 加载资源
            logger.info("开始加载资源...")
            if not await self.load_resources(pre_cfg.task_option):
                logger.error("资源加载失败，流程终止")
                return
            logger.info("资源加载成功")

            # 解锁停止按钮
            self.fs_signal_bus.fs_start_button_status.emit(
                {"text": "STOP", "status": "enabled"}
            )

            # 4. 运行所有已选中的任务
            logger.info("开始执行任务序列...")
            for task in self.task_service.current_tasks:
                # 跳过预配置和控制器基础任务，以及未选中的任务
                if task.name in [PRE_CONFIGURATION, POST_ACTION]:
                    continue

                if task.is_checked:
                    logger.info(f"开始执行任务: {task.name}")
                    try:
                        await self.run_task(task.item_id)
                        logger.info(f"任务执行完成: {task.name}")
                    except Exception as e:
                        logger.error(f"任务执行失败: {task.name}, 错误: {str(e)}")

                if self.need_stop:
                    logger.info("收到停止请求，流程终止")
                    break

        except Exception as e:
            logger.error(f"任务流程执行异常: {str(e)}")
            import traceback

            logger.critical(traceback.format_exc())
        finally:
            await self.stop_task()

    async def connect_device(self, controller_raw: Dict[str, Any]):
        """连接 MaaFW"""
        if self._get_controller_type(controller_raw) == "adb":
            return await self._connect_adb_controller(controller_raw)

        elif self._get_controller_type(controller_raw) == "win":
            return await self._connect_win32_controller(controller_raw)
        else:
            raise ValueError("不支持的控制器类型")

    async def load_resources(self, resource_raw: Dict[str, Any]):
        """加载资源"""
        if self.maafw.resource:
            self.maafw.resource.clear()  # 清除资源

        # 处理两种情况：配置文件场景和 UI 表单场景
        # 配置文件场景：resource 直接是字符串
        # UI 表单场景：resource 是包含 value 字段的字典
        resource = resource_raw.get("resource", {})
        if isinstance(resource, str):
            resource_target = resource
        elif isinstance(resource, dict):
            resource_target = resource.get("value")
        else:
            resource_target = None

        resource_path = []

        # 如果没有找到资源目标，尝试直接从配置中获取 resource_path（用于配置文件场景）
        if not resource_target:
            logger.warning("未找到资源目标，尝试直接从配置中获取资源路径")
            # 配置文件中可能直接包含 resource_path 字段
            resource_path = resource_raw.get("resource_path", [])
        else:
            for i in self.task_service.interface.get("resource", []):
                if i["name"] == resource_target:
                    logger.debug(f"加载资源: {i['path']}")
                    resource_path = i["path"]
                    break  # 找到后停止遍历

        if resource_path == [] or self.need_stop:
            logger.error(f"未找到目标资源: {resource_target}")
            await self.maafw.stop_task()
            return False

        for i in resource_path:
            cwd = Path.cwd()
            path_str = str(i)
            if len(path_str) >= 2 and path_str[1] == ":" and path_str[0].isalpha():
                resource = Path(path_str).resolve()
            else:
                normalized = path_str.lstrip("\\/")
                resource = (cwd / normalized).resolve()

            logger.debug(f"加载资源: {resource}")
            res_cfg = self.task_service.get_task(PRE_CONFIGURATION)
            if res_cfg is None:
                gpu_idx = -1
            else:
                gpu_idx = res_cfg.task_option.get("gpu", -1)
            await self.maafw.load_resource(resource, gpu_idx)
            logger.debug(f"资源加载完成: {resource}")
        return True

    async def run_task(self, task_id: str):
        """运行任务列表"""

        task_item = self.task_service.get_task(task_id)
        if not task_item:
            logger.error(f"任务 ID '{task_id}' 不存在")
            return

        elif not task_item.is_checked:
            logger.warning(f"任务 '{task_item.name}' 未被选中，跳过执行")
            return

        raw_info = self.task_service.get_task_execution_info(task_id)
        if raw_info is None:
            logger.error(f"无法获取任务 '{task_item.name}' 的执行信息")
            return

        entry, pipeline_override = raw_info.get("entry", ""), raw_info.get(
            "pipeline_override", {}
        )

        await self.maafw.run_task(entry, pipeline_override)

    async def stop_task(self):
        """停止当前任务"""
        if self.need_stop:
            return
        self.need_stop = True
        self.fs_signal_bus.fs_start_button_status.emit(
            {"text": "STOP", "status": "disabled"}
        )
        await self.maafw.stop_task()
        self.fs_signal_bus.fs_start_button_status.emit(
            {"text": "START", "status": "enabled"}
        )

    async def _connect_adb_controller(self, controller_raw: Dict[str, Any]):
        """
        连接 ADB 控制器
        """
        if not isinstance(controller_raw, dict):
            logger.error(
                f"控制器配置格式错误(ADB)，期望 dict，实际 {type(controller_raw)}: {controller_raw}"
            )
            return False
        # 从 controller_raw 中提取 ADB 配置
        activate_controller = controller_raw.get("controller_type")

        if activate_controller is None:
            logger.error(f"未找到控制器配置: {controller_raw}")
            return False

        adb_path = controller_raw.get(activate_controller, {}).get("adb_path", "")
        address = controller_raw.get(activate_controller, {}).get("address", "")
        input_method = int(
            controller_raw.get(activate_controller, {}).get("input_methods", -1)
        )
        if input_method == 18446744073709551615:
            input_method = -1

        screen_method = int(
            controller_raw.get(activate_controller, {}).get("screencap_methods", -1)
        )
        config = controller_raw.get(activate_controller, {}).get("config", {})
        logger.debug(
            f"ADB 参数类型: adb_path={type(adb_path)}, address={type(address)}, "
            f"screen_method={screen_method}({type(screen_method)}), "
            f"input_method={input_method}({type(input_method)})"
        )

        # 尝试连接 ADB
        if (
            not await self.maafw.connect_adb(
                adb_path,
                address,
                screen_method,
                input_method,
                config,
            )
            and not self.need_stop
        ):
            return False
        return True

    async def _connect_win32_controller(self, controller_raw: Dict[str, Any]):
        """
        连接 Win32 控制器
        """
        hwnd: int = controller_raw.get("hwnd", 0)
        screencap_method: int = controller_raw.get("screencap_method", 0)
        mouse_method: int = controller_raw.get("screencap_method", 0)
        keyboard_method: int = controller_raw.get("keyboard_method", 0)

        # 直接调用 MaaFW 的连接方法
        if (
            not await self.maafw.connect_win32hwnd(
                hwnd,
                screencap_method,
                mouse_method,
                keyboard_method,
            )
            and not self.need_stop
        ):
            return False
        return True

    def _get_controller_type(self, controller_raw: Dict[str, Any]) -> str:
        """获取控制器类型"""
        if not isinstance(controller_raw, dict):
            raise TypeError(
                f"controller_raw 类型错误，期望 dict，实际 {type(controller_raw)}: {controller_raw}"
            )

        # 从控制器配置中获取控制器名称
        controller_config = controller_raw.get("controller_type", {})

        # 处理两种情况：
        # 1. controller_config 是字符串
        # 2. controller_config 是字典，包含 value 字段（UI 表单场景）
        if isinstance(controller_config, str):
            controller_name = controller_config
        elif isinstance(controller_config, dict):
            controller_name = controller_config.get("value", "")
        else:
            controller_name = ""

        # 查找控制器类型
        controller_name = controller_name.lower()
        for controller in self.task_service.interface.get("controller", []):
            if controller.get("name", "").lower() == controller_name:
                return controller.get("type", "").lower()

        # 如果仍然没有找到，抛出错误
        raise ValueError(f"未找到控制器类型: {controller_raw}")

    # endregion
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
