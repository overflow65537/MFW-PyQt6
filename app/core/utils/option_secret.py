"""PI v2.10.0 密码输入字段的加解密与脱敏。"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable, Mapping

from app.core.utils.option_branches_compat import (
    BRANCHES_FIELD,
    LEGACY_CHILDREN_FIELD,
)
from app.core.utils.option_checkbox import resolve_option_name

PASSWORD_MASK = "******"
_OPTION_CONTAINERS = frozenset(
    {
        "resource_options",
        "setting_options",
        "controller_options",
        "global_options",
    }
)


def is_password_field(input_item: Any) -> bool:
    """判断 inputs[] 项是否为密码字段。"""
    if not isinstance(input_item, Mapping):
        return False
    return bool(input_item.get("password"))


def password_field_names(option_def: Mapping[str, Any] | None) -> frozenset[str]:
    """返回 option 定义中标记为 password 的输入字段 name。"""
    if not isinstance(option_def, Mapping):
        return frozenset()
    names: set[str] = set()
    for item in option_def.get("inputs", []) or []:
        if not is_password_field(item):
            continue
        name = item.get("name")
        if name:
            names.add(str(name))
    return frozenset(names)


def _crypto_manager():
    from app.utils.crypto import crypto_manager

    return crypto_manager


def encrypt_secret_text(value: Any) -> Any:
    """将明文加密为可落盘的 utf-8 文本；空值与已加密文本保持原样。"""
    if value is None:
        return ""
    text = str(value)
    manager = _crypto_manager()
    if not text or manager.is_encrypted_text(text):
        return text
    return manager.encrypt_text(text)


def decrypt_secret_text(value: Any) -> Any:
    """将密文解密为明文；兼容历史明文配置。"""
    if value is None:
        return ""
    text = str(value)
    if not text:
        return text
    return _crypto_manager().decrypt_text(text, fallback_to_plaintext=True)


def mask_secret_text(value: Any) -> str:
    """日志 / 展示用掩码，空值保持为空。"""
    if value is None or str(value) == "":
        return ""
    return PASSWORD_MASK


def _transform_input_payload(
    payload: Any,
    field_names: frozenset[str],
    transform: Callable[[Any], Any],
) -> Any:
    if not field_names:
        return payload
    if isinstance(payload, dict):
        return {
            key: transform(item) if str(key) in field_names else item
            for key, item in payload.items()
        }
    if len(field_names) == 1:
        return transform(payload)
    return payload


def _transform_option_entry(
    option_key: str,
    option_value: Any,
    interface_options: Mapping[str, Any],
    transform: Callable[[Any], Any],
) -> Any:
    option_name = resolve_option_name(option_key)
    option_def = interface_options.get(option_name, {})
    if not isinstance(option_def, Mapping):
        option_def = {}
    field_names = password_field_names(option_def)
    option_type = str(option_def.get("type", "")).lower()

    if isinstance(option_value, dict):
        result = dict(option_value)
        if field_names and option_type == "input" and "value" in result:
            result["value"] = _transform_input_payload(
                result["value"], field_names, transform
            )
        elif field_names and option_type == "input" and "value" not in result:
            result = _transform_input_payload(result, field_names, transform)
        for branch_key in (BRANCHES_FIELD, LEGACY_CHILDREN_FIELD):
            branches = result.get(branch_key)
            if isinstance(branches, dict):
                result[branch_key] = transform_option_tree(
                    branches, interface_options, transform
                )
        return result

    if field_names and option_type == "input":
        return _transform_input_payload(option_value, field_names, transform)
    return option_value


def transform_option_tree(
    data: Any,
    interface_options: Mapping[str, Any] | None,
    transform: Callable[[Any], Any],
) -> Any:
    """递归处理选项树中的密码字段。"""
    options = interface_options if isinstance(interface_options, Mapping) else {}
    if isinstance(data, dict):
        result: dict[str, Any] = {}
        for key, value in data.items():
            if key in _OPTION_CONTAINERS and isinstance(value, dict):
                result[key] = transform_option_tree(value, options, transform)
            elif key == "pretask_entries" and isinstance(value, list):
                transformed_entries: list[Any] = []
                for entry in value:
                    if isinstance(entry, dict):
                        copied = dict(entry)
                        entry_options = copied.get("options")
                        if isinstance(entry_options, dict):
                            copied["options"] = transform_option_tree(
                                entry_options, options, transform
                            )
                        transformed_entries.append(copied)
                    else:
                        transformed_entries.append(entry)
                result[key] = transformed_entries
            else:
                result[key] = _transform_option_entry(key, value, options, transform)
        return result
    if isinstance(data, list):
        return [transform_option_tree(item, options, transform) for item in data]
    return data


def encrypt_option_tree(
    data: Any, interface_options: Mapping[str, Any] | None
) -> Any:
    """加密选项树中的密码字段，返回新对象。"""
    return transform_option_tree(data, interface_options, encrypt_secret_text)


def decrypt_option_tree(
    data: Any, interface_options: Mapping[str, Any] | None
) -> Any:
    """解密选项树中的密码字段，返回新对象。"""
    return transform_option_tree(data, interface_options, decrypt_secret_text)


def mask_option_tree(
    data: Any, interface_options: Mapping[str, Any] | None
) -> Any:
    """将选项树中的密码字段替换为掩码。"""
    return transform_option_tree(data, interface_options, mask_secret_text)


def decrypt_input_values(
    option_def: Mapping[str, Any] | None, input_values: Mapping[str, Any] | None
) -> dict[str, Any]:
    """解密 input 选项的字段值字典，供 pipeline / pretask 运行时使用。"""
    values = dict(input_values) if isinstance(input_values, Mapping) else {}
    for field_name in password_field_names(option_def):
        if field_name in values:
            values[field_name] = decrypt_secret_text(values[field_name])
    return values


def strip_password_fields_from_preset(
    option_def: Mapping[str, Any] | None, preset_value: Any
) -> Any:
    """从 preset 输入值中去掉密码字段，避免明文写入配置。"""
    field_names = password_field_names(option_def)
    if not field_names:
        return deepcopy(preset_value) if isinstance(preset_value, dict) else preset_value
    if isinstance(preset_value, dict):
        return {
            key: value
            for key, value in preset_value.items()
            if str(key) not in field_names
        }
    return preset_value
