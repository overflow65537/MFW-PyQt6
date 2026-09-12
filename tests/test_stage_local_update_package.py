"""本地拖入更新包暂存逻辑测试。"""

from __future__ import annotations

import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from app.utils.local_update import (
    local_update_package_dir,
    path_is_update_archive_readable,
    stage_local_update_package,
)


class StageLocalUpdatePackageTests(unittest.TestCase):
    def test_path_is_update_archive_readable_zip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / "payload.zip"
            with zipfile.ZipFile(archive, "w") as zf:
                zf.writestr("readme.txt", "ok")
            self.assertTrue(path_is_update_archive_readable(archive))

    def test_stage_copies_to_full_package_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "MFW-release.zip"
            with zipfile.ZipFile(source, "w") as zf:
                zf.writestr("interface.json", "{}")

            cwd = root / "app_root"
            cwd.mkdir()
            with patch("app.utils.local_update.Path.cwd", return_value=cwd):
                staged = stage_local_update_package(source, version="v9.9.9")
                target_dir = local_update_package_dir()
                self.assertEqual(staged, target_dir / "update.zip")
                self.assertTrue(staged.is_file())
                metadata = json.loads(
                    (target_dir / "update_metadata.json").read_text(encoding="utf-8")
                )
            self.assertEqual(metadata["source"], "local")
            self.assertEqual(metadata["mode"], "full")
            self.assertEqual(metadata["package_name"], "update.zip")
            self.assertEqual(metadata["version"], "v9.9.9")
            self.assertEqual(metadata["attempts"], 0)

    def test_stage_rejects_unsupported_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "notes.txt"
            source.write_text("not an archive", encoding="utf-8")
            cwd = root / "app_root"
            cwd.mkdir()
            with patch("app.utils.local_update.Path.cwd", return_value=cwd):
                with self.assertRaises(ValueError):
                    stage_local_update_package(source)


if __name__ == "__main__":
    unittest.main()
