"""根据 PI input 字段创建单行、多行或密码输入框。"""

from typing import Any, Callable, Mapping

from qfluentwidgets import LineEdit, PasswordLineEdit, TextEdit


InputWidget = LineEdit | TextEdit


def create_option_line_edit(
    input_item: Mapping[str, Any] | None = None,
) -> InputWidget:
    """按字段配置创建输入框；密码字段优先于多行字段。"""

    if isinstance(input_item, Mapping) and input_item.get("password"):
        return PasswordLineEdit()
    if isinstance(input_item, Mapping) and input_item.get("multiline"):
        editor = TextEdit()
        try:
            height = int(input_item.get("height", 100))
        except (TypeError, ValueError):
            height = 100
        editor.setFixedHeight(max(60, height))
        return editor
    return LineEdit()


def read_option_input(widget: InputWidget) -> str:
    if isinstance(widget, TextEdit):
        return widget.toPlainText()
    return widget.text()


def write_option_input(widget: InputWidget, value: Any) -> None:
    text = "" if value is None else str(value)
    if isinstance(widget, TextEdit):
        widget.setPlainText(text)
    else:
        widget.setText(text)


def connect_option_input_changed(
    widget: InputWidget,
    callback: Callable[[str], None],
) -> None:
    if isinstance(widget, TextEdit):
        widget.textChanged.connect(lambda: callback(widget.toPlainText()))
    else:
        widget.textChanged.connect(callback)


def should_apply_input_default(input_item: Mapping[str, Any] | None) -> bool:
    """密码字段禁止使用 default。"""
    if not isinstance(input_item, Mapping):
        return True
    return not bool(input_item.get("password"))
