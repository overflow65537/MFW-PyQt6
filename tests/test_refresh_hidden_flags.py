from __future__ import annotations

import unittest

from app.common.constants import _CONTROLLER_, _RESOURCE_
from app.core.item import TaskItem
from app.core.service.task_service import TaskService


def _make_task(name: str, item_id: str = "", **options) -> TaskItem:
    return TaskItem(
        name=name,
        item_id=item_id or TaskItem.generate_id(),
        is_checked=True,
        task_option=dict(options),
    )


INTERFACE = {
    "task": [
        {"name": "超弦空间(深渊)", "controller": ["桌面端"]},
        {"name": "家园打工"},
    ]
}


class RefreshHiddenFlagsTests(unittest.TestCase):
    """回归测试：运行时快照必须重算 is_hidden，否则“界面隐藏的任务仍被执行”。"""

    def _service(self, current_tasks: list[TaskItem]) -> TaskService:
        # 只构造被测逻辑所需的字段，避免依赖 Qt 信号与磁盘配置。
        service = TaskService.__new__(TaskService)
        service.interface = INTERFACE
        service.current_tasks = current_tasks
        return service

    def _snapshot(self) -> tuple[TaskService, list[TaskItem]]:
        controller = _make_task("控制器", _CONTROLLER_, controller_type="MuMuPlayer")
        resource = _make_task("资源", _RESOURCE_, resource="B服")
        abyss = _make_task("超弦空间(深渊)")
        home = _make_task("家园打工")
        tasks = [controller, resource, abyss, home]
        return self._service(tasks), tasks

    def test_snapshot_tasks_get_hidden_flag_recomputed(self):
        service, tasks = self._snapshot()
        # 快照由配置反序列化而来，is_hidden 一律是默认 False
        self.assertFalse(any(t.is_hidden for t in tasks))

        service.refresh_hidden_flags(tasks)

        abyss = next(t for t in tasks if t.name == "超弦空间(深渊)")
        home = next(t for t in tasks if t.name == "家园打工")
        self.assertTrue(abyss.is_hidden)
        self.assertFalse(home.is_hidden)
        self.assertFalse(any(t.is_hidden for t in tasks if t.is_base_task()))

    def test_passed_tasks_are_refreshed_not_current_tasks(self):
        service, current = self._snapshot()
        snapshot = [
            _make_task("控制器", _CONTROLLER_, controller_type="MuMuPlayer"),
            _make_task("资源", _RESOURCE_, resource="B服"),
            _make_task("超弦空间(深渊)"),
        ]

        service.refresh_hidden_flags(snapshot)

        self.assertTrue(snapshot[2].is_hidden)
        self.assertFalse(any(t.is_hidden for t in current))

    def test_default_call_still_refreshes_current_tasks(self):
        service, current = self._snapshot()

        service.refresh_hidden_flags()

        abyss = next(t for t in current if t.name == "超弦空间(深渊)")
        self.assertTrue(abyss.is_hidden)

    def test_matching_controller_keeps_task_visible(self):
        service = self._service([])
        controller = _make_task("控制器", _CONTROLLER_, controller_type="桌面端")
        abyss = _make_task("超弦空间(深渊)")

        service.refresh_hidden_flags([controller, abyss])

        self.assertFalse(abyss.is_hidden)


if __name__ == "__main__":
    unittest.main()
