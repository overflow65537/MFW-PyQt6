from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from app.core.speedrun.context import SpeedrunContext


@dataclass
class SpeedrunActionResult:
    should_run: bool
    reason: str = ""


class SpeedrunAction(ABC):
    action_type: str = ""

    @abstractmethod
    def execute(
        self, context: SpeedrunContext, config: dict[str, Any], condition_reason: str
    ) -> SpeedrunActionResult:
        pass

