"""Serialize application-level control commands independently of IPC transport."""

from __future__ import annotations

import asyncio
import inspect
import os
from collections import deque
from typing import Any, Awaitable, Callable

from PySide6.QtCore import Qt, QTimer

from app.ipc.protocol import IpcCommand, IpcRequest, IpcResponse, IpcStatus
from app.utils.logger import logger

CloseCallback = Callable[[], Awaitable[Any] | Any]


class AppCommandDispatcher:
    """Validate, queue and execute commands against the application runtime."""

    _MUTATING_COMMANDS = frozenset(
        {
            IpcCommand.SWITCH_CONFIG,
            IpcCommand.RUN,
            IpcCommand.STOP,
            IpcCommand.SHUTDOWN,
        }
    )

    def __init__(
        self,
        loop: asyncio.AbstractEventLoop,
        *,
        close_callback: CloseCallback | None = None,
    ) -> None:
        self._loop = loop
        self._close_callback = close_callback
        self._window: Any | None = None
        self._coordinator: Any | None = None
        self._pending_commands: deque[IpcRequest] = deque()
        self._command_queue: asyncio.Queue[IpcRequest] = asyncio.Queue()
        self._worker_task: asyncio.Task[Any] | None = None
        self._shutting_down = False
        self._run_reserved = False
        self._closed = False

    @property
    def ready(self) -> bool:
        return self._window is not None and self._coordinator is not None

    @property
    def window(self) -> Any | None:
        return self._window

    @property
    def shutting_down(self) -> bool:
        return self._shutting_down

    def attach_window(self, window: Any) -> None:
        """Attach the application facade and drain startup commands exactly once."""
        if self._closed:
            return
        self._window = window
        self._coordinator = window.service_coordinator
        self._ensure_worker()
        while self._pending_commands:
            self._command_queue.put_nowait(self._pending_commands.popleft())

    def submit(
        self,
        request: IpcRequest,
        *,
        allow_pending_mutations: bool = False,
    ) -> IpcResponse:
        """Validate a command and synchronously return its admission result."""
        logger.info(
            "IPC received request_id=%s command=%s config_id=%s",
            request.request_id,
            request.command.value,
            request.params.get("config_id"),
        )
        validation = self._validate(request)
        if validation is not None:
            logger.info(
                "IPC rejected request_id=%s status=%s code=%s",
                request.request_id,
                validation.status.value,
                validation.code,
            )
            return validation

        if request.command == IpcCommand.STATUS:
            return IpcResponse.ok(request, data=self._status_data())

        if request.command == IpcCommand.ACTIVATE and self.ready:
            try:
                self._activate_window()
                return IpcResponse.ok(request)
            except Exception as exc:
                logger.exception("Window activation failed")
                return IpcResponse(
                    status=IpcStatus.ERROR,
                    request_id=request.request_id,
                    code="activate_failed",
                    message=str(exc),
                )

        if (
            not self.ready
            and request.command in self._MUTATING_COMMANDS
            and request.command != IpcCommand.SHUTDOWN
            and not allow_pending_mutations
        ):
            response = IpcResponse(
                status=IpcStatus.BUSY,
                request_id=request.request_id,
                code="application_not_ready",
            )
            logger.info(
                "IPC rejected request_id=%s status=%s code=%s",
                request.request_id,
                response.status.value,
                response.code,
            )
            return response

        if request.command == IpcCommand.SHUTDOWN:
            self._shutting_down = True
        elif request.command == IpcCommand.RUN:
            self._run_reserved = True

        if not self.ready:
            self._pending_commands.append(request)
        else:
            self._ensure_worker()
            self._command_queue.put_nowait(request)

        logger.info(
            "IPC accepted request_id=%s command=%s",
            request.request_id,
            request.command.value,
        )
        return IpcResponse.ok(request, status=IpcStatus.ACCEPTED)

    def submit_startup(self, request: IpcRequest) -> IpcResponse:
        """Use the same command path for this process' startup request."""
        return self.submit(request, allow_pending_mutations=True)

    async def wait_idle(self) -> None:
        """Wait until all currently queued commands have completed."""
        await self._command_queue.join()

    async def close(self) -> None:
        self._closed = True
        self._pending_commands.clear()
        self._run_reserved = False
        task = self._worker_task
        self._worker_task = None
        if task is not None and not task.done():
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)

    def _validate(self, request: IpcRequest) -> IpcResponse | None:
        command = request.command
        params = request.params

        if self._closed:
            return IpcResponse(
                status=IpcStatus.ERROR,
                request_id=request.request_id,
                code="dispatcher_closed",
            )
        if self._shutting_down:
            if command == IpcCommand.SHUTDOWN:
                return IpcResponse.ok(
                    request,
                    status=IpcStatus.ACCEPTED,
                    code="already_shutting_down",
                )
            if command in self._MUTATING_COMMANDS:
                return IpcResponse(
                    status=IpcStatus.BUSY,
                    request_id=request.request_id,
                    code="shutting_down",
                )

        if command == IpcCommand.SWITCH_CONFIG:
            config_id = self._required_config_id(params)
            if config_id is None:
                return IpcResponse.invalid(
                    request.request_id,
                    code="invalid_config_id",
                )
            if self.ready and not self._config_exists(config_id):
                return IpcResponse(
                    status=IpcStatus.NOT_FOUND,
                    request_id=request.request_id,
                    code="config_not_found",
                )

        if command == IpcCommand.RUN:
            config_id = self._optional_config_id(params)
            if config_id is False:
                return IpcResponse.invalid(
                    request.request_id,
                    code="invalid_config_id",
                )
            force_restart = params.get("force_restart", False)
            if not isinstance(force_restart, bool):
                return IpcResponse.invalid(
                    request.request_id,
                    code="invalid_force_restart",
                )
            if self.ready and config_id and not self._config_exists(config_id):
                return IpcResponse(
                    status=IpcStatus.NOT_FOUND,
                    request_id=request.request_id,
                    code="config_not_found",
                )
            if self._run_reserved:
                return IpcResponse(
                    status=IpcStatus.BUSY,
                    request_id=request.request_id,
                    code="command_in_progress",
                )
            if self.ready and self._is_running() and not force_restart:
                return IpcResponse(
                    status=IpcStatus.BUSY,
                    request_id=request.request_id,
                    code="task_running",
                )

        if command == IpcCommand.STOP:
            config_id = self._optional_config_id(params)
            if config_id is False:
                return IpcResponse.invalid(
                    request.request_id,
                    code="invalid_config_id",
                )
            if self.ready and config_id and not self._config_exists(config_id):
                return IpcResponse(
                    status=IpcStatus.NOT_FOUND,
                    request_id=request.request_id,
                    code="config_not_found",
                )

        if command == IpcCommand.SHUTDOWN:
            reason = params.get("reason", "user")
            if not isinstance(reason, str):
                return IpcResponse.invalid(
                    request.request_id,
                    code="invalid_reason",
                )

        return None

    @staticmethod
    def _required_config_id(params: dict[str, Any]) -> str | None:
        value = params.get("config_id")
        if not isinstance(value, str) or not value.strip():
            return None
        return value.strip()

    @staticmethod
    def _optional_config_id(params: dict[str, Any]) -> str | bool | None:
        value = params.get("config_id")
        if value is None:
            return None
        if not isinstance(value, str):
            return False
        return value.strip() or None

    def _config_exists(self, config_id: str) -> bool:
        return bool(self._coordinator.configs.get_config(config_id))

    def _running_config_ids(self) -> list[str]:
        if not self.ready:
            return []
        value = getattr(self._coordinator, "get_running_config_ids", None)
        if callable(value):
            value = value()
        if value is not None:
            return [str(config_id) for config_id in value if config_id]
        if bool(self._coordinator.runtime.is_running):
            active = self._coordinator.configs.current_config_id
            return [active] if active else []
        return []

    def _is_running(self) -> bool:
        return bool(self._running_config_ids())

    def _status_data(self) -> dict[str, Any]:
        active_config_id = None
        running_config_ids: list[str] = []
        if self.ready:
            active_config_id = self._coordinator.configs.current_config_id
            running_config_ids = self._running_config_ids()
        return {
            "ready": self.ready,
            "active_config_id": active_config_id,
            "running": bool(running_config_ids),
            "running_config_ids": running_config_ids,
            "shutting_down": self._shutting_down,
        }

    def _ensure_worker(self) -> None:
        if self._worker_task is None or self._worker_task.done():
            self._worker_task = self._loop.create_task(self._worker())

    async def _worker(self) -> None:
        while not self._closed:
            request = await self._command_queue.get()
            try:
                if (
                    self._shutting_down
                    and request.command in self._MUTATING_COMMANDS
                    and request.command != IpcCommand.SHUTDOWN
                ):
                    logger.info(
                        "IPC dropped after shutdown request_id=%s command=%s",
                        request.request_id,
                        request.command.value,
                    )
                    continue
                await self._execute(request)
                logger.info(
                    "IPC completed request_id=%s command=%s",
                    request.request_id,
                    request.command.value,
                )
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception(
                    "IPC failed request_id=%s command=%s config_id=%s",
                    request.request_id,
                    request.command.value,
                    request.params.get("config_id"),
                )
            finally:
                if request.command == IpcCommand.RUN:
                    self._run_reserved = False
                self._command_queue.task_done()

    async def _execute(self, request: IpcRequest) -> None:
        command = request.command
        if command == IpcCommand.ACTIVATE:
            self._activate_window()
        elif command == IpcCommand.SWITCH_CONFIG:
            config_id = self._required_config_id(request.params)
            if config_id and not self._coordinator.select_config(config_id):
                logger.warning("Config disappeared before switch: %s", config_id)
        elif command == IpcCommand.RUN:
            await self._run(request)
        elif command == IpcCommand.STOP:
            await self._stop(request.params.get("config_id"))
        elif command == IpcCommand.SHUTDOWN:
            await self._shutdown()

    async def _run(self, request: IpcRequest) -> None:
        force_restart = bool(request.params.get("force_restart", False))
        if self._is_running():
            if not force_restart:
                logger.info("Run skipped because a task is already running")
                return
            await self._stop()

        config_id = self._optional_config_id(request.params)
        if isinstance(config_id, str):
            started = await self._coordinator.run_configuration(config_id)
            if not started:
                logger.warning("Run target no longer exists or is busy: %s", config_id)
            return

        active_config_id = self._coordinator.configs.current_config_id
        run_configuration = getattr(self._coordinator, "run_configuration", None)
        if active_config_id and callable(run_configuration):
            started = await run_configuration(active_config_id)
            if not started:
                logger.warning("Active configuration could not be started: %s", active_config_id)
            return
        await self._coordinator.runtime.run()

    async def _stop(self, config_id: str | None = None) -> None:
        stop_running = getattr(self._coordinator, "stop_running_configuration", None)
        if callable(stop_running):
            result = stop_running(config_id=config_id, manual=True)
            if inspect.isawaitable(result):
                await result
            return
        if bool(self._coordinator.runtime.is_running):
            await self._coordinator.runtime.stop(manual=True)

    async def _shutdown(self) -> None:
        await self._stop()
        callback = self._close_callback
        if callback is not None:
            result = callback()
            if inspect.isawaitable(result):
                await result
            return
        if self._window is not None:
            self._window._allow_window_close = True
            QTimer.singleShot(0, self._window.close)

    def _activate_window(self) -> None:
        window = self._window
        if window is None:
            return
        if not window.isVisible():
            window.show()
        if window.windowState() & Qt.WindowState.WindowMinimized:
            window.showNormal()
        window.raise_()
        window.activateWindow()

        if os.name == "nt":
            try:
                import ctypes

                user32 = ctypes.windll.user32
                hwnd = int(window.winId())
                user32.ShowWindow(hwnd, 9 if user32.IsIconic(hwnd) else 5)
                user32.SetForegroundWindow(hwnd)
            except Exception:
                logger.debug("Windows foreground activation failed", exc_info=True)
