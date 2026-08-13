from PySide6.QtCore import QObject, Signal

from app.core.facade._snapshot import snapshot
from app.core.service.schedule_service import ScheduleEntry, ScheduleService


class ScheduleFacade(QObject):
    """计划任务域的显式 API。"""

    schedules_changed = Signal(list)

    def __init__(self, service: ScheduleService) -> None:
        super().__init__()
        self._service = service
        self._service.schedules_changed.connect(self._forward_schedules_changed)

    def _forward_schedules_changed(self, entries: list[ScheduleEntry]) -> None:
        self.schedules_changed.emit(snapshot(entries))

    def get_schedules(self) -> list[ScheduleEntry]:
        return snapshot(self._service.get_schedules())

    def find_schedule(self, entry_id: str) -> ScheduleEntry | None:
        return snapshot(self._service.find_schedule(entry_id))

    def format_entry_type(self, entry: ScheduleEntry) -> str:
        return self._service.format_entry_type(snapshot(entry))

    def format_entry_pattern(self, entry: ScheduleEntry) -> str:
        return self._service.format_entry_pattern(snapshot(entry))

    def add_schedule(self, entry: ScheduleEntry) -> bool:
        return self._service.add_schedule(snapshot(entry))

    def remove_schedule(self, entry_id: str) -> bool:
        return self._service.remove_schedule(entry_id)

    def set_schedule_enabled(self, entry_id: str, enabled: bool) -> bool:
        return self._service.set_schedule_enabled(entry_id, enabled)
