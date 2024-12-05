import sys
from enum import Enum

from PyQt6.QtCore import QLocale
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
    __version__,
)
import os


class Language(Enum):
    """Language enumeration"""

    CHINESE_SIMPLIFIED = QLocale(QLocale.Language.Chinese, QLocale.Country.China)
    CHINESE_TRADITIONAL = QLocale(QLocale.Language.Chinese, QLocale.Country.HongKong)
    ENGLISH = QLocale(QLocale.Language.English)


class LanguageSerializer(ConfigSerializer):
    """Language serializer"""

    def serialize(self, language):
        return language.value.name()

    def deserialize(self, value: str):
        return Language(QLocale(value))


def isWin11():
    return sys.platform == "win32" and sys.getwindowsversion().build >= 22000


class Config(QConfig):
    """Config of application"""

    # 资源存在
    resource_exist = ConfigItem(
        "resource_exist", "resource_exist", False, BoolValidator()
    )

    # MAA路径
    maa_config_name = ConfigItem("Main", "Maa_config_name", "")
    maa_config_path = ConfigItem("Main", "Maa_config_path", "")

    maa_resource_name = ConfigItem("Main", "Maa_resource_name", "")
    maa_resource_path = ConfigItem("Main", "Maa_resource_path", "")

    # 多配置
    maa_config_list = ConfigItem(
        "config_manager",
        "maa_config_list",
        {},
    )
    maa_resource_list = ConfigItem(
        "config_manager",
        "maa_resource_list",
        {},
    )

    # 外部通知
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
    Notice_SMTP_user_name = ConfigItem("Notice", "SMTP_uesr_name", "")
    Notice_SMTP_password = ConfigItem("Notice", "SMTP_password", "")
    Notice_SMTP_send_mail = ConfigItem("Notice", "SMTP_send_mail", "")
    Notice_SMTP_receive_mail = ConfigItem("Notice", "SMTP_receive_mail", "")

    Notice_WxPusher_status = ConfigItem("Notice", "WxPush_status", False)
    Notice_WxPusher_SPT_token = ConfigItem("Notice", "WxPusher_SPT_token", "")

    # main window
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
        Language.CHINESE_SIMPLIFIED,
        OptionsValidator(Language),
        LanguageSerializer(),
        restart=True,
    )

    # Material
    blurRadius = RangeConfigItem(
        "Material", "AcrylicBlurRadius", 15, RangeValidator(0, 40)
    )

    # software update
    checkUpdateAtStartUp = ConfigItem(
        "Update", "CheckUpdateAtStartUp", True, BoolValidator()
    )


REPO_URL = "https://github.com/overflow65537/PYQT-MAA/"

cfg = Config()
cfg.themeMode.value = Theme.AUTO
qconfig.load("config/config.json", cfg)
