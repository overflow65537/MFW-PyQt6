from __future__ import annotations

from copy import deepcopy
from typing import Any

from app.core.speedrun.time_utils import normalize_hour_value


DEFAULT_CONDITION: dict[str, Any] = {
    "type": "always",
    "period": "daily",
    "count": 1,
    "refresh_hour": 0,
    "weekdays": [1],
    "days": [1],
    "hour": 0,
}

DEFAULT_ACTION: dict[str, Any] = {
    "type": "normal_run",
    "notify": False,
    "external_notify": False,
}


def normalize_speedrun_config(
    config: dict[str, Any], force_legacy_condition: bool = False
) -> dict[str, Any]:
    normalized = deepcopy(config) if isinstance(config, dict) else {}

    condition = normalized.get("condition")
    if not isinstance(condition, dict):
        condition = {}
        normalized["condition"] = condition

    if (force_legacy_condition or _has_legacy_condition_config(normalized)) and (
        not condition or _condition_matches_default(condition)
    ):
        legacy_condition = build_condition_from_legacy(normalized)
        condition.update(legacy_condition)

    merged_condition = deepcopy(DEFAULT_CONDITION)
    merged_condition.update(condition)
    normalized["condition"] = merged_condition

    action = normalized.get("action")
    if not isinstance(action, dict):
        action = {}
    merged_action = deepcopy(DEFAULT_ACTION)
    merged_action.update(action)
    if merged_action.get("type") == "notify":
        merged_action["type"] = "normal_run"
        merged_action["notify"] = True
    elif merged_action.get("type") == "external_notify":
        merged_action["type"] = "normal_run"
        merged_action["external_notify"] = True
    normalized["action"] = merged_action

    _sync_legacy_fields(normalized)
    return normalized


def build_condition_from_legacy(config: dict[str, Any]) -> dict[str, Any]:
    mode = str(config.get("mode", "daily") or "daily").lower()
    if mode not in {"daily", "weekly", "monthly"}:
        mode = "daily"

    run_cfg = config.get("run", {}) if isinstance(config.get("run"), dict) else {}
    trigger = config.get("trigger", {}) if isinstance(config.get("trigger"), dict) else {}
    mode_trigger = trigger.get(mode, {}) if isinstance(trigger, dict) else {}
    if not isinstance(mode_trigger, dict):
        mode_trigger = {}

    weekly = trigger.get("weekly", {}) if isinstance(trigger, dict) else {}
    weekdays = weekly.get("weekday", [1]) if isinstance(weekly, dict) else [1]
    monthly = trigger.get("monthly", {}) if isinstance(trigger, dict) else {}
    days = monthly.get("day", [1]) if isinstance(monthly, dict) else [1]

    return {
        "type": "run_count",
        "period": mode,
        "count": _to_positive_int(run_cfg.get("count"), 1),
        "refresh_hour": normalize_hour_value(mode_trigger.get("hour_start", 0)),
        "weekdays": weekdays if isinstance(weekdays, list) and weekdays else [1],
        "days": days if isinstance(days, list) and days else [1],
        "hour": normalize_hour_value(mode_trigger.get("hour_start", 0)),
    }


def _condition_matches_default(condition: dict[str, Any]) -> bool:
    for key, value in DEFAULT_CONDITION.items():
        if condition.get(key, value) != value:
            return False
    return True


def _has_legacy_condition_config(config: dict[str, Any]) -> bool:
    if config.get("mode") not in (None, "", "daily"):
        return True

    run_cfg = config.get("run")
    if isinstance(run_cfg, dict):
        if run_cfg.get("count") not in (None, "", 1):
            return True
        if run_cfg.get("min_interval_hours") not in (None, "", 0, 0.0):
            return True

    trigger = config.get("trigger")
    if not isinstance(trigger, dict):
        return False
    default_trigger = {
        "daily": {"hour_start": 0},
        "weekly": {"weekday": [1], "hour_start": 0},
        "monthly": {"day": [1], "hour_start": 0},
    }
    return trigger != default_trigger


def _sync_legacy_fields(config: dict[str, Any]) -> None:
    condition = config.get("condition", {})
    if not isinstance(condition, dict):
        condition = DEFAULT_CONDITION

    period = str(condition.get("period", "daily") or "daily")
    count = _to_positive_int(condition.get("count"), 1)
    refresh_hour = normalize_hour_value(condition.get("refresh_hour", 0))
    weekdays = condition.get("weekdays", [1])
    days = condition.get("days", [1])

    config["mode"] = period
    run_cfg = config.setdefault("run", {})
    if isinstance(run_cfg, dict):
        run_cfg["count"] = count

    trigger = config.setdefault("trigger", {})
    if not isinstance(trigger, dict):
        trigger = {}
        config["trigger"] = trigger
    trigger.setdefault("daily", {})["hour_start"] = refresh_hour
    trigger.setdefault("weekly", {})["weekday"] = (
        weekdays if isinstance(weekdays, list) and weekdays else [1]
    )
    trigger.setdefault("weekly", {})["hour_start"] = refresh_hour
    trigger.setdefault("monthly", {})["day"] = (
        days if isinstance(days, list) and days else [1]
    )
    trigger.setdefault("monthly", {})["hour_start"] = refresh_hour


def _to_positive_int(value: Any, default: int) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return default
    return max(1, number)

