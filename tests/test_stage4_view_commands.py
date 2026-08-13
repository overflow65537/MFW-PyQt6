import unittest

from app.core.item import ConfigItem, CoreSignalBus, TaskItem
from app.core.service.config_service import ConfigService
from app.core.service.task_service import TaskService
from app.view.task_interface.components.list_widget import TaskDragListWidget


class _ConfigStore:
    def __init__(self, config: ConfigItem):
        self.current_config_id = config.item_id
        self.config = config
        self.update_calls = 0

    def get_config(self, config_id: str):
        return self.config if config_id == self.config.item_id else None

    def update_config(self, config_id: str, config: ConfigItem) -> bool:
        self.update_calls += 1
        self.config = config
        return True


class Stage4ServiceCommandTests(unittest.TestCase):
    def test_task_checked_persists_and_emits_once(self):
        task = TaskItem("demo", "task-1", False, {})
        config = ConfigItem("config", "config-1", [task], [], "bundle")
        store = _ConfigStore(config)
        service = TaskService.__new__(TaskService)
        service.config_service = store
        service.current_tasks = [task]
        service.signal_bus = CoreSignalBus()
        received: list[TaskItem] = []
        service.signal_bus.task_updated.connect(received.append)

        self.assertTrue(service.update_task_checked("task-1", True))

        self.assertEqual(1, store.update_calls)
        self.assertTrue(store.config.tasks[0].is_checked)
        self.assertEqual(["task-1"], [item.item_id for item in received])

    def test_config_rename_is_owned_by_service(self):
        config = ConfigItem("old", "config-1", [], [], "bundle")

        class _Service:
            def __init__(self):
                self.update_calls = 0

            def get_config(self, config_id: str):
                return config if config_id == config.item_id else None

            def update_config(self, config_id: str, item: ConfigItem) -> bool:
                self.update_calls += 1
                return True

        service = _Service()
        self.assertTrue(ConfigService.rename_config(service, "config-1", " new "))
        self.assertEqual("new", config.name)
        self.assertEqual(1, service.update_calls)


class _Checkbox:
    def __init__(self):
        self.checked = True
        self.block_calls: list[bool] = []

    def blockSignals(self, blocked: bool):
        self.block_calls.append(blocked)

    def setChecked(self, checked: bool):
        self.checked = checked


class _TaskFacade:
    def __init__(self, task: TaskItem):
        self.task = task

    def get_task(self, task_id: str):
        return self.task if task_id == self.task.item_id else None


class _Coordinator:
    def __init__(self, task: TaskItem):
        self.tasks = _TaskFacade(task)
        self.calls: list[tuple[str, bool]] = []

    def update_task_checked(self, task_id: str, checked: bool) -> bool:
        self.calls.append((task_id, checked))
        return False


class Stage4ViewCommandTests(unittest.TestCase):
    def test_checkbox_failure_rolls_back_without_recursive_signal(self):
        task = TaskItem("demo", "task-1", False, {})
        checkbox = _Checkbox()
        coordinator = _Coordinator(task)
        widget = type("_Widget", (), {"checkbox": checkbox})()
        view = type(
            "_View",
            (),
            {
                "service_coordinator": coordinator,
                "_task_widgets": {"task-1": widget},
            },
        )()

        TaskDragListWidget._on_task_checkbox_changed(view, "task-1", True)

        self.assertEqual([("task-1", True)], coordinator.calls)
        self.assertFalse(checkbox.checked)
        self.assertEqual([True, False], checkbox.block_calls)


if __name__ == "__main__":
    unittest.main()
