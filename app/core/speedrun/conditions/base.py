from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from app.core.speedrun.context import SpeedrunContext


@dataclass
class SpeedrunConditionResult:
    matched: bool
    reason: str = ""
    dirty: bool = False


class SpeedrunCondition(ABC):
    condition_type: str = ""

    @abstractmethod
    def evaluate(
        self, context: SpeedrunContext, config: dict[str, Any]
    ) -> SpeedrunConditionResult:
        pass

