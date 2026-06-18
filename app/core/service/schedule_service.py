from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, time
import calendar
from pathlib import Path
from typing import Any, List, Optional

import jsonc
from PySide6.QtCore import QObject, Signal

from app.common.signal_bus import signalBus
from app.core.service.system_scheduler import get_system_scheduler_backend
from app.utils.logger import logger


SCHEDULE_SINGLE = "single"
SCHEDULE_DAILY = "daily"
SCHEDULE_WEEKLY = "weekly"
SCHEDULE_MONTHLY = "monthly"


def _parse_iso(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


@dataclass
class ScheduleEntry:
    entry_id: str
    config_id: str
    name: str
    schedule_type: str
    params: dict[str, Any]
    force_start: bool
    enabled: bool
    created_at: datetime
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "config_id": self.config_id,
            "name": self.name,
            "schedule_type": self.schedule_type,
            "params": self.params,
            "force_start": self.force_start,
            "enabled": self.enabled,
            "created_at": self.created_at.isoformat(),
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "next_run": self.next_run.isoformat() if self.next_run else None,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ScheduleEntry":
        return cls(
            entry_id=payload["entry_id"],
            config_id=payload.get("config_id", ""),
            name=payload.get("name", ""),
            schedule_type=payload.get("schedule_type", SCHEDULE_SINGLE),
            params=payload.get("params", {}),
            force_start=bool(payload.get("force_start", False)),
            enabled=bool(payload.get("enabled", True)),
            created_at=_parse_iso(payload.get("created_at")) or datetime.now(),
            last_run=_parse_iso(payload.get("last_run")),
            next_run=_parse_iso(payload.get("next_run")),
        )

    def compute_next_run(
        self, reference: Optional[datetime] = None
    ) -> Optional[datetime]:
        now = reference or datetime.now()
        now = now.replace(second=0, microsecond=0)

        if self.schedule_type == SCHEDULE_SINGLE:
            run_at = _parse_iso(self.params.get("run_at"))
            if run_at and run_at > now:
                return run_at
            return None

        if self.schedule_type == SCHEDULE_DAILY:
            start_at = _parse_iso(self.params.get("start_at")) or now
            interval = max(1, int(self.params.get("interval_days", 1)))
            hour, minute = self._time_from_params(start_at)
            candidate = datetime.combine(start_at.date(), time(hour, minute))
            while candidate <= now:
                candidate += timedelta(days=interval)
            return candidate

        if self.schedule_type == SCHEDULE_WEEKLY:
            start_at = _parse_iso(self.params.get("start_at")) or now
            interval = max(1, int(self.params.get("interval_weeks", 0) or 1))
            weekdays = sorted({int(w) % 7 for w in self.params.get("weekdays", [])})
            if not weekdays:
                weekdays = [start_at.weekday()]
            hour, minute = self._time_from_params(start_at)
            week_start = start_at.date() - timedelta(days=start_at.weekday())
            max_weeks = 520
            week_index = 0
            while week_index < max_weeks:
                if week_index % interval == 0:
                    for weekday in weekdays:
                        candidate_date = week_start + timedelta(
                            weeks=week_index, days=weekday
                        )
                        candidate = datetime.combine(candidate_date, time(hour, minute))
                        if candidate > now and candidate >= start_at:
                            return candidate
                week_index += 1
            return None

        if self.schedule_type == SCHEDULE_MONTHLY:
            start_at = _parse_iso(self.params.get("start_at")) or now
            hour, minute = self._time_from_params(start_at)
            month_value = int(self.params.get("month", 0))
            months = list(range(1, 13)) if month_value == 0 else [month_value]
            month_day = self.params.get("month_day")
            ordinal = self.params.get("ordinal")
            weekday = self.params.get("weekday")
            month_days = []
            if isinstance(month_day, int):
                month_days = [month_day]
            elif month_day is None:
                month_days = [start_at.day]
            return self._find_next_monthly_candidate(
                now,
                start_at,
                months,
                month_days,
                int(ordinal) if ordinal is not None else None,
                int(weekday) if weekday is not None else None,
                hour,
                minute,
            )

        return None

    def _monthly_candidate(
        self, year: int, month: int, day: int, hour: int, minute: int
    ) -> Optional[datetime]:
        try:
            return datetime(year=year, month=month, day=day, hour=hour, minute=minute)
        except ValueError:
            return None

    def _time_from_params(self, fallback: datetime) -> tuple[int, int]:
        hour = int(self.params.get("hour", fallback.hour))
        minute = int(self.params.get("minute", fallback.minute))
        return hour, minute

    def _find_next_monthly_candidate(
        self,
        now: datetime,
        start_at: datetime,
        months: list[int],
        month_days: list[int],
        ordinal: Optional[int],
        weekday: Optional[int],
        hour: int,
        minute: int,
    ) -> Optional[datetime]:
        base_date = max(now, start_at)
        month_index = base_date.month - 1
        year_base = base_date.year
        months_set = sorted(set(months))
        for offset in range(0, 36):
            current_month = ((month_index + offset) % 12) + 1
            current_year = year_base + (month_index + offset) // 12
            if current_month not in months_set:
                continue
            candidates: list[datetime] = []
            for day in month_days:
                candidate = self._monthly_candidate(
                    current_year, current_month, day, hour, minute
                )
                if candidate and candidate > now and candidate >= start_at:
                    candidates.append(candidate)
            if ordinal is not None and weekday is not None:
                candidate = self._nth_weekday(
                    current_year,
                    current_month,
                    ordinal,
                    weekday,
                    hour,
                    minute,
                )
                if candidate and candidate > now and candidate >= start_at:
                    candidates.append(candidate)
            if candidates:
                return min(candidates)
        return None

    def _nth_weekday(
        self,
        year: int,
        month: int,
        ordinal: int,
        weekday: int,
        hour: int,
        minute: int,
    ) -> Optional[datetime]:
        if ordinal < 0 or weekday < 0 or weekday > 6:
            return None
        if ordinal < 4:
            first_day = datetime(year, month, 1)
            first_weekday = first_day.weekday()
            day = 1 + ((weekday - first_weekday) % 7) + ordinal * 7
            if day > calendar.monthrange(year, month)[1]:
                return None
            return datetime(year, month, day, hour, minute)
        last_day = calendar.monthrange(year, month)[1]
        for delta in range(0, last_day):
            candidate_day = last_day - delta
            candidate = datetime(year, month, candidate_day, hour, minute)
            if candidate.weekday() == weekday:
                return candidate
        return None


class ScheduleService(QObject):
    schedules_changed = Signal(list)

    def __init__(self, storage_path: Path):
        super().__init__()
        self.storage_path = storage_path
        self._schedules: List[ScheduleEntry] = []
        self._system_scheduler = get_system_scheduler_backend()
        self._ensure_storage()
        self._load_schedules()
        if self._system_scheduler.is_supported:
            self._system_scheduler.sync_all(self._schedules)

    def _ensure_storage(self) -> None:
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.storage_path.exists():
            self.storage_path.write_text("[]", encoding="utf-8")

    def _load_schedules(self) -> None:
        try:
            with open(self.storage_path, "r", encoding="utf-8") as handle:
                payload = jsonc.load(handle)
        except Exception as exc:
            logger.warning("无法加载计划任务文件: %s", exc)
            return
        if not isinstance(payload, list):
            logger.warning(
                "计划任务文件结构异常: 期望列表, 得到 %s", type(payload).__name__
            )
            return
        entries: List[ScheduleEntry] = []
        for raw in payload:
            try:
                entry = ScheduleEntry.from_dict(raw)
                entry.next_run = entry.compute_next_run()
                if entry.schedule_type == SCHEDULE_SINGLE and entry.next_run is None:
                    entry.enabled = False
                entries.append(entry)
            except Exception as exc:
                logger.exception("反序列化计划任务失败: %s", exc)
        self._schedules = entries
        self._sort_schedules()
        self._persist()
        self._notify_schedules_changed()

    def _persist(self) -> None:
        try:
            with open(self.storage_path, "w", encoding="utf-8") as handle:
                jsonc.dump(
                    [entry.to_dict() for entry in self._schedules],
                    handle,
                    indent=4,
                    ensure_ascii=False,
                )
        except Exception as exc:
            logger.exception("计划任务保存失败: %s", exc)

    def _notify_schedules_changed(self) -> None:
        self.schedules_changed.emit(self.get_schedules())

    def get_schedules(self) -> List[ScheduleEntry]:
        return list(self._schedules)

    def find_schedule(self, entry_id: str) -> Optional[ScheduleEntry]:
        for entry in self._schedules:
            if entry.entry_id == entry_id:
                return entry
        return None

    def format_entry_type(self, entry: ScheduleEntry) -> str:
        labels = {
            SCHEDULE_SINGLE: self.tr("Single"),
            SCHEDULE_DAILY: self.tr("Daily"),
            SCHEDULE_WEEKLY: self.tr("Weekly"),
            SCHEDULE_MONTHLY: self.tr("Monthly"),
        }
        return labels.get(entry.schedule_type, self.tr("Custom"))

    def format_entry_pattern(self, entry: ScheduleEntry) -> str:
        params = entry.params
        time_text = self._entry_time_text(entry)

        if entry.schedule_type == SCHEDULE_SINGLE:
            run_at = _parse_iso(params.get("run_at"))
            datetime_text = (
                run_at.strftime("%Y-%m-%d %H:%M")
                if run_at
                else entry.created_at.strftime("%Y-%m-%d %H:%M")
            )
            return self.tr("Once at {datetime}").format(datetime=datetime_text)

        if entry.schedule_type == SCHEDULE_DAILY:
            interval = max(1, int(params.get("interval_days", 1)))
            if interval == 1:
                return self.tr("Every day at {time}").format(time=time_text)
            return self.tr("Every {n} days at {time}").format(
                n=interval, time=time_text
            )

        if entry.schedule_type == SCHEDULE_WEEKLY:
            interval = max(1, int(params.get("interval_weeks", 1) or 1))
            weekdays = sorted({int(value) % 7 for value in params.get("weekdays", [])})
            weekday_text = ", ".join(self._weekday_label(value) for value in weekdays)
            if interval == 1:
                return self.tr("Every week on {weekdays} at {time}").format(
                    weekdays=weekday_text, time=time_text
                )
            return self.tr("Every {n} weeks on {weekdays} at {time}").format(
                n=interval, weekdays=weekday_text, time=time_text
            )

        if entry.schedule_type == SCHEDULE_MONTHLY:
            month_value = int(params.get("month", 0))
            month_text = self._month_label(month_value)
            ordinal = params.get("ordinal")
            weekday = params.get("weekday")
            if ordinal is not None and weekday is not None:
                return self.tr(
                    "Every {month} on the {ordinal} {weekday} at {time}"
                ).format(
                    month=month_text,
                    ordinal=self._ordinal_label(int(ordinal)),
                    weekday=self._weekday_label(int(weekday)),
                    time=time_text,
                )
            day = int(params.get("month_day", 1))
            return self.tr("Every {month} on day {day} at {time}").format(
                month=month_text, day=day, time=time_text
            )

        return self.tr("Custom")

    def _entry_time_text(self, entry: ScheduleEntry) -> str:
        params = entry.params
        hour = int(params.get("hour", 0))
        minute = int(params.get("minute", 0))
        return f"{hour:02d}:{minute:02d}"

    def _weekday_label(self, weekday: int) -> str:
        labels = (
            self.tr("Monday"),
            self.tr("Tuesday"),
            self.tr("Wednesday"),
            self.tr("Thursday"),
            self.tr("Friday"),
            self.tr("Saturday"),
            self.tr("Sunday"),
        )
        return labels[int(weekday) % 7]

    def _month_label(self, month: int) -> str:
        if month <= 0:
            return self.tr("Every month")
        labels = (
            self.tr("January"),
            self.tr("February"),
            self.tr("March"),
            self.tr("April"),
            self.tr("May"),
            self.tr("June"),
            self.tr("July"),
            self.tr("August"),
            self.tr("September"),
            self.tr("October"),
            self.tr("November"),
            self.tr("December"),
        )
        return labels[(int(month) - 1) % 12]

    def _ordinal_label(self, ordinal: int) -> str:
        if ordinal >= 4:
            return self.tr("Last")
        return (
            self.tr("First"),
            self.tr("Second"),
            self.tr("Third"),
            self.tr("Fourth"),
        )[ordinal]

    def add_schedule(self, entry: ScheduleEntry) -> bool:
        entry.next_run = entry.compute_next_run()
        if entry.next_run is None and entry.schedule_type != SCHEDULE_SINGLE:
            logger.warning(
                "无法为计划任务生成下一次执行时间: %s",
                self.format_entry_pattern(entry),
            )
            return False
        self._schedules.append(entry)
        self._sort_schedules()
        self._persist()
        self._notify_schedules_changed()
        if self._system_scheduler.is_supported:
            if entry.enabled:
                self._system_scheduler.install(entry)
            else:
                self._system_scheduler.remove(entry.entry_id)
        self._log_info(
            self.tr("Schedule: {name} ({describe}) added").format(
                name=entry.name, describe=self.format_entry_pattern(entry)
            )
        )
        return True

    def remove_schedule(self, entry_id: str) -> bool:
        entry = self.find_schedule(entry_id)
        if not entry:
            return False
        self._schedules.remove(entry)
        self._sort_schedules()
        if self._system_scheduler.is_supported:
            self._system_scheduler.remove(entry_id)
        self._persist()
        self._notify_schedules_changed()
        self._log_info(
            self.tr("Schedule: {name} ({describe}) removed").format(
                name=entry.name, describe=self.format_entry_pattern(entry)
            )
        )
        return True

    def set_schedule_enabled(self, entry_id: str, enabled: bool) -> bool:
        entry = self.find_schedule(entry_id)
        if not entry:
            return False
        entry.enabled = enabled
        if enabled and not entry.next_run:
            entry.next_run = entry.compute_next_run()
        self._sort_schedules()
        self._persist()
        if self._system_scheduler.is_supported:
            if enabled:
                self._system_scheduler.install(entry)
            else:
                self._system_scheduler.set_enabled(entry_id, False)
        self._notify_schedules_changed()
        status = self.tr("enabled") if enabled else self.tr("disabled")
        self._log_info(
            self.tr("Schedule: {name} ({describe}) {status}").format(
                name=entry.name,
                describe=self.format_entry_pattern(entry),
                status=status,
            )
        )
        return True

    def _sort_schedules(self) -> None:
        self._schedules.sort(key=lambda entry: (entry.next_run is None, entry.next_run))

    def _log_info(self, message: str) -> None:
        logger.info(message)
        signalBus.info_bar_requested.emit("info", message)
