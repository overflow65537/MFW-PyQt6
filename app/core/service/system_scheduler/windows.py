from __future__ import annotations

import re
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any
from xml.dom import minidom

from app.core.service.schedule_service import (
    SCHEDULE_DAILY,
    SCHEDULE_MONTHLY,
    SCHEDULE_SINGLE,
    SCHEDULE_WEEKLY,
    ScheduleEntry,
    _parse_iso,
)
from app.core.service.system_scheduler.base import SystemSchedulerBackend
from app.utils.install_paths import (
    resolve_schedule_launch_command,
    resolve_schedule_task_folder,
)
from app.utils.logger import logger
from app.utils.subprocess_helper import hidden_subprocess_kwargs

if TYPE_CHECKING:
    from app.core.service.schedule_service import ScheduleEntry

LEGACY_TASK_FOLDER = "MFW-ChainFlow Assistant"
_TASK_NS = "http://schemas.microsoft.com/windows/2004/02/mit/task"
ET.register_namespace("", _TASK_NS)


def task_folder() -> str:
    return resolve_schedule_task_folder()


def task_full_name(entry_id: str) -> str:
    return f"\\{task_folder()}\\{entry_id}"


def _subprocess_text_encoding() -> str:
    if sys.platform == "win32":
        import locale

        return locale.getpreferredencoding(False) or "utf-8"
    return "utf-8"


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
    if entry.run_elevated:
        _append_text(principal, f"{{{_TASK_NS}}}RunLevel", "HighestAvailable")

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
                encoding=_subprocess_text_encoding(),
                errors="replace",
                timeout=60,
                check=False,
                **hidden_subprocess_kwargs(),
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

        for orphan_id in self._list_registered_entry_ids(task_folder()) - known_ids:
            self.remove(orphan_id)

        self._migrate_legacy_tasks(entries)

    def list_all_entries(self) -> list["ScheduleEntry"]:
        entry_ids = self._list_registered_entry_ids(task_folder())
        if not entry_ids:
            return []
        info_map = self._fetch_tasks_info(entry_ids)
        entries: list[ScheduleEntry] = []
        for entry_id in sorted(entry_ids):
            xml_str = self._get_task_xml(entry_id)
            if not xml_str:
                continue
            entry = self._parse_task_xml(entry_id, xml_str)
            if entry is None:
                continue
            info = info_map.get(entry_id, {})
            entry.enabled = info.get("enabled", True)
            entry.next_run = info.get("next_run")
            entry.last_run = info.get("last_run")
            entries.append(entry)
        return entries

    def _fetch_tasks_info(self, entry_ids: set[str]) -> dict[str, dict]:
        folder_name = task_folder()
        names = ", ".join(f"'{e}'" for e in entry_ids)
        script = (
            f"Get-ScheduledTask -TaskPath '\\{folder_name}\\' "
            f"| Where-Object {{ $_.TaskName -in @({names}) }} "
            "| ForEach-Object { "
            "$t = $_; "
            "$info = $t | Get-ScheduledTaskInfo -ErrorAction SilentlyContinue; "
            "$enabled = ($t.State -ne 'Disabled'); "
            "$nextRun = if ($info.NextRunTime) { $info.NextRunTime.ToString('o') } else { '' }; "
            "$lastRun = if ($info.LastRunTime -and $info.LastRunTime -ne [datetime]::MinValue) { $info.LastRunTime.ToString('o') } else { '' }; "
            "Write-Output (\"$($t.TaskName)|$enabled|$nextRun|$lastRun\") }"
        )
        info_map: dict[str, dict] = {}
        try:
            result = subprocess.run(
                ["powershell", "-NoProfile", "-NonInteractive", "-Command", script],
                capture_output=True,
                text=True,
                encoding=_subprocess_text_encoding(),
                errors="replace",
                timeout=30,
                check=False,
                **hidden_subprocess_kwargs(),
            )
            if result.returncode == 0:
                for line in result.stdout.splitlines():
                    line = line.strip()
                    if not line or "|" not in line:
                        continue
                    parts = line.split("|", 3)
                    if len(parts) < 4:
                        continue
                    tid, enabled_str, next_str, last_str = parts
                    info_map[tid] = {
                        "enabled": enabled_str.lower() == "true",
                        "next_run": _parse_iso(next_str) if next_str else None,
                        "last_run": _parse_iso(last_str) if last_str else None,
                    }
        except Exception as exc:
            logger.warning("获取计划任务状态失败: %s", exc)
        return info_map

    def _get_task_xml(self, entry_id: str) -> str | None:
        task_name = task_full_name(entry_id)
        try:
            result = subprocess.run(
                ["schtasks", "/Query", "/XML", "/TN", task_name],
                capture_output=True,
                text=True,
                encoding=_subprocess_text_encoding(),
                errors="replace",
                timeout=30,
                check=False,
                **hidden_subprocess_kwargs(),
            )
            if result.returncode != 0:
                return None
            return result.stdout
        except Exception as exc:
            logger.warning("获取任务 XML 失败 [%s]: %s", entry_id, exc)
            return None

    def _parse_task_xml(self, entry_id: str, xml_str: str) -> ScheduleEntry | None:
        try:
            root = ET.fromstring(xml_str)
        except ET.ParseError as exc:
            logger.warning("解析任务 XML 失败 [%s]: %s", entry_id, exc)
            return None

        ns = _TASK_NS
        def tag(name: str) -> str:
            return f"{{{ns}}}{name}"

        def text(elem: ET.Element | None, default: str = "") -> str:
            return (elem.text or "").strip() if elem is not None else default

        description = text(root.find(f".//{tag('Description')}"))
        name = description.removeprefix("MFW schedule: ") if description else ""

        args_str = text(root.find(f".//{tag('Arguments')}"))
        config_id = ""
        force_start = False
        if args_str:
            match = re.search(r"--config-id=(\S+)", args_str)
            if match:
                config_id = match.group(1)
            force_start = "--force-restart" in args_str

        run_elevated = False
        run_level = text(root.find(f".//{tag('RunLevel')}"))
        if run_level == "HighestAvailable":
            run_elevated = True

        created_at = datetime.now()
        date_str = text(root.find(f".//{tag('Date')}"))
        if date_str:
            parsed = _parse_iso(date_str)
            if parsed:
                created_at = parsed

        schedule_type = SCHEDULE_SINGLE
        params: dict[str, Any] = {}

        trigger = root.find(f".//{tag('TimeTrigger')}")
        if trigger is not None:
            start = text(trigger.find(tag('StartBoundary')))
            if start:
                params["run_at"] = start
            schedule_type = SCHEDULE_SINGLE
        else:
            trigger = root.find(f".//{tag('CalendarTrigger')}")
            if trigger is not None:
                start = text(trigger.find(tag('StartBoundary')))
                start_dt = _parse_iso(start) if start else datetime.now()
                if start_dt:
                    params["start_at"] = start_dt.isoformat()
                    params["hour"] = start_dt.hour
                    params["minute"] = start_dt.minute

                if trigger.find(f".//{tag('ScheduleByDay')}") is not None:
                    schedule_type = SCHEDULE_DAILY
                    interval = text(trigger.find(f".//{tag('DaysInterval')}"), "1")
                    params["interval_days"] = int(interval)
                elif trigger.find(f".//{tag('ScheduleByWeek')}") is not None:
                    schedule_type = SCHEDULE_WEEKLY
                    weeks = text(trigger.find(f".//{tag('WeeksInterval')}"), "1")
                    params["interval_weeks"] = int(weeks)
                    weekdays = []
                    for day_elem in trigger.findall(f".//{tag('DaysOfWeek')}/*"):
                        if day_elem.tag == f"{{{ns}}}DaysOfWeek":
                            continue
                        day_name = day_elem.tag.split("}")[-1]
                        if day_name in _WEEKDAY_NAMES:
                            weekdays.append(_WEEKDAY_NAMES.index(day_name))
                    params["weekdays"] = weekdays
                elif trigger.find(f".//{tag('ScheduleByMonthDayOfWeek')}") is not None:
                    schedule_type = SCHEDULE_MONTHLY
                    week_elem = trigger.find(f".//{tag('Week')}")
                    ordinal = 0
                    if week_elem is not None:
                        w = text(week_elem)
                        if w.lower() == "last":
                            ordinal = 4
                        else:
                            ordinal = max(0, int(w) - 1)
                    params["ordinal"] = ordinal
                    for day_elem in trigger.findall(f".//{tag('DaysOfWeek')}/*"):
                        day_name = day_elem.tag.split("}")[-1]
                        if day_name in _WEEKDAY_NAMES:
                            params["weekday"] = _WEEKDAY_NAMES.index(day_name)
                            break
                    month_elem = trigger.find(f".//{tag('Months')}")
                    if month_elem is not None:
                        for m_elem in month_elem:
                            m_name = m_elem.tag.split("}")[-1]
                            if m_name in _MONTH_NAMES:
                                params["month"] = _MONTH_NAMES.index(m_name) + 1
                                break
                    if "month" not in params:
                        params["month"] = 0
                elif trigger.find(f".//{tag('ScheduleByMonth')}") is not None:
                    schedule_type = SCHEDULE_MONTHLY
                    day_elem = trigger.find(f".//{tag('Day')}")
                    if day_elem is not None:
                        params["month_day"] = int(text(day_elem, "1"))
                    month_elem = trigger.find(f".//{tag('Months')}")
                    if month_elem is not None:
                        for m_elem in month_elem:
                            m_name = m_elem.tag.split("}")[-1]
                            if m_name in _MONTH_NAMES:
                                params["month"] = _MONTH_NAMES.index(m_name) + 1
                                break
                    if "month" not in params:
                        params["month"] = 0

        return ScheduleEntry(
            entry_id=entry_id,
            config_id=config_id,
            name=name or config_id,
            schedule_type=schedule_type,
            params=params,
            force_start=force_start,
            run_elevated=run_elevated,
            enabled=True,
            created_at=created_at,
        )

    def _migrate_legacy_tasks(self, entries: list["ScheduleEntry"]) -> None:
        """将旧版全局任务文件夹中的本实例计划迁移到按安装路径隔离的文件夹。"""
        legacy_ids = self._list_registered_entry_ids(LEGACY_TASK_FOLDER)
        if not legacy_ids:
            return

        for entry in entries:
            if not entry.enabled or entry.entry_id not in legacy_ids:
                continue
            if self.install(entry):
                self._run_change(
                    ["/Delete", "/TN", f"\\{LEGACY_TASK_FOLDER}\\{entry.entry_id}", "/F"],
                    entry.entry_id,
                    "迁移后删除旧版",
                )

    def _list_registered_entry_ids(self, folder: str | None = None) -> set[str]:
        folder_name = folder or task_folder()
        script = (
            f"Get-ScheduledTask -TaskPath '\\{folder_name}\\' -ErrorAction SilentlyContinue "
            "| ForEach-Object { $_.TaskName }"
        )
        try:
            result = subprocess.run(
                ["powershell", "-NoProfile", "-NonInteractive", "-Command", script],
                capture_output=True,
                text=True,
                encoding=_subprocess_text_encoding(),
                errors="replace",
                timeout=30,
                check=False,
                **hidden_subprocess_kwargs(),
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
                encoding=_subprocess_text_encoding(),
                errors="replace",
                timeout=60,
                check=False,
                **hidden_subprocess_kwargs(),
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
