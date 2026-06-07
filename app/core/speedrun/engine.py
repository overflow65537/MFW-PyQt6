from __future__ import annotations

from datetime import datetime
from typing import Any, Callable

from app.core.item import TaskItem
from app.core.speedrun.actions.base import SpeedrunActionResult
from app.core.speedrun.config import (
    build_condition_from_legacy,
    normalize_speedrun_config,
)
from app.core.speedrun.context import SpeedrunContext
from app.core.speedrun.registry import ACTIONS, CONDITIONS
from app.core.speedrun.time_utils import parse_history
from app.utils.logger import logger


def ensure_speedrun_state(task: TaskItem) -> dict[str, Any]:
    if not isinstance(task.task_option, dict):
        task.task_option = {}

    state = task.task_option.get("_speedrun_state")
    if not isinstance(state, dict):
        epoch = datetime(1970, 1, 1)
        state = {
            "last_runtime": [epoch.isoformat()],
            "remaining_count": -1,
            "run_count": 0,
            "period_key": "",
            "period_start": "",
        }
        task.task_option["_speedrun_state"] = state

    if "last_runtime" not in state or not isinstance(state["last_runtime"], list):
        state["last_runtime"] = [datetime(1970, 1, 1).isoformat()]
    if "remaining_count" not in state or not isinstance(state["remaining_count"], int):
        state["remaining_count"] = -1
    if "run_count" not in state or not isinstance(state["run_count"], int):
        state["run_count"] = 0
    return state


def evaluate_speedrun(
    task: TaskItem,
    speedrun: dict[str, Any],
    update_task: Callable[[TaskItem], None],
    notify_system: Callable[[str], None] | None = None,
    notify_external: Callable[[str, str], None] | None = None,
) -> SpeedrunActionResult:
    if not isinstance(speedrun, dict):
        return SpeedrunActionResult(should_run=True)
    speedrun = normalize_speedrun_config(speedrun)

    state = ensure_speedrun_state(task)
    context = SpeedrunContext(
        task=task,
        config=speedrun,
        state=state,
        now=datetime.now(),
        update_task=update_task,
        notify_system=notify_system,
        notify_external=notify_external,
    )

    condition_cfg = _normalize_condition_config(speedrun)
    action_cfg = _normalize_action_config(speedrun)

    condition_type = str(condition_cfg.get("type", "run_count") or "run_count")
    action_type = str(action_cfg.get("type", "skip") or "skip")
    condition = CONDITIONS.get(condition_type)
    action = ACTIONS.get(action_type)

    if condition is None:
        logger.warning("未知速通条件类型: %s", condition_type)
        return SpeedrunActionResult(should_run=True)
    if action is None:
        logger.warning("未知速通执行类型: %s", action_type)
        return SpeedrunActionResult(should_run=True)

    condition_result = condition.evaluate(context, condition_cfg)
    if condition_result.dirty:
        update_task(task)
    if not condition_result.matched:
        return SpeedrunActionResult(should_run=True)

    _run_side_effects(context, action_cfg, condition_result.reason)
    return action.execute(context, action_cfg, condition_result.reason)


def record_speedrun_runtime(
    task: TaskItem,
    speedrun: dict[str, Any],
    update_task: Callable[[TaskItem], None],
) -> None:
    if not isinstance(speedrun, dict):
        return
    speedrun = normalize_speedrun_config(speedrun)
    if _normalize_condition_config(speedrun).get("type") != "run_count":
        return

    state = ensure_speedrun_state(task)
    history = parse_history(state.get("last_runtime", []))
    now = datetime.now()
    history.append(now)
    state["last_runtime"] = [history[-1].isoformat()]
    state["run_count"] = max(0, int(state.get("run_count", 0) or 0)) + 1
    _sync_legacy_remaining_count(state, speedrun)
    update_task(task)


def _normalize_condition_config(speedrun: dict[str, Any]) -> dict[str, Any]:
    condition = speedrun.get("condition")
    if isinstance(condition, dict):
        normalized = dict(condition)
    else:
        normalized = _legacy_condition_config(speedrun)

    normalized.setdefault("type", "run_count")
    return normalized


def _normalize_action_config(speedrun: dict[str, Any]) -> dict[str, Any]:
    action = speedrun.get("action")
    if isinstance(action, dict):
        normalized = dict(action)
    else:
        normalized = {"type": "skip"}
    normalized.setdefault("type", "skip")
    return normalized


def _run_side_effects(
    context: SpeedrunContext, action_cfg: dict[str, Any], condition_reason: str
) -> None:
    message = _build_notification_message(context, condition_reason)
    if action_cfg.get("notify") and context.notify_system:
        context.notify_system(message)
    if action_cfg.get("external_notify") and context.notify_external:
        context.notify_external("任务条件通知", message)


def _build_notification_message(
    context: SpeedrunContext, condition_reason: str
) -> str:
    reason = condition_reason or "条件已命中"
    return f"任务 {context.task.name}：{reason}"


def _legacy_condition_config(speedrun: dict[str, Any]) -> dict[str, Any]:
    return build_condition_from_legacy(speedrun)


def _sync_legacy_remaining_count(state: dict[str, Any], speedrun: dict[str, Any]) -> None:
    condition = _normalize_condition_config(speedrun)
    if condition.get("type") != "run_count":
        return

    limit = _to_positive_int(condition.get("count"), 1)
    run_count = max(0, int(state.get("run_count", 0) or 0))
    state["remaining_count"] = max(0, limit - run_count)


def _to_positive_int(value: Any, default: int) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return default
    return max(1, number)

