import asyncio
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

from PySide6.QtCore import Qt

from app.core.service.app_command_dispatcher import AppCommandDispatcher
from app.ipc.protocol import IpcCommand, IpcRequest, IpcStatus


class _FakeWindow:
    def __init__(self, coordinator):
        self.service_coordinator = coordinator
        self.visible = True
        self.minimized = False
        self.show = Mock(side_effect=self._show)
        self.showNormal = Mock(side_effect=self._show_normal)
        self.raise_ = Mock()
        self.activateWindow = Mock()
        self.close = Mock()
        self._allow_window_close = False

    def _show(self):
        self.visible = True

    def _show_normal(self):
        self.minimized = False

    def isVisible(self):
        return self.visible

    def windowState(self):
        return (
            Qt.WindowState.WindowMinimized
            if self.minimized
            else Qt.WindowState.WindowNoState
        )

    def winId(self):
        return 0


class AppCommandDispatcherTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.events = []
        self.running_ids = []
        configs = {"config-a": object(), "config-b": object()}
        self.coordinator = SimpleNamespace(
            configs=SimpleNamespace(
                current_config_id="config-a",
                get_config=lambda config_id: configs.get(config_id),
            ),
        )
        self.coordinator.get_running_config_ids = lambda: list(self.running_ids)
        self.coordinator.select_config = Mock(side_effect=self._select_config)
        self.coordinator.run_configuration = AsyncMock(side_effect=self._run_config)
        self.coordinator.stop_configuration = AsyncMock(
            side_effect=self._stop_configuration
        )
        self.coordinator.shutdown_all_configurations = AsyncMock(
            side_effect=self._shutdown_all
        )
        self.window = _FakeWindow(self.coordinator)
        self.close_callback = AsyncMock(side_effect=lambda: self.events.append("close"))
        self.dispatcher = AppCommandDispatcher(
            asyncio.get_running_loop(),
            close_callback=self.close_callback,
        )
        self.dispatcher.attach_window(self.window)

    async def asyncTearDown(self):
        await self.dispatcher.close()

    def _select_config(self, config_id):
        self.events.append(f"switch:{config_id}")
        self.coordinator.configs.current_config_id = config_id
        return True

    async def _run_config(self, config_id, **_kwargs):
        self.events.append(f"run:{config_id}")
        if config_id not in self.running_ids:
            self.running_ids.append(config_id)
        return True

    async def _stop_configuration(self, config_id, **_kwargs):
        self.events.append(f"stop:{config_id}")
        if config_id not in self.running_ids:
            return False
        self.running_ids.remove(config_id)
        return True

    async def _shutdown_all(self, **_kwargs):
        self.events.append("stop_all")
        self.running_ids.clear()
        return []

    async def _submit_and_wait(self, command, params=None):
        request = IpcRequest(command, params or {})
        response = self.dispatcher.submit(request)
        await self.dispatcher.wait_idle()
        return response

    async def test_activate_is_synchronous(self):
        self.window.visible = False
        self.window.minimized = True

        response = self.dispatcher.submit(IpcRequest(IpcCommand.ACTIVATE))

        self.assertEqual(IpcStatus.OK, response.status)
        self.window.show.assert_called_once_with()
        self.window.showNormal.assert_called_once_with()
        self.window.raise_.assert_called_once_with()
        self.window.activateWindow.assert_called_once_with()

    async def test_switch_config_success_and_not_found(self):
        response = await self._submit_and_wait(
            IpcCommand.SWITCH_CONFIG,
            {"config_id": "config-b"},
        )
        self.assertEqual(IpcStatus.ACCEPTED, response.status)
        self.assertEqual("config-b", self.coordinator.configs.current_config_id)

        missing = self.dispatcher.submit(
            IpcRequest(IpcCommand.SWITCH_CONFIG, {"config_id": "missing"})
        )
        self.assertEqual(IpcStatus.NOT_FOUND, missing.status)
        self.assertEqual("config_not_found", missing.code)

    async def test_run_current_and_specified_configuration(self):
        current = await self._submit_and_wait(
            IpcCommand.RUN,
            {"config_id": None, "force_restart": False},
        )
        self.assertEqual(IpcStatus.ACCEPTED, current.status)
        self.coordinator.run_configuration.assert_awaited_with("config-a")

        self.running_ids.clear()
        specified = await self._submit_and_wait(
            IpcCommand.RUN,
            {"config_id": "config-b", "force_restart": False},
        )
        self.assertEqual(IpcStatus.ACCEPTED, specified.status)
        self.coordinator.run_configuration.assert_awaited_with("config-b")

    async def test_running_other_config_does_not_block_run(self):
        self.running_ids[:] = ["config-a"]

        response = await self._submit_and_wait(
            IpcCommand.RUN,
            {"config_id": "config-b", "force_restart": False},
        )

        self.assertEqual(IpcStatus.ACCEPTED, response.status)
        self.coordinator.run_configuration.assert_awaited_once_with("config-b")
        self.assertEqual(["config-a", "config-b"], self.running_ids)

    async def test_running_same_config_is_busy(self):
        self.running_ids[:] = ["config-b"]

        response = self.dispatcher.submit(
            IpcRequest(
                IpcCommand.RUN,
                {"config_id": "config-b", "force_restart": False},
            )
        )

        self.assertEqual(IpcStatus.BUSY, response.status)
        self.assertEqual("task_running", response.code)
        self.coordinator.run_configuration.assert_not_awaited()

    async def test_force_restart_stops_before_running_target(self):
        self.running_ids[:] = ["config-a"]

        response = await self._submit_and_wait(
            IpcCommand.RUN,
            {"config_id": "config-b", "force_restart": True},
        )

        self.assertEqual(IpcStatus.ACCEPTED, response.status)
        self.assertEqual(["stop_all", "run:config-b"], self.events)

    async def test_shutdown_waits_for_graceful_stop_before_close(self):
        self.running_ids[:] = ["config-a"]

        response = await self._submit_and_wait(
            IpcCommand.SHUTDOWN,
            {"reason": "external"},
        )

        self.assertEqual(IpcStatus.ACCEPTED, response.status)
        self.assertEqual(["stop_all", "close"], self.events)
        self.coordinator.shutdown_all_configurations.assert_awaited_once_with(
            manual=False
        )

    async def test_different_configs_can_be_reserved_together(self):
        gate = asyncio.Event()

        async def slow_run(config_id, **_kwargs):
            await gate.wait()
            return await self._run_config(config_id)

        self.coordinator.run_configuration.side_effect = slow_run
        first = self.dispatcher.submit(
            IpcRequest(
                IpcCommand.RUN,
                {"config_id": "config-a", "force_restart": False},
            )
        )
        second = self.dispatcher.submit(
            IpcRequest(
                IpcCommand.RUN,
                {"config_id": "config-b", "force_restart": False},
            )
        )

        self.assertEqual(IpcStatus.ACCEPTED, first.status)
        self.assertEqual(IpcStatus.ACCEPTED, second.status)
        gate.set()
        await self.dispatcher.wait_idle()
        self.assertEqual(["config-a", "config-b"], self.running_ids)

    async def test_same_config_second_reservation_is_busy(self):
        gate = asyncio.Event()

        async def slow_run(config_id, **_kwargs):
            await gate.wait()
            return await self._run_config(config_id)

        self.coordinator.run_configuration.side_effect = slow_run
        first = self.dispatcher.submit(
            IpcRequest(
                IpcCommand.RUN,
                {"config_id": "config-a", "force_restart": False},
            )
        )
        second = self.dispatcher.submit(
            IpcRequest(
                IpcCommand.RUN,
                {"config_id": "config-a", "force_restart": False},
            )
        )

        self.assertEqual(IpcStatus.ACCEPTED, first.status)
        self.assertEqual(IpcStatus.BUSY, second.status)
        self.assertEqual("command_in_progress", second.code)
        gate.set()
        await self.dispatcher.wait_idle()

    async def test_stop_is_idempotent_and_validates_config(self):
        response = await self._submit_and_wait(
            IpcCommand.STOP,
            {"config_id": None},
        )
        self.assertEqual(IpcStatus.ACCEPTED, response.status)
        self.coordinator.stop_configuration.assert_awaited_once_with(
            "config-a",
            manual=True,
        )

        missing = self.dispatcher.submit(
            IpcRequest(IpcCommand.STOP, {"config_id": "missing"})
        )
        self.assertEqual(IpcStatus.NOT_FOUND, missing.status)

    async def test_shutdown_stops_then_closes_and_rejects_mutations(self):
        self.running_ids[:] = ["config-a"]
        shutdown = self.dispatcher.submit(
            IpcRequest(IpcCommand.SHUTDOWN, {"reason": "restart"})
        )
        rejected_run = self.dispatcher.submit(
            IpcRequest(
                IpcCommand.RUN,
                {"config_id": "config-b", "force_restart": True},
            )
        )
        rejected_switch = self.dispatcher.submit(
            IpcRequest(IpcCommand.SWITCH_CONFIG, {"config_id": "config-b"})
        )
        rejected_stop = self.dispatcher.submit(
            IpcRequest(IpcCommand.STOP, {"config_id": None})
        )
        await self.dispatcher.wait_idle()

        self.assertEqual(IpcStatus.ACCEPTED, shutdown.status)
        for response in (rejected_run, rejected_switch, rejected_stop):
            self.assertEqual(IpcStatus.BUSY, response.status)
            self.assertEqual("shutting_down", response.code)
        self.assertEqual(["stop_all", "close"], self.events)
        self.close_callback.assert_awaited_once_with()

    async def test_status_reports_active_and_running_configurations(self):
        self.running_ids[:] = ["config-b"]
        self.coordinator.configs.current_config_id = "config-a"

        response = self.dispatcher.submit(IpcRequest(IpcCommand.STATUS))

        self.assertEqual(IpcStatus.OK, response.status)
        self.assertEqual(
            {
                "ready": True,
                "active_config_id": "config-a",
                "running": True,
                "running_config_ids": ["config-b"],
                "shutting_down": False,
            },
            response.data,
        )


