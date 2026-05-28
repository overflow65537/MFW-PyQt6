"""跑马灯文本标签：文本超出可视宽度时自动横向滚动。"""

import re

from PySide6.QtCore import QTimer
from PySide6.QtGui import QColor, QPainter, QPalette
from qfluentwidgets import BodyLabel


class OptionLabel(BodyLabel):
    """支持跑马灯滚动的文本标签。"""

    def __init__(self, text: str = "", parent=None):
        # 只传 parent，走 BodyLabel 的单参数 __init__；不可 super().__init__("", parent)，
        # 否则会命中 (text, parent) 重载并再次调用 self.__init__(parent) 导致递归。
        BodyLabel.__init__(self, parent)
        self._marquee_text: str = ""
        self._text_width: int = 0
        self._offset_px: float = 0.0
        self._direction: int = 1
        self._paused: bool = False
        self._text_color: QColor | None = None

        self._interval_ms: int = 30
        self._pause_ms: int = 1000
        self._speed_px_per_sec: float = 25.0
        self._step_px: float = self._speed_px_per_sec * (self._interval_ms / 1000.0)

        self._tick_timer = QTimer(self)
        self._tick_timer.timeout.connect(self._on_tick)

        self._pause_timer = QTimer(self)
        self._pause_timer.setSingleShot(True)
        self._pause_timer.timeout.connect(self._on_pause_finished)
        self._pause_next_direction: int | None = None

        if text:
            self.setText(text)

    def setStyleSheet(self, styleSheet: str) -> None:  # type: ignore[override]
        super().setStyleSheet(styleSheet)
        self._text_color = self._parse_color_from_stylesheet(styleSheet)
        self.update()

    @staticmethod
    def _parse_color_from_stylesheet(styleSheet: str) -> QColor | None:
        if not styleSheet:
            return None
        m = re.search(
            r"(?<![-\w])color\s*:\s*([^;]+)", styleSheet, flags=re.IGNORECASE
        )
        if not m:
            return None
        color_str = (m.group(1) or "").strip()
        if not color_str:
            return None
        c = QColor(color_str)
        return c if c.isValid() else None

    def setMarqueeConfig(
        self,
        *,
        speed_px_per_sec: float | None = None,
        interval_ms: int | None = None,
        pause_ms: int | None = None,
    ) -> None:
        """配置跑马灯滚动参数。"""
        if interval_ms is not None and interval_ms > 0:
            self._interval_ms = int(interval_ms)
        if pause_ms is not None and pause_ms >= 0:
            self._pause_ms = int(pause_ms)
        if speed_px_per_sec is not None and speed_px_per_sec >= 0:
            self._speed_px_per_sec = float(speed_px_per_sec)
        self._step_px = self._speed_px_per_sec * (self._interval_ms / 1000.0)
        self.refresh_scroll(reset_offset=False)

    def text(self) -> str:  # type: ignore[override]
        return self._marquee_text

    def setText(self, text: str) -> None:  # type: ignore[override]
        self._marquee_text = text or ""
        super().setText("")
        self._offset_px = 0.0
        self._direction = 1
        self._paused = False
        self._pause_next_direction = None
        self._pause_timer.stop()
        self._recalc_metrics()
        self._update_timer_state()
        if self._needs_scroll():
            self._start_pause(next_direction=1)
        self.update()

    def refresh_scroll(self, reset_offset: bool = True) -> None:
        """外部在 resize/布局变化后调用，用于重新计算是否需要滚动。"""
        if reset_offset:
            self._offset_px = 0.0
            self._direction = 1
            self._paused = False
            self._pause_next_direction = None
            self._pause_timer.stop()
        self._recalc_metrics()
        self._clamp_offset()
        self._update_timer_state()
        self.update()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self.refresh_scroll(reset_offset=False)

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self._update_timer_state()

    def hideEvent(self, event) -> None:
        super().hideEvent(event)
        self._tick_timer.stop()
        self._pause_timer.stop()

    def _recalc_metrics(self) -> None:
        fm = self.fontMetrics()
        self._text_width = (
            fm.horizontalAdvance(self._marquee_text) if self._marquee_text else 0
        )

    def _available_width(self) -> int:
        return max(0, self.contentsRect().width())

    def _max_offset(self) -> int:
        return max(0, self._text_width - self._available_width())

    def _needs_scroll(self) -> bool:
        return bool(self._marquee_text) and self._max_offset() > 0 and self._step_px > 0

    def _clamp_offset(self) -> None:
        max_off = float(self._max_offset())
        if self._offset_px < 0:
            self._offset_px = 0.0
        elif self._offset_px > max_off:
            self._offset_px = max_off

    def _update_timer_state(self) -> None:
        if not self.isVisible():
            self._tick_timer.stop()
            return
        if self._needs_scroll():
            if not self._tick_timer.isActive():
                self._tick_timer.start(self._interval_ms)
        else:
            self._tick_timer.stop()
            self._paused = False
            self._pause_timer.stop()
            self._offset_px = 0.0
            self._direction = 1

    def _start_pause(self, next_direction: int) -> None:
        if self._pause_timer.isActive():
            return
        self._paused = True
        self._pause_next_direction = next_direction
        self._pause_timer.start(self._pause_ms)

    def _on_pause_finished(self) -> None:
        if self._pause_next_direction is not None:
            self._direction = self._pause_next_direction
        self._pause_next_direction = None
        self._paused = False

    def _on_tick(self) -> None:
        if not self._needs_scroll():
            self._update_timer_state()
            return
        if self._paused:
            return

        max_off = float(self._max_offset())
        if max_off <= 0:
            self._offset_px = 0.0
            self._direction = 1
            self.update()
            return

        self._offset_px += self._direction * self._step_px

        if self._offset_px >= max_off:
            self._offset_px = max_off
            self._start_pause(next_direction=-1)
        elif self._offset_px <= 0.0:
            self._offset_px = 0.0
            self._start_pause(next_direction=1)

        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)

        rect = self.contentsRect()
        painter.setClipRect(rect)

        painter.setPen(
            self._text_color
            if self._text_color is not None
            else self.palette().color(QPalette.ColorRole.WindowText)
        )

        if not self._marquee_text:
            return

        fm = self.fontMetrics()
        baseline_y = rect.y() + (rect.height() + fm.ascent() - fm.descent()) // 2
        x = rect.x() - int(self._offset_px)
        painter.drawText(x, baseline_y, self._marquee_text)
