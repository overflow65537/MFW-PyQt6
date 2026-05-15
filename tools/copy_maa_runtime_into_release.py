#   This file is part of MFW-ChainFlow Assistant.
#
#   SPDX-License-Identifier: GPL-3.0-or-later

"""
将 pip 安装的 maa 包内原生库复制到发行根（与 MFW 可执行文件同目录），供 MAAFW_BINARY_PATH 使用。
用法: python tools/copy_maa_runtime_into_release.py <release_dir>
"""

from __future__ import annotations

import importlib.util
import shutil
import sys
from pathlib import Path


def copy_maa_bin_to_release(dst: Path) -> None:
    spec = importlib.util.find_spec("maa")
    if spec is None or not spec.origin:
        raise RuntimeError("找不到已安装的 maa 包（请先 pip install -r requirements.txt）")
    src_bin = Path(spec.origin).resolve().parent / "bin"
    if not src_bin.is_dir():
        raise RuntimeError(f"maa/bin 不存在: {src_bin}")
    dst = dst.resolve()
    dst.mkdir(parents=True, exist_ok=True)
    for item in src_bin.iterdir():
        if item.is_file():
            shutil.copy2(item, dst / item.name)
        elif item.is_dir() and item.name == "plugins":
            plug_dst = dst / "plugins"
            plug_dst.mkdir(exist_ok=True)
            for child in item.iterdir():
                if child.is_file():
                    shutil.copy2(child, plug_dst / child.name)


def main() -> int:
    if len(sys.argv) != 2:
        print("用法: python tools/copy_maa_runtime_into_release.py <release_dir>", file=sys.stderr)
        return 2
    copy_maa_bin_to_release(Path(sys.argv[1]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
