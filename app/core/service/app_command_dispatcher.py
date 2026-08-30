"""Serialize application-level control commands independently of IPC transport."""

from __future__ import annotations

import asyncio
import inspect
import os
from collections import deque
from typing import Any, Awaitable, Callable, Protocol

from PySide6.QtCore import Qt, QTimer

from app.ipc.protocol import IpcCommand, IpcRequest, IpcResponse, IpcStatus
from app.utils.logger import logger

CloseCallback = Callable[[], Awaitable[Any] | Any]


class _ConfigFacadeProtocol(Protocol):
    current_config_id: str

    def get_config(self, config_id: str) -> object | None: ...


class _CoordinatorProtocol(Protocol):
    configs: _ConfigFacadeProtocol

    def get_running_config_ids(self) -> list[str]: ...

    def select_config(self, config_id: str) -> bool: ...

    async def run_configuration(self, config_id: str) -> bool: ...

    async def stop_configuration(
        self, config_id: str, *, manual: bool = True
    ) -> bool: ...

    async def shutdown_all_configurations(
        self, *, manual: bool = False
    ) -> list[str]: ...


class _WindowProtocol(Protocol):
    service_coordinator: _CoordinatorProtocol
    _allow_window_close: bool

    def isVisible(self) -> bool: ...
    def show(self) -> None: ...
    def windowState(self): ...
    def showNormal(self) -> None: ...
    def raise_(self) -> None: ...
    def activateWindow(self) -> None: ...
    def winId(self): ...
    def close(self) -> None: ...


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
        self._window: _WindowProtocol | None = None
        self._coordinator: _CoordinatorProtocol | None = None
        self._pending_commands: deque[IpcRequest] = deque()
        self._command_queue: asyncio.Queue[IpcRequest] = asyncio.Queue()
        self._worker_task: asyncio.Task[Any] | None = None
        self._shutting_down = False
        self._run_reservations: set[str] = set()
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

    def attach_window(self, window: _WindowProtocol) -> None:
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
            self._run_reservations.add(self._run_reservation_key(request.params))

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
        self._run_reservations.clear()
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
            reservation_key = self._run_reservation_key(params)
            if reservation_key in self._run_reservations:
                return IpcResponse(
                    status=IpcStatus.BUSY,
                    request_id=request.request_id,
                    code="command_in_progress",
                )
            if self.ready and not force_restart:
                target_id = config_id or self._coordinator.configs.current_config_id
                if target_id and str(target_id) in self._running_config_ids():
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

    @staticmethod
    def _run_reservation_key(params: dict[str, Any]) -> str:
        value = params.get("config_id")
        if isinstance(value, str) and value.strip():
            return value.strip()
        return "__active__"

    def _config_exists(self, config_id: str) -> bool:
        return bool(self._coordinator.configs.get_config(config_id))

    def _running_config_ids(self) -> list[str]:
        if not self.ready:
            return []
        return [
            str(config_id)
            for config_id in self._coordinator.get_running_config_ids()
            if config_id
        ]

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
                    self._run_reservations.discard(
                        self._run_reservation_key(request.params)
                    )
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
        if force_restart and self._is_running():
            pending = await self._coordinator.shutdown_all_configurations(manual=True)
            if pending:
                logger.warning(
                    "Force-restart runtimes missed the graceful deadline: %s",
                    ", ".join(map(str, pending)),
                )

        config_id = self._optional_config_id(request.params)
        target_id = (
            config_id
            if isinstance(config_id, str)
            else self._coordinator.configs.current_config_id
        )
        if not target_id:
            logger.warning("Run requested without an active configuration")
            return

        started = await self._coordinator.run_configuration(target_id)
        if not started:
            logger.warning(
                "Run target no longer exists or is busy: %s", target_id
            )

    async def _stop(self, config_id: str | None = None) -> None:
        target_id = config_id or self._coordinator.configs.current_config_id
        if not target_id:
            return
        await self._coordinator.stop_configuration(target_id, manual=True)

    async def _shutdown(self) -> None:
        pending = await self._coordinator.shutdown_all_configurations(manual=False)
        if pending:
            logger.warning(
                "Shutdown runtimes missed the graceful deadline: %s",
                ", ".join(map(str, pending)),
            )
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
