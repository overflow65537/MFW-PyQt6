from __future__ import annotations

from PySide6.QtWidgets import QWidget
from qfluentwidgets import ToolTipFilter, ToolTipPosition


def apply_fluent_tooltip(
    widget: QWidget,
    text: str | None = None,
    *,
    delay: int = 0,
    position: ToolTipPosition = ToolTipPosition.TOP,
) -> ToolTipFilter:
    """为控件启用 qfluentwidgets 风格的 tooltip，并避免重复安装过滤器。"""

    filter_obj = getattr(widget, "_mfw_fluent_tooltip_filter", None)
    if not isinstance(filter_obj, ToolTipFilter):
        filter_obj = ToolTipFilter(widget, delay, position)
        widget.installEventFilter(filter_obj)
        setattr(widget, "_mfw_fluent_tooltip_filter", filter_obj)

    widget.setToolTip(text or "")
    return filter_obj