"""Synchronous local IPC client used by secondary application processes."""

from __future__ import annotations

from app.ipc.protocol import (
    MAX_IPC_PAYLOAD,
    IpcCommand,
    IpcProtocolError,
    IpcRequest,
    IpcResponse,
    IpcStatus,
    decode_response,
    encode_request,
)
from app.utils.logger import logger


class LocalIpcClient:
    def __init__(
        self,
        server_name: str,
        *,
        connect_ms: int = 800,
        response_ms: int = 5000,
    ) -> None:
        self.server_name = str(server_name)
        self.connect_ms = int(connect_ms)
        self.response_ms = int(response_ms)

    def send_command(self, request: IpcRequest) -> IpcResponse:
        try:
            from PySide6.QtNetwork import QLocalSocket
        except Exception as exc:
            return IpcResponse(
                status=IpcStatus.ERROR,
                request_id=request.request_id,
                code="transport_unavailable",
                message=str(exc),
            )

        socket = QLocalSocket()
        socket.connectToServer(self.server_name)
        if not socket.waitForConnected(self.connect_ms):
            return IpcResponse(
                status=IpcStatus.ERROR,
                request_id=request.request_id,
                code="connect_failed",
                message=socket.errorString(),
            )

        try:
            payload = encode_request(request)
            socket.write(payload)
            socket.flush()
            if not socket.waitForBytesWritten(self.connect_ms):
                return IpcResponse(
                    status=IpcStatus.ERROR,
                    request_id=request.request_id,
                    code="write_failed",
                    message=socket.errorString(),
                )

            buffer = bytearray()
            while b"\n" not in buffer:
                if not socket.waitForReadyRead(self.response_ms):
                    return IpcResponse(
                        status=IpcStatus.ERROR,
                        request_id=request.request_id,
                        code="response_timeout",
                        message=socket.errorString(),
                    )
                buffer.extend(bytes(socket.readAll()))
                if len(buffer) > MAX_IPC_PAYLOAD + 1:
                    return IpcResponse(
                        status=IpcStatus.ERROR,
                        request_id=request.request_id,
                        code="payload_too_large",
                    )

            frame, _, _rest = bytes(buffer).partition(b"\n")
            response = decode_response(frame)
            if response.request_id != request.request_id:
                return IpcResponse(
                    status=IpcStatus.ERROR,
                    request_id=request.request_id,
                    code="request_id_mismatch",
                )
            return response
        except IpcProtocolError as exc:
            logger.debug("IPC response protocol error: %s", exc)
            return IpcResponse(
                status=IpcStatus.ERROR,
                request_id=request.request_id,
                code=exc.code,
                message=exc.message,
            )
        except Exception as exc:
            logger.debug("IPC client error: %s", exc)
            return IpcResponse(
                status=IpcStatus.ERROR,
                request_id=request.request_id,
                code="transport_error",
                message=str(exc),
            )
        finally:
            try:
                socket.disconnectFromServer()
            except Exception:
                pass

    def activate(self) -> IpcResponse:
        return self.send_command(IpcRequest(IpcCommand.ACTIVATE))

    def switch_config(self, config_id: str) -> IpcResponse:
        return self.send_command(
            IpcRequest(IpcCommand.SWITCH_CONFIG, {"config_id": config_id})
        )

    def run(
        self,
        config_id: str | None = None,
        *,
        force_restart: bool = False,
    ) -> IpcResponse:
        return self.send_command(
            IpcRequest(
                IpcCommand.RUN,
                {
                    "config_id": config_id,
                    "force_restart": bool(force_restart),
                },
            )
        )

    def stop(self, config_id: str | None = None) -> IpcResponse:
        return self.send_command(
            IpcRequest(IpcCommand.STOP, {"config_id": config_id})
        )

    def shutdown(self, reason: str = "user") -> IpcResponse:
        return self.send_command(
            IpcRequest(IpcCommand.SHUTDOWN, {"reason": reason})
        )

    def status(self) -> IpcResponse:
        return self.send_command(IpcRequest(IpcCommand.STATUS))
