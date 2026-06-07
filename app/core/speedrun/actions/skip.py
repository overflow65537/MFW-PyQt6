from __future__ import annotations

from typing import Any

from app.core.speedrun.actions.base import SpeedrunAction, SpeedrunActionResult
from app.core.speedrun.context import SpeedrunContext


class SkipAction(SpeedrunAction):
    action_type = "skip"

    def execute(
        self, context: SpeedrunContext, config: dict[str, Any], condition_reason: str
    ) -> SpeedrunActionResult:
        return SpeedrunActionResult(should_run=False, reason=condition_reason)

