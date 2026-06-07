from __future__ import annotations

from typing import Any

from app.core.speedrun.conditions.base import (
    SpeedrunCondition,
    SpeedrunConditionResult,
)
from app.core.speedrun.context import SpeedrunContext
from app.core.speedrun.time_utils import (
    current_period_start,
    normalize_hour_value,
    parse_history,
)


class RunCountCondition(SpeedrunCondition):
    condition_type = "run_count"

    def evaluate(
        self, context: SpeedrunContext, config: dict[str, Any]
    ) -> SpeedrunConditionResult:
        period = str(config.get("period", "daily") or "daily").lower()
        if period not in {"daily", "weekly", "monthly"}:
            period = "daily"

        refresh_hour = normalize_hour_value(config.get("refresh_hour", 0))
        target_count = self._to_positive_int(config.get("count"), 1)
        weekdays = config.get("weekdays", [1])
        days = config.get("days", [1])
        period_start = current_period_start(
            period,
            context.now,
            refresh_hour,
            weekdays=weekdays if isinstance(weekdays, list) else [1],
            month_days=days if isinstance(days, list) else [1],
        )
        period_key = f"{period}:{period_start.isoformat()}"

        state = context.state
        dirty = False
        if state.get("period_key") != period_key:
            state["period_key"] = period_key
            state["period_start"] = period_start.isoformat()
            state["run_count"] = self._initial_run_count_from_legacy_state(
                state, period_start, target_count
            )
            dirty = True

        run_count = self._to_non_negative_int(state.get("run_count"), 0)
        state["run_count"] = run_count
        matched = run_count >= target_count
        if matched:
            reason = self._build_reason(period, target_count, refresh_hour)
        else:
            reason = ""
        return SpeedrunConditionResult(matched=matched, reason=reason, dirty=dirty)

    def _to_positive_int(self, value: Any, default: int) -> int:
        try:
            number = int(value)
        except (TypeError, ValueError):
            return default
        return max(1, number)

    def _to_non_negative_int(self, value: Any, default: int) -> int:
        try:
            number = int(value)
        except (TypeError, ValueError):
            return default
        return max(0, number)

    def _build_reason(self, period: str, count: int, refresh_hour: int) -> str:
        labels = {
            "daily": "本日",
            "weekly": "本周",
            "monthly": "本月",
        }
        return f"{labels.get(period, '本日')}第 {count} 次运行条件已命中，刷新时间线 {refresh_hour:02d}:00"

    def _initial_run_count_from_legacy_state(
        self, state: dict[str, Any], period_start, target_count: int
    ) -> int:
        history = parse_history(state.get("last_runtime", []))
        if not history or history[-1] < period_start:
            return 0

        remaining = state.get("remaining_count")
        if isinstance(remaining, int) and remaining >= 0:
            return max(0, target_count - remaining)

        return 1