class AppCommandDispatcherStartupTests(unittest.IsolatedAsyncioTestCase):
    async def test_pending_commands_are_fifo_and_attach_drains_once(self):
        events = []
        coordinator = SimpleNamespace(
            configs=SimpleNamespace(
                current_config_id="config-a",
                get_config=lambda config_id: object()
                if config_id in {"config-a", "config-b"}
                else None,
            ),
            get_running_config_ids=lambda: [],
            select_config=Mock(side_effect=lambda config_id: events.append(f"switch:{config_id}") or True),
            run_configuration=AsyncMock(side_effect=lambda config_id: events.append(f"run:{config_id}") or True),
            stop_configuration=AsyncMock(return_value=False),
            shutdown_all_configurations=AsyncMock(return_value=[]),
        )
        window = _FakeWindow(coordinator)
        dispatcher = AppCommandDispatcher(asyncio.get_running_loop())
        try:
            activate = dispatcher.submit(IpcRequest(IpcCommand.ACTIVATE))
            switch = dispatcher.submit_startup(
                IpcRequest(IpcCommand.SWITCH_CONFIG, {"config_id": "config-b"})
            )
            run = dispatcher.submit_startup(
                IpcRequest(
                    IpcCommand.RUN,
                    {"config_id": "config-b", "force_restart": False},
                )
            )
            self.assertEqual(IpcStatus.ACCEPTED, activate.status)
            self.assertEqual(IpcStatus.ACCEPTED, switch.status)
            self.assertEqual(IpcStatus.ACCEPTED, run.status)

            dispatcher.attach_window(window)
            dispatcher.attach_window(window)
            await dispatcher.wait_idle()

            window.raise_.assert_called_once_with()
            self.assertEqual(["switch:config-b", "run:config-b"], events)
            coordinator.run_configuration.assert_awaited_once_with("config-b")
        finally:
            await dispatcher.close()

    async def test_external_mutation_is_busy_until_window_is_ready(self):
        dispatcher = AppCommandDispatcher(asyncio.get_running_loop())
        try:
            activate = dispatcher.submit(IpcRequest(IpcCommand.ACTIVATE))
            run = dispatcher.submit(
                IpcRequest(
                    IpcCommand.RUN,
                    {"config_id": "config-a", "force_restart": False},
                )
            )
            switch = dispatcher.submit(
                IpcRequest(IpcCommand.SWITCH_CONFIG, {"config_id": "config-a"})
            )
            stop = dispatcher.submit(
                IpcRequest(IpcCommand.STOP, {"config_id": None})
            )

            self.assertEqual(IpcStatus.ACCEPTED, activate.status)
            for response in (run, switch, stop):
                self.assertEqual(IpcStatus.BUSY, response.status)
                self.assertEqual("application_not_ready", response.code)
        finally:
            await dispatcher.close()

    async def test_startup_shutdown_drops_earlier_mutating_commands(self):
        events = []
        coordinator = SimpleNamespace(
            configs=SimpleNamespace(
                current_config_id="config-a",
                get_config=lambda _config_id: object(),
            ),
            get_running_config_ids=lambda: [],
            select_config=Mock(side_effect=lambda config_id: events.append(f"switch:{config_id}") or True),
            run_configuration=AsyncMock(side_effect=lambda config_id: events.append(f"run:{config_id}") or True),
            stop_configuration=AsyncMock(side_effect=lambda *_args, **_kwargs: events.append("stop") or False),
            shutdown_all_configurations=AsyncMock(side_effect=lambda **_kwargs: events.append("stop_all") or []),
        )
        close_callback = AsyncMock(side_effect=lambda: events.append("close"))
        dispatcher = AppCommandDispatcher(
            asyncio.get_running_loop(),
            close_callback=close_callback,
        )
        try:
            dispatcher.submit_startup(
                IpcRequest(IpcCommand.SWITCH_CONFIG, {"config_id": "config-b"})
            )
            dispatcher.submit_startup(
                IpcRequest(
                    IpcCommand.RUN,
                    {"config_id": "config-b", "force_restart": False},
                )
            )
            dispatcher.submit(
                IpcRequest(IpcCommand.SHUTDOWN, {"reason": "external"})
            )
            dispatcher.attach_window(_FakeWindow(coordinator))
            await dispatcher.wait_idle()

            self.assertEqual(["stop_all", "close"], events)
            coordinator.select_config.assert_not_called()
            coordinator.run_configuration.assert_not_awaited()
        finally:
            await dispatcher.close()


if __name__ == "__main__":
    unittest.main()
