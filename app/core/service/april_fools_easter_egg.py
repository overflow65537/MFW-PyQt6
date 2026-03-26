from __future__ import annotations

import asyncio
from datetime import datetime
from random import Random
from typing import Callable, Sequence

from PySide6.QtCore import QObject


LogEmitter = Callable[[str, str], None]


class AprilFoolsEasterEgg(QObject):
    """在4月1日启动时随机发出一组愚人节彩蛋日志。"""

    _GROUPS: tuple[tuple[str, ...], ...] = (
        (
            " Checking anti-addiction system...",
            " April Fools detected. System verdict: \"Limited-time April Fools addiction mode\".",
            " Task execution failed! Reason: You are granted \"slacking rights\" today. Please grab a coffee manually.",
            " Just kidding, back to serious work...",
        ),
        (
            " Today's task progress: ▓▓▓▓▓▓▓▓▓▓ 100%",
            " Verifying... Verification failed!",
            " Server fluctuation detected (actually April Fools fluctuation), progress rolled back to 0%.",
            " Re-executing...",
        ),
        (
            " [System Notice] Since today is April Fools, all players can claim the limited title \"Ultimate Sucker\" upon login.",
            " Title claimed automatically. Please restart the game to view it.",
        ),
        (
            " Daily task completion: ■■□□□ 40%",
            " Injecting April Fools special patch...",
            " Output: sudo rm -rf",
            " Got scared? Back to normal task execution...",
        ),
        (
            " April Fools detected, enabling \"Anti-Boss Mode\" automatically.",
            " Taskbar title changed to: \"2025 Q2 Quarterly Report - Data Analysis.exe\"",
            " Pretending to load Excel...",
        ),
        (
            " Today's task list: 1. Enter game; 2. Claim rewards; 3. Be kind to yourself.",
            " The first two are already done for you, please do the third one yourself.",
        ),
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
        now = self._now_provider()
        return now.month == 4 and now.day == 1

    async def emit_random_group(self, emit_log: LogEmitter) -> bool:
        if not self.should_emit_today():
            return False

        chosen_group = self._rng.choice(self._GROUPS)
        await self._emit_group(chosen_group, emit_log)
        return True

    async def _emit_group(self, group: Sequence[str], emit_log: LogEmitter) -> None:
        if not group:
            return

        for line in group[:-1]:
            emit_log("INFO", self.tr(line))

        await asyncio.sleep(2)
        emit_log("INFO", self.tr(group[-1]))


async def emit_april_fools_startup_logs(emit_log: LogEmitter) -> bool:
    """在4月1日启动时随机发出一组愚人节彩蛋日志，返回是否发出过日志。"""
    return await AprilFoolsEasterEgg().emit_random_group(emit_log)
