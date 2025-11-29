from __future__ import annotations

from typing import Callable

from PySide6.QtCore import QEasingCurve, QObject, QPropertyAnimation, QVariantAnimation
from PySide6.QtWidgets import QGraphicsOpacityEffect, QSplitter, QWidget


class DescriptionTransitionAnimator(QObject):
    """控制公告区域展开/收起的大小 + 透明度过渡动画。"""

    def __init__(
        self,
        splitter: QSplitter,
        target_widget: QWidget,
        duration: int = 220,
        expanded_ratio: float = 0.4,
        min_height: int = 90,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self.splitter = splitter
        self.target_widget = target_widget
        self.duration = duration
        self.expanded_ratio = expanded_ratio
        self.min_height = min_height

        self._opacity_effect = QGraphicsOpacityEffect(self.target_widget)
        self.target_widget.setGraphicsEffect(self._opacity_effect)
        self._opacity_effect.setOpacity(1.0)

        self._opacity_animation = QPropertyAnimation(self._opacity_effect, b"opacity", self)
        self._opacity_animation.setDuration(self.duration)
        self._opacity_animation.setEasingCurve(QEasingCurve.Type.OutCubic)

        self._size_animation: QVariantAnimation | None = None
        self._is_expanded = self.target_widget.isVisible()
        self._animation_total = max(self.splitter.height(), 1)

    def expand(self):
        if self._is_expanded and not self._is_animating():
            return
        self._is_expanded = True
        self.target_widget.show()
        self._animation_total = self._measure_total_height()
        target_size = self._calculate_target_height(self._animation_total)
        self._play_size_animation(0, target_size, self._on_expand_finished)
        self._play_opacity_animation(0.0, 1.0)

    def collapse(self):
        if not self._is_expanded and not self._is_animating():
            return
        self._is_expanded = False
        start_size = self._current_description_size()
        self._animation_total = self._measure_total_height()
        self._play_size_animation(start_size, 0, self._on_collapse_finished)
        self._play_opacity_animation(1.0, 0.0)

    def toggle(self, visible: bool | None = None):
        if visible is None:
            visible = not self._is_expanded
        if visible:
            self.expand()
        else:
            self.collapse()

    def is_expanded(self) -> bool:
        return self._is_expanded

    def set_visible_immediate(self, visible: bool):
        self._is_expanded = visible
        self._animation_total = self._measure_total_height()
        if visible:
            self.target_widget.show()
            size = self._calculate_target_height(self._animation_total)
            self.splitter.setSizes([max(self._animation_total - size, 0), size])
        else:
            self.target_widget.hide()
            self.splitter.setSizes([self._animation_total, 0])
        self._opacity_effect.setOpacity(1.0)

    def _is_animating(self) -> bool:
        return bool(
            self._size_animation and self._size_animation.state() == QVariantAnimation.State.Running
        ) or self._opacity_animation.state() == QPropertyAnimation.State.Running

    def _play_size_animation(self, start: int, end: int, finished: Callable[[], None]):
        if self._size_animation:
            self._size_animation.stop()
        animation = QVariantAnimation(self)
        animation.setDuration(self.duration)
        animation.setStartValue(start)
        animation.setEndValue(end)
        animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        animation.valueChanged.connect(self._apply_splitter_sizes)
        animation.finished.connect(finished)
        animation.start()
        self._size_animation = animation

    def _apply_splitter_sizes(self, value):
        desc_height = max(int(value), 0)
        other_height = max(self._animation_total - desc_height, 0)
        self.splitter.setSizes([other_height, desc_height])

    def _play_opacity_animation(self, start: float, end: float):
        if self._opacity_animation.state() == QPropertyAnimation.State.Running:
            self._opacity_animation.stop()
        self._opacity_animation.setStartValue(start)
        self._opacity_animation.setEndValue(end)
        self._opacity_animation.start()

    def _on_expand_finished(self):
        if self._size_animation:
            final = int(self._size_animation.endValue())
            self._apply_splitter_sizes(final)
        self._opacity_effect.setOpacity(1.0)

    def _on_collapse_finished(self):
        self.target_widget.hide()
        self.splitter.setSizes([self._animation_total, 0])
        self._opacity_effect.setOpacity(1.0)

    def _calculate_target_height(self, total_height: int) -> int:
        hint_height = self.target_widget.sizeHint().height()
        ratio_height = int(total_height * self.expanded_ratio)
        target = max(self.min_height, ratio_height)
        return min(target, total_height)

    def _measure_total_height(self) -> int:
        height = max(self.splitter.height(), 1)
        sizes = self.splitter.sizes()
        if height <= 0 and sizes:
            height = sum(sizes)
        return max(height, 1)

    def _current_description_size(self) -> int:
        sizes = self.splitter.sizes()
        return sizes[1] if len(sizes) > 1 else 0

