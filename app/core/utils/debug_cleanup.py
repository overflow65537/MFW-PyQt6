"""``debug`` 目录旧文件清理的分工与实现。

MaaFramework 只维护它自己的产物，清理分工随版本不同：

- 5.x：框架启动时递归删 debug 下超过 7 天的 ``.log`` / ``.jpg`` / ``.png``；
  MFW 另外按更严格的 ``vision`` 1 天、``on_error`` 3 天、``stop`` 3 天兜底
- 6.0 起：框架按 ``vision`` 3 天、``on_error`` 7 天加 1 GiB 总预算维护，且
  **不再扫 MFW 的 ``debug/stop`` 等目录**；所以 MFW 保留自己的 ``stop`` 清理，
  并把 ``vision`` / ``on_error`` 放宽到框架同档，只作为框架维护没跑起来时的兜底

``debug/save_screen``（监控页手动保存的截图）属于用户文件，任何版本都不自动删除。
"""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from typing import Mapping

# 5.x：框架只管 7 天以上，MFW 用更严格的阈值控制体积
LEGACY_RETENTION: Mapping[str, timedelta] = {
    "stop": timedelta(days=3),
    "on_error": timedelta(days=3),
    "vision": timedelta(days=1),
}

# 6.0 起：框架自己按 3 天 / 7 天维护 vision 与 on_error，MFW 只做同档兜底
FRAMEWORK_MANAGED_RETENTION: Mapping[str, timedelta] = {
    "stop": timedelta(days=3),
    "on_error": timedelta(days=7),
    "vision": timedelta(days=3),
}


def build_debug_retention(
    framework_manages_images: bool,
) -> Mapping[str, timedelta]:
    """按框架是否自己维护图片，返回 ``目录名 -> 保留时长``。"""
    return FRAMEWORK_MANAGED_RETENTION if framework_manages_images else LEGACY_RETENTION


def cleanup_old_debug_files(
    debug_dir: Path,
    retention: Mapping[str, timedelta],
    *,
    now: datetime | None = None,
) -> list[Path]:
    """删除各子目录中超过保留时长的旧文件，返回已删除的路径。

    单个文件失败不影响其余文件；不存在的目录直接跳过。
    """
    reference = now or datetime.now()
    removed: list[Path] = []
    for subdir_name, keep_for in retention.items():
        target_dir = debug_dir / subdir_name
        if not target_dir.is_dir():
            continue
        cutoff = reference - keep_for
        for file_path in target_dir.iterdir():
            try:
                if not file_path.is_file():
                    continue
                if datetime.fromtimestamp(file_path.stat().st_mtime) >= cutoff:
                    continue
                file_path.unlink()
            except OSError:
                continue
            removed.append(file_path)
    return removed
