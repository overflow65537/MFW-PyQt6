from __future__ import annotations

import base64
import hashlib
import unittest

from app.utils.notice_content import (
    build_custom_message,
    build_log_summary,
    build_simple_message,
)
from app.utils.notice_image import encode_image_payload


class TestNoticeContent(unittest.TestCase):
    def test_simple_message_builds_all_formats(self):
        payload = build_simple_message(
            "Task Complete",
            "Everything worked.",
            timestamp="2026-09-19 20:00:00",
        )

        self.assertEqual(
            "2026-09-19 20:00:00: Everything worked.", payload.plain_text
        )
        self.assertIn("<h2", payload.html_body)
        self.assertIn("Everything worked.", payload.html_body)
        self.assertIn("**Task Complete**", payload.markdown_body)

    def test_custom_message_escapes_html_and_preserves_newlines(self):
        payload = build_custom_message(
            "MFW",
            "<script>alert(1)</script>\nsecond line",
            timestamp="now",
        )

        self.assertNotIn("<script>", payload.html_body)
        self.assertIn("&lt;script&gt;", payload.html_body)
        self.assertIn("<br>", payload.html_body)
        self.assertEqual("<script>alert(1)</script>\nsecond line", payload.plain_text[5:])

    def test_custom_message_escapes_markdown_control_characters(self):
        payload = build_custom_message(
            "MFW",
            "# heading *bold* [link](url)",
            timestamp="now",
        )

        self.assertIn(r"\# heading \*bold\*", payload.markdown_body)
        self.assertIn(r"\[link\]\(url\)", payload.markdown_body)

    def test_log_summary_formats_level_and_escapes_text(self):
        payload = build_log_summary(
            "Summary",
            "[12:00:00][ERROR]<bad>\nplain",
            timestamp="now",
        )

        self.assertIn("#dc2626", payload.html_body)
        self.assertIn("&lt;bad&gt;", payload.html_body)
        self.assertIn("**[ERROR]**", payload.markdown_body)
        self.assertIn("plain", payload.markdown_body)

    def test_message_dict_omits_empty_image(self):
        payload = build_simple_message("Title", "Body", timestamp="now")
        self.assertNotIn("image_bytes", payload.as_message_dict())

    def test_image_payload_contains_base64_md5_and_data_uri(self):
        image = b"\x89PNG\r\n\x1a\nexample"
        payload = encode_image_payload(image)

        self.assertEqual(base64.b64encode(image).decode("ascii"), payload.base64_data)
        self.assertEqual(hashlib.md5(image).hexdigest(), payload.md5)
        self.assertEqual("image/png", payload.mime_type)
        self.assertTrue(payload.data_uri.startswith("data:image/png;base64,"))


if __name__ == "__main__":
    unittest.main()
