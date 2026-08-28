import unittest
from unittest.mock import patch

from PySide6.QtCore import QLocale

from app.common.config import Language, _language_from_ui_tag, detect_system_language


class LanguageFromUiTagTests(unittest.TestCase):
    def test_zh_hans_is_simplified(self):
        self.assertEqual(_language_from_ui_tag("zh-Hans-CN"), Language.CHINESE_SIMPLIFIED)

    def test_zh_tw_is_traditional(self):
        self.assertEqual(_language_from_ui_tag("zh-Hant-TW"), Language.CHINESE_TRADITIONAL)

    def test_ja(self):
        self.assertEqual(_language_from_ui_tag("ja-JP"), Language.JAPANESE)

    def test_en(self):
        self.assertEqual(_language_from_ui_tag("en-US"), Language.ENGLISH)


class DetectSystemLanguageTests(unittest.TestCase):
    def test_prefers_ui_languages_over_english_locale(self):
        with patch("PySide6.QtCore.QLocale.system") as mock_system:
            locale = mock_system.return_value
            locale.uiLanguages.return_value = ["zh-Hans-CN", "en-US"]
            locale.language.return_value = QLocale.Language.English
            locale.country.return_value = QLocale.Country.UnitedStates
            self.assertEqual(
                detect_system_language(),
                Language.CHINESE_SIMPLIFIED,
            )

    def test_falls_back_to_locale_when_ui_languages_empty(self):
        with patch("PySide6.QtCore.QLocale.system") as mock_system:
            locale = mock_system.return_value
            locale.uiLanguages.return_value = []
            locale.language.return_value = QLocale.Language.Japanese
            locale.country.return_value = QLocale.Country.Japan
            self.assertEqual(detect_system_language(), Language.JAPANESE)


if __name__ == "__main__":
    unittest.main()
