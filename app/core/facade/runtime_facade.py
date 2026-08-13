from typing import Any

from app.core.item import RunnerEvents
from app.core.runner.monitor_task import MonitorTask
from app.core.runner.task_flow import TaskFlowRunner
from app.utils.controller_utils import snapshot_cached_image
from app.utils.logger import logger


class RuntimeFacade:
    """运行时的显式 View API。"""

    def __init__(self, runner: TaskFlowRunner) -> None:
        self._runner = runner

    @property
    def is_running(self) -> bool:
        try:
            return bool(
                self._runner.is_running
                or self._runner.maafw.has_active_runtime()
            )
        except Exception:
            return bool(getattr(self._runner, "is_running", False))

    @property
    def current_running_task_id(self) -> str | None:
        return getattr(self._runner, "_current_running_task_id", None)

    async def run_tasks_flow(
        self,
        task_id: str | None = None,
        *,
        start_task_id: str | None = None,
    ) -> Any:
        return await self.run(task_id, start_task_id=start_task_id)

    async def stop_task(self, *, manual: bool = False) -> Any:
        return await self.stop(manual=manual)

    async def run(
        self,
        task_id: str | None = None,
        *,
        start_task_id: str | None = None,
    ) -> Any:
        """运行任务流，并在单任务临时启用后恢复原状态。"""
        task_api = self._runner.task_service
        restore_checked = False
        if task_id:
            task = task_api.get_task(task_id)
            if task and not task.is_checked:
                restore_checked = task_api.update_task_checked(task_id, True)
        try:
            task_api.refresh_hidden_flags()
        except Exception:
            pass
        try:
            return await self._runner.run_tasks_flow(
                task_id,
                start_task_id=start_task_id,
            )
        finally:
            if restore_checked and task_id is not None:
                task_api.update_task_checked(task_id, False)

    async def stop(self, *, manual: bool = True) -> Any:
        return await self._runner.stop_task(manual=manual)

    def shutdown_runtime_sync(self) -> None:
        self._runner.shutdown_runtime_sync()

    def stop_notification_thread(self, timeout_ms: int = 5000) -> None:
        """停止外部通知发送线程。"""
        thread = getattr(self._runner, "send_thread", None)
        if thread is None:
            return
        try:
            stop = getattr(thread, "stop", None)
            if callable(stop):
                stop()
            else:
                thread.quit()
                if not thread.wait(timeout_ms):
                    thread.terminate()
            logger.debug("关闭发送线程")
        except Exception as exc:
            logger.exception("关闭发送线程失败", exc_info=exc)

    def create_monitor_task(self) -> MonitorTask:
        """创建使用独立 RunnerEvents 的监控 Runner。"""
        return MonitorTask(
            task_service=self._runner.task_service,
            config_service=self._runner.config_service,
            runner_events=RunnerEvents(),
        )

    def get_cached_image_snapshot(self) -> Any | None:
        maafw = getattr(self._runner, "maafw", None)
        controller = getattr(maafw, "controller", None)
        if controller is None:
            return None
        return snapshot_cached_image(controller)
