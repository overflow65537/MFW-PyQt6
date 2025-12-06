"""
MFW-ChainFlow Assistant
MFW-ChainFlow Assistant MaaFW核心
原作者: MaaXYZ
地址: https://github.com/MaaXYZ/MaaDebugger
修改:overflow65537
"""

import re
from enum import Enum
from typing import List, Dict
import subprocess
import threading
from pathlib import Path
import numpy
from asyncify import asyncify

import maa
from maa.context import Context, ContextEventSink
from maa.custom_action import CustomAction
from maa.custom_recognition import CustomRecognition

from maa.controller import AdbController, Win32Controller
from maa.tasker import Tasker
from maa.agent_client import AgentClient
from maa.resource import Resource
from maa.toolkit import Toolkit, AdbDevice, DesktopWindow
from maa.define import (
    MaaAdbScreencapMethodEnum,
    MaaAdbInputMethodEnum,
    MaaWin32InputMethodEnum,
    MaaWin32ScreencapMethodEnum,
)
from PySide6.QtCore import QObject, Signal

from app.utils.logger import logger


# 以下代码引用自 MaaDebugger 项目的 ./src/MaaDebugger/maafw/__init__.py 文件，用于生成maafw实例
class MaaFWError(Enum):
    RESOURCE_OR_CONTROLLER_NOT_INITIALIZED = 1
    AGENT_CONNECTION_FAILED = 2
    TASKER_NOT_INITIALIZED = 3
    AGENT_CONFIG_MISSING = 4
    AGENT_CONFIG_EMPTY_LIST = 5
    AGENT_CONFIG_INVALID = 6
    AGENT_CHILD_EXEC_MISSING = 7
    AGENT_START_FAILED = 8


from maa.controller import ControllerEventSink, Controller, NotificationType
from maa.resource import ResourceEventSink, Resource
from maa.tasker import TaskerEventSink, Tasker
from maa.context import ContextEventSink, Context

from app.common.signal_bus import signalBus


class MaaContextSink(ContextEventSink):
    def on_raw_notification(self, context: Context, msg: str, details: dict):
        if detial := details.get("focus", {}).get(msg, ""):
            detial = detial.replace("{name}", details.get("name", ""))
            detial = detial.replace("{task_id}", str(details.get("task_id", "")))
            detial = detial.replace("{list}", details.get("list", ""))
            signalBus.callback.emit({"name": "context", "details": detial})

    def on_node_next_list(
        self,
        context: Context,
        noti_type: NotificationType,
        detail: ContextEventSink.NodeNextListDetail,
    ):
        pass

    def on_node_action(
        self,
        context: Context,
        noti_type: NotificationType,
        detail: ContextEventSink.NodeActionDetail,
    ):
        pass

    def on_node_recognition(
        self,
        context: Context,
        noti_type: NotificationType,
        detail: ContextEventSink.NodeRecognitionDetail,
    ):
        pass


class MaaControllerEventSink(ControllerEventSink):
    def on_raw_notification(self, controller: Controller, msg: str, details: dict):
        pass

    def on_controller_action(
        self,
        controller: Controller,
        noti_type: NotificationType,
        detail: ControllerEventSink.ControllerActionDetail,
    ):
        #signalBus.callback.emit({"name": "controller", "status": noti_type.value})
        pass


class MaaResourceEventSink(ResourceEventSink):
    def on_raw_notification(self, resource: Resource, msg: str, details: dict):
        pass

    def on_resource_loading(
        self,
        resource: Resource,
        noti_type: NotificationType,
        detail: ResourceEventSink.ResourceLoadingDetail,
    ):
        signalBus.callback.emit({"name": "resource", "status": noti_type.value})


class MaaTaskerEventSink(TaskerEventSink):
    def on_raw_notification(self, tasker: Tasker, msg: str, details: dict):
        pass
        print(f"任务器原始信息:{msg},详细信息:{details}")

    def on_tasker_task(
        self,
        tasker: Tasker,
        noti_type: NotificationType,
        detail: TaskerEventSink.TaskerTaskDetail,
    ):
        signalBus.callback.emit(
            {"name": "task", "task": detail.entry, "status": noti_type.value}
        )


maa_context_sink = MaaContextSink()
maa_controller_sink = MaaControllerEventSink()
maa_resource_sink = MaaResourceEventSink()
maa_tasker_sink = MaaTaskerEventSink()


