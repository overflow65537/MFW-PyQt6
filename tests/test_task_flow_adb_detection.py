import asyncio
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

from maa.toolkit import Toolkit

from app.core.runner.task_flow import TaskFlowRunner


class AdbDetectionTests(unittest.IsolatedAsyncioTestCase):
    async def test_adb_detection_runs_outside_event_loop(self):
        runner = SimpleNamespace(
            need_stop=False,
            _should_use_new_adb_device=Mock(),
        )

        with patch(
            "app.core.runner.task_flow.asyncio.to_thread",
            new=AsyncMock(return_value=[]),
        ) as to_thread:
            result = await TaskFlowRunner._auto_find_adb_device(
                runner,
                controller_raw={},
                controller_type="adb",
                controller_config={},
            )

        self.assertIsNone(result)
        to_thread.assert_awaited_once_with(Toolkit.find_adb_devices)
        runner._should_use_new_adb_device.assert_not_called()

    async def test_stop_during_adb_detection_discards_result(self):
        runner = SimpleNamespace(
            need_stop=False,
            _should_use_new_adb_device=Mock(return_value=True),
        )
        device = SimpleNamespace(
            config={},
            name="emulator",
            address="127.0.0.1:5555",
            adb_path="adb",
            screencap_methods=0,
            input_methods=0,
        )

        async def detect_then_stop(_func):
            runner.need_stop = True
            await asyncio.sleep(0)
            return [device]

        with patch(
            "app.core.runner.task_flow.asyncio.to_thread",
            side_effect=detect_then_stop,
        ):
            result = await TaskFlowRunner._auto_find_adb_device(
                runner,
                controller_raw={},
                controller_type="adb",
                controller_config={},
            )

        self.assertIsNone(result)
        runner._should_use_new_adb_device.assert_not_called()

    async def test_stop_during_connection_defers_runtime_cleanup(self):
        status_signal = SimpleNamespace(emit=Mock())
        runner = SimpleNamespace(
            _manual_stop=False,
            need_stop=False,
            _is_connecting_device=True,
            _stop_task_timeout=Mock(),
            _save_stop_screenshot=AsyncMock(),
            log_output=SimpleNamespace(emit=Mock()),
            runner_events=SimpleNamespace(start_button_status=status_signal),
            maafw=SimpleNamespace(
                has_active_runtime=Mock(return_value=True),
                stop_task=AsyncMock(),
            ),
            tr=lambda text: text,
        )

        await TaskFlowRunner.stop_task(runner, manual=True)

        self.assertTrue(runner.need_stop)
        runner._save_stop_screenshot.assert_awaited_once_with(manual=True)
        runner.maafw.stop_task.assert_not_awaited()
        status_signal.emit.assert_called_once_with(
            {"text": "STOP", "status": "disabled"}
        )

    async def test_connection_phase_stop_skips_screenshot(self):
        maafw = SimpleNamespace(
            controller=object(),
            screencap_test=AsyncMock(),
        )
        runner = SimpleNamespace(
            _active_controller_raw=None,
            _is_connecting_device=True,
            maafw=maafw,
        )

        await TaskFlowRunner._save_stop_screenshot(runner, manual=True)

        maafw.screencap_test.assert_not_awaited()

    async def test_stop_prevents_configured_emulator_from_starting(self):
        runner = SimpleNamespace(
            need_stop=False,
            adb_controller_raw=None,
            adb_activate_controller=None,
            adb_controller_config=None,
            _get_controller_type=Mock(return_value="adb"),
            _get_controller_name=Mock(return_value="controller"),
            _try_prepare_and_connect_adb=AsyncMock(return_value=False),
            _wait_after_controller_connect=AsyncMock(),
            _start_process=Mock(),
            log_output=SimpleNamespace(emit=Mock()),
            tr=lambda text: text,
        )

        async def stop_while_detecting(**_kwargs):
            runner.need_stop = True
            return False

        runner._try_prepare_and_connect_adb.side_effect = stop_while_detecting
        result = await TaskFlowRunner._connect_adb_controller(
            runner,
            {
                "controller_type": "controller",
                "controller": {
                    "emulator_path": "emulator.exe",
                    "emulator_params": "",
                },
            },
        )

        self.assertFalse(result)
        runner._start_process.assert_not_called()
