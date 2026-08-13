from typing import Any

from app.core.runner.task_flow import TaskFlowRunner
from app.utils.controller_utils import snapshot_cached_image


class RuntimeFacade:
    """运行时的显式 View API。"""

    def __init__(self, runner: TaskFlowRunner) -> None:
        self._runner = runner

    @property
    def is_running(self) -> bool:
        return self._runner.is_running

    @property
    def current_running_task_id(self) -> str | None:
        return getattr(self._runner, "_current_running_task_id", None)

    async def run_tasks_flow(
        self,
        task_id: str | None = None,
        *,
        start_task_id: str | None = None,
    ) -> Any:
        return await self._runner.run_tasks_flow(
            task_id,
            start_task_id=start_task_id,
        )

    async def stop_task(self, *, manual: bool = False) -> Any:
        return await self._runner.stop_task(manual=manual)

    def get_cached_image_snapshot(self) -> Any | None:
        maafw = getattr(self._runner, "maafw", None)
        controller = getattr(maafw, "controller", None)
        if controller is None:
            return None
        return snapshot_cached_image(controller)
