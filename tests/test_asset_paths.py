import unittest

from app.utils.asset_paths import (
    APP_LOGO_QT_RESOURCE,
    DEFAULT_APP_LOGO_FILE,
    is_default_app_logo_path,
)


class AssetPathTests(unittest.TestCase):
    def test_default_logo_path_constants(self):
        self.assertEqual(DEFAULT_APP_LOGO_FILE, "app/assets/icons/logo.png")
        self.assertEqual(APP_LOGO_QT_RESOURCE, ":/icons/logo.png")

    def test_is_default_app_logo_path(self):
        self.assertTrue(is_default_app_logo_path(None))
        self.assertTrue(is_default_app_logo_path("app/assets/icons/logo.png"))
        self.assertTrue(is_default_app_logo_path("./app/assets/icons/logo.png"))
        self.assertTrue(is_default_app_logo_path(APP_LOGO_QT_RESOURCE))
        self.assertFalse(is_default_app_logo_path("resource/base/icon.png"))

    def test_load_app_logo_pixmap_from_dev_file(self) -> None:
        try:
            from PySide6.QtGui import QPixmap  # noqa: F401
        except ImportError:
            self.skipTest("PySide6 not installed")
        from app.utils.asset_paths import load_app_logo_pixmap

        pixmap = load_app_logo_pixmap()
        self.assertIsNotNone(pixmap)
        assert pixmap is not None
        self.assertFalse(pixmap.isNull())


if __name__ == "__main__":
    unittest.main()
