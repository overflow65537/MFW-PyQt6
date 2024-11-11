import os
import re

from qfluentwidgets import (
    SettingCardGroup, SwitchSettingCard, OptionsSettingCard, PrimaryPushSettingCard, ScrollArea,
    ComboBoxSettingCard, ExpandLayout, CustomColorSettingCard, setTheme, setThemeColor, ConfigItem
)
from qfluentwidgets import FluentIcon as FIF
from qfluentwidgets import InfoBar
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import QWidget, QLabel, QFileDialog

from ..common.config import (
    cfg, VERSION, UPDATE_URL, FEEDBACK_URL, REPO_URL, isWin11
)
from ..common.signal_bus import signalBus
from ..common.style_sheet import StyleSheet
from ..components.line_edit_card import LineEditCard
from ..components.combobox_setting_card_custom import ComboBoxSettingCardCustom
from ..components.notic_setting_card import NoticeButtonSettingCard
from ..utils.tool import Read_Config, Save_Config, get_gpu_info


class SettingInterface(ScrollArea):
    """Setting interface for configuring application settings."""

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.scrollWidget = QWidget()
        self.expandLayout = ExpandLayout(self.scrollWidget)
        signalBus.update_adb.connect(self.update_adb)

        self.settingLabel = QLabel(self.tr("Settings"), self)

        # Initialize settings
        self.initialize_adb_settings()
        self.initialize_win32_settings()
        self.initialize_start_settings()
        self.initialize_personalization_settings()
        self.initialize_notice_settings()
        self.initialize_dev_settings()
        self.initialize_about_settings()

        self.__initWidget()

    def initialize_adb_settings(self):
        """Initialize ADB settings."""
        self.ADB_Setting = SettingCardGroup(self.tr("ADB"), self.scrollWidget)
        
        # Read ADB configuration
        pi_config = Read_Config(cfg.get(cfg.Maa_config)) if os.path.exists(cfg.get(cfg.Maa_config)) else {}
        address_data = pi_config.get("adb", {}).get("address", "0")
        Port_data = address_data.split(":")[1] if re.match(r"^(\d{1,3}\.){3}\d{1,3}:\d{1,5}$", address_data) else "0"
        path_data = pi_config.get("adb", {}).get("adb_path", "./")

        self.ADB_port = LineEditCard(
            icon=FIF.COMMAND_PROMPT,
            holderText=Port_data,
            title=self.tr("ADB 端口"),
            parent=self.ADB_Setting,
        )
        self.ADB_path = PrimaryPushSettingCard(
            self.tr("选择 ADB 路径"),
            FIF.COMMAND_PROMPT,
            self.tr("ADB 路径"),
            path_data,
            self.ADB_Setting,
        )
        self.emu_path = PrimaryPushSettingCard(
            self.tr("选择模拟器路径"),
            FIF.COMMAND_PROMPT,
            self.tr("模拟器路径"),
            cfg.get(cfg.emu_path),
            self.ADB_Setting,
        )
        self.emu_wait_time = LineEditCard(
            icon=FIF.COMMAND_PROMPT,
            configItem=cfg.emu_wait_time,
            title=self.tr("等待模拟器启动时间"),
            parent=self.ADB_Setting,
        )

        self.ADB_Setting.addSettingCard(self.ADB_port)
        self.ADB_Setting.addSettingCard(self.ADB_path)
        self.ADB_Setting.addSettingCard(self.emu_path)
        self.ADB_Setting.addSettingCard(self.emu_wait_time)

    def initialize_win32_settings(self):
        """Initialize Win32 settings."""
        self.Win32_Setting = SettingCardGroup(self.tr("Win32"), self.scrollWidget)

        self.exe_path = PrimaryPushSettingCard(
            self.tr("选择启动程序路径"),
            FIF.COMMAND_PROMPT,
            self.tr("启动程序路径"),
            cfg.get(cfg.exe_path),
            self.Win32_Setting,
        )
        self.exe_parameter = LineEditCard(
            icon=FIF.COMMAND_PROMPT,
            configItem=cfg.exe_parameter,
            title=self.tr("运行参数"),
            num_only=False,
            parent=self.Win32_Setting,
        )
        self.exe_wait_time = LineEditCard(
            icon=FIF.COMMAND_PROMPT,
            configItem=cfg.exe_wait_time,
            title=self.tr("等待程序启动时间"),
            parent=self.Win32_Setting,
        )

        self.Win32_Setting.addSettingCard(self.exe_path)
        self.Win32_Setting.addSettingCard(self.exe_parameter)
        self.Win32_Setting.addSettingCard(self.exe_wait_time)

    def initialize_start_settings(self):
        """Initialize startup settings."""
        self.start_Setting = SettingCardGroup(self.tr("自定义启动"), self.scrollWidget)
        
        self.run_before_start = PrimaryPushSettingCard(
            self.tr("选择程序"),
            FIF.COMMAND_PROMPT,
            self.tr("启动前运行程序"),
            cfg.get(cfg.run_before_start),
            self.start_Setting,
        )
        self.run_after_finish = PrimaryPushSettingCard(
            self.tr("选择程序"),
            FIF.COMMAND_PROMPT,
            self.tr("完成后运行程序"),
            cfg.get(cfg.run_after_finish),
            self.start_Setting,
        )

        self.start_Setting.addSettingCard(self.run_before_start)
        self.start_Setting.addSettingCard(self.run_after_finish)

    def initialize_personalization_settings(self):
        """Initialize personalization settings."""
        self.personalGroup = SettingCardGroup(self.tr("Personalization"), self.scrollWidget)

        self.micaCard = SwitchSettingCard(
            FIF.TRANSPARENT,
            self.tr("Mica effect"),
            self.tr("Apply semi transparent to windows and surfaces"),
            cfg.micaEnabled,
            self.personalGroup,
        )
        self.themeCard = OptionsSettingCard(
            cfg.themeMode,
            FIF.BRUSH,
            self.tr("Application theme"),
            self.tr("Change the appearance of your application"),
            texts=[self.tr("Light"), self.tr("Dark"), self.tr("Use system setting")],
            parent=self.personalGroup,
        )
        self.themeColorCard = CustomColorSettingCard(
            cfg.themeColor,
            FIF.PALETTE,
            self.tr("Theme color"),
            self.tr("Change the theme color of your application"),
            self.personalGroup,
        )
        self.zoomCard = OptionsSettingCard(
            cfg.dpiScale,
            FIF.ZOOM,
            self.tr("Interface zoom"),
            self.tr("Change the size of widgets and fonts"),
            texts=["100%", "125%", "150%", "175%", "200%", self.tr("Use system setting")],
            parent=self.personalGroup,
        )
        self.languageCard = ComboBoxSettingCard(
            cfg.language,
            FIF.LANGUAGE,
            self.tr("Language"),
            self.tr("Set your preferred language for UI"),
            texts=["简体中文", "繁體中文", "English", self.tr("Use system setting")],
            parent=self.personalGroup,
        )

        self.personalGroup.addSettingCard(self.micaCard)
        self.personalGroup.addSettingCard(self.themeCard)
        self.personalGroup.addSettingCard(self.themeColorCard)
        self.personalGroup.addSettingCard(self.zoomCard)
        self.personalGroup.addSettingCard(self.languageCard)

    def initialize_notice_settings(self):
        """Initialize external notice settings."""
        self.noticeGroup = SettingCardGroup(self.tr("Notice"), self.scrollWidget)

        self.dingtalk_noticeTypeCard = NoticeButtonSettingCard(
            self.tr("Modify"),
            FIF.COMMAND_PROMPT,
            self.tr("DingTalk"),
            "DingTalk",
            "DingTalk Configuration",
            self.noticeGroup,
        )

        self.lark_noticeTypeCard = NoticeButtonSettingCard(
            self.tr("Modify"),
            FIF.COMMAND_PROMPT,
            self.tr("Lark"),
            "Lark",
            "Lark Configuration",
            self.noticeGroup,
        )

        self.qmsg_noticeTypeCard = NoticeButtonSettingCard(
            self.tr("Modify"),
            FIF.COMMAND_PROMPT,
            self.tr("Qmsg"),
            "Qmsg",
            "Qmsg Configuration",
            self.noticeGroup,
        )

        self.SMTP_noticeTypeCard = NoticeButtonSettingCard(
            self.tr("Modify"),
            FIF.COMMAND_PROMPT,
            self.tr("SMTP"),
            "SMTP",
            "SMTP Configuration",
            self.noticeGroup,
        )

        self.noticeGroup.addSettingCard(self.dingtalk_noticeTypeCard)
        self.noticeGroup.addSettingCard(self.lark_noticeTypeCard)
        self.noticeGroup.addSettingCard(self.qmsg_noticeTypeCard)
        self.noticeGroup.addSettingCard(self.SMTP_noticeTypeCard)

    def initialize_dev_settings(self):
        """Initialize developer settings."""
        self.DEVGroup = SettingCardGroup(self.tr("DEV Mode"), self.scrollWidget)

        # Setup DEV Config
        DEV_Config = self.check_and_get_dev_config()

        gpu_list = get_gpu_info()
        gpu_combox_list = self.get_unique_gpu_list(gpu_list)

        win32_input_mapping = {0: self.tr("default"), 1: "seize", 2: "SendMessage"}
        win32_input_combox_list = [self.tr("default"), "seize", "SendMessage"]

        win32_screencap_mapping = {0: self.tr("default"), 1: "GDI", 2: "FramePool", 4: "DXGI_DesktopDup"}
        win32_screencap_combox_list = [self.tr("default"), "GDI", "FramePool", "DXGI_DesktopDup"]

        ADB_input_mapping = {0: self.tr("default"), 1: "AdbShellL", 2: "MinitouchAndAdbKey", 4: "Maatouch", 8: "EmulatorExtras"}
        ADB_input_combox_list = [self.tr("default"), "AdbShell", "MinitouchAndAdbKey", "Maatouch", "EmulatorExtras"]

        ADB_screencap_mapping = {0: self.tr("default"), 1: "EncodeToFileAndPull", 2: "Encode", 4: "RawWithGzip", 8: "RawByNetcat", 16: "MinicapDirect", 32: "MinicapStream", 64: "EmulatorExtras"}
        ADB_screencap_combox_list = [self.tr("default"), "EncodeToFileAndPull", "Encode", "RawWithGzip", "RawByNetcat", "MinicapDirect", "MinicapStream", "EmulatorExtras"]

        self.use_GPU = ComboBoxSettingCardCustom(
            icon=FIF.FILTER,
            title=self.tr("Select GPU"),
            content=self.tr("Use GPU to accelerate inference"),
            texts=gpu_combox_list,
            target=["gpu"],
            path=cfg.get(cfg.Maa_config),
            parent=self.DEVGroup,
            mode="setting",
            mapping=gpu_list,
        )
        
        self.win32_input_mode = ComboBoxSettingCardCustom(
            icon=FIF.FILTER,
            title=self.tr("Select Win32 Input Mode"),
            texts=win32_input_combox_list,
            path=cfg.get(cfg.Maa_interface),
            parent=self.DEVGroup,
            mode="interface_setting",
            controller="Win32",
            controller_type="input",
            mapping=win32_input_mapping,
        )

        self.win32_screencap_mode = ComboBoxSettingCardCustom(
            icon=FIF.FILTER,
            title=self.tr("Select Win32 Screencap Mode"),
            texts=win32_screencap_combox_list,
            path=cfg.get(cfg.Maa_interface),
            parent=self.DEVGroup,
            mode="interface_setting",
            controller="Win32",
            controller_type="screencap",
            mapping=win32_screencap_mapping,
        )

        self.ADB_input_mode = ComboBoxSettingCardCustom(
            icon=FIF.FILTER,
            title=self.tr("Select ADB Input Mode"),
            texts=ADB_input_combox_list,
            path=cfg.get(cfg.Maa_interface),
            parent=self.DEVGroup,
            mode="interface_setting",
            controller="Adb",
            controller_type="input",
            mapping=ADB_input_mapping,
        )

        self.ADB_screencap_mode = ComboBoxSettingCardCustom(
            icon=FIF.FILTER,
            title=self.tr("Select ADB Screencap Mode"),
            texts=ADB_screencap_combox_list,
            path=cfg.get(cfg.Maa_interface),
            parent=self.DEVGroup,
            mode="interface_setting",
            controller="Adb",
            controller_type="screencap",
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
        """Initialize about settings."""
        self.aboutGroup = SettingCardGroup(self.tr("About"), self.scrollWidget)

        self.updateCard = PrimaryPushSettingCard(
            self.tr("Check for updates"),
            FIF.UPDATE,
            self.tr("Check for updates"),
            self.tr(f"Current PyQt-MAA version: {VERSION}"),
            self.aboutGroup,
        )
        self.feedbackCard = PrimaryPushSettingCard(
            self.tr("Submit Feedback"),
            FIF.FEEDBACK,
            self.tr("Submit Feedback"),
            self.tr("Submit feedback to help us improve PyQt-MAA"),
            self.aboutGroup,
        )
        self.aboutCard = PrimaryPushSettingCard(
            self.tr("About Us"),
            FIF.INFO,
            self.tr("About"),
            "PyQt-MAA is open source under the GPLv3 license. Visit the project URL for more information.",
            self.aboutGroup,
        )

        self.aboutGroup.addSettingCard(self.updateCard)
        self.aboutGroup.addSettingCard(self.feedbackCard)
        self.aboutGroup.addSettingCard(self.aboutCard)

    def check_and_get_dev_config(self):
        """Check and retrieve DEV configuration."""
        if os.path.exists(cfg.get(cfg.Maa_dev)):
            return Read_Config(cfg.get(cfg.Maa_dev))["save_draw"]
        else:
            Save_Config(cfg.get(cfg.Maa_dev), {
                "logging": True,
                "recording": False,
                "save_draw": False,
                "show_hit_draw": False,
                "stdout_level": 2,
            })
            return False

    def get_unique_gpu_list(self, gpu_list):
        """Get a unique list of GPU names."""
        gpu_combox_list = list(set(gpu_list.values()))
        gpu_combox_list.insert(0, self.tr("Auto"))
        gpu_combox_list.insert(1, self.tr("Disabled"))
        
        # Update the original list for mapping
        gpu_list[-1] = self.tr("Auto")
        gpu_list[-2] = self.tr("Disabled")
        
        return gpu_combox_list

    def __initWidget(self):
        self.resize(1000, 800)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setViewportMargins(0, 80, 0, 20)
        self.setWidget(self.scrollWidget)
        self.setWidgetResizable(True)
        self.setObjectName("settingInterface")

        # Initialize style sheet
        self.scrollWidget.setObjectName("scrollWidget")
        self.settingLabel.setObjectName("settingLabel")
        StyleSheet.SETTING_INTERFACE.apply(self)

        self.micaCard.setEnabled(isWin11())

        # Initialize layout
        self.__initLayout()
        self.__connectSignalToSlot()

    def __initLayout(self):
        """Initialize layout for setting cards."""
        self.settingLabel.move(36, 30)

        # Add card groups to layout
        self.expandLayout.setSpacing(28)
        self.expandLayout.setContentsMargins(36, 10, 36, 0)
        self.expandLayout.addWidget(self.ADB_Setting)
        self.expandLayout.addWidget(self.Win32_Setting)
        self.expandLayout.addWidget(self.start_Setting)
        self.expandLayout.addWidget(self.personalGroup)
        self.expandLayout.addWidget(self.noticeGroup)
        self.expandLayout.addWidget(self.DEVGroup)
        self.expandLayout.addWidget(self.aboutGroup)

        # Enable/disable controls based on existing paths
        self.emu_wait_time.setEnabled(cfg.get(cfg.emu_path) != "")
        self.exe_parameter.setEnabled(cfg.get(cfg.exe_path) != "")
        self.exe_wait_time.setEnabled(cfg.get(cfg.exe_path) != "")

    def __showRestartTooltip(self):
        """Show restart tooltip."""
        InfoBar.success(
            self.tr("Updated successfully"),
            self.tr("Configuration takes effect after restart"),
            duration=1500,
            parent=self,
        )

    def __onADBPathCardClicked(self):
        """Manually choose the ADB.exe location."""
        self.__select_file(self.ADB_path, "adb")

    def __onEmuPathCardClicked(self):
        """Manually choose the emulator location."""
        self.__select_file(self.emu_path, "emu")

    def __onExePathCardClicked(self):
        """Manually choose the executable path."""
        self.__select_file(self.exe_path, "exe")

    def __onRunBeforeStartCardClicked(self):
        """Manually choose the script to run before launching."""
        self.__select_file(self.run_before_start, "run_before")

    def __onRunAfterFinishCardClicked(self):
        """Manually choose the script to run after finishing."""
        self.__select_file(self.run_after_finish, "run_after")

    def __select_file(self, setting_card, config_key):
        """Helper method to handle file selection and setting content."""
        file_name, _ = QFileDialog.getOpenFileName(
            self, self.tr("Choose file"), "./", self.tr("All Files (*)")
        )
        if not file_name:
            return

        # Update configuration and set the card content
        config_mapping = {
            "adb": lambda: Read_Config(cfg.get(cfg.Maa_config)).update({"adb": {"adb_path": file_name}}),
            "emu": lambda: cfg.set(cfg.emu_path, file_name),
            "exe": lambda: cfg.set(cfg.exe_path, file_name),
            "run_before": lambda: cfg.set(cfg.run_before_start, file_name),
            "run_after": lambda: cfg.set(cfg.run_after_finish, file_name),
        }
        config_mapping.get(config_key)()
        setting_card.setContent(file_name)

    def __connectSignalToSlot(self):
        """Connect signals to corresponding slots."""
        cfg.appRestartSig.connect(self.__showRestartTooltip)

        # Connect ADB signals
        self.ADB_port.text_change.connect(self._onADB_portCardChange)
        self.ADB_path.clicked.connect(self.__onADBPathCardClicked)
        self.emu_path.clicked.connect(self.__onEmuPathCardClicked)

        # Connect Win32 signals
        self.exe_path.clicked.connect(self.__onExePathCardClicked)

        # Connect startup signals
        self.run_before_start.clicked.connect(self.__onRunBeforeStartCardClicked)
        self.run_after_finish.clicked.connect(self.__onRunAfterFinishCardClicked)

        # Connect dev mode signals
        self.DEVmodeCard.checkedChanged.connect(self._onDEVmodeCardChange)
        # Connect personalization signals
        cfg.themeChanged.connect(setTheme)
        self.themeColorCard.colorChanged.connect(lambda c: setThemeColor(c))
        self.micaCard.checkedChanged.connect(signalBus.micaEnableChanged)

        # Connect about signals
        self.updateCard.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(UPDATE_URL)))
        self.feedbackCard.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(FEEDBACK_URL)))
        self.aboutCard.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(REPO_URL)))

    def _onADB_portCardChange(self):
        """Update ADB address based on port change."""
        port = self.ADB_port.lineEdit.text()
        full_ADB_address = f"127.0.0.1:{port}"
        data = Read_Config(cfg.get(cfg.Maa_config))
        data["adb"]["address"] = full_ADB_address
        Save_Config(cfg.get(cfg.Maa_config), data)

    def _onDEVmodeCardChange(self):
        """Toggle DEV mode saving."""
        state = self.DEVmodeCard.isChecked()
        data = Read_Config(cfg.get(cfg.Maa_dev))
        data["save_draw"] = state
        Save_Config(cfg.get(cfg.Maa_dev), data)

    def update_adb(self, msg):
        """Update ADB path and port based on external message."""
        self.ADB_path.setContent(msg["adb_path"])
        self.ADB_port.lineEdit.setText(f'{msg["address"].split(":")[1]}')

    def Switch_Controller(self, controller):
        """Switch between ADB and Win32 controller settings."""
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
