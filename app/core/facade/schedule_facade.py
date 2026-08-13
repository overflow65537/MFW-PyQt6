from app.core.facade._snapshot import snapshot
from app.core.service.schedule_service import (
    SCHEDULE_DAILY,
    SCHEDULE_MONTHLY,
    SCHEDULE_SINGLE,
    SCHEDULE_WEEKLY,
    ScheduleEntry,
    ScheduleService,
)


class ScheduleFacade:
    """计划任务域的显式 API。"""

    def __init__(self, service: ScheduleService) -> None:
        self._service = service

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


__all__ = [
    "SCHEDULE_DAILY",
    "SCHEDULE_MONTHLY",
    "SCHEDULE_SINGLE",
    "SCHEDULE_WEEKLY",
    "ScheduleEntry",
    "ScheduleFacade",
]
