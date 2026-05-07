from __future__ import annotations

from PySide6.QtWidgets import QWidget
from qfluentwidgets import ToolTip, ToolTipFilter, ToolTipPosition
from qfluentwidgets.common.style_sheet import setCustomStyleSheet


class _BorderlessToolTip(ToolTip):
    """Use Fluent tooltip colors without visible border/shadow padding."""

    def __init__(self, text: str = "", parent: QWidget | None = None):
        super().__init__(text, parent)

        # Remove the outer transparent padding reserved for shadow drawing.
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.container.setGraphicsEffect(None)

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


class _BorderlessToolTipFilter(ToolTipFilter):
    def _createToolTip(self):
        return _BorderlessToolTip(self.parent().toolTip(), self.parent().window())


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