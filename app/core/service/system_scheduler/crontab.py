from __future__ import annotations

import re
from datetime import datetime
from typing import Any

from app.core.service.schedule_service import (
    SCHEDULE_DAILY,
    SCHEDULE_MONTHLY,
    SCHEDULE_SINGLE,
    SCHEDULE_WEEKLY,
    ScheduleEntry,
    _parse_iso,
)
from app.core.service.system_scheduler.base import SystemSchedulerBackend
from app.core.service.system_scheduler.unix_common import (
    build_managed_lines,
    current_schedule_instance_id,
    read_user_crontab,
    render_crontab_blocks,
    split_crontab_blocks,
    write_user_crontab,
)
from app.utils.logger import logger


class CrontabSchedulerBackend(SystemSchedulerBackend):
    """通过用户 crontab 注册计划任务（Linux / macOS）。"""

    @property
    def is_supported(self) -> bool:
        return True

    def install(self, entry: "ScheduleEntry") -> bool:
        if not entry.enabled:
            return self.remove(entry.entry_id)
        try:
            lines = build_managed_lines(entry)
        except Exception as exc:
            logger.exception("生成 crontab 计划失败 [%s]: %s", entry.entry_id, exc)
            return False

        preserved, blocks = split_crontab_blocks(read_user_crontab())
        instance_id = current_schedule_instance_id()
        managed = blocks.setdefault(instance_id, {})
        managed[entry.entry_id] = lines
        if write_user_crontab(render_crontab_blocks(preserved, blocks)):
            logger.info("已注册 crontab 计划: %s", entry.entry_id)
            return True
        return False

    def remove(self, entry_id: str) -> bool:
        preserved, blocks = split_crontab_blocks(read_user_crontab())
        instance_id = current_schedule_instance_id()
        managed = blocks.get(instance_id, {})
        if entry_id not in managed:
            return True
        del managed[entry_id]
        if managed:
            blocks[instance_id] = managed
        else:
            blocks.pop(instance_id, None)
        return write_user_crontab(render_crontab_blocks(preserved, blocks))

    def set_enabled(self, entry_id: str, enabled: bool) -> bool:
        if enabled:
            return True
        return self.remove(entry_id)

    def sync_all(self, entries: list["ScheduleEntry"]) -> None:
        preserved, blocks = split_crontab_blocks(read_user_crontab())
        instance_id = current_schedule_instance_id()
        managed: dict[str, list[str]] = {}

        for entry in entries:
            if not entry.enabled:
                continue
            try:
                managed[entry.entry_id] = build_managed_lines(entry)
            except Exception as exc:
                logger.exception("同步 crontab 计划失败 [%s]: %s", entry.entry_id, exc)

        if managed:
            blocks[instance_id] = managed
        else:
            blocks.pop(instance_id, None)

        if not write_user_crontab(render_crontab_blocks(preserved, blocks)):
            logger.warning("同步 crontab 计划到系统失败")

    def list_all_entries(self) -> list["ScheduleEntry"]:
        preserved, blocks = split_crontab_blocks(read_user_crontab())
        instance_id = current_schedule_instance_id()
        managed = blocks.get(instance_id, {})
        if not managed:
            return []
        entries: list[ScheduleEntry] = []
        for entry_id, lines in managed.items():
            entry = self._parse_crontab_entry(entry_id, lines)
            if entry is not None:
                entries.append(entry)
        return entries

    def _parse_crontab_entry(self, entry_id: str, lines: list[str]) -> ScheduleEntry | None:
        from app.core.service.schedule_service import ScheduleEntry

        if not lines:
            return None
        first = lines[0]
        parts = first.split(None, 5)
        if len(parts) < 6:
            return None
        minute_f, hour_f, day_f, month_f, weekday_f, cmd = parts

        run_elevated = cmd.startswith("sudo ")
        if run_elevated:
            cmd = cmd[len("sudo "):]

        config_id = ""
        force_start = False
        if "--config-id=" in cmd:
            match = re.search(r"--config-id=(\S+)", cmd)
            if match:
                config_id = match.group(1)
        force_start = "--force-restart" in cmd

        hour = int(hour_f)
        minute = int(minute_f)

        schedule_type: str = SCHEDULE_SINGLE
        params: dict[str, Any] = {}

        if day_f != "*" and month_f != "*" and weekday_f == "*":
            schedule_type = SCHEDULE_SINGLE
            now = datetime.now()
            try:
                run_at = now.replace(hour=hour, minute=minute, day=int(day_f), month=int(month_f))
                params["run_at"] = run_at.isoformat()
            except (ValueError, OverflowError):
                params["run_at"] = f"{now.year}-{int(month_f):02d}-{int(day_f):02d}T{hour:02d}:{minute:02d}:00"
        elif day_f == "*" and month_f == "*" and weekday_f == "*":
            schedule_type = SCHEDULE_DAILY
            params["start_at"] = datetime.now().replace(hour=hour, minute=minute, second=0, microsecond=0).isoformat()
            params["hour"] = hour
            params["minute"] = minute
            params["interval_days"] = 1
        elif day_f == "*" and month_f == "*" and weekday_f != "*":
            schedule_type = SCHEDULE_WEEKLY
            params["start_at"] = datetime.now().replace(hour=hour, minute=minute, second=0, microsecond=0).isoformat()
            params["hour"] = hour
            params["minute"] = minute
            params["interval_weeks"] = 1
            weekdays = []
            cron_days = [int(x) for x in weekday_f.split(",")]
            for cd in cron_days:
                py_dow = (cd - 1) % 7
                weekdays.append(py_dow)
            params["weekdays"] = weekdays
        elif day_f != "*" and month_f == "*" and weekday_f == "*":
            schedule_type = SCHEDULE_MONTHLY
            params["start_at"] = datetime.now().replace(hour=hour, minute=minute, second=0, microsecond=0).isoformat()
            params["hour"] = hour
            params["minute"] = minute
            if day_f.startswith("*/"):
                params["month_day"] = 1
            elif "-" in day_f:
                params["ordinal"] = 0
                params["weekday"] = 0
                ranges = ["1-7", "8-14", "15-21", "22-28", "25-31"]
                for idx, r in enumerate(ranges):
                    if day_f == r:
                        params["ordinal"] = idx
                        break
                if weekday_f != "*":
                    params["weekday"] = (int(weekday_f) - 1) % 7
                params["month"] = 0
            else:
                params["month_day"] = int(day_f)
                params["month"] = 0
        elif day_f != "*" and month_f != "*" and weekday_f == "*":
            schedule_type = SCHEDULE_MONTHLY
            params["start_at"] = datetime.now().replace(hour=hour, minute=minute, second=0, microsecond=0).isoformat()
            params["hour"] = hour
            params["minute"] = minute
            params["month_day"] = int(day_f)
            params["month"] = int(month_f)

        return ScheduleEntry(
            entry_id=entry_id,
            config_id=config_id,
            name=config_id or entry_id,
            schedule_type=schedule_type,
            params=params,
            force_start=force_start,
            run_elevated=run_elevated,
            enabled=True,
            created_at=datetime.now(),
        )
