"""PI v2.9 telemetry 与 focus.trace 处理服务。"""

from __future__ import annotations

from collections import defaultdict, deque
from hashlib import sha256
import importlib
import os
import platform
import sys
import threading
import time
from typing import Any, Mapping
import uuid

from PySide6.QtCore import QObject, Slot

from app.common.__version__ import __version__
from app.common.config import cfg
from app.core.item import RunnerEvents
from app.utils.logger import logger
from app.utils.version_policy import version_disallows_auto_update


MAX_OPTION_ITEMS = 100
MAX_OPTION_VALUE_LENGTH = 512
MAX_TRACED_NODES_PER_TASK = 1000


def resolve_trace(details: Mapping[str, Any], message: str) -> bool:
    """解析 PI v2.9.1 focus.trace 的有效值。"""
    focus = details.get("focus")
    entry = focus.get(message) if isinstance(focus, Mapping) else None
    if isinstance(entry, Mapping) and isinstance(entry.get("trace"), bool):
        return bool(entry["trace"])
    return message == "Node.PipelineNode.Failed"


def should_process_node(message: str, details: Mapping[str, Any]) -> bool:
    """过滤无需参与遥测的高频 Node 回调。"""
    if message in ("Node.PipelineNode.Starting", "Node.PipelineNode.Failed"):
        return True
    if not message.startswith("Node."):
        return False
    focus = details.get("focus")
    entry = focus.get(message) if isinstance(focus, Mapping) else None
    return isinstance(entry, Mapping) and "trace" in entry


def _unwrap_option_value(value: Any) -> Any:
    if isinstance(value, Mapping) and "value" in value:
        return value.get("value")
    return value


def _bounded_value(value: Any) -> str:
    text = str(value)
    if len(text) > MAX_OPTION_VALUE_LENGTH:
        return text[:MAX_OPTION_VALUE_LENGTH]
    return text


def build_task_option_summary(
    option_values: Mapping[str, Any],
    option_definitions: Mapping[str, Any],
) -> dict[str, str]:
    """生成隐私安全的任务选项摘要。"""
    summary: dict[str, str] = {}
    for option_name, stored_value in option_values.items():
        if len(summary) >= MAX_OPTION_ITEMS or str(option_name).startswith("_"):
            continue
        option_def = option_definitions.get(option_name, {})
        if not isinstance(option_def, Mapping):
            option_def = {}
        option_type = str(option_def.get("type", "select")).lower()
        value = _unwrap_option_value(stored_value)

        if option_type in ("select", "switch"):
            summary[str(option_name)] = _bounded_value(value)
        elif option_type == "checkbox":
            if isinstance(value, list):
                summary[str(option_name)] = _bounded_value(",".join(map(str, value)))
        elif option_type == "hotkey":
            if isinstance(value, Mapping):
                for field_name, field_value in value.items():
                    if len(summary) >= MAX_OPTION_ITEMS:
                        break
                    summary[f"{option_name}.{field_name}"] = _bounded_value(field_value)
        elif option_type == "input" and isinstance(value, Mapping):
            input_types = {
                str(item.get("name")): str(item.get("pipeline_type", "string")).lower()
                for item in option_def.get("inputs", [])
                if isinstance(item, Mapping) and item.get("name")
            }
            for field_name, field_value in value.items():
                if len(summary) >= MAX_OPTION_ITEMS:
                    break
                key = f"{option_name}.{field_name}"
                if input_types.get(str(field_name)) in ("int", "bool"):
                    summary[key] = _bounded_value(field_value)
                else:
                    summary[key] = "filled" if str(field_value or "") else "empty"
    return summary


