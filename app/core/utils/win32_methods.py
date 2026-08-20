"""Win32 控制器截图/输入方式解析。

interface.json 使用 ``Background`` / ``ScreenDC`` 等名字，用户配置里可能是整数、
字符串或缺失。连接层必须在这里完成转换，不能把缺失值默认成 GDI(1)：
Unity/D3D 窗口用 GDI 截到的往往是打开时的第一帧，之后不再更新。
"""

from __future__ import annotations

from typing import Any

from maa.define import MaaWin32InputMethodEnum, MaaWin32ScreencapMethodEnum

# 与 MaaFramework Win32 截图 flag 对齐的兜底别名。
# 即使当前 Python 枚举尚未导出 ScreenDC/Background 等成员，原生库仍可能接受这些值。
_WIN32_SCREENCAP_FALLBACK_ALIASES: dict[str, int] = {
    "gdi": 1,
    "framepool": 2,
    "dxgidesktopdup": 4,
    "dxgidesktopdupwindow": 8,
    "printwindow": 16,
    "screendc": 32,
    "foreground": 8 | 32,
    "background": 2 | 16,
}


def normalize_method_name(value: str) -> str:
    return "".join(ch.lower() for ch in value if ch.isalnum())


def enum_method_aliases(enum_cls: Any) -> dict[str, int]:
    aliases: dict[str, int] = {}
    for name, member in getattr(enum_cls, "__members__", {}).items():
        key = normalize_method_name(str(name))
        if not key:
            continue
        aliases[key] = int(getattr(member, "value", member))
    return aliases


def coerce_method_int(value: Any) -> int | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            return int(text, 0)
        except ValueError:
            return None
    return None


def resolve_method_value(
    value: Any,
    *,
    aliases: dict[str, int],
    default: int | None = None,
    zero_is_missing: bool = True,
) -> int | None:
    parsed_int = coerce_method_int(value)
    if parsed_int is not None:
        if parsed_int == -1 or (zero_is_missing and parsed_int == 0):
            return default
        return parsed_int

    if isinstance(value, str):
        mapped = aliases.get(normalize_method_name(value))
        if mapped is None:
            return default
        if zero_is_missing and mapped == 0:
            return default
        return mapped

    return default


def win32_screencap_aliases() -> dict[str, int]:
    aliases = dict(_WIN32_SCREENCAP_FALLBACK_ALIASES)
    aliases.update(enum_method_aliases(MaaWin32ScreencapMethodEnum))
    return aliases


def win32_input_aliases() -> dict[str, int]:
    return enum_method_aliases(MaaWin32InputMethodEnum)


def resolve_win32_screencap_method(
    value: Any,
    *,
    fallback: Any = None,
) -> int:
    aliases = win32_screencap_aliases()
    default = int(MaaWin32ScreencapMethodEnum.DXGI_DesktopDup.value)
    resolved = resolve_method_value(value, aliases=aliases, default=None)
    if resolved is not None:
        return resolved
    resolved = resolve_method_value(fallback, aliases=aliases, default=None)
    if resolved is not None:
        return resolved
    return default


def resolve_win32_input_method(
    value: Any,
    *,
    fallback: Any = None,
) -> int:
    aliases = win32_input_aliases()
    default = int(MaaWin32InputMethodEnum.Seize.value)
    resolved = resolve_method_value(value, aliases=aliases, default=None)
    if resolved is not None:
        return resolved
    resolved = resolve_method_value(fallback, aliases=aliases, default=None)
    if resolved is not None:
        return resolved
    return default
