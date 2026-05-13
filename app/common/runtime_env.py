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

- 源码：应用根 = main.py 所在目录。
- Win/Linux 打包：应用根 = ``dirname(sys.executable)``。
- macOS ``.app``：主程序 Mach-O 在 ``…/MFW.app/Contents/MacOS/MFW`` 时，应用根为
  **包含 ``MFW.app`` 的目录**（与 .app 同级），便于 ``./interface.json``、``./app`` 等。
- 更新器（mac）：二进制放在 ``MFW.app/Contents/MacOS/`` 与 ``MFW`` 同级；解析路径时
  **优先**该目录，再回落安装根（与 ``cwd`` 一致）。
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


def apply_startup_workdir(main_file: str) -> Path:
    """将进程 ``cwd`` 设为安装根；打包时设置 ``MAAFW_BINARY_PATH``。"""
    base = resolve_application_base_dir(main_file)
    os.chdir(base)
    if is_frozen_bundle():
        os.environ["MAAFW_BINARY_PATH"] = os.fspath(base)
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
        names = ("MFWUpdater1", "MFWUpdater")
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
