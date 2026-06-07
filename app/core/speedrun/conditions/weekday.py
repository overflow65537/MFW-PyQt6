from __future__ import annotations

from typing import Any

from app.core.speedrun.conditions.base import (
    SpeedrunCondition,
    SpeedrunConditionResult,
)
from app.core.speedrun.context import SpeedrunContext
from app.core.speedrun.time_utils import collect_valid_ints


class WeekdayCondition(SpeedrunCondition):
    condition_type = "weekday"

    def evaluate(
        self, context: SpeedrunContext, config: dict[str, Any]
    ) -> SpeedrunConditionResult:
        weekdays = collect_valid_ints(config.get("weekdays", []), 1, 7)
        if not weekdays:
            return SpeedrunConditionResult(False)

        current = context.now.isoweekday()
        matched = current in weekdays
        reason = f"今天是周 {current}，已命中周几条件" if matched else ""
        return SpeedrunConditionResult(matched=matched, reason=reason)

