#   This file is part of MFW-ChainFlow Assistant.
#
#   SPDX-License-Identifier: GPL-3.0-or-later

"""打包运行时定位 MaaFW 原生库，并补齐 macOS dylib 的 @rpath 布局。"""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

FRAMEWORK_LIB_NAMES = (
    "libMaaFramework.dylib",
    "libMaaFramework.so",
    "MaaFramework.dll",
)


def _has_framework_lib(path: Path) -> bool:
    return path.is_dir() and any((path / name).is_file() for name in FRAMEWORK_LIB_NAMES)


def _is_native_lib(path: Path) -> bool:
    name = path.name.lower()
    return (
        name.endswith(".dylib")
        or name.endswith(".dll")
        or name.endswith(".so")
        or ".so." in name
    )


def _place_file(src: Path, dest: Path) -> None:
    if dest.exists() or src.resolve() == dest.resolve():
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.link(src, dest)
    except OSError:
        shutil.copy2(src, dest)


def _mirror_native_libs(src_dir: Path, dest_dir: Path) -> None:
    if not src_dir.is_dir():
        return
    dest_dir.mkdir(parents=True, exist_ok=True)
    for item in src_dir.iterdir():
        if item.is_file() and _is_native_lib(item):
            _place_file(item, dest_dir / item.name)


def resolve_maafw_binary_dir(install_root: Path, meipass: str | None = None) -> Path:
    """定位实际含有 MaaFramework 动态库的目录。"""
    candidates = [
        install_root / "maafw" / "maa" / "bin",
        install_root / "maafw",
    ]
    internal = Path(meipass).resolve() if meipass else None
    if internal is not None:
        candidates.append(internal / "maa" / "bin")
        candidates.append(internal)
    candidates.append(install_root / "maa" / "bin")
    for candidate in candidates:
        if _has_framework_lib(candidate):
            return candidate.resolve()
    return (install_root / "maafw").resolve()


def prepare_macos_rpath_layout(framework_dir: Path) -> Path:
    """让 ``@loader_path/../..`` 能解析到 libMaaUtils 等依赖。

    PyInstaller 会把 macOS dylib 的 LC_RPATH 改成 ``@loader_path/../..``。
    因此主库若在 ``maafw/maa/bin``，配件必须同时出现在 ``maafw/``；
    若发行布局是扁平的 ``maafw/*.dylib``，则补一套 ``maafw/maa/bin`` 视图，
    让加载路径的上两级仍然落在 ``maafw/``。
    """
    if sys.platform != "darwin" or not framework_dir.is_dir():
        return framework_dir

    nested_pip_layout = (
        framework_dir.name == "bin" and framework_dir.parent.name == "maa"
    )
    if nested_pip_layout:
        _mirror_native_libs(framework_dir, framework_dir.parent.parent)
        return framework_dir

    if not _has_framework_lib(framework_dir):
        return framework_dir

    nested_bin = framework_dir / "maa" / "bin"
    try:
        _mirror_native_libs(framework_dir, nested_bin)
    except OSError:
        return framework_dir
    if _has_framework_lib(nested_bin):
        return nested_bin
    return framework_dir


def configure_packed_maafw_binary_path(
    install_root: Path, meipass: str | None = None
) -> Path:
    """设置 ``MAAFW_BINARY_PATH``，并在 Windows 上注册 DLL 搜索目录。"""
    binary_dir = resolve_maafw_binary_dir(install_root, meipass=meipass)
    binary_dir = prepare_macos_rpath_layout(binary_dir)
    os.environ["MAAFW_BINARY_PATH"] = str(binary_dir)
    if sys.platform == "win32":
        try:
            os.add_dll_directory(str(binary_dir))
            plugin_dir = binary_dir / "plugins"
            if plugin_dir.is_dir():
                os.add_dll_directory(str(plugin_dir))
            # 扁平布局下插件仍在 maafw/plugins
            flat_plugin_dir = install_root / "maafw" / "plugins"
            if flat_plugin_dir.is_dir() and flat_plugin_dir != plugin_dir:
                os.add_dll_directory(str(flat_plugin_dir))
        except (AttributeError, OSError, ValueError):
            pass
    return binary_dir
