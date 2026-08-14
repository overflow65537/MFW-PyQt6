from PIL import Image

from app.core.runner.maafw import MaaFW
from app.core.runner.task_flow import TaskFlowRunner
from app.core.item import RunnerEvents
from app.core.service.task_service import TaskService
from app.core.service.config_service import ConfigService
from app.utils.screencap_lock import screencap_guard


class MonitorTask(TaskFlowRunner):
    """监控任务"""

    def __init__(
        self,
        task_service: TaskService,
        config_service: ConfigService,
        runner_events: RunnerEvents | None = None,
        *,
        config_id: str | None = None,
        maafw: MaaFW | None = None,
    ):
        super().__init__(
            task_service,
            config_service,
            runner_events if runner_events is not None else RunnerEvents(),
            config_id=config_id,
            maafw=maafw,
            connect_maafw_signals=maafw is None,
        )
        self.screen_pixmap = None

    def is_controller_connected(self) -> bool:
        controller = getattr(self.maafw, "controller", None)
        if controller is None:
            return False
        return getattr(controller, "connected", None) is not False

    async def connect_controller(self) -> bool:
        from app.common.constants import _CONTROLLER_

        if not self._runtime_snapshot_ready:
            if not self._prepare_runtime_snapshot():
                raise ValueError("Configuration no longer exists")
            self._reload_interface_for_current_bundle()
        controller_cfg = self._get_task(_CONTROLLER_)
        if not controller_cfg:
            raise ValueError("未找到基础预配置任务")
        return bool(await self.connect_device(controller_cfg.task_option))

    def capture_frame(self) -> Image.Image:
        controller = getattr(self.maafw, "controller", None)
        if controller is None:
            raise RuntimeError("控制器尚未初始化，无法抓取画面")
        with screencap_guard():
            raw_frame = controller.post_screencap().wait().get()
            if raw_frame is None:
                raise ValueError("采集返回空帧")
            frame = raw_frame.copy()
        return Image.fromarray(frame[..., ::-1])

    def click(self, x: int, y: int) -> None:
        controller = getattr(self.maafw, "controller", None)
        if controller is None:
            raise RuntimeError("控制器尚未初始化，无法同步点击")
        controller.post_click(x, y).wait()

    async def teardown_controller(self) -> None:
        await self.maafw.stop_task()
