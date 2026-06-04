"""
将 embedded agent 包内 logging / loguru 日志转发到 Runner log_output（UI 日志面板）。

仅在任务流生命周期内挂载，避免污染 app 自身日志。
"""

from __future__ import annotations

import importlib
import logging
import sys
from collections.abc import Callable
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


class _RunnerUiLogHandler(logging.Handler):
    """把标准 logging 记录转发到 UI log_output。"""

    def __init__(self, emit_fn: EmitFn):
        super().__init__(level=logging.INFO)
        self._emit_fn = emit_fn

    def emit(self, record: logging.LogRecord) -> None:
        try:
            if record.levelno < logging.INFO:
                return
            message = record.getMessage()
            if not message:
                return
            self._emit_fn(_logging_level_to_ui(record.levelno), message)
        except Exception:
            self.handleError(record)


def _path_under_roots(file_path: str, roots: tuple[str, ...]) -> bool:
    normalized = str(file_path).replace("\\", "/").lower()
    return any(normalized.startswith(root) for root in roots)


def collect_agent_loggers(agent_root: Path) -> list[Any]:
    """
    收集 agent 工程内可能用于输出的 logger 对象（logging.Logger 或 loguru logger）。
    """
    agent_root = agent_root.resolve()
    roots = (
        str(agent_root).replace("\\", "/").lower() + "/",
        str(agent_root.parent).replace("\\", "/").lower() + "/",
    )
    found: list[Any] = []
    seen_ids: set[int] = set()

    def _add(obj: Any) -> None:
        oid = id(obj)
        if oid in seen_ids:
            return
        if _is_logging_logger(obj) or _is_loguru_logger(obj):
            seen_ids.add(oid)
            found.append(obj)

    for mod_name in ("utils", "utils.logger"):
        try:
            mod = importlib.import_module(mod_name)
        except Exception:
            continue
        for attr in ("logger", "log"):
            _add(getattr(mod, attr, None))

    for mod in list(sys.modules.values()):
        if mod is None:
            continue
        file_name = getattr(mod, "__file__", None)
        if not file_name or not _path_under_roots(file_name, roots):
            continue
        for attr in ("logger", "log"):
            _add(getattr(mod, attr, None))

    return found


class EmbeddedAgentLogBridge:
    """任务流内临时挂载 / 卸载 embedded agent 日志转发。"""

    def __init__(self) -> None:
        self._emit_fn: EmitFn | None = None
        self._logging_handlers: list[tuple[logging.Logger, _RunnerUiLogHandler]] = []
        self._loguru_sinks: list[tuple[Any, int]] = []

    def attach(self, emit_fn: EmitFn, agent_root: Path) -> int:
        self.detach()
        self._emit_fn = emit_fn
        attached = 0
        for logger_obj in collect_agent_loggers(agent_root):
            if _is_logging_logger(logger_obj):
                handler = _RunnerUiLogHandler(emit_fn)
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
        def _sink(message: Any) -> None:
            try:
                record = message.record
                level_name = record["level"].name
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
        self._emit_fn = None
