from __future__ import annotations

from typing import TYPE_CHECKING

from app.core.service.system_scheduler.base import SystemSchedulerBackend
from app.core.service.system_scheduler.unix_common import (
    build_managed_lines,
    read_user_crontab,
    render_crontab,
    split_crontab,
    write_user_crontab,
)
from app.utils.logger import logger

if TYPE_CHECKING:
    from app.core.service.schedule_service import ScheduleEntry


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

        preserved, managed = split_crontab(read_user_crontab())
        managed[entry.entry_id] = lines
        if write_user_crontab(render_crontab(preserved, managed)):
            logger.info("已注册 crontab 计划: %s", entry.entry_id)
            return True
        return False

    def remove(self, entry_id: str) -> bool:
        preserved, managed = split_crontab(read_user_crontab())
        if entry_id not in managed:
            return True
        del managed[entry_id]
        return write_user_crontab(render_crontab(preserved, managed))

    def set_enabled(self, entry_id: str, enabled: bool) -> bool:
        if enabled:
            return True
        return self.remove(entry_id)

    def sync_all(self, entries: list["ScheduleEntry"]) -> None:
        preserved, _ = split_crontab(read_user_crontab())
        managed: dict[str, list[str]] = {}

        for entry in entries:
            if not entry.enabled:
                continue
            try:
                managed[entry.entry_id] = build_managed_lines(entry)
            except Exception as exc:
                logger.exception("同步 crontab 计划失败 [%s]: %s", entry.entry_id, exc)

        if not write_user_crontab(render_crontab(preserved, managed)):
            logger.warning("同步 crontab 计划到系统失败")
