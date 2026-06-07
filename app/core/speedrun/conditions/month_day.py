from __future__ import annotations

from typing import Any

from app.core.speedrun.conditions.base import (
    SpeedrunCondition,
    SpeedrunConditionResult,
)
from app.core.speedrun.context import SpeedrunContext
from app.core.speedrun.time_utils import collect_valid_ints


class MonthDayCondition(SpeedrunCondition):
    condition_type = "month_day"

    def evaluate(
        self, context: SpeedrunContext, config: dict[str, Any]
    ) -> SpeedrunConditionResult:
        days = collect_valid_ints(config.get("days", []), 1, 31)
        if not days:
            return SpeedrunConditionResult(False)

        current = context.now.day
        matched = current in days
        reason = f"今天是 {current} 日，已命中日期条件" if matched else ""
        return SpeedrunConditionResult(matched=matched, reason=reason)

