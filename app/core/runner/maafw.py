"""
MFW-ChainFlow Assistant
MFW-ChainFlow Assistant MaaFW核心
原作者: MaaXYZ
地址: https://github.com/MaaXYZ/MaaDebugger
修改:overflow65537
"""

import os
import re
import sys
import importlib.util
import types
from enum import Enum, IntEnum
from typing import Any, Dict, List
import subprocess
import threading
from pathlib import Path
import numpy
from asyncify import asyncify

import maa
from maa.context import Context, ContextEventSink
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

# 不同 maa 版本对 GamepadType 的导出名字不一致：
# - 新版本: MaaGamepadTypeEnum
# - 部分版本: MaaGamepadType（可能是 enum 或常量容器）
try:
    from maa.define import MaaGamepadTypeEnum  # type: ignore
except ImportError:  # pragma: no cover
    try:
        from maa.define import MaaGamepadType as MaaGamepadTypeEnum  # type: ignore
    except ImportError:  # pragma: no cover
        class MaaGamepadTypeEnum(IntEnum):
            Xbox360 = 0

from PySide6.QtCore import QObject, Signal

from app.utils.logger import logger


def iter_agent_entries(agent_config: Any):
    """遍历 interface.agent 中的全部启动项（dict 为单项，list 为多项）。"""
    if isinstance(agent_config, dict):
        if agent_config:
            yield agent_config
    elif isinstance(agent_config, list):
        for item in agent_config:
            if isinstance(item, dict) and item:
                yield item


def normalize_agent_entry(agent_config: Any) -> dict | None:
    """将 interface.agent 规范为第一个启动项 dict（兼容旧逻辑）。"""
    return next(iter_agent_entries(agent_config), None)


def should_start_external_agent(agent_config: Any) -> bool:
    """是否应以外部子进程方式启动 agent（非 embedded）。"""
    return any(not entry.get("embedded") for entry in iter_agent_entries(agent_config))


def _child_exec_looks_like_path(child_exec: str) -> bool:
    return (
        "/" in child_exec
        or "\\" in child_exec
        or child_exec.startswith(".")
        or child_exec.startswith("{PROJECT_DIR}")
    )


def resolve_agent_executable(child_exec: str, project_dir: Path) -> str:
    """
    将 interface.agent.child_exec 解析为可执行路径。

    相对路径（如 agent/go-service）相对于 PI 项目目录（interface 所在目录），
    而非 Client 进程 cwd。纯命令名（如 python）保持原样以便从 PATH 查找。
    """
    raw = child_exec.strip()
    if not raw or not _child_exec_looks_like_path(raw):
        return raw

    expanded = raw.replace("{PROJECT_DIR}", str(project_dir))
    path = Path(expanded)
    if not path.is_absolute():
        path = (project_dir / path).resolve()
    else:
        path = path.resolve()

    if path.is_file():
        return str(path)

    if sys.platform == "win32" and path.suffix == "":
        with_exe = path.with_suffix(".exe")
        if with_exe.is_file():
            return str(with_exe)

    return str(path)


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

try:
    from maa.controller import PlayCoverController
except ImportError:
    PlayCoverController = None

try:
    from maa.controller import GamepadController
except ImportError:
    GamepadController = None

