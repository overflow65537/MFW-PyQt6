from __future__ import annotations

from typing import Any

from qfluentwidgets import setTheme, setThemeColor

from app.common.config import cfg
from app.utils.logger import logger
from app.view.main_window.v5_style import build_v5_stylesheet


def apply_theme_from_config() -> None:
    """根据当前配置应用 qfluentwidgets 全局主题与主题色。"""
    theme_mode = cfg.get(cfg.themeMode)
    if theme_mode:
        try:
            setTheme(theme_mode)
        except Exception as exc:
            logger.warning("应用主题模式失败: %s", exc)

    theme_color_item = getattr(cfg, "themeColor", None)
    if theme_color_item:
        theme_color = cfg.get(theme_color_item)
        if theme_color:
            try:
                setThemeColor(theme_color)
            except Exception as exc:
                logger.warning("应用主题色失败: %s", exc)


def bind_setting_interface_theme(setting_interface: Any) -> None:
    """绑定设置页中的主题相关控件到 qfluentwidgets 全局主题。"""
    cfg.themeChanged.connect(setTheme)
    setting_interface.themeColorCard.colorChanged.connect(setThemeColor)


def apply_v5_window_style(window: Any) -> None:
    """应用 V5 页面结构样式，不覆盖 qfluentwidgets 的全局主题配色。"""
    window.setObjectName("V5MainWindow")
    try:
        window.navigationInterface.setObjectName("v5Navigation")
    except Exception:
        pass
    try:
        window.stackedWidget.setObjectName("v5StackedWidget")
    except Exception:
        pass
    window.setStyleSheet(build_v5_stylesheet())