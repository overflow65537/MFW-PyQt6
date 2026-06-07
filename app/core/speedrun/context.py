from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable

from app.core.item import TaskItem


@dataclass
class SpeedrunContext:
    task: TaskItem
    config: dict[str, Any]
    state: dict[str, Any]
    now: datetime
    update_task: Callable[[TaskItem], None]
    notify_system: Callable[[str], None] | None = None
    notify_external: Callable[[str, str], None] | None = None

