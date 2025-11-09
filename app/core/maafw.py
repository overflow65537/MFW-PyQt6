#   This file is part of MFW-ChainFlow Assistant.

#   MFW-ChainFlow Assistant is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published
#   by the Free Software Foundation, either version 3 of the License,
#   or (at your option) any later version.

#   MFW-ChainFlow Assistant is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty
#   of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See
#   the GNU General Public License for more details.

#   You should have received a copy of the GNU General Public License
#   along with MFW-ChainFlow Assistant. If not, see <https://www.gnu.org/licenses/>.

#   Contact: err.overflow@gmail.com
#   Copyright (C) 2024-2025  MFW-ChainFlow Assistant. All rights reserved.

# MIT License
#
# Copyright (c) 2024 MaaXYZ
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

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
from enum import Enum
from pathlib import Path

from asyncify import asyncify
from maa.controller import AdbController, Win32Controller
from maa.tasker import Tasker, NotificationHandler
from maa.agent_client import AgentClient
from maa.resource import Resource
from maa.toolkit import Toolkit, AdbDevice, DesktopWindow
from maa.define import MaaAdbScreencapMethodEnum, MaaAdbInputMethodEnum
from PySide6.QtCore import Signal, QObject

from ..utils.logger import logger
from ..common.config import cfg
from ..utils.tool import Read_Config, path_to_list
from ..utils.tool import ProcessThread
from .service import ConfigService, TaskService


class MaaFWMessageType(Enum):
    """MaaFW 消息类型枚举"""

    INFO = "info"
    SUCCESS = "success"
    FAIL = "fail"
    WARNING = "warning"


class MaaFWMessageCode(Enum):
    """MaaFW 消息代码枚举

    用于标识特定的消息类型，UI 层可以根据代码进行国际化翻译
    """

    # 自定义加载相关
    CUSTOM_ACTION_LOAD_FAILED = "custom_action_load_failed"
    CUSTOM_RECOGNIZER_LOAD_FAILED = "custom_recognizer_load_failed"
    CUSTOM_LOAD_ERROR = "custom_load_error"

    # 初始化相关
    RESOURCE_NOT_INITIALIZED = "resource_not_initialized"
    TASKER_NOT_INITIALIZED = "tasker_not_initialized"

    # Agent 相关
    AGENT_STARTING = "agent_starting"
    AGENT_START_FAILED = "agent_start_failed"
    AGENT_CONNECT_FAILED = "agent_connect_failed"
    AGENT_CONNECTED = "agent_connected"


# 以下代码引用自 MaaDebugger 项目的 ./src/MaaDebugger/maafw/__init__.py 文件，用于生成maafw实例
class MaaFWSignal(QObject):
    """MaaFW 信号发送辅助类

    内部定义信号，用于向 UI 层发送消息。
    使用枚举来标识消息类型和代码，UI 层可以根据枚举进行国际化处理。

    信号格式：
    {
        "type": MaaFWMessageType,  # 消息类型枚举
        "code": MaaFWMessageCode,  # 消息代码枚举
        "args": list               # 消息参数（用于格式化翻译文本）
    }
    """

    # 定义信号
    message = Signal(dict)

    def __init__(self):
        super().__init__()

    def emit_message(self, msg_type: MaaFWMessageType, code: MaaFWMessageCode, *args):
        """发送消息

        Args:
            msg_type: 消息类型
            code: 消息代码
            *args: 消息参数（用于格式化翻译文本）
        """
        self.message.emit({"type": msg_type, "code": code, "args": list(args)})

    def info(self, code: MaaFWMessageCode, *args):
        """发送信息消息"""
        self.emit_message(MaaFWMessageType.INFO, code, *args)

    def success(self, code: MaaFWMessageCode, *args):
        """发送成功消息"""
        self.emit_message(MaaFWMessageType.SUCCESS, code, *args)

    def fail(self, code: MaaFWMessageCode, *args):
        """发送失败消息"""
        self.emit_message(MaaFWMessageType.FAIL, code, *args)

    def warning(self, code: MaaFWMessageCode, *args):
        """发送警告消息"""
        self.emit_message(MaaFWMessageType.WARNING, code, *args)


