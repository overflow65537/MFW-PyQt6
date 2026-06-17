from __future__ import annotations

import subprocess
import tempfile
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING
from xml.dom import minidom

from app.core.service.schedule_service import (
    SCHEDULE_DAILY,
    SCHEDULE_MONTHLY,
    SCHEDULE_SINGLE,
    SCHEDULE_WEEKLY,
    _parse_iso,
)
from app.core.service.system_scheduler.base import SystemSchedulerBackend
from app.utils.install_paths import resolve_schedule_launch_command
from app.utils.logger import logger

if TYPE_CHECKING:
    from app.core.service.schedule_service import ScheduleEntry

TASK_FOLDER = "MFW-ChainFlow Assistant"
_TASK_NS = "http://schemas.microsoft.com/windows/2004/02/mit/task"
ET.register_namespace("", _TASK_NS)


def task_full_name(entry_id: str) -> str:
    return f"\\{TASK_FOLDER}\\{entry_id}"


_WEEKDAY_NAMES = (
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
)
_MONTH_NAMES = (
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
)


def _append_weekday_elements(parent: ET.Element, weekdays: list[int]) -> None:
    days = ET.SubElement(parent, f"{{{_TASK_NS}}}DaysOfWeek")
    for weekday in sorted({int(value) % 7 for value in weekdays}):
        ET.SubElement(days, f"{{{_TASK_NS}}}{_WEEKDAY_NAMES[weekday]}")


def _append_month_elements(parent: ET.Element, month_value: int) -> None:
    months = ET.SubElement(parent, f"{{{_TASK_NS}}}Months")
    month_indexes = range(1, 13) if int(month_value) <= 0 else [int(month_value)]
    for month in month_indexes:
        ET.SubElement(months, f"{{{_TASK_NS}}}{_MONTH_NAMES[(month - 1) % 12]}")


def _format_start_boundary(value: datetime) -> str:
    return value.replace(second=0, microsecond=0).strftime("%Y-%m-%dT%H:%M:%S")


def _append_text(parent: ET.Element, tag: str, text: str) -> None:
    element = ET.SubElement(parent, tag)
    element.text = text


def build_task_xml(entry: "ScheduleEntry") -> str:
    """生成 Windows 任务计划程序 XML（与 schtasks 导出的 1.2 格式对齐）。"""
    command, arguments = resolve_schedule_launch_command(
        entry.config_id, force_start=entry.force_start
    )

    root = ET.Element(f"{{{_TASK_NS}}}Task")
    root.set("version", "1.2")

    registration = ET.SubElement(root, f"{{{_TASK_NS}}}RegistrationInfo")
    _append_text(registration, f"{{{_TASK_NS}}}Description", f"MFW schedule: {entry.name}")

    principals = ET.SubElement(root, f"{{{_TASK_NS}}}Principals")
    principal = ET.SubElement(principals, f"{{{_TASK_NS}}}Principal", id="Author")
    _append_text(principal, f"{{{_TASK_NS}}}LogonType", "InteractiveToken")

    settings = ET.SubElement(root, f"{{{_TASK_NS}}}Settings")
    _append_text(settings, f"{{{_TASK_NS}}}DisallowStartIfOnBatteries", "true")
    _append_text(settings, f"{{{_TASK_NS}}}StopIfGoingOnBatteries", "true")
    _append_text(settings, f"{{{_TASK_NS}}}MultipleInstancesPolicy", "IgnoreNew")
    idle_settings = ET.SubElement(settings, f"{{{_TASK_NS}}}IdleSettings")
    _append_text(idle_settings, f"{{{_TASK_NS}}}Duration", "PT10M")
    _append_text(idle_settings, f"{{{_TASK_NS}}}WaitTimeout", "PT1H")
    _append_text(idle_settings, f"{{{_TASK_NS}}}StopOnIdleEnd", "true")
    _append_text(idle_settings, f"{{{_TASK_NS}}}RestartOnIdle", "false")

    triggers = ET.SubElement(root, f"{{{_TASK_NS}}}Triggers")
    _append_trigger(triggers, entry)

    actions = ET.SubElement(root, f"{{{_TASK_NS}}}Actions", Context="Author")
    exec_action = ET.SubElement(actions, f"{{{_TASK_NS}}}Exec")
    _append_text(exec_action, f"{{{_TASK_NS}}}Command", command)
    _append_text(exec_action, f"{{{_TASK_NS}}}Arguments", arguments)

    rough = ET.tostring(root, encoding="unicode")
    parsed = minidom.parseString(rough)
    return parsed.toprettyxml(indent="  ")


