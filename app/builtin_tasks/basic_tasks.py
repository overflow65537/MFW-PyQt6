from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
import shlex
import sys
from typing import Any


def _option_value(task_option: dict[str, Any], key: str, default: Any = None) -> Any:
    value = task_option.get(key)
    if isinstance(value, dict) and "value" in value:
        return value.get("value", default)
    return default


def _nested_value(
    task_option: dict[str, Any], key: str, field: str, default: Any = None
) -> Any:
    value = _option_value(task_option, key, {})
    if isinstance(value, dict):
        return value.get(field, default)
    return default


def _switch_enabled(task_option: dict[str, Any], key: str, default: bool = False) -> bool:
    value = str(_option_value(task_option, key, "Yes" if default else "No") or "")
    return value.strip().lower() in {"yes", "y", "true", "1", "on", "是"}


def _parse_args(args: str) -> list[str]:
    args = (args or "").strip()
    if not args:
        return []
    try:
        return shlex.split(args, posix=sys.platform != "win32")
    except ValueError:
        return [item for item in args.split() if item]


async def execute_launch_program(context, task_option: dict[str, Any]):
    program_path = str(_nested_value(task_option, "program", "path", "") or "").strip()
    program_args = str(_nested_value(task_option, "program", "args", "") or "").strip()
    wait = _switch_enabled(task_option, "wait_process", False)
    if not program_path:
        context.log("WARNING", context.tr("Builtin launch program path is empty, skipped."))
        return {"success": True, "message": "program path is empty"}
    return_code = await context.start_process(program_path, _parse_args(program_args), wait)
    if wait and return_code not in (0, None):
        return {"success": False, "message": f"process exited with {return_code}"}
    return {"success": True}


async def execute_wait_duration(context, task_option: dict[str, Any]):
    raw_seconds = _nested_value(task_option, "duration", "seconds", 1)
    try:
        seconds = max(0.0, float(raw_seconds))
    except (TypeError, ValueError):
        seconds = 1.0
    context.log("INFO", context.tr("Builtin task waits {seconds} second(s).").format(seconds=f"{seconds:g}"))
    return await context.sleep(seconds)


async def execute_wait_until(context, task_option: dict[str, Any]):
    target_text = str(_nested_value(task_option, "target_time", "time", "") or "").strip()
    if not target_text:
        context.log("WARNING", context.tr("Builtin wait-until target time is empty, skipped."))
        return True

    target = _parse_target_datetime(target_text)
    if target is None:
        context.log("ERROR", context.tr("Failed to parse builtin wait-until target time: {time}").format(time=target_text))
        return False

    seconds = max(0.0, (target - datetime.now()).total_seconds())
    context.log(
        "INFO",
        context.tr("Builtin task waits until {time}.").format(
            time=target.strftime("%Y-%m-%d %H:%M:%S")
        ),
    )
    return await context.sleep(seconds)


def _parse_target_datetime(text: str) -> datetime | None:
    now = datetime.now()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%H:%M:%S", "%H:%M"):
        try:
            parsed = datetime.strptime(text, fmt)
        except ValueError:
            continue
        if fmt.startswith("%H"):
            candidate = now.replace(
                hour=parsed.hour, minute=parsed.minute, second=parsed.second, microsecond=0
            )
            if candidate <= now:
                candidate += timedelta(days=1)
            return candidate
        return parsed
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


async def execute_system_notification(context, task_option: dict[str, Any]):
    message = str(_nested_value(task_option, "system_notice", "message", "") or "").strip()
    if not message:
        message = "MFW builtin task notification"
    message = context.tr(message)
    if _switch_enabled(task_option, "play_sound", True):
        await context.play_system_sound()
    context.notify_system(message)
    return True


async def execute_external_notification(context, task_option: dict[str, Any]):
    title = str(_nested_value(task_option, "external_notice", "title", "") or "").strip()
    text = str(_nested_value(task_option, "external_notice", "text", "") or "").strip()
    if not title:
        title = "MFW"
    if not text:
        text = "MFW builtin task external notification"
    title = context.tr(title)
    text = context.tr(text)
    context.notify_external(title, text)
    return True


def _input_option(label: str, inputs: list[dict[str, Any]], description: str = ""):
    payload: dict[str, Any] = {"type": "input", "label": label, "inputs": inputs}
    if description:
        payload["description"] = description
    return payload


def _switch_option(label: str, default: bool = False, description: str = ""):
    payload: dict[str, Any] = {
        "type": "switch",
        "label": label,
        "default_case": "Yes" if default else "No",
        "cases": [{"name": "Yes", "label": "Yes"}, {"name": "No", "label": "No"}],
    }
    if description:
        payload["description"] = description
    return payload


def get_builtin_tasks():
    return [
        {
            "key": "launch_program",
            "name": "BuiltinLaunchProgram",
            "label": "Launch Program",
            "description": "Launch an external program and optionally wait for it to exit.",
            "options": ["program", "wait_process"],
            "option_defs": {
                "program": _input_option(
                    "Program",
                    [
                        {"name": "path", "label": "Program Path", "default": ""},
                        {"name": "args", "label": "Arguments", "default": ""},
                    ],
                ),
                "wait_process": _switch_option("Wait for Process", False),
            },
            "execute": execute_launch_program,
        },
        {
            "key": "wait_duration",
            "name": "BuiltinWaitDuration",
            "label": "Wait",
            "description": "Wait for the specified number of seconds before continuing.",
            "options": ["duration"],
            "option_defs": {
                "duration": _input_option(
                    "Wait",
                    [{"name": "seconds", "label": "Seconds", "default": 5, "pipeline_type": "int"}],
                )
            },
            "execute": execute_wait_duration,
        },
        {
            "key": "wait_until",
            "name": "BuiltinWaitUntil",
            "label": "Wait Until",
            "description": "Wait until the specified time. Supports HH:MM or YYYY-MM-DD HH:MM.",
            "options": ["target_time"],
            "option_defs": {
                "target_time": _input_option(
                    "Target Time",
                    [{"name": "time", "label": "Time", "default": "23:59"}],
                )
            },
            "execute": execute_wait_until,
        },
        {
            "key": "system_notification",
            "name": "BuiltinSystemNotification",
            "label": "System Notification",
            "description": "Send a system notification and optionally play the system sound.",
            "options": ["system_notice", "play_sound"],
            "option_defs": {
                "system_notice": _input_option(
                    "System Notification",
                    [{"name": "message", "label": "Message", "default": "MFW builtin task notification"}],
                ),
                "play_sound": _switch_option("Play System Sound", True),
            },
            "execute": execute_system_notification,
        },
        {
            "key": "external_notification",
            "name": "BuiltinExternalNotification",
            "label": "External Notification",
            "description": "Send a message to all currently enabled external notification channels.",
            "options": ["external_notice"],
            "option_defs": {
                "external_notice": _input_option(
                    "External Notification",
                    [
                        {"name": "title", "label": "Title", "default": "MFW"},
                        {"name": "text", "label": "Message", "default": "MFW builtin task external notification"},
                    ],
                )
            },
            "execute": execute_external_notification,
        },
    ]
