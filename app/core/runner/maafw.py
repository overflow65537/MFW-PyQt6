"""
MFW-ChainFlow Assistant
MFW-ChainFlow Assistant MaaFW核心
原作者: MaaXYZ
地址: https://github.com/MaaXYZ/MaaDebugger
修改:overflow65537
"""

import ast
import importlib
import os
import re
import sys
from dataclasses import dataclass
from enum import Enum, IntEnum
from typing import Any, Dict, List
import subprocess
import threading
import time
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
    MaaMacOSInputMethodEnum,
    MaaMacOSScreencapMethodEnum,
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
from app.core.runner.recognition_roi import (
    extract_node_recognition_roi,
    extract_recognition_box,
)
from app.common.config import cfg


@dataclass(frozen=True)
class EmbeddedDecoratorInfo:
    file_path: Path
    module_name: str
    class_name: str
    kind: str
    register_name: str | None = None


_EMBEDDED_AGENT_SERVER_SINK_DECORATORS = {
    "resource_sink",
    "controller_sink",
    "tasker_sink",
    "context_sink",
}


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
    AGENT_CONNECTION_TIMEOUT = 9


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

try:
    from maa.controller import WlRootsController
except ImportError:
    WlRootsController = None

try:
    from maa.controller import MacOSController
except ImportError:
    MacOSController = None

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

        self._emit(
            {
                "name": "context",
                "details": content,
                "display": display,
                "context_meta": {
                    "name": details.get("name", ""),
                    "task_id": str(details.get("task_id", "")),
                    "list": details.get("list", ""),
                },
            }
        )

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
        if not cfg.get(cfg.monitor_recognition_roi_enabled):
            return

        if noti_type == NotificationType.Starting:
            box = extract_node_recognition_roi(context, detail.name)
            if not box:
                return
            self._emit(
                {
                    "name": "recognition_roi",
                    "phase": "recognizing",
                    "node": detail.name,
                    "box": list(box),
                }
            )
            return

        if noti_type == NotificationType.Failed:
            self._emit(
                {
                    "name": "recognition_roi",
                    "clear": True,
                    "node": detail.name,
                }
            )
            return

        if noti_type != NotificationType.Succeeded:
            return

        reco_detail = None
        try:
            reco_detail = context.tasker.get_recognition_detail(detail.reco_id)
        except Exception as exc:
            logger.debug("获取识别详情失败 reco_id=%s: %s", detail.reco_id, exc)

        box = extract_recognition_box(reco_detail)
        if not box:
            return

        algorithm = getattr(reco_detail, "algorithm", "") if reco_detail else ""
        self._emit(
            {
                "name": "recognition_roi",
                "phase": "hit",
                "node": detail.name,
                "reco_id": detail.reco_id,
                "box": list(box),
                "algorithm": algorithm,
            }
        )


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
    # agent 连接默认超时（秒）；interface / 控制器配置可覆盖
    DEFAULT_AGENT_CONNECT_TIMEOUT_SECONDS: int = 30
    # post_stop 后等待 Tasker 完全空闲的最长时长（避免 CustomAction 仍在执行时销毁原生对象）
    TASKER_IDLE_TIMEOUT_SECONDS: float = 30.0
    TASKER_IDLE_POLL_INTERVAL_SECONDS: float = 0.05

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
        # 控制器配置中的 agent 连接超时（秒）；None 表示使用 interface 或默认值
        self.agent_connection_timeout_seconds: int | None = None
        self._last_agent_connect_timeout_seconds: int | None = None
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
        self._last_embedded_module_keys: list[str] = []
        # 内置模式下的额外 Maa event sink。
        self._embedded_resource_sinks: List[ResourceEventSink] = []
        self._embedded_controller_sinks: List[ControllerEventSink] = []
        self._embedded_tasker_sinks: List[TaskerEventSink] = []
        self._embedded_context_sinks: List[ContextEventSink] = []
        # 底层 maa 对象清理不是线程安全的，必须串行执行。
        self._cleanup_lock = threading.Lock()

    def load_embedded_agent_custom(
        self, agent_root: str | Path, agent_entry: str | Path | None = None
    ) -> bool:
        """
        内置模式：扫描 agent 源码中的装饰器并导入相关模块完成注册。

        :param agent_root: agent 源目录
        :param agent_entry: interface.agent 解析出的入口脚本
        """
        agent_path = Path(str(agent_root).replace("{PROJECT_DIR}", str(Path.cwd()))).resolve()
        if not agent_path.is_dir():
            logger.warning("agent 目录 %s 不存在", agent_path)
            return False

        entry_path: Path | None = None
        if agent_entry is not None:
            entry_path = Path(
                str(agent_entry).replace("{PROJECT_DIR}", str(Path.cwd()))
            )
            if not entry_path.is_absolute():
                entry_path = (agent_path / entry_path).resolve()
            else:
                entry_path = entry_path.resolve()
        if entry_path is not None and not entry_path.is_file():
            logger.error("内置 agent 入口脚本不存在: %s", entry_path)
            return False

        logger.info("准备加载内置 agent 源目录: %s，入口脚本: %s", agent_path, entry_path)
        self._embedded_resource_sinks.clear()
        self._embedded_controller_sinks.clear()
        self._embedded_tasker_sinks.clear()
        self._embedded_context_sinks.clear()
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
        decorators = self._scan_embedded_decorators(agent_path)
        rewritten_files = self._rewrite_embedded_agent_sources(decorators)
        if rewritten_files:
            logger.info(
                "已将内置 agent 装饰器写回为 resource/add_sink 模式: %s",
                ", ".join(str(path) for path in rewritten_files),
            )
            decorators = self._scan_embedded_decorators(agent_path)
        for item in decorators:
            logger.info(
                "扫描到内置 agent 装饰器: type=%s, name=%s, class=%s.%s, file=%s",
                item.kind,
                item.register_name or "",
                item.module_name,
                item.class_name,
                item.file_path,
            )

        actions_before = set(resource.custom_action_list or [])
        recognitions_before = set(resource.custom_recognition_list or [])
        sink_count_before = self._embedded_sink_counts()
        modules_before = set(sys.modules.keys())

        resource_patch = self._patch_maa_resource_instance(resource)
        cwd = Path.cwd()
        try:
            self._load_embedded_decorator_modules(agent_path, decorators)
        except Exception:
            logger.exception("加载内置 agent custom 失败")
            return False
        finally:
            os.chdir(cwd)
            resource_patch()

        actions = list(resource.custom_action_list or [])
        recognitions = list(resource.custom_recognition_list or [])
        converted_actions = sorted(set(actions) - actions_before)
        converted_recognitions = sorted(set(recognitions) - recognitions_before)
        converted_sinks = self._embedded_sinks_after(sink_count_before)
        self.custom_load_report["actions"]["success"] = actions
        self.custom_load_report["recognitions"]["success"] = recognitions

        logger.info(
            "内置 agent 转换结果: actions=%s, recognitions=%s, sinks=%s",
            converted_actions or [],
            converted_recognitions or [],
            [
                f"{kind}:{sink.__class__.__module__}.{sink.__class__.__name__}"
                for kind, sink in converted_sinks
            ],
        )

        if actions:
            logger.info("成功加载内置自定义动作: %s", ", ".join(actions))
        if recognitions:
            logger.info("成功加载内置自定义识别器: %s", ", ".join(recognitions))

        self._last_embedded_module_keys = self._collect_embedded_module_keys(
            agent_path, modules_before
        )

        if not actions and not recognitions and not self._has_embedded_sinks():
            imported_modules = self._collect_imported_modules_under_root(
                agent_path, modules_before
            )
            logger.warning(
                "内置 agent 未注册任何自定义动作、识别器或事件 sink，源目录: %s，入口脚本: %s，"
                "本次导入模块: %s",
                agent_path,
                entry_path,
                imported_modules or [],
            )
            return False
        return True

    def _has_embedded_sinks(self) -> bool:
        return any(self._embedded_sink_counts().values())

    def _embedded_sink_counts(self) -> dict[str, int]:
        return {
            "resource_sink": len(self._embedded_resource_sinks),
            "controller_sink": len(self._embedded_controller_sinks),
            "tasker_sink": len(self._embedded_tasker_sinks),
            "context_sink": len(self._embedded_context_sinks),
        }

    def _embedded_sinks_after(
        self, counts: dict[str, int]
    ) -> list[tuple[str, ResourceEventSink | ControllerEventSink | TaskerEventSink | ContextEventSink]]:
        return [
            ("resource_sink", sink)
            for sink in self._embedded_resource_sinks[counts["resource_sink"] :]
        ] + [
            ("controller_sink", sink)
            for sink in self._embedded_controller_sinks[counts["controller_sink"] :]
        ] + [
            ("tasker_sink", sink)
            for sink in self._embedded_tasker_sinks[counts["tasker_sink"] :]
        ] + [
            ("context_sink", sink)
            for sink in self._embedded_context_sinks[counts["context_sink"] :]
        ]

    @staticmethod
    def _collect_embedded_module_keys(
        root: Path, modules_before: set[Any]
    ) -> list[str]:
        """收集本次内置 agent 加载导入的模块名（字符串前缀匹配，避免 resolve 开销）。"""
        try:
            root_prefix = str(root.resolve()).replace("\\", "/").lower()
        except OSError:
            return []
        if not root_prefix.endswith("/"):
            root_prefix += "/"
        keys: list[str] = []
        for module_key in sys.modules.keys() - modules_before:
            if not isinstance(module_key, str):
                continue
            module = sys.modules.get(module_key)
            if module is None:
                continue
            module_file = getattr(module, "__file__", None)
            if not module_file:
                continue
            normalized = str(module_file).replace("\\", "/").lower()
            if normalized.startswith(root_prefix):
                keys.append(module_key)
        return sorted(keys)

    @staticmethod
    def _collect_imported_modules_under_root(
        root: Path, modules_before: set[Any]
    ) -> list[str]:
        imported_modules: list[str] = []
        for module_key in sys.modules.keys() - modules_before:
            if not isinstance(module_key, str):
                continue
            module = sys.modules.get(module_key)
            module_file = getattr(module, "__file__", None)
            if not module_file:
                continue
            try:
                module_path = Path(module_file).resolve()
                if module_path.is_relative_to(root):
                    imported_modules.append(f"{module_key} ({module_path})")
            except (OSError, ValueError):
                continue
        return sorted(imported_modules)

    @staticmethod
    def _patch_maa_resource_instance(resource: Resource):
        import maa.resource as maa_resource_module

        sentinel = object()
        old_value = getattr(maa_resource_module, "resource", sentinel)
        setattr(maa_resource_module, "resource", resource)

        def restore() -> None:
            if old_value is sentinel:
                try:
                    delattr(maa_resource_module, "resource")
                except AttributeError:
                    pass
            else:
                setattr(maa_resource_module, "resource", old_value)

        return restore

    def _rewrite_embedded_agent_sources(
        self, decorators: list[EmbeddedDecoratorInfo]
    ) -> list[Path]:
        rewritten: list[Path] = []
        for file_path in sorted({item.file_path for item in decorators}):
            try:
                text = file_path.read_text(encoding="utf-8")
            except OSError as exc:
                logger.warning("读取内置 agent 源文件失败，跳过改写 %s: %s", file_path, exc)
                continue

            original = text
            has_custom = (
                "@AgentServer.custom_action(" in text
                or "@AgentServer.custom_recognition(" in text
            )
            has_sink = any(
                f"@AgentServer.{decorator}()" in text
                for decorator in _EMBEDDED_AGENT_SERVER_SINK_DECORATORS
            )

            if has_custom:
                text = text.replace(
                    "@AgentServer.custom_action(", "@resource.custom_action("
                )
                text = text.replace(
                    "@AgentServer.custom_recognition(",
                    "@resource.custom_recognition(",
                )
                text = self._ensure_resource_import(text)

            if has_sink:
                text = re.sub(
                    (
                        r"^[ \t]*@AgentServer\."
                        r"(?:resource_sink|controller_sink|tasker_sink|context_sink)"
                        r"\(\)\r?\n"
                    ),
                    "",
                    text,
                    flags=re.MULTILINE,
                )

            if "AgentServer." not in text:
                text = re.sub(
                    r"^[ \t]*from maa\.agent\.agent_server import AgentServer\r?\n",
                    "",
                    text,
                    count=1,
                    flags=re.MULTILINE,
                )

            if text == original:
                continue

            try:
                file_path.write_text(text, encoding="utf-8")
            except OSError as exc:
                logger.warning("写回内置 agent 源文件失败 %s: %s", file_path, exc)
                continue
            rewritten.append(file_path)
        return rewritten

    @staticmethod
    def _ensure_resource_import(text: str) -> str:
        resource_import = "from maa.resource import resource"
        if resource_import in text:
            return text
        agent_import_pattern = (
            r"^[ \t]*from maa\.agent\.agent_server import AgentServer\r?\n"
        )
        if re.search(agent_import_pattern, text, flags=re.MULTILINE):
            return re.sub(
                agent_import_pattern,
                f"{resource_import}\n",
                text,
                count=1,
                flags=re.MULTILINE,
            )
        return f"{resource_import}\n{text}"

    _EMBEDDED_SKIP_DIRS = {
        ".git",
        ".hg",
        ".svn",
        ".venv",
        "venv",
        "env",
        "__pycache__",
        "site-packages",
        "dist-packages",
        "node_modules",
        "build",
        "dist",
    }

    def _scan_embedded_decorators(self, root: Path) -> list[EmbeddedDecoratorInfo]:
        decorators: list[EmbeddedDecoratorInfo] = []
        for file_path in sorted(root.rglob("*.py")):
            if self._should_skip_embedded_scan_file(root, file_path):
                continue
            try:
                tree = ast.parse(file_path.read_text(encoding="utf-8"))
            except (OSError, SyntaxError, UnicodeDecodeError) as exc:
                logger.warning("扫描内置 agent 装饰器失败，跳过 %s: %s", file_path, exc)
                continue

            module_name = self._module_name_from_path(root, file_path)
            if not module_name:
                continue
            for node in ast.walk(tree):
                if not isinstance(node, ast.ClassDef):
                    continue
                has_sink_decorator = False
                for decorator in node.decorator_list:
                    info = self._parse_embedded_decorator(
                        decorator, file_path, module_name, node.name
                    )
                    if info is not None:
                        has_sink_decorator = has_sink_decorator or info.kind.endswith(
                            "_sink"
                        )
                        decorators.append(info)
                if not has_sink_decorator:
                    implicit_sink_kind = self._implicit_sink_kind(node)
                    if implicit_sink_kind is None:
                        continue
                    decorators.append(
                        EmbeddedDecoratorInfo(
                            file_path=file_path,
                            module_name=module_name,
                            class_name=node.name,
                            kind=implicit_sink_kind,
                        )
                    )
        return decorators

    def _should_skip_embedded_scan_file(self, root: Path, file_path: Path) -> bool:
        try:
            relative = file_path.relative_to(root)
        except ValueError:
            return True
        return any(part in self._EMBEDDED_SKIP_DIRS for part in relative.parts)

    @staticmethod
    def _module_name_from_path(root: Path, file_path: Path) -> str | None:
        try:
            relative = file_path.relative_to(root)
        except ValueError:
            return None
        parts = list(relative.with_suffix("").parts)
        if not parts:
            return None
        if parts[-1] == "__init__":
            parts = parts[:-1]
        if not parts:
            return None
        return ".".join(parts)

    @staticmethod
    def _parse_embedded_decorator(
        decorator: ast.expr, file_path: Path, module_name: str, class_name: str
    ) -> EmbeddedDecoratorInfo | None:
        if not isinstance(decorator, ast.Call):
            return None
        func = decorator.func
        if not isinstance(func, ast.Attribute):
            return None

        owner = func.value
        owner_name = owner.id if isinstance(owner, ast.Name) else ""
        attr = func.attr

        if owner_name in {"AgentServer", "resource", "Resource"}:
            if attr == "custom_action":
                kind = "action"
            elif attr == "custom_recognition":
                kind = "recognition"
            else:
                return None
            register_name = None
            if decorator.args and isinstance(decorator.args[0], ast.Constant):
                if isinstance(decorator.args[0].value, str):
                    register_name = decorator.args[0].value
            return EmbeddedDecoratorInfo(
                file_path=file_path,
                module_name=module_name,
                class_name=class_name,
                kind=kind,
                register_name=register_name,
            )

        if owner_name == "AgentServer" and attr in _EMBEDDED_AGENT_SERVER_SINK_DECORATORS:
            return EmbeddedDecoratorInfo(
                file_path=file_path,
                module_name=module_name,
                class_name=class_name,
                kind=attr,
            )
        if owner_name == "MaaTasker" and attr == "tasker_sink":
            return EmbeddedDecoratorInfo(
                file_path=file_path,
                module_name=module_name,
                class_name=class_name,
                kind="tasker_sink",
            )
        return None

    @staticmethod
    def _implicit_sink_kind(node: ast.ClassDef) -> str | None:
        for base in node.bases:
            base_name = ""
            if isinstance(base, ast.Name):
                base_name = base.id
            elif isinstance(base, ast.Attribute):
                base_name = base.attr
            if base_name == "ResourceEventSink":
                return "resource_sink"
            if base_name == "ControllerEventSink":
                return "controller_sink"
            if base_name == "TaskerEventSink":
                return "tasker_sink"
            if base_name == "ContextEventSink":
                return "context_sink"
        return None

    def _load_embedded_decorator_modules(
        self, root: Path, decorators: list[EmbeddedDecoratorInfo]
    ) -> None:
        modules = sorted({item.module_name for item in decorators})
        for module_name in modules:
            if module_name in sys.modules:
                if self._module_belongs_to_root(sys.modules[module_name], root):
                    logger.debug("内置 agent 装饰器模块已由依赖链导入: %s", module_name)
                    continue
                del sys.modules[module_name]
            logger.info("导入内置 agent 装饰器模块: %s", module_name)
            importlib.import_module(module_name)

        for item in decorators:
            if not item.kind.endswith("_sink"):
                continue
            module = sys.modules.get(item.module_name)
            if module is None:
                continue
            class_obj = getattr(module, item.class_name, None)
            if class_obj is None:
                logger.warning(
                    "内置 agent sink 类不存在: %s.%s", item.module_name, item.class_name
                )
                continue
            instance = class_obj()
            self._register_embedded_sink(item.kind, instance, item)

    def _register_embedded_sink(
        self,
        kind: str,
        instance: Any,
        item: EmbeddedDecoratorInfo,
    ) -> None:
        class_name = f"{item.module_name}.{item.class_name}"
        if kind == "resource_sink":
            if not isinstance(instance, ResourceEventSink):
                raise TypeError(f"{class_name} 不是 ResourceEventSink 子类")
            logger.info("内置 agent 注册 Resource sink: %s", class_name)
            self._embedded_resource_sinks.append(instance)
            if self.resource is not None:
                self.resource.add_sink(instance)
            return

        if kind == "controller_sink":
            if not isinstance(instance, ControllerEventSink):
                raise TypeError(f"{class_name} 不是 ControllerEventSink 子类")
            logger.info("内置 agent 注册 Controller sink: %s", class_name)
            self._embedded_controller_sinks.append(instance)
            if self.controller is not None:
                self.controller.add_sink(instance)
            return

        if kind == "tasker_sink":
            if not isinstance(instance, TaskerEventSink):
                raise TypeError(f"{class_name} 不是 TaskerEventSink 子类")
            logger.info("内置 agent 注册 Tasker sink: %s", class_name)
            self._embedded_tasker_sinks.append(instance)
            if self.tasker is not None:
                self.tasker.add_sink(instance)
            return

        if kind == "context_sink":
            if not isinstance(instance, ContextEventSink):
                raise TypeError(f"{class_name} 不是 ContextEventSink 子类")
            logger.info("内置 agent 注册 Context sink: %s", class_name)
            self._embedded_context_sinks.append(instance)
            if self.tasker is not None:
                self.tasker.add_context_sink(instance)

    @staticmethod
    def _module_belongs_to_root(module: Any, root: Path) -> bool:
        module_file = getattr(module, "__file__", None)
        if not module_file:
            return False
        try:
            return Path(module_file).resolve().is_relative_to(root)
        except (OSError, ValueError):
            return False

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

    def load_embedded_aspect_ratio_sink(self) -> bool:
        """
        兼容旧调用点。

        内置模式的 Tasker sink 已在 load_embedded_agent_custom 中通过装饰器扫描统一加载。
        """
        logger.info("内置 Tasker sink 已随自定义组件扫描加载: %s 个", len(self._embedded_tasker_sinks))
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

    @asyncify
    def connect_wlroots(
        self,
        wlr_socket_path: str,
        use_win32_vk_code: bool = False,
    ) -> bool:
        if WlRootsController is None:
            raise RuntimeError("当前安装的 maa 版本不支持 WlRootsController")
        controller = WlRootsController(wlr_socket_path, use_win32_vk_code)
        controller = self._init_controller(controller)
        connected = controller.post_connection().wait().succeeded
        if not connected:
            print(f"Failed to connect wlroots socket {wlr_socket_path}")
            return False
        return True

    @asyncify
    def connect_macos(
        self,
        window_id: int,
        screencap_method: int = MaaMacOSScreencapMethodEnum.ScreenCaptureKit,
        input_method: int = MaaMacOSInputMethodEnum.GlobalEvent,
    ) -> bool:
        if MacOSController is None:
            raise RuntimeError("当前安装的 maa 版本不支持 MacOSController")
        screencap_method = (
            screencap_method or MaaMacOSScreencapMethodEnum.ScreenCaptureKit
        )
        input_method = input_method or MaaMacOSInputMethodEnum.GlobalEvent
        controller = MacOSController(window_id, screencap_method, input_method)
        controller = self._init_controller(controller)
        connected = controller.post_connection().wait().succeeded
        if not connected:
            print(f"Failed to connect macOS window {window_id}")
            return False
        return True

    def _init_controller(self, controller: Controller) -> Controller:
        if self.maa_controller_sink:
            controller.add_sink(self.maa_controller_sink)
        for sink in self._embedded_controller_sinks:
            controller.add_sink(sink)
        self.controller = controller
        return self.controller

    def _init_resource(self) -> Resource:
        if self.resource is None:
            self.resource = Resource()
            if self.maa_resource_sink:
                self.resource.add_sink(self.maa_resource_sink)
            for sink in self._embedded_resource_sinks:
                self.resource.add_sink(sink)
        return self.resource

    def _init_tasker(self) -> Tasker:
        if self.tasker is None:
            self.tasker = Tasker()
            self.tasker.add_context_sink(self.maa_context_sink)
            for sink in self._embedded_context_sinks:
                self.tasker.add_context_sink(sink)

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

    @staticmethod
    def _coerce_timeout_seconds(value: Any) -> int | None:
        if value is None:
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    def _resolve_agent_connect_timeout_ms(self, agent_data: dict) -> int | None:
        """解析 agent 连接超时（秒 → 毫秒）。返回 None 表示无限等待。"""
        for value in (
            self.agent_connection_timeout_seconds,
            agent_data.get("timeout"),
        ):
            seconds = self._coerce_timeout_seconds(value)
            if seconds is None:
                continue
            if seconds < 0:
                return None
            if seconds > 0:
                return seconds * 1000
        return self.DEFAULT_AGENT_CONNECT_TIMEOUT_SECONDS * 1000

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

        timeout_ms = self._resolve_agent_connect_timeout_ms(agent_data)
        self._last_agent_connect_timeout_seconds = (
            timeout_ms // 1000 if timeout_ms is not None else None
        )
        if timeout_ms is None:
            logger.debug("agent 连接超时: 无限等待")
        elif not client.set_timeout(timeout_ms):
            logger.warning("设置 agent 连接超时失败 (%sms)", timeout_ms)
        else:
            logger.debug("agent 连接超时: %sms", timeout_ms)

        if not client.connect():
            try:
                client.disconnect()
            except Exception as exc:
                logger.debug("agent 连接失败后断开异常: %s", exc)
            if timeout_ms is not None:
                logger.error(
                    "agent 连接超时 (%ss)",
                    self._last_agent_connect_timeout_seconds,
                )
                self._send_custom_info(MaaFWError.AGENT_CONNECTION_TIMEOUT)
            else:
                logger.error("agent 连接失败")
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

    def _wait_for_tasker_idle(self, tasker: Tasker) -> None:
        """等待 Tasker 完全停止，避免 CustomAction 回调仍在执行时触发原生析构。"""
        deadline = time.monotonic() + self.TASKER_IDLE_TIMEOUT_SECONDS
        while time.monotonic() < deadline:
            try:
                if not tasker.running and not tasker.stopping:
                    return
            except Exception as exc:
                logger.debug(f"查询 Tasker 状态失败，跳过空闲等待: {exc}")
                return
            time.sleep(self.TASKER_IDLE_POLL_INTERVAL_SECONDS)

        logger.warning(
            "等待 Tasker 空闲超时 (%.0fs)，将强制销毁",
            self.TASKER_IDLE_TIMEOUT_SECONDS,
        )

    def _cleanup_runtime(self) -> None:
        if not self._cleanup_lock.acquire(blocking=False):
            logger.debug("MaaFW 清理已在进行中，忽略重复请求")
            return

        try:
            if self.tasker:
                tasker = self.tasker
                try:
                    tasker.post_stop().wait()
                    self._wait_for_tasker_idle(tasker)
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
            self.agent_connection_timeout_seconds = None
            self._last_agent_connect_timeout_seconds = None
            self._purge_modules_under_root(self._last_custom_root)
            self._last_custom_root = None
            self._embedded_resource_sinks.clear()
            self._embedded_controller_sinks.clear()
            self._embedded_tasker_sinks.clear()
            self._embedded_context_sinks.clear()
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
