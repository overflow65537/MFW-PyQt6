"""QLocalServer transport for the versioned application command protocol."""

from __future__ import annotations

import json
from collections.abc import Callable

from PySide6.QtCore import QObject

from app.ipc.protocol import (
    MAX_IPC_PAYLOAD,
    IpcCommand,
    IpcProtocolError,
    IpcRequest,
    IpcResponse,
    IpcStatus,
    decode_request,
    encode_response,
)
from app.utils.logger import logger

CommandHandler = Callable[[IpcRequest], IpcResponse]

LEGACY_ACTIVATE = b"activate"
LEGACY_SHUTDOWN = b"shutdown"
LEGACY_RUN_PREFIX = b"run-config:"
LEGACY_OK = b"ok"
LEGACY_ACCEPTED = b"accepted"
LEGACY_FAIL = b"fail"
LEGACY_BUSY = b"busy"
LEGACY_INVALID = b"invalid"


class LocalIpcServer(QObject):
    """Transport-only local server; each connection handles one command."""

    def __init__(self, server_name: str, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.server_name = str(server_name)
        self._server = None
        self._command_handler: CommandHandler | None = None
        self._buffers: dict[object, bytearray] = {}

    def set_command_handler(self, handler: CommandHandler | None) -> None:
        self._command_handler = handler

    def start(self) -> bool:
        from PySide6.QtNetwork import QLocalServer

        try:
            QLocalServer.removeServer(self.server_name)
        except Exception:
            pass
        self._server = QLocalServer(self)
        self._server.newConnection.connect(self._handle_new_connection)
        if self._server.listen(self.server_name):
            return True
        self._server.deleteLater()
        self._server = None
        return False

    def close(self) -> None:
        if self._server is None:
            return
        try:
            self._server.close()
        finally:
            try:
                from PySide6.QtNetwork import QLocalServer

                QLocalServer.removeServer(self.server_name)
            except Exception:
                pass
            self._buffers.clear()
            self._server.deleteLater()
            self._server = None

    def _handle_new_connection(self) -> None:
        if self._server is None:
            return
        while self._server.hasPendingConnections():
            socket = self._server.nextPendingConnection()
            if socket is None:
                continue
            socket.setParent(self._server)
            self._buffers[socket] = bytearray()
            socket.readyRead.connect(
                lambda current_socket=socket: self._consume(current_socket)
            )
            socket.disconnected.connect(
                lambda current_socket=socket: self._discard(current_socket)
            )
            if socket.bytesAvailable() > 0:
                self._consume(socket)

    def _discard(self, socket) -> None:
        self._buffers.pop(socket, None)
        socket.deleteLater()

    def _consume(self, socket) -> None:
        buffer = self._buffers.get(socket)
        if buffer is None:
            return
        try:
            buffer.extend(bytes(socket.readAll()))
        except Exception:
            self._reply_and_close(
                socket,
                IpcResponse.invalid(code="read_failed"),
            )
            return

        if len(buffer) > MAX_IPC_PAYLOAD + 1:
            self._reply_and_close(
                socket,
                IpcResponse.invalid(code="payload_too_large"),
            )
            return

        raw = bytes(buffer)
        try:
            legacy_request = self._decode_legacy_request(raw)
        except IpcProtocolError as exc:
            self._reply_legacy_and_close(socket, exc.to_response())
            return
        if legacy_request is not None:
            response = self._dispatch(legacy_request)
            self._reply_legacy_and_close(socket, response)
            return

        if not raw.lstrip().startswith((b"{", b"[")):
            # A legacy run-config frame may arrive in pieces. Wait while the
            # bytes are still a prefix of a known command.
            if self._is_legacy_prefix(raw):
                return
            self._reply_legacy_and_close(
                socket,
                IpcResponse.invalid(code="unknown_legacy_command"),
            )
            return

        if b"\n" not in buffer:
            return

        frame, _, _rest = raw.partition(b"\n")
        try:
            request = decode_request(frame)
            response = self._dispatch(request)
        except IpcProtocolError as exc:
            response = exc.to_response()
        except Exception as exc:
            logger.exception("IPC request handling failed")
            response = IpcResponse(
                status=IpcStatus.ERROR,
                request_id="",
                code="internal_error",
                message=str(exc),
            )
        self._reply_and_close(socket, response)

    @staticmethod
    def _is_legacy_prefix(payload: bytes) -> bool:
        stripped = payload.strip().lower()
        if not stripped:
            return True
        return any(
            command.startswith(stripped)
            for command in (LEGACY_ACTIVATE, LEGACY_SHUTDOWN, LEGACY_RUN_PREFIX)
        ) or stripped.startswith(LEGACY_RUN_PREFIX)

    @staticmethod
    def _decode_legacy_request(payload: bytes) -> IpcRequest | None:
        stripped = payload.strip()
        lowered = stripped.lower()
        if lowered == LEGACY_ACTIVATE:
            return IpcRequest(IpcCommand.ACTIVATE)
        if lowered == LEGACY_SHUTDOWN:
            return IpcRequest(IpcCommand.SHUTDOWN, {"reason": "external"})
        if not stripped.startswith(LEGACY_RUN_PREFIX):
            return None
        try:
            params = json.loads(stripped[len(LEGACY_RUN_PREFIX) :].decode("utf-8"))
        except json.JSONDecodeError as exc:
            if exc.pos >= max(0, len(exc.doc) - 1):
                return None
            raise IpcProtocolError("invalid_legacy_request") from exc
        except (TypeError, ValueError, UnicodeDecodeError) as exc:
            raise IpcProtocolError("invalid_legacy_request") from exc
        if not isinstance(params, dict):
            raise IpcProtocolError("invalid_legacy_request")
        return IpcRequest(
            IpcCommand.RUN,
            {
                "config_id": params.get("config_id"),
                "force_restart": bool(params.get("force_start", False)),
            },
        )

    def _dispatch(self, request: IpcRequest) -> IpcResponse:
        if self._command_handler is None:
            return IpcResponse(
                status=IpcStatus.ERROR,
                request_id=request.request_id,
                code="handler_unavailable",
            )
        response = self._command_handler(request)
        if not isinstance(response, IpcResponse):
            return IpcResponse(
                status=IpcStatus.ERROR,
                request_id=request.request_id,
                code="invalid_handler_response",
            )
        return response

    @staticmethod
    def _legacy_response_bytes(response: IpcResponse) -> bytes:
        if response.status == IpcStatus.OK:
            return LEGACY_OK
        if response.status == IpcStatus.ACCEPTED:
            return LEGACY_ACCEPTED
        if response.status == IpcStatus.BUSY:
            return LEGACY_BUSY
        if response.status in {IpcStatus.INVALID, IpcStatus.NOT_FOUND}:
            return LEGACY_INVALID
        return LEGACY_FAIL

    def _reply_legacy_and_close(self, socket, response: IpcResponse) -> None:
        self._reply_bytes_and_close(socket, self._legacy_response_bytes(response), response)

    def _reply_and_close(self, socket, response: IpcResponse) -> None:
        self._reply_bytes_and_close(socket, encode_response(response), response)

    def _reply_bytes_and_close(
        self, socket, payload: bytes, response: IpcResponse
    ) -> None:
        try:
            socket.write(payload)
            socket.flush()
            socket.waitForBytesWritten(800)
            logger.info(
                "IPC replied request_id=%s status=%s code=%s",
                response.request_id,
                response.status.value,
                response.code,
            )
        except Exception:
            logger.debug("IPC response write failed", exc_info=True)
        finally:
            self._buffers.pop(socket, None)
            try:
                socket.disconnectFromServer()
            except Exception:
                pass
