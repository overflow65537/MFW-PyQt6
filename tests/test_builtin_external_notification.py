from __future__ import annotations

import unittest

from app.builtin_tasks.basic_tasks import (
    execute_external_notification,
    get_builtin_tasks,
)


class _Context:
    def __init__(self):
        self.capture_count = 0
        self.screenshot: bytes | None = b"image"
        self.sent: list[tuple[str, str, bytes | None]] = []
        self.logs: list[tuple[str, str]] = []

    @staticmethod
    def tr(text: str) -> str:
        return text

    async def capture_screenshot(self) -> bytes | None:
        self.capture_count += 1
        return self.screenshot

    def log(self, level: str, text: str) -> None:
        self.logs.append((level, text))

    def notify_external(
        self,
        title: str,
        text: str,
        image_bytes: bytes | None = None,
    ) -> None:
        self.sent.append((title, text, image_bytes))


class TestBuiltinExternalNotification(unittest.IsolatedAsyncioTestCase):
    async def test_sends_fixed_title_body_and_optional_screenshot(self):
        context = _Context()
        option = {
            "external_notice": {
                "value": {
                    "title": "legacy title",
                    "text": "custom body",
                }
            },
            "include_screenshot": {"value": "Yes"},
        }

        result = await execute_external_notification(context, option)

        self.assertTrue(result)
        self.assertEqual(1, context.capture_count)
        self.assertEqual([("MFW", "custom body", b"image")], context.sent)

    async def test_does_not_capture_when_task_switch_is_off(self):
        context = _Context()
        option = {
            "external_notice": {"value": {"text": "body"}},
            "include_screenshot": {"value": "No"},
        }

        await execute_external_notification(context, option)

        self.assertEqual(0, context.capture_count)
        self.assertEqual([("MFW", "body", None)], context.sent)

    async def test_uses_custom_legacy_title_as_body_when_text_is_default(self):
        context = _Context()
        option = {
            "external_notice": {
                "value": {
                    "title": "legacy custom message",
                    "text": "$builtin_default_external_notification",
                }
            }
        }

        await execute_external_notification(context, option)

        self.assertEqual(
            [("MFW", "legacy custom message", None)],
            context.sent,
        )

    async def test_warns_when_requested_screenshot_is_unavailable(self):
        context = _Context()
        context.screenshot = None
        option = {
            "external_notice": {"value": {"text": "body"}},
            "include_screenshot": {"value": "Yes"},
        }

        await execute_external_notification(context, option)

        self.assertEqual("WARNING", context.logs[0][0])
        self.assertIn("screenshot", context.logs[0][1])

    async def test_definition_uses_multiline_body_and_screenshot_switch(self):
        definition = next(
            task
            for task in get_builtin_tasks()
            if task["key"] == "external_notification"
        )

        self.assertEqual(
            ["external_notice", "include_screenshot"],
            definition["options"],
        )
        body_input = definition["option_defs"]["external_notice"]["inputs"][0]
        self.assertTrue(body_input["multiline"])
        self.assertEqual(
            "switch",
            definition["option_defs"]["include_screenshot"]["type"],
        )


if __name__ == "__main__":
    unittest.main()
