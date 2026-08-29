from collections.abc import Callable
from typing import Any

from app.core.item import RunnerEvents
from app.core.runner.monitor_task import MonitorTask
from app.core.runner.runtime_context import RuntimeContext
from app.core.runner.task_flow import TaskFlowRunner
from app.utils.controller_utils import snapshot_cached_image
from app.utils.logger import logger


class RuntimeFacade:
    """当前配置运行时的显式 View API。"""

    def __init__(
        self,
        runtime_source: Callable[[], RuntimeContext] | TaskFlowRunner,
    ) -> None:
        if callable(runtime_source) and not hasattr(runtime_source, "run_tasks_flow"):
            self._context_provider: Callable[[], RuntimeContext] | None = runtime_source
            self._legacy_runner: TaskFlowRunner | None = None
        else:
            self._context_provider = None
            self._legacy_runner = runtime_source  # type: ignore[assignment]

    @property
    def context(self) -> RuntimeContext:
        if self._context_provider is None:
            raise RuntimeError("RuntimeContext 尚未接入")
        return self._context_provider()

    @property
    def _runner(self) -> TaskFlowRunner:
        if self._context_provider is not None:
            return self.context.task_runner
        if self._legacy_runner is None:
            raise RuntimeError("运行时尚未初始化")
        return self._legacy_runner

    @property
    def config_id(self) -> str | None:
        if self._context_provider is None:
            return None
        return self.context.config_id

    @property
    def events(self) -> RunnerEvents:
        if self._context_provider is not None:
            return self.context.events
        return self._runner.runner_events

    @property
    def logs(self):
        return self.context.logs

    @property
    def monitor(self):
        return self.context.monitor

    def get_context(self, config_id: str | None = None) -> RuntimeContext:
        """Return the active context; config lookup belongs to the coordinator."""
        context = self.context
        if config_id is not None and context.config_id != config_id:
            raise ValueError(f"RuntimeContext {config_id!r} is not active")
        return context

    def clear_logs(self) -> None:
        self.logs.clear()

    @property
    def is_running(self) -> bool:
        if self._context_provider is not None:
            return self.context.is_running
        runner = self._runner
        try:
            return bool(runner.is_running or runner.maafw.has_active_runtime())
        except Exception:
            return bool(getattr(runner, "is_running", False))

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
        """Start the bound runtime without redirecting through UI state."""
        if self._context_provider is not None:
            return await self.context.start(
                task_id,
                start_task_id=start_task_id,
            )

        # Compatibility path for tests and legacy callers that still bind a
        # bare TaskFlowRunner.
        runner = self._runner
        runner.need_stop = False
        task_api = runner.task_service
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
            return await runner.run_tasks_flow(
                task_id,
                start_task_id=start_task_id,
            )
        finally:
            if restore_checked and task_id is not None:
                task_api.update_task_checked(task_id, False)

    async def stop(self, *, manual: bool = True) -> Any:
        if self._context_provider is not None:
            return await self.context.stop(manual=manual)
        return await self._runner.stop_task(manual=manual)

    def submit_resource_run_confirmation(self, accepted: bool) -> None:
        """完成首次资源运行确认（由 View 对话框回调）。"""
        submit = getattr(self._runner, "submit_resource_run_confirmation", None)
        if callable(submit):
            submit(accepted)

    def shutdown_runtime_sync(self) -> None:
        if self._context_provider is not None:
            self.context.shutdown_runtime_sync()
            return
        self._runner.shutdown_runtime_sync()

    def stop_notification_thread(self, timeout_ms: int = 5000) -> None:
        """停止当前运行时的外部通知发送线程。"""
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
        """返回 Context 监控 Runner，或为兼容模式创建独立实例。"""
        if self._context_provider is not None:
            return self.context.monitor_task
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
