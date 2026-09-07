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


def _enabled_interface(**sentry_extra) -> dict:
    sentry = {"dsn": "https://example.invalid/1"}
    sentry.update(sentry_extra)
    return {
        "name": "demo",
        "version": "1.0.0",
        "telemetry": {"sentry": sentry},
        "option": {},
    }


def _cfg_get(item):
    return True if item is cfg.telemetry_enabled else 2


def _make_service(fake_sentry, **sentry_extra) -> TelemetryService:
    with (
        patch.object(cfg, "get", side_effect=_cfg_get),
        patch(
            "app.core.service.telemetry_service.importlib.import_module",
            return_value=fake_sentry,
        ),
    ):
        return TelemetryService(
            RunnerEvents(), _enabled_interface(**sentry_extra), debug_override=False
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


class FakeScope:
    def __init__(self):
        self.attachments: list[dict[str, object]] = []

    def add_attachment(self, **kwargs):
        self.attachments.append(kwargs)

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


class FakeSentry:
    def __init__(self):
        self.guard = FakeGuard()
        self.transaction: FakeSpan | None = None
        self.transactions: list[FakeSpan] = []
        self.init_kwargs: dict[str, object] = {}
        self.messages: list[dict[str, object]] = []
        self.scopes: list[FakeScope] = []

    def init(self, **kwargs):
        self.init_kwargs = kwargs
        return self.guard

    def set_user(self, _user):
        pass

    def set_tag(self, _key, _value):
        pass

    def start_transaction(self, name: str, op: str):
        self.transaction = FakeSpan(op, name)
        self.transactions.append(self.transaction)
        return self.transaction

    def new_scope(self):
        scope = FakeScope()
        self.scopes.append(scope)
        return scope

    def capture_message(self, message, level="info"):
        self.messages.append({"message": message, "level": level})

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

    def test_password_input_is_omitted_from_summary(self):
        definitions = {
            "账号登录": {
                "type": "input",
                "inputs": [
                    {"name": "username", "pipeline_type": "string"},
                    {"name": "password", "pipeline_type": "string", "password": True},
                ],
            }
        }
        values = {
            "账号登录": {"value": {"username": "alice", "password": "s3cret"}},
        }
        summary = build_task_option_summary(values, definitions)
        self.assertEqual("filled", summary["账号登录.username"])
        self.assertNotIn("账号登录.password", summary)
        self.assertNotIn("s3cret", summary.values())


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

    def test_concurrent_runner_sources_keep_independent_transactions(self):
        fake_sentry = FakeSentry()
        interface = {
            "name": "demo",
            "version": "1.0.0",
            "telemetry": {"sentry": {"dsn": "https://example.invalid/1"}},
            "option": {},
        }
        events_a = RunnerEvents()
        events_b = RunnerEvents()

        def get_config(item):
            return True if item is cfg.telemetry_enabled else 2

        with (
            patch.object(cfg, "get", side_effect=get_config),
            patch(
                "app.core.service.telemetry_service.importlib.import_module",
                return_value=fake_sentry,
            ),
        ):
            service = TelemetryService(events_a, interface, debug_override=False)
            service.add_runner_events(events_b)

            events_a.telemetry.emit(
                {"event": "run_start", "tasks": ["A"], "controller": None}
            )
            events_b.telemetry.emit(
                {"event": "run_start", "tasks": ["B"], "controller": None}
            )
            transaction_a, transaction_b = fake_sentry.transactions

            events_b.telemetry.emit({"event": "run_finished"})
            self.assertTrue(transaction_b.finished)
            self.assertFalse(transaction_a.finished)

            events_a.telemetry.emit(
                {"event": "prepare_task", "name": "EntryA", "options": {}}
            )
            events_a.callback.emit(
                {"name": "task", "task_id": 101, "status": 1, "task": "EntryA"}
            )
            events_a.callback.emit(
                {
                    "name": "node",
                    "message": "Node.PipelineNode.Failed",
                    "details": {
                        "task_id": 101,
                        "node_id": 7,
                        "name": "NodeA",
                    },
                }
            )

            self.assertEqual("mfw.task", transaction_a.children[0].op)
            self.assertEqual("mfw.node", transaction_a.children[0].children[0].op)
            self.assertEqual([], transaction_b.children)

            events_a.telemetry.emit({"event": "run_finished"})
            self.assertTrue(transaction_a.finished)


class TestFailureAttachmentsAndRunFailed(unittest.TestCase):
    def test_sample_rate_is_parsed_from_interface(self):
        service = _make_service(FakeSentry(), failure_attachments_sample_rate=0)
        self.assertEqual(0.0, service._failure_attachments_sample_rate)

        service = _make_service(FakeSentry(), failure_attachments_sample_rate=2)
        self.assertEqual(1.0, service._failure_attachments_sample_rate)

    def test_attachment_rate_does_not_change_trace_sampling(self):
        fake_sentry = FakeSentry()
        service = _make_service(
            fake_sentry,
            failure_attachments_sample_rate=0,
            traces_sample_rate=0.8,
        )
        self.assertEqual(0.8, fake_sentry.init_kwargs["traces_sample_rate"])
        self.assertEqual(0.0, service._failure_attachments_sample_rate)

    def test_run_failed_captures_error_when_tracing_disabled(self):
        fake_sentry = FakeSentry()
        service = _make_service(fake_sentry, tracing=False)
        self.assertTrue(service.is_active)
        self.assertFalse(service._tracing)
        self.assertEqual(0.0, fake_sentry.init_kwargs["traces_sample_rate"])

        with patch(
            "app.core.service.telemetry_service.collect_failure_diagnostic_files",
            return_value=[
                {
                    "filename": "maafw.log.tail.txt",
                    "content_type": "text/plain",
                    "bytes": b"log",
                }
            ],
        ):
            service.on_run_failed(error="boom")

        self.assertEqual(
            [{"message": "boom", "level": "error"}], fake_sentry.messages
        )
        self.assertEqual(1, len(fake_sentry.scopes))
        self.assertEqual("maafw.log.tail.txt", fake_sentry.scopes[0].attachments[0]["filename"])
        self.assertIsNone(fake_sentry.transaction)

    def test_rate_zero_omits_attachments_but_still_reports_error(self):
        fake_sentry = FakeSentry()
        service = _make_service(fake_sentry, failure_attachments_sample_rate=0)
        with patch(
            "app.core.service.telemetry_service.collect_failure_diagnostic_files",
            return_value=[
                {
                    "filename": "maafw.log.tail.txt",
                    "content_type": "text/plain",
                    "bytes": b"log",
                }
            ],
        ) as collect:
            service.on_run_failed(
                attachments=[
                    {
                        "filename": "screenshot.png",
                        "content_type": "image/png",
                        "bytes": b"png",
                    }
                ],
                error="failed",
            )
        collect.assert_not_called()
        self.assertEqual(
            [{"message": "failed", "level": "error"}], fake_sentry.messages
        )
        self.assertEqual([], fake_sentry.scopes[0].attachments)

    def test_run_failed_finishes_transaction_as_failed(self):
        fake_sentry = FakeSentry()
        service = _make_service(fake_sentry)
        service.on_run_start(["Task"], {"name": "Win32", "type": "Win32"})
        transaction = fake_sentry.transaction
        self.assertIsNotNone(transaction)

        with patch(
            "app.core.service.telemetry_service.collect_failure_diagnostic_files",
            return_value=[],
        ):
            service.on_run_failed(
                attachments=[
                    {
                        "filename": "screenshot.png",
                        "content_type": "image/png",
                        "bytes": b"png",
                    }
                ],
                error="task failed",
            )

        self.assertTrue(transaction.finished)
        self.assertEqual("internal_error", transaction.status)
        self.assertEqual("failed", transaction.data["result"])
        self.assertEqual("screenshot.png", fake_sentry.scopes[0].attachments[0]["filename"])
        self.assertEqual(b"png", fake_sentry.scopes[0].attachments[0]["bytes"])

    def test_run_failed_event_payload_is_routed(self):
        fake_sentry = FakeSentry()
        service = _make_service(fake_sentry)
        service.on_run_start(["Task"])
        with patch(
            "app.core.service.telemetry_service.collect_failure_diagnostic_files",
            return_value=[],
        ):
            service.runner_events.telemetry.emit(
                {
                    "event": "run_failed",
                    "error": "pipeline failed",
                    "attachments": [
                        {
                            "filename": "screenshot.png",
                            "content_type": "image/png",
                            "bytes": b"png",
                        }
                    ],
                }
            )

        self.assertEqual("pipeline failed", fake_sentry.messages[0]["message"])
        self.assertEqual("failed", fake_sentry.transaction.data["result"])
        self.assertTrue(fake_sentry.transaction.finished)


if __name__ == "__main__":
    unittest.main()
