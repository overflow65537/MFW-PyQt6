import asyncio
import calendar
import os
import platform
import shlex
import subprocess
import sys
import time as _time

from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict
from PySide6.QtCore import QCoreApplication, QObject, Signal, QTimer
from app.common.constants import (
    POST_ACTION,
    _CONTROLLER_,
    _RESOURCE_,
)
from app.common.signal_bus import signalBus
from app.common.config import cfg, Config

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
from app.utils.emulator_utils import EmulatorHelper

from app.core.Item import FromeServiceCoordinator, TaskItem


class TaskFlowRunner(QObject):
    """负责执行任务流的运行时组件"""

    task_timeout_restart_requested = Signal(
        str, int
    )  # 任务超时需要重启 (entry, attempts)

    def __init__(
        self,
        task_service: TaskService,
        config_service: ConfigService,
        fs_signal_bus: FromeServiceCoordinator | None = None,
    ):
        super().__init__()
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

        self.need_stop = False
        self.monitor_need_stop = False
        self._is_running = False
        self._next_config_to_run: str | None = None
        self.adb_controller_raw: dict[str, Any] | None = None
        self.adb_activate_controller: str | None = None
        self.adb_controller_config: dict[str, Any] | None = None

        # bundle 相关：在任务流开始时根据当前配置初始化
        self.bundle_path: str = "./"

        # 任务超时相关
        self._timeout_timer = QTimer(self)
        self._timeout_timer.setSingleShot(True)
        self._timeout_timer.timeout.connect(self._on_task_timeout)
        self._timeout_active_entry = ""
        self._timeout_restart_attempts = 0
        self._is_timeout_restart = False
        # 当前正在执行的任务ID，用于超时处理
        self._current_running_task_id: str | None = None
        # 标记是否为"手动停止"，用于控制是否发送完成通知
        self._manual_stop = False
        # 标记是否为"超时停止"，用于避免重复发送通知
        self._timeout_stop = False
        # 任务运行状态标记：每个任务开始前置为 True，收到 abort 信号时置为 False
        self._current_task_ok: bool = True

        # 监听 MaaFW 回调信号，用于接收 abort 等特殊事件
        signalBus.callback.connect(self._handle_maafw_callback)

    def _handle_maafw_callback(self, payload: Dict[str, Any]):
        """处理来自 MaaFW 的通用回调信号（包括自定义的 abort 信号）。

        当前实现只负责更新内部状态变量，不直接控制任务流转。
        """
        try:
            name = payload.get("name", "")
            if name == "abort":
                # 收到 abort 信号：仅标记当前任务状态，等待 run_task 完成后再由调用方判断
                self._current_task_ok = False
        except Exception as exc:
            logger.warning(f"处理 MaaFW 回调信号时出错: {exc}")

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
                    msg = self.tr("Unknown MaaFW error code: {}").format(error_code)
            signalBus.log_output.emit("ERROR", msg)
        except ValueError:
            logger.warning(f"Received unknown MaaFW error code: {error_code}")
            signalBus.log_output.emit(
                "WARNING", self.tr("Unknown MaaFW error code: {}").format(error_code)
            )

    async def run_tasks_flow(
        self,
        task_id: str | None = None,
        is_timeout_restart: bool = False,
        timeout_restart_entry: str | None = None,
        timeout_restart_attempts: int = 0,
    ):
        """任务完整流程：连接设备、加载资源、批量运行任务"""
        if self._is_running:
            logger.warning("任务流已经在运行，忽略新的启动请求")
            return
        self._is_running = True
        self.need_stop = False
        self._manual_stop = False
        self._timeout_stop = False
        self._is_timeout_restart = is_timeout_restart
        # 跟踪任务流是否成功启动并执行了任务
        self._tasks_started = False
        
        # 发送任务流启动通知
        send_notice(
            NoticeTiming.WHEN_FLOW_STARTED,
            self.tr("Task Flow Started"),
            self.tr("Task flow has been started."),
        )
        # 如果不是超时重启，重置超时状态
        if not is_timeout_restart:
            self._reset_task_timeout_state()
        else:
            # 超时重启时，从传入参数恢复重启次数和entry
            if timeout_restart_entry:
                self._timeout_active_entry = timeout_restart_entry
                self._timeout_restart_attempts = timeout_restart_attempts
                logger.info(
                    f"恢复超时重启状态: entry={timeout_restart_entry}, attempts={timeout_restart_attempts}"
                )
            self._timeout_timer.stop()
            self._current_running_task_id = None
        is_single_task_mode = task_id is not None

        # 初始化日志收集列表
        log_messages: list[tuple[str, str]] = []  # (level, text)

        def collect_log(level: str, text: str):
            """收集日志信息"""
            log_messages.append((level, text))

        # 连接日志输出信号
        signalBus.log_output.connect(collect_log)
        current_config = self.config_service.get_config(
            self.config_service.current_config_id
        )
        if not current_config:
            # 保持 bundle_path 的安全默认值
            self.bundle_path = "./"
        else:
            self.bundle_path = self.config_service.get_bundle_path_for_config(
                current_config
            )
        try:
            if self.fs_signal_bus:
                self.fs_signal_bus.fs_start_button_status.emit(
                    {"text": "STOP", "status": "disabled"}
                )
            controller_cfg = self.task_service.get_task(_CONTROLLER_)
            if not controller_cfg:
                raise ValueError("未找到基础预配置任务")

            logger.info("开始连接设备...")
            signalBus.log_output.emit("INFO", self.tr("Starting to connect device..."))
            connected = await self.connect_device(controller_cfg.task_option)
            if not connected:
                logger.error("设备连接失败")
                # 发送连接失败通知
                send_notice(
                    NoticeTiming.WHEN_CONNECT_FAILED,
                    self.tr("Device Connection Failed"),
                    self.tr("Failed to connect to the device."),
                )
                return
            signalBus.log_output.emit("INFO", self.tr("Device connected successfully"))
            logger.info("设备连接成功")
            # 发送连接成功通知
            send_notice(
                NoticeTiming.WHEN_CONNECT_SUCCESS,
                self.tr("Device Connected Successfully"),
                self.tr("Device has been connected successfully."),
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
            resource_cfg = self.task_service.get_task(_RESOURCE_)
            if not resource_cfg:
                raise ValueError("未找到资源设置任务")
            if not await self.load_resources(resource_cfg.task_option):
                logger.error("资源加载失败，流程终止")
                return
            logger.info("资源加载成功")

            if self.task_service.interface.get("agent", None):
                logger.info("传入agent配置...")
                self.maafw.agent_data_raw = self.task_service.interface.get(
                    "agent", None
                )
                signalBus.log_output.emit("INFO", self.tr("Agent Service Start"))

            if self.task_service.interface.get("custom", None) and self.maafw.resource:
                logger.info("开始加载自定义组件...")
                signalBus.log_output.emit(
                    "INFO", self.tr("Starting to load custom components...")
                )
                self.maafw.resource.clear_custom_recognition()
                self.maafw.resource.clear_custom_action()

                # 兼容绝对路径与相对 bundle.path 的自定义配置路径
                custom_config_path = self.task_service.interface.get("custom", "")
                if custom_config_path:
                    bundle_path_str = self.bundle_path or "./"
                    base_dir = Path(bundle_path_str)
                    if not base_dir.is_absolute():
                        base_dir = (Path.cwd() / base_dir).resolve()

                    # 先处理占位符与前导分隔符
                    raw_custom = str(custom_config_path).replace("{PROJECT_DIR}", "")
                    normalized_custom = raw_custom.lstrip("\\/")
                    custom_path_obj = Path(normalized_custom)

                    # 绝对路径：直接使用，保持兼容已有配置
                    if custom_path_obj.is_absolute():
                        custom_config_path = custom_path_obj
                    else:
                        # 相对路径：视为相对 bundle.path 的路径
                        custom_config_path = (base_dir / normalized_custom).resolve()

                result = self.maafw.load_custom_objects(
                    custom_config_path=custom_config_path
                )
                if not result:
                    failed_actions = self.maafw.custom_load_report["actions"]["failed"]
                    failed_recogs = self.maafw.custom_load_report["recognitions"][
                        "failed"
                    ]
                    detail_parts = [
                        f"动作 {item.get('name', '')}: {item.get('reason', '')}"
                        for item in failed_actions
                    ] + [
                        f"识别器 {item.get('name', '')}: {item.get('reason', '')}"
                        for item in failed_recogs
                    ]
                    detail_msg = (
                        "；".join([part for part in detail_parts if part]) or "未知原因"
                    )

                    logger.error(f"自定义组件加载失败，流程终止: {detail_msg}")
                    signalBus.log_output.emit(
                        "ERROR",
                        self.tr(
                            "Custom components loading failed, the flow is terminated: "
                        )
                        + detail_msg,
                    )
                    signalBus.log_output.emit(
                        "ERROR", self.tr("please try to reset resource in setting")
                    )
                    await self.stop_task()
                    return
            if task_id:
                logger.info(f"开始执行任务: {task_id}")
                task = self.task_service.get_task(task_id)
                if not task:
                    logger.error(f"任务 ID '{task_id}' 不存在")
                    return
                if task.is_hidden:
                    logger.warning(f"任务 '{task.name}' 被隐藏，跳过执行")
                    return
                if not task.is_checked:
                    logger.warning(f"任务 '{task.name}' 未被选中，跳过执行")
                    return
                self._tasks_started = True
                # 每个任务开始前，假定其可以正常完成
                self._current_task_ok = True
                # 记录当前正在执行的任务，用于超时处理
                self._current_running_task_id = task.item_id
                await self.run_task(task_id, skip_speedrun=True)
                # 检查任务执行结果并发送通知
                if not self._current_task_ok:
                    # 发送任务失败通知
                    send_notice(
                        NoticeTiming.WHEN_TASK_FAILED,
                        self.tr("Task Failed"),
                        self.tr("Task '{}' was aborted or failed.").format(task.name),
                    )
                else:
                    # 发送任务成功通知
                    send_notice(
                        NoticeTiming.WHEN_TASK_SUCCESS,
                        self.tr("Task Completed"),
                        self.tr("Task '{}' has been completed successfully.").format(task.name),
                    )
                # 清除当前执行任务记录
                self._current_running_task_id = None
                return
            else:
                logger.info("开始执行任务序列...")
                self._tasks_started = True
                for task in self.task_service.current_tasks:
                    if task.name in [_CONTROLLER_, _RESOURCE_, POST_ACTION]:
                        continue

                    elif not task.is_checked:
                        continue

                    elif task.is_special:
                        continue

                    # 跳过被隐藏的任务
                    if task.is_hidden:
                        logger.info(f"任务 '{task.name}' 被隐藏，跳过执行")
                        continue

                    # 根据资源过滤任务：跳过隐藏的任务
                    if not self._should_run_task_by_resource(task):
                        logger.info(f"任务 '{task.name}' 因资源过滤被跳过")
                        continue

                    logger.info(f"开始执行任务: {task.name}")
                    # 每个任务开始前，假定其可以正常完成
                    self._current_task_ok = True
                    # 记录当前正在执行的任务，用于超时处理
                    self._current_running_task_id = task.item_id
                    try:
                        task_result = await self.run_task(task.item_id)
                        if task_result == "skipped":
                            continue
                        # 如果任务显式返回 False，视为致命失败，终止整个任务流
                        if task_result is False:
                            msg = f"任务执行失败: {task.name}, 返回 False，终止流程"
                            logger.error(msg)
                            # 发送任务失败通知
                            send_notice(
                                NoticeTiming.WHEN_TASK_FAILED,
                                self.tr("Task Failed"),
                                self.tr("Task '{}' failed and the flow was terminated.").format(task.name),
                            )
                            await self.stop_task()
                            break

                        # 任务运行过程中如果触发了 abort 信号，则认为该任务未成功完成，
                        # 但不中断整个任务流，直接切换到下一个任务。
                        if not self._current_task_ok:
                            logger.warning(
                                f"任务执行被中途中止(abort): {task.name}，切换到下一个任务"
                            )
                            # 发送任务失败通知
                            send_notice(
                                NoticeTiming.WHEN_TASK_FAILED,
                                self.tr("Task Failed"),
                                self.tr("Task '{}' was aborted.").format(task.name),
                            )
                        else:
                            # 发送任务成功通知
                            send_notice(
                                NoticeTiming.WHEN_TASK_SUCCESS,
                                self.tr("Task Completed"),
                                self.tr("Task '{}' has been completed successfully.").format(task.name),
                            )

                        logger.info(f"任务执行完成: {task.name}")
                        # 任务成功后重置重启计数，以便下一个任务重新开始计数
                        # 注意：状态清除由 UI 层控制，这里只重置内存中的计数
                        self._reset_timeout_attempts_if_needed()

                    except Exception as exc:
                        logger.error(f"任务执行失败: {task.name}, 错误: {str(exc)}")
                        # 发送任务失败通知
                        send_notice(
                            NoticeTiming.WHEN_TASK_FAILED,
                            self.tr("Task Failed"),
                            self.tr("Task '{}' failed with error: {}").format(task.name, str(exc)),
                        )
                        # 任务失败后也重置重启计数
                        # 注意：状态清除由 UI 层控制，这里只重置内存中的计数
                        self._reset_timeout_attempts_if_needed()

                    # 清除当前执行任务记录
                    self._current_running_task_id = None

                    if self.need_stop:
                        if self._manual_stop:
                            logger.info("收到手动停止请求，流程终止")
                        else:
                            logger.info("收到停止请求，流程终止")
                        break

                # 只有在任务流正常完成（非手动停止）时才输出"所有任务都已完成"
                if self._is_tasks_flow_completed_normally():
                    signalBus.log_output.emit(
                        "INFO", self.tr("All tasks have been completed")
                    )

        except Exception as exc:
            logger.error(f"任务流程执行异常: {str(exc)}")
            signalBus.log_output.emit("ERROR", self.tr("Task flow error: ") + str(exc))
            import traceback

            logger.critical(traceback.format_exc())
        finally:
            # 判断是否需要执行完成后操作
            should_run_post_action = (
                not self.need_stop and not is_single_task_mode and self._tasks_started
            )
            try:
                if should_run_post_action:
                    await self._handle_post_action()
                else:
                    if not self._tasks_started:
                        logger.info("跳过完成后操作：任务流未成功启动")
                    else:
                        logger.info("跳过完成后操作：手动停止或单任务执行")
            except Exception as exc:
                logger.error(f"完成后操作执行失败: {exc}")

            await self.stop_task()

            # 断开日志收集信号
            signalBus.log_output.disconnect(collect_log)

            # 发送收集的日志信息（仅在非手动停止且非超时停止时发送）
            # 超时停止时已经发送了超时通知，避免重复发送任务流完成通知
            if not self._manual_stop and not self._timeout_stop and log_messages:
                # 将日志信息格式化为文本
                log_text_lines = []
                for level, text in log_messages:
                    # 翻译日志级别
                    translated_level = self._translate_log_level(level)
                    log_text_lines.append(f"[{translated_level}] {text}")
                log_text = "\n".join(log_text_lines)

                send_notice(
                    NoticeTiming.WHEN_POST_TASK,
                    self.tr("Task Flow Completed"),
                    log_text,
                )

            self._is_running = False

            next_config = self._next_config_to_run
            self._next_config_to_run = None
            if next_config:
                logger.info(f"完成后自动启动配置: {next_config}")
                asyncio.create_task(self.run_tasks_flow())

    def _translate_log_level(self, level: str) -> str:
        """翻译日志级别"""
        level_upper = (level or "").upper()
        level_map = {
            "INFO": self.tr("INFO"),
            "WARNING": self.tr("WARNING"),
            "ERROR": self.tr("ERROR"),
            "CRITICAL": self.tr("CRITICAL"),
        }
        return level_map.get(level_upper, level)

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
        elif controller_type == "win32":
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
            # 所有资源路径均为相对路径：优先相对于当前 bundle.path，再回落到项目根目录
            bundle_path_str = self.bundle_path or "./"

            # 先解析 bundle 基础目录为绝对路径
            bundle_base = Path(bundle_path_str)
            if not bundle_base.is_absolute():
                bundle_base = (Path.cwd() / bundle_base).resolve()

            # 兼容旧格式：移除占位符 {PROJECT_DIR}，并清理前导分隔符
            raw = str(path_item)
            raw = raw.replace("{PROJECT_DIR}", "")
            normalized = raw.lstrip("\\/")

            # 资源实际路径 = bundle 基础目录 / 相对资源路径
            resource = (bundle_base / normalized).resolve()
            if not resource.exists():
                logger.error(f"资源不存在: {resource}")
                signalBus.log_output.emit(
                    "ERROR",
                    self.tr("Resource ")
                    + path_item
                    + self.tr(" not found in bundle: ")
                    + bundle_path_str,
                )
                signalBus.log_output.emit(
                    "ERROR", self.tr("please try to reset resource in setting")
                )
                return False

            logger.debug(f"加载资源: {resource}")
            res_cfg = self.task_service.get_task(_RESOURCE_)
            gpu_idx = res_cfg.task_option.get("gpu", -1) if res_cfg else -1
            await self.maafw.load_resource(resource, gpu_idx)
            logger.debug(f"资源加载完成: {resource}")
        return True

    async def run_task(self, task_id: str, skip_speedrun: bool = False):
        """执行指定任务"""
        task = self.task_service.get_task(task_id)
        if not task:
            logger.error(f"任务 ID '{task_id}' 不存在")
            return
        elif task.is_hidden:
            logger.warning(f"任务 '{task.name}' 被隐藏，跳过执行")
            return
        elif not task.is_checked:
            logger.warning(f"任务 '{task.name}' 未被选中，跳过执行")
            return
        speedrun_cfg = self._resolve_speedrun_config(task)
        # 仅依据任务自身的速通开关，不再依赖全局 speedrun_mode；单任务执行可跳过校验
        if (not skip_speedrun) and speedrun_cfg and speedrun_cfg.get("enabled", False):
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
            else:
                signalBus.log_output.emit(
                    "INFO", self.tr("Speedrun rule allows execution")
                )

        raw_info = self.task_service.get_task_execution_info(task_id)
        logger.info(f"任务 '{task.name}' 的执行信息: {raw_info}")
        if raw_info is None:
            logger.error(f"无法获取任务 '{task.name}' 的执行信息")
            return

        entry = raw_info.get("entry", "") or ""
        pipeline_override = raw_info.get("pipeline_override", {})

        if not self.maafw.resource:
            logger.error("资源未初始化，无法执行任务")
            return

        self._start_task_timeout(entry)

        if not await self.maafw.run_task(
            entry, pipeline_override, cfg.get(cfg.save_screenshot)
        ):
            logger.error(f"任务 '{task.name}' 执行失败")
            # 发送任务失败通知
            send_notice(
                NoticeTiming.WHEN_TASK_FAILED,
                self.tr("Task Failed"),
                self.tr("Task '{}' execution failed.").format(task.name),
            )
            self._stop_task_timeout()
            return
        self._stop_task_timeout()
        # 仅在任务未被 abort 且正常完成时记录速通耗时
        if self._current_task_ok:
            self._record_speedrun_runtime(task)

    async def stop_task(self, *, manual: bool = False):
        """停止当前正在运行的任务

        Args:
            manual: 是否为“手动停止”（由用户或外部调用显式触发）。
        """
        if self.need_stop:
            return
        self.need_stop = True
        if manual:
            self._manual_stop = True
        self._stop_task_timeout()
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

    def _start_task_timeout(self, entry: str):
        """开始任务超时计时"""
        if not cfg.get(cfg.task_timeout_enable):
            self._reset_task_timeout_state()
            return

        timeout_seconds = int(cfg.get(cfg.task_timeout) or 0)
        if timeout_seconds <= 0:
            self._reset_task_timeout_state()
            return

        entry_text = (entry or "").strip() or self.tr("Unknown Task Entry")
        # 如果entry不同，重置计数器
        if entry_text != self._timeout_active_entry:
            self._timeout_active_entry = entry_text
            # 如果不是超时重启，重置计数器
            if not self._is_timeout_restart:
                self._timeout_restart_attempts = 0
            # 如果是超时重启且entry不同，应该不会发生（超时重启时entry应该相同）
            # 但为了安全，如果entry不同，重置为0
            elif self._is_timeout_restart:
                self._timeout_restart_attempts = 0
        # entry相同且是超时重启时，保持当前计数（已在 run_tasks_flow 中恢复）

        self._timeout_timer.stop()
        self._timeout_timer.start(timeout_seconds * 1000)

    def _stop_task_timeout(self):
        """停止任务超时计时"""
        self._timeout_timer.stop()

    def _reset_task_timeout_state(self):
        """重置任务超时状态"""
        self._timeout_timer.stop()
        # 注意：配置中的状态清除由 UI 层控制
        self._timeout_active_entry = ""
        self._timeout_restart_attempts = 0
        self._current_running_task_id = None

    def _reset_timeout_attempts_if_needed(self):
        """在任务完成或失败时重置超时重启计数（如果不在超时重启流程中）"""
        if not self._is_timeout_restart and self._timeout_restart_attempts > 0:
            self._timeout_restart_attempts = 0

    def _is_tasks_flow_completed_normally(self) -> bool:
        """判断任务流是否正常完成（非手动停止）"""
        return not self.need_stop and not self._manual_stop

    def _handle_timeout_restart(self, entry_text: str) -> None:
        """处理任务超时重启逻辑"""
        self._timeout_restart_attempts += 1
        restart_message = self.tr(
            "Task entry {} timed out, restarting attempt {}/3."
        ).format(entry_text, self._timeout_restart_attempts)
        logger.info(restart_message)
        signalBus.log_output.emit("WARNING", restart_message)
        # 通过信号通知外部需要重启，传递 entry 和 attempts 信息
        # UI 层负责保存状态
        self.task_timeout_restart_requested.emit(
            entry_text, self._timeout_restart_attempts
        )
        # 注意：重启模式下不立即发送通知，等待最终总结时发送

    def _on_task_timeout(self):
        """任务超时处理"""
        self._timeout_timer.stop()
        timeout_seconds = int(cfg.get(cfg.task_timeout) or 0)
        entry_text = self._timeout_active_entry or self.tr("Unknown Task Entry")
        timeout_message = self.tr("Task entry {} timed out after {} seconds.").format(
            entry_text, timeout_seconds
        )
        logger.warning(timeout_message)
        signalBus.log_output.emit("WARNING", timeout_message)

        action_value = cfg.get(cfg.task_timeout_action)
        try:
            action = Config.TaskTimeoutAction(action_value)
        except ValueError:
            action = Config.TaskTimeoutAction.NOTIFY_ONLY

        if action == Config.TaskTimeoutAction.NOTIFY_ONLY:
            # 仅通知模式：立即发送超时通知
            send_notice(
                NoticeTiming.WHEN_TASK_TIMEOUT,
                self.tr("Task Timeout"),
                self.tr("Task entry '{}' timed out after {} seconds.").format(
                    entry_text, timeout_seconds
                ),
            )
            self._reset_task_timeout_state()
            return

        # 重启并通知模式
        if self._timeout_restart_attempts < 3:
            self._handle_timeout_restart(entry_text)
            return

        # 超过3次重启，停止任务并发送通知
        stop_message = self.tr(
            "Task entry {} timed out after {} restarts, stopping flow."
        ).format(entry_text, self._timeout_restart_attempts)
        logger.error(stop_message)
        signalBus.log_output.emit("ERROR", stop_message)
        # 标记为超时停止，避免在 finally 块中重复发送任务流完成通知
        self._timeout_stop = True
        # 发送超时停止通知
        send_notice(
            NoticeTiming.WHEN_TASK_TIMEOUT,
            self.tr("Task Timeout - Flow Stopped"),
            self.tr(
                "Task entry '{}' timed out after {} restart attempts, flow stopped."
            ).format(entry_text, self._timeout_restart_attempts),
        )
        asyncio.create_task(self.stop_task())
        self._reset_task_timeout_state()
        return

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

        # 获取控制器类型（adb或win32）
        controller_type = self._get_controller_type(controller_raw)

        self.adb_controller_raw = controller_raw
        self.adb_activate_controller = activate_controller

        # 使用控制器类型作为键来获取配置
        controller_raw.setdefault(controller_type, {})
        controller_config = controller_raw[controller_type]
        self.adb_controller_config = controller_config

        logger.info("每次连接前自动搜索 ADB 设备...")
        signalBus.log_output.emit("INFO", self.tr("Auto searching ADB devices..."))
        found_device = await self._auto_find_adb_device(
            controller_raw, controller_type, controller_config
        )
        if found_device:
            logger.info("检测到与配置匹配的 ADB 设备，更新连接参数")
            self._save_device_to_config(controller_raw, controller_type, found_device)
            controller_config = controller_raw[controller_type]
            self.adb_controller_config = controller_config
        else:
            logger.debug("未匹配到与配置一致的 ADB 设备，继续使用当前配置")

        adb_path = controller_config.get("adb_path", "")
        address = controller_config.get("address", "")

        # 检查 adb 路径和连接地址
        if not adb_path:
            error_msg = self.tr(
                "ADB path is empty, please configure ADB path in settings"
            )
            logger.error("ADB 路径为空")
            signalBus.log_output.emit("ERROR", error_msg)
            return False

        if not address:
            error_msg = self.tr(
                "ADB connection address is empty, please configure device connection in settings"
            )
            logger.error("ADB 连接地址为空")
            signalBus.log_output.emit("ERROR", error_msg)
            return False
        raw_input_method = int(controller_config.get("input_methods", -1))

        raw_screen_method = int(controller_config.get("screencap_methods", -1))

        def normalize_input_method(value: int) -> int:
            mask = (1 << 64) - 1
            value &= mask
            if value & (1 << 63):
                value -= 1 << 64
            return value

        input_method = normalize_input_method(raw_input_method)
        screen_method = normalize_input_method(raw_screen_method)
        config = controller_config.get("config", {})
        logger.debug(
            (
                f"ADB 参数类型: adb_path={type(adb_path)}, address={type(address)}, "
                f"screen_method={screen_method}({type(screen_method)}), "
                f"input_method={input_method}({type(input_method)})"
            )
        )
        logger.debug(
            f"ADB 参数值: adb_path={adb_path}, address={address}, screen_method={screen_method}, input_method={input_method}"
        )
        logger.debug(f"ADB 参数配置: config={config}")

        if await self.maafw.connect_adb(
            adb_path,
            address,
            screen_method,
            input_method,
            config,
        ):
            return True
        elif controller_config.get("emulator_path", ""):
            logger.info("尝试启动模拟器")
            signalBus.log_output.emit("INFO", self.tr("try to start emulator"))
            emu_path = controller_config.get("emulator_path", "")
            emu_params = controller_config.get("emulator_params", "")
            wait_emu_start = int(controller_config.get("wait_time", 0))

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
        signalBus.log_output.emit("ERROR", self.tr("Device connection failed"))
        return False

    async def _connect_win32_controller(self, controller_raw: Dict[str, Any]):
        """连接 Win32 控制器"""
        activate_controller = controller_raw.get("controller_type")
        if activate_controller is None:
            logger.error(f"未找到控制器配置: {controller_raw}")
            return False

        # 获取控制器类型（adb或win32）
        controller_type = self._get_controller_type(controller_raw)

        # 使用控制器类型作为键来获取配置
        controller_raw.setdefault(controller_type, {})
        controller_config = controller_raw[controller_type]

        hwnd = controller_config.get("hwnd", 0)
        screencap_method: int = controller_config.get("win32_screencap_methods", 0)
        mouse_method: int = controller_config.get("mouse_input_methods", 0)
        keyboard_method: int = controller_config.get("keyboard_input_methods", 0)

        logger.info("每次连接前自动搜索 Win32 窗口...")
        signalBus.log_output.emit("INFO", self.tr("Auto searching Win32 windows..."))
        found_device = await self._auto_find_win32_window(
            controller_raw, controller_type, controller_config
        )
        if found_device:
            logger.info("检测到与配置匹配的 Win32 窗口，更新连接参数")
            self._save_device_to_config(controller_raw, controller_type, found_device)
            controller_config = controller_raw[controller_type]
        else:
            logger.debug("未匹配到与配置一致的 Win32 窗口，继续使用当前配置")

        hwnd = int(controller_config.get("hwnd", 0))
        screencap_method = controller_config.get("win32_screencap_methods", 1)
        mouse_method = controller_config.get("mouse_input_methods", 1)
        keyboard_method = controller_config.get("keyboard_input_methods", 1)

        # 检查 hwnd 是否为空
        if not hwnd:
            error_msg = self.tr(
                "Window handle (hwnd) is empty, please configure window connection in settings"
            )
            logger.error("Win32 窗口句柄为空")
            signalBus.log_output.emit("ERROR", error_msg)
            return False

        logger.debug(
            f"Win32 参数类型: hwnd={hwnd}, screencap_method={screencap_method}, mouse_method={mouse_method}, keyboard_method={keyboard_method}"
        )

        if await self.maafw.connect_win32hwnd(
            hwnd,
            screencap_method,
            mouse_method,
            keyboard_method,
        ):
            return True
        elif controller_config.get("program_path", ""):
            logger.info("尝试启动程序")
            signalBus.log_output.emit("INFO", self.tr("try to start program"))
            program_path = controller_config.get("program_path", "")
            program_params = controller_config.get("program_params", "")
            wait_program_start = int(controller_config.get("wait_launch_time", 0))
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

    def _parse_address_components(self, address: str | None) -> tuple[str, str | None]:
        """提取 ADB 地址和端口"""
        raw_address = (address or "").strip()
        if not raw_address:
            return "", None
        if ":" in raw_address:
            host, port = raw_address.rsplit(":", 1)
            return host.strip(), port.strip() or None
        return raw_address, None

    def _should_use_new_adb_device(
        self,
        old_config: Dict[str, Any],
        new_device: Dict[str, Any] | None,
    ) -> bool:
        """判断自动搜索到的 ADB 设备是否和旧配置一致"""
        if not new_device:
            return False

        old_name = (old_config.get("device_name") or "").strip()
        new_name = (new_device.get("device_name") or "").strip()
        old_host, old_port = self._parse_address_components(old_config.get("address"))
        new_host, new_port = self._parse_address_components(new_device.get("address"))

        fields_present = sum(bool(value) for value in (old_name, old_host, old_port))
        if fields_present < 2:
            return True

        match_count = 0
        if old_name and new_name and old_name == new_name:
            match_count += 1
        if old_host and new_host and old_host == new_host:
            match_count += 1
        if old_port and new_port and old_port == new_port:
            match_count += 1

        return match_count >= 2

    def _should_use_new_win32_window(
        self,
        old_config: Dict[str, Any],
        new_device: Dict[str, Any] | None,
    ) -> bool:
        """判断自动搜索到的 Win32 窗口是否属于旧配置"""
        if not new_device:
            return False

        old_name = (old_config.get("device_name") or "").strip()
        new_name = (new_device.get("device_name") or "").strip()

        # 如果旧配置没有设备名，只要有新设备名就使用
        if not old_name:
            return bool(new_name)
        # 如果旧配置有设备名，需要新设备名存在且与旧配置匹配
        elif new_name:
            return old_name == new_name
        else:
            return False

    def _start_process(
        self, entry: str | Path, argv: list[str] | tuple[str, ...] | str | None = None
    ) -> subprocess.Popen:
        """根据入口路径/命令开启子进程，返回 Popen 对象"""
        command = [str(entry)]
        if argv is not None:
            import shlex

            if isinstance(argv, (list, tuple)):
                # If argv is already a list/tuple, just append the arguments directly
                # Don't split them again as they're already parsed
                command.extend(str(arg) for arg in argv)
            else:
                # If argv is a string, split it properly
                command.extend(shlex.split(str(argv)))

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
        self,
        controller_raw: Dict[str, Any],
        controller_type: str,
        controller_config: Dict[str, Any],
    ) -> Dict[str, Any] | None:
        """自动搜索 ADB 设备并找到与旧配置一致的那一项"""
        try:
            devices = Toolkit.find_adb_devices()
            if not devices:
                logger.warning("未找到任何 ADB 设备")
                return None

            for device in devices:
                # 优先使用 config 中的雷电 pid，补充给解析函数
                ld_pid_cfg = (
                    controller_config.get("config", {})
                    .get("extras", {})
                    .get("ld", {})
                    .get("pid")
                )
                device_index = EmulatorHelper.resolve_emulator_index(
                    device, ld_pid=ld_pid_cfg
                )
                display_name = (
                    f"{device.name}[{device_index}]({device.address})"
                    if device_index is not None
                    else f"{device.name}({device.address})"
                )

                device_info = {
                    "adb_path": str(device.adb_path),
                    "address": device.address,
                    "screencap_methods": device.screencap_methods,
                    "input_methods": device.input_methods,
                    "config": device.config,
                    "device_name": display_name,
                }
                if self._should_use_new_adb_device(controller_config, device_info):
                    return device_info
            logger.debug("ADB 设备列表均未满足与配置匹配的条件，跳过更新")
            return None

        except Exception as e:
            logger.error(f"自动搜索 ADB 设备时出错: {e}")
            return None

    async def _auto_find_win32_window(
        self,
        controller_raw: Dict[str, Any],
        controller_type: str,
        controller_config: Dict[str, Any],
    ) -> Dict[str, Any] | None:
        """自动搜索 Win32 窗口并找到与旧配置一致的那一项"""
        try:
            windows = Toolkit.find_desktop_windows()
            if not windows:
                logger.warning("未找到任何 Win32 窗口")
                return None

            for window in windows:
                window_info = {
                    "hwnd": str(window.hwnd),
                    "window_name": window.window_name,
                    "class_name": window.class_name,
                    "device_name": f"{window.window_name or 'Unknown Window'}({window.hwnd})",
                }
                if self._should_use_new_win32_window(controller_config, window_info):
                    return window_info
            logger.debug("Win32 窗口列表均未满足与配置匹配的条件，跳过更新")
            return None

        except Exception as e:
            logger.error(f"自动搜索 Win32 窗口时出错: {e}")
            return None

    def _save_device_to_config(
        self,
        controller_raw: Dict[str, Any],
        controller_type: str,
        device_info: Dict[str, Any],
    ) -> None:
        """保存设备信息到配置

        Args:
            controller_raw: 控制器原始配置
            controller_type: 控制器类型（"adb"或"win32"）
            device_info: 设备信息字典
        """
        try:
            # 确保控制器配置存在（使用控制器类型作为键）
            if controller_type not in controller_raw:
                controller_raw[controller_type] = {}

            # 更新设备信息
            controller_raw[controller_type].update(device_info)

            # 获取预配置任务并更新
            if controller_cfg := self.task_service.get_task(_CONTROLLER_):
                controller_cfg.task_option.update(controller_raw)
                self.task_service.update_task(controller_cfg)
                logger.info(f"设备配置已保存: {device_info.get('device_name', '')}")

        except Exception as e:
            logger.error(f"保存设备配置时出错: {e}")

    async def _handle_post_action(self) -> None:
        """统一处理完成后操作顺序，按选项顺序执行，支持多个动作"""
        post_task = self.task_service.get_task(POST_ACTION)
        if not post_task:
            return

        post_config = post_task.task_option.get("post_action")
        if not isinstance(post_config, dict):
            return

        # 按照界面定义的顺序执行动作
        # 1. 如果选择了"无动作"，直接返回（不会与其他选项同时存在）
        if post_config.get("none"):
            logger.info("完成后操作: 无动作")
            return

        # 2. 如果选择了"关闭模拟器"，执行关闭模拟器
        if post_config.get("close_emulator"):
            logger.info("完成后操作: 关闭模拟器")
            self._close_emulator()

        # 3. 如果选择了"运行其他程序"，执行并等待程序退出
        if post_config.get("run_program"):
            logger.info("完成后操作: 运行其他程序")
            await self._run_program_from_post_action(
                post_config.get("program_path", ""),
                post_config.get("program_args", ""),
            )

        # 4. 如果选择了"运行其他配置"，切换配置（继续执行后续操作）
        if post_config.get("run_other"):
            if target_config := (post_config.get("target_config") or "").strip():
                await self._run_other_configuration(target_config)
            else:
                logger.warning("完成后运行其他配置开关被激活，但未配置目标配置")

        # 5. 如果选择了"退出软件"，执行退出软件（这会退出应用）
        if post_config.get("close_software"):
            logger.info("完成后操作: 退出软件")
            await self._close_software()
            return  # 退出软件后不再执行后续操作

        # 6. 如果选择了"关机"，执行关机（这会关闭系统）
        if post_config.get("shutdown"):
            logger.info("完成后操作: 关机")
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
            self._next_config_to_run = config_id
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
        """关闭模拟器"""
        if self.adb_controller_config is None:
            return

        adb_address = self.adb_controller_config.get("address", "")
        if ":" in adb_address:
            adb_port = adb_address.split(":")[-1]
        elif "-" in adb_address:
            adb_port = adb_address.split("-")[-1]
        else:
            adb_port = None
        adb_path = self.adb_controller_config.get("adb_path")

        device_name = self.adb_controller_config.get("device_name", "")

        if "mumuplayer12" in device_name.lower():
            EmulatorHelper.close_mumu(adb_path, adb_port)
        elif "ldplayer" in device_name.lower():
            ld_pid_cfg = (
                self.adb_controller_config.get("config", {})
                .get("extras", {})
                .get("ld", {})
                .get("pid")
            )
            EmulatorHelper.close_ldplayer(adb_path, ld_pid_cfg)
        else:
            logger.warning(f"未找到对应的模拟器: {device_name}")

    def shutdown(self):
        """
        关机
        """
        shutdown_commands = {
            "Windows": "shutdown /s /t 1",
            "Linux": "shutdown now",
            "Darwin": "sudo shutdown -h now",  # macOS
        }
        os.system(shutdown_commands.get(platform.system(), ""))

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

    def _resolve_speedrun_config(self, task: TaskItem) -> Dict[str, Any] | None:
        """优先使用任务保存的速通配置，其次使用 interface，最终回落默认值"""
        try:
            if not isinstance(task.task_option, dict):
                task.task_option = {}

            existing_cfg = task.task_option.get("_speedrun_config")
            merged_cfg = self.task_service.build_speedrun_config(
                task.name, existing_cfg
            )
            if task.task_option.get("_speedrun_config") != merged_cfg:
                task.task_option["_speedrun_config"] = merged_cfg
                self.task_service.update_task(task)
            return merged_cfg if isinstance(merged_cfg, dict) else {}
        except Exception as exc:
            logger.warning(f"合成速通配置失败，使用 interface 数据: {exc}")
            interface_task = self._get_task_by_name(task.name)
            return (
                interface_task.get("speedrun")
                if interface_task and isinstance(interface_task, dict)
                else {}
            )

    def _evaluate_speedrun(
        self, task: TaskItem, speedrun: Dict[str, Any]
    ) -> tuple[bool, str]:
        """校验 speedrun 限制"""
        if not speedrun or not isinstance(speedrun, dict):
            return True, ""

        if speedrun.get("enabled") is False:
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
        # 如果剩余次数小于0，则设置为0
        if remaining_count < 0:
            state["remaining_count"] = 0
            remaining_count = 0
            state_dirty = True

        # 如果当前时间大于下次刷新时间，且剩余次数不等于限制次数，则更新剩余次数
        if now >= next_refresh and state.get("remaining_count") != count_limit_value:
            state["remaining_count"] = count_limit_value
            remaining_count = count_limit_value
            state_dirty = True

        # 如果剩余次数为0，则返回False
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
        epoch = datetime(1970, 1, 1)

        for entry in entries:
            parsed_entry: datetime | None = None
            if isinstance(entry, (int, float)):
                try:
                    parsed_entry = datetime.fromtimestamp(entry)
                except (OverflowError, OSError):
                    parsed_entry = None
            elif isinstance(entry, str):
                try:
                    parsed_entry = datetime.fromisoformat(entry)
                except ValueError:
                    try:
                        parsed_entry = datetime.fromtimestamp(float(entry))
                    except (TypeError, ValueError, OverflowError, OSError):
                        parsed_entry = None

            # 对不合法时间回退到 epoch
            parsed.append(parsed_entry or epoch)

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
        for day_offset in range(14):
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
        for month_offset in range(24):
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

        hour = max(0, hour)
        # 将小时限制在0-23之间
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

    def _should_run_task_by_resource(self, task: TaskItem) -> bool:
        """根据当前选择的资源判断任务是否应该执行

        规则：
        - 基础任务（资源、完成后操作）始终执行
        - 如果任务没有 resource 字段或 resource 为空列表，表示所有资源都可用，执行
        - 如果任务的 resource 列表包含当前资源，则执行
        - 否则跳过
        """
        # 基础任务始终执行
        if task.is_base_task():
            return True

        try:
            resource_cfg = self.task_service.get_task(_RESOURCE_)  # sourcery skip
            if not resource_cfg:
                return True  # 如果没有资源设置任务，执行所有任务

            current_resource_name = resource_cfg.task_option.get("resource", "")
            if not current_resource_name:
                return True

            # 获取 interface 中的任务定义
            interface = self.task_service.interface
            if not interface:
                return True

            # 查找任务定义中的 resource 字段
            for task_def in interface.get("task", []):
                if task_def.get("name") == task.name:
                    task_resources = task_def.get("resource", [])
                    # 如果任务没有 resource 字段，或者 resource 为空列表，表示所有资源都可用
                    if not task_resources:
                        return True
                    # 如果任务的 resource 列表包含当前资源，则执行
                    if current_resource_name in task_resources:
                        return True
                    return False

            # 如果找不到任务定义，默认执行
            return True
        except Exception:
            # 发生错误时，默认执行所有任务
            return True
