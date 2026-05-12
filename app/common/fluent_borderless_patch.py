from __future__ import annotations

from typing import Any, Callable

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QWidget
from qfluentwidgets.common.style_sheet import setCustomStyleSheet
from qfluentwidgets.components.date_time.calendar_view import CalendarView
from qfluentwidgets.components.date_time.picker_base import PickerPanel
from qfluentwidgets.components.widgets.combo_box import ComboBox, EditableComboBox
from qfluentwidgets.components.widgets.flyout import Flyout, FlyoutViewBase
from qfluentwidgets.components.widgets.menu import RoundMenu
from qfluentwidgets.components.widgets.model_combo_box import (
    EditableModelComboBox,
    ModelComboBox,
)
from qfluentwidgets.components.widgets.tool_tip import ToolTip

_PATCH_INSTALLED = False

_TOOLTIP_LIGHT_QSS = """
ToolTip {
    background: transparent;
}

ToolTip > #container {
    border: none;
}
"""

_TOOLTIP_DARK_QSS = """
ToolTip {
    background: transparent;
}

ToolTip > #container {
    border: none;
}
"""

_MENU_LIGHT_QSS = """
RoundMenu {
    background: transparent;
    border: none;
}

MenuActionListWidget {
    border: none;
}
"""

_MENU_DARK_QSS = """
RoundMenu {
    background: transparent;
    border: none;
}

MenuActionListWidget {
    border: none;
}
"""

_COMBO_BOX_LIGHT_QSS = """
ComboBox, ModelComboBox {
    border: none;
}

ComboBox:pressed, ModelComboBox:pressed {
    border: none;
}

ComboBox:disabled, ModelComboBox:disabled {
    border: none;
}
"""

_COMBO_BOX_DARK_QSS = """
ComboBox, ModelComboBox {
    border: none;
}

ComboBox:pressed, ModelComboBox:pressed {
    border: none;
}

ComboBox:disabled, ModelComboBox:disabled {
    border: none;
}
"""

_EDITABLE_COMBO_BOX_LIGHT_QSS = """
QLineEdit {
    border: none;
}

QLineEdit:disabled {
    border: none;
}
"""

_EDITABLE_COMBO_BOX_DARK_QSS = """
QLineEdit {
    border: none;
}

QLineEdit:disabled {
    border: none;
}
"""

_PICKER_PANEL_LIGHT_QSS = """
PickerPanel {
    background: transparent;
}

PickerPanel > #view {
    border: none;
}
"""

_PICKER_PANEL_DARK_QSS = """
PickerPanel {
    background: transparent;
}

PickerPanel > #view {
    border: none;
}
"""

_CALENDAR_VIEW_LIGHT_QSS = """
CalendarView {
    background: transparent;
}

CalendarViewBase {
    border: none;
}
"""

_CALENDAR_VIEW_DARK_QSS = """
CalendarView {
    background: transparent;
}

CalendarViewBase {
    border: none;
}
"""


def _set_zero_margins(widget: QWidget, attr_name: str) -> None:
    layout = getattr(widget, attr_name, None)
    if layout is not None:
        layout.setContentsMargins(0, 0, 0, 0)


def _clear_graphics_effect(widget: QWidget, attr_name: str) -> None:
    target = getattr(widget, attr_name, None)
    if target is not None and hasattr(target, "setGraphicsEffect"):
        target.setGraphicsEffect(None)


def _disable_shadow(self: QWidget, *_args: Any, **_kwargs: Any) -> None:
    for attr_name in ("container", "view", "stackedWidget"):
        _clear_graphics_effect(self, attr_name)


def _style_tooltip(widget: ToolTip) -> None:
    if widget.layout() is not None:
        widget.layout().setContentsMargins(0, 0, 0, 0)
    _clear_graphics_effect(widget, "container")
    setCustomStyleSheet(widget, _TOOLTIP_LIGHT_QSS, _TOOLTIP_DARK_QSS)


def _style_round_menu(widget: RoundMenu) -> None:
    _set_zero_margins(widget, "hBoxLayout")
    _clear_graphics_effect(widget, "view")
    setCustomStyleSheet(widget, _MENU_LIGHT_QSS, _MENU_DARK_QSS)


def _style_combo_box(widget: QWidget) -> None:
    setCustomStyleSheet(widget, _COMBO_BOX_LIGHT_QSS, _COMBO_BOX_DARK_QSS)


def _style_editable_combo_box(widget: QWidget) -> None:
    setCustomStyleSheet(
        widget,
        _EDITABLE_COMBO_BOX_LIGHT_QSS,
        _EDITABLE_COMBO_BOX_DARK_QSS,
    )


def _style_flyout(widget: Flyout) -> None:
    _set_zero_margins(widget, "hBoxLayout")
    _clear_graphics_effect(widget, "view")


def _style_picker_panel(widget: PickerPanel) -> None:
    _set_zero_margins(widget, "hBoxLayout")
    _clear_graphics_effect(widget, "view")
    setCustomStyleSheet(widget, _PICKER_PANEL_LIGHT_QSS, _PICKER_PANEL_DARK_QSS)


def _style_calendar_view(widget: CalendarView) -> None:
    _set_zero_margins(widget, "hBoxLayout")
    _clear_graphics_effect(widget, "stackedWidget")
    setCustomStyleSheet(widget, _CALENDAR_VIEW_LIGHT_QSS, _CALENDAR_VIEW_DARK_QSS)


def _patch_init(cls: type[Any], styler: Callable[[Any], None]) -> None:
    original_init = cls.__init__

    def patched_init(self: Any, *args: Any, **kwargs: Any) -> None:
        original_init(self, *args, **kwargs)
        styler(self)

    cls.__init__ = patched_init


def _paint_borderless_flyout_view(self: FlyoutViewBase, _event: Any) -> None:
    painter = QPainter(self)
    painter.setRenderHints(QPainter.Antialiasing)
    painter.setBrush(self.backgroundColor())
    painter.setPen(Qt.NoPen)
    rect = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
    painter.drawRoundedRect(rect, 8, 8)


def install_borderless_fluent_styles() -> None:
    global _PATCH_INSTALLED
    if _PATCH_INSTALLED:
        return

    _patch_init(ToolTip, _style_tooltip)
    _patch_init(RoundMenu, _style_round_menu)
    _patch_init(ComboBox, _style_combo_box)
    _patch_init(ModelComboBox, _style_combo_box)
    _patch_init(EditableComboBox, _style_editable_combo_box)
    _patch_init(EditableModelComboBox, _style_editable_combo_box)
    _patch_init(Flyout, _style_flyout)
    _patch_init(PickerPanel, _style_picker_panel)
    _patch_init(CalendarView, _style_calendar_view)

    RoundMenu.setShadowEffect = _disable_shadow
    Flyout.setShadowEffect = _disable_shadow
    PickerPanel.setShadowEffect = _disable_shadow
    CalendarView.setShadowEffect = _disable_shadow
    FlyoutViewBase.paintEvent = _paint_borderless_flyout_view

    _PATCH_INSTALLED = True