def _append_trigger(triggers: ET.Element, entry: "ScheduleEntry") -> None:
    params = entry.params
    schedule_type = entry.schedule_type

    if schedule_type == SCHEDULE_SINGLE:
        run_at = _parse_iso(params.get("run_at"))
        if run_at is None:
            raise ValueError("single schedule missing run_at")
        trigger = ET.SubElement(triggers, f"{{{_TASK_NS}}}TimeTrigger")
        _append_text(trigger, f"{{{_TASK_NS}}}StartBoundary", _format_start_boundary(run_at))
        return

    start_at = _parse_iso(params.get("start_at")) or datetime.now()
    hour = int(params.get("hour", start_at.hour))
    minute = int(params.get("minute", start_at.minute))
    start_boundary = start_at.replace(hour=hour, minute=minute, second=0, microsecond=0)
    boundary = _format_start_boundary(start_boundary)

    if schedule_type == SCHEDULE_DAILY:
        interval = max(1, int(params.get("interval_days", 1)))
        trigger = ET.SubElement(triggers, f"{{{_TASK_NS}}}CalendarTrigger")
        _append_text(trigger, f"{{{_TASK_NS}}}StartBoundary", boundary)
        schedule = ET.SubElement(trigger, f"{{{_TASK_NS}}}ScheduleByDay")
        _append_text(schedule, f"{{{_TASK_NS}}}DaysInterval", str(interval))
        return

    if schedule_type == SCHEDULE_WEEKLY:
        interval = max(1, int(params.get("interval_weeks", 1) or 1))
        weekdays = sorted({int(w) % 7 for w in params.get("weekdays", [])})
        if not weekdays:
            weekdays = [start_at.weekday()]
        trigger = ET.SubElement(triggers, f"{{{_TASK_NS}}}CalendarTrigger")
        _append_text(trigger, f"{{{_TASK_NS}}}StartBoundary", boundary)
        schedule = ET.SubElement(trigger, f"{{{_TASK_NS}}}ScheduleByWeek")
        _append_text(schedule, f"{{{_TASK_NS}}}WeeksInterval", str(interval))
        _append_weekday_elements(schedule, weekdays)
        return

    if schedule_type == SCHEDULE_MONTHLY:
        month_value = int(params.get("month", 0))
        ordinal = params.get("ordinal")
        weekday = params.get("weekday")
        trigger = ET.SubElement(triggers, f"{{{_TASK_NS}}}CalendarTrigger")
        _append_text(trigger, f"{{{_TASK_NS}}}StartBoundary", boundary)
        if ordinal is not None and weekday is not None:
            schedule = ET.SubElement(trigger, f"{{{_TASK_NS}}}ScheduleByMonthDayOfWeek")
            weeks = ET.SubElement(schedule, f"{{{_TASK_NS}}}Weeks")
            if int(ordinal) >= 4:
                week_value = "Last"
            else:
                week_value = str(int(ordinal) + 1)
            ET.SubElement(weeks, f"{{{_TASK_NS}}}Week").text = week_value
            _append_weekday_elements(schedule, [int(weekday)])
            _append_month_elements(schedule, month_value)
        else:
            day = int(params.get("month_day", start_at.day))
            schedule = ET.SubElement(trigger, f"{{{_TASK_NS}}}ScheduleByMonth")
            _append_month_elements(schedule, month_value)
            days = ET.SubElement(schedule, f"{{{_TASK_NS}}}DaysOfMonth")
            ET.SubElement(days, f"{{{_TASK_NS}}}Day").text = str(day)
        return

    raise ValueError(f"unsupported schedule type: {schedule_type}")


