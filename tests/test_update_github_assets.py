import unittest
from types import SimpleNamespace
from unittest.mock import patch

try:
    from app.utils.update import (
        Update,
        derive_download_filename,
        path_is_update_archive_readable,
    )
except ModuleNotFoundError as exc:  # 精简环境下可能未安装 PySide6
    if "PySide6" not in str(exc):
        raise
    Update = None
    derive_download_filename = None
    path_is_update_archive_readable = None


def _asset_selector(os_type: str, arch: str = "aarch64"):
    selector = Update.__new__(Update)
    selector.current_os_type = os_type
    selector.current_arch = arch
    selector.project_name = "MFW-PyQt6"
    return selector


@unittest.skipIf(Update is None, "PySide6 not installed")
class DeriveDownloadFilenameTests(unittest.TestCase):
    def test_prefers_content_disposition(self):
        resp = SimpleNamespace(
            headers={"content-disposition": 'attachment; filename="MFW.dmg"'},
            url="https://example.com/ignored.zip",
        )
        self.assertEqual(derive_download_filename(resp), "MFW.dmg")

    def test_falls_back_to_response_url(self):
        resp = SimpleNamespace(
            headers={},
            url="https://github.com/o/r/releases/download/v1.0.0/MFW-macos-arm64.dmg",
        )
        self.assertEqual(
            derive_download_filename(resp, "https://example.com/fallback.zip"),
            "MFW-macos-arm64.dmg",
        )

    def test_falls_back_to_update_zip(self):
        resp = SimpleNamespace(headers={}, url="")
        self.assertEqual(derive_download_filename(resp, ""), "update.zip")


@unittest.skipIf(Update is None, "PySide6 not installed")
class GithubUiAssetSelectionTests(unittest.TestCase):
    def test_macos_accepts_dmg_and_scores_it_highest(self):
        selector = _asset_selector("macos")
        self.assertTrue(
            selector._github_release_asset_accepted(
                "mfw.dmg", False, zip_tar_github_assets_only=True
            )
        )
        dmg_bonus = selector._github_release_asset_format_bonus(
            "mfw.dmg", False, zip_tar_github_assets_only=True
        )
        tar_bonus = selector._github_release_asset_format_bonus(
            "mfw.tar.gz", False, zip_tar_github_assets_only=True
        )
        zip_bonus = selector._github_release_asset_format_bonus(
            "mfw.zip", False, zip_tar_github_assets_only=True
        )
        self.assertEqual(dmg_bonus, 12)
        self.assertGreater(dmg_bonus, tar_bonus)
        self.assertGreater(tar_bonus, zip_bonus)

    def test_macos_prefers_dmg_over_zip_and_tar(self):
        selector = _asset_selector("macos")
        chosen = selector._select_github_asset_by_keywords(
            [
                {
                    "name": "MFW-PyQt6-macos-aarch64-v1.0.0.zip",
                    "browser_download_url": "https://example.com/app.zip",
                },
                {
                    "name": "MFW-PyQt6-macos-aarch64-v1.0.0.tar.gz",
                    "browser_download_url": "https://example.com/app.tar.gz",
                },
                {
                    "name": "MFW-PyQt6-macos-aarch64-v1.0.0.dmg",
                    "browser_download_url": "https://example.com/app.dmg",
                },
            ],
            "v1.0.0",
            primary_name="MFW-PyQt6",
            zip_tar_github_assets_only=True,
        )
        self.assertIsNotNone(chosen)
        self.assertEqual(chosen["name"], "MFW-PyQt6-macos-aarch64-v1.0.0.dmg")

    def test_linux_ui_update_rejects_dmg(self):
        selector = _asset_selector("linux")
        self.assertFalse(
            selector._github_release_asset_accepted(
                "mfw.dmg", False, zip_tar_github_assets_only=True
            )
        )

    def test_path_is_update_archive_readable_dmg_is_macos_only(self):
        with patch("app.utils.update.sys.platform", "darwin"):
            self.assertTrue(path_is_update_archive_readable("update.dmg"))
        with patch("app.utils.update.sys.platform", "win32"):
            self.assertFalse(path_is_update_archive_readable("update.dmg"))


if __name__ == "__main__":
    unittest.main()