class MaaFW(QObject):

    resource: Resource | None
    controller: AdbController | Win32Controller | None
    tasker: Tasker | None
    agent: AgentClient | None

    agent_thread: subprocess.Popen | None
    agent_output_thread: threading.Thread | None

    maa_controller_sink: MaaControllerEventSink | None
    maa_context_sink: MaaContextSink | None
    maa_resource_sink: MaaResourceEventSink | None
    maa_tasker_sink: MaaTaskerEventSink | None

    custom_info = Signal(int)
    agent_info = Signal(str)

    # 超时后仍未停止的 agent 进程最长等待时间
    AGENT_TERMINATE_TIMEOUT_SECONDS: float = 5.0

    def __init__(
        self,
        maa_controller_sink: MaaControllerEventSink | None = None,
        maa_context_sink: MaaContextSink | None = None,
        maa_resource_sink: MaaResourceEventSink | None = None,
        maa_tasker_sink: MaaTaskerEventSink | None = None,
    ):
        # 确保正确初始化 QObject 基类，避免 Qt 运行时错误
        super().__init__()

        Toolkit.init_option("./")
        self.resource = None
        self.controller = None
        self.tasker = None

        # 这里传入的是 Sink 类，需要在此处实例化，避免把类对象/descriptor 直接交给底层 C 接口
        self.maa_controller_sink = maa_controller_sink
        self.maa_context_sink = maa_context_sink
        self.maa_resource_sink = maa_resource_sink
        self.maa_tasker_sink = maa_tasker_sink

        self.agent = None
        self.agent_thread = None
        self.agent_output_thread = None

        self.agent_data_raw = None

    @staticmethod
    @asyncify
    def detect_adb() -> List[AdbDevice]:
        return Toolkit.find_adb_devices()

    @staticmethod
    @asyncify
    def detect_win32hwnd(window_regex: str) -> List[DesktopWindow]:
        windows = Toolkit.find_desktop_windows()
        result = []
        for win in windows:
            if not re.search(window_regex, win.window_name):
                continue

            result.append(win)

        return result

    @asyncify
    def connect_adb(
        self,
        adb_path: str,
        address: str,
        screencap_method: int = 0,
        input_method: int = 0,
        config: Dict = {},
    ) -> bool:
        screencap_method = MaaAdbScreencapMethodEnum(screencap_method)

        input_method = MaaAdbInputMethodEnum(input_method)

        controller = AdbController(
            adb_path, address, screencap_method, input_method, config
        )
        controller = self._init_controller(controller)
        connected = controller.post_connection().wait().succeeded
        if not connected:
            print(f"Failed to connect {adb_path} {address}")
            return False

        return True

    @asyncify
    def connect_win32hwnd(
        self,
        hwnd: int | str,
        screencap_method: int = MaaWin32ScreencapMethodEnum.DXGI_DesktopDup,
        mouse_method: int = MaaWin32InputMethodEnum.Seize,
        keyboard_method: int = MaaWin32InputMethodEnum.Seize,
    ) -> bool:
        if isinstance(hwnd, str):
            hwnd = int(hwnd, 16)
        screencap_method = (
            screencap_method or MaaWin32ScreencapMethodEnum.DXGI_DesktopDup
        )
        mouse_method = mouse_method or MaaWin32InputMethodEnum.Seize
        keyboard_method = keyboard_method or MaaWin32InputMethodEnum.Seize
        controller = Win32Controller(
            hwnd,
            screencap_method=screencap_method,
            mouse_method=mouse_method,
            keyboard_method=keyboard_method,
        )
        controller = self._init_controller(controller)

        connected = controller.post_connection().wait().succeeded
        if not connected:
            print(f"Failed to connect {hwnd}")
            return False

        return True

    def _init_controller(
        self, controller: AdbController | Win32Controller
    ) -> AdbController | Win32Controller:
        if self.maa_controller_sink:
            controller.add_sink(self.maa_controller_sink)
        self.controller = controller
        return self.controller

    def _init_resource(self) -> Resource:
        if self.resource is None:
            self.resource = Resource()
            if self.maa_resource_sink:
                self.resource.add_sink(self.maa_resource_sink)
        return self.resource

    def _init_tasker(self) -> Tasker:
        if self.tasker is None:
            self.tasker = Tasker()
            self.tasker.add_context_sink(self.maa_context_sink)

            if self.maa_tasker_sink:
                self.tasker.add_sink(self.maa_tasker_sink)
        if not self.resource or not self.controller:
            raise RuntimeError("Resource 与 Controller 必须先初始化再初始化 Tasker")
        self.tasker.bind(self.resource, self.controller)
        return self.tasker

    def _init_agent(self, agent_data_raw: dict) -> bool:
        if not (self.resource and self.controller):
            raise RuntimeError("agent 初始化前必须存在 resource/controller")
        if not self.tasker:
            self.tasker = self._init_tasker()
        if self.agent:
            return True

        self.agent = AgentClient()
        self.agent.register_sink(self.resource, self.controller, self.tasker)
        self.agent.bind(self.resource)

        if not agent_data_raw:
            logger.warning("未找到agent配置")
            self._send_custom_info(MaaFWError.AGENT_CONFIG_MISSING)
            return False

        if isinstance(agent_data_raw, list):
            if agent_data_raw:
                agent_data: dict = agent_data_raw[0]
            else:
                agent_data = {}
                logger.warning("agent 配置为一个空列表，使用空字典作为默认值")
                self._send_custom_info(MaaFWError.AGENT_CONFIG_EMPTY_LIST)
        elif isinstance(agent_data_raw, dict):
            agent_data = agent_data_raw
        else:
            agent_data = {}
            logger.warning("agent 配置既不是字典也不是列表，使用空字典作为默认值")
            self._send_custom_info(MaaFWError.AGENT_CONFIG_INVALID)

        child_exec = agent_data.get("child_exec", "")
        if not child_exec:
            logger.warning("agent 配置缺少 child_exec，无法启动")
            self._send_custom_info(MaaFWError.AGENT_CHILD_EXEC_MISSING)
            return False

        socket_id = self.agent.identifier
        if callable(socket_id):
            socket_id = socket_id() or "maafw_socket_id"
        elif socket_id is None:
            socket_id = "maafw_socket_id"
        socket_id = str(socket_id)
        child_args = agent_data.get("child_args", [])
        project_dir = Path.cwd()
        child_args = [
            arg.replace("{PROJECT_DIR}", str(project_dir)) for arg in child_args
        ]
        agent_process: subprocess.Popen | None = None
        start_cmd = [child_exec, *child_args, socket_id]
        logger.debug(f"启动agent命令: {start_cmd}")
        # 如果是打包模式,使用utf8,否则使用gbk
        import os

        is_packed = os.path.exists("./lrelease.py")
        encoding = "utf-8" if is_packed else "gbk"
        try:
            agent_process = subprocess.Popen(
                start_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding=encoding,
                errors="replace",
                bufsize=1,
            )
            self.agent_thread = agent_process
            self._watch_agent_output(agent_process)
        except Exception as e:
            logger.error(f"启动agent失败: {e}")
            self._send_custom_info(MaaFWError.AGENT_START_FAILED)
            return False
        if self.agent_data_raw and self.agent_data_raw.get("timeout"):
            timeout = self.agent_data_raw.get("timeout")
            self.agent.set_timeout(timeout)
        if not self.agent.connect():
            self._send_custom_info(MaaFWError.AGENT_CONNECTION_FAILED)
            return False
        return True

    @asyncify
    def load_resource(self, dir: str | Path, gpu_index: int = -1) -> bool:
        resource = self._init_resource()
        if not isinstance(gpu_index, int):
            logger.warning("gpu_index 不是 int 类型，使用默认值 -1")
            gpu_index = -1
        if gpu_index == -2:
            logger.debug("设置CPU推理")
            resource.use_cpu()
        elif gpu_index == -1:
            logger.debug("设置自动")
            resource.use_auto_ep()
        else:
            logger.debug(f"设置GPU推理: {gpu_index}")
            resource.use_directml(gpu_index)
        return resource.post_bundle(dir).wait().succeeded

    @asyncify
    def run_task(
        self,
        entry: str,
        pipeline_override: dict = {},
        custom_dir: str | None = None,
        save_draw: bool = False,
    ) -> bool:
        if not self.resource or not self.controller:
            self._send_custom_info(MaaFWError.RESOURCE_OR_CONTROLLER_NOT_INITIALIZED)
            return False

        tasker = self._init_tasker()

        if self.agent_data_raw:
            if not self._init_agent(self.agent_data_raw):
                return False
        if not tasker.inited:
            self._send_custom_info(MaaFWError.TASKER_NOT_INITIALIZED)
            return False
        tasker.set_save_draw(save_draw)
        return tasker.post_task(entry, pipeline_override).wait().succeeded

    @asyncify
    def stop_task(self):
        if self.tasker:
            try:
                self.tasker.post_stop().wait()
            except Exception as e:
                logger.error(f"停止任务失败: {e}")
            finally:
                self.tasker = None
            self.tasker = None
        if self.resource:
            try:
                self.resource.clear()
            except Exception as e:
                logger.error(f"清除资源失败: {e}")
            finally:
                self.resource = None
            self.resource = None
        if self.agent:
            try:
                self.agent.disconnect()
                self.agent_data_raw = None
            except Exception as e:
                logger.error(f"断开agent连接失败: {e}")
            finally:
                self.agent = None
            self.agent = None
        if self.agent_thread:
            try:
                self.agent_thread.terminate()
                try:
                    self.agent_thread.wait(timeout=self.AGENT_TERMINATE_TIMEOUT_SECONDS)
                except subprocess.TimeoutExpired:
                    logger.warning("等待 agent 终止超时，执行 kill 操作")
                    self.agent_thread.kill()
            except Exception as e:
                logger.error(f"终止agent线程失败: {e}")
            finally:
                self.agent_thread = None
        if self.agent_output_thread:
            self.agent_output_thread.join(timeout=0.1)
            self.agent_output_thread = None

    def _send_custom_info(self, error: MaaFWError):
        self.custom_info.emit(error.value)

    def _watch_agent_output(self, process: subprocess.Popen):
        def _forward_output():
            stream = process.stdout
            if not stream:
                return
            for line in stream:
                text = line.rstrip("\r\n")
                if text:
                    self.agent_info.emit(text)
            stream.close()

        watcher = threading.Thread(target=_forward_output, daemon=True)
        watcher.start()
        self.agent_output_thread = watcher

    async def screencap_test(self) -> numpy.ndarray:
        if not self.controller:
            raise RuntimeError("Controller not initialized")
        return self.controller.post_screencap().wait().get()
