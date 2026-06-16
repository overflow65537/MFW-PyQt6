from __future__ import annotations

from typing import Any, Mapping


def _non_empty_str(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    return value.strip()


def _has_explicit_field(data: Mapping[str, Any], key: str) -> bool:
    if key not in data:
        return False
    return bool(_non_empty_str(data.get(key)))


def resolve_interface_display_name(
    translated: Mapping[str, Any] | None,
    original: Mapping[str, Any] | None,
    default_name: str = "ChainFlow Assistant",
) -> str:
    """解析 Dashboard / 设置页等头部展示名称（不含 title 与 version）。

    优先级：
    1. 原始配置有 label → label
    2. 无 label → name
    3. 都没有 → default_name
    """
    translated = translated or {}
    original = original or {}

    if _has_explicit_field(original, "label"):
        label = _non_empty_str(translated.get("label"))
        if label:
            return label

    name = _non_empty_str(translated.get("name"))
    if name:
        return name

    return default_name


def resolve_interface_display_title(
    translated: Mapping[str, Any] | None,
    original: Mapping[str, Any] | None,
    default_name: str = "ChainFlow Assistant",
) -> str:
    """根据 interface 元数据解析 UI 展示标题。

    优先级：
    1. 有 title → 仅显示 title
    2. 无 title 且原始配置有 label → label + version
    3. 无 label → name + version
    4. 都没有 → default_name
    """
    translated = translated or {}
    original = original or {}

    title = _non_empty_str(translated.get("title"))
    if title:
        return title

    version = _non_empty_str(translated.get("version"))
    version_suffix = f" {version}" if version else ""

    if _has_explicit_field(original, "label"):
        label = _non_empty_str(translated.get("label"))
        if label:
            return f"{label}{version_suffix}".strip()

    name = _non_empty_str(translated.get("name"))
    if name:
        return f"{name}{version_suffix}".strip()

    return default_name
