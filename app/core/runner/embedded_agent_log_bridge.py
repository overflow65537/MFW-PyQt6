"""
将 embedded agent 包内 logging / loguru 日志转发到 Runner log_output（UI 日志面板）。

路径范围由调用方传入：须为 interface 解析出的 custom 根目录（及可选的补充根），
不得写死 agent/ 目录名。
"""

from __future__ import annotations

import importlib
import logging
import sys
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

EmitFn = Callable[[str, str], None]

_LOGGING_TO_UI = {
    logging.DEBUG: "INFO",
    logging.INFO: "INFO",
    logging.WARNING: "WARNING",
    logging.ERROR: "ERROR",
    logging.CRITICAL: "CRITICAL",
}

_LOGURU_TO_UI = {
    "TRACE": "INFO",
    "DEBUG": "INFO",
    "INFO": "INFO",
    "SUCCESS": "INFO",
    "WARNING": "WARNING",
    "ERROR": "ERROR",
    "CRITICAL": "CRITICAL",
}

_CLIENT_PATH_MARKERS = ("/app/", "\\app\\")


def _logging_level_to_ui(levelno: int) -> str:
    return _LOGGING_TO_UI.get(levelno, "INFO")


def _loguru_level_to_ui(level_name: str) -> str:
    return _LOGURU_TO_UI.get(str(level_name).upper(), "INFO")


def _is_loguru_logger(obj: Any) -> bool:
    return (
        obj is not None
        and callable(getattr(obj, "add", None))
        and callable(getattr(obj, "remove", None))
    )


def _is_logging_logger(obj: Any) -> bool:
    return isinstance(obj, logging.Logger)


def _normalize_path(file_path: str) -> str:
    return str(file_path).replace("\\", "/").lower()


def _build_allowed_roots(
    custom_root: Path, extra_roots: Sequence[Path] = ()
) -> tuple[str, ...]:
    """
    将 interface 解析的 custom 目录（及额外根）转为用于路径比对的规范前缀。

    custom_root: 对应 interface 注入的 custom 字段（agent 入口脚本所在目录）。
    """
    ordered: list[Path] = [custom_root, *extra_roots]
    prefixes: list[str] = []
    seen: set[str] = set()
    for raw in ordered:
        try:
            resolved = raw.resolve()
        except OSError:
            continue
        prefix = str(resolved).replace("\\", "/").lower() + "/"
        if prefix in seen:
            continue
        seen.add(prefix)
        prefixes.append(prefix)
    return tuple(prefixes)


def _resolve_log_path(file_path: str) -> str:
    if not file_path:
        return ""
    path = Path(file_path)
    try:
        if path.is_absolute():
            return str(path.resolve())
    except OSError:
        pass
    try:
        return str((Path.cwd() / path).resolve())
    except OSError:
        return str(path)


def _is_client_log_path(file_path: str) -> bool:
    """主程序 app/ 目录下的日志不得进入 UI 桥接（避免与 logoutput_widget 形成环）。"""
    normalized = _normalize_path(file_path)
    return any(marker in normalized for marker in _CLIENT_PATH_MARKERS)


def _is_under_custom_roots(file_path: str, allowed_roots: tuple[str, ...]) -> bool:
    if not file_path or not allowed_roots or _is_client_log_path(file_path):
        return False
    normalized = _normalize_path(file_path)
    if any(normalized.startswith(root) for root in allowed_roots):
        return True
    try:
        path_obj = Path(_resolve_log_path(file_path)).resolve()
        for root in allowed_roots:
            root_path = Path(root.rstrip("/"))
            if path_obj.is_relative_to(root_path):
                return True
    except (OSError, ValueError):
        pass
    return False


def _should_skip_logging_logger(logger_obj: logging.Logger) -> bool:
    name = (logger_obj.name or "").strip()
    return bool(name.startswith("app."))


