"""读取当前集成的 MaaFramework 版本，并按主版本号判断能力差异。"""

from __future__ import annotations

import re

_VERSION_PATTERN = re.compile(r"(\d+)\.(\d+)(?:\.(\d+))?")


def parse_maafw_version(text: str | None) -> tuple[int, int, int] | None:
    """解析 ``v5.16.1`` / ``v6.0.0-beta.3`` 这类版本串；无法解析时返回 None。"""
    if not text:
        return None
    match = _VERSION_PATTERN.search(str(text))
    if not match:
        return None
    major, minor, patch = match.group(1), match.group(2), match.group(3) or "0"
    return int(major), int(minor), int(patch)


def current_maafw_version() -> tuple[int, int, int] | None:
    """返回当前加载的 MaaFramework 原生库版本；拿不到时返回 None。"""
    try:
        from maa.library import Library

        return parse_maafw_version(Library.version())
    except Exception:
        return None


def maafw_manages_debug_images() -> bool:
    """MaaFramework 6.0 起自己维护 ``debug/vision`` 与 ``debug/on_error``。

    维护内容包括 3 天 / 7 天的保留期限和 1 GiB 总预算（见 MaaUtils 的
    ``LogMaintenance.cpp``）。更早的版本只在启动时递归删 debug 下超过 7 天的
    ``.log`` / ``.jpg`` / ``.png``，力度弱得多。
    """
    version = current_maafw_version()
    return version is not None and version[0] >= 6
