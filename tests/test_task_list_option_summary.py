from __future__ import annotations

import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from app.common.constants import POST_ACTION, _CONTROLLER_, _RESOURCE_
from app.core.item import TaskItem
from app.view.task_interface.components.list_item import TaskListItem

_INTERFACE = {
    "controller": [
        {"name": "Android", "type": "Adb", "label": "安卓"},
        {"name": "Win32-Window", "type": "Win32", "label": "窗口"},
    ],
    "resource": [
        {"name": "zh_CN", "label": "简体中文"},
        {"name": "zh_TW", "label": "繁体中文"},
    ],
    "option": {
        "mode": {
            "cases": [
                {"name": "auto", "label": "自动"},
                {"name": "manual", "label": "手动"},
            ]
        }
    },
}


class TestTaskListOptionSummary(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def _item(self, item_id: str, name: str, task_option: dict) -> TaskListItem:
        task = TaskItem(
            name=name,
            item_id=item_id,
            is_checked=True,
            task_option=task_option,
        )
        widget = TaskListItem(task, interface=_INTERFACE)
        self.addCleanup(widget.close)
        return widget

    def test_controller_shows_current_type_label(self):
        widget = self._item(
            _CONTROLLER_,
            "Controller",
            {"controller_type": "Win32-Window"},
        )
        self.assertEqual("窗口", widget.option_label.text())

    def test_resource_shows_active_resource_label(self):
        widget = self._item(
            _RESOURCE_,
            "Resource",
            {"resource": "zh_TW"},
        )
        self.assertEqual("繁体中文", widget.option_label.text())

    def test_other_base_task_stays_blank(self):
        widget = self._item(POST_ACTION, "Post-Action", {"post_action": "none"})
        self.assertEqual("", widget.option_label.text())

    def test_regular_task_still_shows_option_labels(self):
        widget = self._item(
            "t_demo",
            "战斗辅助",
            {"mode": {"value": "auto"}},
        )
        self.assertEqual("自动", widget.option_label.text())


if __name__ == "__main__":
    unittest.main()
