import unittest
from unittest.mock import patch

from PySide6.QtCore import QLocale

from app.common.config import (
    Language,
    _language_from_ui_tag,
    _parse_defaults_apple_languages,
    detect_system_language,
)


class LanguageFromUiTagTests(unittest.TestCase):
    def test_zh_hans_is_simplified(self):
        self.assertEqual(_language_from_ui_tag("zh-Hans-CN"), Language.CHINESE_SIMPLIFIED)

    def test_zh_tw_is_traditional(self):
        self.assertEqual(_language_from_ui_tag("zh-Hant-TW"), Language.CHINESE_TRADITIONAL)

    def test_ja(self):
        self.assertEqual(_language_from_ui_tag("ja-JP"), Language.JAPANESE)

    def test_en(self):
        self.assertEqual(_language_from_ui_tag("en-US"), Language.ENGLISH)


class ParseDefaultsAppleLanguagesTests(unittest.TestCase):
    def test_parse_array_output(self):
        output = "(\n    \"zh-Hans-CN\",\n    \"en-US\",\n)"
        self.assertEqual(
            _parse_defaults_apple_languages(output),
            ["zh-Hans-CN", "en-US"],
        )


class DetectSystemLanguageTests(unittest.TestCase):
    def test_macos_uses_apple_languages(self):
        with patch("sys.platform", "darwin"):
            with patch(
                "app.common.config._macos_apple_languages",
                return_value=["zh-Hans-CN", "en-US"],
            ):
                self.assertEqual(
                    detect_system_language(),
                    Language.CHINESE_SIMPLIFIED,
                )

    def test_non_macos_prefers_ui_languages(self):
        with patch("sys.platform", "linux"):
            with patch("PySide6.QtCore.QLocale.system") as mock_system:
                locale = mock_system.return_value
                locale.uiLanguages.return_value = ["zh-Hans-CN", "en-US"]
                locale.name.return_value = "en_US"
                locale.language.return_value = QLocale.Language.English
                locale.country.return_value = QLocale.Country.UnitedStates
                self.assertEqual(
                    detect_system_language(),
                    Language.CHINESE_SIMPLIFIED,
                )

    def test_non_macos_falls_back_to_locale_when_ui_languages_empty(self):
        with patch("sys.platform", "win32"):
            with patch("PySide6.QtCore.QLocale.system") as mock_system:
                locale = mock_system.return_value
                locale.uiLanguages.return_value = []
                locale.name.return_value = "ja_JP"
                locale.language.return_value = QLocale.Language.Japanese
                locale.country.return_value = QLocale.Country.Japan
                self.assertEqual(detect_system_language(), Language.JAPANESE)


if __name__ == "__main__":
    unittest.main()
