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
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import QWidget, QLabel, QFileDialog, QApplication


from ..common.config import cfg, REPO_URL, isWin11
from ..common.signal_bus import signalBus
from ..common.style_sheet import StyleSheet
from ..components.line_edit_card import LineEditCard
from ..components.combobox_setting_card_custom import ComboBoxSettingCardCustom
from ..components.notic_setting_card import NoticeButtonSettingCard
from ..utils.update import Update, UpdateSelf
from ..utils.tool import Save_Config, get_gpu_info, for_config_get_url, decrypt, encrypt
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
        self.scrollWidget = QWidget()
        self.expandLayout = ExpandLayout(self.scrollWidget)
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
        self.settingLabel = QLabel(self.tr("Settings"), self)

        # 初始化设置
        self.initialize_adb_settings()
        self.initialize_win32_settings()
        self.initialize_start_settings()
        self.initialize_personalization_settings()
        self.initialize_notice_settings()
        self.initialize_dev_settings()
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

        self.ADB_port.lineEdit.setText(
            maa_config_data.config.get("adb", {}).get("address", "")
        )
        self.ADB_path.lineEdit.setText(
            maa_config_data.config.get("adb", {}).get("adb_path", "")
        )
        self.emu_path.lineEdit.setText(maa_config_data.config.get("emu_path", ""))
        self.emu_args.lineEdit.setText(maa_config_data.config.get("emu_args", ""))
        self.emu_wait_time.lineEdit.setText(
            str(maa_config_data.config.get("emu_wait_time", ""))
        )
        self.exe_path.lineEdit.setText(maa_config_data.config.get("exe_path", ""))
        self.exe_args.lineEdit.setText(maa_config_data.config.get("exe_args", ""))
        self.exe_wait_time.lineEdit.setText(
            str(maa_config_data.config.get("exe_wait_time", ""))
        )
        self.run_before_start.lineEdit.setText(
            maa_config_data.config.get("run_before_start", "")
        )
        self.run_before_start_args.lineEdit.setText(
            maa_config_data.config.get("run_before_start_args", "")
        )
        self.run_after_finish.lineEdit.setText(
            maa_config_data.config.get("run_after_finish", "")
        )
        self.run_after_finish_args.lineEdit.setText(
            maa_config_data.config.get("run_after_finish_args", "")
        )
        self.use_GPU.path = maa_config_data.config_path
        self.win32_input_mode.path = maa_config_data.config_path
        self.win32_screencap_mode.path = maa_config_data.config_path
        self.ADB_input_mode.path = maa_config_data.config_path
        self.ADB_screencap_mode.path = maa_config_data.config_path
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
        self.ADB_port.lineEdit.clear()
        self.ADB_path.lineEdit.clear()
        self.emu_path.lineEdit.clear()
        self.emu_args.lineEdit.clear()
        self.emu_wait_time.lineEdit.clear()
        self.exe_path.lineEdit.clear()
        self.exe_args.lineEdit.clear()
        self.exe_wait_time.lineEdit.clear()
        self.run_before_start.lineEdit.clear()
        self.run_before_start_args.lineEdit.clear()
        self.run_after_finish.lineEdit.clear()
        self.run_after_finish_args.lineEdit.clear()
        self.DEVmodeCard.switchButton.setChecked(False)
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
        for widget in self.scrollWidget.findChildren(QWidget):
            # 启用或禁用控件
            widget.setEnabled(enable)

    def initialize_adb_settings(self):
        """初始化 ADB 设置。"""
        self.ADB_Setting = SettingCardGroup(self.tr("ADB"), self.scrollWidget)

        # 读取 ADB 配置（默认为空）
        address_data = ""
        path_data = "./"
        emu_path = ""
        emu_wait_time = "10"

        self.ADB_port = LineEditCard(
            icon=FIF.COMMAND_PROMPT,
            holderText=address_data,
            title=self.tr("ADB Port"),
            num_only=False,
            parent=self.ADB_Setting,
        )
        self.ADB_path = LineEditCard(
            icon=FIF.APPLICATION,
            title=self.tr("ADB Path"),
            num_only=False,
            holderText=path_data,
            content=self.tr("Select ADB Path"),
            button=True,
            parent=self.ADB_Setting,
        )
        self.emu_path = LineEditCard(
            icon=FIF.APPLICATION,
            title=self.tr("Select Emulator Path"),
            num_only=False,
            holderText=emu_path,
            content=self.tr("Select Emulator Path"),
            button=True,
            parent=self.ADB_Setting,
        )
        self.emu_args = LineEditCard(
            icon=FIF.LABEL,
            holderText="",
            title=self.tr("Run Parameters"),
            num_only=False,
            parent=self.ADB_Setting,
        )
        self.emu_wait_time = LineEditCard(
            icon=FIF.STOP_WATCH,
            holderText=emu_wait_time,
            title=self.tr("Wait Time for Emulator Startup"),
            num_only=True,
            parent=self.ADB_Setting,
        )

        self.ADB_Setting.addSettingCard(self.ADB_port)
        self.ADB_Setting.addSettingCard(self.ADB_path)
        self.ADB_Setting.addSettingCard(self.emu_path)
        self.ADB_Setting.addSettingCard(self.emu_args)
        self.ADB_Setting.addSettingCard(self.emu_wait_time)

    def initialize_win32_settings(self):
        """初始化 Win32 设置。"""

        exe_path = ""
        exe_args = ""
        exe_wait_time = "10"
        self.Win32_Setting = SettingCardGroup(self.tr("Win32"), self.scrollWidget)
        self.exe_path = LineEditCard(
            icon=FIF.APPLICATION,
            title=self.tr("Executable Path"),
            content=self.tr("Select Executable Path"),
            num_only=False,
            holderText=exe_path,
            button=True,
            parent=self.Win32_Setting,
        )
        self.exe_args = LineEditCard(
            icon=FIF.LABEL,
            holderText=exe_args,
            title=self.tr("Run Parameters"),
            num_only=False,
            parent=self.Win32_Setting,
        )
        self.exe_wait_time = LineEditCard(
            icon=FIF.STOP_WATCH,
            holderText=exe_wait_time,
            title=self.tr("Wait Time for Program Startup"),
            parent=self.Win32_Setting,
        )

        self.Win32_Setting.addSettingCard(self.exe_path)
        self.Win32_Setting.addSettingCard(self.exe_args)
        self.Win32_Setting.addSettingCard(self.exe_wait_time)

    def initialize_start_settings(self):
        """初始化启动设置。"""

        run_before_start = ""
        run_after_finish = ""

        self.start_Setting = SettingCardGroup(
            self.tr("Custom Startup"), self.scrollWidget
        )

        self.run_after_startup = SwitchSettingCard(
            FIF.SPEED_HIGH,
            self.tr("run after startup"),
            self.tr("Launch the task immediately after starting the GUI program"),
            configItem=cfg.run_after_startup,
            parent=self.start_Setting,
        )

        self.run_before_start = LineEditCard(
            icon=FIF.APPLICATION,
            title=self.tr("Run Program Before Start"),
            content=self.tr("Select Program"),
            num_only=False,
            holderText=run_before_start,
            button=True,
            parent=self.start_Setting,
        )
        self.run_before_start_args = LineEditCard(
            icon=FIF.LABEL,
            holderText="",
            title=self.tr("Run Parameters"),
            num_only=False,
            parent=self.start_Setting,
        )

        self.run_after_finish = LineEditCard(
            icon=FIF.APPLICATION,
            title=self.tr("Run Program After Finish"),
            content=self.tr("Select Program"),
            num_only=False,
            holderText=run_after_finish,
            button=True,
            parent=self.start_Setting,
        )
        self.run_after_finish_args = LineEditCard(
            icon=FIF.LABEL,
            holderText="",
            title=self.tr("Run Parameters"),
            num_only=False,
            parent=self.start_Setting,
        )
        self.start_Setting.addSettingCard(self.run_after_startup)
        self.start_Setting.addSettingCard(self.run_before_start)
        self.start_Setting.addSettingCard(self.run_before_start_args)
        self.start_Setting.addSettingCard(self.run_after_finish)
        self.start_Setting.addSettingCard(self.run_after_finish_args)

    def initialize_personalization_settings(self):
        """初始化个性化设置。"""
        self.personalGroup = SettingCardGroup(
            self.tr("Personalization"), self.scrollWidget
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
        self.noticeGroup = SettingCardGroup(self.tr("Notice"), self.scrollWidget)

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

        self.noticeGroup.addSettingCard(self.dingtalk_noticeTypeCard)
        self.noticeGroup.addSettingCard(self.lark_noticeTypeCard)
        self.noticeGroup.addSettingCard(self.SMTP_noticeTypeCard)
        self.noticeGroup.addSettingCard(self.WxPusher_noticeTypeCard)

    def initialize_dev_settings(self):
        """初始化开发者设置。"""
        self.DEVGroup = SettingCardGroup(self.tr("DEV Mode"), self.scrollWidget)

        # 设置开发者配置
        cfg.set(cfg.save_draw, False)

        gpu_mapping = get_gpu_info()
        logger.debug(f"GPU列表: {gpu_mapping}")
        gpu_combox_list = self.get_unique_gpu_mapping(gpu_mapping)
        gpu_mapping[-1] = self.tr("Auto")
        gpu_mapping[-2] = self.tr("Disabled")

        win32_input_mapping = {
            0: self.tr("default"),
            1: "seize",
            2: "SendMessage",
        }
        win32_input_combox_list = [
            self.tr("default"),
            "seize",
            "SendMessage",
        ]

        win32_screencap_mapping = {
            0: self.tr("default"),
            1: "GDI",
            2: "FramePool",
            4: "DXGI_DesktopDup",
        }

        ADB_input_mapping = {
            0: self.tr("default"),
            1: "AdbShell",
            2: "MinitouchAndAdbKey",
            4: "Maatouch",
            8: "EmulatorExtras",
        }

        ADB_screencap_mapping = {
            0: self.tr("default"),
            1: "EncodeToFileAndPull",
            2: "Encode",
            4: "RawWithGzip",
            8: "RawByNetcat",
            16: "MinicapDirect",
            32: "MinicapStream",
            64: "EmulatorExtras",
        }

        self.use_GPU = ComboBoxSettingCardCustom(
            icon=FIF.IOT,
            title=self.tr("Select GPU"),
            content=self.tr("Use GPU to accelerate inference"),
            texts=gpu_combox_list,
            target=["gpu"],
            path=maa_config_data.config_path,
            parent=self.DEVGroup,
            mode="setting",
            mapping=gpu_mapping,
        )

        self.win32_input_mode = ComboBoxSettingCardCustom(
            icon=FIF.SAVE_AS,
            title=self.tr("Select Win32 Input Mode"),
            texts=win32_input_combox_list,
            target=["win32", "input_method"],
            path=maa_config_data.config_path,
            parent=self.DEVGroup,
            mode="setting",
            mapping=win32_input_mapping,
        )

        self.win32_screencap_mode = ComboBoxSettingCardCustom(
            icon=FIF.SAVE_AS,
            title=self.tr("Select Win32 Screencap Mode"),
            texts=[self.tr("default"), "GDI", "FramePool", "DXGI_DesktopDup"],
            target=["win32", "screen_method"],
            path=maa_config_data.config_path,
            parent=self.DEVGroup,
            mode="setting",
            mapping=win32_screencap_mapping,
        )

        self.ADB_input_mode = ComboBoxSettingCardCustom(
            icon=FIF.SAVE_AS,
            title=self.tr("Select ADB Input Mode"),
            texts=[
                self.tr("default"),
                "AdbShell",
                "MinitouchAndAdbKey",
                "Maatouch",
                "EmulatorExtras",
            ],
            target=["adb", "input_method"],
            path=maa_config_data.config_path,
            parent=self.DEVGroup,
            mode="setting",
            mapping=ADB_input_mapping,
        )

        self.ADB_screencap_mode = ComboBoxSettingCardCustom(
            icon=FIF.SAVE_AS,
            title=self.tr("Select ADB Screencap Mode"),
            texts=[
                self.tr("default"),
                "EncodeToFileAndPull",
                "Encode",
                "RawWithGzip",
                "RawByNetcat",
                "MinicapDirect",
                "MinicapStream",
                "EmulatorExtras",
            ],
            target=["adb", "screen_method"],
            path=maa_config_data.config_path,
            parent=self.DEVGroup,
            mode="setting",
            mapping=ADB_screencap_mapping,
        )

        self.DEVmodeCard = SwitchSettingCard(
            FIF.PHOTO,
            self.tr("DEV Mode"),
            self.tr("If enabled, screenshots will be saved in ./debug/vision"),
            configItem=cfg.save_draw,
            parent=self.DEVGroup,
        )

        self.DEVGroup.addSettingCard(self.DEVmodeCard)
        self.DEVGroup.addSettingCard(self.use_GPU)
        self.DEVGroup.addSettingCard(self.win32_input_mode)
        self.DEVGroup.addSettingCard(self.win32_screencap_mode)
        self.DEVGroup.addSettingCard(self.ADB_input_mode)
        self.DEVGroup.addSettingCard(self.ADB_screencap_mode)

    def initialize_update_settings(self):
        """初始化更新设置。"""
        with open("k.ey", "rb") as key_file:
            key = key_file.read()
            holddertext = decrypt(cfg.get(cfg.Mcdk), key)
        self.updateGroup = SettingCardGroup(self.tr("Update"), self.scrollWidget)
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

        self.updateGroup.addSettingCard(self.MirrorCard)
        self.updateGroup.addSettingCard(self.auto_update)

    def initialize_about_settings(self):
        """初始化关于设置。"""
        self.aboutGroup = SettingCardGroup(self.tr("About"), self.scrollWidget)
        with open(
            os.path.join(os.getcwd(), "config", "version.txt"), "r", encoding="utf-8"
        ) as f:
            try:
                MFW_Version = f.read().split()[2]
            except:
                MFW_Version = "Unknown"

        self.updateCard = DoubleButtonSettingCard(
            text2=self.tr("Check for updates"),
            text=self.tr("Submit Feedback"),
            icon=FIF.UPDATE,
            title=self.tr("Check for updates"),
            content=self.tr("Current") + " " + " " + self.tr("version:") + " ",
            parent=self.aboutGroup,
        )
        self.aboutCard = DoubleButtonSettingCard(
            text=self.tr("About"),
            text2=self.tr("Check for updates"),
            icon=FIF.INFO,
            title="MFW-PyQt6 "+ MFW_Version,
            content=self.tr(
                "MFW-PyQt6 is open source under the GPLv3 license. Visit the project URL for more information."
            ),
            parent=self.aboutGroup,
        )

        self.aboutGroup.addSettingCard(self.updateCard)
        self.aboutGroup.addSettingCard(self.aboutCard)

    def get_unique_gpu_mapping(self, gpu_mapping: dict) -> list:
        """获取唯一的 GPU 名称列表。"""
        gpu_combox_list = list(set(gpu_mapping.values()))
        gpu_combox_list.insert(0, self.tr("Auto"))
        gpu_combox_list.insert(1, self.tr("Disabled"))

        return gpu_combox_list

    def update_check(self):
        self.Updatethread.start()
        self.updateCard.button2.setEnabled(False)
        self.updateCard.button2.setText(self.tr("Checking for updates..."))

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
        elif data_dict["status"] == "info":
            return
        self.updateCard.button2.setText(self.tr("Check for updates"))
        self.updateCard.button2.setEnabled(True)

    def __initWidget(self):
        self.resize(1000, 800)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setViewportMargins(0, 80, 0, 20)
        self.setWidget(self.scrollWidget)
        self.setWidgetResizable(True)
        self.setObjectName("settingInterface")

        # 初始化样式表
        self.scrollWidget.setObjectName("scrollWidget")
        self.settingLabel.setObjectName("settingLabel")
        StyleSheet.SETTING_INTERFACE.apply(self)

        self.micaCard.setEnabled(isWin11())

        # 初始化布局
        self.__initLayout()

    def __initLayout(self):
        """初始化设置卡片的布局。"""
        self.settingLabel.move(36, 30)

        # 将卡片组添加到布局中
        self.expandLayout.setSpacing(28)
        self.expandLayout.setContentsMargins(36, 10, 36, 0)
        self.expandLayout.addWidget(self.ADB_Setting)
        self.expandLayout.addWidget(self.Win32_Setting)
        self.expandLayout.addWidget(self.start_Setting)
        self.expandLayout.addWidget(self.personalGroup)
        self.expandLayout.addWidget(self.noticeGroup)
        self.expandLayout.addWidget(self.DEVGroup)
        self.expandLayout.addWidget(self.updateGroup)
        self.expandLayout.addWidget(self.aboutGroup)

    def __showRestartTooltip(self):
        """显示重启提示。"""
        InfoBar.success(
            self.tr("Updated successfully"),
            self.tr("Configuration takes effect after restart"),
            duration=1500,
            parent=self,
        )

    def __onADBPathCardClicked(self):
        """手动选择 ADB.exe 的位置。"""
        self.__select_file(self.ADB_path, "adb")

    def __onEmuPathCardClicked(self):
        """手动选择模拟器的位置。"""
        self.__select_file(self.emu_path, "emu")

    def __onExePathCardClicked(self):
        """手动选择可执行文件的路径。"""
        self.__select_file(self.exe_path, "exe")

    def __onRunBeforeStartCardClicked(self):
        """手动选择启动前运行的程序脚本。"""
        self.__select_file(self.run_before_start, "run_before")

    def __onRunAfterFinishCardClicked(self):
        """手动选择完成后运行的程序脚本。"""
        self.__select_file(self.run_after_finish, "run_after")

    def __select_file(self, setting_card: LineEditCard, config_key):
        """帮助方法，用于处理文件选择和设置内容。"""
        file_name, _ = QFileDialog.getOpenFileName(
            self, self.tr("Choose file"), "./", "All Files (*)"
        )
        if not file_name:
            return

        # 更新配置并设置卡片内容
        if config_key == "adb":
            maa_config_data.config["adb"]["adb_path"] = file_name
            logger.debug(f"选择的 ADB 路径: {file_name}")
        elif config_key == "emu":
            maa_config_data.config["emu_path"] = file_name
            logger.debug(f"选择的模拟器路径: {file_name}")
        elif config_key == "exe":
            maa_config_data.config["exe_path"] = file_name
            logger.debug(f"选择的可执行文件路径: {file_name}")
        elif config_key == "run_before":
            maa_config_data.config["run_before_start"] = file_name
            logger.debug(f"选择的启动前运行程序脚本路径: {file_name}")
        elif config_key == "run_after":
            maa_config_data.config["run_after_finish"] = file_name
            logger.debug(f"选择的完成后运行程序脚本路径: {file_name}")

        Save_Config(maa_config_data.config_path, maa_config_data.config)
        logger.info(f"保存至{maa_config_data.config_path}")

        setting_card.lineEdit.setText(file_name)

    def __connectSignalToSlot(self):
        """连接信号到对应的槽函数。"""
        signalBus.update_download_finished.connect(self.on_update_finished)
        cfg.appRestartSig.connect(self.__showRestartTooltip)
        signalBus.update_adb.connect(self.update_adb)
        signalBus.auto_update.connect(self.update_check)
        signalBus.download_self_finished.connect(self.update_self_finished)

        # 连接 ADB 信号
        self.ADB_port.lineEdit.textChanged.connect(self._onADB_portCardChange)
        self.ADB_path.toolbutton.clicked.connect(self.__onADBPathCardClicked)
        self.ADB_path.lineEdit.textChanged.connect(self._onADB_pathCardChange)
        self.emu_path.toolbutton.clicked.connect(self.__onEmuPathCardClicked)
        self.emu_path.lineEdit.textChanged.connect(self._onEmuPathCardChange)
        self.emu_args.lineEdit.textChanged.connect(self._onEmuArgsCardChange)
        self.emu_wait_time.lineEdit.textChanged.connect(self._onEmuWaitTimeCardChange)

        # 连接 Win32 信号
        self.exe_path.toolbutton.clicked.connect(self.__onExePathCardClicked)
        self.exe_path.lineEdit.textChanged.connect(self._onExePathCardChange)
        self.exe_args.lineEdit.textChanged.connect(self._onExeParameterCardChange)
        self.exe_wait_time.lineEdit.textChanged.connect(self._onExeWaitTimeCardChange)

        # 连接启动信号
        self.run_after_startup.checkedChanged.connect(self._onRunAfterStartupCardChange)
        self.run_before_start.toolbutton.clicked.connect(
            self.__onRunBeforeStartCardClicked
        )
        self.run_before_start.lineEdit.textChanged.connect(
            self._onRunBeforeStartCardChange
        )
        self.run_before_start_args.lineEdit.textChanged.connect(
            self._onRunBeforeStartArgsCardChange
        )
        self.run_after_finish.toolbutton.clicked.connect(
            self.__onRunAfterFinishCardClicked
        )
        self.run_after_finish.lineEdit.textChanged.connect(
            self._onRunAfterFinishCardChange
        )
        self.run_after_finish_args.lineEdit.textChanged.connect(
            self._onRunAfterFinishArgsCardChange
        )

        # 连接开发者模式信号
        self.DEVmodeCard.checkedChanged.connect(self._onDEVmodeCardChange)

        # 连接个性化信号
        cfg.themeChanged.connect(setTheme)
        self.themeColorCard.colorChanged.connect(lambda c: setThemeColor(c))
        self.micaCard.checkedChanged.connect(signalBus.micaEnableChanged)
        # 连接更新信号
        self.MirrorCard.button.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl("https://mirrorchyan.com/"))
        )
        self.MirrorCard.lineEdit.textChanged.connect(self._onMirrorCardChange)
        self.updateCard.clicked2.connect(self.update_check)
        # 连接关于信号
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
        button.setEnabled(True)

        status_type = status["status"]
        if status_type in ["no_need", "failed", "stoped"]:
            button.setText(self.tr("Update"))
        elif status_type == "success":
            button.setText(self.tr("Update Now"))
            button.clicked.disconnect()
            button.clicked.connect(self.update_self_start)


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

    def _onADB_portCardChange(self):
        """根据端口更改更新 ADB 地址。"""
        if maa_config_data.config_path == "":
            return
        port = self.ADB_port.lineEdit.text()
        maa_config_data.config["adb"]["address"] = port
        Save_Config(maa_config_data.config_path, maa_config_data.config)

    def _onADB_pathCardChange(self):
        """根据输入更新 ADB 路径。"""
        if maa_config_data.config_path == "":
            return
        adb_path = self.ADB_path.lineEdit.text()
        maa_config_data.config["adb"]["adb_path"] = adb_path
        Save_Config(maa_config_data.config_path, maa_config_data.config)

    def _onEmuPathCardChange(self):
        """根据输入更新模拟器路径。"""
        self._update_config(self.emu_path, "emu_path")

    def _onEmuWaitTimeCardChange(self):
        """根据输入更新启动模拟器等待时间。"""
        self._update_config(self.emu_wait_time, "emu_wait_time")

    def _onExePathCardChange(self):
        """根据输入更新可执行文件路径。"""
        self._update_config(self.exe_path, "exe_path")

    def _onExeWaitTimeCardChange(self):
        """根据输入更新启动可执行文件等待时间。"""
        self._update_config(self.exe_wait_time, "exe_wait_time")

    def _onExeParameterCardChange(self):
        """根据输入更新可执行文件的参数。"""
        self._update_config(self.exe_args, "exe_args")

    def _onEmuArgsCardChange(self):
        """根据输入更新模拟器参数。"""
        self._update_config(self.emu_args, "emu_args")

    def _onRunBeforeStartArgsCardChange(self):
        """根据输入更新启动前运行的程序脚本参数。"""
        self._update_config(self.run_before_start_args, "run_before_start_args")

    def _onRunAfterFinishArgsCardChange(self):
        """根据输入更新完成后运行的程序脚本参数。"""
        self._update_config(self.run_after_finish_args, "run_after_finish_args")

    def _onRunBeforeStartCardChange(self):
        """根据输入更新启动前运行的程序脚本路径。"""
        self._update_config(self.run_before_start, "run_before_start")

    def _onRunAfterFinishCardChange(self):
        """根据输入更新完成后运行的程序脚本路径。"""
        self._update_config(self.run_after_finish, "run_after_finish")

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

    def _onDEVmodeCardChange(self):
        """切换开发者模式的保存设置。"""
        if maa_config_data.config_path == "":
            return
        state = self.DEVmodeCard.isChecked()
        maa_config_data.config["save_draw"] = state
        Save_Config(maa_config_data.config_path, maa_config_data.config)

    def update_adb(self):
        """根据外部消息更新 ADB 路径和端口。"""
        logger.info(f"adb_信息更新")
        self.ADB_path.lineEdit.setText(
            maa_config_data.config.get("adb", {}).get("adb_path", "")
        )
        self.ADB_port.lineEdit.setText(
            maa_config_data.config.get("adb", {}).get("address", "")
        )

    def Switch_Controller(self, controller):
        """在 ADB 和 Win32 控制器设置之间切换。"""
        if controller == "Win32":
            self.ADB_input_mode.hide()
            self.ADB_screencap_mode.hide()
            self.win32_input_mode.show()
            self.win32_screencap_mode.show()
        elif controller == "Adb":
            self.win32_input_mode.hide()
            self.win32_screencap_mode.hide()
            self.ADB_input_mode.show()
            self.ADB_screencap_mode.show()