class TelemetryService(QObject):
    """管理 Sentry 生命周期并将 Runner 事件转换为事务与 Span。"""

    def __init__(
        self,
        runner_events: RunnerEvents,
        interface: Mapping[str, Any] | None = None,
        *,
        debug_override: bool | None = None,
    ):
        super().__init__()
        self.runner_events = runner_events
        self._debug_override = debug_override
        self._interface: dict[str, Any] = {}
        self._sentry: Any = None
        self._init_guard: Any = None
        self._active = False
        self._tracing = False
        self._session_started = False
        self._configuration_key: tuple[Any, ...] | None = None
        self._transaction: Any = None
        self._task_spans: dict[int, Any] = {}
        self._pending_tasks: dict[str, deque[dict[str, Any]]] = defaultdict(deque)
        self._active_task_id: int | None = None
        self._step_starts: dict[int, tuple[int | None, float]] = {}
        self._traced_nodes: dict[int, int] = defaultdict(int)
        self._lock = threading.RLock()

        self._connect_runner_events(self.runner_events)
        self.configure_from_interface(interface or {})

    def _connect_runner_events(self, runner_events: RunnerEvents) -> None:
        runner_events.callback.connect(self._on_callback)
        runner_events.telemetry.connect(self._on_telemetry_event)

    def _disconnect_runner_events(self, runner_events: RunnerEvents) -> None:
        for signal, slot in (
            (runner_events.callback, self._on_callback),
            (runner_events.telemetry, self._on_telemetry_event),
        ):
            try:
                signal.disconnect(slot)
            except (RuntimeError, TypeError):
                pass

    def set_runner_events(self, runner_events: RunnerEvents) -> None:
        """切换当前运行配置对应的 Runner 事件源。"""
        if runner_events is self.runner_events:
            return
        self._disconnect_runner_events(self.runner_events)
        self.runner_events = runner_events
        self._connect_runner_events(runner_events)

    @property
    def is_active(self) -> bool:
        return self._active

    def is_forced_disabled(self, interface: Mapping[str, Any] | None = None) -> bool:
        if os.environ.get("MFW_TELEMETRY_FORCE") == "1":
            return False
        if self._debug_override is not None:
            return self._debug_override
        current = interface or self._interface
        resource_version = str(current.get("version", "") or "")
        if version_disallows_auto_update(resource_version):
            return True
        if version_disallows_auto_update(__version__) or "beta" in __version__.lower():
            return True
        return not bool(getattr(sys, "frozen", False))

    def configure_from_interface(self, interface: Mapping[str, Any]) -> None:
        self._interface = dict(interface or {})
        telemetry = self._interface.get("telemetry", {})
        sentry_config = (
            telemetry.get("sentry", {})
            if isinstance(telemetry, Mapping)
            else {}
        )
        if not isinstance(sentry_config, Mapping):
            sentry_config = {}
        dsn = str(sentry_config.get("dsn", "") or "").strip()
        enabled = bool(cfg.get(cfg.telemetry_enabled))
        forced_disabled = self.is_forced_disabled(self._interface)
        tracing = sentry_config.get("tracing", True) is not False
        try:
            sample_rate = float(sentry_config.get("traces_sample_rate", 1.0))
        except (TypeError, ValueError):
            sample_rate = 1.0
        sample_rate = max(0.0, min(1.0, sample_rate)) if tracing else 0.0

        environment = str(sentry_config.get("environment", "") or "").strip()
        if not environment:
            channel_names = {0: "alpha", 1: "beta", 2: "stable"}
            try:
                environment = channel_names.get(
                    int(cfg.get(cfg.resource_update_channel)), "production"
                )
            except (TypeError, ValueError):
                environment = "production"

        project_name = str(self._interface.get("name", "unknown") or "unknown")
        project_version = str(self._interface.get("version", "unknown") or "unknown")
        configuration_key = (
            dsn,
            enabled,
            forced_disabled,
            tracing,
            sample_rate,
            environment,
            project_name,
            project_version,
        )
        should_enable = bool(dsn and enabled and not forced_disabled)
        if configuration_key == self._configuration_key and (
            self._active or not should_enable
        ):
            return
        self._configuration_key = configuration_key
        if not should_enable:
            self.shutdown()
            return

        self.shutdown()
        try:
            self._sentry = importlib.import_module("sentry_sdk")
            self._init_guard = self._sentry.init(
                dsn=dsn,
                release=f"MFW@{__version__}+{project_name}@{project_version}",
                environment=environment,
                traces_sample_rate=sample_rate,
                send_default_pii=False,
                auto_session_tracking=True,
                shutdown_timeout=1,
            )
            self._sentry.set_user({"id": self._anonymous_machine_id()})
            self._sentry.set_tag("app.name", project_name)
            self._sentry.set_tag("app.version", project_version)
            self._sentry.set_tag("client.version", __version__)
            start_session = getattr(self._sentry, "start_session", None)
            if callable(start_session):
                start_session()
                self._session_started = True
            self._tracing = tracing
            self._active = True
            logger.info(
                "PI 匿名遥测已启用: project=%s environment=%s tracing=%s",
                project_name,
                environment,
                tracing,
            )
        except Exception as exc:
            self._active = False
            self._tracing = False
            self._sentry = None
            self._init_guard = None
            logger.warning("初始化 PI 匿名遥测失败，已禁用: %s", exc)

    def set_user_enabled(self, enabled: bool) -> None:
        cfg.set(cfg.telemetry_enabled, bool(enabled))
        self.configure_from_interface(self._interface)

    def on_run_start(
        self, task_names: list[str], controller: Mapping[str, Any] | None = None
    ) -> None:
        if not self._active or not self._tracing or self._sentry is None:
            return
        with self._lock:
            self._finish_run(cancelled=True)
            try:
                self._transaction = self._sentry.start_transaction(
                    name="mfw.task_run", op="mfw.run"
                )
                self._set_data(self._transaction, "task_count", len(task_names))
                self._set_data(self._transaction, "tasks", ",".join(task_names))
                if controller:
                    self._set_data(
                        self._transaction, "controller.name", controller.get("name", "")
                    )
                    self._set_data(
                        self._transaction, "controller.type", controller.get("type", "")
                    )
            except Exception as exc:
                logger.debug("创建遥测事务失败: %s", exc)
                self._transaction = None

    def prepare_task(
        self,
        entry: str,
        option_values: Mapping[str, Any],
        display_name: str | None = None,
    ) -> None:
        if not self._active or not self._tracing:
            return
        options = self._interface.get("option", {})
        summary = build_task_option_summary(
            option_values, options if isinstance(options, Mapping) else {}
        )
        with self._lock:
            self._pending_tasks[str(entry)].append(
                {"name": str(display_name or entry), "options": summary}
            )

    def on_task_start(self, task_id: int, entry: str) -> None:
        if not self._active or not self._tracing or self._transaction is None:
            return
        with self._lock:
            meta = (
                self._pending_tasks[str(entry)].popleft()
                if self._pending_tasks.get(str(entry))
                else {"name": str(entry), "options": {}}
            )
            try:
                span = self._transaction.start_child(
                    op="mfw.task", description=meta["name"]
                )
                self._set_data(span, "task", meta["name"])
                self._set_data(span, "task_id", task_id)
                for key, value in meta["options"].items():
                    self._set_data(span, f"option.{key}", value)
                self._task_spans[task_id] = span
                self._active_task_id = task_id
            except Exception as exc:
                logger.debug("创建任务遥测 Span 失败: %s", exc)

    def on_task_finished(self, task_id: int, failed: bool = False) -> None:
        with self._lock:
            span = self._task_spans.pop(task_id, None)
            if span is not None:
                self._finish_span(span, "internal_error" if failed else "ok")
            self._step_starts.pop(task_id, None)
            self._traced_nodes.pop(task_id, None)
            if self._active_task_id == task_id:
                self._active_task_id = None

    def on_node_event(self, message: str, details: Mapping[str, Any]) -> None:
        if (
            not self._active
            or not self._tracing
            or not should_process_node(message, details)
        ):
            return
        task_id = self._coerce_int(details.get("task_id"))
        node_id = self._coerce_int(details.get("node_id"))
        if task_id is None:
            return
        if message == "Node.PipelineNode.Starting":
            with self._lock:
                self._step_starts[task_id] = (node_id, time.monotonic())
        if not resolve_trace(details, message):
            return

        with self._lock:
            self._traced_nodes[task_id] += 1
            if self._traced_nodes[task_id] > MAX_TRACED_NODES_PER_TASK:
                return
            parent = self._task_spans.get(task_id)
            if parent is None and self._active_task_id is not None:
                parent = self._task_spans.get(self._active_task_id)
            if parent is None:
                parent = self._transaction
            if parent is None:
                return

            node_details = details.get("node_details")
            hit_name = (
                node_details.get("name")
                if isinstance(node_details, Mapping)
                and message.startswith("Node.PipelineNode.")
                else None
            )
            node_name = str(hit_name or details.get("name", "") or "")
            if not node_name:
                return
            try:
                span = parent.start_child(op="mfw.node", description=node_name)
                self._set_data(span, "message", message)
                self._set_data(span, "task_id", task_id)
                if node_id is not None:
                    self._set_data(span, "node_id", node_id)
                search_node = str(details.get("name", "") or "")
                if hit_name and search_node and search_node != hit_name:
                    self._set_data(span, "search_node", search_node)
                if message == "Node.PipelineNode.Failed":
                    self._set_data(span, "stage", "action" if hit_name else "recognition")
                started = self._step_starts.get(task_id)
                if started and (node_id is None or started[0] == node_id):
                    self._set_data(
                        span, "duration_ms", int((time.monotonic() - started[1]) * 1000)
                    )
                self._finish_span(
                    span,
                    "internal_error"
                    if message.endswith(".Failed")
                    else "ok",
                )
            except Exception as exc:
                logger.debug("创建节点遥测 Span 失败: %s", exc)

    def on_run_finished(self) -> None:
        with self._lock:
            self._finish_run(cancelled=False)

    def on_run_cancelled(self) -> None:
        with self._lock:
            self._finish_run(cancelled=True)

    def shutdown(self) -> None:
        with self._lock:
            self._finish_run(cancelled=True)
            sentry = self._sentry
            guard = self._init_guard
            self._active = False
            self._tracing = False
            self._sentry = None
            self._init_guard = None
        if sentry is not None:
            try:
                end_session = getattr(sentry, "end_session", None)
                if self._session_started and callable(end_session):
                    end_session()
                sentry.flush(timeout=1)
            except Exception:
                pass
        self._session_started = False
        if guard is not None:
            try:
                guard.__exit__(None, None, None)
            except Exception:
                pass

    @Slot(dict)
    def _on_telemetry_event(self, payload: dict) -> None:
        event = str(payload.get("event", ""))
        if event == "configure":
            self.configure_from_interface(payload.get("interface", {}) or {})
        elif event == "run_start":
            self.on_run_start(
                list(payload.get("tasks", []) or []),
                payload.get("controller"),
            )
        elif event == "prepare_task":
            self.prepare_task(
                str(payload.get("name", "")),
                payload.get("options", {}) or {},
                str(payload.get("display_name", "") or ""),
            )
        elif event == "run_finished":
            self.on_run_finished()
        elif event == "run_cancelled":
            self.on_run_cancelled()

    @Slot(dict)
    def _on_callback(self, payload: dict) -> None:
        signal_name = payload.get("name")
        if signal_name == "node":
            details = payload.get("details", {})
            if isinstance(details, Mapping):
                self.on_node_event(str(payload.get("message", "")), details)
        elif signal_name == "task":
            task_id = self._coerce_int(payload.get("task_id"))
            if task_id is None:
                return
            status = self._coerce_int(payload.get("status"))
            if status == 1:
                self.on_task_start(task_id, str(payload.get("task", "")))
            elif status in (2, 3):
                self.on_task_finished(task_id, failed=status == 3)

    def _finish_run(self, cancelled: bool) -> None:
        for task_id, span in list(self._task_spans.items()):
            self._finish_span(span, "cancelled" if cancelled else "ok")
            self._task_spans.pop(task_id, None)
        if self._transaction is not None:
            self._set_data(
                self._transaction,
                "result",
                "cancelled" if cancelled else "completed",
            )
            self._finish_span(
                self._transaction, "cancelled" if cancelled else "ok"
            )
        self._transaction = None
        self._pending_tasks.clear()
        self._active_task_id = None
        self._step_starts.clear()
        self._traced_nodes.clear()

    @staticmethod
    def _set_data(span: Any, key: str, value: Any) -> None:
        try:
            span.set_data(key, value)
        except Exception:
            pass

    @staticmethod
    def _finish_span(span: Any, status: str) -> None:
        try:
            span.set_status(status)
        except Exception:
            pass
        try:
            span.finish()
        except Exception:
            pass

    @staticmethod
    def _coerce_int(value: Any) -> int | None:
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _anonymous_machine_id() -> str:
        raw = f"{uuid.getnode()}:{platform.node()}:{platform.system()}"
        return sha256(f"mfw-telemetry-v1:{raw}".encode("utf-8")).hexdigest()


__all__ = [
    "TelemetryService",
    "build_task_option_summary",
    "resolve_trace",
    "should_process_node",
]
