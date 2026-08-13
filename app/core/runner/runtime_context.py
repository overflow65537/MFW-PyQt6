"""Per-configuration runtime state and runner lifecycle."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime
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


class RuntimeContext(QObject):
    """All non-persistent runtime objects belonging to one configuration."""

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
        )
        self.task_runner.setParent(self)
        self.monitor_task = MonitorTask(
            task_service=task_service,
            config_service=config_service,
            runner_events=RunnerEvents(self),
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

        self.events.log_output.connect(self.logs.append)
        self.events.log_clear_requested.connect(self.logs.clear)
        self.events.monitor_recognition_roi.connect(self.monitor.update_roi)
        self.events.task_flow_finished.connect(self._on_task_flow_finished)

    @property
    def is_running(self) -> bool:
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
