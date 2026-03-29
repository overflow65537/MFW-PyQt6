from typing import Any

from app.core.runner.monitor_task import MonitorTask
from app.core.runner.task_flow import TaskFlowRunner
from app.core.service.config_service import ConfigService
from app.core.service.task_service import TaskService
from app.utils.logger import logger


class RuntimeQueryService:
    """运行时只读/辅助查询入口。"""

    def __init__(
        self,
        task_runner: TaskFlowRunner,
        task_service: TaskService,
        config_service: ConfigService,
    ) -> None:
        self._task_runner = task_runner
        self._task_service = task_service
        self._config_service = config_service

    def get_current_running_task_name(self) -> str | None:
        runner = self._task_runner
        task_id = getattr(runner, "_current_running_task_id", None)
        if not task_id:
            return None

        task = self._task_service.get_task(task_id)
        if task is None:
            return None
        return str(getattr(task, "name", "") or "") or None

    def is_task_flow_running(self) -> bool:
        return bool(getattr(self._task_runner, "is_running", False))

    def create_monitor_task(self) -> MonitorTask:
        return MonitorTask(self._task_service, self._config_service)

    def get_notice_send_thread(self) -> Any:
        return getattr(self._task_runner, "send_thread", None)

    def get_task_flow_controller(self) -> Any:
        maafw = getattr(self._task_runner, "maafw", None)
        if maafw is None:
            return None
        return getattr(maafw, "controller", None)

    def is_controller_connected(self, controller: Any) -> bool:
        if controller is None:
            return False
        connected = getattr(controller, "connected", None)
        return connected is not False

    def is_task_flow_controller_ready(self) -> bool:
        controller = self.get_task_flow_controller()
        if controller is None:
            return False
        return getattr(controller, "connected", None) is True

    def get_agent_thread_process(self) -> Any:
        maafw = getattr(self._task_runner, "maafw", None)
        if maafw is None:
            return None
        return getattr(maafw, "agent_thread", None)

    def clear_agent_thread_process(self) -> None:
        maafw = getattr(self._task_runner, "maafw", None)
        if maafw is None:
            return
        maafw.agent_thread = None

    def clear_maafw_sync(self) -> None:
        maafw = self._task_runner.maafw
        if maafw.tasker and maafw.tasker.running:
            logger.debug("停止任务线程")
            maafw.tasker.post_stop().wait()
            logger.debug("停止任务线程完成")
        maafw.tasker = None
        if maafw.resource:
            maafw.resource.clear()
        maafw.resource = None
        maafw.controller = None
        if maafw.agent:
            maafw.agent.disconnect()
        maafw.agent = None