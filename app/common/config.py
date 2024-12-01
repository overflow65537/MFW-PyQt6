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

    # 文件地址
    emu_path = ConfigItem("Path", "emu_path", "")
    emu_wait_time = ConfigItem("Path", "emu_wati_time", "10")
    exe_path = ConfigItem("Path", "exe_path", "")
    exe_parameter = ConfigItem("Path", "exe_parameter", "")
    exe_wait_time = ConfigItem("Path", "exe_wait_time", "10")
    run_before_start = ConfigItem("Path", "run_before_start", "")
    run_after_finish = ConfigItem("Path", "run_after_finish", "")

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
    Notice_Webhook = ConfigItem(
        "Notice",
        "Webhook",
        {
            "DingTalk": {"status": False, "url": "", "secret": ""},
            "Lark": {"status": False, "url": "", "secret": ""},
        },
    )
    Notice_Qmsg = ConfigItem(
        "Notice",
        "Qmsg",
        {"status": False, "sever": "", "key": "", "uesr_qq": "", "robot_qq": ""},
    )
    Notice_SMTP = ConfigItem(
        "Notice",
        "SMTP",
        {
            "status": False,
            "sever_address": "",
            "sever_port": 0,
            "uesr_name": "",
            "password": "",
            "send_mail": "",
            "receive_mail": "",
        },
    )

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
