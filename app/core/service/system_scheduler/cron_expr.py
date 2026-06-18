from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from app.core.service.schedule_service import (
    SCHEDULE_DAILY,
    SCHEDULE_MONTHLY,
    SCHEDULE_SINGLE,
    SCHEDULE_WEEKLY,
    _parse_iso,
)
from app.utils.logger import logger

if TYPE_CHECKING:
    from app.core.service.schedule_service import ScheduleEntry

_ORDINAL_DAY_RANGES = ("1-7", "8-14", "15-21", "22-28", "25-31")


def python_weekday_to_cron(weekday: int) -> int:
    """Python weekday (Mon=0) -> crontab weekday (Sun=0, Mon=1)."""
    return (int(weekday) + 1) % 7


def _time_fields(params: dict, fallback: datetime) -> tuple[int, int]:
    hour = int(params.get("hour", fallback.hour))
    minute = int(params.get("minute", fallback.minute))
    return minute, hour


def build_cron_schedule_lines(entry: "ScheduleEntry") -> list[str]:
    """将计划任务转换为 crontab 调度字段行（不含命令部分）。"""
    params = entry.params
    schedule_type = entry.schedule_type

    if schedule_type == SCHEDULE_SINGLE:
        run_at = _parse_iso(params.get("run_at"))
        if run_at is None:
            raise ValueError("single schedule missing run_at")
        return [f"{run_at.minute} {run_at.hour} {run_at.day} {run_at.month} *"]

    start_at = _parse_iso(params.get("start_at")) or datetime.now()
    minute, hour = _time_fields(params, start_at)

    if schedule_type == SCHEDULE_DAILY:
        interval = max(1, int(params.get("interval_days", 1)))
        if interval > 1:
            logger.warning(
                "计划任务 [%s] 的每 %s 日间隔在 crontab 中按每月日期步进近似",
                entry.entry_id,
                interval,
            )
            return [f"{minute} {hour} */{interval} * *"]
        return [f"{minute} {hour} * * *"]

    if schedule_type == SCHEDULE_WEEKLY:
        interval = max(1, int(params.get("interval_weeks", 1) or 1))
        weekdays = sorted({python_weekday_to_cron(int(w)) for w in params.get("weekdays", [])})
        if not weekdays:
            weekdays = [python_weekday_to_cron(start_at.weekday())]
        if interval > 1:
            logger.warning(
                "计划任务 [%s] 的每 %s 周间隔在 crontab 中按每周近似",
                entry.entry_id,
                interval,
            )
        dow = ",".join(str(value) for value in weekdays)
        return [f"{minute} {hour} * * {dow}"]

    if schedule_type == SCHEDULE_MONTHLY:
        month_value = int(params.get("month", 0))
        month_field = "*" if month_value <= 0 else str(month_value)
        ordinal = params.get("ordinal")
        weekday = params.get("weekday")
        if ordinal is not None and weekday is not None:
            day_range = _ORDINAL_DAY_RANGES[min(max(int(ordinal), 0), 4)]
            cron_dow = python_weekday_to_cron(int(weekday))
            return [f"{minute} {hour} {day_range} {month_field} {cron_dow}"]
        day = int(params.get("month_day", start_at.day))
        return [f"{minute} {hour} {day} {month_field} *"]

    raise ValueError(f"unsupported schedule type: {schedule_type}")
