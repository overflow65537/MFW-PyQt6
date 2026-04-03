"""任务选项 `children`/`branches` 兼容辅助工具。

新增时间: 2026-04-03

说明:
- 持久化字段已从 `children` 迁移为 `branches`
- 为兼容旧配置，读取时仍接受 `children`
- 配置加载后会优先更正为 `branches`，后续保存统一输出新字段
"""

from __future__ import annotations

from typing import Any, Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from app.core.item import ConfigItem

BRANCHES_FIELD = "branches"
LEGACY_CHILDREN_FIELD = "children"


def get_option_branches(option_value: Any) -> Dict[str, Any]:
    """读取选项的分支配置，兼容 `branches` / `children`。"""
    if not isinstance(option_value, dict):
        return {}

    branches = option_value.get(BRANCHES_FIELD)
    if isinstance(branches, dict):
        return branches

    legacy_children = option_value.get(LEGACY_CHILDREN_FIELD)
    if isinstance(legacy_children, dict):
        return legacy_children

    return {}


def set_option_branches(option_value: Dict[str, Any], branches: Dict[str, Any]) -> None:
    """写入新的分支字段，并移除旧字段。"""
    if branches:
        option_value[BRANCHES_FIELD] = branches
    else:
        option_value.pop(BRANCHES_FIELD, None)
    option_value.pop(LEGACY_CHILDREN_FIELD, None)


def normalize_option_branches_payload(payload: Any) -> bool:
    """递归将旧字段 `children` 更正为 `branches`。"""
    changed = False

    if isinstance(payload, list):
        for item in payload:
            changed = normalize_option_branches_payload(item) or changed
        return changed

    if not isinstance(payload, dict):
        return False

    if LEGACY_CHILDREN_FIELD in payload:
        legacy_children = payload.pop(LEGACY_CHILDREN_FIELD)
        branches = payload.get(BRANCHES_FIELD)
        if not isinstance(branches, dict):
            branches = {}
            payload[BRANCHES_FIELD] = branches
        if isinstance(legacy_children, dict):
            for key, value in legacy_children.items():
                branches.setdefault(key, value)
        changed = True

    for value in payload.values():
        changed = normalize_option_branches_payload(value) or changed

    return changed


def normalize_config_item_branches(config_item: "ConfigItem") -> bool:
    """读取配置后，将旧字段统一更正为 `branches`。"""
    changed = False

    for task in getattr(config_item, "tasks", []) or []:
        task_option = getattr(task, "task_option", None)
        if isinstance(task_option, dict):
            changed = normalize_option_branches_payload(task_option) or changed

    global_options = getattr(config_item, "global_options", None)
    if isinstance(global_options, dict):
        changed = normalize_option_branches_payload(global_options) or changed

    return changed
