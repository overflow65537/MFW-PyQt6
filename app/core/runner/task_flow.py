import asyncio
import calendar
import os
import shlex
import subprocess
import sys
import time as _time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict
from PySide6.QtCore import QCoreApplication, QObject
from app.common.constants import POST_ACTION, PRE_CONFIGURATION
from app.common.signal_bus import signalBus

from maa.toolkit import Toolkit
from app.utils.notice import NoticeTiming, send_notice

from app.utils.logger import logger
from app.core.service.Config_Service import ConfigService
from app.core.service.Task_Service import TaskService
from app.core.runner.maafw import (
    MaaFW,
    MaaFWError,
    maa_context_sink,
    maa_controller_sink,
    maa_resource_sink,
    maa_tasker_sink,
)

from app.core.Item import FromeServiceCoordinator, TaskItem


class TaskFlowRunner(QObject):
    """负责执行任务流的运行时组件"""

    def __init__(
        self,
        task_service: TaskService,
        config_service: ConfigService,
        fs_signal_bus: FromeServiceCoordinator | None = None,
    ):
        self.task_service = task_service
        self.config_service = config_service
        if fs_signal_bus:
            self.maafw = MaaFW(
                maa_context_sink=maa_context_sink,
                maa_controller_sink=maa_controller_sink,
                maa_resource_sink=maa_resource_sink,
                maa_tasker_sink=maa_tasker_sink,
            )
            self.fs_signal_bus = fs_signal_bus
        else:
            self.maafw = MaaFW()
            self.fs_signal_bus = None
        self.maafw.custom_info.connect(self._handle_maafw_custom_info)
        self.maafw.agent_info.connect(self._handle_agent_info)
        self.process = None

        self.speedrun_mode = (
            False  # 速通模式,这个状态需要通过UI或者cli的开始方法进行更改
        )

        self.need_stop = False
        self.monitor_need_stop = False
        self._is_running = False

    def _handle_agent_info(self, info: str):
        if "| WARNING |" in info:
            # 从warning开始截断
            info = info.split("| WARNING |")[1]
            signalBus.log_output.emit("WARNING", info)
        elif "| ERROR |" in info:
            # 从error开始截断
            info = info.split("| ERROR |")[1]
            signalBus.log_output.emit("ERROR", info)
        elif "| INFO |" in info:
            # 从info开始截断
            info = info.split("| INFO |")[1]
            signalBus.log_output.emit("INFO", info)


    def _handle_maafw_custom_info(self, error_code: int):
        try:
            error = MaaFWError(error_code)
            match error:
                case MaaFWError.RESOURCE_OR_CONTROLLER_NOT_INITIALIZED:
                    msg = self.tr("Resource or controller not initialized")
                case MaaFWError.AGENT_CONNECTION_FAILED:
                    msg = self.tr("Agent connection failed")
                case MaaFWError.TASKER_NOT_INITIALIZED:
                    msg = self.tr("Tasker not initialized")
                case _:
                    msg = self.tr(f"Unknown MaaFW error code: " + str(error_code))
            signalBus.log_output.emit("ERROR", msg)
        except ValueError:
            logger.warning(f"Received unknown MaaFW error code: {error_code}")
            signalBus.log_output.emit(
                "WARNING", self.tr(f"Unknown MaaFW error code: {error_code}")
            )

    async def run_tasks_flow(self):
        """任务完整流程：连接设备、加载资源、批量运行任务"""
        if self._is_running:
            logger.warning("任务流已经在运行，忽略新的启动请求")
            if self._is_running:
                logger.warning("等待结束后仍在运行，取消当前启动请求")
                return
        self._is_running = True
        self.need_stop = False
        tasks_to_report = [
            task
            for task in self.task_service.current_tasks
            if task.name not in [PRE_CONFIGURATION, POST_ACTION]
        ]
        task_status_records: list[dict[str, str]] = []
        task_status_by_id: dict[str, dict[str, str]] = {}
        for report_task in tasks_to_report:
            record = {
                "item_id": report_task.item_id,
                "name": report_task.name,
                "status": self.tr("NOT STARTED"),
            }
            task_status_records.append(record)
            task_status_by_id[report_task.item_id] = record

        selected_task_count = sum(1 for task in tasks_to_report if task.is_checked)
        post_task_event_pending = bool(task_status_records)
        config_label = self.config_service.current_config_id or self.tr(
            "Unknown Config"
        )
        try:
            if self.fs_signal_bus:
                self.fs_signal_bus.fs_start_button_status.emit(
                    {"text": "STOP", "status": "disabled"}
                )

            pre_cfg = self.task_service.get_task(PRE_CONFIGURATION)
            if not pre_cfg:
                raise ValueError("未找到基础预配置任务")

            selected_task_count = len(
                [
                    task
                    for task in self.task_service.current_tasks
                    if task.is_checked
                    and task.name not in [PRE_CONFIGURATION, POST_ACTION]
                ]
            )
            send_notice(
                NoticeTiming.WHEN_START_UP,
                self.tr("Task Flow Started"),
                self.tr("Config ")
                + str(config_label)
                + self.tr(" contains ")
                + str(selected_task_count)
                + self.tr(" tasks, ready to connect device."),
            )

            logger.info("开始连接设备...")
            signalBus.log_output.emit("INFO", self.tr("Starting to connect device..."))
            connected = await self.connect_device(pre_cfg.task_option)
            if not connected:
                logger.error("设备连接失败，尝试启动进程")
                send_notice(
                    NoticeTiming.WHEN_CONNECT_FAILED,
                    self.tr("Device Connection Failed"),
                    self.tr("Config ")
                    + str(config_label)
                    + self.tr(
                        " cannot connect device, please check controller configuration."
                    ),
                )

                return
            signalBus.log_output.emit("INFO", self.tr("Device connected successfully"))
            logger.info("设备连接成功")
            send_notice(
                NoticeTiming.WHEN_CONNECT_SUCCESS,
                self.tr("Device Connection Successful"),
                self.tr("Config ")
                + str(config_label)
                + self.tr(" device connection successful, start to execute tasks."),
            )

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

            if self.task_service.interface.get("agent", None):
                logger.info("传入agent配置...")
                self.maafw.agent_data_raw = self.task_service.interface.get(
                    "agent", None
                )
                signalBus.log_output.emit("INFO", self.tr("Agent Service Start"))

            logger.info("开始执行任务序列...")
            for task in self.task_service.current_tasks:
                if task.name in [PRE_CONFIGURATION, POST_ACTION]:
                    continue

                if not task.is_checked:
                    continue

                logger.info(f"开始执行任务: {task.name}")
                record = task_status_by_id.get(task.item_id)
                try:
                    task_result = await self.run_task(task.item_id)
                    if task_result == "skipped":
                        if record:
                            record["status"] = self.tr("SKIPPED")
                        continue
                    if task_result is False:
                        if record:
                            record["status"] = self.tr("FAILED")
                        logger.error(f"任务执行失败: {task.name}, 返回 False，终止流程")
                        send_notice(
                            NoticeTiming.WHEN_TASK_FAILED,
                            self.tr("Task Failed"),
                            self.tr("Task ")
                            + str(task.name)
                            + self.tr(
                                " did not return a successful status, the flow is terminated."
                            ),
                        )
                        await self.stop_task()
                        break

                    logger.info(f"任务执行完成: {task.name}")
                    if record:
                        record["status"] = self.tr("SUCCESS")
                    send_notice(
                        NoticeTiming.WHEN_TASK_FINISHED,
                        self.tr("Task Finished"),
                        self.tr("Task ")
                        + str(task.name)
                        + self.tr(" has been completed."),
                    )

                except Exception as exc:
                    logger.error(f"任务执行失败: {task.name}, 错误: {str(exc)}")
                    if record:
                        record["status"] = self.tr("FAILED")
                    send_notice(
                        NoticeTiming.WHEN_TASK_FAILED,
                        self.tr("Task Failed"),
                        self.tr("Task ")
                        + str(task.name)
                        + self.tr(" execution failed: ")
                        + str(exc),
                    )

                if self.need_stop:
                    logger.info("收到停止请求，流程终止")
                    break
            signalBus.log_output.emit("INFO", self.tr("All tasks have been completed"))

        except Exception as exc:
            logger.error(f"任务流程执行异常: {str(exc)}")
            send_notice(
                NoticeTiming.WHEN_TASK_FAILED,
                self.tr("Task Flow Exception"),
                self.tr("Task flow execution exception: ") + str(exc),
            )
            import traceback

            logger.critical(traceback.format_exc())
        finally:
            try:
                await self._handle_post_action()
            except Exception as exc:
                logger.error(f"完成后操作执行失败: {exc}")
            await self.stop_task()
            if post_task_event_pending:
                if task_status_records:
                    task_summary = "\n".join(
                        f"{record['name']}: {record['status']}"
                        for record in task_status_records
                    )
                else:
                    task_summary = self.tr("No tasks")
                send_notice(
                    NoticeTiming.WHEN_POST_TASK,
                    self.tr("Task Flow Completed"),
                    self.tr("Configuration ")
                    + config_label
                    + self.tr(
                        " all tasks and post actions have been completed, processed "
                    )
                    + str(selected_task_count)
                    + self.tr(" tasks.\nTask Status:\n")
                    + task_summary,
                )

            self._is_running = False

    @property
    def is_running(self) -> bool:
        return self._is_running

    async def connect_device(self, controller_raw: Dict[str, Any]):
        """连接 MaaFW 控制器"""
        controller_type = self._get_controller_type(controller_raw)
        if self.fs_signal_bus:
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
            await self.stop_task()
            return False

        for path_item in resource_path:
            cwd = Path.cwd()
            path_str = str(path_item.replace("{PROJECT_DIR}", ""))
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
        elif not task.is_checked:
            logger.warning(f"任务 '{task.name}' 未被选中，跳过执行")
            return

        speedrun_cfg = self._get_task_by_name(task.name).get("speedrun", None)
        if speedrun_cfg and self.speedrun_mode:
            allowed, reason = self._evaluate_speedrun(task, speedrun_cfg)
            if not allowed:
                logger.info(
                    f"任务 '{task.name}' 遵循 speedrun 限制，跳过本次运行: {reason}"
                )
                signalBus.log_output.emit(
                    "INFO",
                    self.tr("Task ")
                    + task.name
                    + self.tr(" follows speedrun limit, skipping this run: ")
                    + reason,
                )
                return "skipped"
            signalBus.log_output.emit("INFO", self.tr("Speedrun rule allows execution"))

        raw_info = self.task_service.get_task_execution_info(task_id)
        logger.info(f"任务 '{task.name}' 的执行信息: {raw_info}")
        if raw_info is None:
            logger.error(f"无法获取任务 '{task.name}' 的执行信息")
            return

        entry = raw_info.get("entry", "")
        pipeline_override = raw_info.get("pipeline_override", {})

        await self.maafw.run_task(entry, pipeline_override)
        self._record_speedrun_runtime(task)

    async def stop_task(self):
        """停止当前正在运行的任务"""
        if self.need_stop:
            return
        self.need_stop = True
        if self.fs_signal_bus:
            signalBus.log_output.emit("INFO", self.tr("Stopping task..."))
            self.fs_signal_bus.fs_start_button_status.emit(
                {"text": "STOP", "status": "disabled"}
            )
        await self.maafw.stop_task()
        if self.fs_signal_bus:
            self.fs_signal_bus.fs_start_button_status.emit(
                {"text": "START", "status": "enabled"}
            )
        self._is_running = False
        logger.info("任务流停止")

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
            (
                f"ADB 参数类型: adb_path={type(adb_path)}, address={type(address)}, "
                f"screen_method={screen_method}({type(screen_method)}), "
                f"input_method={input_method}({type(input_method)})"
            )
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

    async def _handle_post_action(self) -> None:
        """统一处理完成后操作顺序"""
        post_task = self.task_service.get_task(POST_ACTION)
        if not post_task:
            return

        post_config = post_task.task_option.get("post_action")
        if not isinstance(post_config, dict):
            return

        if post_config.get("run_program"):
            await self._run_program_from_post_action(
                post_config.get("program_path", ""),
                post_config.get("program_args", ""),
            )

        if post_config.get("run_other"):
            target_config = (post_config.get("target_config") or "").strip()
            if target_config:
                await self._run_other_configuration(target_config)
            else:
                logger.warning("完成后运行其他配置开关被激活，但未配置目标配置")

        if post_config.get("close_software"):
            await self._close_software()

        if post_config.get("close_emulator"):
            self._close_emulator()

        if post_config.get("shutdown"):
            self._shutdown_system()

    async def _run_program_from_post_action(
        self, program_path: str, program_args: str
    ) -> None:
        """根据配置启动指定程序，等待退出"""
        executable = (program_path or "").strip()
        if not executable:
            logger.warning("完成后程序未填写路径，跳过")
            return

        args_list = self._parse_program_args(program_args)
        try:
            process = await asyncio.to_thread(
                self._start_process, executable, args_list or None
            )
        except Exception as exc:
            logger.error(f"启动完成后程序失败: {exc}")
            return

        logger.info(f"完成后程序已启动: {executable}")
        try:
            return_code = await asyncio.to_thread(process.wait)
            logger.info(f"完成后程序已退出，返回码: {return_code}")
        except Exception as exc:
            logger.error(f"等待完成后程序退出时失败: {exc}")

    def _parse_program_args(self, args: str) -> list[str]:
        """解析完成后程序的参数字符串"""
        trimmed = (args or "").strip()
        if not trimmed:
            return []

        try:
            return shlex.split(trimmed, posix=os.name != "nt")
        except ValueError as exc:
            logger.warning(f"解析完成后程序参数失败，退回简单分割: {exc}")
            return [item for item in trimmed.split() if item]

    async def _run_other_configuration(self, config_id: str) -> None:
        """尝试切换到指定的配置"""
        config_service = self.config_service
        if not config_service:
            logger.warning("配置服务未初始化，跳过运行其他配置")
            return

        target_config = config_service.get_config(config_id)
        if not target_config:
            logger.warning(f"完成后操作指定的配置不存在: {config_id}")
            return

        config_service.current_config_id = config_id
        if config_service.current_config_id == config_id:
            logger.info(f"已切换至完成后指定配置: {config_id}")
        else:
            logger.warning(f"切换至配置 {config_id} 失败")

    async def _close_software(self) -> None:
        """发出退出信号让程序自身关闭"""
        app = QCoreApplication.instance()
        if not app:
            logger.warning("完成后关闭软件: 无法获取 QCoreApplication 实例")
            return

        logger.info("完成后关闭软件: 退出应用")
        app.quit()

    def _close_emulator(self) -> None:
        """关闭模拟器（占位实现，待补充）"""
        pass

    def _shutdown_system(self) -> None:
        """执行系统关机命令，兼容 Windows/macOS/Linux"""
        try:
            if sys.platform.startswith("win"):
                subprocess.run(["shutdown", "/s", "/t", "0"], check=False)
            elif sys.platform == "darwin":
                subprocess.run(["sudo", "shutdown", "-h", "now"], check=False)
            else:
                subprocess.run(["shutdown", "-h", "now"], check=False)
            logger.info("完成后执行关机命令")
        except Exception as exc:
            logger.error(f"执行关机命令失败: {exc}")

    def _evaluate_speedrun(
        self, task: TaskItem, speedrun: Dict[str, Any]
    ) -> tuple[bool, str]:
        """校验 speedrun 限制"""
        if not speedrun or not isinstance(speedrun, dict):
            return True, ""

        run_cfg = speedrun.get("run") or {}
        if not isinstance(run_cfg, dict):
            run_cfg = {}

        count_limit_value = self._get_speedrun_count_limit(run_cfg)
        if count_limit_value is None:
            return True, ""

        state = self._ensure_speedrun_state(task)
        history_entries = state.get("last_runtime", [])
        history = self._parse_speedrun_history(history_entries)
        last_run = history[-1] if history else datetime(1970, 1, 1)
        now = datetime.now()

        next_refresh = self._get_speedrun_next_refresh_time(last_run, speedrun)
        if not next_refresh:
            return True, ""

        state_dirty = False
        remaining_count = state.get("remaining_count")
        if not isinstance(remaining_count, int):
            remaining_count = -1
        if remaining_count < 0:
            state["remaining_count"] = 0
            remaining_count = 0
            state_dirty = True

        if now >= next_refresh:
            if state.get("remaining_count") != count_limit_value:
                state["remaining_count"] = count_limit_value
                remaining_count = count_limit_value
                state_dirty = True

        if remaining_count == 0:
            if state_dirty:
                self.task_service.update_task(task)
            return False, self.tr("This period's remaining execution count is 0")

        min_interval_value = self._get_speedrun_min_interval(run_cfg)
        if min_interval_value and history:
            last_run_time = history[-1]
            elapsed = (now - last_run_time).total_seconds()
            if elapsed < min_interval_value * 3600:
                if state_dirty:
                    self.task_service.update_task(task)
                return (
                    False,
                    self.tr(
                        "Not enough time passed since last run. Minimum interval is "
                    )
                    + str(min_interval_value)
                    + self.tr(" hours."),
                )

        if state_dirty:
            self.task_service.update_task(task)
        return True, ""

    def _record_speedrun_runtime(self, task: TaskItem) -> None:
        """记录 speedrun 运行时间"""
        state = self._ensure_speedrun_state(task)

        history = self._parse_speedrun_history(state.get("last_runtime", []))
        history.append(datetime.now())
        last_entry = history[-1]
        state["last_runtime"] = [last_entry.isoformat()]
        self._consume_speedrun_count(state)
        remaining = state.get("remaining_count", -1)
        logger.info(
            f"任务 '{task.name}' 已记录 speedrun 运行时间, 最新 {state['last_runtime'][-1]}, 剩余 {remaining}"
        )
        self.task_service.update_task(task)

    def _parse_speedrun_history(self, raw_history: Any) -> list[datetime]:
        entries = raw_history or []
        if not isinstance(entries, list):
            entries = [entries]

        parsed: list[datetime] = []
        for entry in entries:
            parsed_entry: datetime | None = None
            if isinstance(entry, (int, float)):
                try:
                    parsed_entry = datetime.fromtimestamp(entry)
                except OverflowError:
                    parsed_entry = None
            elif isinstance(entry, str):
                try:
                    parsed_entry = datetime.fromisoformat(entry)
                except ValueError:
                    try:
                        parsed_entry = datetime.fromtimestamp(float(entry))
                    except (TypeError, ValueError, OverflowError):
                        parsed_entry = None
            if parsed_entry:
                parsed.append(parsed_entry)

        parsed.sort()
        return parsed

    def _get_speedrun_next_refresh_time(
        self, base_time: datetime, speedrun: Dict[str, Any]
    ) -> datetime | None:
        mode = (speedrun.get("mode") or "").lower()
        trigger_cfg = speedrun.get("trigger") or {}
        if not isinstance(trigger_cfg, dict):
            return None

        if mode == "daily":
            daily_trigger = trigger_cfg.get("daily") or {}
            hour_start = self._normalize_hour_value(daily_trigger.get("hour_start"))
            if hour_start is None:
                hour_start = 0
            return self._next_daily_refresh_time(base_time, hour_start)

        if mode == "weekly":
            weekly_trigger = trigger_cfg.get("weekly") or {}
            weekdays = self._collect_valid_ints(weekly_trigger.get("weekday", []), 1, 7)
            hour_start = self._normalize_hour_value(weekly_trigger.get("hour_start"))
            if hour_start is None:
                hour_start = 0
            return self._next_weekly_refresh_time(base_time, weekdays, hour_start)

        if mode == "monthly":
            monthly_trigger = trigger_cfg.get("monthly") or {}
            days = self._collect_valid_ints(monthly_trigger.get("day", []), 1, 31)
            hour_start = self._normalize_hour_value(monthly_trigger.get("hour_start"))
            if hour_start is None:
                hour_start = 0
            return self._next_monthly_refresh_time(base_time, days, hour_start)

        return None

    def _next_daily_refresh_time(
        self, base_time: datetime, hour_start: int
    ) -> datetime:
        candidate = base_time.replace(
            hour=hour_start, minute=0, second=0, microsecond=0
        )
        if candidate <= base_time:
            candidate += timedelta(days=1)
        return candidate

    def _next_weekly_refresh_time(
        self, base_time: datetime, weekdays: list[int], hour_start: int
    ) -> datetime | None:
        allowed = weekdays or list(range(1, 8))
        start_date = base_time.date()
        for day_offset in range(0, 14):
            candidate_date = start_date + timedelta(days=day_offset)
            if candidate_date.isoweekday() not in allowed:
                continue
            candidate = datetime(
                candidate_date.year,
                candidate_date.month,
                candidate_date.day,
                hour_start,
                0,
                0,
            )
            if candidate > base_time:
                return candidate
        offset = 14
        while True:
            candidate_date = start_date + timedelta(days=offset)
            if candidate_date.isoweekday() in allowed:
                candidate = datetime(
                    candidate_date.year,
                    candidate_date.month,
                    candidate_date.day,
                    hour_start,
                    0,
                    0,
                )
                if candidate > base_time:
                    return candidate
            offset += 1

    def _next_monthly_refresh_time(
        self, base_time: datetime, days: list[int], hour_start: int
    ) -> datetime | None:
        allowed_days = sorted(set(days)) if days else list(range(1, 32))
        start_year = base_time.year
        start_month = base_time.month
        for month_offset in range(0, 24):
            month_index = start_month - 1 + month_offset
            year = start_year + month_index // 12
            month = (month_index % 12) + 1
            days_in_month = calendar.monthrange(year, month)[1]
            for day in allowed_days:
                if day > days_in_month:
                    continue
                candidate = datetime(year, month, day, hour_start, 0, 0)
                if candidate > base_time:
                    return candidate
        return None

    def _collect_valid_ints(
        self, raw_value: Any, min_value: int, max_value: int
    ) -> list[int]:
        if not isinstance(raw_value, (list, tuple)):
            return []

        normalized: list[int] = []
        for item in raw_value:
            try:
                number = int(item)
            except (TypeError, ValueError):
                continue
            if min_value <= number <= max_value:
                normalized.append(number)

        return normalized

    def _normalize_hour_value(self, raw_value: Any) -> int | None:
        try:
            hour = int(raw_value)
        except (TypeError, ValueError):
            return None

        if hour < 0:
            hour = 0
        hour %= 24
        return hour

    def _ensure_speedrun_state(self, task: TaskItem) -> dict:
        if not isinstance(task.task_option, dict):
            task.task_option = {}
        state = task.task_option.get("_speedrun_state")
        if not isinstance(state, dict):
            epoch = datetime(1970, 1, 1)
            state = {
                "last_runtime": [epoch.isoformat()],
                "remaining_count": -1,
            }
            task.task_option["_speedrun_state"] = state
        if "last_runtime" not in state or not isinstance(state["last_runtime"], list):
            epoch = datetime(1970, 1, 1)
            state["last_runtime"] = [epoch.isoformat()]
        if "remaining_count" not in state or not isinstance(
            state["remaining_count"], int
        ):
            state["remaining_count"] = -1
        return state

    def _get_speedrun_count_limit(self, run_cfg: Dict[str, Any]) -> int | None:
        count_limit = run_cfg.get("count")
        try:
            return int(count_limit) if count_limit not in (None, "", False) else None
        except (TypeError, ValueError):
            return None

    def _get_speedrun_min_interval(self, run_cfg: Dict[str, Any]) -> float | None:
        min_interval = run_cfg.get("min_interval_hours")
        try:
            return (
                float(min_interval) if min_interval not in (None, "", False) else None
            )
        except (TypeError, ValueError):
            return None

    def _consume_speedrun_count(self, state: dict) -> None:
        remaining = state.get("remaining_count")
        if isinstance(remaining, int) and remaining > 0:
            state["remaining_count"] = remaining - 1

    def _get_task_by_name(self, name: str) -> Dict[str, Any]:
        interface = self.task_service.interface
        tasks = interface.get("task")

        if not isinstance(tasks, list):
            return {}
        for task in tasks:
            if not isinstance(task, dict):
                continue
            if task.get("name") == name:
                return task

        return {}
