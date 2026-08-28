import unittest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from app.ipc.protocol import IpcResponse, IpcStatus
from app.utils.single_instance import (
    CMD_ACTIVATE,
    CMD_RUN_CONFIG,
    CMD_SHUTDOWN,
    RESP_OK,
    process_matches_install_anchor,
    try_activate_existing_instance,
    try_force_terminate_stale_instance,
)


class ProcessMatchesInstallAnchorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.anchor = Path(r"D:\MFW\MFW.exe").resolve()

    def test_matches_same_executable(self) -> None:
        self.assertTrue(
            process_matches_install_anchor(
                pid=100,
                exe=str(self.anchor),
                cmdline=[str(self.anchor)],
                anchor_path=self.anchor,
            )
        )

    def test_matches_macos_app_bundle_executable(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            anchor = Path(raw) / "MFW.app" / "Contents" / "MacOS" / "MFW"
            anchor.parent.mkdir(parents=True)
            anchor.touch()
            self.assertTrue(
                process_matches_install_anchor(
                    pid=101,
                    exe=str(anchor),
                    cmdline=[str(anchor)],
                    anchor_path=anchor,
                )
            )

    def test_shutdown_command_constants(self) -> None:
        self.assertEqual(CMD_ACTIVATE, b"activate")
        self.assertEqual(CMD_SHUTDOWN, b"shutdown")
        self.assertEqual(CMD_RUN_CONFIG, b"run-config:")
        self.assertEqual(RESP_OK, b"ok")

    @patch("app.utils.single_instance.LocalIpcClient")
    def test_pending_activation_is_treated_as_success(self, client_cls: Mock) -> None:
        client_cls.return_value.activate.return_value = IpcResponse(
            status=IpcStatus.ACCEPTED,
            request_id="activate-request",
        )

        self.assertTrue(try_activate_existing_instance("test-server"))

    @patch("app.utils.single_instance.is_running_with_admin_privileges", return_value=False)
    def test_force_terminate_requires_admin(self, _mock_admin: object) -> None:
        self.assertFalse(
            try_force_terminate_stale_instance(str(self.anchor), exclude_pid=99999)
        )


if __name__ == "__main__":
    unittest.main()
