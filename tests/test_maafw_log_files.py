"""MaaFramework 日志命名规则与收集测试。

覆盖三代命名：``maa.bak.log``（5.12 及更早）、``maafw.bak.<时间戳>.log``
（5.13 起的轮转备份，本仓库实际使用的版本）与 ``.log.gz``（6.0 起压缩）。
"""

from __future__ import annotations

from pathlib import Path

import pytest

from app.core.utils.maafw_log_files import (
    is_maafw_backup_name,
    is_maafw_log_name,
    iter_maafw_log_files,
    read_log_tail,
    should_tail_trim,
)


def test_recognizes_active_log_and_legacy_backups():
    for name in ("maa.bak.log", "maafw.log.bak"):
        assert is_maafw_log_name(name)
        assert should_tail_trim(name)

    assert is_maafw_log_name("maafw.log")
    assert should_tail_trim("maafw.log")


def test_recognizes_rotated_backups_and_compressed_backups():
    plain = "maafw.bak.2026-11-21_12-34-56.log"
    compressed = "maafw.bak.2026-11-21_12-34-56.log.gz"

    assert is_maafw_log_name(plain)
    assert is_maafw_log_name(compressed)
    assert is_maafw_backup_name(plain)
    assert is_maafw_backup_name(compressed)

    # 轮转备份已受阈值约束，gzip 更是二进制，都不能按行截断
    assert not should_tail_trim(plain)
    assert not should_tail_trim(compressed)


@pytest.mark.parametrize(
    "name",
    [
        "gui.log",
        "maafw_notes.txt",
        "maafw.log.txt",
        "maa.bak.log.gz",
        "maafw.bak.2026-11-21_12-34-56.log.gz.2026-11-21_12-35-00.tmp",
        "maafw.bak.2026-11-21_12-34-56.log.bak",
        "maafw.log.bak.gz",
    ],
)
def test_ignores_unrelated_or_partial_files(name: str):
    assert not is_maafw_log_name(name)
    assert not is_maafw_backup_name(name)
    assert not should_tail_trim(name)


def test_active_log_is_not_a_backup():
    assert not is_maafw_backup_name("maafw.log")


def test_iter_collects_old_and_new_maafw_logs(tmp_path: Path):
    expected = [
        "maa.bak.log",
        "maafw.bak.2026-11-20_08-00-00.log",
        "maafw.bak.2026-11-21_09-30-00.log.gz",
        "maafw.log",
        "maafw.log.bak",
    ]
    for name in expected:
        (tmp_path / name).write_bytes(b"log")

    # 框架压缩期间的临时文件、其他日志同目录时都不应被收集
    (
        tmp_path / "maafw.bak.2026-11-21_09-30-00.log.gz.2026-11-21_09-31-00.tmp"
    ).write_bytes(b"tmp")
    (tmp_path / "gui.log").write_bytes(b"gui")
    (tmp_path / "maafw").mkdir()

    collected = [path.name for path in iter_maafw_log_files(tmp_path)]

    assert collected == sorted(expected, key=str.lower)


def test_iter_returns_empty_for_missing_dir(tmp_path: Path):
    assert iter_maafw_log_files(tmp_path / "debug") == []


def test_read_log_tail_returns_full_content_below_limit(tmp_path: Path):
    log = tmp_path / "maafw.log"
    log.write_bytes(b"first\nsecond\npartial")

    assert read_log_tail(log, 1024) == b"first\nsecond\npartial"


def test_read_log_tail_keeps_tail_and_drops_partial_first_line(tmp_path: Path):
    log = tmp_path / "maafw.log"
    log.write_bytes(b"AAAA\nBBBB\nCCCC\n")

    # 从末尾回退 10 字节会切在 "BBBB" 中间，按行对齐后应从 "CCCC" 开始
    assert read_log_tail(log, 10) == b"CCCC\n"
