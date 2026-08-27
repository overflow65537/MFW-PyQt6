import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.utils.maafw_binary import (
    configure_packed_maafw_binary_path,
    prepare_macos_rpath_layout,
    resolve_maafw_binary_dir,
    restore_internal_dylibs_from_maafw,
)


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

    def test_does_not_use_pyinstaller_internal_as_maafw_dir(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            meipass = root / "_internal"
            _touch(meipass / "libMaaFramework.dylib")
            _touch(meipass / "libshiboken6.abi3.6.11.dylib")
            found = resolve_maafw_binary_dir(root, meipass=str(meipass))
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
            # @loader_path/../.. from nested bin must still see the originals
            self.assertTrue((maafw / "libMaaUtils.dylib").is_file())


class RestoreInternalDylibsTests(unittest.TestCase):
    def test_puts_stolen_shiboken_back_into_internal(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            internal = root / "_internal"
            internal.mkdir()
            stolen = root / "maafw" / "libshiboken6.abi3.6.11.dylib"
            _touch(stolen)
            _touch(root / "maafw" / "libMaaUtils.dylib")
            restored = restore_internal_dylibs_from_maafw(root, meipass=str(internal))
            self.assertIn("libshiboken6.abi3.6.11.dylib", restored)
            self.assertTrue((internal / "libshiboken6.abi3.6.11.dylib").is_file())
            self.assertFalse((internal / "libMaaUtils.dylib").exists())


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


if __name__ == "__main__":
    unittest.main()
