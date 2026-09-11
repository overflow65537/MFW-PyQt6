import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.utils.install_paths import (
    APP_EXECUTABLE_RELATIVE_PATH,
    UPDATER_COPY_DIR_NAME,
    UPDATER_DIR_NAME,
    UPDATER_EXECUTABLE_NAME,
    is_app_bundle_layout,
    normalize_install_anchor,
    resolve_app_i18n_dir,
    resolve_install_root,
    resolve_main_executable,
    resolve_schedule_launch_command,
    resolve_updater_copy_dir,
    resolve_updater_dir,
    resolve_updater_executable,
    resolve_updater_paths,
)


class InstallPathTests(unittest.TestCase):
    def test_resolves_flat_install_root(self):
        anchor = Path("release") / "MFW.exe"
        self.assertEqual(resolve_install_root(anchor), anchor.resolve().parent)

    def test_resolves_app_bundle_parent_as_install_root(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            anchor = root / "MFW.app" / APP_EXECUTABLE_RELATIVE_PATH
            anchor.parent.mkdir(parents=True)
            anchor.touch()

            self.assertTrue(is_app_bundle_layout(anchor))
            self.assertEqual(resolve_install_root(anchor), root.resolve())
            self.assertEqual(resolve_main_executable(root, anchor=anchor), anchor.resolve())

    def test_normalizes_app_path_to_bundle_executable(self):
        app = Path("release") / "MFW.app"
        self.assertEqual(
            normalize_install_anchor(app),
            (app / APP_EXECUTABLE_RELATIVE_PATH).resolve(),
        )

    def test_resolves_updater_and_running_copy(self):
        root = Path("release").resolve()
        updater_dir = resolve_updater_dir(root)
        updater_copy_dir = resolve_updater_copy_dir(root)
        updater, updater_copy = resolve_updater_paths(root)
        self.assertEqual(updater_dir, root / UPDATER_DIR_NAME)
        self.assertEqual(updater_copy_dir, root / UPDATER_COPY_DIR_NAME)
        self.assertEqual(updater, resolve_updater_executable(updater_dir))
        self.assertEqual(updater_copy, resolve_updater_executable(updater_copy_dir))
        self.assertEqual(updater.parent, updater_dir)
        self.assertEqual(updater_copy.parent, updater_copy_dir)

    def test_prepare_updater_skips_rename_when_official_dir_missing(self):
        from app.utils.install_paths import (
            prepare_updater_runtime_copy,
            rename_updater_binary,
        )

        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            copy_dir = root / UPDATER_COPY_DIR_NAME
            copy_dir.mkdir()
            (copy_dir / UPDATER_EXECUTABLE_NAME).touch()

            self.assertFalse(
                rename_updater_binary(root / UPDATER_DIR_NAME, copy_dir)
            )
            self.assertTrue(copy_dir.exists())
            self.assertTrue((copy_dir / UPDATER_EXECUTABLE_NAME).exists())

            renamed, runtime_dir = prepare_updater_runtime_copy(root)
            self.assertFalse(renamed)
            self.assertEqual(runtime_dir, copy_dir.resolve())
            self.assertTrue(copy_dir.exists())
            self.assertTrue((copy_dir / UPDATER_EXECUTABLE_NAME).exists())

    def test_prepare_updater_renames_when_official_dir_exists(self):
        from app.utils.install_paths import prepare_updater_runtime_copy

        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            official = root / UPDATER_DIR_NAME
            copy_dir = root / UPDATER_COPY_DIR_NAME
            official.mkdir()
            (official / UPDATER_EXECUTABLE_NAME).touch()
            copy_dir.mkdir()
            (copy_dir / "stale.txt").touch()

            renamed, runtime_dir = prepare_updater_runtime_copy(root)
            self.assertTrue(renamed)
            self.assertEqual(runtime_dir, copy_dir.resolve())
            self.assertFalse(official.exists())
            self.assertTrue(copy_dir.exists())
            self.assertTrue((copy_dir / UPDATER_EXECUTABLE_NAME).exists())
            self.assertFalse((copy_dir / "stale.txt").exists())

    def test_schedule_uses_bundle_executable(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            executable = root / "MFW.app" / APP_EXECUTABLE_RELATIVE_PATH
            executable.parent.mkdir(parents=True)
            executable.touch()
            with (
                patch(
                    "app.utils.install_paths.resolve_install_anchor",
                    return_value=executable,
                ),
                patch("app.utils.install_paths.is_packed", return_value=True),
            ):
                command, arguments = resolve_schedule_launch_command(
                    "config-a", force_start=True
                )
            self.assertEqual(command, str(executable.resolve()))
            self.assertIn("--config-id=config-a", arguments)
            self.assertIn("--force-restart", arguments)

    def test_resolves_app_i18n_dir_for_dev_fallback(self):
        resolved = resolve_app_i18n_dir()
        expected = (
            Path(__file__).resolve().parents[1] / "app" / "i18n"
        ).resolve()
        self.assertEqual(resolved, expected)


if __name__ == "__main__":
    unittest.main()
