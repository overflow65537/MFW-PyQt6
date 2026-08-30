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

    def __init__(self, context_provider: Callable[[], RuntimeContext]) -> None:
        self._context_provider = context_provider

    @property
    def context(self) -> RuntimeContext:
        return self._context_provider()

    @property
    def _runner(self) -> TaskFlowRunner:
        return self.context.task_runner

    @property
    def config_id(self) -> str:
        return self.context.config_id

    @property
    def events(self) -> RunnerEvents:
        return self.context.events

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
        return self.context.is_running

    @property
    def current_running_task_id(self) -> str | None:
        return self._runner.current_running_task_id

    async def run(
        self,
        task_id: str | None = None,
        *,
        start_task_id: str | None = None,
    ) -> bool:
        """Start the active configuration runtime."""
        return await self.context.start(
            task_id,
            start_task_id=start_task_id,
        )

    async def stop(self, *, manual: bool = True) -> bool:
        return await self.context.stop(manual=manual)

    def submit_resource_run_confirmation(self, accepted: bool) -> None:
        """完成首次资源运行确认（由 View 对话框回调）。"""
        self._runner.submit_resource_run_confirmation(accepted)

    def shutdown_runtime_sync(self) -> None:
        self.context.shutdown_runtime_sync()

    def stop_notification_thread(self, timeout_ms: int = 5000) -> None:
        """停止当前运行时的外部通知发送线程。"""
        try:
            self._runner.send_thread.stop(timeout_ms)
            logger.debug("关闭发送线程")
        except Exception:
            logger.exception("关闭发送线程失败")

    def create_monitor_task(self) -> MonitorTask:
        return self.context.monitor_task

    def get_cached_image_snapshot(self) -> Any | None:
        controller = self._runner.maafw.controller
        if controller is None:
            return None
        return snapshot_cached_image(controller)
