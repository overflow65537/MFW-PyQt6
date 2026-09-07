import unittest

from app.common.constants import _CONTROLLER_, _PRETASK_, _RESOURCE_, POST_ACTION
from app.core.item import TaskItem
from app.view.task_interface.components.list_widget import TaskDragListWidget


def _task(item_id: str, name: str | None = None) -> TaskItem:
    return TaskItem(name or item_id, item_id, True, {})


class TaskDragProtectedPositionTests(unittest.TestCase):
    def setUp(self):
        self.widget = TaskDragListWidget.__new__(TaskDragListWidget)

    def test_protected_positions_follow_visible_base_tasks(self):
        tasks = [
            _task(_PRETASK_),
            _task(_CONTROLLER_),
            _task(_RESOURCE_),
            _task("t-1", "User Task"),
            _task(POST_ACTION),
        ]

        protected = self.widget._protected_positions(tasks)

        self.assertEqual(
            protected,
            {
                0: _PRETASK_,
                1: _CONTROLLER_,
                2: _RESOURCE_,
                4: POST_ACTION,
            },
        )

    def test_protected_positions_without_pretask_row(self):
        tasks = [
            _task(_CONTROLLER_),
            _task(_RESOURCE_),
            _task("t-1", "User Task"),
            _task("t-2", "User Task 2"),
            _task(POST_ACTION),
        ]

        protected = self.widget._protected_positions(tasks)

        self.assertEqual(
            protected,
            {
                0: _CONTROLLER_,
                1: _RESOURCE_,
                4: POST_ACTION,
            },
        )

    def test_reorder_non_base_tasks_when_pretask_row_is_hidden(self):
        before = [
            _task(_CONTROLLER_),
            _task(_RESOURCE_),
            _task("t-1", "User Task 1"),
            _task("t-2", "User Task 2"),
            _task(POST_ACTION),
        ]
        after = [
            _task(_CONTROLLER_),
            _task(_RESOURCE_),
            _task("t-2", "User Task 2"),
            _task("t-1", "User Task 1"),
            _task(POST_ACTION),
        ]
        protected = self.widget._protected_positions(before)

        self.assertTrue(self.widget._base_positions_intact(after, protected))

    def test_reorder_rejected_when_base_task_row_moves(self):
        before = [
            _task(_PRETASK_),
            _task(_CONTROLLER_),
            _task(_RESOURCE_),
            _task("t-1", "User Task"),
            _task(POST_ACTION),
        ]
        after = [
            _task(_CONTROLLER_),
            _task(_PRETASK_),
            _task(_RESOURCE_),
            _task("t-1", "User Task"),
            _task(POST_ACTION),
        ]
        protected = self.widget._protected_positions(before)

        self.assertFalse(self.widget._base_positions_intact(after, protected))


if __name__ == "__main__":
    unittest.main()
