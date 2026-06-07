from __future__ import annotations

import calendar
from datetime import datetime, timedelta
from typing import Any


def normalize_hour_value(raw_value: Any) -> int:
    try:
        hour = int(raw_value)
    except (TypeError, ValueError):
        return 0
    return max(0, hour) % 24


def collect_valid_ints(raw_value: Any, min_value: int, max_value: int) -> list[int]:
    if not isinstance(raw_value, (list, tuple)):
        raw_value = [raw_value]

    normalized: list[int] = []
    for item in raw_value:
        try:
            number = int(item)
        except (TypeError, ValueError):
            continue
        if min_value <= number <= max_value:
            normalized.append(number)

    return normalized


def parse_history(raw_history: Any) -> list[datetime]:
    entries = raw_history or []
    if not isinstance(entries, list):
        entries = [entries]

    parsed: list[datetime] = []
    epoch = datetime(1970, 1, 1)
    for entry in entries:
        parsed_entry: datetime | None = None
        if isinstance(entry, (int, float)):
            try:
                parsed_entry = datetime.fromtimestamp(entry)
            except (OverflowError, OSError):
                parsed_entry = None
        elif isinstance(entry, str):
            try:
                parsed_entry = datetime.fromisoformat(entry)
            except ValueError:
                try:
                    parsed_entry = datetime.fromtimestamp(float(entry))
                except (TypeError, ValueError, OverflowError, OSError):
                    parsed_entry = None
        parsed.append(parsed_entry or epoch)

    parsed.sort()
    return parsed


def current_period_start(
    mode: str,
    now: datetime,
    refresh_hour: int,
    weekdays: list[int] | None = None,
    month_days: list[int] | None = None,
) -> datetime:
    refresh_hour = normalize_hour_value(refresh_hour)
    if mode == "weekly":
        anchor_weekday = _first_valid_int(weekdays, 1, 7, default=1)
        return _weekly_period_start(now, refresh_hour, anchor_weekday)

    if mode == "monthly":
        anchor_day = _first_valid_int(month_days, 1, 31, default=1)
        return _monthly_period_start(now, refresh_hour, anchor_day)

    base = now.replace(hour=refresh_hour, minute=0, second=0, microsecond=0)
    if now < base:
        base -= timedelta(days=1)
    return base


def _weekly_period_start(now: datetime, refresh_hour: int, weekday: int) -> datetime:
    candidate = now.replace(hour=refresh_hour, minute=0, second=0, microsecond=0)
    days_back = (candidate.isoweekday() - weekday) % 7
    period_start = candidate - timedelta(days=days_back)
    if period_start > now:
        period_start -= timedelta(days=7)
    return period_start


def _monthly_period_start(now: datetime, refresh_hour: int, day: int) -> datetime:
    year = now.year
    month = now.month
    days_in_month = calendar.monthrange(year, month)[1]
    safe_day = min(max(1, day), days_in_month)
    candidate = datetime(year, month, safe_day, refresh_hour, 0, 0)

    if candidate > now:
        month -= 1
        if month < 1:
            month = 12
            year -= 1
        days_in_month = calendar.monthrange(year, month)[1]
        safe_day = min(max(1, day), days_in_month)
        candidate = datetime(year, month, safe_day, refresh_hour, 0, 0)

    return candidate


def _first_valid_int(
    values: list[int] | None, min_value: int, max_value: int, default: int
) -> int:
    normalized = collect_valid_ints(values or [], min_value, max_value)
    return normalized[0] if normalized else default


def next_month_start(base_time: datetime) -> datetime:
    year = base_time.year + (1 if base_time.month == 12 else 0)
    month = 1 if base_time.month == 12 else base_time.month + 1
    return base_time.replace(year=year, month=month, day=1)


def days_in_month(year: int, month: int) -> int:
    return calendar.monthrange(year, month)[1]

