from __future__ import annotations

import shlex
import subprocess
from typing import TYPE_CHECKING

from app.utils.install_paths import resolve_schedule_launch_command
from app.utils.logger import logger

if TYPE_CHECKING:
    from app.core.service.schedule_service import ScheduleEntry

MFW_CRON_BEGIN = "# BEGIN MFW-ChainFlow Assistant schedules"
MFW_CRON_END = "# END MFW-ChainFlow Assistant schedules"
MFW_CRON_ENTRY_PREFIX = "# mfw-schedule:"


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


def split_crontab(content: str) -> tuple[list[str], dict[str, list[str]]]:
    """拆分 crontab 为 MFW 块外的行与 entry_id -> 任务行列表。"""
    preserved_before: list[str] = []
    preserved_after: list[str] = []
    managed: dict[str, list[str]] = {}

    in_block = False
    after_block = False
    current_entry: str | None = None

    for raw_line in content.splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
        if stripped == MFW_CRON_BEGIN:
            in_block = True
            current_entry = None
            continue
        if stripped == MFW_CRON_END:
            in_block = False
            after_block = True
            current_entry = None
            continue
        if not in_block:
            if after_block:
                preserved_after.append(line)
            else:
                preserved_before.append(line)
            continue
        if line.startswith(MFW_CRON_ENTRY_PREFIX):
            current_entry = line[len(MFW_CRON_ENTRY_PREFIX) :].strip()
            if current_entry:
                managed[current_entry] = []
            continue
        if current_entry and stripped:
            managed[current_entry].append(line)

    preserved = [line for line in preserved_before + preserved_after if line.strip()]
    return preserved, managed


def render_crontab(preserved_lines: list[str], managed: dict[str, list[str]]) -> str:
    lines: list[str] = list(preserved_lines)
    if lines and lines[-1].strip():
        lines.append("")
    lines.append(MFW_CRON_BEGIN)
    for entry_id in sorted(managed):
        lines.append(entry_marker(entry_id))
        lines.extend(managed[entry_id])
    lines.append(MFW_CRON_END)
    return "\n".join(lines) + "\n"


def list_managed_entry_ids(content: str) -> set[str]:
    _, managed = split_crontab(content)
    return set(managed)


def build_managed_lines(entry: "ScheduleEntry") -> list[str]:
    from app.core.service.system_scheduler.cron_expr import build_cron_schedule_lines

    job = build_shell_job(entry.config_id, force_start=entry.force_start)
    schedule_lines = build_cron_schedule_lines(entry)
    return [f"{schedule} {job}" for schedule in schedule_lines]
