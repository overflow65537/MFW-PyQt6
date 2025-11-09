from PySide6.QtCore import QEasingCurve, QObject, QPropertyAnimation
from PySide6.QtWidgets import QWidget, QGraphicsOpacityEffect
from typing import Callable, Optional


class OptionTransitionAnimator(QObject):
    """Option 面板切换时的过渡动画

    使用淡出->内容更新->淡入的方式，避免突兀闪动。
    """

    def __init__(self, target_widget: QWidget, duration: int = 220, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.target = target_widget
        self.duration = duration

        # 配置透明度效果
        self._effect = QGraphicsOpacityEffect(self.target)
        self.target.setGraphicsEffect(self._effect)
        self._effect.setOpacity(1.0)

        # 出场/入场动画
        self.fade_out = QPropertyAnimation(self._effect, b"opacity", self)
        self.fade_out.setDuration(self.duration)
        self.fade_out.setStartValue(1.0)
        self.fade_out.setEndValue(0.0)
        self.fade_out.setEasingCurve(QEasingCurve.Type.OutCubic)

        self.fade_in = QPropertyAnimation(self._effect, b"opacity", self)
        self.fade_in.setDuration(self.duration)
        self.fade_in.setStartValue(0.0)
        self.fade_in.setEndValue(1.0)
        self.fade_in.setEasingCurve(QEasingCurve.Type.OutCubic)

        self._pending_update: Optional[Callable[[], None]] = None

        # 串联动画：淡出完成后执行更新，再淡入
        self.fade_out.finished.connect(self._on_fade_out_finished)

    def _on_fade_out_finished(self):
        # 执行等待的更新动作（清空/填充等）
        if self._pending_update:
            try:
                self._pending_update()
            finally:
                self._pending_update = None
        # 开始淡入
        self.fade_in.start()

    def play(self, update_callable: Optional[Callable[[], None]] = None):
        """开始一次过渡。

        Args:
            update_callable: 在淡出完成后调用的函数（通常用于清空旧内容并填充新内容）。
        """
        self._pending_update = update_callable
        # 如果当前仍在动画中，先停止以避免叠加
        if self.fade_out.state() == QPropertyAnimation.State.Running:
            self.fade_out.stop()
        if self.fade_in.state() == QPropertyAnimation.State.Running:
            self.fade_in.stop()
        self.fade_out.start()
