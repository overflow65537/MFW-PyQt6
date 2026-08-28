#   This file is part of MFW-ChainFlow Assistant.
#
#   SPDX-License-Identifier: GPL-3.0-or-later

"""
将编译目录下的 maa/bin 原生库迁移到发行根 maafw/。

Nuitka standalone 产物中 DLL 默认在 <release>/maa/bin；本脚本在组装阶段执行。
macOS app-dist 的源目录位于 MFW.app/Contents/MacOS，目标则是 .app 的父目录。
用法: python tools/packaging/move_maa_bin_to_maafw.py <source_root> [destination_root]
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path


def move_maa_bin_to_maafw(
    source_root: Path, destination_root: Path | None = None
) -> bool:
    maa_bin = source_root / "maa" / "bin"
    if not maa_bin.is_dir():
        return False
    dest = (destination_root or source_root) / "maafw"
    dest.mkdir(parents=True, exist_ok=True)
    for item in list(maa_bin.iterdir()):
        target = dest / item.name
        if target.exists():
            if target.is_dir():
                shutil.rmtree(target)
            else:
                target.unlink()
        shutil.move(str(item), str(target))
    shutil.rmtree(maa_bin, ignore_errors=True)
    return True


def main() -> int:
    if len(sys.argv) not in {2, 3}:
        print(
            "用法: python tools/packaging/move_maa_bin_to_maafw.py <source_root> [destination_root]",
            file=sys.stderr,
        )
        return 2
    source_root = Path(sys.argv[1])
    destination_root = Path(sys.argv[2]) if len(sys.argv) == 3 else source_root
    if not source_root.is_dir():
        print(f"目录不存在: {source_root}", file=sys.stderr)
        return 1
    destination_root.mkdir(parents=True, exist_ok=True)
    if not move_maa_bin_to_maafw(source_root, destination_root):
        print(f"错误: 未找到 {source_root / 'maa' / 'bin'}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
