import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.utils.install_paths import (
    APP_EXECUTABLE_RELATIVE_PATH,
    is_app_bundle_layout,
    normalize_install_anchor,
    resolve_install_root,
    resolve_main_executable,
    resolve_schedule_launch_command,
    resolve_updater_paths,
)


class InstallPathTests(unittest.TestCase):
    def test_resolves_flat_install_root(self):
        anchor = Path("release") / "MFW.exe"
        self.assertEqual(resolve_install_root(anchor), anchor.resolve().parent)

    def test_resolves_pyinstaller_internal_root(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            anchor = root / "_internal" / "MFW"
            self.assertEqual(
                resolve_install_root(anchor, meipass=root / "_internal"),
                root.resolve(),
            )

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
        updater, updater_copy = resolve_updater_paths(root)
        self.assertEqual(updater.parent, root)
        self.assertEqual(updater_copy.parent, root)
        self.assertEqual(updater_copy.stem, f"{updater.stem}1")

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


if __name__ == "__main__":
    unittest.main()
