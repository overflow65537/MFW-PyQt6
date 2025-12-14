#   This file is part of MFW-ChainFlow Assistant.

#   MFW-ChainFlow Assistant is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published
#   by the Free Software Foundation, either version 3 of the License,
#   or (at your option) any later version.

#   MFW-ChainFlow Assistant is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty
#   of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See
#   the GNU General Public License for more details.

#   You should have received a copy of the GNU General Public License
#   along with MFW-ChainFlow Assistant. If not, see <https://www.gnu.org/licenses/>.

#   Contact: err.overflow@gmail.com
#   Copyright (C) 2024-2025  MFW-ChainFlow Assistant. All rights reserved.

"""
MFW-ChainFlow Assistant
MFW-ChainFlow Assistant 配置
作者:overflow65537
"""


import sys
from pathlib import Path
from enum import Enum

from PySide6.QtCore import QLocale
from qfluentwidgets import (
    qconfig,
    QConfig,
    ConfigItem,
    OptionsConfigItem,
    BoolValidator,
    OptionsValidator,
    RangeConfigItem,
    RangeValidator,
    Theme,
    ConfigSerializer,
)


class Language(Enum):
    """Language enumeration mapped to QLocale."""

    CHINESE_SIMPLIFIED = QLocale(QLocale.Language.Chinese, QLocale.Country.China)
    CHINESE_TRADITIONAL = QLocale(QLocale.Language.Chinese, QLocale.Country.HongKong)
    ENGLISH = QLocale(QLocale.Language.English)


def isWin11():
    return sys.platform == "win32" and sys.getwindowsversion().build >= 22000


def _detect_default_background_image() -> str:
    """查找默认背景图，依次尝试 ./background.jpg 与 ./background.png。"""
    for name in ("background.jpg", "background.png"):
        candidate = Path(name)
        if candidate.is_file():
            return str(candidate)
    return ""


