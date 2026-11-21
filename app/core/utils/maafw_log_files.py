"""MaaFramework 日志文件命名规则与收集。

MaaFramework 的日志轮转规则随版本变过几轮：

- 活动日志：``debug/maafw.log``，运行期间一直被框架占用
- 5.12 及更早：轮转备份是固定名 ``debug/maa.bak.log``，每次轮转覆盖
- 5.13 起：改成带时间戳的 ``debug/maafw.bak.<时间戳>.log``，16 MiB 轮转；
  框架启动时还会删掉 debug 目录下超过 7 天的 ``.log`` / ``.jpg`` / ``.png``
- 6.0 起：轮转阈值提到 128 MiB，任务结束后在后台把备份压成同名的 ``.log.gz``
  （压缩过程中有短暂的 ``*.tmp``），并按 7 天 / 1 GiB 的保留策略清理日志备份、
  ``vision`` 与 ``on_error`` 图片

打包日志时按这些命名收集，并且只对未压缩的日志做「保留末尾 N MB」的截断：轮转
备份本身已经受阈值约束，gzip 文件更是二进制，按行截断会直接损坏。

（本仓库早期把备份记成 ``maafw.log.bak``，这个名字实际没人用过，仍按旧文件兼容。）
"""

from __future__ import annotations

from pathlib import Path

ACTIVE_LOG_NAME = "maafw.log"
# 历史命名：MaaFW 5.12 及更早是 maa.bak.log，MFW 早期误记的 maafw.log.bak 仍未清理
LEGACY_BACKUP_LOG_NAMES = frozenset({"maa.bak.log", "maafw.log.bak"})
ROTATED_BACKUP_PREFIX = "maafw.bak."
ROTATED_BACKUP_SUFFIXES = (".log", ".log.gz")

# 运行中被占用、体积可能超过 100 MB 的日志，打包时只保留末尾内容。
TAIL_TRIMMED_LOG_NAMES = frozenset({ACTIVE_LOG_NAME}) | LEGACY_BACKUP_LOG_NAMES


def is_maafw_log_name(name: str) -> bool:
    """判断文件名是否属于 MaaFW 日志（活动日志、旧备份或新轮转备份）。"""
    if name in TAIL_TRIMMED_LOG_NAMES:
        return True
    if not name.startswith(ROTATED_BACKUP_PREFIX):
        return False
    return name.endswith(ROTATED_BACKUP_SUFFIXES)


def is_maafw_backup_name(name: str) -> bool:
    """判断文件名是否为 MaaFW 轮转备份（旧命名或新命名）。"""
    return name != ACTIVE_LOG_NAME and is_maafw_log_name(name)


def should_tail_trim(name: str) -> bool:
    """只有未压缩的活动日志才做末尾截断，避免破坏 gzip 备份。"""
    return name in TAIL_TRIMMED_LOG_NAMES


def iter_maafw_log_files(debug_dir: Path) -> list[Path]:
    """按文件名排序列出 debug 目录下的全部 MaaFW 日志文件。

    跳过压缩过程中的 ``*.tmp`` 临时文件，也跳过目录。
    """
    if not debug_dir.is_dir():
        return []
    files = [
        path
        for path in debug_dir.iterdir()
        if path.is_file() and is_maafw_log_name(path.name)
    ]
    files.sort(key=lambda path: path.name.lower())
    return files


def read_log_tail(path: Path, max_bytes: int) -> bytes:
    """读取日志内容；超过 ``max_bytes`` 时只保留末尾部分并按行对齐。

    用于活动日志（可能被框架占用且体积很大）。轮转备份与 ``.log.gz`` 不要走这里，
    否则 gzip 会被截断损坏。
    """
    size = path.stat().st_size
    with path.open("rb") as handle:
        truncated = size > max_bytes
        if truncated:
            handle.seek(size - max_bytes)
            data = handle.read(max_bytes)
        else:
            data = handle.read()
    if truncated:
        newline_index = data.find(b"\n")
        if newline_index != -1:
            data = data[newline_index + 1 :]
    return data
