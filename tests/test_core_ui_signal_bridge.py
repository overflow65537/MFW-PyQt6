import inspect
import re
import unittest

from PySide6.QtCore import QCoreApplication, Qt

from app.common.constants import _CONTROLLER_, _RESOURCE_, POST_ACTION
from app.core.core import _CoreUiSignalBridge, ServiceCoordinator
from app.core.item import (
    CoreSignalBus,
    TaskItem,
    ViewSignalBus,
)
from app.core.service.option_service import OptionService


class CoreUiSignalBridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QCoreApplication.instance() or QCoreApplication([])

    def setUp(self):
        self.core_signals = CoreSignalBus()
        self.view_signals = ViewSignalBus()
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
        self.core_signals.task_updated.connect(
            self.bridge.forward_task_updated,
            Qt.ConnectionType.QueuedConnection,
        )

    def test_domain_events_are_forwarded_once_with_payload_unchanged(self):
        config_ids: list[str] = []
        options_loaded: list[bool] = []
        option_payloads: list[object] = []
        modified_tasks: list[object] = []
        self.view_signals.config_changed.connect(config_ids.append)
        self.view_signals.options_loaded.connect(lambda: options_loaded.append(True))
        self.view_signals.option_updated.connect(option_payloads.append)
        self.view_signals.task_modified.connect(modified_tasks.append)

        payload = {"resource": "demo"}
        task = TaskItem("demo", "task-1", True, {})
        self.core_signals.config_changed.emit("config-1")
        self.core_signals.options_loaded.emit()
        self.core_signals.option_updated.emit(payload)
        self.core_signals.task_updated.emit(task)
        self.app.processEvents()

        self.assertEqual(["config-1"], config_ids)
        self.assertEqual([True], options_loaded)
        self.assertEqual([payload], option_payloads)
        self.assertEqual([task], modified_tasks)

    def test_coordinator_wires_each_core_event_with_queued_connection(self):
        source = inspect.getsource(ServiceCoordinator._connect_signals)
        forwarders = {
            "config_changed": "forward_config_changed",
            "options_loaded": "forward_options_loaded",
            "option_updated": "forward_option_updated",
            "task_updated": "forward_task_updated",
        }
        for signal_name, forwarder_name in forwarders.items():
            pattern = (
                rf"_core_signals\.{signal_name}\.connect\("
                rf".*?{forwarder_name}.*?Qt\.ConnectionType\.QueuedConnection"
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

    def test_controller_options_filter_and_persist_once(self):
        controller_task = TaskItem(
            name="Controller",
            item_id=_CONTROLLER_,
            is_checked=True,
            task_option={
                "controller_type": "demo",
                "resource": "invalid",
                "_speedrun_config": {"enabled": True},
            },
        )

        class _ControllerTaskService:
            def __init__(self):
                self.interface = {"controller": [{"name": "demo"}]}
                self.update_calls = 0

            def get_task(self, task_id: str):
                return controller_task if task_id == _CONTROLLER_ else None

            def update_task(self, task: TaskItem) -> bool:
                self.update_calls += 1
                return True

            def refresh_hidden_flags(self):
                raise AssertionError("controller_type did not change")

        task_service = _ControllerTaskService()
        core_signals = CoreSignalBus()
        service = OptionService(task_service, core_signals)  # type: ignore[arg-type]
        received: list[object] = []
        core_signals.option_updated.connect(received.append)

        self.assertTrue(
            service.update_controller_options(
                {"gpu": 2, "demo": {"address": "127.0.0.1"}, "junk": True}
            )
        )

        self.assertEqual(1, task_service.update_calls)
        self.assertEqual(
            {
                "controller_type": "demo",
                "gpu": 2,
                "demo": {"address": "127.0.0.1"},
            },
            controller_task.task_option,
        )
        self.assertEqual(
            [{"gpu": 2, "demo": {"address": "127.0.0.1"}}],
            received,
        )

    def test_post_action_is_normalized_and_persisted_once(self):
        post_task = TaskItem(
            name="Post-Action",
            item_id=POST_ACTION,
            is_checked=True,
            task_option={},
        )

        class _PostTaskService:
            interface = {}

            def __init__(self):
                self.update_calls = 0

            def get_task(self, task_id: str):
                return post_task if task_id == POST_ACTION else None

            def update_task(self, task: TaskItem) -> bool:
                self.update_calls += 1
                return True

        task_service = _PostTaskService()
        core_signals = CoreSignalBus()
        service = OptionService(task_service, core_signals)  # type: ignore[arg-type]
        received: list[object] = []
        core_signals.option_updated.connect(received.append)

        self.assertTrue(
            service.update_post_action(
                {
                    "none": False,
                    "shutdown": True,
                    "run_other": True,
                    "target_config": "config-2",
                    "unknown": "discarded",
                }
            )
        )

        self.assertEqual(1, task_service.update_calls)
        state = post_task.task_option["post_action"]
        self.assertTrue(state["shutdown"])
        self.assertFalse(state["run_other"])
        self.assertEqual("", state["target_config"])
        self.assertNotIn("unknown", state)
        self.assertEqual([{"post_action": state}], received)


if __name__ == "__main__":
    unittest.main()
