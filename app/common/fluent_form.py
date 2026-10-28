"""QFormLayout 行标签辅助。

qfluentwidgets 只为自己的 ``FluentLabelBase`` 子类（``BodyLabel``、``CaptionLabel``
等）在 QSS 里设置文字颜色。直接给 ``QFormLayout.addRow`` 传字符串时，Qt 会自动
生成一个裸 ``QLabel``，它不受主题 QSS 控制，走的是 Qt 默认（浅色）调色板，
深色主题下就变成几乎看不清的黑字。
"""

from __future__ import annotations

from qfluentwidgets import BodyLabel


def form_label(text: str) -> BodyLabel:
    """创建可用于 ``QFormLayout.addRow`` 的主题感知标签。"""
    return BodyLabel(text)
