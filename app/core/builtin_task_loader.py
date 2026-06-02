from __future__ import annotations

import importlib
import inspect
import pkgutil
from dataclasses import dataclass
from types import ModuleType
from typing import Any, Awaitable, Callable

from app.core.service.i18n_service import I18nService
from app.utils.logger import logger


TASK_SOURCE_BUILTIN = "builtin"
TASK_SOURCE_RESOURCE = "resource"
BUILTIN_TASK_GROUP_NAME = "__mfw_builtin_tasks__"
BUILTIN_TASK_GROUP_LABEL = "$builtin_group_label"


class BuiltinTaskError(RuntimeError):
    """Raised when a builtin task cannot be loaded or executed."""


@dataclass(slots=True)
class BuiltinTaskResult:
    success: bool = True
    message: str = ""

    @classmethod
    def from_value(cls, value: Any) -> "BuiltinTaskResult":
        if isinstance(value, cls):
            return value
        if isinstance(value, bool):
            return cls(success=value)
        if isinstance(value, dict):
            return cls(
                success=bool(value.get("success", True)),
                message=str(value.get("message", "") or ""),
            )
        if value is None:
            return cls()
        return cls(success=bool(value), message=str(value))


class BuiltinTaskContext:
    """Controlled capabilities exposed to external builtin task modules."""

    def __init__(
        self,
        *,
        log: Callable[[str, str], None],
        sleep: Callable[[float], Awaitable[bool]],
        is_stopping: Callable[[], bool],
        notify_system: Callable[[str], None],
        notify_external: Callable[[str, str], None],
        start_process: Callable[[str, list[str] | str | None, bool], Awaitable[int | None]],
        play_system_sound: Callable[[], Awaitable[None]],
        tr: Callable[[str], str] | None = None,
    ):
        self._log = log
        self._sleep = sleep
        self._is_stopping = is_stopping
        self._notify_system = notify_system
        self._notify_external = notify_external
        self._start_process = start_process
        self._play_system_sound = play_system_sound
        self._tr = tr or (lambda text: text)

    def log(self, level: str, text: str) -> None:
        self._log(level, text)

    async def sleep(self, seconds: float) -> bool:
        return await self._sleep(seconds)

    def is_stopping(self) -> bool:
        return self._is_stopping()

    def notify_system(self, message: str) -> None:
        self._notify_system(message)

    def notify_external(self, title: str, text: str) -> None:
        self._notify_external(title, text)

    async def start_process(
        self, path: str, args: list[str] | str | None = None, wait: bool = False
    ) -> int | None:
        return await self._start_process(path, args, wait)

    async def play_system_sound(self) -> None:
        await self._play_system_sound()

    def tr(self, text: str) -> str:
        return self._tr(text)


@dataclass(slots=True)
class BuiltinTaskDefinition:
    key: str
    name: str
    label: str
    description: str
    options: list[str]
    option_defs: dict[str, dict[str, Any]]
    execute: Callable[[BuiltinTaskContext, dict[str, Any]], Any]
    icon: str = ""

    @classmethod
    def from_mapping(cls, payload: dict[str, Any]) -> "BuiltinTaskDefinition":
        key = str(payload.get("key", "") or "").strip()
        name = str(payload.get("name", "") or "").strip()
        if not key:
            raise BuiltinTaskError("builtin task key is empty")
        if not name:
            raise BuiltinTaskError(f"builtin task '{key}' name is empty")

        execute = payload.get("execute")
        if not callable(execute):
            raise BuiltinTaskError(f"builtin task '{key}' execute is not callable")

        raw_options = payload.get("options", [])
        if isinstance(raw_options, str):
            options = [raw_options]
        elif isinstance(raw_options, list):
            options = [item for item in raw_options if isinstance(item, str) and item]
        else:
            options = []

        raw_option_defs = payload.get("option_defs", {})
        option_defs = raw_option_defs if isinstance(raw_option_defs, dict) else {}
        missing_options = [name for name in options if name not in option_defs]
        if missing_options:
            raise BuiltinTaskError(
                f"builtin task '{key}' references missing options: {missing_options}"
            )

        label = str(payload.get("label", "") or name)
        description = str(payload.get("description", "") or "")
        icon = str(payload.get("icon", "") or "")
        return cls(
            key=key,
            name=name,
            label=label,
            description=description,
            options=options,
            option_defs=option_defs,
            execute=execute,
            icon=icon,
        )

    def to_interface_task(self) -> dict[str, Any]:
        task_def: dict[str, Any] = {
            "name": self.name,
            "label": self.label,
            "description": self.description,
            "option": list(self.options),
            "group": BUILTIN_TASK_GROUP_NAME,
            "task_source": TASK_SOURCE_BUILTIN,
            "builtin": True,
            "builtin_key": self.key,
            "default_check": True,
        }
        if self.icon:
            task_def["icon"] = self.icon
        return task_def


