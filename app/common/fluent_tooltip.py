from __future__ import annotations

from typing import cast

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QSizePolicy, QWidget
from qfluentwidgets import ToolTip, ToolTipFilter, ToolTipPosition
from qfluentwidgets.common.auto_wrap import TextWrap
from qfluentwidgets.common.style_sheet import setCustomStyleSheet

# 过长 tooltip 在此宽度内自动换行，避免单行横跨整屏
_MAX_TOOLTIP_WIDTH_PX = 300
# TextWrap 字符宽度上限（中文等按 2 计），与上面像素宽度大致对应
_MAX_TOOLTIP_WRAP_CHARS = 32


def _prepare_tooltip_text(text: str) -> str:
    """将过长文本拆成多行（含无空格长串）。"""
    if not text:
        return ""
    wrapped, _ = TextWrap.wrap(text, _MAX_TOOLTIP_WRAP_CHARS, once=False)
    return wrapped


def _fit_tooltip_label(label: QLabel, text: str) -> None:
    """按换行后的内容设置标签尺寸，避免只显示前两行或被横向裁切。"""
    prepared = _prepare_tooltip_text(text)
    # 换行由 TextWrap 预先插入 \n；QLabel 无 setWordWrapMode，仅用于兜底折行
    label.setWordWrap(True)
    label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
    label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
    label.setText(prepared)

    fm = label.fontMetrics()
    lines = prepared.split("\n") if prepared else [""]
    content_width = max((fm.horizontalAdvance(line) for line in lines), default=0)
    use_width = min(_MAX_TOOLTIP_WIDTH_PX, max(content_width, 1))

    bounds = fm.boundingRect(
        0,
        0,
        use_width,
        10_000,
        int(Qt.AlignmentFlag.AlignLeft | Qt.TextFlag.TextWordWrap),
        prepared,
    )
    label.setFixedSize(use_width, max(bounds.height(), fm.height()))


class _BorderlessToolTip(ToolTip):
    """Use Fluent tooltip colors without visible border/shadow padding."""

    def __init__(self, text: str = "", parent: QWidget | None = None):
        super().__init__(text, parent)

        # Remove the outer transparent padding reserved for shadow drawing.
        if (layout := self.layout()):
            layout.setContentsMargins(0, 0, 0, 0)
        self.container.setGraphicsEffect(None)  # pyright: ignore[reportArgumentType]

        setCustomStyleSheet(
            self,
            """
            ToolTip {
                background: transparent;
            }

            ToolTip > #container {
                border: none;
                background-color: rgb(249, 249, 249);
                border-radius: 4px;
            }
            """,
            """
            ToolTip {
                background: transparent;
            }

            ToolTip > #container {
                border: none;
                background-color: rgb(43, 43, 43);
                border-radius: 4px;
            }
            """,
        )
        self._relayout_content(text)

    def setText(self, text: str) -> None:
        self._ToolTip__text = text or ""
        self._relayout_content(self._ToolTip__text)
        self.container.adjustSize()
        self.adjustSize()

    def _relayout_content(self, text: str) -> None:
        _fit_tooltip_label(self.label, text or "")


class _BorderlessToolTipFilter(ToolTipFilter):
    def _createToolTip(self):
        parent = cast(QWidget, self.parent())
        return _BorderlessToolTip(parent.toolTip(), parent.window())


def apply_fluent_tooltip(
    widget: QWidget,
    text: str | None = None,
    *,
    delay: int = 0,
    position: ToolTipPosition = ToolTipPosition.TOP,
) -> ToolTipFilter:
    """为控件启用 qfluentwidgets 风格的 tooltip，并避免重复安装过滤器。"""

    filter_obj = getattr(widget, "_mfw_fluent_tooltip_filter", None)
    if not isinstance(filter_obj, _BorderlessToolTipFilter):
        if isinstance(filter_obj, ToolTipFilter):
            filter_obj.hideToolTip()
            widget.removeEventFilter(filter_obj)

        filter_obj = _BorderlessToolTipFilter(widget, delay, position)
        widget.installEventFilter(filter_obj)
        setattr(widget, "_mfw_fluent_tooltip_filter", filter_obj)

    widget.setToolTip(text or "")
    return filter_obj