class WindowsTaskSchedulerBackend(SystemSchedulerBackend):
    """通过 schtasks 将计划任务注册到 Windows 任务计划程序。"""

    @property
    def is_supported(self) -> bool:
        return True

    def install(self, entry: "ScheduleEntry") -> bool:
        task_name = task_full_name(entry.entry_id)
        try:
            xml_content = build_task_xml(entry)
        except Exception as exc:
            logger.exception("生成 Windows 计划任务 XML 失败 [%s]: %s", entry.entry_id, exc)
            return False

        temp_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-16",
                suffix=".xml",
                delete=False,
            ) as handle:
                handle.write(xml_content)
                temp_path = Path(handle.name)

            result = subprocess.run(
                ["schtasks", "/Create", "/TN", task_name, "/XML", str(temp_path), "/F"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=60,
                check=False,
            )
            if result.returncode != 0:
                detail = (result.stderr or result.stdout or "").strip()
                logger.warning(
                    "注册 Windows 计划任务失败 [%s]: %s",
                    entry.entry_id,
                    detail or f"exit {result.returncode}",
                )
                return False
            logger.info("已注册 Windows 计划任务: %s", task_name)
            return True
        except Exception as exc:
            logger.exception("注册 Windows 计划任务异常 [%s]: %s", entry.entry_id, exc)
            return False
        finally:
            if temp_path is not None:
                temp_path.unlink(missing_ok=True)

    def remove(self, entry_id: str) -> bool:
        return self._run_change(["/Delete", "/TN", task_full_name(entry_id), "/F"], entry_id, "删除")

    def set_enabled(self, entry_id: str, enabled: bool) -> bool:
        flag = "/ENABLE" if enabled else "/DISABLE"
        return self._run_change(["/Change", "/TN", task_full_name(entry_id), flag], entry_id, "更新状态")

    def sync_all(self, entries: list["ScheduleEntry"]) -> None:
        known_ids = {entry.entry_id for entry in entries}
        for entry in entries:
            if entry.enabled:
                self.install(entry)
            else:
                self.set_enabled(entry.entry_id, False)

        for orphan_id in self._list_registered_entry_ids() - known_ids:
            self.remove(orphan_id)

    def _list_registered_entry_ids(self) -> set[str]:
        script = (
            f"Get-ScheduledTask -TaskPath '\\{TASK_FOLDER}\\' -ErrorAction SilentlyContinue "
            "| ForEach-Object { $_.TaskName }"
        )
        try:
            result = subprocess.run(
                ["powershell", "-NoProfile", "-NonInteractive", "-Command", script],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=30,
                check=False,
            )
        except Exception as exc:
            logger.warning("列举 Windows 计划任务失败: %s", exc)
            return set()

        if result.returncode != 0:
            detail = (result.stderr or result.stdout or "").strip()
            if detail:
                logger.warning("列举 Windows 计划任务失败: %s", detail)
            return set()

        return {line.strip() for line in result.stdout.splitlines() if line.strip()}

    def _run_change(self, args: list[str], entry_id: str, action: str) -> bool:
        task_name = task_full_name(entry_id)
        try:
            result = subprocess.run(
                ["schtasks", *args],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=60,
                check=False,
            )
            if result.returncode != 0:
                detail = (result.stderr or result.stdout or "").strip()
                if "cannot find" in detail.lower() or "找不到" in detail:
                    return True
                logger.warning(
                    "%s Windows 计划任务失败 [%s]: %s",
                    action,
                    entry_id,
                    detail or f"exit {result.returncode}",
                )
                return False
            return True
        except Exception as exc:
            logger.exception("%s Windows 计划任务异常 [%s]: %s", action, entry_id, exc)
            return False
