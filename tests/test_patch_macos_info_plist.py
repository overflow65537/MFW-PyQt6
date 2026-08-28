import plistlib
import tempfile
import unittest
from pathlib import Path

from tools.packaging.patch_macos_info_plist import patch_info_plist


class PatchMacosInfoPlistTests(unittest.TestCase):
    def test_patch_adds_localizations_and_removes_english_dev_region(self):
        with tempfile.TemporaryDirectory() as raw:
            app = Path(raw) / "MFW.app"
            plist_path = app / "Contents" / "Info.plist"
            plist_path.parent.mkdir(parents=True)
            plist_path.write_bytes(
                plistlib.dumps(
                    {
                        "CFBundleExecutable": "MFW",
                        "CFBundleDevelopmentRegion": "English",
                    },
                    fmt=plistlib.FMT_XML,
                )
            )

            patch_info_plist(app)

            info = plistlib.loads(plist_path.read_bytes())
            self.assertTrue(info["CFBundleAllowMixedLocalizations"])
            self.assertEqual(
                info["CFBundleLocalizations"],
                ["en", "zh-Hans", "zh-Hant", "ja"],
            )
            self.assertNotIn("CFBundleDevelopmentRegion", info)


if __name__ == "__main__":
    unittest.main()
