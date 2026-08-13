import inspect
import re
import unittest

from PySide6.QtCore import QCoreApplication, Qt

from app.common.constants import _RESOURCE_
from app.core.core import _CoreUiSignalBridge, ServiceCoordinator
from app.core.item import (
    CoreSignalBus,
    FromeServiceCoordinator,
    TaskItem,
)
from app.core.service.option_service import OptionService


class CoreUiSignalBridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QCoreApplication.instance() or QCoreApplication([])

    def setUp(self):
        self.core_signals = CoreSignalBus()
        self.view_signals = FromeServiceCoordinator()
        self.bridge = _CoreUiSignalBridge(self.view_signals)

        self.core_signals.config_changed.connect(
            self.bridge.forward_config_changed,
            Qt.ConnectionType.QueuedConnection,
        )
        self.core_signals.options_loaded.connect(
            self.bridge.forward_options_loaded,
            Qt.ConnectionType.QueuedConnection,
        )
        self.core_signals.option_updated.connect(
            self.bridge.forward_option_updated,
            Qt.ConnectionType.QueuedConnection,
        )

    def test_domain_events_are_forwarded_once_with_payload_unchanged(self):
        config_ids: list[str] = []
        options_loaded: list[bool] = []
        option_payloads: list[object] = []
        self.view_signals.config_changed.connect(config_ids.append)
        self.view_signals.options_loaded.connect(lambda: options_loaded.append(True))
        self.view_signals.option_updated.connect(option_payloads.append)

        payload = {"resource": "demo"}
        self.core_signals.config_changed.emit("config-1")
        self.core_signals.options_loaded.emit()
        self.core_signals.option_updated.emit(payload)
        self.app.processEvents()

        self.assertEqual(["config-1"], config_ids)
        self.assertEqual([True], options_loaded)
        self.assertEqual([payload], option_payloads)

    def test_coordinator_wires_each_core_event_with_queued_connection(self):
        source = inspect.getsource(ServiceCoordinator._connect_signals)
        for signal_name in ("config_changed", "options_loaded", "option_updated"):
            pattern = (
                rf"_core_signals\.{signal_name}\.connect\("
                rf".*?Qt\.ConnectionType\.QueuedConnection"
            )
            self.assertRegex(source, re.compile(pattern, re.DOTALL))


class _FakeTaskService:
    def __init__(self, resource_task: TaskItem):
        self.resource_task = resource_task
        self.interface = {
            "resource": [
                {"name": "demo", "option": ["mode"]},
                {"name": "other", "option": ["legacy"]},
            ]
        }
        self.update_calls = 0
        self.refresh_calls = 0

    def get_task(self, task_id: str):
        return self.resource_task if task_id == _RESOURCE_ else None

    def update_task(self, task: TaskItem) -> bool:
        self.resource_task = task
        self.update_calls += 1
        return True

    def refresh_hidden_flags(self) -> None:
        self.refresh_calls += 1


class OptionServiceDomainEventTests(unittest.TestCase):
    def test_resource_selection_persists_then_emits_once(self):
        resource_task = TaskItem(
            name="Resource",
            item_id=_RESOURCE_,
            is_checked=True,
            task_option={"gpu": 1},
        )
        task_service = _FakeTaskService(resource_task)
        core_signals = CoreSignalBus()
        service = OptionService(task_service, core_signals)  # type: ignore[arg-type]
        received: list[object] = []
        core_signals.option_updated.connect(received.append)

        self.assertTrue(service.update_resource_selection("demo"))

        self.assertEqual(1, task_service.update_calls)
        self.assertEqual(1, task_service.refresh_calls)
        self.assertEqual("demo", resource_task.task_option["resource"])
        self.assertNotIn("gpu", resource_task.task_option)
        self.assertEqual([{"resource": "demo"}], received)

    def test_resource_options_preserve_inactive_values_as_hidden(self):
        resource_task = TaskItem(
            name="Resource",
            item_id=_RESOURCE_,
            is_checked=True,
            task_option={
                "resource": "demo",
                "resource_options": {
                    "mode": {"value": "old", "hidden": True},
                    "legacy": "kept",
                },
            },
        )
        task_service = _FakeTaskService(resource_task)
        core_signals = CoreSignalBus()
        service = OptionService(task_service, core_signals)  # type: ignore[arg-type]
        received: list[object] = []
        core_signals.option_updated.connect(received.append)

        self.assertTrue(service.update_resource_options({"mode": "new"}, ["mode"]))

        stored = resource_task.task_option["resource_options"]
        self.assertEqual("new", stored["mode"])
        self.assertEqual({"value": "kept", "hidden": True}, stored["legacy"])
        self.assertEqual([{"mode": "new"}], received)


if __name__ == "__main__":
    unittest.main()
