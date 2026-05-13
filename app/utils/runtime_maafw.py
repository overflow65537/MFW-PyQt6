"""
外置 MaaFramework 运行库（maafw）路径配置。

与 MXU 一致：在可执行文件同目录下使用子目录 maafw，存放官方发布包中的 bin 内容。
maa 包在 import 时会读取环境变量 MAAFW_BINARY_PATH（见 site-packages/maa/__init__.py）。
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


def is_bundled_executable() -> bool:
    """是否为 PyInstaller / Nuitka 等打包后的可执行文件环境。"""
    v = getattr(sys, "frozen", False)
    if isinstance(v, str):
        return v.lower() in ("yes", "true", "1")
    return bool(v)


def maafw_directory(app_root: Path) -> Path:
    return app_root / "maafw"


def _framework_filenames() -> tuple[str, ...]:
    if sys.platform == "win32":
        return ("MaaFramework.dll",)
    if sys.platform == "darwin":
        return ("libMaaFramework.dylib",)
    return ("libMaaFramework.so",)


def _maafw_has_framework_libs(directory: Path) -> bool:
    if not directory.is_dir():
        return False
    return any((directory / name).is_file() for name in _framework_filenames())


def apply_maafw_runtime_layout(
    app_root: Path, *, require_external_when_bundled: bool | None = None
) -> Path | None:
    """
    在首次 import maa 之前调用。

    - 打包环境：要求 app_root/maafw 存在且含 MaaFramework 主库，并设置 MAAFW_BINARY_PATH；
      Windows 下同时将 maafw 注册为 DLL 搜索目录。
    - 开发环境：若存在 app_root/maafw 且含主库，则优先使用；否则不设置环境变量，
      由 maa 回退到 site-packages/maa/bin。

    返回实际使用的 maafw 绝对路径；若使用内置 pip bin 则返回 None。
    """
    root = app_root.resolve()
    ext = maafw_directory(root)
    if require_external_when_bundled is None:
        require_external_when_bundled = is_bundled_executable()

    has_libs = _maafw_has_framework_libs(ext)

    if require_external_when_bundled:
        if not has_libs:
            names = ", ".join(_framework_filenames())
            print(
                "未找到外置 MaaFramework 运行库（maafw）。\n"
                f"请将官方运行库压缩包中的 bin 目录内文件解压到：\n  {ext}\n"
                f"并确保其中包含：{names}\n"
                "说明与 MXU 相同：主程序旁放置 maafw 文件夹承载原生库。\n",
                file=sys.stderr,
            )
            raise SystemExit(1)
        resolved = ext.resolve()
        os.environ["MAAFW_BINARY_PATH"] = str(resolved)
        if sys.platform == "win32" and hasattr(os, "add_dll_directory"):
            os.add_dll_directory(str(resolved))
        return resolved

    if has_libs:
        resolved = ext.resolve()
        os.environ["MAAFW_BINARY_PATH"] = str(resolved)
        if sys.platform == "win32" and hasattr(os, "add_dll_directory"):
            os.add_dll_directory(str(resolved))
        return resolved

    return None