class MaaFW:

    resource: Resource | None
    controller: AdbController | Win32Controller | None
    tasker: Tasker | None
    notification_handler: NotificationHandler | None
    agent: AgentClient | None

    def __init__(self, config: ConfigService, task: TaskService):
        Toolkit.init_option("./")
        self.resource = None
        self.controller = None
        self.tasker = None
        self.notification_handler = None
        self.agent = None
        self.agent_thread = None
        self.signal = MaaFWSignal()  # 信号发送器
        self.config = config
        self.task = task

    def _load_custom_module(self, custom_file_path: str, custom_class_name: str):
        """加载自定义模块并返回实例

        Args:
            custom_name: 自定义对象名称
            custom_file_path: 模块文件路径
            custom_class_name: 类名

        Returns:
            实例对象，加载失败返回 None
        """
        module_name = os.path.splitext(os.path.basename(custom_file_path))[0]

        # 动态导入模块
        spec = importlib.util.spec_from_file_location(module_name, custom_file_path)
        if spec is None or spec.loader is None:
            logger.error(f"无法加载模块 {module_name}")
            return None

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # 获取类对象并实例化
        class_obj = getattr(module, custom_class_name)
        return class_obj()

    def _register_custom_object(self, custom_type: str, custom_name: str, instance):
        """注册自定义对象

        Args:
            custom_type: 对象类型 ("action" 或 "recognition")
            custom_name: 对象名称
            instance: 对象实例
        """
        assert self.resource is not None, "self.resource 不应为 None"

        if custom_type == "action":
            success = self.resource.register_custom_action(custom_name, instance)
            type_name = "动作"
            code = MaaFWMessageCode.CUSTOM_ACTION_LOAD_FAILED
        else:  # recognition
            success = self.resource.register_custom_recognition(custom_name, instance)
            type_name = "识别器"
            code = MaaFWMessageCode.CUSTOM_RECOGNIZER_LOAD_FAILED

        if success:
            logger.info(f"加载自定义{type_name}: {custom_name}")
        else:
            logger.error(f"注册自定义{type_name}失败: {custom_name}")
            self.signal.fail(code, custom_name)

    def load_custom_objects(self, custom_dir: str):
        """加载自定义对象

        Args:
            custom_dir: 自定义对象目录路径
        """
        # 检查目录
        if not os.path.exists(custom_dir):
            logger.warning(f"自定义文件夹 {custom_dir} 不存在")
            return
        if not os.listdir(custom_dir):
            logger.warning(f"自定义文件夹 {custom_dir} 为空")
            return

        # 检查配置文件
        config_path = os.path.join(custom_dir, "custom.json")
        if not os.path.exists(config_path):
            return

        logger.info("加载自定义配置文件")
        custom_config: Dict[str, Dict] = Read_Config(config_path)

        for custom_name, custom in custom_config.items():
            # 获取配置项
            custom_type = custom.get("type", "")
            custom_class_name = custom.get("class", "")
            custom_file_path = custom.get("file_path", "")

            # 处理路径占位符
            if "{custom_path}" in custom_file_path:
                custom_file_path = custom_file_path.replace("{custom_path}", custom_dir)
                custom_file_path = os.path.join(*path_to_list(custom_file_path))

            # 验证必要信息
            if not all([custom_type, custom_name, custom_class_name, custom_file_path]):
                logger.warning(f"配置项 {custom_name} 缺少必要信息，跳过")
                continue

            # 加载模块
            instance = self._load_custom_module(custom_file_path, custom_class_name)
            if instance is None:
                continue

            # 注册对象
            if custom_type in ("action", "recognition"):
                self._register_custom_object(custom_type, custom_name, instance)
            else:
                logger.warning(f"未知的自定义类型: {custom_type}")

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
        self
    ) -> bool:
        adb_data = self.task.get_task("r_resource_base_task")

        if screencap_method == 0:
            screencap_method = MaaAdbScreencapMethodEnum.Default
        if input_method == 0:
            input_method = MaaAdbInputMethodEnum.Default
        self.controller = AdbController(
            adb_path, address, screencap_method, input_method, config
        )
        connected = self.controller.post_connection().wait().succeeded
        if not connected:
            print(f"Failed to connect {adb_path} {address}")
            return False

        return True

    @asyncify
    def connect_win32hwnd(
        self, hwnd: int | str, screencap_method: int, input_method: int
    ) -> bool:
        if isinstance(hwnd, str):
            hwnd = int(hwnd, 16)
        if screencap_method == 0:
            screencap_method = 4  # DXGI_DesktopDup
        if input_method == 0:
            input_method = 1  # Seize

        self.controller = Win32Controller(
            hwnd, screencap_method=screencap_method, input_method=input_method  # type: ignore
        )
        connected = self.controller.post_connection().wait().succeeded
        if not connected:
            print(f"Failed to connect {hwnd}")
            return False

        return True

    @asyncify
    def load_resource(self, dir: str | Path, gpu_index: int = -1) -> bool:
        if not self.resource:
            self.resource = Resource()
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

    def start_agent(
        self, child_exec: str, child_args: list[str], resource_path
    ) -> bool:
        """启动 Agent

        Args:
            child_exec: Agent 可执行文件路径
            child_args: Agent 启动参数列表

        Returns:
            bool: 启动并连接成功返回 True，否则返回 False
        """
        if self.agent:
            logger.warning("Agent 已经启动")
            return True

        assert self.resource is not None, "Resource 未初始化"

        # 创建并绑定 Agent
        self.agent = AgentClient()
        self.agent.bind(self.resource)

        # 获取 socket ID
        socket_id = self.agent.identifier
        if callable(socket_id):
            socket_id = socket_id() or "maafw_socket_id"
        elif socket_id is None:
            socket_id = "maafw_socket_id"
        socket_id = str(socket_id)

        self.signal.info(MaaFWMessageCode.AGENT_STARTING)
        logger.info(f"Agent 启动中: {child_exec}")

        try:
            # 获取 MAA 库路径
            maa_bin = os.getenv("MAAFW_BINARY_PATH") or os.getcwd()

            # 替换路径占位符
            child_exec = child_exec.replace("{PROJECT_DIR}", resource_path)
            child_args = [
                arg.replace("{PROJECT_DIR}", resource_path) for arg in child_args
            ]

            logger.debug(
                f"Agent 启动参数: {child_exec} {child_args} {maa_bin} {socket_id}"
            )

            # 启动 Agent 进程
            if cfg.get(cfg.show_agent_cmd):
                subprocess.Popen([child_exec, *child_args, maa_bin, socket_id])
            else:
                self.agent_thread = ProcessThread(
                    child_exec, [*child_args, maa_bin, socket_id]
                )
                self.agent_thread.setObjectName("AgentThread")
                self.agent_thread.start()

            cfg.set(cfg.agent_path, child_exec)

        except Exception as e:
            logger.error(f"Agent 启动失败: {e}")
            self.signal.fail(MaaFWMessageCode.AGENT_START_FAILED, str(e))
            self.agent = None
            return False

        # 连接 Agent
        if not self.agent.connect():
            logger.error("Agent 连接失败")
            self.signal.fail(MaaFWMessageCode.AGENT_CONNECT_FAILED)
            self.agent = None
            return False

        logger.info("Agent 连接成功")
        self.signal.success(MaaFWMessageCode.AGENT_CONNECTED)
        return True

    @asyncify
    def run_task(self, entry: str, pipeline_override: dict = {}) -> bool:
        if not self.tasker:
            self.tasker = Tasker(notification_handler=self.notification_handler)

        if not self.resource or not self.controller:
            self.signal.fail(MaaFWMessageCode.RESOURCE_NOT_INITIALIZED)
            return False

        self.tasker.bind(self.resource, self.controller)

        if not self.tasker.inited:
            self.signal.fail(MaaFWMessageCode.TASKER_NOT_INITIALIZED)
            return False
        return self.tasker.post_task(entry, pipeline_override).wait().succeeded

    def set_save_draw(self, save_draw: bool):
        if self.tasker:
            self.tasker.set_save_draw(save_draw)

    def set_recording(self, recording: bool):
        if self.tasker:
            self.tasker.set_recording(recording)

    @asyncify
    def stop_task(self):
        if self.tasker:
            self.tasker.post_stop().wait()
            self.tasker = None
        if self.agent:
            self.agent.disconnect()
            self.agent = None
        if self.agent_thread:
            self.agent_thread.stop()
            self.agent_thread = None

