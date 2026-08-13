from __future__ import annotations

import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

from app.core.runner.task_flow import TaskFlowRunner
from app.core.utils.resource_pipeline_check import check_resource_pipeline


class TaskFlowStartupAsyncTest(unittest.IsolatedAsyncioTestCase):
    async def test_embedded_agent_cleanup_runs_in_worker_thread(self) -> None:
        clear_resource_custom = Mock()
        runner = SimpleNamespace(
            maafw=SimpleNamespace(clear_resource_custom=clear_resource_custom)
        )

        with patch(
            "app.core.runner.task_flow.asyncio.to_thread",
            new=AsyncMock(return_value=True),
        ) as to_thread:
            await TaskFlowRunner._clear_embedded_agent_custom(runner)

        to_thread.assert_awaited_once_with(clear_resource_custom)

    async def test_embedded_agent_loading_runs_in_worker_thread(self) -> None:
        loader = Mock()
        runner = SimpleNamespace(
            maafw=SimpleNamespace(load_embedded_agent_custom=loader)
        )
        agent_root = Path("agent")
        agent_entry = agent_root / "main.py"

        with patch(
            "app.core.runner.task_flow.asyncio.to_thread",
            new=AsyncMock(return_value=True),
        ) as to_thread:
            result = await TaskFlowRunner._load_embedded_agent_custom(
                runner,
                agent_root,
                agent_entry,
            )

        self.assertTrue(result)
        to_thread.assert_awaited_once_with(
            loader,
            agent_root=agent_root,
            agent_entry=agent_entry,
        )

    async def test_resource_pipeline_precheck_runs_in_worker_thread(self) -> None:
        runner = SimpleNamespace()
        resource_dir = Path("resource")

        with patch(
            "app.core.runner.task_flow.asyncio.to_thread",
            new=AsyncMock(return_value=[]),
        ) as to_thread:
            result = await TaskFlowRunner._precheck_resource_pipeline(
                runner,
                resource_dir,
            )

        self.assertTrue(result)
        to_thread.assert_awaited_once_with(check_resource_pipeline, resource_dir)


if __name__ == "__main__":
    unittest.main()