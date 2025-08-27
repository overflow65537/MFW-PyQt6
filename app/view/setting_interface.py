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
MFW-ChainFlow Assistant 设置界面
作者:overflow65537
"""

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
    PrimaryPushSettingCard,
)
from qfluentwidgets import FluentIcon as FIF
from qfluentwidgets import InfoBar
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QWidget, QLabel, QApplication


from ..common.config import cfg, REPO_URL, isWin11
from ..common.signal_bus import signalBus
from ..common.style_sheet import StyleSheet
from ..utils.widget import (
    LineEditCard,
    DoubleButtonSettingCard,
    ProxySettingCard,
)
from ..utils.update import Update, UpdateSelf
from ..utils.tool import Save_Config, for_config_get_url, decrypt, encrypt
from ..utils.logger import logger
from ..common.resource_config import maa_config_data
from ..common.__version__ import __version__

import subprocess
import os
import sys
import zipfile


class SettingInterface(ScrollArea):
    """
    设置界面，用于配置应用程序设置。
    """

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
        """
        更新文件是否存在
        """
        if os.path.exists(os.path.join(os.getcwd(), "update.zip")):
            logger.info("存在更新文件")
            self.aboutCard.button2.setText(self.tr("Update Now"))
            self.aboutCard.button2.clicked.disconnect()
            self.aboutCard.button2.clicked.connect(self.update_self_start)

    def resource_exist(self, status: bool):
        """
        资源是否存在的槽函数。
        """
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
        """
        初始化界面内容。
        """
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
        """
        初始化更新线程
        """
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
        self.Updatethread.setObjectName("UpdateThread")
        signalBus.update_download_stopped.connect(self.Updatethread.stop)
        self.update_self = UpdateSelf(self)
        self.update_self.setObjectName("UpdateSelfThread")
        signalBus.download_self_stopped.connect(self.update_self.stop)

    def init_info(self):
        """
        初始化控件信息
        """
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
        """
        清空输入框和设置内容
        """
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
        """
        启用或禁用所有可交互控件。
        """
        # 遍历所有子控件
        if enable:
            logger.info("启用所有可交互控件")
        else:
            logger.info("禁用所有可交互控件")
        for widget in self.Setting_scroll_widget.findChildren(QWidget):
            # 启用或禁用控件
            widget.setEnabled(enable)

    def initialize_start_settings(self):
        """
        初始化启动设置。
        """

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
        self.never_show_notice = SwitchSettingCard(
            FIF.MEGAPHONE,
            self.tr("never show notice"),
            self.tr("Announcements will never pop up regardless of the situation"),
            configItem=cfg.hide_notice,
            parent=self.start_Setting,
        )

        self.start_Setting.addSettingCard(self.run_after_startup)
        self.start_Setting.addSettingCard(self.never_show_notice)

    def initialize_personalization_settings(self):
        """
        初始化个性化设置。
        """
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
        """
        初始化外部通知设置。
        """
        self.noticeGroup = SettingCardGroup(
            self.tr("Notice"), self.Setting_scroll_widget
        )
        if cfg.get(cfg.Notice_DingTalk_status):
            dingtalk_contene = self.tr("DingTalk Notification Enabled")
        else:
            dingtalk_contene = self.tr("DingTalk Notification Disabled")

        self.dingtalk_noticeTypeCard = PrimaryPushSettingCard(
            text=self.tr("Modify"),
            icon=FIF.SEND,
            title=self.tr("DingTalk"),
            content=dingtalk_contene,
            parent=self.noticeGroup,
        )
        if cfg.get(cfg.Notice_Lark_status):
            lark_contene = self.tr("Lark Notification Enabled")
        else:
            lark_contene = self.tr("Lark Notification Disabled")
        self.lark_noticeTypeCard = PrimaryPushSettingCard(
            text=self.tr("Modify"),
            icon=FIF.SEND,
            title=self.tr("Lark"),
            content=lark_contene,
            parent=self.noticeGroup,
        )
        if cfg.get(cfg.Notice_SMTP_status):
            SMTP_contene = self.tr("SMTP Notification Enabled")
        else:
            SMTP_contene = self.tr("SMTP Notification Disabled")
        self.SMTP_noticeTypeCard = PrimaryPushSettingCard(
            text=self.tr("Modify"),
            icon=FIF.SEND,
            title=self.tr("SMTP"),
            content=SMTP_contene,
            parent=self.noticeGroup,
        )
        if cfg.get(cfg.Notice_WxPusher_status):
            WxPusher_contene = self.tr("WxPusher Notification Enabled")
        else:
            WxPusher_contene = self.tr("WxPusher Notification Disabled")

        self.WxPusher_noticeTypeCard = PrimaryPushSettingCard(
            text=self.tr("Modify"),
            icon=FIF.SEND,
            title=self.tr("WxPusher"),
            content=WxPusher_contene,
            parent=self.noticeGroup,
        )
        if cfg.get(cfg.Notice_QYWX_status):
            QYWX_contene = self.tr("QYWX Notification Enabled")
        else:
            QYWX_contene = self.tr("QYWX Notification Disabled")

        self.QYWX_noticeTypeCard = PrimaryPushSettingCard(
            text=self.tr("Modify"),
            icon=FIF.SEND,
            title=self.tr("QYWX"),
            content=QYWX_contene,
            parent=self.noticeGroup,
        )

        self.send_settingCard = PrimaryPushSettingCard(
            text=self.tr("Modify"),
            icon=FIF.SEND,
            title=self.tr("Send Setting"),
            content=self.tr("Choose the timing to send notifications"),
            parent=self.noticeGroup,
        )

        self.noticeGroup.addSettingCard(self.dingtalk_noticeTypeCard)
        self.noticeGroup.addSettingCard(self.lark_noticeTypeCard)
        self.noticeGroup.addSettingCard(self.SMTP_noticeTypeCard)
        self.noticeGroup.addSettingCard(self.WxPusher_noticeTypeCard)
        self.noticeGroup.addSettingCard(self.QYWX_noticeTypeCard)
        self.noticeGroup.addSettingCard(self.send_settingCard)

    def initialize_advanced_settings(self):
        """初始化高级设置。"""
        self.advancedGroup = SettingCardGroup(
            self.tr("Advanced"), self.Setting_scroll_widget
        )
        # 设置开发者配置
        cfg.set(cfg.recording, False)
        cfg.set(cfg.save_draw, False)

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

        self.advancedGroup.addSettingCard(self.Show_Agent_CMD_Card)
        self.advancedGroup.addSettingCard(self.RecordingCard)
        self.advancedGroup.addSettingCard(self.SaveDrawCard)

        # 更改标题栏至调试模式
        self.RecordingCard.switchButton.checkedChanged.connect(
            lambda: signalBus.title_changed.emit()
        )
        self.SaveDrawCard.switchButton.checkedChanged.connect(
            lambda: signalBus.title_changed.emit()
        )

    def initialize_update_settings(self):
        """初始化更新设置。"""
        with open("k.ey", "rb") as key_file:
            key = key_file.read()
            holddertext = decrypt(cfg.get(cfg.Mcdk), key)
        self.updateGroup = SettingCardGroup(
            self.tr("Update"), self.Setting_scroll_widget
        )
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
        self.MFW_auto_update = SwitchSettingCard(
            FIF.UPDATE,
            self.tr("Auto Update MFW"),
            self.tr(
                "Automatically update MFW after opening the program. Not recommended, as it may cause the loss of the current running progress."
            ),
            configItem=cfg.auto_update_MFW,
            parent=self.updateGroup,
        )

        self.force_github = SwitchSettingCard(
            FIF.UPDATE,
            self.tr("Force use GitHub"),
            self.tr("Force use GitHub for resource update"),
            configItem=cfg.force_github,
            parent=self.updateGroup,
        )
        self.proxy = ProxySettingCard(
            FIF.GLOBE,
            self.tr("Use Proxy"),
            self.tr(
                "After filling in the proxy settings, all traffic except that to the Mirror will be proxied."
            ),
            parent=self.updateGroup,
        )

        combox_index = cfg.get(cfg.proxy)
        self.proxy.combobox.setCurrentIndex(combox_index)

        if combox_index == 0:
            self.proxy.input.setText(cfg.get(cfg.http_proxy))
        elif combox_index == 1:
            self.proxy.input.setText(cfg.get(cfg.socks5_proxy))

        self.proxy.combobox.currentIndexChanged.connect(self.proxy_com_change)
        self.proxy.input.textChanged.connect(self.proxy_inp_change)

        self.updateGroup.addSettingCard(self.MirrorCard)
        self.updateGroup.addSettingCard(self.auto_update)
        self.updateGroup.addSettingCard(self.MFW_auto_update)
        self.updateGroup.addSettingCard(self.force_github)
        self.updateGroup.addSettingCard(self.proxy)

    def proxy_com_change(self):
        cfg.set(cfg.proxy, self.proxy.combobox.currentIndex())
        if self.proxy.combobox.currentIndex() == 0:
            self.proxy.input.setText(cfg.get(cfg.http_proxy))
        elif self.proxy.combobox.currentIndex() == 1:
            self.proxy.input.setText(cfg.get(cfg.socks5_proxy))

    def proxy_inp_change(self):
        if self.proxy.combobox.currentIndex() == 0:
            cfg.set(cfg.http_proxy, self.proxy.input.text())
        elif self.proxy.combobox.currentIndex() == 1:
            cfg.set(cfg.socks5_proxy, self.proxy.input.text())

    def initialize_about_settings(self):
        """初始化关于设置。"""

        MFW_update_channel = cfg.get(cfg.MFW_update_channel)
        resource_update_channel = cfg.get(cfg.resource_update_channel)
        self.aboutGroup = SettingCardGroup(
            self.tr("Feedback and About"), self.Setting_scroll_widget
        )

        self.feedbackCard = DoubleButtonSettingCard(
            text=self.tr("Open the debug folder"),
            text2=self.tr("Generate a debug ZIP package"),
            icon=FIF.UPDATE,
            title=self.tr("Feedback"),
            configItem=cfg.resource_update_channel,
            comboBox=False,
            parent=self.aboutGroup,
        )

        self.updateCard = DoubleButtonSettingCard(
            text2=self.tr("Check for updates"),
            text=self.tr("About Resource"),
            icon=FIF.UPDATE,
            title=self.tr("Check for updates"),
            configItem=cfg.resource_update_channel,
            content=self.tr("Current") + " " + " " + self.tr("version:") + " ",
            parent=self.aboutGroup,
        )
        self.aboutCard = DoubleButtonSettingCard(
            text=self.tr("About UI"),
            text2=self.tr("Check for updates"),
            icon=FIF.INFO,
            title=self.tr("ChainFlow Assistant") + " " + __version__,
            configItem=cfg.MFW_update_channel,
            content=self.tr(
                "ChainFlow Assistant is open source under the GPLv3 license. Visit the project URL for more information."
            ),
            parent=self.aboutGroup,
        )
        self.aboutCard.combobox.setCurrentIndex(MFW_update_channel)
        self.updateCard.combobox.setCurrentIndex(resource_update_channel)

        self.aboutGroup.addSettingCard(self.feedbackCard)
        self.aboutGroup.addSettingCard(self.updateCard)
        self.aboutGroup.addSettingCard(self.aboutCard)

    def update_check(self):
        """执行更新检查操作。"""

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
        """初始化界面"""
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
            lambda: QDesktopServices.openUrl(
                QUrl("https://mirrorchyan.com/zh/get-start?source=MFW-CL_Setting")
            )
        )
        self.MirrorCard.lineEdit.textChanged.connect(self._onMirrorCardChange)

        # 连接关于信号
        self.feedbackCard.clicked.connect(self.open_debug_folder)
        self.feedbackCard.clicked2.connect(self.zip_debug_folder)

        self.updateCard.clicked2.connect(self.update_check)
        self.updateCard.clicked2.connect(lambda: cfg.set(cfg.start_complete, True))
        resource_issue_link = for_config_get_url(self.project_url, "about")
        if resource_issue_link is None:
            resource_issue_link = self.project_url
            # 绑定一个弹出信息
            self.updateCard.clicked.connect(
                lambda: InfoBar.warning(
                    self.tr("Warning"),
                    self.tr(
                        "The current version of the program does not support automatic updates."
                    ),
                    duration=1500,
                    parent=self,
                )
            )
        else:
            self.updateCard.clicked.connect(
                lambda: QDesktopServices.openUrl(QUrl(resource_issue_link))
            )
        self.aboutCard.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(REPO_URL)))
        self.aboutCard.clicked2.connect(self.update_self_func)
    def open_file_or_folder(self,path):
        try:
            if sys.platform == "win32":
                os.startfile(path)
            elif sys.platform == "darwin":
                # macOS 系统使用 open 命令
                subprocess.run(["open", path], check=True)
            elif sys.platform == "linux":
                # Linux 系统使用 xdg-open 命令
                subprocess.run(["xdg-open", path], check=True)
            else:
                logger.error(f"不支持的操作系统: {sys.platform}")
        except Exception as e:
            logger.error(f"打开 {path} 时出错: {e}")
    def open_debug_folder(self):
        """打开debug文件夹"""
        debug_path = os.path.join(".", "debug", maa_config_data.resource_name)
        if os.path.exists(debug_path):
            self.open_file_or_folder(debug_path)

    def zip_debug_folder(self):
        """压缩debug文件夹"""
        debug_path = os.path.join(".", "debug", "maa.tem.log")
        log_path = os.path.join(".", "debug", maa_config_data.resource_name, "maa.log")
        log_bak_path = os.path.join(
            ".", "debug", maa_config_data.resource_name, "maa.log.bak"
        )
        # 读取log_path中的maa.log和maa.log.bak并拼接,maa.log在后
        maa_log = ""
        if os.path.exists(log_bak_path):
            with open(log_bak_path, "r", encoding="utf-8") as log_file:
                maa_log += log_file.read()
        if os.path.exists(log_path):
            with open(log_path, "r", encoding="utf-8") as log_file:
                maa_log += log_file.read()
        if os.path.exists(debug_path):
            os.remove(debug_path)
        with open(debug_path, "w", encoding="utf-8") as log_file:
            log_file.write(maa_log)

        # 将maa.log和gui.log和vision文件夹和所有的png文件打包到一个zip中

        zip_path = os.path.join(".", "debug", "debug" + ".zip")
        if os.path.exists(zip_path):
            os.remove(zip_path)
        with zipfile.ZipFile(zip_path, "w") as zipf:
            # 定义要添加到 zip 的文件和文件夹
            files_to_add = ["maa.tem.log", "gui.log"]
            folders_to_add = [os.path.join(os.getcwd(),"debug",maa_config_data.resource_name, "vision")]

            # 添加单个文件
            for file in files_to_add:
                file_path = os.path.join(".", "debug", file)
                if os.path.exists(file_path):
                    # 写入文件时保留相对路径
                    zipf.write(file_path, os.path.relpath(file_path, "."))

            if os.path.exists(debug_path):
                os.remove(debug_path)
                
            # 添加文件夹及其内容
            for folder in folders_to_add:
                folder_path = os.path.join(".", "debug", folder)
                if os.path.exists(folder_path):
                    for root, dirs, files in os.walk(folder_path):
                        for file in files:
                            file_path = os.path.join(root, file)
                            # 写入文件时保留相对路径
                            zipf.write(file_path, os.path.relpath(file_path, "."))

            # 遍历 debug 文件夹，将所有 png 文件添加到 zip 中
            debug_path = os.path.join(".", "debug")
            for root, dirs, files in os.walk(debug_path):
                for file in files:
                    if file.endswith(".png"):
                        file_path = os.path.join(root, file)
                        # 写入文件时保留相对路径
                        zipf.write(file_path, os.path.relpath(file_path, "."))

        debug_zip_path = os.path.join(".", "debug")
        if os.path.exists(debug_zip_path):
            self.open_file_or_folder(debug_zip_path)

    def update_self_func(self):
        """更新程序。"""
        self.update_self.start()
        self.aboutCard.button2.setEnabled(False)
        self.aboutCard.button2.setText(self.tr("Updating..."))
        signalBus.show_download.emit(True)

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
            if cfg.get(cfg.auto_update_MFW):
                self.update_self_start()

    def update_self_start(self):
        """开始更新程序。"""
        # 重命名更新程序防止占用
        try:
            if sys.platform.startswith("win32"):
                self._rename_updater("MFWUpdater.exe", "MFWUpdater1.exe")
            elif sys.platform.startswith("darwin") or sys.platform.startswith("linux"):
                self._rename_updater("MFWUpdater", "MFWUpdater1")
        except Exception as e:
            logger.error(f"重命名更新程序失败: {e}")
            signalBus.infobar_message.emit({"status": "failed", "msg": e})
            return

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
        try:
            if sys.platform.startswith("win32"):
                from subprocess import CREATE_NEW_PROCESS_GROUP, DETACHED_PROCESS

                subprocess.Popen(
                    ["./MFWUpdater1.exe", "-update"],
                    creationflags=CREATE_NEW_PROCESS_GROUP | DETACHED_PROCESS,
                )
            elif sys.platform.startswith("darwin") or sys.platform.startswith("linux"):
                subprocess.Popen(["./MFWUpdater1", "-update"], start_new_session=True)
            else:
                raise NotImplementedError("Unsupported platform")
        except Exception as e:
            logger.error(f"启动更新程序失败: {e}")
            signalBus.infobar_message.emit({"status": "failed", "msg": e})
            return

        logger.info("正在启动更新程序")

    def _update_config(self, card: LineEditCard, config_key: str):
        """根据输入更新配置文件中的值。"""
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
