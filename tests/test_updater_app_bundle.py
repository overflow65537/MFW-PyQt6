import os
import stat
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

import updater


def _write_app(root: Path, version: str) -> Path:
    app = root / "MFW.app"
    executable = app / "Contents" / "MacOS" / "MFW"
    executable.parent.mkdir(parents=True)
    executable.write_text(version, encoding="utf-8")
    (app / "Contents" / "Info.plist").write_text(
        f"<plist><string>{version}</string></plist>", encoding="utf-8"
    )
    return app


class AppBundleUpdateTests(unittest.TestCase):
    def test_zip_extraction_preserves_executable_mode(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            archive_path = root / "app.zip"
            info = zipfile.ZipInfo("MFW.app/Contents/MacOS/MFW")
            info.external_attr = (stat.S_IFREG | 0o755) << 16
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr(info, b"binary")

            destination = root / "extract"
            with zipfile.ZipFile(archive_path) as archive:
                updater._extract_zip_member_preserving_mode(
                    archive, archive.getinfo(info.filename), destination
                )

            executable = destination / info.filename
            self.assertEqual(executable.read_bytes(), b"binary")
            if os.name != "nt":
                self.assertTrue(executable.stat().st_mode & stat.S_IXUSR)

    def test_replaces_app_and_runtime_but_preserves_user_data(self):
        with tempfile.TemporaryDirectory() as raw:
            base = Path(raw)
            install_root = base / "install"
            payload = base / "payload"
            install_root.mkdir()
            payload.mkdir()
            _write_app(install_root, "old")
            _write_app(payload, "new")
            (install_root / "maafw").mkdir()
            (install_root / "maafw" / "old.dylib").write_text("old")
            (payload / "maafw").mkdir()
            (payload / "maafw" / "new.dylib").write_text("new")
            (payload / "MFWUpdater").write_text("updater")

            for name in ("config", "bundle", "resource", "update"):
                directory = install_root / name
                directory.mkdir()
                (directory / "keep.txt").write_text("keep")
            (install_root / "interface.json").write_text("{}")

            self.assertTrue(
                updater._replace_app_bundle_atomic(payload, install_root)
            )
            self.assertEqual(
                (
                    install_root
                    / "MFW.app"
                    / "Contents"
                    / "MacOS"
                    / "MFW"
                ).read_text(),
                "new",
            )
            self.assertTrue((install_root / "maafw" / "new.dylib").is_file())
            self.assertFalse((install_root / "maafw" / "old.dylib").exists())
            self.assertTrue((install_root / "MFWUpdater").is_file())
            self.assertTrue((install_root / "interface.json").is_file())
            for name in ("config", "bundle", "resource", "update"):
                self.assertTrue((install_root / name / "keep.txt").is_file())

    def test_rolls_back_when_staging_cannot_be_installed(self):
        with tempfile.TemporaryDirectory() as raw:
            base = Path(raw)
            install_root = base / "install"
            payload = base / "payload"
            install_root.mkdir()
            payload.mkdir()
            _write_app(install_root, "old")
            _write_app(payload, "new")

            real_replace = os.replace
            failed_once = False

            def fail_new_app_once(src, dst):
                nonlocal failed_once
                src_path = Path(src)
                dst_path = Path(dst)
                if (
                    not failed_once
                    and ".MFW.app.staging-" in src_path.name
                    and dst_path.name == "MFW.app"
                ):
                    failed_once = True
                    raise OSError("simulated install failure")
                return real_replace(src, dst)

            with patch("updater.os.replace", side_effect=fail_new_app_once):
                self.assertFalse(
                    updater._replace_app_bundle_atomic(payload, install_root)
                )

            executable = (
                install_root / "MFW.app" / "Contents" / "MacOS" / "MFW"
            )
            self.assertEqual(executable.read_text(), "old")
            self.assertFalse(
                any(".staging-" in path.name for path in install_root.iterdir())
            )

    def test_rejects_incomplete_app(self):
        with tempfile.TemporaryDirectory() as raw:
            base = Path(raw)
            install_root = base / "install"
            payload = base / "payload"
            install_root.mkdir()
            (payload / "MFW.app" / "Contents").mkdir(parents=True)
            self.assertFalse(
                updater._replace_app_bundle_atomic(payload, install_root)
            )

    def test_restart_uses_install_root_as_working_directory(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            executable = root / "MFW.app" / "Contents" / "MacOS" / "MFW"
            executable.parent.mkdir(parents=True)
            executable.touch()
            with (
                patch(
                    "updater._restore_startup_executable_name",
                    return_value=str(executable),
                ),
                patch("updater.os.getcwd", return_value=str(root)),
                patch("updater.subprocess.Popen") as popen,
            ):
                updater.start_mfw_process()
            popen.assert_called_once()
            self.assertEqual(popen.call_args.kwargs["cwd"], str(root))


if __name__ == "__main__":
    unittest.main()
