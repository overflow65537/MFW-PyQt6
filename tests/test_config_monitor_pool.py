"""ConfigMonitorPool 与 MonitorSession 行为单元测试。"""

import asyncio
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from PIL import Image

from app.view.monitor.config_monitor_pool import ConfigMonitorPool
from app.view.monitor.monitor_session import MonitorSession


class MonitorSessionLoopTests(unittest.IsolatedAsyncioTestCase):
    def _make_session(self) -> MonitorSession:
        monitor_task = MagicMock()
        monitor_task.maafw = MagicMock(controller=None)
        return MonitorSession(monitor_task, log_prefix="TestMonitor")

    async def test_is_loop_running_requires_both_tasks(self) -> None:
        session = self._make_session()
        self.assertFalse(session.is_loop_running())

        session._monitoring_active = True
        self.assertFalse(session.is_loop_running())

        session._monitor_loop_task = asyncio.create_task(asyncio.sleep(3600))
        self.assertFalse(session.is_loop_running())

        session._image_processing_task = asyncio.create_task(asyncio.sleep(3600))
        self.assertTrue(session.is_loop_running())

        await session.stop_loop_async()

    async def test_stop_loop_async_cancels_both_tasks(self) -> None:
        session = self._make_session()
        session._monitoring_active = True
        monitor_task = asyncio.create_task(asyncio.sleep(3600))
        processing_task = asyncio.create_task(asyncio.sleep(3600))
        session._monitor_loop_task = monitor_task
        session._image_processing_task = processing_task

        await session.stop_loop_async()

        self.assertFalse(session._monitoring_active)
        self.assertTrue(monitor_task.done())
        self.assertTrue(processing_task.done())


class ConfigMonitorPoolTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.frames: list[tuple[str, Image.Image]] = []
        self.cleared: list[str] = []
        self.disconnected: list[str] = []

        coordinator = SimpleNamespace(
            is_multi_instance_enabled=lambda: True,
            is_config_running=lambda _cid: False,
            runtime_manager=SimpleNamespace(get_instance=lambda _cid: None),
            task_service=MagicMock(),
            config_service=MagicMock(),
        )
        self.pool = ConfigMonitorPool(
            coordinator,
            on_frame=lambda cid, img: self.frames.append((cid, img)),
            on_capture_failure_clear=lambda cid: self.cleared.append(cid),
            on_controller_disconnected=lambda cid: self.disconnected.append(cid),
        )

    def test_set_display_config_returns_cached_frame(self) -> None:
        img = Image.new("RGB", (4, 4), color=(1, 2, 3))
        slot = self.pool._ensure_slot("cfg_a")
        slot.last_pil_image = img

        cached = self.pool.set_display_config("cfg_a")
        self.assertIs(cached, img)
        self.assertEqual(self.pool.display_config_id, "cfg_a")

    async def test_ensure_monitoring_skips_when_loop_running(self) -> None:
        slot = self.pool._ensure_slot("cfg_a")
        slot.session._monitoring_active = True
        slot.session._monitor_loop_task = asyncio.create_task(asyncio.sleep(3600))
        slot.session._image_processing_task = asyncio.create_task(asyncio.sleep(3600))

        with patch.object(
            slot.session, "run_startup_sequence", new=AsyncMock(return_value=True)
        ) as mock_start:
            result = await self.pool.ensure_monitoring("cfg_a", auto=True)
            self.assertTrue(result)
            mock_start.assert_not_called()

        await slot.session.stop_loop_async()

    async def test_ensure_monitoring_skips_after_loop_running(self) -> None:
        slot = self.pool._ensure_slot("cfg_c")

        async def _mark_running(*_args, **_kwargs) -> bool:
            slot.session._monitoring_active = True
            slot.session._monitor_loop_task = asyncio.create_task(asyncio.sleep(3600))
            slot.session._image_processing_task = asyncio.create_task(
                asyncio.sleep(3600)
            )
            return True

        with patch.object(
            slot.session, "run_startup_sequence", side_effect=_mark_running
        ) as mock_start:
            self.assertTrue(await self.pool.ensure_monitoring("cfg_c", auto=True))
            self.assertTrue(await self.pool.ensure_monitoring("cfg_c", auto=True))
            mock_start.assert_called_once()

        await slot.session.stop_loop_async()

    def test_bind_runner_maafw_shares_controller(self) -> None:
        shared_maafw = MagicMock()
        runner = SimpleNamespace(maafw=shared_maafw)
        inst = SimpleNamespace(
            runner=runner,
            task_service=MagicMock(),
            config_service=MagicMock(),
        )
        self.pool._coordinator.runtime_manager.get_instance = lambda cid: (
            inst if cid == "cfg_run" else None
        )
        slot = self.pool._ensure_slot("cfg_run")
        own_maafw = slot.monitor_task.maafw

        self.assertTrue(self.pool._bind_runner_maafw("cfg_run"))
        self.assertIs(slot.monitor_task.maafw, shared_maafw)
        self.assertTrue(slot.uses_shared_maafw)

        self.pool._release_shared_maafw(slot)
        self.assertFalse(slot.uses_shared_maafw)
        self.assertIsNot(slot.monitor_task.maafw, shared_maafw)
        self.assertIsNot(slot.monitor_task.maafw, own_maafw)

    async def test_ensure_monitoring_when_ready_waits_for_runner(self) -> None:
        shared_maafw = MagicMock(controller=MagicMock(connected=True))
        runner = SimpleNamespace(maafw=shared_maafw)
        inst = SimpleNamespace(
            runner=runner,
            task_service=MagicMock(),
            config_service=MagicMock(),
        )
        self.pool._coordinator.runtime_manager.get_instance = lambda cid: (
            inst if cid == "cfg_wait" else None
        )
        self.pool._coordinator.is_config_running = lambda cid: cid == "cfg_wait"

        slot = self.pool._ensure_slot("cfg_wait")
        with patch.object(
            slot.session, "run_startup_sequence", new=AsyncMock(return_value=True)
        ) as mock_start:
            result = await self.pool.ensure_monitoring_when_ready(
                "cfg_wait", auto=True, timeout_s=1.0
            )
            self.assertTrue(result)
            mock_start.assert_called_once()
            self.assertTrue(slot.uses_shared_maafw)


if __name__ == "__main__":
    unittest.main()
