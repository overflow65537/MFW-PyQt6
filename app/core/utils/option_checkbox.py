"""PI v2.10.1 checkbox min_count / max_count 解析与校验。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping

import re

from app.core.utils.option_branches_compat import get_option_branches

_PRETASK_WIDGET_KEY = re.compile(r"^entry_\d+_(.+)$")


def resolve_option_name(option_key: str) -> str:
    """从任务选项 key（含 pretask 的 entry_{idx}_{name}）解析 interface option 名。"""
    if not option_key:
        return ""
    match = _PRETASK_WIDGET_KEY.match(option_key)
    return match.group(1) if match else option_key


@dataclass(frozen=True, slots=True)
class CheckboxCountViolation:
    """一条不满足 min_count / max_count 的 checkbox 选择。"""

    option_name: str
    option_label: str
    selected_count: int
    min_count: int
    max_count: int | None
    kind: str  # "min" | "max"


def _as_non_negative_int(value: Any, default: int) -> int:
    if value is None or value == "":
        return default
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return parsed if parsed >= 0 else default


def get_checkbox_limits(option_def: Mapping[str, Any] | None) -> tuple[int, int | None]:
    """返回 (min_count, max_count)。max_count 为 None 表示不限制。"""
    if not isinstance(option_def, Mapping):
        return 0, None
    cases = option_def.get("cases", [])
    case_count = len(cases) if isinstance(cases, list) else 0
    min_count = _as_non_negative_int(option_def.get("min_count"), 0)
    raw_max = option_def.get("max_count", None)
    max_count: int | None
    if raw_max is None or raw_max == "":
        max_count = None
    else:
        max_count = _as_non_negative_int(raw_max, case_count)
    if case_count > 0:
        min_count = min(min_count, case_count)
        if max_count is not None:
            max_count = min(max_count, case_count)
    if max_count is not None and min_count > max_count:
        min_count = max_count
    return min_count, max_count


def normalize_checkbox_selection(value: Any) -> list[str]:
    """将 checkbox 存储值规范为 case.name 字符串列表。"""
    if value is None:
        return []
    if isinstance(value, dict) and "value" in value:
        value = value.get("value")
    if isinstance(value, str):
        return [value] if value else []
    if isinstance(value, (list, tuple)):
        return [str(item) for item in value if item is not None and str(item) != ""]
    return []


def clamp_checkbox_selection(
    selected: Iterable[str], option_def: Mapping[str, Any] | None
) -> list[str]:
    """按 cases 定义顺序去重，并截断到 max_count。"""
    names = [str(item) for item in selected if item is not None and str(item) != ""]
    seen: set[str] = set()
    ordered: list[str] = []
    cases = []
    if isinstance(option_def, Mapping):
        raw_cases = option_def.get("cases", [])
        if isinstance(raw_cases, list):
            cases = raw_cases
    case_names = [
        str(case.get("name", ""))
        for case in cases
        if isinstance(case, Mapping) and case.get("name")
    ]
    if case_names:
        selected_set = set(names)
        for name in case_names:
            if name in selected_set and name not in seen:
                seen.add(name)
                ordered.append(name)
        for name in names:
            if name not in seen:
                seen.add(name)
                ordered.append(name)
    else:
        for name in names:
            if name not in seen:
                seen.add(name)
                ordered.append(name)

    _, max_count = get_checkbox_limits(option_def)
    if max_count is not None:
        return ordered[:max_count]
    return ordered


def checkbox_selection_violation(
    selected: Iterable[str], option_def: Mapping[str, Any] | None, option_name: str = ""
) -> CheckboxCountViolation | None:
    """若选中数量不满足上下限则返回违规信息。"""
    names = list(selected)
    min_count, max_count = get_checkbox_limits(option_def)
    count = len(names)
    label = ""
    if isinstance(option_def, Mapping):
        label = str(option_def.get("label") or option_def.get("name") or option_name)
    else:
        label = option_name
    if count < min_count:
        return CheckboxCountViolation(
            option_name=option_name,
            option_label=label or option_name,
            selected_count=count,
            min_count=min_count,
            max_count=max_count,
            kind="min",
        )
    if max_count is not None and count > max_count:
        return CheckboxCountViolation(
            option_name=option_name,
            option_label=label or option_name,
            selected_count=count,
            min_count=min_count,
            max_count=max_count,
            kind="max",
        )
    return None


def collect_checkbox_violations(
    option_map: Any,
    interface_options: Mapping[str, Any] | None,
) -> list[CheckboxCountViolation]:
    """从选项树中收集所有 checkbox 数量违规。"""
    options = interface_options if isinstance(interface_options, Mapping) else {}
    violations: list[CheckboxCountViolation] = []
    _collect_from_map(option_map, options, violations)
    return violations


def _collect_from_map(
    option_map: Any,
    interface_options: Mapping[str, Any],
    violations: list[CheckboxCountViolation],
) -> None:
    if not isinstance(option_map, Mapping):
        return
    for key, value in option_map.items():
        if key in {
            "resource_options",
            "setting_options",
            "controller_options",
            "global_options",
        } and isinstance(value, dict):
            _collect_from_map(value, interface_options, violations)
            continue
        if key == "pretask_entries" and isinstance(value, list):
            for entry in value:
                if isinstance(entry, dict):
                    _collect_from_map(
                        entry.get("options"), interface_options, violations
                    )
            continue
        if str(key).startswith("_"):
            continue
        option_name = resolve_option_name(str(key))
        option_def = interface_options.get(option_name, {})
        if not isinstance(option_def, Mapping):
            option_def = {}
        if str(option_def.get("type", "")).lower() == "checkbox":
            selected = normalize_checkbox_selection(value)
            violation = checkbox_selection_violation(selected, option_def, option_name)
            if violation is not None:
                violations.append(violation)
        if isinstance(value, dict):
            for branch_value in get_option_branches(value).values():
                if isinstance(branch_value, dict):
                    _collect_from_map(branch_value, interface_options, violations)
