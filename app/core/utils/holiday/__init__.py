"""holiday — 节日彩蛋模块

用法：
    from app.core.utils.holiday import emit_holiday_startup_logs
    await emit_holiday_startup_logs(emit_log, title_setter)

新增节日步骤：
    1. 在本目录创建新文件（如 new_years.py），继承 HolidayEasterEgg
    2. 在下方 _REGISTRY 列表中追加该类
"""

from __future__ import annotations

from app.core.utils.holiday.base import HolidayEasterEgg, LogEmitter, TitleSetter
from app.core.utils.holiday.april_fools import AprilFoolsEasterEgg

# 所有已注册的节日彩蛋，按顺序尝试，第一个 should_emit_today() 为 True 的会被触发
_REGISTRY: list[type[HolidayEasterEgg]] = [
    AprilFoolsEasterEgg,
]


async def emit_holiday_startup_logs(
    emit_log: LogEmitter,
    title_setter: TitleSetter | None = None,
) -> bool:
    """遍历已注册的节日彩蛋，触发当天适用的那个。

    Returns:
        True  — 有节日彩蛋被触发
        False — 今天不是任何节日
    """
    for cls in _REGISTRY:
        egg = cls()
        if await egg.emit_random_group(emit_log, title_setter):
            return True
    return False


__all__ = [
    "HolidayEasterEgg",
    "LogEmitter",
    "TitleSetter",
    "AprilFoolsEasterEgg",
    "emit_holiday_startup_logs",
]
