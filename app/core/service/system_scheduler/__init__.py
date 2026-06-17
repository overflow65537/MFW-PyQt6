from __future__ import annotations

import sys

from app.core.service.system_scheduler.base import (
    NoopSystemSchedulerBackend,
    SystemSchedulerBackend,
)


def get_system_scheduler_backend() -> SystemSchedulerBackend:
    if sys.platform == "win32":
        from app.core.service.system_scheduler.windows import WindowsTaskSchedulerBackend

        return WindowsTaskSchedulerBackend()
    if sys.platform in {"linux", "linux2"} or sys.platform.startswith("linux"):
        from app.core.service.system_scheduler.crontab import CrontabSchedulerBackend

        return CrontabSchedulerBackend()
    if sys.platform == "darwin":
        from app.core.service.system_scheduler.crontab import CrontabSchedulerBackend

        return CrontabSchedulerBackend()
    return NoopSystemSchedulerBackend()


__all__ = [
    "NoopSystemSchedulerBackend",
    "SystemSchedulerBackend",
    "get_system_scheduler_backend",
]
