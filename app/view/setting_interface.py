from qfluentwidgets import (
    SettingCardGroup,
    SwitchSettingCard,
    OptionsSettingCard,
    ScrollArea,
    ComboBoxSettingCard,
    ExpandLayout,
    CustomColorSettingCard,
    setTheme,
    setThemeColor,
)
from qfluentwidgets import FluentIcon as FIF
from qfluentwidgets import InfoBar
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QWidget, QLabel, QApplication


from ..common.config import cfg, REPO_URL, isWin11
from ..common.signal_bus import signalBus
from ..common.style_sheet import StyleSheet
from ..components.line_edit_card import LineEditCard
from ..components.notic_setting_card import NoticeButtonSettingCard
from ..utils.update import Update, UpdateSelf
from ..utils.tool import Save_Config, for_config_get_url, decrypt, encrypt
from ..utils.logger import logger
from ..common.maa_config_data import maa_config_data
from ..components.doble_button_setting_card import DoubleButtonSettingCard
from ..components.show_download import ShowDownload

import subprocess
import os
import sys


class SettingInterface(ScrollArea):
    """设置界面，用于配置应用程序设置。"""

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.Setting_scroll_widget = QWidget()
        self.Setting_expand_Layout = ExpandLayout(self.Setting_scroll_widget)
        signalBus.resource_exist.connect(self.resource_exist)
        # 初始化界面

        self.init_ui()
        self.__connectSignalToSlot()
        if not cfg.get(cfg.resource_exist):
            self.enable_widgets(False)
        self.update_exist()

    def update_exist(self):
        """更新文件是否存在"""
        if os.path.exists(os.path.join(os.getcwd(), "update.zip")):
            logger.info("存在更新文件")
            self.aboutCard.button2.setText(self.tr("Update Now"))
            self.aboutCard.button2.clicked.disconnect()
            self.aboutCard.button2.clicked.connect(self.update_self_start)

    def resource_exist(self, status: bool):
        if status:
            logger.info("收到信号,初始化界面并连接信号")
            self.init_info()
            self.enable_widgets(True)
            self.init_update_thread()
        else:
            logger.info("收到信号,清空界面并断开信号")
            self.enable_widgets(False)
            self.clear_content()
            self.init_update_thread()

    def init_ui(self):
        """初始化界面内容。"""
        # 设置标签
        self.setting_Label = QLabel(self.tr("Settings"), self)

        # 初始化设置
        self.initialize_start_settings()
        self.initialize_personalization_settings()
        self.initialize_notice_settings()
        self.initialize_advanced_settings()
        self.initialize_update_settings()
        self.initialize_about_settings()
        self.__initWidget()
        self.init_info()
        self.init_update_thread()

    def init_update_thread(self):
        if cfg.get(cfg.Mcdk) and maa_config_data.interface_config.get(
            "mirrorchyan_rid"
        ):
            self.MirrorCard.setContent(
                self.tr("Enter mirrorchyan CDK for stable update path")
            )
            logger.debug("使用镜像站更新")

        elif maa_config_data.interface_config.get("mirrorchyan_rid"):
            self.MirrorCard.setContent(
                self.tr("Enter mirrorchyan CDK for stable update path")
            )
            logger.debug("使用Github更新")
        else:
            self.MirrorCard.setContent(
                self.tr(
                    "Resource does not support Mirrorchyan, right-click about mirror to unlock input"
                )
            )
            self.MirrorCard.lineEdit.setEnabled(False)
            logger.debug("使用Github更新")
        self.Updatethread = Update(self)
        signalBus.update_download_stopped.connect(self.Updatethread.stop)
        self.update_self = UpdateSelf(self)
        signalBus.download_self_stopped.connect(self.update_self.stop)

    def init_info(self):
        """初始化控件信息。"""
        # 从配置中读取数据并填充到控件
        if maa_config_data.interface_config:
            self.project_name = maa_config_data.interface_config.get("name", "")
            self.project_version = maa_config_data.interface_config.get("version", "")
            self.project_url = maa_config_data.interface_config.get("url", "")

        else:
            self.project_name = ""
            self.project_version = ""
            self.project_url = ""


        self.updateCard.setContent(
            self.tr("Current")
            + " "
            + self.project_name
            + " "
            + self.tr("version:")
            + " "
            + self.project_version,
        )

    def clear_content(self):
        # 清空输入框和设置内容
        cfg.set(cfg.save_draw, False)


        self.updateCard.setContent(
            self.tr("Current")
            + " "
            + self.project_name
            + " "
            + self.tr("version:")
            + " "
            + self.project_version,
        )

    def enable_widgets(self, enable: bool):
        """启用或禁用所有可交互控件。"""
        # 遍历所有子控件
        if enable:
            logger.info("启用所有可交互控件")
        else:
            logger.info("禁用所有可交互控件")
        for widget in self.Setting_scroll_widget.findChildren(QWidget):
            # 启用或禁用控件
            widget.setEnabled(enable)

    def initialize_start_settings(self):
        """初始化启动设置。"""


        self.start_Setting = SettingCardGroup(
            self.tr("Custom Startup"), self.Setting_scroll_widget
        )

        self.run_after_startup = SwitchSettingCard(
            FIF.SPEED_HIGH,
            self.tr("run after startup"),
            self.tr("Launch the task immediately after starting the GUI program"),
            configItem=cfg.run_after_startup,
            parent=self.start_Setting,
        )

        self.start_Setting.addSettingCard(self.run_after_startup)

    def initialize_personalization_settings(self):
        """初始化个性化设置。"""
        self.personalGroup = SettingCardGroup(
            self.tr("Personalization"), self.Setting_scroll_widget
        )

        self.micaCard = SwitchSettingCard(
            FIF.TRANSPARENT,
            self.tr("Mica Effect"),
            self.tr("Apply semi transparent to windows and surfaces"),
            cfg.micaEnabled,
            self.personalGroup,
        )
        self.themeCard = OptionsSettingCard(
            cfg.themeMode,
            FIF.BRUSH,
            self.tr("Application Theme"),
            self.tr("Change the appearance of your application"),
            texts=[self.tr("Light"), self.tr("Dark"), self.tr("Use system setting")],
            parent=self.personalGroup,
        )
        self.themeColorCard = CustomColorSettingCard(
            cfg.themeColor,
            FIF.PALETTE,
            self.tr("Theme Color"),
            self.tr("Change the theme color of your application"),
            self.personalGroup,
        )
        self.zoomCard = OptionsSettingCard(
            cfg.dpiScale,
            FIF.ZOOM,
            self.tr("Interface Zoom"),
            self.tr("Change the size of widgets and fonts"),
            texts=[
                "100%",
                "125%",
                "150%",
                "175%",
                "200%",
                self.tr("Use system setting"),
            ],
            parent=self.personalGroup,
        )
        self.languageCard = ComboBoxSettingCard(
            cfg.language,
            FIF.LANGUAGE,
            self.tr("Language"),
            self.tr("Set your preferred language for UI"),
            texts=["简体中文", "繁體中文", "English"],
            parent=self.personalGroup,
        )

        self.personalGroup.addSettingCard(self.micaCard)
        self.personalGroup.addSettingCard(self.themeCard)
        self.personalGroup.addSettingCard(self.themeColorCard)
        self.personalGroup.addSettingCard(self.zoomCard)
        self.personalGroup.addSettingCard(self.languageCard)

    def initialize_notice_settings(self):
        """初始化外部通知设置。"""
        self.noticeGroup = SettingCardGroup(self.tr("Notice"), self.Setting_scroll_widget)

        self.dingtalk_noticeTypeCard = NoticeButtonSettingCard(
            text=self.tr("Modify"),
            icon=FIF.SEND,
            title=self.tr("DingTalk"),
            notice_type="DingTalk",
            parent=self.noticeGroup,
        )

        self.lark_noticeTypeCard = NoticeButtonSettingCard(
            text=self.tr("Modify"),
            icon=FIF.SEND,
            title=self.tr("Lark"),
            notice_type="Lark",
            parent=self.noticeGroup,
        )

        self.SMTP_noticeTypeCard = NoticeButtonSettingCard(
            text=self.tr("Modify"),
            icon=FIF.SEND,
            title=self.tr("SMTP"),
            notice_type="SMTP",
            parent=self.noticeGroup,
        )

        self.WxPusher_noticeTypeCard = NoticeButtonSettingCard(
            text=self.tr("Modify"),
            icon=FIF.SEND,
            title=self.tr("WxPusher"),
            notice_type="WxPusher",
            parent=self.noticeGroup,
        )

        self.QYWX_noticeTypeCard = NoticeButtonSettingCard(
            text=self.tr("Modify"),
            icon=FIF.SEND,
            title=self.tr("QYWX"),
            notice_type="QYWX",
            parent=self.noticeGroup,
        )

        self.noticeGroup.addSettingCard(self.dingtalk_noticeTypeCard)
        self.noticeGroup.addSettingCard(self.lark_noticeTypeCard)
        self.noticeGroup.addSettingCard(self.SMTP_noticeTypeCard)
        self.noticeGroup.addSettingCard(self.WxPusher_noticeTypeCard)
        self.noticeGroup.addSettingCard(self.QYWX_noticeTypeCard)

    def initialize_advanced_settings(self):
        """初始化高级设置。"""
        self.advancedGroup = SettingCardGroup(self.tr("Advanced"), self.Setting_scroll_widget)
        # 设置开发者配置
        cfg.set(cfg.recording, False)
        cfg.set(cfg.save_draw, False)
        cfg.set(cfg.show_hit_draw, False)

        self.Show_Agent_CMD_Card = SwitchSettingCard(
            FIF.APPLICATION,
            self.tr("Show Agent CMD"),
            self.tr("Show the agent command line"),
            configItem=cfg.show_agent_cmd,
            parent=self.advancedGroup,
        )
        self.RecordingCard = SwitchSettingCard(
            FIF.VIDEO,
            self.tr("Recording"),
            self.tr(
                "The video recording and saving function saves all screenshots and operation data during the runtime. You can use the DbgController for reproduction and debugging."
            ),
            configItem=cfg.recording,
            parent=self.advancedGroup,
        )

        self.SaveDrawCard = SwitchSettingCard(
            FIF.PHOTO,
            self.tr("Save Draw"),
            self.tr(
                "Saving the visualization results of image recognition will save all the drawn diagrams of the visualization results of image recognition during the runtime."
            ),
            configItem=cfg.save_draw,
            parent=self.advancedGroup,
        )
        self.show_hit_draw = SwitchSettingCard(
            FIF.PHOTO,
            self.tr("Show Hit Draw"),
            self.tr(
                "Show the node hit pop-up window. A pop-up window will appear to display the recognition results every time the recognition is successful."
            ),
            configItem=cfg.show_hit_draw,
            parent=self.advancedGroup,
        )

        self.advancedGroup.addSettingCard(self.Show_Agent_CMD_Card)
        self.advancedGroup.addSettingCard(self.RecordingCard)
        self.advancedGroup.addSettingCard(self.SaveDrawCard)
        self.advancedGroup.addSettingCard(self.show_hit_draw)

        # 更改标题栏至调试模式
        self.RecordingCard.switchButton.checkedChanged.connect(
            lambda: signalBus.title_changed.emit()
        )
        self.SaveDrawCard.switchButton.checkedChanged.connect(
            lambda: signalBus.title_changed.emit()
        )
        self.show_hit_draw.switchButton.checkedChanged.connect(
            lambda: signalBus.title_changed.emit()
        )

    def initialize_update_settings(self):
        """初始化更新设置。"""
        with open("k.ey", "rb") as key_file:
            key = key_file.read()
            holddertext = decrypt(cfg.get(cfg.Mcdk), key)
        self.updateGroup = SettingCardGroup(self.tr("Update"), self.Setting_scroll_widget)
        self.MirrorCard = LineEditCard(
            icon=FIF.APPLICATION,
            title=self.tr("mirrorchyan CDK"),
            content=self.tr("Enter mirrorchyan CDK for stable update path"),
            is_passwork=True,
            num_only=False,
            holderText=holddertext,
            button=True,
            button_type="primary",
            button_text=self.tr("About Mirror"),
            parent=self.updateGroup,
        )
        self.auto_update = SwitchSettingCard(
            FIF.UPDATE,
            self.tr("Auto Update resource"),
            self.tr("Automatically update resources on every startup"),
            configItem=cfg.auto_update_resource,
            parent=self.updateGroup,
        )

        self.force_github = SwitchSettingCard(
            FIF.UPDATE,
            self.tr("Force use GitHub"),
            self.tr("Force use GitHub for resource update"),
            configItem=cfg.force_github,
            parent=self.updateGroup,
        )

        self.updateGroup.addSettingCard(self.MirrorCard)
        self.updateGroup.addSettingCard(self.auto_update)
        self.updateGroup.addSettingCard(self.force_github)

    def initialize_about_settings(self):
        """初始化关于设置。"""
        self.aboutGroup = SettingCardGroup(self.tr("About"), self.Setting_scroll_widget)
        with open(
            os.path.join(os.getcwd(), "config", "version.txt"), "r", encoding="utf-8"
        ) as f:
            try:
                MFW_Version = f.read().split()[2]
            except:
                MFW_Version = "Unknown"
        MFW_update_channel = cfg.get(cfg.MFW_update_channel)
        resource_update_channel = cfg.get(cfg.resource_update_channel)
        

        self.updateCard = DoubleButtonSettingCard(
            text2=self.tr("Check for updates"),
            text=self.tr("Submit Feedback"),
            icon=FIF.UPDATE,
            title=self.tr("Check for updates"),
            configItem=cfg.resource_update_channel,
            content=self.tr("Current") + " " + " " + self.tr("version:") + " ",
            parent=self.aboutGroup,
        )
        self.aboutCard = DoubleButtonSettingCard(
            text=self.tr("About"),
            text2=self.tr("Check for updates"),
            icon=FIF.INFO,
            title="MFW-PyQt6 " + MFW_Version,
            configItem=cfg.MFW_update_channel,
            content=self.tr(
                "MFW-PyQt6 is open source under the GPLv3 license. Visit the project URL for more information."
            ),
            parent=self.aboutGroup,
        )
        self.aboutCard.combobox.setCurrentIndex(MFW_update_channel)
        self.updateCard.combobox.setCurrentIndex(resource_update_channel)

        self.aboutGroup.addSettingCard(self.updateCard)
        self.aboutGroup.addSettingCard(self.aboutCard)


    def update_check(self):
        self.Updatethread.start()
        self.updateCard.button2.setEnabled(False)
        self.updateCard.button2.setText(self.tr("Checking for updates..."))
        signalBus.lock_res_changed.emit(True)

    def on_update_finished(self, data_dict: dict):
        """更新检查完成的回调函数。"""
        logger.debug(f"更新检查完成: {data_dict}")
        if data_dict["status"] == "success":
            self.project_version = maa_config_data.interface_config.get("version", "")
            self.updateCard.setContent(
                self.tr("Current")
                + " "
                + self.project_name
                + " "
                + self.tr("version:")
                + " "
                + self.project_version,
            )
        elif "info" in data_dict["status"]:
            return

        self.updateCard.button2.setText(self.tr("Check for updates"))
        self.updateCard.button2.setEnabled(True)
        signalBus.title_changed.emit()
        signalBus.lock_res_changed.emit(False)

    def __initWidget(self):
        self.resize(1000, 800)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setViewportMargins(0, 80, 0, 20)
        self.setWidget(self.Setting_scroll_widget)
        self.setWidgetResizable(True)
        self.setObjectName("settingInterface")

        # 初始化样式表
        self.Setting_scroll_widget.setObjectName("scrollWidget")
        self.setting_Label.setObjectName("settingLabel")
        StyleSheet.SETTING_INTERFACE.apply(self)

        self.micaCard.setEnabled(isWin11())

        # 初始化布局
        self.__initLayout()

    def __initLayout(self):
        """初始化设置卡片的布局。"""
        self.setting_Label.move(36, 30)

        # 将卡片组添加到布局中
        self.Setting_expand_Layout.setSpacing(28)
        self.Setting_expand_Layout.setContentsMargins(36, 10, 36, 0)
        self.Setting_expand_Layout.addWidget(self.start_Setting)
        self.Setting_expand_Layout.addWidget(self.personalGroup)
        self.Setting_expand_Layout.addWidget(self.noticeGroup)
        self.Setting_expand_Layout.addWidget(self.advancedGroup)
        self.Setting_expand_Layout.addWidget(self.updateGroup)
        self.Setting_expand_Layout.addWidget(self.aboutGroup)

    def __showRestartTooltip(self):
        """显示重启提示。"""
        InfoBar.success(
            self.tr("Updated successfully"),
            self.tr("Configuration takes effect after restart"),
            duration=1500,
            parent=self,
        )

    def __connectSignalToSlot(self):
        """连接信号到对应的槽函数。"""
        signalBus.update_download_finished.connect(self.on_update_finished)
        cfg.appRestartSig.connect(self.__showRestartTooltip)
        signalBus.auto_update.connect(self.update_check)
        signalBus.download_self_finished.connect(self.update_self_finished)

        # 连接启动信号
        self.run_after_startup.checkedChanged.connect(self._onRunAfterStartupCardChange)


        # 连接个性化信号
        cfg.themeChanged.connect(setTheme)
        self.themeColorCard.colorChanged.connect(lambda c: setThemeColor(c))
        self.micaCard.checkedChanged.connect(signalBus.micaEnableChanged)
        # 连接更新信号
        self.MirrorCard.button.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl("https://mirrorchyan.com/"))
        )
        self.MirrorCard.lineEdit.textChanged.connect(self._onMirrorCardChange)

        # 连接关于信号
        self.updateCard.clicked2.connect(self.update_check)
        self.updateCard.clicked2.connect(lambda: cfg.set(cfg.click_update, True))
        self.updateCard.clicked.connect(
            lambda: QDesktopServices.openUrl(
                QUrl(for_config_get_url(self.project_url, "issue"))
            )
        )
        self.aboutCard.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(REPO_URL)))
        self.aboutCard.clicked2.connect(self.update_self_func)

    def update_self_func(self):
        """更新程序。"""
        self.update_self.start()
        self.aboutCard.button2.setEnabled(False)
        self.aboutCard.button2.setText(self.tr("Updating..."))
        w = ShowDownload(self)
        w.show()

    def update_self_finished(self, status: dict):
        """更新程序停止。"""
        button = self.aboutCard.button2

        status_type = status["status"]
        if status_type in ["no_need", "failed", "stoped"]:
            button.setText(self.tr("Check for updates"))
            button.setEnabled(True)
        elif status_type == "failed_info":
            return
        elif status_type == "success":
            button.setText(self.tr("Update Now"))
            button.clicked.disconnect()
            button.clicked.connect(self.update_self_start)
            button.setEnabled(True)

    def update_self_start(self):
        """开始更新程序。"""
        # 重命名更新程序防止占用
        if sys.platform.startswith("win32"):
            self._rename_updater("MFWUpdater.exe", "MFWUpdater1.exe")
        elif sys.platform.startswith("darwin"):
            self._rename_updater("MFWUpdater", "MFWUpdater1")
        elif sys.platform.startswith("linux"):
            self._rename_updater("MFWupdater.bin", "MFWupdater1.bin")

        # 启动更新程序
        self._start_updater()

        QApplication.quit()

    def _rename_updater(self, old_name, new_name):
        """重命名更新程序。"""
        if os.path.exists(old_name) and os.path.exists(new_name):
            os.remove(new_name)
        if os.path.exists(old_name):
            os.rename(old_name, new_name)

    def _start_updater(self):
        """启动更新程序。"""
        if sys.platform.startswith("win32"):
            subprocess.Popen(["./MFWUpdater1.exe"])
        elif sys.platform.startswith("linux"):
            subprocess.Popen(["./MFWupdater1.bin"])
        elif sys.platform.startswith("darwin"):
            subprocess.Popen(["./MFWUpdater1"])
        else:
            raise NotImplementedError("Unsupported platform")
        with open(
            os.path.join(os.getcwd(), "config", "version.txt"), "r", encoding="utf-8"
        ) as f:
            version_data = f.read().split()
        version_data[2] = version_data[3]
        with open(
            os.path.join(os.getcwd(), "config", "version.txt"), "w", encoding="utf-8"
        ) as f:
            f.write(" ".join(version_data))

        logger.info("正在启动更新程序")

    def _update_config(self, card: LineEditCard, config_key: str):
        if maa_config_data.config_path == "":
            return
        value = card.lineEdit.text()
        maa_config_data.config[config_key] = value
        Save_Config(maa_config_data.config_path, maa_config_data.config)

    def _onRunAfterStartupCardChange(self):
        """根据输入更新启动前运行的程序脚本路径。"""
        print(self.run_after_startup.isChecked())
        cfg.set(cfg.run_after_startup, self.run_after_startup.isChecked())

    def _onMirrorCardChange(self):
        """根据输入更新镜像地址。"""
        with open("k.ey", "rb") as file:
            key = file.read()
            Mcdk = encrypt(self.MirrorCard.lineEdit.text(), key)
        cfg.set(cfg.Mcdk, str(Mcdk))
        cfg.set(cfg.is_change_cdk, True)