class MaaContextSink(ContextEventSink):
    def __init__(self, emit_callback=None):
        self._emit_callback = emit_callback

    def _emit(self, payload: dict) -> None:
        if self._emit_callback is not None:
            self._emit_callback(payload)

    def on_raw_notification(self, context: Context, msg: str, details: dict):
        focus_entry = (details.get("focus") or {}).get(msg)
        if not focus_entry:
            return

        # 兼容两种格式：
        # 旧格式 (str): "focus": { "Node.Action.Starting": "{name} 开始执行" }
        # 新格式 (dict): "focus": { "Node.Action.Starting": { "content": "{name} 开始执行", "display": "toast" } }
        if isinstance(focus_entry, str):
            content = focus_entry
            display = ["log"]
        elif isinstance(focus_entry, dict):
            content = focus_entry.get("content", "")
            raw_display = focus_entry.get("display", "log")
            if isinstance(raw_display, list):
                display = raw_display
            else:
                display = [raw_display]
        else:
            return

        if not content:
            return

        # 替换占位符
        content = content.replace("{name}", details.get("name", ""))
        content = content.replace("{task_id}", str(details.get("task_id", "")))
        content = content.replace("{list}", details.get("list", ""))

        self._emit({"name": "context", "details": content, "display": display})

        if msg == "Node.Recognition.Succeeded":
            if details.get("Abort", False):
                self._emit({"name": "abort"})
            if details.get("Notice", False):
                pass

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
    def __init__(self, emit_callback=None):
        self._emit_callback = emit_callback

    def on_raw_notification(self, controller: Controller, msg: str, details: dict):
        pass

    def on_controller_action(
        self,
        controller: Controller,
        noti_type: NotificationType,
        detail: ControllerEventSink.ControllerActionDetail,
    ):
        # signalBus.callback.emit({"name": "controller", "status": noti_type.value})
        pass


class MaaResourceEventSink(ResourceEventSink):
    def __init__(self, emit_callback=None):
        self._emit_callback = emit_callback

    def on_raw_notification(self, resource: Resource, msg: str, details: dict):
        pass

    def on_resource_loading(
        self,
        resource: Resource,
        noti_type: NotificationType,
        detail: ResourceEventSink.ResourceLoadingDetail,
    ):
        if self._emit_callback is not None:
            self._emit_callback({"name": "resource", "status": noti_type.value})


class MaaTaskerEventSink(TaskerEventSink):
    def __init__(self, emit_callback=None):
        self._emit_callback = emit_callback

    def on_raw_notification(self, tasker: Tasker, msg: str, details: dict):
        pass

    def on_tasker_task(
        self,
        tasker: Tasker,
        noti_type: NotificationType,
        detail: TaskerEventSink.TaskerTaskDetail,
    ):
        if self._emit_callback is not None:
            self._emit_callback(
                {"name": "task", "task": detail.entry, "status": noti_type.value}
            )


