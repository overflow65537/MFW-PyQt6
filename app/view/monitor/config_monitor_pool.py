"""多实例模式下按 config_id 维护独立监控会话，切换配置时仅切换显示。"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Callable, Dict, Optional

from PIL import Image

from app.core.runner.monitor_task import MonitorTask
from app.utils.logger import logger
from app.view.monitor.monitor_session import MonitorSession
from app.view.monitor.recognition_roi_store import RecognitionRoiStore

if TYPE_CHECKING:
    from app.core.core import ServiceCoordinator


FrameCallback = Callable[[str, Image.Image], None]
ClearCallback = Callable[[str], None]


@dataclass
class ConfigMonitorSlot:
    """单个配置的监控槽：独立连接 + 帧缓存。"""

    config_id: str
    monitor_task: MonitorTask
    session: MonitorSession
    roi_store: RecognitionRoiStore = field(default_factory=RecognitionRoiStore)
    last_pil_image: Optional[Image.Image] = None
    starting: bool = False
    stopping: bool = False
    uses_shared_maafw: bool = False
    ensure_lock: asyncio.Lock = field(default_factory=asyncio.Lock)


class ConfigMonitorPool:
    """按 config_id 池化 MonitorSession；切换显示配置不断开后台连接。"""

    def __init__(
        self,
        coordinator: "ServiceCoordinator",
        *,
        on_frame: FrameCallback,
        on_capture_failure_clear: ClearCallback,
        on_controller_disconnected: Callable[[str], None],
    ) -> None:
        self._coordinator = coordinator
        self._on_frame = on_frame
        self._on_capture_failure_clear = on_capture_failure_clear
        self._on_controller_disconnected = on_controller_disconnected
        self._slots: Dict[str, ConfigMonitorSlot] = {}
        self._display_config_id: str = ""

    @property
    def display_config_id(self) -> str:
        return self._display_config_id

    def get_slot(self, config_id: str) -> Optional[ConfigMonitorSlot]:
        if not config_id:
            return None
        return self._slots.get(config_id)

    def get_display_session(self) -> Optional[MonitorSession]:
        slot = self._slots.get(self._display_config_id)
        return slot.session if slot else None

    def get_display_monitor_task(self) -> Optional[MonitorTask]:
        slot = self._slots.get(self._display_config_id)
        return slot.monitor_task if slot else None

    def get_display_roi_store(self) -> RecognitionRoiStore:
        slot = self._slots.get(self._display_config_id)
        if slot is not None:
            return slot.roi_store
        return RecognitionRoiStore()

    def is_display_monitoring(self) -> bool:
        slot = self._slots.get(self._display_config_id)
        return bool(slot and slot.session.is_loop_running())

    def is_display_starting(self) -> bool:
        slot = self._slots.get(self._display_config_id)
        return bool(slot and slot.starting)

    def is_display_stopping(self) -> bool:
        slot = self._slots.get(self._display_config_id)
        return bool(slot and slot.stopping)

    def is_config_monitoring(self, config_id: str) -> bool:
        slot = self._slots.get(config_id)
        return bool(slot and slot.session.is_loop_running())

    def is_config_starting(self, config_id: str) -> bool:
        slot = self._slots.get(config_id)
        return bool(slot and slot.starting)

    def list_slot_ids(self) -> list[str]:
        return list(self._slots.keys())

    def set_display_config(self, config_id: str) -> Optional[Image.Image]:
        """切换显示目标，返回缓存帧供 UI 秒切。"""
        self._display_config_id = config_id or ""
        slot = self._slots.get(self._display_config_id)
        return slot.last_pil_image if slot else None

    def _resolve_services(self, config_id: str):
        """解析指定配置的控制器/资源服务栈。"""
        coord = self._coordinator
        if coord.is_multi_instance_enabled():
            inst = coord.runtime_manager.get_instance(config_id)
            if inst is not None:
                return inst.task_service, inst.config_service
        return coord.task_service, coord.config_service

    def _ensure_slot(self, config_id: str) -> ConfigMonitorSlot:
        existing = self._slots.get(config_id)
        if existing is not None:
            return existing

        task_service, config_service = self._resolve_services(config_id)
        monitor_task = MonitorTask(task_service, config_service)
        session = MonitorSession(
            monitor_task, log_prefix=f"Monitor[{config_id[:8]}]"
        )

        slot = ConfigMonitorSlot(
            config_id=config_id,
            monitor_task=monitor_task,
            session=session,
        )

        def _on_frame(pil_image: Image.Image, cid: str = config_id) -> None:
            try:
                slot.last_pil_image = pil_image.copy()
            except Exception:
                slot.last_pil_image = pil_image
            self._on_frame(cid, pil_image)

        def _on_clear(cid: str = config_id) -> None:
            slot.last_pil_image = None
            self._on_capture_failure_clear(cid)

        async def _on_disconnect(cid: str = config_id) -> None:
            self._on_controller_disconnected(cid)

        session.set_callbacks(
            on_frame=_on_frame,
            on_capture_failure_clear=_on_clear,
            on_controller_disconnected=_on_disconnect,
        )
        self._slots[config_id] = slot
        return slot

    def _bind_runner_maafw(self, config_id: str) -> bool:
        """多实例：监控复用任务运行体的 MaaFW，避免与 Runner 争抢控制器连接。"""
        if not self._coordinator.is_multi_instance_enabled():
            return False
        inst = self._coordinator.runtime_manager.get_instance(config_id)
        slot = self._slots.get(config_id)
        if inst is None or slot is None:
            return False
        slot.monitor_task.maafw = inst.runner.maafw
        slot.uses_shared_maafw = True
        return True

    def _release_shared_maafw(self, slot: ConfigMonitorSlot) -> None:
        """恢复监控槽独立 MaaFW（任务停止后或共享连接失败回退）。"""
        if not slot.uses_shared_maafw:
            return
        slot.uses_shared_maafw = False
        from app.core.runner.maafw import MaaFW

        slot.monitor_task.maafw = MaaFW()

    async def ensure_monitoring_when_ready(
        self,
        config_id: str,
        *,
        auto: bool = True,
        timeout_s: float = 90.0,
    ) -> bool:
        """等待任务流完成控制器连接后，再启动监控（共享同一 MaaFW）。"""
        import time

        self._ensure_slot(config_id)
        deadline = time.monotonic() + max(5.0, timeout_s)
        while time.monotonic() < deadline:
            if not self._coordinator.is_config_running(config_id):
                return False
            if self._bind_runner_maafw(config_id):
                slot = self._slots.get(config_id)
                if slot is not None and slot.session.is_controller_connected():
                    return await self.ensure_monitoring(config_id, auto=auto)
            await asyncio.sleep(0.2)
        slot = self._slots.get(config_id)
        if slot is not None:
            self._release_shared_maafw(slot)
        return await self.ensure_monitoring(config_id, auto=auto)

    async def ensure_monitoring(self, config_id: str, *, auto: bool = True) -> bool:
        """为指定配置启动监控（若已在运行则跳过）。"""
        if not config_id:
            return False
        slot = self._ensure_slot(config_id)
        async with slot.ensure_lock:
            if slot.session.is_loop_running():
                return True
            if slot.starting:
                return True
            if slot.session.monitoring_active or slot.session.is_loop_running():
                await slot.session.stop_loop_async()

            slot.starting = True
            log_prefix = f"Monitor[{config_id[:8]}]"
            try:
                if self._coordinator.is_config_running(config_id):
                    self._bind_runner_maafw(config_id)
                logger.info(
                    "[%s] 后台启动监控（%s）", log_prefix, "自动" if auto else "手动"
                )
                started = await slot.session.run_startup_sequence(
                    should_abort=lambda: not slot.starting,
                )
                if not started:
                    logger.warning("[%s] 监控启动失败", log_prefix)
                    if slot.uses_shared_maafw:
                        self._release_shared_maafw(slot)
                return bool(started)
            except Exception as exc:
                logger.error(
                    "[%s] 监控启动异常: %s", log_prefix, exc, exc_info=True
                )
                return False
            finally:
                slot.starting = False

    async def stop_monitoring(self, config_id: str, *, clear_cache: bool = False) -> None:
        """停止指定配置的监控会话（不影响其他配置）。"""
        slot = self._slots.get(config_id)
        if slot is None:
            return
        if slot.stopping:
            return
        slot.stopping = True
        slot.starting = False
        try:
            async with slot.ensure_lock:
                await slot.session.stop(
                    teardown=not slot.uses_shared_maafw,
                )
                self._release_shared_maafw(slot)
            if clear_cache:
                slot.last_pil_image = None
                slot.roi_store.clear()
        except Exception as exc:
            logger.warning(
                "停止配置 %s 监控失败: %s", config_id, exc, exc_info=True
            )
        finally:
            slot.stopping = False

    async def stop_all(self) -> None:
        for config_id in list(self._slots.keys()):
            await self.stop_monitoring(config_id, clear_cache=True)

    def shutdown_sync(self) -> None:
        """应用退出时同步停止所有循环。"""
        for slot in self._slots.values():
            try:
                slot.session.stop_loop()
            except Exception:
                pass
            slot.starting = False
            slot.stopping = False

    def remove_slot(self, config_id: str) -> None:
        self._slots.pop(config_id, None)
