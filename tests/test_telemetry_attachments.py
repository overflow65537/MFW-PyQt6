"""PI v2.9.2 失败诊断附件采样与收集测试。"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.core.utils.telemetry_attachments import (
    collect_failure_diagnostic_files,
    parse_unit_interval,
    should_sample_attachments,
)


class TestParseUnitInterval(unittest.TestCase):
    def test_clamps_and_falls_back(self):
        self.assertEqual(0.0, parse_unit_interval(-1))
        self.assertEqual(1.0, parse_unit_interval(2))
        self.assertEqual(0.25, parse_unit_interval("0.25"))
        self.assertEqual(1.0, parse_unit_interval("bad", default=1.0))
        self.assertEqual(0.0, parse_unit_interval(None, default=0.0))


class TestShouldSampleAttachments(unittest.TestCase):
    def test_rate_zero_never_samples(self):
        self.assertFalse(should_sample_attachments(0))
        self.assertFalse(should_sample_attachments(0.0))

    def test_rate_one_always_samples(self):
        self.assertTrue(should_sample_attachments(1))
        self.assertTrue(should_sample_attachments(1.0))

    def test_mid_rate_uses_rng(self):
        class _FixedRng:
            def __init__(self, value: float):
                self._value = value

            def random(self) -> float:
                return self._value

        self.assertTrue(should_sample_attachments(0.5, rng=_FixedRng(0.49)))
        self.assertFalse(should_sample_attachments(0.5, rng=_FixedRng(0.5)))


class TestCollectFailureDiagnosticFiles(unittest.TestCase):
    def test_collects_newest_images_and_log_tail(self):
        with tempfile.TemporaryDirectory() as raw_root:
            root = Path(raw_root)
            (root / "on_error").mkdir()
            (root / "vision").mkdir()
            (root / "on_error" / "err.png").write_bytes(b"png-err")
            (root / "vision" / "frame.jpg").write_bytes(b"jpg-vis")
            oversized = root / "on_error" / "huge.png"
            oversized.write_bytes(b"x" * (2 * 1024 * 1024 + 1))
            (root / "maafw.log").write_bytes(b"head\n" + b"tail-line\n")

            attachments = collect_failure_diagnostic_files(root)
            names = [item["filename"] for item in attachments]
            self.assertIn("on_error_err.png", names)
            self.assertIn("vision_frame.jpg", names)
            self.assertIn("maafw.log.tail.txt", names)
            self.assertNotIn("on_error_huge.png", names)
            log = next(
                item for item in attachments if item["filename"] == "maafw.log.tail.txt"
            )
            self.assertIn(b"tail-line", log["bytes"])

    def test_missing_debug_root_returns_empty(self):
        with tempfile.TemporaryDirectory() as raw_root:
            self.assertEqual(
                [], collect_failure_diagnostic_files(Path(raw_root) / "missing")
            )


if __name__ == "__main__":
    unittest.main()
