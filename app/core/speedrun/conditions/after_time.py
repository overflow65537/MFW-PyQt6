from __future__ import annotations

from typing import Any

from app.core.speedrun.conditions.base import (
    SpeedrunCondition,
    SpeedrunConditionResult,
)
from app.core.speedrun.context import SpeedrunContext
from app.core.speedrun.time_utils import normalize_hour_value


class AfterTimeCondition(SpeedrunCondition):
    condition_type = "after_time"

    def evaluate(
        self, context: SpeedrunContext, config: dict[str, Any]
    ) -> SpeedrunConditionResult:
        hour = normalize_hour_value(config.get("hour", 0))
        matched = context.now.hour >= hour
        reason = f"当前时间已超过 {hour:02d}:00" if matched else ""
        return SpeedrunConditionResult(matched=matched, reason=reason)

