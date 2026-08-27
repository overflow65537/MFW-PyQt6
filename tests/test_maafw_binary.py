import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.utils.maafw_binary import (
    configure_packed_maafw_binary_path,
    prepare_macos_rpath_layout,
    resolve_maafw_binary_dir,
)
from tools.packaging.fix_maafw_macos_dylib_paths import rewrite_maafw_dependency
from tools.packaging.move_maa_bin_to_maafw import move_maa_bin_to_maafw


def _touch(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"dylib")


class ResolveMaafwBinaryDirTests(unittest.TestCase):
    def test_prefers_nested_maa_bin_when_framework_exists(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            nested = root / "maafw" / "maa" / "bin"
            _touch(nested / "libMaaFramework.dylib")
            _touch(root / "maafw" / "libMaaFramework.dylib")
            found = resolve_maafw_binary_dir(root)
            self.assertEqual(found, nested.resolve())

    def test_falls_back_to_flat_maafw(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            _touch(root / "maafw" / "libMaaFramework.dylib")
            found = resolve_maafw_binary_dir(root)
            self.assertEqual(found, (root / "maafw").resolve())

    def test_ignores_framework_outside_maafw(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            _touch(root / "runtime" / "libMaaFramework.dylib")
            found = resolve_maafw_binary_dir(root)
            self.assertEqual(found, (root / "maafw").resolve())


class PrepareMacosRpathLayoutTests(unittest.TestCase):
    def test_mirrors_nested_bin_dylibs_two_levels_up(self):
        with tempfile.TemporaryDirectory() as raw:
            nested = Path(raw) / "maafw" / "maa" / "bin"
            _touch(nested / "libMaaFramework.dylib")
            _touch(nested / "libMaaUtils.dylib")
            with patch("app.utils.maafw_binary.sys.platform", "darwin"):
                result = prepare_macos_rpath_layout(nested)
            self.assertEqual(result, nested)
            self.assertTrue((Path(raw) / "maafw" / "libMaaUtils.dylib").is_file())
            self.assertTrue((Path(raw) / "maafw" / "libMaaFramework.dylib").is_file())

    def test_flat_layout_gets_nested_bin_view_so_rpath_resolves(self):
        with tempfile.TemporaryDirectory() as raw:
            maafw = Path(raw) / "maafw"
            _touch(maafw / "libMaaFramework.dylib")
            _touch(maafw / "libMaaUtils.dylib")
            with patch("app.utils.maafw_binary.sys.platform", "darwin"):
                result = prepare_macos_rpath_layout(maafw)
            nested = maafw / "maa" / "bin"
            self.assertEqual(result, nested)
            self.assertTrue((nested / "libMaaFramework.dylib").is_file())
            self.assertTrue((nested / "libMaaUtils.dylib").is_file())
            self.assertTrue((maafw / "libMaaUtils.dylib").is_file())


class ConfigurePackedMaafwBinaryPathTests(unittest.TestCase):
    def test_sets_env_to_nested_bin_after_macos_prepare(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            nested = root / "maafw" / "maa" / "bin"
            _touch(nested / "libMaaFramework.dylib")
            _touch(nested / "libMaaUtils.dylib")
            old = os.environ.get("MAAFW_BINARY_PATH")
            try:
                with patch("app.utils.maafw_binary.sys.platform", "darwin"):
                    configured = configure_packed_maafw_binary_path(root)
                self.assertEqual(configured, nested.resolve())
                self.assertEqual(os.environ["MAAFW_BINARY_PATH"], str(nested.resolve()))
                self.assertTrue((root / "maafw" / "libMaaUtils.dylib").is_file())
            finally:
                if old is None:
                    os.environ.pop("MAAFW_BINARY_PATH", None)
                else:
                    os.environ["MAAFW_BINARY_PATH"] = old


class MoveMaafwBinaryTests(unittest.TestCase):
    def test_moves_bundle_maa_bin_to_external_release_root(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            source = root / "MFW.app" / "Contents" / "MacOS"
            destination = root / "release"
            _touch(source / "maa" / "bin" / "libMaaFramework.dylib")
            _touch(source / "maa" / "bin" / "plugins" / "libMaaPlugin.dylib")

            self.assertTrue(move_maa_bin_to_maafw(source, destination))
            self.assertTrue(
                (destination / "maafw" / "libMaaFramework.dylib").is_file()
            )
            self.assertTrue(
                (
                    destination
                    / "maafw"
                    / "plugins"
                    / "libMaaPlugin.dylib"
                ).is_file()
            )
            self.assertFalse((source / "maa" / "bin").exists())


class RewriteMaafwDependencyTests(unittest.TestCase):
    def test_rewrites_executable_path_maa_bin_to_loader_path(self):
        old = "@executable_path/maa/bin/libfastdeploy_ppocr.dylib"
        self.assertEqual(
            rewrite_maafw_dependency(old),
            "@loader_path/libfastdeploy_ppocr.dylib",
        )

    def test_rewrites_absolute_maa_bin_path(self):
        old = "/tmp/build/maa/bin/libMaaUtils.dylib"
        self.assertEqual(
            rewrite_maafw_dependency(old),
            "@loader_path/libMaaUtils.dylib",
        )


if __name__ == "__main__":
    unittest.main()
