#   This file is part of MFW-ChainFlow Assistant.
#
#   MFW-ChainFlow Assistant is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published
#   by the Free Software Foundation, either version 3 of the License,
#   or (at your option) any later version.
#
#   MFW-ChainFlow Assistant is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty
#   of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See
#   the GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with MFW-ChainFlow Assistant. If not, see <https://www.gnu.org/licenses/>.
#
#   Contact: err.overflow@gmail.com
#   Copyright (C) 2024-2025  MFW-ChainFlow Assistant. All rights reserved.

"""
打包运行环境与安装根目录（与 Win/Linux 单目录布局对齐）。

- 源码：应用根 = main.py 所在目录；**不设置** ``MAAFW_BINARY_PATH``（保持环境原样）。
- Win/Linux 打包：应用根 = ``dirname(sys.executable)``。
- macOS ``.app``：主程序 Mach-O 在 ``…/MFW.app/Contents/MacOS/MFW.bin``（或旧版无后缀 ``MFW``）时，应用根为
  **包含 ``MFW.app`` 的目录**（与 .app 同级），便于 ``./interface.json``、``./app`` 等。
- 打包时 ``MAAFW_BINARY_PATH``：指向 **``{安装根}/maafw``**（外部提供的运行库目录；mac 即 app 同级下的 ``maafw/``）。
- Maa 原生工具链须保留在 **``maa/bin``**（勿平铺到安装根）；Windows/Linux 打包启动时会调整 ``PATH`` / ``LD_LIBRARY_PATH`` 以便加载。
- 更新器（mac）：在 ``MFW.app/Contents/MacOS/`` 与安装根中解析 ``MFWUpdater*``。
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


def is_frozen_bundle() -> bool:
    """是否为打包运行（PyInstaller / Nuitka）。"""
    if getattr(sys, "frozen", False):
        return True
    main_mod = sys.modules.get("__main__")
    return main_mod is not None and getattr(main_mod, "__compiled__", None) is not None


def _darwin_install_root_if_app_bundle(executable: Path) -> Path | None:
    """若在 ``*.app/Contents/MacOS/`` 下运行，返回包含该 ``.app`` 的目录。"""
    if sys.platform != "darwin":
        return None
    resolved = executable.resolve()
    p = resolved.parent
    if p.name != "MacOS" or p.parent.name != "Contents":
        return None
    bundle = p.parent.parent
    if bundle.suffix != ".app":
        return None
    return bundle.parent


def resolve_application_base_dir(main_file: str) -> Path:
    """应用安装根目录（相对路径资源、用户数据均相对此目录）。"""
    if not is_frozen_bundle():
        return Path(main_file).resolve().parent
    exe = Path(sys.executable).resolve()
    root = _darwin_install_root_if_app_bundle(exe)
    if root is not None:
        return root
    return exe.parent


def _bootstrap_linux_frozen_env(base: Path) -> None:
    """Linux 单目录发行：Qt 插件 + 动态库搜索路径（maa 工具链须留在 maa/bin，勿平铺到安装根）。"""
    if sys.platform != "linux" or not is_frozen_bundle():
        return
    exe_dir = Path(sys.executable).resolve().parent
    qt_plugins = exe_dir / "PySide6" / "Qt" / "plugins"
    if qt_plugins.is_dir():
        os.environ.setdefault("QT_PLUGIN_PATH", str(qt_plugins))
    maa_bin = exe_dir / "maa" / "bin"
    prepend: list[str] = []
    if maa_bin.is_dir():
        prepend.append(str(maa_bin))
    prepend.append(str(exe_dir))
    ld = os.environ.get("LD_LIBRARY_PATH", "")
    os.environ["LD_LIBRARY_PATH"] = ":".join(prepend + ([ld] if ld else []))


def _bootstrap_win_frozen_env(base: Path) -> None:
    """Windows 打包：将 maa/bin 加入 PATH，便于按包内路径查找 maabinary 等，勿与安装根平铺混用。"""
    if not sys.platform.startswith("win32") or not is_frozen_bundle():
        return
    maa_bin = base.resolve() / "maa" / "bin"
    if not maa_bin.is_dir():
        return
    p = str(maa_bin)
    path = os.environ.get("PATH", "")
    if p not in path.split(os.pathsep):
        os.environ["PATH"] = p + os.pathsep + path
    add_dll = getattr(os, "add_dll_directory", None)
    if callable(add_dll):
        try:
            add_dll(p)
        except OSError:
            pass


def apply_startup_workdir(main_file: str) -> Path:
    """将进程 ``cwd`` 设为安装根；仅在打包时设置 ``MAAFW_BINARY_PATH`` 为 ``{cwd}/maafw``。"""
    base = resolve_application_base_dir(main_file)
    os.chdir(base)
    _bootstrap_linux_frozen_env(base)
    _bootstrap_win_frozen_env(base)
    # if is_frozen_bundle():
    #    maafw_dir = (Path(base) / "maafw").resolve()
    #    os.environ["MAAFW_BINARY_PATH"] = os.fspath(maafw_dir)
    return base


def main_entry_abspath(main_file: str) -> str:
    """单实例键：打包为 ``sys.executable`` 绝对路径（mac 为 bundle 内 Mach-O）。"""
    if is_frozen_bundle():
        return os.path.abspath(sys.executable)
    return os.path.abspath(main_file)


def _updater_search_dirs() -> list[Path]:
    """更新器可能出现的位置（顺序即查找优先级）。"""
    root = Path.cwd()
    if sys.platform == "darwin":
        inner = root / "MFW.app" / "Contents" / "MacOS"
        if inner.is_dir():
            return [inner, root]
    return [root]


def resolve_sidecar_updater_path() -> Path | None:
    """解析更新器绝对路径；找不到返回 ``None``。"""
    if sys.platform.startswith("win32"):
        names = ("MFWUpdater1.exe", "MFWUpdater.exe")
    elif sys.platform.startswith(("darwin", "linux")):
        names = (
            "MFWUpdater1.bin",
            "MFWUpdater.bin",
            "MFWUpdater1",
            "MFWUpdater",
        )
    else:
        return None
    for d in _updater_search_dirs():
        for name in names:
            p = d / name
            if p.is_file():
                return p.resolve()
    return None


def rename_updater_sidecar(old_name: str, new_name: str) -> None:
    """在可能目录下重命名更新器（首个命中 ``old_name`` 的目录内执行）。"""
    for d in _updater_search_dirs():
        old_p = d / old_name
        new_p = d / new_name
        if not old_p.is_file():
            continue
        if new_p.is_file():
            new_p.unlink()
        old_p.rename(new_p)
        return