class MaaFW(QObject):
    callback = Signal(dict)

    resource: Resource | None
    controller: Controller | None
    tasker: Tasker | None
    agent: AgentClient | None

    agent_thread: subprocess.Popen | None
    agent_output_thread: threading.Thread | None
    agents: list[AgentClient]
    agent_threads: list[subprocess.Popen]
    agent_output_threads: list[threading.Thread]

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

        # sink 默认绑定到 MaaFW 自身回调信号，供上层按需转发到 UI。
        self.maa_controller_sink = maa_controller_sink or MaaControllerEventSink(
            self.callback.emit
        )
        self.maa_context_sink = maa_context_sink or MaaContextSink(self.callback.emit)
        self.maa_resource_sink = maa_resource_sink or MaaResourceEventSink(
            self.callback.emit
        )
        self.maa_tasker_sink = maa_tasker_sink or MaaTaskerEventSink(
            self.callback.emit
        )

        self.agents = []
        self.agent_threads = []
        self.agent_output_threads = []
        self.agent = None
        self.agent_thread = None
        self.agent_output_thread = None

        self.agent_data_raw = None
        # PI 项目目录（interface.json 所在目录），用于解析 agent 相对路径
        self.agent_project_dir: Path | None = None
        # v2.5.0: 启动 agent 子进程时注入的 PI_* 环境变量
        self.agent_env_vars: Dict[str, str] = {}
        # 控制是否需要向 UI 报告自定义对象注册情况
        self.need_register_report: bool = False
        # 记录最近一次自定义对象加载的成功/失败情况
        self.custom_load_report: Dict[str, Dict[str, List]] = {
            "actions": {"success": [], "failed": []},
            "recognitions": {"success": [], "failed": []},
        }
        # 记录添加到 sys.path 的路径，用于后续清理
        self._custom_sys_paths: List[str] = []
        # 记录上次加载的 custom_root，用于清理模块缓存
        self._last_custom_root: Path | None = None
        # 内置模式下的额外 Tasker sink（如分辨率检查）
        self._embedded_tasker_sinks: List[TaskerEventSink] = []
        # 底层 maa 对象清理不是线程安全的，必须串行执行。
        self._cleanup_lock = threading.Lock()

    def load_embedded_agent_custom(
        self, agent_root: str | Path, agent_entry: str | Path | None = None
    ) -> bool:
        """
        内置模式：直接 import agent 源入口，经 Resource 装饰器注册动作/识别器。

        :param agent_root: agent 源目录
        :param agent_entry: agent 入口脚本；为空时默认使用 agent_root/main.py
        """
        agent_path = Path(str(agent_root).replace("{PROJECT_DIR}", str(Path.cwd()))).resolve()
        if not agent_path.is_dir():
            logger.warning("agent 目录 %s 不存在", agent_path)
            return False

        if agent_entry is None:
            entry_path = agent_path / "main.py"
        else:
            entry_path = Path(
                str(agent_entry).replace("{PROJECT_DIR}", str(Path.cwd()))
            )
            if not entry_path.is_absolute():
                entry_path = (agent_path / entry_path).resolve()
            else:
                entry_path = entry_path.resolve()
        if not entry_path.is_file():
            logger.error("内置 agent 入口脚本不存在: %s", entry_path)
            return False

        self._embedded_tasker_sinks.clear()
        self._purge_modules_under_root(self._last_custom_root)
        self._remove_custom_sys_paths()
        self._last_custom_root = agent_path

        # 源入口作为脚本运行时通常可同时 import 同目录模块与项目根包。
        for sys_path in (str(agent_path), str(agent_path.parent)):
            if sys_path not in sys.path:
                sys.path.insert(0, sys_path)
                self._custom_sys_paths.append(sys_path)

        resource = self._init_resource()
        self.custom_load_report = {
            "actions": {"success": [], "failed": []},
            "recognitions": {"success": [], "failed": []},
        }

        try:
            self._bind_embedded_registries(resource)
            self._load_embedded_agent_entry(entry_path)
        except Exception:
            logger.exception("加载内置 agent custom 失败")
            return False

        actions = list(resource.custom_action_list or [])
        recognitions = list(resource.custom_recognition_list or [])
        self.custom_load_report["actions"]["success"] = actions
        self.custom_load_report["recognitions"]["success"] = recognitions

        if actions:
            logger.info("成功加载内置自定义动作: %s", ", ".join(actions))
        if recognitions:
            logger.info("成功加载内置自定义识别器: %s", ", ".join(recognitions))

        if not actions and not recognitions:
            logger.warning("内置 agent 未注册任何自定义动作或识别器")
            return False
        return True

    def _bind_embedded_registries(self, resource: Resource) -> None:
        """向源 agent 暴露当前 MaaFW 正在使用的注册入口。"""
        resource_module = types.ModuleType("maa_resource_registry")
        resource_module.MaaResource = resource
        sys.modules["maa_resource_registry"] = resource_module

        class EmbeddedTaskerRegistry:
            def tasker_sink(registry_self):
                def wrapper_sink(sink):
                    instance = sink()
                    if not isinstance(instance, TaskerEventSink):
                        raise TypeError(f"{sink.__name__} 不是 TaskerEventSink 子类")
                    self._embedded_tasker_sinks.append(instance)
                    if self.tasker is not None:
                        self.tasker.add_sink(instance)
                    return sink

                return wrapper_sink

        tasker_module = types.ModuleType("maa_tasker_registry")
        tasker_module.MaaTasker = EmbeddedTaskerRegistry()
        sys.modules["maa_tasker_registry"] = tasker_module

    @staticmethod
    def _load_embedded_agent_entry(entry_path: Path) -> None:
        """导入内置 agent 的源入口脚本，触发 MaaResource 装饰器注册。"""
        module_key = f"embedded_agent_entry:{entry_path}"
        if module_key in sys.modules:
            del sys.modules[module_key]

        spec = importlib.util.spec_from_file_location(module_key, entry_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"无法加载 {entry_path}")

        module = importlib.util.module_from_spec(spec)
        sys.modules[module_key] = module
        cwd = Path.cwd()
        try:
            spec.loader.exec_module(module)  # type: ignore[arg-type]
        finally:
            os.chdir(cwd)

    def _purge_modules_under_root(self, root: Path | None) -> None:
        if not root:
            return
        modules_to_remove: list[str] = []
        for module_key in list(sys.modules.keys()):
            if isinstance(module_key, str) and (
                module_key.startswith(str(root))
                or (
                    os.path.isabs(module_key)
                    and Path(module_key).is_relative_to(root)
                )
            ):
                modules_to_remove.append(module_key)
                continue
            if not isinstance(module_key, str):
                continue
            try:
                module = sys.modules.get(module_key)
                if not module:
                    continue
                if getattr(module, "__file__", None):
                    try:
                        if Path(module.__file__).resolve().is_relative_to(root):
                            modules_to_remove.append(module_key)
                            continue
                    except (ValueError, OSError):
                        pass
                if hasattr(module, "__path__"):
                    for path_entry in module.__path__:
                        try:
                            if Path(path_entry).resolve().is_relative_to(root):
                                modules_to_remove.append(module_key)
                                break
                        except (ValueError, OSError):
                            pass
            except Exception:
                pass
        for module_key in set(modules_to_remove):
            try:
                del sys.modules[module_key]
            except KeyError:
                pass

    def _remove_custom_sys_paths(self) -> None:
        for path in self._custom_sys_paths:
            if path in sys.path:
                sys.path.remove(path)
        self._custom_sys_paths.clear()
        sys.modules.pop("maa_resource_registry", None)
        sys.modules.pop("maa_tasker_registry", None)

    _EMBEDDED_ASPECT_RATIO_SINK = (
        "custom",
        "sink",
        "aspect_ratio.py",
    )

    def load_embedded_aspect_ratio_sink(self) -> bool:
        """
        内置模式下从 agent 源目录加载分辨率检查 Tasker sink。

        须在 load_embedded_agent_custom 之后调用（依赖其设置的 agent 根目录与 sys.path）。
        """
        custom_root = self._last_custom_root
        if custom_root is None:
            logger.warning("未设置 custom_root，跳过分辨率检查 sink 加载")
            return False

        sink_file = custom_root.joinpath(*self._EMBEDDED_ASPECT_RATIO_SINK)
        if not sink_file.is_file():
            logger.debug("未找到内置分辨率检查模块 %s，跳过", sink_file)
            return True

        module_name = sink_file.stem
        module_key = f"embedded_sink:{sink_file}"

        if module_key in sys.modules:
            del sys.modules[module_key]

        spec = importlib.util.spec_from_file_location(module_name, sink_file)
        if spec is None or spec.loader is None:
            logger.error("无法加载内置分辨率检查模块 %s", sink_file)
            return False

        try:
            sink_count = len(self._embedded_tasker_sinks)
            self._bind_embedded_registries(self._init_resource())
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_key] = module
            spec.loader.exec_module(module)  # type: ignore[arg-type]
            if len(self._embedded_tasker_sinks) <= sink_count:
                logger.error("模块 %s 未通过 MaaTasker 注册任何 Tasker sink", sink_file)
                return False
        except Exception:
            logger.exception("加载内置分辨率检查 sink 失败")
            return False

        logger.info("已加载内置分辨率检查 sink")
        return True

    @staticmethod
    @asyncify
    def detect_adb() -> List[AdbDevice]:
        return Toolkit.find_adb_devices()

    @staticmethod
    @asyncify
    def detect_win32hwnd(window_regex: str) -> List[DesktopWindow]:
        windows = Toolkit.find_desktop_windows()
        return [win for win in windows if re.search(window_regex, win.window_name)]

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
        hwnd: int,
        screencap_method: int = MaaWin32ScreencapMethodEnum.DXGI_DesktopDup,
        mouse_method: int = MaaWin32InputMethodEnum.Seize,
        keyboard_method: int = MaaWin32InputMethodEnum.Seize,
    ) -> bool:
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

    @asyncify
    def connect_playcover(self, address: str, uuid: str) -> bool:
        if PlayCoverController is None:
            raise RuntimeError("当前安装的 maa 版本不支持 PlayCoverController")
        controller = PlayCoverController(address, uuid)
        controller = self._init_controller(controller)
        connected = controller.post_connection().wait().succeeded
        if not connected:
            print(f"Failed to connect {address} {uuid}")
            return False
        return True

    @asyncify
    def connect_gamepad(
        self,
        hwnd: int,
        gamepad_type: int = MaaGamepadTypeEnum.Xbox360,
        screencap_method: int = MaaWin32ScreencapMethodEnum.DXGI_DesktopDup,
    ) -> bool:
        if GamepadController is None:
            raise RuntimeError("当前安装的 maa 版本不支持 GamepadController")
        controller = GamepadController(hwnd, gamepad_type, screencap_method)
        controller = self._init_controller(controller)
        connected = controller.post_connection().wait().succeeded
        if not connected:
            print(f"Failed to connect {hwnd} {gamepad_type}")
            return False
        return True

    def _init_controller(self, controller: Controller) -> Controller:
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

            for sink in self._embedded_tasker_sinks:
                self.tasker.add_sink(sink)
            if self.maa_tasker_sink:
                self.tasker.add_sink(self.maa_tasker_sink)
        if not self.resource or not self.controller:
            raise RuntimeError("Resource 与 Controller 必须先初始化再初始化 Tasker")
        self.tasker.bind(self.resource, self.controller)
        return self.tasker

    def _init_agent(self, agent_data_raw: Any) -> bool:
        if not (self.resource and self.controller):
            raise RuntimeError("agent 初始化前必须存在 resource/controller")
        if not self.tasker:
            self.tasker = self._init_tasker()
        if self.agents:
            return True

        if not agent_data_raw:
            logger.warning("未找到agent配置")
            self._send_custom_info(MaaFWError.AGENT_CONFIG_MISSING)
            return False

        if isinstance(agent_data_raw, list) and not agent_data_raw:
            logger.warning("agent 配置为一个空列表")
            self._send_custom_info(MaaFWError.AGENT_CONFIG_EMPTY_LIST)
            return False

        entries = [
            entry
            for entry in iter_agent_entries(agent_data_raw)
            if not entry.get("embedded")
        ]
        if not entries:
            logger.warning("agent 配置既不是字典也不是列表，或全部为 embedded")
            self._send_custom_info(MaaFWError.AGENT_CONFIG_INVALID)
            return False

        for agent_data in entries:
            if not self._start_one_agent(agent_data):
                self._teardown_agents()
                return False

        self._sync_agent_legacy_fields()
        return True

    def _agent_socket_id(self, client: AgentClient, agent_data: dict) -> str:
        configured = agent_data.get("identifier")
        if configured is not None and str(configured).strip():
            return str(configured).strip()
        socket_id = client.identifier
        if callable(socket_id):
            socket_id = socket_id() or "maafw_socket_id"
        elif socket_id is None:
            socket_id = "maafw_socket_id"
        return str(socket_id)

    def _start_one_agent(self, agent_data: dict) -> bool:
        child_exec = agent_data.get("child_exec", "")
        if not child_exec:
            logger.warning("agent 配置缺少 child_exec，无法启动")
            self._send_custom_info(MaaFWError.AGENT_CHILD_EXEC_MISSING)
            return False

        configured_id = agent_data.get("identifier")
        if configured_id is not None and str(configured_id).strip():
            client = AgentClient(str(configured_id).strip())
        else:
            client = AgentClient()

        if not client.register_sink(self.resource, self.controller, self.tasker):
            logger.error("agent register_sink 失败")
            return False
        if not client.bind(self.resource):
            logger.error("agent bind resource 失败")
            return False

        socket_id = self._agent_socket_id(client, agent_data)
        child_args = agent_data.get("child_args", [])
        project_dir = (self.agent_project_dir or Path.cwd()).resolve()
        child_exec = resolve_agent_executable(child_exec, project_dir)
        child_args = [
            arg.replace("{PROJECT_DIR}", str(project_dir)) for arg in child_args
        ]
        start_cmd = [child_exec, *child_args, socket_id]
        logger.debug(f"启动agent命令: {start_cmd}")

        is_packed = getattr(sys, "frozen", False)
        encoding = "utf-8" if is_packed else "gbk"
        env = os.environ.copy()
        if self.agent_env_vars:
            env.update(self.agent_env_vars)
            logger.debug(
                f"注入 PI_* 环境变量: {list(self.agent_env_vars.keys())}"
            )

        try:
            agent_process = subprocess.Popen(
                start_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding=encoding,
                errors="replace",
                bufsize=1,
                env=env,
            )
        except Exception as e:
            logger.error(f"启动agent失败: {e}")
            self._send_custom_info(MaaFWError.AGENT_START_FAILED)
            return False

        self.agents.append(client)
        self.agent_threads.append(agent_process)
        self._watch_agent_output(agent_process)

        if agent_data.get("timeout"):
            client.set_timeout(agent_data.get("timeout"))
        if not client.connect():
            self._send_custom_info(MaaFWError.AGENT_CONNECTION_FAILED)
            return False
        return True

    def _sync_agent_legacy_fields(self) -> None:
        self.agent = self.agents[0] if self.agents else None
        self.agent_thread = self.agent_threads[0] if self.agent_threads else None
        self.agent_output_thread = (
            self.agent_output_threads[0] if self.agent_output_threads else None
        )

    def _teardown_agents(self) -> None:
        for client in self.agents:
            try:
                client.disconnect()
            except Exception as e:
                logger.error(f"断开agent连接失败: {e}")
        self.agents.clear()

        for process in self.agent_threads:
            try:
                process.terminate()
                try:
                    process.wait(timeout=self.AGENT_TERMINATE_TIMEOUT_SECONDS)
                except subprocess.TimeoutExpired:
                    logger.warning("等待 agent 终止超时，执行 kill 操作")
                    process.kill()
                    try:
                        process.wait(timeout=1)
                    except Exception:
                        pass
            except Exception as e:
                logger.error(f"终止agent进程失败: {e}")
        self.agent_threads.clear()

        for watcher in self.agent_output_threads:
            watcher.join(timeout=0.1)
        self.agent_output_threads.clear()
        self.agent = None
        self.agent_thread = None
        self.agent_output_thread = None

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
        self._cleanup_runtime()

    def has_active_runtime(self) -> bool:
        return any(
            (
                self.tasker is not None,
                self.resource is not None,
                self.controller is not None,
                bool(self.agents),
                bool(self.agent_threads),
                bool(self.agent_output_threads),
            )
        )

    def force_shutdown(self) -> None:
        """同步强制清理 MaaFW 运行态，供应用退出阶段调用。"""
        self._cleanup_runtime()

    def _cleanup_runtime(self) -> None:
        if not self._cleanup_lock.acquire(blocking=False):
            logger.debug("MaaFW 清理已在进行中，忽略重复请求")
            return

        try:
            if self.tasker:
                try:
                    self.tasker.post_stop().wait()
                except Exception as e:
                    logger.error(f"停止任务失败: {e}")
                finally:
                    self.tasker = None
            if self.resource:
                try:
                    self.resource.clear()
                except Exception as e:
                    logger.error(f"清除资源失败: {e}")
                finally:
                    self.resource = None
            if self.controller:
                self.controller = None
            self._teardown_agents()
            self.agent_data_raw = None
            self.agent_project_dir = None
            self.agent_env_vars = {}
            self._purge_modules_under_root(self._last_custom_root)
            self._last_custom_root = None
            self._embedded_tasker_sinks.clear()
            self._remove_custom_sys_paths()
        finally:
            self._cleanup_lock.release()

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
        self.agent_output_threads.append(watcher)
        self.agent_output_thread = watcher

    async def screencap_test(self) -> numpy.ndarray:
        if not self.controller:
            raise RuntimeError("Controller not initialized")
        return self.controller.post_screencap().wait().get()
