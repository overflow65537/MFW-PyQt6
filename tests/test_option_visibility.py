"""option.resource / option.controller 对 Setting 表单的可见性过滤。"""

from __future__ import annotations

import unittest

from app.common.constants import _CONTROLLER_, _RESOURCE_
from app.core.item import CoreSignalBus, TaskItem
from app.core.service.option_service import OptionService


class _SettingTaskService:
    def __init__(self, resource_task: TaskItem, controller_task: TaskItem):
        self.resource_task = resource_task
        self.controller_task = controller_task
        self.interface = {
            "controller": [{"name": "Android"}],
            "resource": [{"name": "zh_CN"}, {"name": "zh_TW"}],
            "setting": [{"name": "global", "option": ["切换服务器"]}],
            "option": {
                "切换服务器": {
                    "type": "select",
                    "resource": ["zh_CN"],
                    "controller": ["Android"],
                    "cases": [{"name": "官服"}],
                }
            },
        }

    def get_task(self, task_id: str):
        if task_id == _RESOURCE_:
            return self.resource_task
        if task_id == _CONTROLLER_:
            return self.controller_task
        return None


class TestSettingOptionVisibility(unittest.TestCase):
    def test_setting_form_filters_option_by_current_resource(self):
        resource_task = TaskItem(
            name="Resource",
            item_id=_RESOURCE_,
            is_checked=True,
            task_option={"resource": "zh_TW"},
        )
        controller_task = TaskItem(
            name="Controller",
            item_id=_CONTROLLER_,
            is_checked=True,
            task_option={"controller_type": "Android"},
        )
        service = OptionService(
            _SettingTaskService(resource_task, controller_task),  # type: ignore[arg-type]
            CoreSignalBus(),
        )

        form = service.get_setting_form_structure()
        self.assertNotIn("切换服务器", form)

        resource_task.task_option["resource"] = "zh_CN"
        form = service.get_setting_form_structure()
        self.assertIn("切换服务器", form)


if __name__ == "__main__":
    unittest.main()
