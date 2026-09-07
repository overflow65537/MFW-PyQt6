"""根据 PI input 字段创建普通或密码输入框。"""

from typing import Any, Mapping

from qfluentwidgets import LineEdit, PasswordLineEdit


def create_option_line_edit(input_item: Mapping[str, Any] | None = None) -> LineEdit:
    """password 为 true 时返回掩码输入框。"""
    if isinstance(input_item, Mapping) and input_item.get("password"):
        return PasswordLineEdit()
    return LineEdit()


def should_apply_input_default(input_item: Mapping[str, Any] | None) -> bool:
    """密码字段禁止使用 default。"""
    if not isinstance(input_item, Mapping):
        return True
    return not bool(input_item.get("password"))
