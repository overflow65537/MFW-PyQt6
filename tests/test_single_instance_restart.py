import unittest
from pathlib import Path

from app.utils.single_instance import (
    CMD_ACTIVATE,
    CMD_SHUTDOWN,
    process_matches_install_anchor,
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

    def test_shutdown_command_constants(self) -> None:
        self.assertEqual(CMD_ACTIVATE, b"activate")
        self.assertEqual(CMD_SHUTDOWN, b"shutdown")


if __name__ == "__main__":
    unittest.main()
