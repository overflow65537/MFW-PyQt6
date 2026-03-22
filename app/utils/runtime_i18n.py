"""
运行时 i18n 工具。

用于在应用启动和语言热切换时，统一安装/替换 Qt 翻译器，
避免重复代码并确保旧翻译器被正确移除。
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTranslator
from qfluentwidgets import FluentTranslator

from app.common.config import Language
from app.utils.logger import logger
from app.utils.ts_translator import TsTranslator


_RUNTIME_TRANSLATORS_ATTR = "_mfw_runtime_translators"


def map_locale_to_code(locale: Language) -> str:
    """将 Language 枚举映射到 interface 语言码。"""
    if locale == Language.CHINESE_TRADITIONAL:
        return "zh_hk"
    if locale == Language.ENGLISH:
        return "en_us"
    if locale == Language.JAPANESE:
        return "ja_jp"
    return "zh_cn"


def _remove_previous_translators(app: QApplication) -> None:
    """移除上一次安装的运行时翻译器。"""
    previous = getattr(app, _RUNTIME_TRANSLATORS_ATTR, [])
    if not isinstance(previous, list):
        previous = []

    for translator in previous:
        try:
            app.removeTranslator(translator)
        except Exception as exc:
            logger.debug("移除旧翻译器失败（已忽略）: %s", exc)


def apply_runtime_translations(app: QApplication, locale: Language) -> str:
    """
    根据目标语言安装 Qt 翻译器（支持运行时重复调用）。

    Returns:
        str: 对应的语言码（zh_cn / zh_hk / en_us / ja_jp）
    """
    _remove_previous_translators(app)

    language_code = map_locale_to_code(locale)
    translators = [FluentTranslator(locale.value)]

    gallery_translator = QTranslator()
    fallback_ts_translator = TsTranslator()

    mapping = {
        "zh_cn": ("i18n.zh_CN.qm", "i18n.zh_CN.ts", "简体中文"),
        "zh_hk": ("i18n.zh_HK.qm", "i18n.zh_HK.ts", "繁体中文"),
        "ja_jp": ("i18n.ja_JP.qm", "i18n.ja_JP.ts", "日语"),
    }

    if language_code in mapping:
        qm_name, ts_name, log_name = mapping[language_code]
        qm_path = Path(".") / "app" / "i18n" / qm_name
        ts_path = Path(".") / "app" / "i18n" / ts_name

        if gallery_translator.load(str(qm_path)):
            translators.append(gallery_translator)
            logger.info("加载%s翻译(qm): %s", log_name, qm_path)
        elif fallback_ts_translator.load_ts(ts_path):
            translators.append(fallback_ts_translator)
            logger.info("加载%s翻译(ts回退): %s", log_name, ts_path)
        else:
            logger.warning("未找到可用的%s翻译文件: %s / %s", log_name, qm_path, ts_path)
    else:
        logger.info("加载英文翻译")

    for translator in translators:
        app.installTranslator(translator)

    setattr(app, _RUNTIME_TRANSLATORS_ATTR, translators)
    return language_code
