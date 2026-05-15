#   This file is part of MFW-ChainFlow Assistant.
#
#   SPDX-License-Identifier: GPL-3.0-or-later

"""
将发行目录下的 maa/bin 原生库迁移到 maafw/（与运行时 MAAFW_BINARY_PATH 一致）。

Nuitka standalone 产物中 DLL 默认在 <release>/maa/bin；本脚本在组装阶段执行。
用法: python tools/move_maa_bin_to_maafw.py <release_dir>
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path


def move_maa_bin_to_maafw(release: Path) -> bool:
    maa_bin = release / "maa" / "bin"
    if not maa_bin.is_dir():
        return False
    dest = release / "maafw"
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
    if len(sys.argv) != 2:
        print(
            "用法: python tools/move_maa_bin_to_maafw.py <release_dir>",
            file=sys.stderr,
        )
        return 2
    release = Path(sys.argv[1])
    if not release.is_dir():
        print(f"目录不存在: {release}", file=sys.stderr)
        return 1
    if not move_maa_bin_to_maafw(release):
        print(f"错误: 未找到 {release / 'maa' / 'bin'}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
