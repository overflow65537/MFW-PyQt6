import time
from pathlib import Path
from typing import Any, Dict

from app.common.constants import POST_ACTION, PRE_CONFIGURATION
from app.common.signal_bus import signalBus

from ...utils.logger import logger
from ..service.Task_Service import TaskService
from .maafw import MaaFW
from .maasink import (
    MaaContextSink,
    MaaControllerEventSink,
    MaaResourceEventSink,
    MaaTaskerEventSink,
)


class TaskFlowRunner:
    """负责执行任务流的运行时组件"""

    def __init__(
        self,
        task_service: TaskService,
        fs_signal_bus,
    ):
        self.task_service = task_service
        self.maafw = MaaFW(
            maa_context_sink=MaaContextSink,
            maa_controller_sink=MaaControllerEventSink,
            maa_resource_sink=MaaResourceEventSink,
            maa_tasker_sink=MaaTaskerEventSink,
        )
        self.fs_signal_bus = fs_signal_bus
        self.need_stop = False

    async def run_tasks_flow(self):
        """任务完整流程：连接设备、加载资源、批量运行任务"""
        self.need_stop = False
        try:
            self.fs_signal_bus.fs_start_button_status.emit(
                {"text": "STOP", "status": "disabled"}
            )

            pre_cfg = self.task_service.get_task(PRE_CONFIGURATION)
            if not pre_cfg:
                raise ValueError("未找到基础预配置任务")

            logger.info("开始连接设备...")
            connected = await self.connect_device(pre_cfg.task_option)
            if not connected:
                logger.error("设备连接失败，流程终止")
                return
            logger.info("设备连接成功")

            logger.info("开始截图测试...")
            start_time = time.time()
            await self.maafw.screencap_test()
            end_time = time.time()
            logger.info(f"截图测试成功，耗时: {end_time - start_time}毫秒")
            signalBus.callback.emit(
                {"name": "speed_test", "details": end_time - start_time}
            )

            logger.info("开始加载资源...")
            if not await self.load_resources(pre_cfg.task_option):
                logger.error("资源加载失败，流程终止")
                return
            logger.info("资源加载成功")

            self.fs_signal_bus.fs_start_button_status.emit(
                {"text": "STOP", "status": "enabled"}
            )

            logger.info("开始执行任务序列...")
            for task in self.task_service.current_tasks:
                if task.name in [PRE_CONFIGURATION, POST_ACTION]:
                    continue

                if task.is_checked:
                    logger.info(f"开始执行任务: {task.name}")
                    try:
                        await self.run_task(task.item_id)
                        logger.info(f"任务执行完成: {task.name}")
                    except Exception as exc:
                        logger.error(f"任务执行失败: {task.name}, 错误: {str(exc)}")

                if self.need_stop:
                    logger.info("收到停止请求，流程终止")
                    break

        except Exception as exc:
            logger.error(f"任务流程执行异常: {str(exc)}")
            import traceback

            logger.critical(traceback.format_exc())
        finally:
            await self.stop_task()

    async def connect_device(self, controller_raw: Dict[str, Any]):
        """连接 MaaFW 控制器"""
        controller_type = self._get_controller_type(controller_raw)
        if controller_type == "adb":
            return await self._connect_adb_controller(controller_raw)
        if controller_type == "win":
            return await self._connect_win32_controller(controller_raw)
        raise ValueError("不支持的控制器类型")

    async def load_resources(self, resource_raw: Dict[str, Any]):
        """根据配置加载资源"""
        if self.maafw.resource:
            self.maafw.resource.clear()

        resource_target = resource_raw.get("resource")
        resource_path = []

        if not resource_target:
            logger.warning("未找到资源目标，尝试直接从配置中获取资源路径")
            raise ValueError("未找到资源目标")

        for resource in self.task_service.interface.get("resource", []):
            if resource["name"] == resource_target:
                logger.debug(f"加载资源: {resource['path']}")
                resource_path = resource["path"]
                break

        if not resource_path or self.need_stop:
            logger.error(f"未找到目标资源: {resource_target}")
            await self.maafw.stop_task()
            return False

        for path_item in resource_path:
            cwd = Path.cwd()
            path_str = str(path_item)
            if len(path_str) >= 2 and path_str[1] == ":" and path_str[0].isalpha():
                resource = Path(path_str).resolve()
            else:
                normalized = path_str.lstrip("\\/")
                resource = (cwd / normalized).resolve()

            logger.debug(f"加载资源: {resource}")
            res_cfg = self.task_service.get_task(PRE_CONFIGURATION)
            gpu_idx = res_cfg.task_option.get("gpu", -1) if res_cfg else -1
            await self.maafw.load_resource(resource, gpu_idx)
            logger.debug(f"资源加载完成: {resource}")
        return True

    async def run_task(self, task_id: str):
        """执行指定任务"""
        task = self.task_service.get_task(task_id)
        if not task:
            logger.error(f"任务 ID '{task_id}' 不存在")
            return
        if not task.is_checked:
            logger.warning(f"任务 '{task.name}' 未被选中，跳过执行")
            return

        raw_info = self.task_service.get_task_execution_info(task_id)
        if raw_info is None:
            logger.error(f"无法获取任务 '{task.name}' 的执行信息")
            return

        entry = raw_info.get("entry", "")
        pipeline_override = raw_info.get("pipeline_override", {})
        await self.maafw.run_task(entry, pipeline_override)

    async def stop_task(self):
        """停止当前正在运行的任务"""
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
        """连接 ADB 控制器"""
        if not isinstance(controller_raw, dict):
            logger.error(
                f"控制器配置格式错误(ADB)，期望 dict，实际 {type(controller_raw)}: {controller_raw}"
            )
            return False

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
        """连接 Win32 控制器"""
        hwnd: int = controller_raw.get("hwnd", 0)
        screencap_method: int = controller_raw.get("screencap_method", 0)
        mouse_method: int = controller_raw.get("screencap_method", 0)
        keyboard_method: int = controller_raw.get("keyboard_method", 0)

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

        controller_config = controller_raw.get("controller_type", {})
        if isinstance(controller_config, str):
            controller_name = controller_config
        elif isinstance(controller_config, dict):
            controller_name = controller_config.get("value", "")
        else:
            controller_name = ""

        controller_name = controller_name.lower()
        for controller in self.task_service.interface.get("controller", []):
            if controller.get("name", "").lower() == controller_name:
                return controller.get("type", "").lower()

        raise ValueError(f"未找到控制器类型: {controller_raw}")

