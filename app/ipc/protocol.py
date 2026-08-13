"""Versioned request/response models for the local IPC control plane."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Mapping

IPC_VERSION = 1
MAX_IPC_PAYLOAD = 64 * 1024


class IpcCommand(StrEnum):
    ACTIVATE = "activate"
    SWITCH_CONFIG = "switch_config"
    RUN = "run"
    STOP = "stop"
    SHUTDOWN = "shutdown"
    STATUS = "status"


class IpcStatus(StrEnum):
    OK = "ok"
    ACCEPTED = "accepted"
    BUSY = "busy"
    INVALID = "invalid"
    NOT_FOUND = "not_found"
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class IpcRequest:
    command: IpcCommand
    params: dict[str, Any] = field(default_factory=dict)
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    version: int = IPC_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "request_id": self.request_id,
            "command": self.command.value,
            "params": dict(self.params),
        }


@dataclass(frozen=True, slots=True)
class IpcResponse:
    status: IpcStatus
    request_id: str
    code: str = "ok"
    message: str = ""
    data: dict[str, Any] = field(default_factory=dict)
    version: int = IPC_VERSION

    @property
    def succeeded(self) -> bool:
        return self.status in {IpcStatus.OK, IpcStatus.ACCEPTED}

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "request_id": self.request_id,
            "status": self.status.value,
            "code": self.code,
            "message": self.message,
            "data": dict(self.data),
        }

    @classmethod
    def ok(
        cls,
        request: IpcRequest,
        *,
        status: IpcStatus = IpcStatus.OK,
        code: str = "ok",
        message: str = "",
        data: Mapping[str, Any] | None = None,
    ) -> "IpcResponse":
        return cls(
            status=status,
            request_id=request.request_id,
            code=code,
            message=message,
            data=dict(data or {}),
        )

    @classmethod
    def invalid(
        cls,
        request_id: str = "",
        *,
        code: str,
        message: str = "",
    ) -> "IpcResponse":
        return cls(
            status=IpcStatus.INVALID,
            request_id=request_id,
            code=code,
            message=message,
        )


class IpcProtocolError(ValueError):
    def __init__(self, code: str, message: str = "", request_id: str = "") -> None:
        super().__init__(message or code)
        self.code = code
        self.message = message
        self.request_id = request_id

    def to_response(self) -> IpcResponse:
        return IpcResponse.invalid(
            self.request_id,
            code=self.code,
            message=self.message,
        )


def _encode_json(payload: Mapping[str, Any]) -> bytes:
    try:
        encoded = json.dumps(
            payload,
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise IpcProtocolError("invalid_json", str(exc)) from exc
    if len(encoded) > MAX_IPC_PAYLOAD:
        raise IpcProtocolError("payload_too_large")
    return encoded + b"\n"


def encode_request(request: IpcRequest) -> bytes:
    return _encode_json(request.to_dict())


def encode_response(response: IpcResponse) -> bytes:
    return _encode_json(response.to_dict())


def _decode_json(payload: bytes) -> dict[str, Any]:
    raw = bytes(payload).rstrip(b"\r\n")
    if len(raw) > MAX_IPC_PAYLOAD:
        raise IpcProtocolError("payload_too_large")
    try:
        decoded = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise IpcProtocolError("invalid_json", str(exc)) from exc
    if not isinstance(decoded, dict):
        raise IpcProtocolError("invalid_message", "IPC message must be an object")
    return decoded


def decode_request(payload: bytes) -> IpcRequest:
    decoded = _decode_json(payload)
    request_id = decoded.get("request_id")
    if not isinstance(request_id, str) or not request_id.strip():
        raise IpcProtocolError("missing_request_id")
    request_id = request_id.strip()

    version = decoded.get("version")
    if version != IPC_VERSION:
        raise IpcProtocolError("unsupported_version", request_id=request_id)

    raw_command = decoded.get("command")
    if not isinstance(raw_command, str) or not raw_command:
        raise IpcProtocolError("missing_command", request_id=request_id)
    try:
        command = IpcCommand(raw_command)
    except ValueError as exc:
        raise IpcProtocolError("unknown_command", request_id=request_id) from exc

    params = decoded.get("params")
    if params is None:
        raise IpcProtocolError("missing_params", request_id=request_id)
    if not isinstance(params, dict):
        raise IpcProtocolError("invalid_params", request_id=request_id)

    return IpcRequest(
        version=version,
        request_id=request_id,
        command=command,
        params=dict(params),
    )


def decode_response(payload: bytes) -> IpcResponse:
    decoded = _decode_json(payload)
    request_id = decoded.get("request_id")
    if not isinstance(request_id, str):
        raise IpcProtocolError("missing_request_id")
    if decoded.get("version") != IPC_VERSION:
        raise IpcProtocolError("unsupported_version", request_id=request_id)
    try:
        status = IpcStatus(decoded.get("status"))
    except (TypeError, ValueError) as exc:
        raise IpcProtocolError("invalid_status", request_id=request_id) from exc

    code = decoded.get("code", "ok")
    message = decoded.get("message", "")
    data = decoded.get("data", {})
    if not isinstance(code, str) or not isinstance(message, str) or not isinstance(data, dict):
        raise IpcProtocolError("invalid_response", request_id=request_id)
    return IpcResponse(
        version=IPC_VERSION,
        request_id=request_id,
        status=status,
        code=code,
        message=message,
        data=dict(data),
    )
