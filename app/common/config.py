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


class Language(Enum):
    """Language enumeration"""

    CHINESE_SIMPLIFIED = QLocale(QLocale.Language.Chinese, QLocale.Country.China)
    CHINESE_TRADITIONAL = QLocale(QLocale.Language.Chinese, QLocale.Country.HongKong)
    ENGLISH = QLocale(QLocale.Language.English)


class LanguageSerializer(ConfigSerializer):
    """Language serializer"""

    def serialize(self, value):
        return value.value.name()

    def deserialize(self, value: str) -> Language:
        return Language(QLocale(value))


def isWin11():
    return sys.platform == "win32" and sys.getwindowsversion().build >= 22000


class Config(QConfig):
    """Config of application"""

    # Mirror酱cdk
    Mcdk = ConfigItem("program", "cdk", "")
    is_change_cdk = ConfigItem("program", "is_change_cdk", True, BoolValidator())
    # 强制更新
    force_update = ConfigItem("program", "force_update", False, BoolValidator())
    # 标题
    title = ConfigItem("MainWindow", "Title", "MFW-PyQt6")

    # 资源存在
    resource_exist = ConfigItem("program", "resource_exist", False, BoolValidator())

    # 启动后直接运行
    run_after_startup = ConfigItem(
        "program", "run_after_startup", False, BoolValidator()
    )
    run_after_startup_arg = ConfigItem(
        "program", "run_after_startup_arg", False, BoolValidator()
    )

    # 保存截图
    save_draw = ConfigItem("program", "save_draw", False, BoolValidator())

    # MAA路径
    maa_config_name = ConfigItem("Maa", "Maa_config_name", "")
    maa_config_path = ConfigItem("Maa", "Maa_config_path", "")
    maa_resource_name = ConfigItem("Maa", "Maa_resource_name", "")
    maa_resource_path = ConfigItem("Maa", "Maa_resource_path", "")

    # 多配置
    maa_config_list = ConfigItem("Maa", "maa_config_list", {})
    maa_resource_list = ConfigItem("Maa", "maa_resource_list", {})
    # 自动更新资源
    auto_update_resource = ConfigItem(
        "Maa", "auto_update_resource", True, BoolValidator()
    )
    force_github = ConfigItem("Maa", "force_github", False, BoolValidator())
    click_update = ConfigItem("Maa", "click_update", False, BoolValidator())
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


REPO_URL = "https://github.com/overflow65537/MFW-PyQt6/"

cfg = Config()
cfg.themeMode.value = Theme.AUTO
qconfig.load("config/config.json", cfg)
