from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.core.service.schedule_service import ScheduleEntry


class SystemSchedulerBackend(ABC):
    """将计划任务同步到操作系统调度器的抽象后端。"""

    @property
    @abstractmethod
    def is_supported(self) -> bool:
        """当前平台是否由该后端接管调度。"""

    @abstractmethod
    def install(self, entry: "ScheduleEntry") -> bool:
        """创建或更新一条系统计划任务。"""

    @abstractmethod
    def remove(self, entry_id: str) -> bool:
        """删除一条系统计划任务。"""

    @abstractmethod
    def set_enabled(self, entry_id: str, enabled: bool) -> bool:
        """启用或禁用一条系统计划任务。"""

    @abstractmethod
    def list_all_entries(self) -> list["ScheduleEntry"]:
        """从系统调度器读取所有本实例管理的计划任务。"""

    @abstractmethod
    def sync_all(self, entries: list["ScheduleEntry"]) -> None:
        """将本地计划列表与系统调度器对齐。"""


class NoopSystemSchedulerBackend(SystemSchedulerBackend):
    """尚未接入系统调度器的平台：不操作 OS 调度器。"""

    @property
    def is_supported(self) -> bool:
        return False

    def install(self, entry: "ScheduleEntry") -> bool:
        return True

    def remove(self, entry_id: str) -> bool:
        return True

    def set_enabled(self, entry_id: str, enabled: bool) -> bool:
        return True

    def sync_all(self, entries: list["ScheduleEntry"]) -> None:
        return

    def list_all_entries(self) -> list["ScheduleEntry"]:
        return []
