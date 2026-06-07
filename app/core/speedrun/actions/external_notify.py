from __future__ import annotations

from typing import Any

from app.core.speedrun.actions.base import SpeedrunAction, SpeedrunActionResult
from app.core.speedrun.context import SpeedrunContext


class ExternalNotifyAction(SpeedrunAction):
    action_type = "external_notify"

    def execute(
        self, context: SpeedrunContext, config: dict[str, Any], condition_reason: str
    ) -> SpeedrunActionResult:
        if context.notify_external:
            context.notify_external("任务速通通知", _build_message(context, condition_reason))
        return SpeedrunActionResult(should_run=True, reason=condition_reason)


def _build_message(context: SpeedrunContext, condition_reason: str) -> str:
    reason = condition_reason or "速通条件已命中"
    return f"任务 {context.task.name}：{reason}"

