"""多实例模式运行时管理与配置切换守卫的单元测试。"""

import asyncio
import unittest
from types import SimpleNamespace

from PySide6.QtWidgets import QApplication

from app.common.config import cfg
from app.core.core import ServiceCoordinator
from app.core.runtime_manager import RuntimeInstance, RuntimeInstanceManager


def _ensure_qapp() -> None:
    if QApplication.instance() is None:
        # 提供最简 QApplication，使信号 emit 安全执行
        QApplication([])


class _FakeRunner:
    def __init__(self, is_running: bool = False):
        self.is_running = is_running
        self.run_calls = 0
        self.stop_calls = 0
        self.run_other_config_callback = None

    async def run_tasks_flow(self, task_id=None, *, start_task_id=None):
        self.run_calls += 1
        return "ran"

    async def stop_task(self, *, manual: bool = False):
        self.stop_calls += 1
        return "stopped"


def _make_instance(config_id: str, *, running: bool = False) -> RuntimeInstance:
    runner = _FakeRunner(is_running=running)
    inst = RuntimeInstance(
        config_id=config_id,
        runner=runner,
        runner_events=None,
        fs_signal_bus=None,
        log_processor=None,
        bridge=None,
        config_service=None,
        task_service=None,
    )
    inst.running = running
    return inst


class RuntimeInstanceManagerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        _ensure_qapp()

    def setUp(self) -> None:
        self.coordinator = SimpleNamespace(
            config_service=SimpleNamespace(current_config_id="c_a"),
        )
        self.manager = RuntimeInstanceManager(self.coordinator)

    def test_running_state_aggregation(self) -> None:
        self.manager._instances["c_a"] = _make_instance("c_a", running=True)
        self.manager._instances["c_b"] = _make_instance("c_b", running=False)

        self.assertTrue(self.manager.is_running("c_a"))
        self.assertFalse(self.manager.is_running("c_b"))
        self.assertTrue(self.manager.any_running())
        self.assertEqual(self.manager.running_config_ids(), ["c_a"])

    def test_instance_is_running_follows_runner(self) -> None:
        inst = _make_instance("c_a", running=False)
        self.assertFalse(inst.is_running)
        inst.runner.is_running = True
        self.assertTrue(inst.is_running)

    def test_run_skips_when_already_running(self) -> None:
        inst = _make_instance("c_a", running=True)
        self.manager._instances["c_a"] = inst

        asyncio.run(self.manager.run("c_a"))
        self.assertEqual(inst.runner.run_calls, 0)

    def test_run_invokes_runner_when_idle(self) -> None:
        inst = _make_instance("c_a", running=False)
        self.manager._instances["c_a"] = inst
        # 避免触发协调器的真实刷新逻辑
        self.coordinator._refresh_runtime_instance = lambda _inst: None

        result = asyncio.run(self.manager.run("c_a"))
        self.assertEqual(result, "ran")
        self.assertEqual(inst.runner.run_calls, 1)

    def test_stop_invokes_runner(self) -> None:
        inst = _make_instance("c_a", running=True)
        self.manager._instances["c_a"] = inst

        result = asyncio.run(self.manager.stop("c_a", manual=True))
        self.assertEqual(result, "stopped")
        self.assertEqual(inst.runner.stop_calls, 1)
        self.assertFalse(inst.running)


    def test_button_status_stop_disabled_counts_as_running(self) -> None:
        inst = _make_instance("c_a", running=False)
        self.manager._instances["c_a"] = inst
        self.manager._on_instance_button_status(
            "c_a", {"text": "STOP", "status": "disabled"}
        )
        self.assertTrue(inst.running)

    def test_button_status_start_counts_as_not_running(self) -> None:
        inst = _make_instance("c_a", running=True)
        self.manager._instances["c_a"] = inst
        self.manager._on_instance_button_status(
            "c_a", {"text": "START", "status": "enabled"}
        )
        self.assertFalse(inst.running)


class SwitchConfigGuardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        _ensure_qapp()

    def setUp(self) -> None:
        # 通过 __new__ 跳过重型初始化，仅装配守卫逻辑所需的属性
        self.coord = ServiceCoordinator.__new__(ServiceCoordinator)
        self.coord.task_runner = _FakeRunner(is_running=False)
        self.coord.config_service = SimpleNamespace(current_config_id="c_a")
        self.coord.runtime_manager = RuntimeInstanceManager(self.coord)
        self._original_mode = cfg.get(cfg.multi_instance_mode)

    def tearDown(self) -> None:
        cfg.set(cfg.multi_instance_mode, self._original_mode)

    def test_single_instance_blocks_switch_while_running(self) -> None:
        cfg.set(cfg.multi_instance_mode, False)
        self.assertTrue(self.coord.is_switch_config_allowed())

        self.coord.task_runner.is_running = True
        self.assertFalse(self.coord.is_switch_config_allowed())
        self.assertTrue(self.coord.any_config_running())
        self.assertTrue(self.coord.is_current_config_running())

    def test_multi_instance_allows_switch_while_running(self) -> None:
        cfg.set(cfg.multi_instance_mode, True)
        # 即使某配置在运行，多实例模式也允许切换
        self.coord.runtime_manager._instances["c_b"] = _make_instance(
            "c_b", running=True
        )
        self.assertTrue(self.coord.is_switch_config_allowed())
        self.assertTrue(self.coord.is_config_running("c_b"))
        self.assertFalse(self.coord.is_config_running("c_a"))


if __name__ == "__main__":
    unittest.main()
