"""resource_pipeline_check 单元测试。"""

from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from app.core.utils.resource_pipeline_check import (
    check_resource_pipeline,
    format_pipeline_issue,
)


class ResourcePipelineCheckTest(unittest.TestCase):
    def _write(self, root: Path, relative: str, content: str) -> Path:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def test_valid_pipeline_passes(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root,
                "pipeline/a.json",
                '{"NodeA": {"action": "DoNothing"}, "NodeB": {"action": "DoNothing"}}\n',
            )
            self._write(
                root,
                "pipeline/sub/b.jsonc",
                """
                // comment is allowed
                {
                  "NodeC": {
                    "action": "DoNothing"
                  }
                }
                """,
            )
            issues = check_resource_pipeline(root)
            self.assertEqual(issues, [])

    def test_missing_pipeline_dir_passes(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            issues = check_resource_pipeline(root)
            self.assertEqual(issues, [])

    def test_duplicate_in_same_file(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = self._write(
                root,
                "pipeline/dup.json",
                '{"Same": {"action": "DoNothing"}, "Same": {"action": "Click"}}\n',
            )
            issues = check_resource_pipeline(root)
            self.assertEqual(len(issues), 1)
            self.assertEqual(issues[0].kind, "duplicate_in_file")
            self.assertEqual(issues[0].key, "Same")
            self.assertEqual(issues[0].path, path)
            self.assertIn('duplicate node "Same"', format_pipeline_issue(issues[0]))

    def test_duplicate_across_files(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            first = self._write(
                root,
                "pipeline/a.json",
                '{"Shared": {"action": "DoNothing"}}\n',
            )
            second = self._write(
                root,
                "pipeline/b.json",
                '{"Shared": {"action": "Click"}}\n',
            )
            issues = check_resource_pipeline(root)
            self.assertEqual(len(issues), 1)
            self.assertEqual(issues[0].kind, "duplicate_across_files")
            self.assertEqual(issues[0].key, "Shared")
            self.assertEqual(issues[0].first_path, first)
            self.assertEqual(issues[0].path, second)
            text = format_pipeline_issue(issues[0])
            self.assertIn('duplicate node "Shared"', text)
            self.assertIn(str(first), text)

    def test_invalid_json(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = self._write(root, "pipeline/bad.json", '{"broken": \n')
            issues = check_resource_pipeline(root)
            self.assertEqual(len(issues), 1)
            self.assertEqual(issues[0].kind, "parse_error")
            self.assertEqual(issues[0].path, path)
            self.assertIn("invalid JSON", format_pipeline_issue(issues[0]))


if __name__ == "__main__":
    unittest.main()
