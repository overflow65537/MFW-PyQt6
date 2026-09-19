from __future__ import annotations

import base64
import hashlib
import unittest
from unittest.mock import patch

from app.utils.notice import DingTalk, Lark, QYWX, SMTP, Webhook
from app.utils.notice_content import build_simple_message


class TestNoticeChannels(unittest.TestCase):
    def setUp(self):
        self.message = build_simple_message(
            "Title",
            "Body",
            timestamp="2026-09-19 20:00:00",
            image_bytes=b"\x89PNG\r\n\x1a\nimage",
        ).as_message_dict()

    def test_dingtalk_uses_markdown_variant(self):
        message = DingTalk().msg(self.message)
        self.assertEqual("markdown", message["msgtype"])
        self.assertEqual(
            self.message["markdown"],
            message["markdown"]["text"],
        )

    def test_qywx_image_contains_base64_and_md5(self):
        image = b"\x89PNG\r\n\x1a\nimage"
        message = QYWX.image_msg(image)

        self.assertIsNotNone(message)
        self.assertEqual("image", message["msgtype"])
        self.assertEqual(
            base64.b64encode(image).decode("ascii"),
            message["image"]["base64"],
        )
        self.assertEqual(hashlib.md5(image).hexdigest(), message["image"]["md5"])

    def test_lark_uses_interactive_markdown_card(self):
        channel = Lark()
        channel.sign = lambda: ["https://example.com", "timestamp", "signature"]

        message = channel.msg(self.message)

        self.assertEqual("interactive", message["msg_type"])
        markdown = message["card"]["elements"][0]["text"]
        self.assertEqual("lark_md", markdown["tag"])
        self.assertEqual(self.message["markdown"], markdown["content"])

    def test_qywx_truncates_long_markdown_to_api_limit(self):
        message = dict(self.message)
        message["markdown"] = "测" * 5000

        content = QYWX().msg(message)["markdown"]["content"]

        self.assertLessEqual(len(content.encode("utf-8")), 3900)
        self.assertTrue(content.endswith("…"))

    def test_smtp_embeds_and_attaches_screenshot(self):
        message = dict(self.message)
        message["image_bytes"] = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0l"
            "EQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
        )

        with patch("app.utils.notice.cfg.get", return_value="test@example.com"):
            mime = SMTP().msg(message)

        self.assertEqual("multipart/related", mime.get_content_type())
        image_parts = [
            part for part in mime.walk() if part.get_content_maintype() == "image"
        ]
        self.assertEqual(2, len(image_parts))
        html_part = mime.get_payload()[0]
        html_body = html_part.get_payload(decode=True).decode("utf-8")
        self.assertIn("cid:screenshot", html_body)

    def test_webhook_json_contains_rich_text_and_image_fields(self):
        message = Webhook().msg(self.message)

        self.assertEqual(self.message["html"], message["html"])
        self.assertEqual(self.message["markdown"], message["markdown"])
        self.assertIn("image_base64", message)
        self.assertIn("image_md5", message)
        self.assertEqual("image/png", message["image_content_type"])

    def test_webhook_multipart_contains_image_file(self):
        payload = Webhook._multipart_payload(self.message)

        self.assertIsNotNone(payload)
        data, files = payload
        self.assertEqual(self.message["text"], data["content"])
        self.assertEqual(self.message["text"], data["text"])
        self.assertEqual("screenshot.png", files["image"][0])
        self.assertEqual("image/png", files["image"][2])


if __name__ == "__main__":
    unittest.main()