class BuiltinTaskLoader:
    """Loads self-describing builtin task modules outside app.core."""

    def __init__(
        self,
        package_name: str = "app.builtin_tasks",
        *,
        i18n_service: I18nService | None = None,
    ):
        self.package_name = package_name
        self.i18n_service = i18n_service or I18nService()
        self._tasks_by_key: dict[str, BuiltinTaskDefinition] = {}
        self._tasks_by_name: dict[str, BuiltinTaskDefinition] = {}
        self.reload()

    def reload(self) -> None:
        self._tasks_by_key.clear()
        self._tasks_by_name.clear()
        try:
            package = importlib.import_module(self.package_name)
        except ModuleNotFoundError:
            logger.info("未找到内置任务包: %s", self.package_name)
            return
        except Exception as exc:
            logger.warning("加载内置任务包失败 %s: %s", self.package_name, exc)
            return

        self._load_module(package)
        package_path = getattr(package, "__path__", None)
        if package_path is None:
            return

        for module_info in pkgutil.iter_modules(package_path, f"{self.package_name}."):
            if module_info.ispkg:
                continue
            try:
                module = importlib.import_module(module_info.name)
            except Exception as exc:
                logger.warning("导入内置任务模块失败 %s: %s", module_info.name, exc)
                continue
            self._load_module(module)

    def _load_module(self, module: ModuleType) -> None:
        payloads: list[Any] = []
        get_builtin_tasks = getattr(module, "get_builtin_tasks", None)
        if callable(get_builtin_tasks):
            try:
                result = get_builtin_tasks()
                if isinstance(result, list):
                    payloads.extend(result)
            except Exception as exc:
                logger.warning("读取内置任务模块失败 %s: %s", module.__name__, exc)

        register_builtin_tasks = getattr(module, "register_builtin_tasks", None)
        if callable(register_builtin_tasks):
            try:
                registry: list[Any] = []
                register_builtin_tasks(registry)
                payloads.extend(registry)
            except Exception as exc:
                logger.warning("注册内置任务模块失败 %s: %s", module.__name__, exc)

        for payload in payloads:
            if not isinstance(payload, dict):
                logger.warning("跳过无效内置任务定义: %r", payload)
                continue
            try:
                definition = BuiltinTaskDefinition.from_mapping(payload)
            except BuiltinTaskError as exc:
                logger.warning("跳过内置任务定义: %s", exc)
                continue
            if definition.key in self._tasks_by_key:
                logger.warning("跳过重复内置任务 key: %s", definition.key)
                continue
            if definition.name in self._tasks_by_name:
                logger.warning("跳过重复内置任务 name: %s", definition.name)
                continue
            self._tasks_by_key[definition.key] = definition
            self._tasks_by_name[definition.name] = definition

    def list_tasks(self) -> list[BuiltinTaskDefinition]:
        return list(self._tasks_by_key.values())

    def get_by_key(self, key: str) -> BuiltinTaskDefinition | None:
        return self._tasks_by_key.get(key)

    def get_by_name(self, name: str) -> BuiltinTaskDefinition | None:
        return self._tasks_by_name.get(name)

    def build_interface_extension(self) -> dict[str, Any]:
        option_defs: dict[str, dict[str, Any]] = {}
        task_defs: list[dict[str, Any]] = []
        for task in self.list_tasks():
            task_defs.append(task.to_interface_task())
            for option_name, option_def in task.option_defs.items():
                option_defs[option_name] = dict(option_def)
        extension = {
            "group": [
                {
                    "name": BUILTIN_TASK_GROUP_NAME,
                    "label": BUILTIN_TASK_GROUP_LABEL,
                    "description": "Builtin tasks loaded by the framework.",
                    "default_expand": True,
                    "builtin": True,
                }
            ],
            "task": task_defs,
            "option": option_defs,
        }
        return self.i18n_service.translate_any(extension)

    async def execute(
        self,
        builtin_key: str,
        context: BuiltinTaskContext,
        task_option: dict[str, Any],
    ) -> BuiltinTaskResult:
        definition = self.get_by_key(builtin_key)
        if definition is None:
            raise BuiltinTaskError(f"unknown builtin task: {builtin_key}")

        result = definition.execute(context, task_option)
        if inspect.isawaitable(result):
            result = await result
        return BuiltinTaskResult.from_value(result)
