from __future__ import annotations

from typing import Any


def is_pretask_entry_allowed(
    entry: dict[str, Any],
    current_controller: str,
    current_resource: str,
) -> bool:
    """按 pretask 条目的 controller/resource 白名单过滤。"""
    for key, current in (("controller", current_controller), ("resource", current_resource)):
        value = entry.get(key)
        if value in (None, "", [], {}):
            continue
        if not current:
            continue
        allowed: list[str] = []
        if isinstance(value, str):
            if value.strip():
                allowed = [value.strip()]
        elif isinstance(value, list):
            allowed = [
                str(item).strip()
                for item in value
                if item is not None and str(item).strip()
            ]
        else:
            continue
        if current.lower() not in {name.lower() for name in allowed if name}:
            return False
    return True


def iter_visible_pretask_entries(
    interface: dict[str, Any] | None,
    current_controller: str = "",
    current_resource: str = "",
) -> list[dict[str, Any]]:
    """返回当前控制器/资源下可见的 pretask 条目。"""
    if not isinstance(interface, dict):
        return []

    raw_entries = interface.get("pretask")
    if not raw_entries:
        return []

    if isinstance(raw_entries, dict):
        pretask_entries = [raw_entries]
    elif isinstance(raw_entries, list):
        pretask_entries = [entry for entry in raw_entries if isinstance(entry, dict)]
    else:
        return []

    visible: list[dict[str, Any]] = []
    for entry in pretask_entries:
        if not is_pretask_entry_allowed(entry, current_controller, current_resource):
            continue
        visible.append(entry)
    return visible


def has_visible_pretask_entries(
    interface: dict[str, Any] | None,
    current_controller: str = "",
    current_resource: str = "",
) -> bool:
    """interface 在当前控制器/资源下是否存在可展示的 pretask 内容。"""
    return bool(iter_visible_pretask_entries(
        interface,
        current_controller,
        current_resource,
    ))
