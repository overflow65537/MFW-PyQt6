from __future__ import annotations

from typing import Any

from app.core.speedrun.conditions.base import (
    SpeedrunCondition,
    SpeedrunConditionResult,
)
from app.core.speedrun.context import SpeedrunContext


class AlwaysCondition(SpeedrunCondition):
    condition_type = "always"

    def evaluate(
        self, context: SpeedrunContext, config: dict[str, Any]
    ) -> SpeedrunConditionResult:
        return SpeedrunConditionResult(matched=True, reason="条件始终为真")

