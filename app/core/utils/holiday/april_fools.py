from __future__ import annotations

from datetime import datetime
from random import Random
from typing import Callable

from app.core.utils.holiday.base import HolidayEasterEgg


class AprilFoolsEasterEgg(HolidayEasterEgg):
    """在 4 月 1 日启动时随机发出一组愚人节彩蛋日志。"""

    _GROUPS: tuple[tuple[str, ...], ...] = (
        (
            " Checking anti-addiction system...",
            ' April Fools detected. System verdict: "Limited-time April Fools addiction mode".',
            ' Task execution failed! Reason: You are granted "slacking rights" today. Please grab a coffee manually.',
            " Just kidding, back to serious work...",
        ),
        (
            " Today's task progress: ▓▓▓▓▓▓▓▓▓▓ 100%",
            " Verifying... Verification failed!",
            " Server fluctuation detected (actually April Fools fluctuation), progress rolled back to 0%.",
            " Re-executing...",
        ),
        (
            ' [System Notice] Since today is April Fools, all players can claim the limited title "Ultimate Sucker" upon login.',
            " Title claimed automatically. Please restart the game to view it.",
        ),
        (
            " Daily task completion: ■■□□□ 40%",
            " Injecting April Fools special patch...",
            " Output: sudo rm -rf",
            " Got scared? Back to normal task execution...",
        ),
        (
            ' April Fools detected, enabling "Anti-Boss Mode" automatically.',
            ' Taskbar title changed to: "2026 Q2 Quarterly Report - Data Analysis.exe"',
            " Pretending to load Excel...",
        ),
        (
            " Today's task list: 1. Enter game; 2. Claim rewards; 3. Be kind to yourself.",
            " The first two are already done for you, please do the third one yourself.",
        ),
    )

    # 与 _GROUPS 一一对应，触发时要设置的假窗口标题；None 表示不改变标题
    _GROUP_FAKE_TITLES: tuple[str | None, ...] = (
        None,
        None,
        None,
        None,
        "2026 Q2 Quarterly Report - Data Analysis.exe",
        None,
    )

    def __init__(
        self,
        *,
        rng: Random | None = None,
        now_provider: Callable[[], datetime] | None = None,
    ) -> None:
        super().__init__()
        self._rng = rng or Random()
        self._now_provider = now_provider or datetime.now

    def should_emit_today(self) -> bool:
        #return True
        now = self._now_provider()
        return now.month == 4 and now.day == 1
