from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from app.core.speedrun.conditions.base import (
    SpeedrunCondition,
    SpeedrunConditionResult,
)
from app.core.speedrun.context import SpeedrunContext

DEFAULT_CRON_EXPRESSION = "0 9 * * *"


def normalize_cron_expression(raw_value: Any) -> str:
    expression = str(raw_value or "").strip()
    return expression or DEFAULT_CRON_EXPRESSION


def cron_matches(expression: str, now: datetime) -> bool:
    """判断当前时间是否处于 cron 表达式当日最近一次触发点之后。"""
    expression = normalize_cron_expression(expression)
    try:
        from croniter import croniter
    except ImportError:
        return False

    try:
        if not croniter.is_valid(expression):
            return False
    except Exception:
        return False

    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    iterator = croniter(expression, start_of_day - timedelta(seconds=1))
    last_fire_today: datetime | None = None
    while True:
        candidate = iterator.get_next(datetime)
        if candidate.date() != now.date():
            break
        if candidate <= now:
            last_fire_today = candidate
        else:
            break
    return last_fire_today is not None


class CronCondition(SpeedrunCondition):
    condition_type = "cron"

    def evaluate(
        self, context: SpeedrunContext, config: dict[str, Any]
    ) -> SpeedrunConditionResult:
        expression = normalize_cron_expression(config.get("expression"))
        matched = cron_matches(expression, context.now)
        reason = (
            f"Cron 表达式 [{expression}] 已命中，最近触发点已到达"
            if matched
            else ""
        )
        return SpeedrunConditionResult(matched=matched, reason=reason)
