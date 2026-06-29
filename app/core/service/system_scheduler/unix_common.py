from __future__ import annotations

import re
import shlex
import subprocess
from typing import TYPE_CHECKING

from app.utils.install_paths import (
    resolve_schedule_instance_id,
    resolve_schedule_launch_command,
)
from app.utils.logger import logger
from app.utils.subprocess_helper import hidden_subprocess_kwargs

if TYPE_CHECKING:
    from app.core.service.schedule_service import ScheduleEntry

MFW_CRON_BEGIN = "# BEGIN MFW-ChainFlow Assistant schedules"
MFW_CRON_END = "# END MFW-ChainFlow Assistant schedules"
MFW_CRON_ENTRY_PREFIX = "# mfw-schedule:"
_MFW_CRON_BEGIN_RE = re.compile(
    r"^# BEGIN MFW-ChainFlow Assistant schedules(?: \(([0-9a-f]{8})\))?$"
)


def mfw_cron_begin(instance_id: str) -> str:
    return f"{MFW_CRON_BEGIN} ({instance_id})"


def mfw_cron_end(instance_id: str) -> str:
    return f"{MFW_CRON_END} ({instance_id})"


def current_schedule_instance_id() -> str:
    return resolve_schedule_instance_id()


def build_shell_job(config_id: str, *, force_start: bool) -> str:
    """构建可在 shell/cron 中执行的 MFW 启动命令。"""
    executable, arguments = resolve_schedule_launch_command(
        config_id, force_start=force_start
    )
    return f"{shlex.quote(executable)} {arguments}"


def entry_marker(entry_id: str) -> str:
    return f"{MFW_CRON_ENTRY_PREFIX}{entry_id}"


def read_user_crontab() -> str:
    try:
        result = subprocess.run(
            ["crontab", "-l"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
            check=False,
            **hidden_subprocess_kwargs(),
        )
    except FileNotFoundError:
        logger.warning("未找到 crontab 命令，无法管理系统计划任务")
        return ""
    except Exception as exc:
        logger.warning("读取 crontab 失败: %s", exc)
        return ""

    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip().lower()
        if "no crontab" in detail or "cannot open" in detail:
            return ""
        logger.warning("读取 crontab 失败: %s", (result.stderr or result.stdout or "").strip())
        return ""
    return result.stdout


def write_user_crontab(content: str) -> bool:
    payload = content if content.endswith("\n") else f"{content}\n"
    try:
        result = subprocess.run(
            ["crontab", "-"],
            input=payload,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
            check=False,
            **hidden_subprocess_kwargs(),
        )
    except FileNotFoundError:
        logger.warning("未找到 crontab 命令，无法写入系统计划任务")
        return False
    except Exception as exc:
        logger.exception("写入 crontab 异常: %s", exc)
        return False

    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        logger.warning("写入 crontab 失败: %s", detail or f"exit {result.returncode}")
        return False
    return True


def _parse_block_begin(line: str) -> str | None:
    match = _MFW_CRON_BEGIN_RE.match(line.strip())
    if not match:
        return None
    return match.group(1) or ""


def split_crontab(content: str) -> tuple[list[str], dict[str, list[str]]]:
    """拆分 crontab 为 MFW 块外的行与 entry_id -> 任务行列表（当前实例或首个块，兼容旧 API）。"""
    preserved, blocks = split_crontab_blocks(content)
    instance_id = current_schedule_instance_id()
    if instance_id in blocks:
        return preserved, blocks[instance_id]
    if "" in blocks:
        return preserved, blocks[""]
    if blocks:
        first_block = next(iter(blocks.values()))
        return preserved, first_block
    return preserved, {}


def split_crontab_blocks(
    content: str,
) -> tuple[list[str], dict[str, dict[str, list[str]]]]:
    """拆分 crontab 为 MFW 块外的行与各安装实例 entry_id -> 任务行列表。"""
    preserved: list[str] = []
    blocks: dict[str, dict[str, list[str]]] = {}

    in_block = False
    current_instance: str | None = None
    current_entry: str | None = None

    for raw_line in content.splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
        block_instance = _parse_block_begin(stripped)
        if block_instance is not None:
            in_block = True
            current_instance = block_instance
            blocks.setdefault(current_instance, {})
            current_entry = None
            continue
        if stripped == MFW_CRON_END or (
            current_instance
            and stripped == mfw_cron_end(current_instance)
        ):
            in_block = False
            current_instance = None
            current_entry = None
            continue
        if not in_block:
            if stripped:
                preserved.append(line)
            continue
        if line.startswith(MFW_CRON_ENTRY_PREFIX):
            current_entry = line[len(MFW_CRON_ENTRY_PREFIX) :].strip()
            if current_entry and current_instance is not None:
                blocks.setdefault(current_instance, {}).setdefault(current_entry, [])
            continue
        if current_entry and current_instance is not None and stripped:
            blocks.setdefault(current_instance, {}).setdefault(current_entry, []).append(
                line
            )

    return preserved, blocks


def render_crontab(
    preserved_lines: list[str],
    managed: dict[str, list[str]],
    *,
    instance_id: str | None = None,
) -> str:
    instance = instance_id if instance_id is not None else current_schedule_instance_id()
    return render_crontab_blocks(preserved_lines, {instance: managed})


def render_crontab_blocks(
    preserved_lines: list[str],
    blocks: dict[str, dict[str, list[str]]],
) -> str:
    lines: list[str] = list(preserved_lines)
    if lines and lines[-1].strip():
        lines.append("")

    for instance_id in sorted(blocks):
        managed = blocks[instance_id]
        if not managed:
            continue
        begin = MFW_CRON_BEGIN if instance_id == "" else mfw_cron_begin(instance_id)
        end = MFW_CRON_END if instance_id == "" else mfw_cron_end(instance_id)
        lines.append(begin)
        for entry_id in sorted(managed):
            lines.append(entry_marker(entry_id))
            lines.extend(managed[entry_id])
        lines.append(end)

    return "\n".join(lines) + "\n"


def list_managed_entry_ids(content: str) -> set[str]:
    _, managed = split_crontab(content)
    return set(managed)


def build_managed_lines(entry: "ScheduleEntry") -> list[str]:
    from app.core.service.system_scheduler.cron_expr import build_cron_schedule_lines

    job = build_shell_job(entry.config_id, force_start=entry.force_start)
    schedule_lines = build_cron_schedule_lines(entry)
    return [f"{schedule} {job}" for schedule in schedule_lines]