class Config(QConfig):
    """Application configuration container."""

    class LanguageSerializer(ConfigSerializer):
        """序列化 Language 枚举，方便写入/读取 settting."""

        def serialize(self, value):
            return value.name

        def deserialize(self, value: str) -> Language:
            if isinstance(value, str):
                try:
                    return Language[value]
                except KeyError:
                    for lang in Language:
                        # 兼容旧版用 QLocale.name() 保存的值
                        if lang.value.name() == value or lang.name == value:
                            return lang
            return Language.CHINESE_SIMPLIFIED

    class UpdateChannel(Enum):
        """Update channel options."""

        ALPHA = 0
        BETA = 1
        STABLE = 2

    _update_channel_validator = OptionsValidator([item.value for item in UpdateChannel])

    # ===== 通用设置 =====
    proxy = ConfigItem("General", "proxy", 0)
    http_proxy = ConfigItem("General", "http_proxy", "")
    socks5_proxy = ConfigItem("General", "socks5_proxy", "")

    Mcdk = ConfigItem("General", "cdk", "")

    run_after_startup = ConfigItem(
        "General", "run_after_startup", False, BoolValidator()
    )
    auto_minimize_on_startup = ConfigItem(
        "General", "auto_minimize_on_startup", False, BoolValidator()
    )
    run_after_startup_arg = ConfigItem(
        "General", "run_after_startup_arg", False, BoolValidator()
    )
    multi_resource_adaptation = ConfigItem(
        "Compatibility", "multi_resource_adaptation", False, BoolValidator()
    )
    save_screenshot = ConfigItem(
        "Compatibility", "save_screenshot", False, BoolValidator()
    )

    announcement = ConfigItem("General", "announcement", "")

    auto_update = ConfigItem("Update", "auto_update", True, BoolValidator())
    force_github = ConfigItem("Update", "force_github", False, BoolValidator())
    github_api_key = ConfigItem("Update", "github_api_key", "")

    resource_update_channel = OptionsConfigItem(
        "Update",
        "resource_update_channel",
        UpdateChannel.STABLE.value,
        _update_channel_validator,
    )

    # ===== 任务设置 =====
    task_timeout_enable = ConfigItem("Task", "task_timeout_enable", True)  # 是否开启任务超时设置
    task_timeout = ConfigItem("Task", "task_timeout", 600)  # 默认600秒

    # 任务超时后动作
    class TaskTimeoutAction(Enum):
        """Task timeout action options."""

        NOTIFY_ONLY = 0  # 仅通知
        RESTART_AND_NOTIFY = 1  # 重启并通知

    _task_timeout_action_validator = OptionsValidator([item.value for item in TaskTimeoutAction])
    
    task_timeout_action = OptionsConfigItem(
        "Task",
        "task_timeout_action",
        TaskTimeoutAction.NOTIFY_ONLY.value,
        _task_timeout_action_validator,
    )

    # ===== 通知 =====
    Notice_DingTalk_status = ConfigItem("Notice", "DingTalk_status", False)
    Notice_DingTalk_url = ConfigItem("Notice", "DingTalk_url", "")
    Notice_DingTalk_secret = ConfigItem("Notice", "DingTalk_secret", "")

    Notice_Lark_status = ConfigItem("Notice", "Lark_status", False)
    Notice_Lark_url = ConfigItem("Notice", "Lark_url", "")
    Notice_Lark_secret = ConfigItem("Notice", "Lark_secret", "")

    Notice_Qmsg_status = ConfigItem("Notice", "Qmsg_status", False)
    Notice_Qmsg_sever = ConfigItem("Notice", "Qmsg_sever", "")
    Notice_Qmsg_key = ConfigItem("Notice", "Qmsg_key", "")
    Notice_Qmsg_user_qq = ConfigItem("Notice", "Qmsg_uesr_qq", "")
    Notice_Qmsg_robot_qq = ConfigItem("Notice", "Qmsg_robot_qq", "")

    Notice_SMTP_status = ConfigItem("Notice", "SMTP_status", False)
    Notice_SMTP_sever_address = ConfigItem("Notice", "SMTP_sever_address", "")
    Notice_SMTP_sever_port = ConfigItem("Notice", "SMTP_sever_port", "25")
    Notice_SMTP_used_ssl = ConfigItem("Notice", "SMTP_used_ssl", False)
    Notice_SMTP_user_name = ConfigItem("Notice", "SMTP_uesr_name", "")
    Notice_SMTP_password = ConfigItem("Notice", "SMTP_password", "")
    Notice_SMTP_send_mail = ConfigItem("Notice", "SMTP_send_mail", "")
    Notice_SMTP_receive_mail = ConfigItem("Notice", "SMTP_receive_mail", "")

    Notice_WxPusher_status = ConfigItem("Notice", "WxPush_status", False)
    Notice_WxPusher_SPT_token = ConfigItem("Notice", "WxPusher_SPT_token", "")

    Notice_QYWX_status = ConfigItem("Notice", "QYWX_status", False)
    Notice_QYWX_key = ConfigItem("Notice", "QYWX_key", "")

    when_start_up = ConfigItem("Notice", "when_start_up", False)
    when_connect_failed = ConfigItem("Notice", "when_connect_failed", False)
    when_connect_success = ConfigItem("Notice", "when_connect_success", False)
    when_post_task = ConfigItem("Notice", "when_post_task", False)
    when_task_failed = ConfigItem("Notice", "when_task_failed", True)
    when_task_finished = ConfigItem("Notice", "when_task_finished", True)

    # ===== 主窗口 =====
    micaEnabled = ConfigItem("MainWindow", "MicaEnabled", isWin11(), BoolValidator())

    dpiScale = OptionsConfigItem(
        "MainWindow",
        "DpiScale",
        "Auto",
        OptionsValidator([1, 1.25, 1.5, 1.75, 2, "Auto"]),
        restart=True,
    )

    language = OptionsConfigItem(
        "MainWindow",
        "Language",
        Language.CHINESE_SIMPLIFIED,  # 默认值（后续会被自动检测覆盖）
        OptionsValidator(Language),
        LanguageSerializer(),
        restart=True,
    )

    language_auto_detected = ConfigItem(
        "MainWindow", "LanguageAutoDetected", False, BoolValidator()
    )

    remember_window_geometry = ConfigItem(
        "MainWindow", "remember_window_geometry", False, BoolValidator()
    )
    last_window_geometry = ConfigItem("MainWindow", "LastWindowGeometry", "")

    start_task_shortcut = ConfigItem("Shortcuts", "start_task_shortcut", "Ctrl+`")
    stop_task_shortcut = ConfigItem("Shortcuts", "stop_task_shortcut", "Alt+`")

    show_advanced_startup_options = ConfigItem(
        "Personalization",
        "show_advanced_startup_options",
        False,
        BoolValidator(),
    )

    # ===== 背景 =====
    _default_background = _detect_default_background_image()
    background_image_path = ConfigItem(
        "Personalization", "background_image_path", _default_background
    )
    background_image_opacity = RangeConfigItem(
        "Personalization", "background_image_opacity", 80, RangeValidator(0, 100)
    )

    # ===== 材质 & 通用界面 =====
    blurRadius = RangeConfigItem(
        "Material", "AcrylicBlurRadius", 15, RangeValidator(0, 40)
    )

    # ===== 软件更新 =====
    latest_update_version = ConfigItem("Update", "LatestUpdateVersion", "")
    cdk_expired_time = ConfigItem("Update", "CdkExpiredTime", -1)

    # dev
    enable_test_interface_page = ConfigItem(
        "Dev", "enable_test_interface_page", False, BoolValidator()
    )


cfg = Config()
cfg.themeMode.value = Theme.AUTO
qconfig.load("config/config.json", cfg)


def detect_system_language() -> Language:
    """检测系统语言并返回对应的 Language 枚举

    Returns:
        Language: 根据系统语言返回对应枚举，默认简体中文
    """
    system_locale = QLocale.system()
    language = system_locale.language()
    country = system_locale.country()

    # 中文判断
    if language == QLocale.Language.Chinese:
        # 繁体
        if country in (QLocale.Country.HongKong,):
            return Language.CHINESE_TRADITIONAL
        # 简体
        return Language.CHINESE_SIMPLIFIED

    # 其他语言默认英文
    else:
        return Language.ENGLISH


def init_language_on_first_run():
    """初次运行时自动检测并设置系统语言

    仅在未设置过语言时执行（通过 language_auto_detected 标记判断）
    """
    if not cfg.get(cfg.language_auto_detected):
        detected_lang = detect_system_language()
        cfg.set(cfg.language, detected_lang)
        cfg.set(cfg.language_auto_detected, True)
        from app.utils.logger import logger

        logger.info(f"首次启动，自动检测系统语言: {detected_lang}")
    else:
        from app.utils.logger import logger

        logger.debug("已设置语言偏好，跳过自动检测")
