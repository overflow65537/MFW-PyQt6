from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

from PySide6.QtWidgets import QApplication

from app.common.constants import _CONTROLLER_, _RESOURCE_
from app.core.item import ConfigItem, RunnerEvents, TaskItem
from app.core.runner.task_flow import TaskFlowRunner
from app.core.service.i18n_service import I18nService
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

    def _service(
        self, current_tasks: list[TaskItem], interface: dict | None = None
    ) -> TaskService:
        # 只构造被测逻辑所需的字段，避免依赖 Qt 信号与磁盘配置。
        service = TaskService.__new__(TaskService)
        service.interface = INTERFACE if interface is None else interface
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

    def test_interface_argument_overrides_service_interface(self):
        """runner 必须能用自己 bundle 的 interface 判定，而不是全局 interface。"""
        service = self._service([], interface=INTERFACE)
        controller = _make_task("控制器", _CONTROLLER_, controller_type="MuMuPlayer")
        abyss = _make_task("超弦空间(深渊)")
        bundle_interface = {
            "task": [{"name": "超弦空间(深渊)", "controller": ["MuMuPlayer"]}]
        }

        service.refresh_hidden_flags([controller, abyss], interface=bundle_interface)

        self.assertFalse(abyss.is_hidden)

    def test_interface_argument_can_still_hide_task(self):
        service = self._service(
            [],
            interface={
                "task": [{"name": "超弦空间(深渊)", "controller": ["MuMuPlayer"]}]
            },
        )
        controller = _make_task("控制器", _CONTROLLER_, controller_type="MuMuPlayer")
        abyss = _make_task("超弦空间(深渊)")

        service.refresh_hidden_flags([controller, abyss], interface=INTERFACE)

        self.assertTrue(abyss.is_hidden)

    def test_dict_option_values_are_supported(self):
        """历史配置里 controller_type/resource 可能是 {"value": ...}。"""
        service = self._service([])
        controller = _make_task(
            "控制器", _CONTROLLER_, controller_type={"value": "桌面端"}
        )
        abyss = _make_task("超弦空间(深渊)")

        service.refresh_hidden_flags([controller, abyss])
        self.assertFalse(abyss.is_hidden)

        controller = _make_task(
            "控制器", _CONTROLLER_, controller_type={"value": "MuMuPlayer"}
        )
        service.refresh_hidden_flags([controller, abyss])
        self.assertTrue(abyss.is_hidden)

    def test_dict_resource_value_is_supported(self):
        service = self._service(
            [],
            interface={"task": [{"name": "超弦空间(深渊)", "resource": ["B服"]}]},
        )
        abyss = _make_task("超弦空间(深渊)")

        service.refresh_hidden_flags(
            [_make_task("资源", _RESOURCE_, resource={"value": "B服"}), abyss]
        )
        self.assertFalse(abyss.is_hidden)

        service.refresh_hidden_flags(
            [_make_task("资源", _RESOURCE_, resource={"value": "C服"}), abyss]
        )
        self.assertTrue(abyss.is_hidden)

    def test_explicit_tasks_do_not_fall_back_to_current_tasks(self):
        """显式传入任务列表时，base 任务缺失不能去读 current_tasks。"""
        current = [
            _make_task("控制器", _CONTROLLER_, controller_type="MuMuPlayer"),
            _make_task("资源", _RESOURCE_, resource="B服"),
        ]
        service = self._service(current)
        abyss = _make_task("超弦空间(深渊)")

        # 快照里没有 base 任务：应视为“不过滤”，而不是借用 current_tasks 的控制器
        service.refresh_hidden_flags([abyss])

        self.assertFalse(abyss.is_hidden)


class _Signal:
    def __init__(self):
        self.connect = Mock()


class _ConfigService:
    def __init__(self, config: ConfigItem, bundle_path: Path):
        self.current_config_id = config.item_id
        self._config = config
        self._bundle_path = bundle_path

    def get_config(self, config_id: str):
        return self._config if config_id == self._config.item_id else None

    def get_bundle_path_for_config(self, config: ConfigItem) -> str:
        return str(self._bundle_path)


class RuntimeRefreshCallSiteTests(unittest.TestCase):
    """run_tasks_flow 必须按当前 bundle 的 interface 重算快照隐藏标记。"""

    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.bundle_path = Path(self.temp_dir.name) / "bundle-b"
        self.bundle_path.mkdir()
        (self.bundle_path / "interface.json").write_text(
            json.dumps(
                {
                    "name": "Bundle B",
                    "version": "1.0.0",
                    "controller": [{"name": "MuMuPlayer", "type": "adb"}],
                    "resource": [{"name": "B服"}],
                    # 当前 bundle 允许在 MuMuPlayer 上运行深渊
                    "task": [
                        {
                            "name": "超弦空间(深渊)",
                            "entry": "Abyss",
                            "controller": ["MuMuPlayer"],
                        }
                    ],
                    "option": {},
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        self.config = ConfigItem(
            name="B",
            item_id="config-b",
            bundle="bundle-b",
            know_task=[],
            tasks=[
                TaskItem(
                    name="控制器",
                    item_id=_CONTROLLER_,
                    is_checked=True,
                    task_option={"controller_type": {"value": "MuMuPlayer"}},
                ),
                TaskItem(
                    name="资源",
                    item_id=_RESOURCE_,
                    is_checked=True,
                    task_option={"resource": {"value": "B服"}},
                ),
                TaskItem(
                    name="超弦空间(深渊)",
                    item_id="task-abyss",
                    is_checked=True,
                    task_option={},
                ),
            ],
        )

        self.task_service = SimpleNamespace(
            # 全局（活动配置）的 interface：深渊仅限桌面端，与当前 bundle 相反
            interface={
                "task": [{"name": "超弦空间(深渊)", "controller": ["桌面端"]}]
            },
            builtin_task_loader=SimpleNamespace(
                i18n_service=I18nService(language="zh_cn")
            ),
            refresh_hidden_flags=Mock(),
            get_task=Mock(return_value=None),
            get_tasks=Mock(return_value=[]),
            update_task=Mock(return_value=True),
        )
        self.runner = TaskFlowRunner(
            task_service=self.task_service,
            config_service=_ConfigService(self.config, self.bundle_path),
            runner_events=RunnerEvents(),
            config_id="config-b",
            maafw=SimpleNamespace(
                callback=_Signal(),
                custom_info=_Signal(),
                agent_info=_Signal(),
            ),
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_refresh_uses_runtime_bundle_interface(self):
        self.assertTrue(self.runner._prepare_runtime_snapshot())
        self.runner._reload_interface_for_current_bundle()
        self.assertEqual("Bundle B", self.runner._runtime_interface["name"])

        self.runner._refresh_runtime_hidden_flags()

        self.task_service.refresh_hidden_flags.assert_called_once_with(
            self.runner._runtime_tasks,
            interface=self.runner._runtime_interface,
        )


if __name__ == "__main__":
    unittest.main()
