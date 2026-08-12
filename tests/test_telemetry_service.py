"""PI telemetry 与 focus.trace 单元测试。"""

from __future__ import annotations

import unittest
from unittest.mock import patch

from app.common.config import cfg
from app.core.item import RunnerEvents
from app.core.service.telemetry_service import (
    TelemetryService,
    build_task_option_summary,
    resolve_trace,
    should_process_node,
)


class FakeSpan:
    def __init__(self, op: str = "", description: str = ""):
        self.op = op
        self.description = description
        self.data: dict[str, object] = {}
        self.children: list[FakeSpan] = []
        self.status = ""
        self.finished = False

    def start_child(self, op: str, description: str):
        child = FakeSpan(op, description)
        self.children.append(child)
        return child

    def set_data(self, key: str, value: object):
        self.data[key] = value

    def set_status(self, status: str):
        self.status = status

    def finish(self):
        self.finished = True


class FakeGuard:
    def __init__(self):
        self.closed = False

    def __exit__(self, *_args):
        self.closed = True


class FakeSentry:
    def __init__(self):
        self.guard = FakeGuard()
        self.transaction: FakeSpan | None = None
        self.init_kwargs: dict[str, object] = {}

    def init(self, **kwargs):
        self.init_kwargs = kwargs
        return self.guard

    def set_user(self, _user):
        pass

    def set_tag(self, _key, _value):
        pass

    def start_transaction(self, name: str, op: str):
        self.transaction = FakeSpan(op, name)
        return self.transaction

    def flush(self, timeout: int):
        pass


class TestResolveTrace(unittest.TestCase):
    def test_failed_pipeline_node_defaults_true(self):
        self.assertTrue(resolve_trace({}, "Node.PipelineNode.Failed"))

    def test_other_node_defaults_false(self):
        self.assertFalse(resolve_trace({}, "Node.Action.Succeeded"))

    def test_explicit_trace_overrides_default(self):
        details = {
            "focus": {
                "Node.PipelineNode.Failed": {"trace": False},
                "Node.Action.Succeeded": {"trace": True},
            }
        }
        self.assertFalse(resolve_trace(details, "Node.PipelineNode.Failed"))
        self.assertTrue(resolve_trace(details, "Node.Action.Succeeded"))

    def test_string_focus_uses_default(self):
        details = {"focus": {"Node.Action.Succeeded": "done"}}
        self.assertFalse(resolve_trace(details, "Node.Action.Succeeded"))

    def test_node_processing_gate(self):
        self.assertTrue(
            should_process_node("Node.PipelineNode.Starting", {"large": "payload"})
        )
        self.assertFalse(
            should_process_node("Node.PipelineNode.Succeeded", {"large": "payload"})
        )
        self.assertTrue(
            should_process_node(
                "Node.PipelineNode.Succeeded",
                {
                    "focus": {
                        "Node.PipelineNode.Succeeded": {"trace": True}
                    }
                },
            )
        )


class TestOptionSummary(unittest.TestCase):
    def test_sensitive_input_is_redacted_but_safe_types_are_kept(self):
        definitions = {
            "账号": {
                "type": "input",
                "inputs": [
                    {"name": "路径", "pipeline_type": "string"},
                    {"name": "次数", "pipeline_type": "int"},
                ],
            },
            "模式": {"type": "select"},
            "键位": {"type": "hotkey"},
        }
        values = {
            "账号": {"value": {"路径": "C:/private/file", "次数": "3"}},
            "模式": {"value": "快速"},
            "键位": {"value": {"攻击": "Ctrl+A"}},
        }
        summary = build_task_option_summary(values, definitions)
        self.assertEqual("filled", summary["账号.路径"])
        self.assertEqual("3", summary["账号.次数"])
        self.assertEqual("快速", summary["模式"])
        self.assertEqual("Ctrl+A", summary["键位.攻击"])
        self.assertNotIn("C:/private/file", summary.values())


class TestTelemetryConfiguration(unittest.TestCase):
    def test_no_dsn_does_not_import_sdk(self):
        with patch(
            "app.core.service.telemetry_service.importlib.import_module"
        ) as import_module:
            service = TelemetryService(
                RunnerEvents(), {"name": "demo"}, debug_override=False
            )
        self.assertFalse(service.is_active)
        import_module.assert_not_called()

    def test_user_disabled_does_not_initialize(self):
        interface = {"telemetry": {"sentry": {"dsn": "https://example.invalid/1"}}}
        with (
            patch.object(cfg, "get", return_value=False),
            patch(
                "app.core.service.telemetry_service.importlib.import_module"
            ) as import_module,
        ):
            service = TelemetryService(
                RunnerEvents(), interface, debug_override=False
            )
        self.assertFalse(service.is_active)
        import_module.assert_not_called()

    def test_debug_build_does_not_initialize(self):
        interface = {"telemetry": {"sentry": {"dsn": "https://example.invalid/1"}}}
        with (
            patch.object(cfg, "get", return_value=True),
            patch(
                "app.core.service.telemetry_service.importlib.import_module"
            ) as import_module,
        ):
            service = TelemetryService(
                RunnerEvents(), interface, debug_override=True
            )
        self.assertFalse(service.is_active)
        import_module.assert_not_called()

    def test_traced_node_creates_child_span(self):
        fake_sentry = FakeSentry()
        interface = {
            "name": "demo",
            "version": "1.0.0",
            "telemetry": {"sentry": {"dsn": "https://example.invalid/1"}},
            "option": {},
        }

        def get_config(item):
            return True if item is cfg.telemetry_enabled else 2

        with (
            patch.object(cfg, "get", side_effect=get_config),
            patch(
                "app.core.service.telemetry_service.importlib.import_module",
                return_value=fake_sentry,
            ),
        ):
            service = TelemetryService(
                RunnerEvents(), interface, debug_override=False
            )
            service.on_run_start(["Task"], {"name": "Win32", "type": "Win32"})
            service.prepare_task("Entry", {})
            service.on_task_start(42, "Entry")
            service.on_node_event(
                "Node.PipelineNode.Failed",
                {"task_id": 42, "node_id": 7, "name": "NodeA"},
            )

        self.assertTrue(service.is_active)
        task_span = fake_sentry.transaction.children[0]  # type: ignore[union-attr]
        self.assertEqual("mfw.task", task_span.op)
        self.assertEqual("mfw.node", task_span.children[0].op)
        self.assertEqual("internal_error", task_span.children[0].status)
        with (
            patch.object(cfg, "set"),
            patch.object(cfg, "get", return_value=False),
        ):
            service.set_user_enabled(False)
        self.assertFalse(service.is_active)
        self.assertTrue(fake_sentry.guard.closed)


if __name__ == "__main__":
    unittest.main()
