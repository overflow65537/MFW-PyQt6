import json
import unittest
from unittest.mock import patch

from PySide6.QtCore import QCoreApplication

from app.ipc.local_client import LocalIpcClient
from app.ipc.local_server import (
    LEGACY_ACCEPTED,
    LEGACY_ACTIVATE,
    LEGACY_BUSY,
    LEGACY_INVALID,
    LEGACY_OK,
    LEGACY_RUN_PREFIX,
    LEGACY_SHUTDOWN,
    LocalIpcServer,
)
from app.ipc.protocol import (
    IPC_VERSION,
    MAX_IPC_PAYLOAD,
    IpcCommand,
    IpcProtocolError,
    IpcRequest,
    IpcResponse,
    IpcStatus,
    decode_request,
    decode_response,
    encode_request,
    encode_response,
)


class IpcProtocolTests(unittest.TestCase):
    def test_request_and_response_round_trip_with_unicode_config_id(self):
        request = IpcRequest(
            IpcCommand.RUN,
            {"config_id": "配置-甲", "force_restart": False},
            request_id="request-1",
        )
        decoded_request = decode_request(encode_request(request))
        self.assertEqual(request, decoded_request)

        response = IpcResponse.ok(
            request,
            status=IpcStatus.ACCEPTED,
            code="queued",
            data={"config_id": "配置-甲"},
        )
        decoded_response = decode_response(encode_response(response))
        self.assertEqual(response, decoded_response)

    def test_unknown_command_is_rejected(self):
        payload = json.dumps(
            {
                "version": IPC_VERSION,
                "request_id": "request-2",
                "command": "unknown",
                "params": {},
            }
        ).encode()
        with self.assertRaises(IpcProtocolError) as raised:
            decode_request(payload)
        self.assertEqual("unknown_command", raised.exception.code)
        self.assertEqual("request-2", raised.exception.request_id)

    def test_unsupported_version_is_rejected(self):
        payload = json.dumps(
            {
                "version": IPC_VERSION + 1,
                "request_id": "request-3",
                "command": "status",
                "params": {},
            }
        ).encode()
        with self.assertRaises(IpcProtocolError) as raised:
            decode_request(payload)
        self.assertEqual("unsupported_version", raised.exception.code)

    def test_missing_params_is_rejected(self):
        payload = json.dumps(
            {
                "version": IPC_VERSION,
                "request_id": "request-4",
                "command": "status",
            }
        ).encode()
        with self.assertRaises(IpcProtocolError) as raised:
            decode_request(payload)
        self.assertEqual("missing_params", raised.exception.code)

    def test_invalid_json_is_rejected(self):
        with self.assertRaises(IpcProtocolError) as raised:
            decode_request(b"{not-json")
        self.assertEqual("invalid_json", raised.exception.code)

    def test_oversized_payload_is_rejected(self):
        with self.assertRaises(IpcProtocolError) as raised:
            decode_request(b"x" * (MAX_IPC_PAYLOAD + 1))
        self.assertEqual("payload_too_large", raised.exception.code)


class _FakeSocket:
    def __init__(self, chunks=()):
        self.chunks = list(chunks)
        self.writes = []
        self.disconnected = False
        self.deleted = False

    def readAll(self):
        return self.chunks.pop(0) if self.chunks else b""

    def write(self, payload):
        self.writes.append(bytes(payload))
        return len(payload)

    def flush(self):
        return True

    def waitForBytesWritten(self, _timeout):
        return True

    def disconnectFromServer(self):
        self.disconnected = True

    def deleteLater(self):
        self.deleted = True


class LocalIpcServerFramingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QCoreApplication.instance() or QCoreApplication([])

    def _make_server(self):
        server = LocalIpcServer("test-ipc")
        requests = []

        def handler(request):
            requests.append(request)
            return IpcResponse.ok(request, status=IpcStatus.ACCEPTED)

        server.set_command_handler(handler)
        return server, requests

    def test_new_protocol_waits_for_complete_newline_delimited_frame(self):
        server, requests = self._make_server()
        payload = encode_request(
            IpcRequest(IpcCommand.RUN, {"config_id": "??-A"}, request_id="split")
        )
        split_at = len(payload) // 2
        socket = _FakeSocket([payload[:split_at], payload[split_at:]])
        server._buffers[socket] = bytearray()

        server._consume(socket)
        self.assertEqual([], requests)
        self.assertEqual([], socket.writes)
        self.assertFalse(socket.disconnected)

        server._consume(socket)
        self.assertEqual(1, len(requests))
        self.assertEqual("??-A", requests[0].params["config_id"])
        self.assertEqual(IpcStatus.ACCEPTED, decode_response(socket.writes[0]).status)
        self.assertTrue(socket.disconnected)

    def test_only_first_request_on_connection_is_dispatched(self):
        server, requests = self._make_server()
        first = IpcRequest(IpcCommand.STATUS, request_id="first")
        second = IpcRequest(IpcCommand.STATUS, request_id="second")
        socket = _FakeSocket([encode_request(first) + encode_request(second)])
        server._buffers[socket] = bytearray()

        server._consume(socket)

        self.assertEqual(["first"], [request.request_id for request in requests])
        self.assertEqual("first", decode_response(socket.writes[0]).request_id)
        self.assertTrue(socket.disconnected)

    def test_oversized_transport_payload_gets_invalid_response(self):
        server, requests = self._make_server()
        socket = _FakeSocket([b"{" + b"x" * (MAX_IPC_PAYLOAD + 1)])
        server._buffers[socket] = bytearray()

        server._consume(socket)

        self.assertEqual([], requests)
        response = decode_response(socket.writes[0])
        self.assertEqual(IpcStatus.INVALID, response.status)
        self.assertEqual("payload_too_large", response.code)

    def test_legacy_commands_are_mapped_and_replied(self):
        cases = (
            (LEGACY_ACTIVATE, IpcCommand.ACTIVATE, LEGACY_OK, IpcStatus.OK),
            (LEGACY_SHUTDOWN, IpcCommand.SHUTDOWN, LEGACY_ACCEPTED, IpcStatus.ACCEPTED),
            (
                LEGACY_RUN_PREFIX
                + json.dumps(
                    {"config_id": "??-B", "force_start": True},
                    ensure_ascii=False,
                ).encode("utf-8"),
                IpcCommand.RUN,
                LEGACY_BUSY,
                IpcStatus.BUSY,
            ),
        )
        for payload, command, expected_reply, status in cases:
            with self.subTest(command=command):
                server = LocalIpcServer("legacy-ipc")
                received = []

                def handler(request, response_status=status):
                    received.append(request)
                    return IpcResponse.ok(request, status=response_status)

                server.set_command_handler(handler)
                socket = _FakeSocket([payload])
                server._buffers[socket] = bytearray()
                server._consume(socket)

                self.assertEqual(command, received[0].command)
                self.assertEqual(expected_reply, socket.writes[0])
                if command == IpcCommand.RUN:
                    self.assertEqual("??-B", received[0].params["config_id"])
                    self.assertTrue(received[0].params["force_restart"])

    def test_legacy_activate_can_arrive_in_parts(self):
        server, requests = self._make_server()
        socket = _FakeSocket([b"acti", b"vate"])
        server._buffers[socket] = bytearray()

        server._consume(socket)
        self.assertEqual([], requests)
        server._consume(socket)

        self.assertEqual(IpcCommand.ACTIVATE, requests[0].command)
        self.assertEqual(LEGACY_ACCEPTED, socket.writes[0])

    def test_unknown_legacy_command_is_invalid(self):
        server, requests = self._make_server()
        socket = _FakeSocket([b"not-a-command"])
        server._buffers[socket] = bytearray()

        server._consume(socket)

        self.assertEqual([], requests)
        self.assertEqual(LEGACY_INVALID, socket.writes[0])


class LocalIpcClientTests(unittest.TestCase):
    def test_response_request_id_mismatch_is_rejected(self):
        response = IpcResponse(
            status=IpcStatus.OK,
            request_id="other-request",
        )

        class FakeClientSocket:
            def __init__(self):
                self._response = encode_response(response)

            def connectToServer(self, _name):
                pass

            def waitForConnected(self, _timeout):
                return True

            def write(self, payload):
                return len(payload)

            def flush(self):
                return True

            def waitForBytesWritten(self, _timeout):
                return True

            def waitForReadyRead(self, _timeout):
                return True

            def readAll(self):
                payload, self._response = self._response, b""
                return payload

            def errorString(self):
                return ""

            def disconnectFromServer(self):
                pass

        request = IpcRequest(IpcCommand.STATUS, request_id="expected-request")
        with patch("PySide6.QtNetwork.QLocalSocket", FakeClientSocket):
            result = LocalIpcClient("test-ipc").send_command(request)

        self.assertEqual(IpcStatus.ERROR, result.status)
        self.assertEqual("request_id_mismatch", result.code)
        self.assertEqual("expected-request", result.request_id)


if __name__ == "__main__":
    unittest.main()
