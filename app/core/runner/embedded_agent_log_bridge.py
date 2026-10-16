"""
将 embedded agent 包内 logging / loguru 日志转发到 Runner log_output（UI 日志面板）。

路径范围由调用方传入：须为 interface 解析出的 custom 根目录（及可选的补充根），
不得写死 agent/ 目录名。
"""

from __future__ import annotations

import importlib
import logging
import os
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

_CLIENT_APP_ROOT: Path | None = None

# 目录真实路径缓存：realpath 有文件系统开销，而 sys.modules 里同一目录会被反复问到。
_CANONICAL_DIR_CACHE: dict[str, str] = {}
_CANONICAL_DIR_CACHE_LIMIT = 512


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
    return os.path.normcase(str(file_path)).replace("\\", "/").lower()


def _normalize_absolute_path(file_path: str | Path) -> str:
    """低开销规范化路径，避免遍历 sys.modules 时反复调用 Path.resolve()。"""
    try:
        raw = os.fspath(file_path)
        absolute = raw if os.path.isabs(raw) else os.path.abspath(raw)
        return _normalize_path(os.path.normpath(absolute))
    except (TypeError, ValueError, OSError):
        return _normalize_path(str(file_path))


def _canonical_path(file_path: str | Path) -> str:
    """真实路径（展开 8.3 短名与软链接），按所在目录缓存以避免重复的系统调用。

    Windows 上同一目录可能以短名（``C:\\Users\\RUNNER~1\\...``）或长名出现：
    ``Path.resolve()`` / ``realpath`` 给出长名，而调用方传入的字符串可能是短名，
    只按字面规范化前缀比较会漏判（CI 的 TEMP 就是短名）。
    """
    normalized = _normalize_absolute_path(file_path)
    directory, _, name = normalized.rpartition("/")
    if not name:
        return ""
    canonical_dir = _CANONICAL_DIR_CACHE.get(directory)
    if canonical_dir is None:
        try:
            canonical_dir = _normalize_path(os.path.realpath(directory))
        except (ValueError, OSError):
            canonical_dir = ""
        if len(_CANONICAL_DIR_CACHE) >= _CANONICAL_DIR_CACHE_LIMIT:
            _CANONICAL_DIR_CACHE.clear()
        _CANONICAL_DIR_CACHE[directory] = canonical_dir
    return f"{canonical_dir}/{name}" if canonical_dir else ""


def _build_allowed_roots(
    custom_root: Path, extra_roots: Sequence[Path] = ()
) -> tuple[str, ...]:
    """
    将 interface 解析的 custom 目录（及额外根）转为用于路径比对的规范前缀。

    custom_root: 对应 interface 注入的 custom 字段（agent 入口脚本所在目录）。

    每个根同时记录“字面规范化”与“真实路径”两种前缀：调用方可能给短名或未
    resolve 的绝对路径，而模块 ``__file__`` 来自已 resolve 的 sys.path 条目（或相反），
    只存一种形式会漏判。
    """
    ordered: list[Path] = [custom_root, *extra_roots]
    prefixes: list[str] = []
    seen: set[str] = set()
    for raw in ordered:
        for base in (_normalize_absolute_path(raw), _canonical_path(raw)):
            if not base:
                continue
            prefix = base.rstrip("/") + "/"
            if prefix in seen:
                continue
            seen.add(prefix)
            prefixes.append(prefix)
    return tuple(prefixes)


def _client_app_root() -> Path:
    """MFW 主程序 app 包目录（绝对路径，懒加载缓存）。"""
    global _CLIENT_APP_ROOT
    if _CLIENT_APP_ROOT is None:
        import app as mfw_app

        _CLIENT_APP_ROOT = Path(mfw_app.__file__).resolve().parent
    return _CLIENT_APP_ROOT


def _is_client_log_path(file_path: str) -> bool:
    """主程序 app/ 目录下的日志不得进入 UI 桥接（避免与 logoutput_widget 形成环）。"""
    try:
        return Path(file_path).resolve().is_relative_to(_client_app_root())
    except (OSError, ValueError, TypeError):
        return False


def _is_under_custom_roots(file_path: str, allowed_roots: tuple[str, ...]) -> bool:
    if not file_path or not allowed_roots or _is_client_log_path(file_path):
        return False
    if _normalize_absolute_path(file_path).startswith(allowed_roots):
        return True
    # 字面形式不一致（8.3 短名 / 软链接）时再按真实路径比一次。
    return _canonical_path(file_path).startswith(allowed_roots)


def _should_skip_logging_logger(logger_obj: logging.Logger) -> bool:
    name = (logger_obj.name or "").strip()
    return bool(name.startswith("app."))


def collect_agent_loggers(
    custom_root: Path, allowed_roots: tuple[str, ...]
) -> list[Any]:
    """
    收集 custom 工程内的 logger（含 root），去重后挂载；由路径过滤保证不污染 app 日志。
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

    for mod in list(sys.modules.values()):
        if mod is None:
            continue
        file_name = getattr(mod, "__file__", None)
        if not file_name or not _is_under_custom_roots(file_name, allowed_roots):
            continue
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
    ) -> int:
        """
        :param custom_root: interface.custom 解析后的绝对路径（agent 源码根目录）
        :param extra_roots: 可选补充根（如与 custom 不同的入口父目录）
        """
        self.detach()
        self._allowed_roots = _build_allowed_roots(custom_root, extra_roots)
        attached = 0
        for logger_obj in collect_agent_loggers(custom_root, self._allowed_roots):
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