def collect_agent_loggers(
    custom_root: Path,
    allowed_roots: tuple[str, ...],
    *,
    module_keys: Sequence[str] | None = None,
) -> list[Any]:
    """
    收集 custom 工程内的 logger（含 root），去重后挂载；由路径过滤保证不污染 app 日志。

    module_keys: 内置 agent 加载后已导入的模块名，传入时仅扫描这些模块，避免遍历 sys.modules。
    """
    found: list[Any] = []
    seen_logging_names: set[str] = set()
    seen_loguru_ids: set[int] = set()

    def _add(obj: Any) -> None:
        if _is_logging_logger(obj):
            if _should_skip_logging_logger(obj):
                return
            if obj.name in seen_logging_names:
                return
            seen_logging_names.add(obj.name)
            found.append(obj)
        elif _is_loguru_logger(obj):
            oid = id(obj)
            if oid in seen_loguru_ids:
                return
            seen_loguru_ids.add(oid)
            found.append(obj)

    for mod_name in ("utils.logger", "utils"):
        try:
            mod = importlib.import_module(mod_name)
        except Exception:
            continue
        for attr in ("logger", "log"):
            _add(getattr(mod, attr, None))

    if module_keys:
        modules_to_scan = [
            sys.modules[key]
            for key in module_keys
            if isinstance(key, str) and sys.modules.get(key) is not None
        ]
    else:
        modules_to_scan = [
            mod
            for mod in sys.modules.values()
            if mod is not None
            and getattr(mod, "__file__", None)
            and _is_under_custom_roots(str(mod.__file__), allowed_roots)
        ]

    for mod in modules_to_scan:
        for attr in ("logger", "log"):
            _add(getattr(mod, attr, None))

    return found


class _RunnerUiLogHandler(logging.Handler):
    """把 custom 源文件内的标准 logging 记录转发到 UI log_output。"""

    def __init__(self, emit_fn: EmitFn, allowed_roots: tuple[str, ...]):
        super().__init__(level=logging.INFO)
        self._emit_fn = emit_fn
        self._allowed_roots = allowed_roots

    def emit(self, record: logging.LogRecord) -> None:
        try:
            if record.levelno < logging.INFO:
                return
            pathname = getattr(record, "pathname", "") or ""
            if not _is_under_custom_roots(pathname, self._allowed_roots):
                return
            message = record.getMessage()
            if not message:
                return
            self._emit_fn(_logging_level_to_ui(record.levelno), message)
        except Exception:
            self.handleError(record)


class EmbeddedAgentLogBridge:
    """任务流内临时挂载 / 卸载 embedded agent 日志转发。"""

    def __init__(self) -> None:
        self._allowed_roots: tuple[str, ...] = ()
        self._logging_handlers: list[tuple[logging.Logger, _RunnerUiLogHandler]] = []
        self._loguru_sinks: list[tuple[Any, int]] = []

    def attach(
        self,
        emit_fn: EmitFn,
        *,
        custom_root: Path,
        extra_roots: Sequence[Path] = (),
        module_keys: Sequence[str] | None = None,
    ) -> int:
        """
        :param custom_root: interface.custom 解析后的绝对路径（agent 源码根目录）
        :param extra_roots: 可选补充根（如与 custom 不同的入口父目录）
        :param module_keys: 内置 agent 已导入的模块名，用于加速 logger 收集
        """
        self.detach()
        self._allowed_roots = _build_allowed_roots(custom_root, extra_roots)
        attached = 0
        for logger_obj in collect_agent_loggers(
            custom_root, self._allowed_roots, module_keys=module_keys
        ):
            if _is_logging_logger(logger_obj):
                handler = _RunnerUiLogHandler(emit_fn, self._allowed_roots)
                logger_obj.addHandler(handler)
                self._logging_handlers.append((logger_obj, handler))
                attached += 1
            elif _is_loguru_logger(logger_obj):
                sink_id = self._attach_loguru(logger_obj, emit_fn)
                if sink_id is not None:
                    self._loguru_sinks.append((logger_obj, sink_id))
                    attached += 1
        return attached

    def _attach_loguru(self, logger_obj: Any, emit_fn: EmitFn) -> int | None:
        allowed_roots = self._allowed_roots

        def _sink(message: Any) -> None:
            try:
                record = message.record
                level_name = record["level"].name
                file_info = record["file"]
                file_path = getattr(file_info, "path", None) or str(file_info)
                if not _is_under_custom_roots(str(file_path), allowed_roots):
                    return
                text = str(record["message"])
                if not text:
                    return
                if str(level_name).upper() == "DEBUG":
                    return
                emit_fn(_loguru_level_to_ui(level_name), text)
            except Exception:
                return

        try:
            return int(logger_obj.add(_sink, level="INFO", format="{message}"))
        except Exception:
            return None

    def detach(self) -> None:
        for logger_obj, handler in self._logging_handlers:
            try:
                logger_obj.removeHandler(handler)
                handler.close()
            except Exception:
                pass
        self._logging_handlers.clear()

        for logger_obj, sink_id in self._loguru_sinks:
            try:
                logger_obj.remove(sink_id)
            except Exception:
                pass
        self._loguru_sinks.clear()
        self._allowed_roots = ()
