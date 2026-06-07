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


def current_period_start(mode: str, now: datetime, refresh_hour: int) -> datetime:
    refresh_hour = normalize_hour_value(refresh_hour)
    base = now.replace(hour=refresh_hour, minute=0, second=0, microsecond=0)
    if now < base:
        base -= timedelta(days=1)

    if mode == "weekly":
        return base - timedelta(days=base.isoweekday() - 1)

    if mode == "monthly":
        return base.replace(day=1)

    return base


def next_month_start(base_time: datetime) -> datetime:
    year = base_time.year + (1 if base_time.month == 12 else 0)
    month = 1 if base_time.month == 12 else base_time.month + 1
    return base_time.replace(year=year, month=month, day=1)


def days_in_month(year: int, month: int) -> int:
    return calendar.monthrange(year, month)[1]

