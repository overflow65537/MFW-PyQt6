import os
import re

from qfluentwidgets import (
    SettingCardGroup,
    SwitchSettingCard,
    OptionsSettingCard,
    PrimaryPushSettingCard,
    ScrollArea,
    ComboBoxSettingCard,
    ExpandLayout,
    CustomColorSettingCard,
    setTheme,
    setThemeColor,
    ConfigItem,
)
from qfluentwidgets import FluentIcon as FIF
from qfluentwidgets import InfoBar
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import QWidget, QLabel, QFileDialog

from ..common.config import cfg, REPO_URL, isWin11
from ..common.signal_bus import signalBus
from ..common.style_sheet import StyleSheet
from ..components.line_edit_card import LineEditCard
from ..components.combobox_setting_card_custom import ComboBoxSettingCardCustom
from ..components.notic_setting_card import NoticeButtonSettingCard
from ..utils.update import check_Update, Update
from ..utils.tool import Read_Config, Save_Config, get_gpu_info, for_config_get_url


class SettingInterface(ScrollArea):
    """设置界面，用于配置应用程序设置。"""

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.scrollWidget = QWidget()
        self.expandLayout = ExpandLayout(self.scrollWidget)
        signalBus.update_adb.connect(self.update_adb)

        self.settingLabel = QLabel(self.tr("Settings"), self)

        self.UpdateWorker = check_Update(self)

        # 初始化设置
        self.initialize_adb_settings()
        self.initialize_win32_settings()
        self.initialize_start_settings()
        self.initialize_personalization_settings()
        # self.initialize_notice_settings()
        self.initialize_dev_settings()
        self.initialize_about_settings()

        self.__initWidget()

    def initialize_adb_settings(self):
        """初始化 ADB 设置。"""
        self.ADB_Setting = SettingCardGroup(self.tr("ADB"), self.scrollWidget)

        # 读取 ADB 配置
        pi_config = (
            Read_Config(cfg.get(cfg.Maa_config))
            if os.path.exists(cfg.get(cfg.Maa_config))
            else {}
        )
        address_data = pi_config.get("adb", {}).get("address", "")

        path_data = pi_config.get("adb", {}).get("adb_path", "./")

        self.ADB_port = LineEditCard(
            icon=FIF.COMMAND_PROMPT,
            holderText=address_data,
            title=self.tr("ADB Port"),
            num_only=False,
            parent=self.ADB_Setting,
        )
        self.ADB_path = PrimaryPushSettingCard(
            self.tr("Select ADB Path"),
            FIF.COMMAND_PROMPT,
            self.tr("ADB Path"),
            path_data,
            self.ADB_Setting,
        )
        self.emu_path = PrimaryPushSettingCard(
            self.tr("Select Emulator Path"),
            FIF.COMMAND_PROMPT,
            self.tr("Emulator Path"),
            cfg.get(cfg.emu_path),
            self.ADB_Setting,
        )
        self.emu_wait_time = LineEditCard(
            icon=FIF.COMMAND_PROMPT,
            configItem=cfg.emu_wait_time,
            title=self.tr("Wait Time for Emulator Startup"),
            parent=self.ADB_Setting,
        )

        self.ADB_Setting.addSettingCard(self.ADB_port)
        self.ADB_Setting.addSettingCard(self.ADB_path)
        self.ADB_Setting.addSettingCard(self.emu_path)
        self.ADB_Setting.addSettingCard(self.emu_wait_time)

    def initialize_win32_settings(self):
        """初始化 Win32 设置。"""
        self.Win32_Setting = SettingCardGroup(self.tr("Win32"), self.scrollWidget)

        self.exe_path = PrimaryPushSettingCard(
            self.tr("Select Executable Path"),
            FIF.COMMAND_PROMPT,
            self.tr("Executable Path"),
            cfg.get(cfg.exe_path),
            self.Win32_Setting,
        )
        self.exe_parameter = LineEditCard(
            icon=FIF.COMMAND_PROMPT,
            configItem=cfg.exe_parameter,
            title=self.tr("Run Parameters"),
            num_only=False,
            parent=self.Win32_Setting,
        )
        self.exe_wait_time = LineEditCard(
            icon=FIF.COMMAND_PROMPT,
            configItem=cfg.exe_wait_time,
            title=self.tr("Wait Time for Program Startup"),
            parent=self.Win32_Setting,
        )

        self.Win32_Setting.addSettingCard(self.exe_path)
        self.Win32_Setting.addSettingCard(self.exe_parameter)
        self.Win32_Setting.addSettingCard(self.exe_wait_time)

    def initialize_start_settings(self):
        """初始化启动设置。"""
        self.start_Setting = SettingCardGroup(
            self.tr("Custom Startup"), self.scrollWidget
        )

        self.run_before_start = PrimaryPushSettingCard(
            self.tr("Select Program"),
            FIF.COMMAND_PROMPT,
            self.tr("Run Program Before Start"),
            cfg.get(cfg.run_before_start),
            self.start_Setting,
        )
        self.run_after_finish = PrimaryPushSettingCard(
            self.tr("Select Program"),
            FIF.COMMAND_PROMPT,
            self.tr("Run Program After Finish"),
            cfg.get(cfg.run_after_finish),
            self.start_Setting,
        )

        self.start_Setting.addSettingCard(self.run_before_start)
        self.start_Setting.addSettingCard(self.run_after_finish)

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
            icon=FIF.COMMAND_PROMPT,
            title=self.tr("DingTalk"),
            notice_type="DingTalk",
            parent=self.noticeGroup,
        )

        self.lark_noticeTypeCard = NoticeButtonSettingCard(
            text=self.tr("Modify"),
            icon=FIF.COMMAND_PROMPT,
            title=self.tr("Lark"),
            notice_type="Lark",
            parent=self.noticeGroup,
        )

        self.qmsg_noticeTypeCard = NoticeButtonSettingCard(
            text=self.tr("Modify"),
            icon=FIF.COMMAND_PROMPT,
            title=self.tr("Qmsg"),
            notice_type="Qmsg",
            parent=self.noticeGroup,
        )

        self.SMTP_noticeTypeCard = NoticeButtonSettingCard(
            text=self.tr("Modify"),
            icon=FIF.COMMAND_PROMPT,
            title=self.tr("SMTP"),
            notice_type="SMTP",
            parent=self.noticeGroup,
        )

        self.noticeGroup.addSettingCard(self.dingtalk_noticeTypeCard)
        self.noticeGroup.addSettingCard(self.lark_noticeTypeCard)
        self.noticeGroup.addSettingCard(self.qmsg_noticeTypeCard)
        self.noticeGroup.addSettingCard(self.SMTP_noticeTypeCard)

    def initialize_dev_settings(self):
        """初始化开发者设置。"""
        self.DEVGroup = SettingCardGroup(self.tr("DEV Mode"), self.scrollWidget)

        # 设置开发者配置
        DEV_Config = self.check_and_get_dev_config()

        gpu_mapping = get_gpu_info()
        gpu_combox_list = self.get_unique_gpu_mapping(gpu_mapping)

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
            icon=FIF.FILTER,
            title=self.tr("Select GPU"),
            content="Use GPU to accelerate inference",
            texts=gpu_combox_list,
            target=["gpu"],
            path=cfg.get(cfg.Maa_config),
            parent=self.DEVGroup,
            mode="setting",
            mapping=gpu_mapping,
        )

        self.win32_input_mode = ComboBoxSettingCardCustom(
            icon=FIF.FILTER,
            title=self.tr("Select Win32 Input Mode"),
            texts=win32_input_combox_list,
            target=["win32", "input_method"],
            path=cfg.get(cfg.Maa_config),
            parent=self.DEVGroup,
            mode="setting",
            mapping=win32_input_mapping,
        )

        self.win32_screencap_mode = ComboBoxSettingCardCustom(
            icon=FIF.FILTER,
            title=self.tr("Select Win32 Screencap Mode"),
            texts=[
                self.tr("default"),
                "GDI",
                "FramePool",
                "DXGI_DesktopDup",
            ],
            target=["win32", "screen_method"],
            path=cfg.get(cfg.Maa_config),
            parent=self.DEVGroup,
            mode="setting",
            mapping=win32_screencap_mapping,
        )

        self.ADB_input_mode = ComboBoxSettingCardCustom(
            icon=FIF.FILTER,
            title=self.tr("Select ADB Input Mode"),
            texts=[
                self.tr("default"),
                "AdbShell",
                "MinitouchAndAdbKey",
                "Maatouch",
                "EmulatorExtras",
            ],
            target=["adb", "input_method"],
            path=cfg.get(cfg.Maa_config),
            parent=self.DEVGroup,
            mode="setting",
            mapping=ADB_input_mapping,
        )

        self.ADB_screencap_mode = ComboBoxSettingCardCustom(
            icon=FIF.FILTER,
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
            path=cfg.get(cfg.Maa_config),
            parent=self.DEVGroup,
            mode="setting",
            mapping=ADB_screencap_mapping,
        )

        self.DEVmodeCard = SwitchSettingCard(
            FIF.ALBUM,
            self.tr("DEV Mode"),
            self.tr("If enabled, screenshots will be saved in ./debug/vision"),
            configItem=ConfigItem(group="DEV", name="DEV", default=DEV_Config),
            parent=self.DEVGroup,
        )

        self.DEVGroup.addSettingCard(self.DEVmodeCard)
        self.DEVGroup.addSettingCard(self.use_GPU)
        self.DEVGroup.addSettingCard(self.win32_input_mode)
        self.DEVGroup.addSettingCard(self.win32_screencap_mode)
        self.DEVGroup.addSettingCard(self.ADB_input_mode)
        self.DEVGroup.addSettingCard(self.ADB_screencap_mode)

    def initialize_about_settings(self):
        """初始化关于设置。"""
        self.aboutGroup = SettingCardGroup(self.tr("About"), self.scrollWidget)

        self.updateCard = PrimaryPushSettingCard(
            self.tr("Check for updates"),
            FIF.UPDATE,
            self.tr("Check for updates"),
            self.tr("Current")
            + cfg.get(cfg.Project_name)
            + self.tr("version:")
            + cfg.get(cfg.Project_version),
            self.aboutGroup,
        )
        self.feedbackCard = PrimaryPushSettingCard(
            self.tr("Submit Feedback"),
            FIF.FEEDBACK,
            self.tr("Submit Feedback"),
            self.tr("Submit feedback to help us improve") + cfg.get(cfg.Project_name),
            self.aboutGroup,
        )
        self.aboutCard = PrimaryPushSettingCard(
            self.tr("About"),
            FIF.INFO,
            self.tr("About PyQt-MAA"),
            self.tr(
                "PyQt-MAA is open source under the GPLv3 license. Visit the project URL for more information."
            ),
            self.aboutGroup,
        )

        self.aboutGroup.addSettingCard(self.updateCard)
        self.aboutGroup.addSettingCard(self.feedbackCard)
        self.aboutGroup.addSettingCard(self.aboutCard)

    def check_and_get_dev_config(self):
        """检查并获取开发者配置。"""
        if os.path.exists(cfg.get(cfg.Maa_dev)):
            return Read_Config(cfg.get(cfg.Maa_dev))["save_draw"]
        else:
            Save_Config(
                cfg.get(cfg.Maa_dev),
                {
                    "logging": True,
                    "recording": False,
                    "save_draw": False,
                    "show_hit_draw": False,
                    "stdout_level": 2,
                },
            )
            return False

    def get_unique_gpu_mapping(self, gpu_mapping):
        """获取唯一的 GPU 名称列表。"""
        gpu_combox_list = list(set(gpu_mapping.values()))
        gpu_combox_list.insert(0, self.tr("Auto"))
        gpu_combox_list.insert(1, self.tr("Disabled"))

        # 更新原始列表以供映射
        gpu_mapping[-1] = self.tr("Auto")
        gpu_mapping[-2] = self.tr("Disabled")

        return gpu_combox_list

    def update_check(self):
        if cfg.get(cfg.Project_url) != "":
            self.UpdateWorker.update_available.connect(self.ready_to_update)
            self.UpdateWorker.start()
            self.updateCard.clicked.disconnect()
            self.updateCard.button.setEnabled(False)
            self.updateCard.button.setText(self.tr("Checking for updates..."))
        else:
            InfoBar.warning(
                self.tr("Update failed"),
                self.tr("Please set the project URL first"),
                duration=2000,
                parent=self,
            )

    def ready_to_update(self, data_dict: dict):
        global update_dict
        update_dict = data_dict
        if data_dict == {}:
            InfoBar.warning(
                self.tr("Update failed"),
                self.tr("Please check your internet connection"),
                duration=2000,
                parent=self,
            )
            self.updateCard.button.setText(self.tr("Check for updates"))
            self.updateCard.button.setEnabled(True)
            self.updateCard.clicked.connect(self.update_check)

        elif data_dict["tag_name"] == cfg.get(cfg.Project_version):
            InfoBar.info(
                self.tr("No need to update"),
                self.tr("You are using the latest version"),
                duration=2000,
                parent=self,
            )
            self.updateCard.button.setText(self.tr("Check for updates"))
            self.updateCard.button.setEnabled(True)
            self.updateCard.clicked.connect(self.update_check)
        else:
            InfoBar.info(
                self.tr("Update available"),
                f"{self.tr('New version: ')}{data_dict['tag_name']}",
                duration=2000,
                parent=self,
            )
            self.updateCard.button.setEnabled(True)
            self.updateCard.button.setText(self.tr("Update"))
            self.updateCard.clicked.connect(self.update_now)
            self.Updatethread = Update(update_dict)
            self.Updatethread.update_finished.connect(self.on_update_finished)

    def update_now(self):
        self.Updatethread.start()
        self.updateCard.button.setEnabled(False)
        self.updateCard.button.setText(self.tr("Updating..."))

    def on_update_finished(self):
        InfoBar.success(
            self.tr("Update completed"),
            f"{self.tr('Successfully updated to')} {update_dict["tag_name"]}",
            duration=2000,
            parent=self,
        )
        self.updateCard.setContent(
            f"{self.tr('Current')} {cfg.get(cfg.Project_name)} {self.tr('version:')} {update_dict['tag_name']}"
        )
        self.updateCard.button.setText(self.tr("Check for updates"))
        self.updateCard.button.setEnabled(True)
        self.updateCard.clicked.connect(self.update_check)
        cfg.set(cfg.Project_version, update_dict["tag_name"])

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
        self.__connectSignalToSlot()

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
        # self.expandLayout.addWidget(self.noticeGroup)
        self.expandLayout.addWidget(self.DEVGroup)
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

    def __select_file(self, setting_card, config_key):
        """帮助方法，用于处理文件选择和设置内容。"""
        file_name, _ = QFileDialog.getOpenFileName(
            self, self.tr("Choose file"), "./", "All Files (*)"
        )
        if not file_name:
            return

        # 更新配置并设置卡片内容
        config_mapping = {
            "adb": lambda: Read_Config(cfg.get(cfg.Maa_config)).update(
                {"adb": {"adb_path": file_name}}
            ),
            "emu": lambda: cfg.set(cfg.emu_path, file_name),
            "exe": lambda: cfg.set(cfg.exe_path, file_name),
            "run_before": lambda: cfg.set(cfg.run_before_start, file_name),
            "run_after": lambda: cfg.set(cfg.run_after_finish, file_name),
        }
        config_mapping.get(config_key)()
        setting_card.setContent(file_name)

    def __connectSignalToSlot(self):
        """连接信号到对应的槽函数。"""
        cfg.appRestartSig.connect(self.__showRestartTooltip)

        # 连接 ADB 信号
        self.ADB_port.text_change.connect(self._onADB_portCardChange)
        self.ADB_path.clicked.connect(self.__onADBPathCardClicked)
        self.emu_path.clicked.connect(self.__onEmuPathCardClicked)

        # 连接 Win32 信号
        self.exe_path.clicked.connect(self.__onExePathCardClicked)

        # 连接启动信号
        self.run_before_start.clicked.connect(self.__onRunBeforeStartCardClicked)
        self.run_after_finish.clicked.connect(self.__onRunAfterFinishCardClicked)

        # 连接开发者模式信号
        self.DEVmodeCard.checkedChanged.connect(self._onDEVmodeCardChange)
        # 连接个性化信号
        cfg.themeChanged.connect(setTheme)
        self.themeColorCard.colorChanged.connect(lambda c: setThemeColor(c))
        self.micaCard.checkedChanged.connect(signalBus.micaEnableChanged)

        # 连接关于信号
        self.updateCard.clicked.connect(self.update_check)

        self.feedbackCard.clicked.connect(
            lambda: QDesktopServices.openUrl(
                QUrl(for_config_get_url(cfg.get(cfg.Project_url), "issue"))
            )
        )
        self.aboutCard.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(REPO_URL)))

    def _onADB_portCardChange(self):
        """根据端口更改更新 ADB 地址。"""
        port = self.ADB_port.lineEdit.text()
        full_ADB_address = f"127.0.0.1:{port}"
        data = Read_Config(cfg.get(cfg.Maa_config))
        data["adb"]["address"] = full_ADB_address
        Save_Config(cfg.get(cfg.Maa_config), data)

    def _onDEVmodeCardChange(self):
        """切换开发者模式的保存设置。"""
        state = self.DEVmodeCard.isChecked()
        data = Read_Config(cfg.get(cfg.Maa_dev))
        data["save_draw"] = state
        Save_Config(cfg.get(cfg.Maa_dev), data)

    def update_adb(self, msg):
        """根据外部消息更新 ADB 路径和端口。"""
        self.ADB_path.setContent(str(msg.adb_path))
        self.ADB_port.lineEdit.setText(f'{msg.address.split(":")[1]}')

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
