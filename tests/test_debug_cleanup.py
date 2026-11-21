"""debug 目录清理分工与保留时长测试。"""

from __future__ import annotations

import os
from datetime import datetime, timedelta
from pathlib import Path

from app.core.utils.debug_cleanup import (
    FRAMEWORK_MANAGED_RETENTION,
    LEGACY_RETENTION,
    build_debug_retention,
    cleanup_old_debug_files,
)

NOW = datetime(2026, 11, 21, 12, 0, 0)


def _make_file(root: Path, relative: str, age: timedelta) -> Path:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"x")
    timestamp = (NOW - age).timestamp()
    os.utime(path, (timestamp, timestamp))
    return path


def test_retention_matches_framework_ownership():
    assert build_debug_retention(False) is LEGACY_RETENTION
    assert build_debug_retention(True) is FRAMEWORK_MANAGED_RETENTION

    # 5.x 框架只管 7 天以上，MFW 用更严格的阈值兜底
    assert LEGACY_RETENTION["vision"] == timedelta(days=1)
    assert LEGACY_RETENTION["on_error"] == timedelta(days=3)

    # 6.x 框架自己按 3 天 / 7 天维护，MFW 对齐同档
    assert FRAMEWORK_MANAGED_RETENTION["vision"] == timedelta(days=3)
    assert FRAMEWORK_MANAGED_RETENTION["on_error"] == timedelta(days=7)

    # stop 是 MFW 自己的目录，任何版本都由 MFW 清理
    for retention in (LEGACY_RETENTION, FRAMEWORK_MANAGED_RETENTION):
        assert retention["stop"] == timedelta(days=3)


def test_cleanup_5x_keeps_vision_for_one_day_only(tmp_path: Path):
    root = tmp_path / "debug"
    stale_vision = _make_file(root, "vision/stale.png", timedelta(days=2))
    fresh_vision = _make_file(root, "vision/fresh.png", timedelta(hours=2))
    stale_error = _make_file(root, "on_error/stale.png", timedelta(days=5))
    stale_stop = _make_file(root, "stop/stale.png", timedelta(days=5))

    removed = cleanup_old_debug_files(root, LEGACY_RETENTION, now=NOW)

    assert set(removed) == {stale_vision, stale_error, stale_stop}
    assert fresh_vision.exists()


def test_cleanup_6x_defers_vision_and_on_error_to_framework(tmp_path: Path):
    root = tmp_path / "debug"
    two_days_vision = _make_file(root, "vision/two_days.png", timedelta(days=2))
    five_days_error = _make_file(root, "on_error/five_days.png", timedelta(days=5))
    eight_days_error = _make_file(root, "on_error/eight_days.png", timedelta(days=8))
    stale_stop = _make_file(root, "stop/stale.png", timedelta(days=5))

    removed = cleanup_old_debug_files(root, FRAMEWORK_MANAGED_RETENTION, now=NOW)

    # 框架的保留期是 vision 3 天 / on_error 7 天，MFW 只做同档兜底
    assert two_days_vision.exists()
    assert five_days_error.exists()
    assert set(removed) == {eight_days_error, stale_stop}


def test_cleanup_skips_missing_dirs_and_nested_files(tmp_path: Path):
    root = tmp_path / "debug"
    nested = _make_file(root, "vision/2026-11-01/stale.png", timedelta(days=30))

    # 不存在的子目录直接跳过，不抛异常
    assert cleanup_old_debug_files(root, FRAMEWORK_MANAGED_RETENTION, now=NOW) == []

    # 只清子目录顶层的文件，与旧实现一致，不递归
    assert nested.exists()


def test_cleanup_ignores_unreadable_entries(tmp_path: Path, monkeypatch):
    root = tmp_path / "debug"
    stale_stop = _make_file(root, "stop/stale.png", timedelta(days=5))

    real_stat = Path.stat

    def flaky_stat(self, *args, **kwargs):
        if self.name == "stale.png":
            raise OSError("boom")
        return real_stat(self, *args, **kwargs)

    monkeypatch.setattr(Path, "stat", flaky_stat)

    assert cleanup_old_debug_files(root, LEGACY_RETENTION, now=NOW) == []
    # Path.stat 已被打桩，这里用 os.path.exists 确认文件还在
    assert os.path.exists(stale_stop)
