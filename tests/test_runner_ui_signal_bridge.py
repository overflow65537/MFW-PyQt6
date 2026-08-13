import ast
import unittest
from pathlib import Path

from PySide6.QtCore import QCoreApplication, Qt

from app.common.signal_bus import signalBus
from app.core.core import _RunnerUiSignalBridge
from app.core.item import RunnerEvents


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RUNNER_ROOT = PROJECT_ROOT / "app" / "core" / "runner"


class RunnerUiSignalBridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QCoreApplication.instance() or QCoreApplication([])

    def test_start_button_status_is_forwarded_once_with_payload_unchanged(self):
        runner_events = RunnerEvents()
        bridge = _RunnerUiSignalBridge()
        received: list[dict] = []

        def collect(payload: dict) -> None:
            received.append(payload)

        signalBus.start_button_status.connect(collect)
        runner_events.start_button_status.connect(
            bridge.forward_start_button_status,
            Qt.ConnectionType.QueuedConnection,
        )
        try:
            connecting = {"text": "STOP", "status": "enabled"}
            runner_events.start_button_status.emit(connecting)
            self.app.processEvents()
            self.assertEqual([connecting], received)

            ready = {
                "text": "STOP",
                "status": "enabled",
                "device_ready": True,
            }
            runner_events.start_button_status.emit(ready)
            self.app.processEvents()
            self.assertEqual([connecting, ready], received)
        finally:
            signalBus.start_button_status.disconnect(collect)


class RunnerArchitectureTests(unittest.TestCase):
    def test_runner_does_not_depend_on_ui_signal_buses(self):
        violations: list[str] = []

        for file_path in RUNNER_ROOT.rglob("*.py"):
            source = file_path.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(file_path))
            relative_path = file_path.relative_to(PROJECT_ROOT).as_posix()

            for node in ast.walk(tree):
                if (
                    isinstance(node, ast.ImportFrom)
                    and node.module == "app.common.signal_bus"
                ):
                    violations.append(f"{relative_path}:{node.lineno}: signalBus import")
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name == "app.common.signal_bus":
                            violations.append(
                                f"{relative_path}:{node.lineno}: signalBus import"
                            )
                elif isinstance(node, ast.Name) and node.id in {
                    "FromeServiceCoordinator",
                    "signalBus",
                }:
                    violations.append(f"{relative_path}:{node.lineno}: {node.id}")
                elif isinstance(node, ast.Attribute) and node.attr == "fs_signal_bus":
                    violations.append(
                        f"{relative_path}:{node.lineno}: fs_signal_bus attribute"
                    )

        self.assertEqual(
            [],
            violations,
            msg="Runner 只能通过 RunnerEvents/自身 Signal 上报运行时事件",
        )


if __name__ == "__main__":
    unittest.main()
