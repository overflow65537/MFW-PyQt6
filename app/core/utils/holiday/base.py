from __future__ import annotations

import asyncio
from abc import abstractmethod
from typing import Callable, Sequence

from PySide6.QtCore import QObject


LogEmitter = Callable[[str, str], None]
TitleSetter = Callable[[str], None]


class HolidayEasterEgg(QObject):
    """节日彩蛋基类，提供通用的日志输出与标题更改能力。

    子类需实现：
    - should_emit_today() -> bool   判断今天是否触发
    - _GROUPS                       消息组
    - _GROUP_FAKE_TITLES            与 _GROUPS 一一对应的假窗口标题（None 表示不改）
    """

    _GROUPS: tuple[tuple[str, ...], ...]
    _GROUP_FAKE_TITLES: tuple[str | None, ...]

    @abstractmethod
    def should_emit_today(self) -> bool:
        """返回今天是否应当触发该节日彩蛋。"""

    async def emit_random_group(
        self,
        emit_log: LogEmitter,
        title_setter: TitleSetter | None = None,
    ) -> bool:
        """随机选取一组消息并输出；返回是否实际输出过。"""
        if not self.should_emit_today():
            return False

        import random

        idx = random.randrange(len(self._GROUPS))
        await self._emit_group(
            self._GROUPS[idx],
            emit_log,
            self._GROUP_FAKE_TITLES[idx],
            title_setter,
        )
        return True

    async def _emit_group(
        self,
        group: Sequence[str],
        emit_log: LogEmitter,
        fake_title: str | None = None,
        title_setter: TitleSetter | None = None,
    ) -> None:
        """输出一组消息：先立即输出前 N-1 行，等待 2 秒后输出最后一行。
        若该组有假标题，则在输出前先更改窗口标题。
        """
        if not group:
            return

        if fake_title and title_setter:
            title_setter(self.tr(fake_title))

        for line in group[:-1]:
            emit_log("INFO", self.tr(line))

        await asyncio.sleep(2)
        emit_log("INFO", self.tr(group[-1]))
