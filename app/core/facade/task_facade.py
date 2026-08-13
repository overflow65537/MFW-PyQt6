from typing import Any

from app.core.facade._snapshot import snapshot
from app.core.item import TaskItem
from app.core.service.task_service import DEFAULT_SPEEDRUN_CONFIG, TaskService


class TaskFacade:
    """任务域的显式 View API。"""

    def __init__(self, service: TaskService) -> None:
        self._service = service

    @property
    def interface(self) -> dict[str, Any]:
        return snapshot(self._service.interface)

    @property
    def default_option(self) -> dict[str, Any]:
        return snapshot(self._service.default_option)

    def get_tasks(self) -> list[TaskItem]:
        return snapshot(self._service.get_tasks())

    def get_task(self, task_id: str) -> TaskItem | None:
        return snapshot(self._service.get_task(task_id))

    def update_task_checked(self, task_id: str, is_checked: bool) -> bool:
        return self._service.update_task_checked(task_id, is_checked)

    def update_task(self, task: TaskItem, idx: int = -2) -> bool:
        return self._service.update_task(snapshot(task), idx)

    def build_speedrun_config(
        self,
        task_name: str,
        existing: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return snapshot(
            self._service.build_speedrun_config(
                task_name,
                snapshot(existing),
            )
        )

    def get_builtin_task_label(self, task: TaskItem) -> str | None:
        task_snapshot = snapshot(task)
        definition = self._service.get_builtin_task_definition(task_snapshot)
        if not definition:
            return None
        return self._service.builtin_task_loader.i18n_service.translate_text(
            definition.label
        )


__all__ = ["DEFAULT_SPEEDRUN_CONFIG", "TaskFacade"]
