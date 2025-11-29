import subprocess
import time as _time
from pathlib import Path
from typing import Any, Dict
import asyncio
from PySide6.QtCore import QObject
from app.common.constants import POST_ACTION, PRE_CONFIGURATION
from app.common.signal_bus import signalBus

from maa.toolkit import Toolkit

from ...utils.logger import logger
from ..service.Task_Service import TaskService
from .maafw import MaaFW
from .maasink import (
    MaaContextSink,
    MaaControllerEventSink,
    MaaResourceEventSink,
    MaaTaskerEventSink,
)


class TaskFlowRunner(QObject):
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
        self.process = None
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
                logger.error("设备连接失败，尝试启动进程")
                return
            logger.info("设备连接成功")

            logger.info("开始截图测试...")
            start_time = _time.time()
            await self.maafw.screencap_test()
            end_time = _time.time()
            logger.info(f"截图测试成功，耗时: {end_time - start_time}毫秒")
            signalBus.callback.emit(
                {"name": "speed_test", "details": end_time - start_time}
            )

            logger.info("开始加载资源...")
            if not await self.load_resources(pre_cfg.task_option):
                logger.error("资源加载失败，流程终止")
                return
            logger.info("资源加载成功")

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
        self.fs_signal_bus.fs_start_button_status.emit(
            {"text": "STOP", "status": "enabled"}
        )
        if controller_type == "adb":
            return await self._connect_adb_controller(controller_raw)
        elif controller_type == "win":
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

        # 如果 adb_path 或 address 为空，自动搜索设备
        if not adb_path or not address:
            logger.info("ADB 路径或地址为空，开始自动搜索设备...")
            signalBus.log_output.emit("INFO", self.tr("Auto searching ADB devices..."))
            found_device = await self._auto_find_adb_device(
                controller_raw, activate_controller
            )
            if found_device:
                adb_path = found_device.get("adb_path", "")
                address = found_device.get("address", "")
            else:
                logger.warning("未找到可用的 ADB 设备")
                signalBus.log_output.emit("WARNING", self.tr("No ADB device found"))
                return False
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

        if await self.maafw.connect_adb(
            adb_path,
            address,
            screen_method,
            input_method,
            config,
        ):
            return True
        elif controller_raw.get(activate_controller, {}).get("emulator_path", ""):
            logger.info("尝试启动模拟器")
            signalBus.log_output.emit("INFO", self.tr("try to start emulator"))
            emu_path = controller_raw.get(activate_controller, {}).get(
                "emulator_path", ""
            )
            emu_params = controller_raw.get(activate_controller, {}).get(
                "emulator_params", ""
            )
            wait_emu_start = int(
                controller_raw.get(activate_controller, {}).get("wait_time", 0)
            )

            self.process = self._start_process(emu_path, emu_params)
            # 异步等待
            if wait_emu_start > 0:
                countdown_ok = await self._countdown_wait(
                    wait_emu_start, self.tr("waiting for emulator start...")
                )
                if not countdown_ok:
                    return False
            if await self.maafw.connect_adb(
                adb_path,
                address,
                screen_method,
                input_method,
                config,
            ):
                print("connect adb success")
                return True

        return False

    async def _connect_win32_controller(self, controller_raw: Dict[str, Any]):
        """连接 Win32 控制器"""
        activate_controller = controller_raw.get("controller_type")
        if activate_controller is None:
            logger.error(f"未找到控制器配置: {controller_raw}")
            return False

        hwnd = controller_raw.get(activate_controller, {}).get("hwnd", 0)
        screencap_method: int = controller_raw.get(activate_controller, {}).get(
            "win32_screencap_methods", 0
        )
        mouse_method: int = controller_raw.get(activate_controller, {}).get(
            "mouse_input_methods", 0
        )
        keyboard_method: int = controller_raw.get(activate_controller, {}).get(
            "keyboard_input_methods", 0
        )

        # 如果 hwnd 为空，自动搜索窗口
        if not hwnd:
            logger.info("HWND 为空，开始自动搜索 Win32 窗口...")
            signalBus.log_output.emit(
                "INFO", self.tr("Auto searching Win32 windows...")
            )
            found_device = await self._auto_find_win32_window(
                controller_raw, activate_controller
            )
            if found_device:
                hwnd = found_device.get("hwnd", 0)
            else:
                logger.warning("未找到可用的 Win32 窗口")
                signalBus.log_output.emit("WARNING", self.tr("No Win32 window found"))
                return False

        if await self.maafw.connect_win32hwnd(
            hwnd,
            screencap_method,
            mouse_method,
            keyboard_method,
        ):
            return True
        elif controller_raw.get(activate_controller, {}).get("program_path", ""):
            logger.info("尝试启动程序")
            signalBus.log_output.emit("INFO", self.tr("try to start program"))
            program_path = controller_raw.get(activate_controller, {}).get(
                "program_path", ""
            )
            program_params = controller_raw.get(activate_controller, {}).get(
                "program_params", ""
            )
            wait_program_start = int(
                controller_raw.get(activate_controller, {}).get("wait_launch_time", 0)
            )
            self.process = self._start_process(program_path, program_params)
            if wait_program_start > 0:
                countdown_ok = await self._countdown_wait(
                    wait_program_start,
                    self.tr("waiting for program start..."),
                )
                if not countdown_ok:
                    return False
            if await self.maafw.connect_win32hwnd(
                hwnd,
                screencap_method,
                mouse_method,
                keyboard_method,
            ):
                return False
        else:
            return False
        return True

    def _start_process(
        self, entry: str | Path, argv: list[str] | tuple[str, ...] | str | None = None
    ) -> subprocess.Popen:
        """根据入口路径/命令开启子进程，返回 Popen 对象"""

        command = [str(entry)]
        if argv is not None:
            if isinstance(argv, (list, tuple)):
                command.extend(str(arg) for arg in argv)
            else:
                command.append(str(argv))

        logger.debug(f"准备启动子进程: {command}")
        return subprocess.Popen(command)

    async def _countdown_wait(self, wait_seconds: int, message: str) -> bool:
        """按指定阈值输出倒计时日志，返回 False 表示提前停止"""

        if wait_seconds <= 0:
            return True

        thresholds = [60, 30, 15, 10, 5, 4, 3, 2, 1]
        log_points = {wait_seconds}
        for point in thresholds:
            if wait_seconds >= point:
                log_points.add(point)

        for remaining in range(wait_seconds, 0, -1):
            if remaining in log_points:
                signalBus.log_output.emit(
                    "INFO",
                    message + str(remaining) + self.tr(" seconds"),
                )
                log_points.remove(remaining)
            if self.need_stop:
                return False
            await asyncio.sleep(1)
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

    async def _auto_find_adb_device(
        self, controller_raw: Dict[str, Any], activate_controller: str
    ) -> Dict[str, Any] | None:
        """自动搜索 ADB 设备并保存第一个结果到配置

        Args:
            controller_raw: 控制器原始配置
            activate_controller: 当前激活的控制器名称

        Returns:
            找到的设备信息字典，未找到返回 None
        """
        try:
            devices = Toolkit.find_adb_devices()
            if not devices:
                logger.warning("未找到任何 ADB 设备")
                return None

            # 取第一个设备
            device = devices[0]
            device_info = {
                "adb_path": str(device.adb_path),
                "address": device.address,
                "screencap_methods": device.screencap_methods,
                "input_methods": device.input_methods,
                "config": device.config,
                "device_name": f"{device.name}({device.address})",
            }

            logger.info(f"自动搜索到 ADB 设备: {device_info['device_name']}")
            signalBus.log_output.emit(
                "INFO",
                self.tr("Found ADB device: ") + device_info["device_name"],
            )

            # 更新配置并保存
            self._save_device_to_config(
                controller_raw, activate_controller, device_info
            )

            return device_info

        except Exception as e:
            logger.error(f"自动搜索 ADB 设备时出错: {e}")
            return None

    async def _auto_find_win32_window(
        self, controller_raw: Dict[str, Any], activate_controller: str
    ) -> Dict[str, Any] | None:
        """自动搜索 Win32 窗口并保存第一个结果到配置

        Args:
            controller_raw: 控制器原始配置
            activate_controller: 当前激活的控制器名称

        Returns:
            找到的窗口信息字典，未找到返回 None
        """
        try:
            windows = Toolkit.find_desktop_windows()
            if not windows:
                logger.warning("未找到任何 Win32 窗口")
                return None

            # 取第一个窗口
            window = windows[0]
            window_info = {
                "hwnd": str(window.hwnd),
                "window_name": window.window_name,
                "class_name": window.class_name,
                "device_name": f"{window.window_name or 'Unknown Window'}({window.hwnd})",
            }

            logger.info(f"自动搜索到 Win32 窗口: {window_info['device_name']}")
            signalBus.log_output.emit(
                "INFO",
                self.tr("Found Win32 window: ") + window_info["device_name"],
            )

            # 更新配置并保存
            self._save_device_to_config(
                controller_raw, activate_controller, window_info
            )

            return window_info

        except Exception as e:
            logger.error(f"自动搜索 Win32 窗口时出错: {e}")
            return None

    def _save_device_to_config(
        self,
        controller_raw: Dict[str, Any],
        activate_controller: str,
        device_info: Dict[str, Any],
    ) -> None:
        """保存设备信息到配置

        Args:
            controller_raw: 控制器原始配置
            activate_controller: 当前激活的控制器名称
            device_info: 设备信息字典
        """
        try:
            # 确保控制器配置存在
            if activate_controller not in controller_raw:
                controller_raw[activate_controller] = {}

            # 更新设备信息
            controller_raw[activate_controller].update(device_info)

            # 获取预配置任务并更新
            pre_cfg = self.task_service.get_task(PRE_CONFIGURATION)
            if pre_cfg:
                pre_cfg.task_option.update(controller_raw)
                self.task_service.update_task(pre_cfg)
                logger.info(f"设备配置已保存: {device_info.get('device_name', '')}")

        except Exception as e:
            logger.error(f"保存设备配置时出错: {e}")
