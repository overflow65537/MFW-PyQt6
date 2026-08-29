"""首次资源运行确认：身份指纹与确认流程。"""

from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from app.core.utils.resource_run_confirm import (
    acknowledge_resource_run,
    build_resource_run_identity,
    is_resource_run_acknowledged,
    resource_run_fingerprint,
)

try:
    from app.core.item import RunnerEvents
    from app.core.runner.task_flow import TaskFlowRunner
except ImportError:  # pragma: no cover
    RunnerEvents = None
    TaskFlowRunner = None


class ResourceRunIdentityTest(unittest.TestCase):
    def test_prefers_translated_label(self) -> None:
        identity = build_resource_run_identity(
            {
                "name": "raw",
                "label": "展示名",
                "github": "https://github.com/owner/repo",
                "contact": "me@example.com",
            }
        )
        self.assertEqual(identity["name"], "展示名")
        self.assertEqual(identity["github"], "https://github.com/owner/repo")
        self.assertEqual(identity["contact"], "me@example.com")

    def test_github_falls_back_to_url(self) -> None:
        identity = build_resource_run_identity({"name": "Demo", "url": "https://github.com/a/b"})
        self.assertEqual(identity["github"], "https://github.com/a/b")

    def test_fingerprint_changes_with_github(self) -> None:
        left = resource_run_fingerprint({"name": "Demo", "github": "https://a", "contact": ""})
        right = resource_run_fingerprint({"name": "Demo", "github": "https://b", "contact": ""})
        self.assertNotEqual(left, right)


class ResourceRunAcknowledgeTest(unittest.TestCase):
    def test_acknowledge_then_skip(self) -> None:
        identity = {"name": "Demo", "github": "https://github.com/a/b", "contact": "hi"}
        stored: list[str] = []

        def fake_read() -> str:
            import json

            return json.dumps(stored)

        def fake_write(value: str) -> None:
            import json

            stored.clear()
            stored.extend(json.loads(value))

        with patch(
            "app.core.utils.resource_run_confirm._read_config_value",
            side_effect=fake_read,
        ), patch(
            "app.core.utils.resource_run_confirm._write_config_value",
            side_effect=fake_write,
        ):
            self.assertFalse(is_resource_run_acknowledged(identity))
            acknowledge_resource_run(identity)
            self.assertTrue(is_resource_run_acknowledged(identity))
            other = {**identity, "github": "https://github.com/evil/repo"}
            self.assertFalse(is_resource_run_acknowledged(other))


@unittest.skipIf(TaskFlowRunner is None or RunnerEvents is None, "PySide6 is not installed")
class ConfirmResourceRunRunnerTest(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        from PySide6.QtCore import QCoreApplication

        cls.app = QCoreApplication.instance() or QCoreApplication([])
    def _runner(self, *, acknowledged: bool):
        events = RunnerEvents()
        runner = SimpleNamespace(
            _runtime_interface={
                "name": "Demo",
                "github": "https://github.com/owner/repo",
                "contact": "me@example.com",
            },
            need_stop=False,
            _resource_run_confirm_future=None,
            runner_events=events,
        )
        return runner

    async def test_already_acknowledged_skips_prompt(self) -> None:
        runner = self._runner(acknowledged=True)
        handler = Mock()
        runner.runner_events.resource_run_confirmation_requested.connect(handler)
        with patch(
            "app.core.runner.task_flow.is_resource_run_acknowledged",
            return_value=True,
        ):
            ok = await TaskFlowRunner._confirm_resource_run_if_needed(runner)
        self.assertTrue(ok)
        handler.assert_not_called()

    async def test_user_confirm_acknowledges_and_passes(self) -> None:
        runner = self._runner(acknowledged=False)

        def accept(payload: dict) -> None:
            TaskFlowRunner.submit_resource_run_confirmation(runner, True)

        runner.runner_events.resource_run_confirmation_requested.connect(accept)
        with patch(
            "app.core.runner.task_flow.is_resource_run_acknowledged",
            return_value=False,
        ), patch(
            "app.core.runner.task_flow.acknowledge_resource_run"
        ) as ack:
            ok = await TaskFlowRunner._confirm_resource_run_if_needed(runner)
        self.assertTrue(ok)
        ack.assert_called_once()

    async def test_user_cancel_blocks_run(self) -> None:
        runner = self._runner(acknowledged=False)

        def reject(payload: dict) -> None:
            TaskFlowRunner.submit_resource_run_confirmation(runner, False)

        runner.runner_events.resource_run_confirmation_requested.connect(reject)
        with patch(
            "app.core.runner.task_flow.is_resource_run_acknowledged",
            return_value=False,
        ), patch(
            "app.core.runner.task_flow.acknowledge_resource_run"
        ) as ack:
            ok = await TaskFlowRunner._confirm_resource_run_if_needed(runner)
        self.assertFalse(ok)
        ack.assert_not_called()


if __name__ == "__main__":
    unittest.main()
