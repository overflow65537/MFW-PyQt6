from __future__ import annotations

from app.core.speedrun.actions.base import SpeedrunAction
from app.core.speedrun.actions.normal_run import NormalRunAction
from app.core.speedrun.actions.skip import SkipAction
from app.core.speedrun.conditions.always import AlwaysCondition
from app.core.speedrun.conditions.after_time import AfterTimeCondition
from app.core.speedrun.conditions.base import SpeedrunCondition
from app.core.speedrun.conditions.month_day import MonthDayCondition
from app.core.speedrun.conditions.run_count import RunCountCondition
from app.core.speedrun.conditions.weekday import WeekdayCondition


CONDITIONS: dict[str, SpeedrunCondition] = {
    condition.condition_type: condition
    for condition in (
        AlwaysCondition(),
        RunCountCondition(),
        WeekdayCondition(),
        MonthDayCondition(),
        AfterTimeCondition(),
    )
}

ACTIONS: dict[str, SpeedrunAction] = {
    action.action_type: action
    for action in (
        NormalRunAction(),
        SkipAction(),
    )
}

