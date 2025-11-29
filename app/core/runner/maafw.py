"""
MFW-ChainFlow Assistant
MFW-ChainFlow Assistant MaaFW核心
原作者: MaaXYZ
地址: https://github.com/MaaXYZ/MaaDebugger
修改:overflow65537
"""

import re
import os
import importlib.util
from typing import List, Dict
import subprocess
from pathlib import Path

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

from ...utils.logger import logger
from .maasink import (
    MaaContextSink,
    MaaControllerEventSink,
    MaaResourceEventSink,
    MaaTaskerEventSink,
)


# 以下代码引用自 MaaDebugger 项目的 ./src/MaaDebugger/maafw/__init__.py 文件，用于生成maafw实例
class MaaFW(QObject):

    resource: Resource | None
    controller: AdbController | Win32Controller | None
    tasker: Tasker | None
    agent: AgentClient | None

    agent_thread: subprocess.Popen | None

    maa_controller_sink: MaaControllerEventSink
    maa_context_sink: MaaContextSink
    maa_resource_sink: MaaResourceEventSink
    maa_tasker_sink: MaaTaskerEventSink

    custom_info = Signal(str)

    def __init__(
        self, maa_controller_sink, maa_context_sink, maa_resource_sink, maa_tasker_sink
    ):
        # 确保正确初始化 QObject 基类，避免 Qt 运行时错误
        super().__init__()

        Toolkit.init_option("./")
        self.resource = None
        self.controller = None
        self.tasker = None

        # 这里传入的是 Sink 类，需要在此处实例化，避免把类对象/descriptor 直接交给底层 C 接口
        self.maa_controller_sink = maa_controller_sink()
        self.maa_context_sink = maa_context_sink()
        self.maa_resource_sink = maa_resource_sink()
        self.maa_tasker_sink = maa_tasker_sink()

        self.agent = None
        self.agent_thread = None

        # 防止 stop_task 在短时间内被多次并发调用，导致底层资源重复释放
        self._stopping = False

    def load_custom_objects(self, custom_json_path: str | Path):
        if not os.path.exists(custom_json_path):
            logger.error(f"custom.json 路径不存在: {custom_json_path}")
            return
        logger.info(f"开始加载自定义配置: {custom_json_path}")
        import jsonc

        with open(custom_json_path, "r", encoding="utf-8") as f:
            custom_config: Dict[str, Dict] = jsonc.load(f)
        success = 0
        failed = []
        for custom_name, custom in custom_config.items():
            if self._load_single_custom(custom_name, custom):
                success += 1
            else:
                failed.append(custom_name)
        logger.info(f"自定义加载完成: 成功 {success} 个, 失败 {len(failed)} 个")

    def _load_single_custom(self, custom_name: str, custom: dict) -> bool:
        custom_type: str = custom.get("type", "")
        custom_class_name: str = custom.get("class", "")
        custom_file_path: str = custom.get("file_path", "")
        if not all([custom_type, custom_name, custom_class_name, custom_file_path]):
            logger.warning(f"配置项 {custom} 缺少必要信息，跳过")
            msg = custom_name + self.tr(f" custom load failed: missing info")
            self._send_custom_info(msg)
            return False
        module_name = os.path.splitext(os.path.basename(custom_file_path))[0]
        spec = importlib.util.spec_from_file_location(module_name, custom_file_path)
        if spec is None:
            logger.error(f"无法获取模块 {module_name} 的 spec，跳过加载")
            msg = custom_name + self.tr(f" custom load failed: no spec")
            self._send_custom_info(msg)
            return False
        module = importlib.util.module_from_spec(spec)
        if spec.loader is None:
            logger.error(f"模块 {module_name} 的 loader 为 None，跳过加载")
            msg = custom_name + self.tr(f" custom load failed: no loader")
            self._send_custom_info(msg)
            return False
        try:
            spec.loader.exec_module(module)
        except Exception as e:
            logger.error(f"模块加载异常: {e}")
            msg = custom_name + self.tr(f" custom load failed: module error")
            self._send_custom_info(msg)
            return False
        try:
            class_obj = getattr(module, custom_class_name)
        except Exception as e:
            logger.error(f"获取类对象失败: {e}")
            msg = custom_name + self.tr(f" custom load failed: class error")
            self._send_custom_info(msg)
            return False
        try:
            instance = class_obj()
        except Exception as e:
            logger.error(f"实例化类失败: {e}")
            msg = custom_name + self.tr(f" custom load failed: instance error")
            self._send_custom_info(msg)
            return False
        try:
            if custom_type == "action":
                assert self.resource is not None, "self.resource 不应为 None"
                if self.resource.register_custom_action(custom_name, instance):
                    logger.info(f"加载自定义动作{custom_name}")
                    return True
                else:
                    logger.error(f"注册自定义动作失败: {custom_name}")
                    msg = custom_name + self.tr(f" action load failed")
                    self._send_custom_info(msg)
                    return False
            elif custom_type == "recognition":
                assert self.resource is not None, "self.resource 不应为 None"
                if self.resource.register_custom_recognition(custom_name, instance):
                    logger.info(f"加载自定义识别器{custom_name}")
                    return True
                else:
                    logger.error(f"注册自定义识别器失败: {custom_name}")
                    msg = custom_name + self.tr(f" recognition load failed")
                    self._send_custom_info(msg)
                    return False
            else:
                logger.warning(f"未知类型: {custom_type}")
                msg = custom_name + self.tr(f" custom load failed: unknown type")
                self._send_custom_info(msg)
                return False
        except Exception as e:
            logger.error(f"注册自定义对象失败: {e}")
            msg = custom_name + self.tr(f" custom load failed: register error")
            self._send_custom_info(msg)
            return False

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

        self.controller = AdbController(
            adb_path, address, screencap_method, input_method, config
        )

        self.controller.add_sink(self.maa_controller_sink)
        connected = self.controller.post_connection().wait().succeeded
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
        self.controller = Win32Controller(
            hwnd,
            screencap_method=screencap_method,
            mouse_method=mouse_method,
            keyboard_method=keyboard_method,
        )

        # self.controller.add_sink(self.maa_controller_sink)

        connected = self.controller.post_connection().wait().succeeded
        if not connected:
            print(f"Failed to connect {hwnd}")
            return False

        return True

    @asyncify
    def load_resource(self, dir: str | Path, gpu_index: int = -1) -> bool:
        if not self.resource:
            self.resource = Resource()
            self.resource.add_sink(self.maa_resource_sink)
        if not isinstance(gpu_index, int):
            logger.warning("gpu_index 不是 int 类型，使用默认值 -1")
            gpu_index = -1
        if gpu_index == -2:
            logger.debug("设置CPU推理")
            self.resource.use_cpu()
        elif gpu_index == -1:
            logger.debug("设置自动")
            self.resource.use_auto_ep()
        else:
            logger.debug(f"设置GPU推理: {gpu_index}")
            self.resource.use_directml(gpu_index)
        return self.resource.post_bundle(dir).wait().succeeded

    @asyncify
    def run_task(
        self,
        entry: str,
        pipeline_override: dict = {},
        custom_dir: str | None = None,
        agent_data_raw: dict | None = None,
        save_draw: bool = False,
    ) -> bool:
        if not self.tasker:
            self.tasker = Tasker()
            self.tasker.add_context_sink(self.maa_context_sink)
            self.tasker.add_sink(self.maa_tasker_sink)

        if not self.resource or not self.controller:
            self._send_custom_info(self.tr("Resource or Controller not initialized"))
            return False

        self.tasker.bind(self.resource, self.controller)

        # 动态加载.py
        self.resource.clear_custom_recognition()
        self.resource.clear_custom_action()
        if custom_dir is not None:
            try:
                logger.debug(f"加载自定义内容路径: {custom_dir}")
                self.load_custom_objects(custom_dir)
            except Exception as e:
                logger.error(f"加载自定义内容时发生错误: {e}")

        # agent加载
        if agent_data_raw is not None:
            if isinstance(agent_data_raw, list):
                if agent_data_raw:
                    agent_data: dict = agent_data_raw[0]
                else:
                    agent_data = {}
                    logger.warning("agent 配置为一个空列表，使用空字典作为默认值")
            elif isinstance(agent_data_raw, dict):
                agent_data = agent_data_raw
            else:
                agent_data = {}
                logger.warning("agent 配置既不是字典也不是列表，使用空字典作为默认值")

            if agent_data and agent_data.get("child_exec") and not self.agent:
                self.agent = AgentClient()
                self.agent.register_sink(self.resource, self.controller, self.tasker)
                self.agent.bind(self.resource)
                socket_id = self.agent.identifier
                if callable(socket_id):
                    socket_id = socket_id() or "maafw_socket_id"
                elif socket_id is None:
                    socket_id = "maafw_socket_id"
                socket_id = str(socket_id)
                self._send_custom_info(self.tr("Agent Service Start"))
                print("agent启动")
                try:
                    maa_bin = os.getenv("MAAFW_BINARY_PATH")
                    if not maa_bin:
                        maa_bin = os.getcwd()

                    child_exec = agent_data.get("child_exec", "").replace(
                        "{PROJECT_DIR}", "./"
                    )
                    child_args = agent_data.get("child_args", [])

                    for i in range(len(child_args)):
                        if "{PROJECT_DIR}" in child_args[i]:
                            child_args[i] = child_args[i].replace("{PROJECT_DIR}", "./")
                    print(
                        f"agent启动: {child_exec}\n参数{child_args}\nMAA库地址{maa_bin}\nsocket_id: {socket_id}"
                    )

                    self.agent_thread = subprocess.Popen(
                        [
                            child_exec,
                            *child_args,
                            maa_bin,
                            socket_id,
                        ],
                    )

                except Exception as e:
                    logger.error(f"agent启动失败: {e}")
                    self._send_custom_info(self.tr("Agent start failed"))
                if not self.agent.connect():
                    logger.error(f"agent连接失败")
                    self._send_custom_info(self.tr("Agent connection failed"))
                print("cusotm加载完毕 ")
        if not self.tasker.inited:
            self._send_custom_info(self.tr("Tasker not initialized"))
            return False
        self.tasker.set_save_draw(save_draw)
        return self.tasker.post_task(entry, pipeline_override).wait().succeeded

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
            except Exception as e:
                logger.error(f"断开agent连接失败: {e}")
            finally:
                self.agent = None
            self.agent = None
        if self.agent_thread:
            try:
                self.agent_thread.terminate()
            except Exception as e:
                logger.error(f"终止agent线程失败: {e}")
            finally:
                self.agent_thread = None
            self.agent_thread = None

    def _send_custom_info(self, info: str):
        self.custom_info.emit(info)
