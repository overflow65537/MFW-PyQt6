from __future__ import annotations

from typing import TYPE_CHECKING

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
