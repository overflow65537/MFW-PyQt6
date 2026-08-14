"""Per-configuration runtime state and runner lifecycle."""

from __future__ import annotations

import asyncio
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any, Awaitable, Callable

from PySide6.QtCore import QByteArray, QObject, Signal, Slot

from app.core.item import RunnerEvents
from app.core.log_processor import CallbackLogProcessor
from app.core.runner.monitor_task import MonitorTask
from app.core.runner.task_flow import TaskFlowRunner
from app.core.service.config_service import ConfigService
from app.core.service.task_service import TaskService


@dataclass(slots=True)
class RuntimeLogEntry:
    """UI-independent log record retained by one configuration context."""

    level: str
    text: str
    timestamp: str
    task_id: str | None = None
    image_bytes: QByteArray | None = None


class RuntimeLogStore(QObject):
    """Bounded in-memory log history owned by one runtime context."""

    entry_added = Signal(object)
    cleared = Signal()

    def __init__(
        self,
        *,
        max_entries: int = 500,
        task_id_provider: Callable[[], str | None] | None = None,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._max_entries = max(1, int(max_entries))
        self._task_id_provider = task_id_provider
        self._entries: list[RuntimeLogEntry] = []

    @property
    def entries(self) -> tuple[RuntimeLogEntry, ...]:
        return tuple(self._entries)

    def set_max_entries(self, value: int) -> None:
        self._max_entries = max(1, int(value))
        if len(self._entries) > self._max_entries:
            del self._entries[: len(self._entries) - self._max_entries]

    @Slot(str, str)
    def append(self, level: str, text: str) -> None:
        task_id = self._task_id_provider() if self._task_id_provider else None
        entry = RuntimeLogEntry(
            level=str(level or "INFO").upper(),
            text=str(text or ""),
            timestamp=datetime.now().strftime("%H:%M:%S"),
            task_id=task_id,
        )
        self._entries.append(entry)
        if len(self._entries) > self._max_entries:
            del self._entries[: len(self._entries) - self._max_entries]
        self.entry_added.emit(entry)

    @Slot()
    def clear(self) -> None:
        self._entries.clear()
        self.cleared.emit()


class RuntimeMonitorState(QObject):
    """Latest monitor frame/ROI state for one configuration context."""

    frame_changed = Signal(object)
    frame_cleared = Signal()
    roi_changed = Signal(object)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._latest_frame: Any | None = None
        self._latest_roi: dict | None = None

    @property
    def latest_frame(self) -> Any | None:
        frame = self._latest_frame
        copy = getattr(frame, "copy", None)
        return copy() if callable(copy) else frame

    @property
    def latest_roi(self) -> dict | None:
        return deepcopy(self._latest_roi)

    @Slot(object)
    def update_frame(self, frame: Any) -> None:
        copy = getattr(frame, "copy", None)
        self._latest_frame = copy() if callable(copy) else frame
        self.frame_changed.emit(self.latest_frame)

    @Slot()
    def clear_frame(self) -> None:
        self._latest_frame = None
        self.frame_cleared.emit()

    @Slot(dict)
    def update_roi(self, payload: dict) -> None:
        if not isinstance(payload, dict):
            return
        if payload.get("clear"):
            self._latest_roi = None
        else:
            self._latest_roi = deepcopy(payload)
        self.roi_changed.emit(self.latest_roi or {"clear": True})

    @Slot()
    def clear_roi(self) -> None:
        self._latest_roi = None
        self.roi_changed.emit({"clear": True})

    @Slot()
    def clear(self) -> None:
        self.clear_frame()
        self.clear_roi()


class RuntimeState(StrEnum):
    """Lifecycle state of one configuration runtime."""

    IDLE = "idle"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    FAILED = "failed"


class RuntimeContext(QObject):
    """All non-persistent runtime objects belonging to one configuration."""

    state_changed = Signal(str)

    def __init__(
        self,
        config_id: str,
        task_service: TaskService,
        config_service: ConfigService,
        *,
        run_config_callback: Callable[[str], Awaitable[Any] | Any] | None = None,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self.config_id = str(config_id)
        self.events = RunnerEvents(self)
        self.task_runner = TaskFlowRunner(
            task_service=task_service,
            config_service=config_service,
            runner_events=self.events,
            run_config_callback=run_config_callback,
            config_id=self.config_id,
        )
        self.task_runner.setParent(self)
        self.monitor_task = MonitorTask(
            task_service=task_service,
            config_service=config_service,
            runner_events=self.events,
            config_id=self.config_id,
            maafw=self.task_runner.maafw,
        )
        self.monitor_task.setParent(self)
        self.logs = RuntimeLogStore(
            task_id_provider=lambda: getattr(
                self.task_runner, "_current_running_task_id", None
            ),
            parent=self,
        )
        self.monitor = RuntimeMonitorState(parent=self)
        self.log_processor = CallbackLogProcessor(self.events, parent=self)
        self._state = RuntimeState.IDLE
        self._lifecycle_lock = asyncio.Lock()
        self._run_task: asyncio.Task[Any] | None = None
        self._stop_requested = False

        self.events.log_output.connect(self.logs.append)
        self.events.log_clear_requested.connect(self.logs.clear)
        self.events.monitor_recognition_roi.connect(self.monitor.update_roi)
        self.events.task_flow_finished.connect(self._on_task_flow_finished)
        self.events.start_button_status.connect(self._on_button_status_changed)

    @property
    def state(self) -> RuntimeState:
        return self._state

    @property
    def run_task(self) -> asyncio.Task[Any] | None:
        return self._run_task

    @property
    def button_status(self) -> dict[str, str]:
        if self._state in (RuntimeState.STARTING, RuntimeState.RUNNING):
            return {"text": "STOP", "status": "enabled"}
        if self._state == RuntimeState.STOPPING:
            return {"text": "STOP", "status": "disabled"}
        return {"text": "START", "status": "enabled"}

    def _set_state(self, state: RuntimeState) -> None:
        if state == self._state:
            return
        self._state = state
        self.state_changed.emit(state.value)

    async def start(
        self,
        task_id: str | None = None,
        *,
        start_task_id: str | None = None,
    ) -> bool:
        """Start this configuration without waiting for the whole flow to finish."""
        async with self._lifecycle_lock:
            if self._run_task is not None and not self._run_task.done():
                return False
            if self._state in (
                RuntimeState.STARTING,
                RuntimeState.RUNNING,
                RuntimeState.STOPPING,
            ):
                return False
            self._stop_requested = False
            self.task_runner.need_stop = False
            self.task_runner._manual_stop = False
            self._set_state(RuntimeState.STARTING)
            self._run_task = asyncio.create_task(
                self._drive_run(task_id, start_task_id=start_task_id),
                name=f"mfw-runtime-{self.config_id}",
            )
            return True

    async def _drive_run(
        self,
        task_id: str | None,
        *,
        start_task_id: str | None,
    ) -> None:
        failed = False
        try:
            if self._stop_requested:
                return
            await self.task_runner.run_tasks_flow(
                task_id,
                start_task_id=start_task_id,
            )
        except asyncio.CancelledError:
            self._stop_requested = True
            self.task_runner.need_stop = True
            raise
        except Exception as exc:
            failed = True
            self.logs.append("ERROR", f"Runtime {self.config_id} failed: {exc}")
            self._set_state(RuntimeState.FAILED)
        finally:
            async with self._lifecycle_lock:
                current = asyncio.current_task()
                if self._run_task is current:
                    self._run_task = None
                if not failed:
                    self._set_state(RuntimeState.IDLE)
                terminal_button_status = self.button_status
            # The runner may exit before it ever creates a MaaFW runtime (for
            # example, Start followed immediately by Stop). Replay the terminal
            # state so the active UI cannot remain stuck on disabled STOP.
            self.events.start_button_status.emit(terminal_button_status)

    async def stop(self, *, manual: bool = True) -> bool:
        """Request an idempotent stop without blocking startup initialization."""
        async with self._lifecycle_lock:
            if self._state == RuntimeState.STOPPING and self._stop_requested:
                return True
            task = self._run_task
            has_runtime = self.is_running
            if task is None and not has_runtime:
                if self._state != RuntimeState.FAILED:
                    self._set_state(RuntimeState.IDLE)
                return True
            was_starting = self._state == RuntimeState.STARTING
            self._stop_requested = True
            self.task_runner.need_stop = True
            if manual:
                self.task_runner._manual_stop = True
            self._set_state(RuntimeState.STOPPING)

        # run_tasks_flow owns cleanup while STARTING. Entering MaaFW cleanup in
        # parallel with resource/controller initialization can deadlock native locks.
        if was_starting:
            self.events.start_button_status.emit(
                {"text": "STOP", "status": "disabled"}
            )
            return True

        await self.task_runner.stop_task(manual=manual)
        if task is None or task.done():
            async with self._lifecycle_lock:
                if self._run_task is None or self._run_task.done():
                    self._set_state(RuntimeState.IDLE)
        return True

    def shutdown_runtime_sync(self) -> None:
        """Synchronously clean the runtime owned by this configuration."""
        shared_maafw = getattr(self.monitor_task, "maafw", None) is getattr(
            self.task_runner, "maafw", None
        )
        try:
            self.task_runner.shutdown_runtime_sync()
        finally:
            if not shared_maafw:
                self.monitor_task.shutdown_runtime_sync()

    @property
    def is_running(self) -> bool:
        if self._state in (
            RuntimeState.STARTING,
            RuntimeState.RUNNING,
            RuntimeState.STOPPING,
        ):
            return True
        if self._run_task is not None and not self._run_task.done():
            return True
        try:
            return bool(
                self.task_runner.is_running
                or self.task_runner.maafw.has_active_runtime()
            )
        except Exception:
            return bool(getattr(self.task_runner, "is_running", False))

    @Slot(dict)
    def _on_task_flow_finished(self, _payload: dict) -> None:
        self.monitor.clear_roi()

    @Slot(dict)
    def _on_button_status_changed(self, payload: dict) -> None:
        if not isinstance(payload, dict):
            return
        text = str(payload.get("text", "")).upper()
        enabled = payload.get("status") != "disabled"
        if text == "STOP" and enabled and self._state == RuntimeState.STARTING:
            self._set_state(RuntimeState.RUNNING)
