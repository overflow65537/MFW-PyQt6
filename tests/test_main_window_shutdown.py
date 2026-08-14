import asyncio
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

from app.view.main_window.main_window import MainWindow


class MainWindowShutdownFlowTests(unittest.IsolatedAsyncioTestCase):
    async def test_graceful_stop_starts_sync_cleanup_after_runtime_tasks_finish(self):
        coordinator = SimpleNamespace(
            shutdown_all_configurations=AsyncMock(return_value=[]),
        )
        harness = SimpleNamespace(
            service_coordinator=coordinator,
            _shutdown_stop_task=object(),
            _start_shutdown_cleanup_thread=Mock(),
        )

        await MainWindow._stop_all_runtimes_before_cleanup(harness)

        coordinator.shutdown_all_configurations.assert_awaited_once_with(timeout=5.0)
        self.assertIsNone(harness._shutdown_stop_task)
        harness._start_shutdown_cleanup_thread.assert_called_once_with()

    async def test_cancelled_graceful_stop_preserves_cancellation_and_starts_fallback(self):
        coordinator = SimpleNamespace(
            shutdown_all_configurations=AsyncMock(side_effect=asyncio.CancelledError),
        )
        harness = SimpleNamespace(
            service_coordinator=coordinator,
            _shutdown_stop_task=object(),
            _start_shutdown_cleanup_thread=Mock(),
        )

        with self.assertRaises(asyncio.CancelledError):
            await MainWindow._stop_all_runtimes_before_cleanup(harness)

        self.assertIsNone(harness._shutdown_stop_task)
        harness._start_shutdown_cleanup_thread.assert_called_once_with()


class MainWindowShutdownSchedulingTests(unittest.TestCase):
    def test_missing_running_loop_falls_back_without_creating_coroutine(self):
        harness = SimpleNamespace(
            _shutdown_cleanup_completed=False,
            _shutdown_cleanup_started=False,
            _allow_window_close=False,
            _start_shutdown_cleanup_thread=Mock(),
        )

        with patch("app.view.main_window.main_window.logger"):
            MainWindow.clear_thread_async(harness)

        self.assertTrue(harness._shutdown_cleanup_started)
        harness._start_shutdown_cleanup_thread.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()