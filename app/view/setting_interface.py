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

from ..common.config import (
    cfg,
    VERSION,
    UPDATE_URL,
    FEEDBACK_URL,
    REPO_URL,
    isWin11,
)
from ..common.signal_bus import signalBus
from ..common.style_sheet import StyleSheet
from ..components.line_edit_card import LineEditCard
from ..components.combobox_setting_card_custom import ComboBoxSettingCardCustom
from ..utils.tool import Read_Config, Save_Config, get_gpu_info, access_nested_dict


class SettingInterface(ScrollArea):
    """Setting interface"""

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.scrollWidget = QWidget()
        self.expandLayout = ExpandLayout(self.scrollWidget)
        signalBus.update_adb.connect(self.update_adb)

        # setting label
        self.settingLabel = QLabel(self.tr("Settings"), self)

        # ADB设备设置

        if os.path.exists(cfg.get(cfg.Maa_config)):
            pi_config = Read_Config(cfg.get(cfg.Maa_config))
            address_data = pi_config["adb"]["address"]
            if re.match(r"^(\d{1,3}\.){3}\d{1,3}:\d{1,5}$", address_data):
                Port_data = address_data.split(":")[1]
            else:
                Port_data = "0"
            path_data = pi_config["adb"]["adb_path"]
        else:
            Port_data = "0"
            path_data = "./"

        self.ADB_Setting = SettingCardGroup(self.tr("ADB"), self.scrollWidget)
        self.ADB_port = LineEditCard(
            FIF.COMMAND_PROMPT,
            Port_data,
            title=self.tr("ADB 端口"),  # TODO:i18n
            parent=self.ADB_Setting,
        )
        self.ADB_path = PrimaryPushSettingCard(
            self.tr("选择 ADB 路径"),  # TODO:i18n
            FIF.COMMAND_PROMPT,
            self.tr("ADB 路径"),
            f"当前路径：{path_data}",
            self.ADB_Setting,
        )
        self.emu_path = PrimaryPushSettingCard(
            self.tr("选择模拟器路径"),  # TODO:i18n
            FIF.COMMAND_PROMPT,
            self.tr("模拟器路径"),
            f"当前路径：{cfg.get(cfg.emu_path)}",
            self.ADB_Setting,
        )
        self.emu_wait_time = LineEditCard(
            FIF.COMMAND_PROMPT,
            cfg.get(cfg.emu_wait_time),
            title=self.tr("等待模拟器启动时间"),  # TODO:i18n
            parent=self.ADB_Setting,
        )
        # win32程序
        self.Win32_Setting = SettingCardGroup(self.tr("Win32"), self.scrollWidget)
        self.exe_path = PrimaryPushSettingCard(
            self.tr("选择启动程序路径"),  # TODO:i18n
            FIF.COMMAND_PROMPT,
            self.tr("启动程序路径"),
            f"当前路径：{cfg.get(cfg.exe_path)}",
            self.Win32_Setting,
        )
        self.exe_parameter = LineEditCard(
            FIF.COMMAND_PROMPT,
            cfg.get(cfg.exe_parameter),
            title=self.tr("运行参数"),  # TODO:i18n
            parent=self.Win32_Setting,
        )
        self.exe_wait_time = LineEditCard(
            FIF.COMMAND_PROMPT,
            cfg.get(cfg.exe_wait_time),
            title=self.tr("等待程序启动时间"),  # TODO:i18n
            parent=self.Win32_Setting,
        )
        # 启动设置
        self.start_Setting = SettingCardGroup(self.tr("自定义启动"), self.scrollWidget)
        self.run_before_start = PrimaryPushSettingCard(
            self.tr("选择程序"),  # TODO:i18n
            FIF.COMMAND_PROMPT,
            self.tr("启动前运行程序"),
            f"当前路径：{cfg.get(cfg.run_before_start)}",
            self.start_Setting,
        )
        self.run_after_finish = PrimaryPushSettingCard(
            self.tr("选择程序"),  # TODO:i18n
            FIF.COMMAND_PROMPT,
            self.tr("完成后运行程序"),
            f"当前路径：{cfg.get(cfg.run_after_finish)}",
            self.start_Setting,
        )
        # 个性化
        self.personalGroup = SettingCardGroup(
            self.tr("Personalization"), self.scrollWidget
        )
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
            self.tr("Change the theme color of you application"),
            self.personalGroup,
        )
        self.zoomCard = OptionsSettingCard(
            cfg.dpiScale,
            FIF.ZOOM,
            self.tr("Interface zoom"),
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
            texts=["简体中文", "繁體中文", "English", self.tr("Use system setting")],
            parent=self.personalGroup,
        )

        # 保存截图
        if os.path.exists(cfg.get(cfg.Maa_dev)):
            DEV_Config = Read_Config(cfg.get(cfg.Maa_dev))["save_draw"]
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
            DEV_Config = False
        # GPU设置
        gpu_list = get_gpu_info()

        gpu_combox_list = list(set(gpu_list.values()))
        gpu_combox_list.insert(0, self.tr("Auto"))
        gpu_combox_list.insert(1, self.tr("disabeld"))
        gpu_list["-1"] = self.tr("Auto")
        gpu_list["-2"] = self.tr("disabeld")
        # win32输入模式
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
        # win32截图模式
        win32_screencap_mapping = {
            0: self.tr("default"),
            1: "GDI",
            2: "FramePool",
            4: "DXGI_DesktopDup",
        }
        win32_screencap_combox_list = [
            self.tr("default"),
            "GDI",
            "FramePool",
            "DXGI_DesktopDup",
        ]
        # ADB输入模式
        ADB_input_mapping = {
            0: self.tr("default"),
            1: "AdbShellL",
            2: "MinitouchAndAdbKey",
            4: "Maatouch",
            8: "EmulatorExtras",
        }
        ADB_input_combox_list = [
            self.tr("default"),
            "AdbShell",
            "MinitouchAndAdbKey",
            "Maatouch",
            "EmulatorExtras",
        ]
        # ADB截图模式
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
        ADB_screencap_combox_list = [
            self.tr("default"),
            "EncodeToFileAndPull",
            "Encode",
            "RawWithGzip",
            "RawByNetcat",
            "MinicapDirect",
            "MinicapStream",
            "EmulatorExtras",
        ]

        self.DEVGroup = SettingCardGroup(self.tr("DEV Mode"), self.scrollWidget)

        self.use_GPU = ComboBoxSettingCardCustom(
            icon=FIF.FILTER,
            title=self.tr("select GPU"),
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
            title=self.tr("select win32 input mode"),
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
            title=self.tr("select win32 screencap mode"),
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
            title=self.tr("select Adb input mode"),
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
            title=self.tr("select Adb screencap mode"),
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
            self.tr(
                "When the DEV Mode is enabled,screenshots will be saved in ./debug/vision"
            ),
            configItem=ConfigItem(group="DEV", name="DEV", default=DEV_Config),
            parent=self.DEVGroup,
        )

        # application
        self.aboutGroup = SettingCardGroup(self.tr("About"), self.scrollWidget)
        self.updateCard = PrimaryPushSettingCard(
            self.tr("检查更新"),  # TODO:i18n
            FIF.UPDATE,
            self.tr("检查更新"),
            self.tr(f"当前 PyQt-MAA 版本：{VERSION}"),
            self.aboutGroup,
        )
        self.feedbackCard = PrimaryPushSettingCard(
            self.tr("提交反馈"),  # TODO:i18n
            FIF.FEEDBACK,
            self.tr("提交反馈"),
            self.tr("提交反馈以帮助我们改进 PyQt-MAA"),
            self.aboutGroup,
        )
        self.aboutCard = PrimaryPushSettingCard(
            self.tr("关于我们"),  # TODO:i18n
            FIF.INFO,
            self.tr("关于"),
            "PyQt-MAA 使用 GPLv3 许可证进行开源，访问项目地址以获取源码与更多信息",
            self.aboutGroup,
        )

        self.__initWidget()

    def __initWidget(self):
        self.resize(1000, 800)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setViewportMargins(0, 80, 0, 20)
        self.setWidget(self.scrollWidget)
        self.setWidgetResizable(True)
        self.setObjectName("settingInterface")

        # initialize style sheet
        self.scrollWidget.setObjectName("scrollWidget")
        self.settingLabel.setObjectName("settingLabel")
        StyleSheet.SETTING_INTERFACE.apply(self)

        self.micaCard.setEnabled(isWin11())

        # initialize layout
        self.__initLayout()
        self.__connectSignalToSlot()

    def __initLayout(self):
        self.settingLabel.move(36, 30)

        # add cards to group
        self.ADB_Setting.addSettingCard(self.ADB_port)
        self.ADB_Setting.addSettingCard(self.ADB_path)
        self.ADB_Setting.addSettingCard(self.emu_path)
        self.ADB_Setting.addSettingCard(self.emu_wait_time)

        self.Win32_Setting.addSettingCard(self.exe_path)
        self.Win32_Setting.addSettingCard(self.exe_parameter)
        self.Win32_Setting.addSettingCard(self.exe_wait_time)

        self.start_Setting.addSettingCard(self.run_before_start)
        self.start_Setting.addSettingCard(self.run_after_finish)

        self.personalGroup.addSettingCard(self.micaCard)
        self.personalGroup.addSettingCard(self.themeCard)
        self.personalGroup.addSettingCard(self.themeColorCard)
        self.personalGroup.addSettingCard(self.zoomCard)
        self.personalGroup.addSettingCard(self.languageCard)

        self.DEVGroup.addSettingCard(self.DEVmodeCard)
        self.DEVGroup.addSettingCard(self.use_GPU)
        self.DEVGroup.addSettingCard(self.win32_input_mode)
        self.DEVGroup.addSettingCard(self.win32_screencap_mode)
        self.DEVGroup.addSettingCard(self.ADB_input_mode)
        self.DEVGroup.addSettingCard(self.ADB_screencap_mode)

        self.aboutGroup.addSettingCard(self.updateCard)
        self.aboutGroup.addSettingCard(self.feedbackCard)
        self.aboutGroup.addSettingCard(self.aboutCard)

        # add setting card group to layout
        self.expandLayout.setSpacing(28)
        self.expandLayout.setContentsMargins(36, 10, 36, 0)
        self.expandLayout.addWidget(self.ADB_Setting)
        self.expandLayout.addWidget(self.Win32_Setting)
        self.expandLayout.addWidget(self.start_Setting)
        self.expandLayout.addWidget(self.personalGroup)
        self.expandLayout.addWidget(self.DEVGroup)
        self.expandLayout.addWidget(self.aboutGroup)

        # 检查模拟器路径是否填写
        if cfg.get(cfg.emu_path) == "":
            self.emu_wait_time.setEnabled(False)

        # 检查启动程序路径是否填写
        if cfg.get(cfg.exe_path) == "":
            self.exe_parameter.setEnabled(False)
            self.exe_wait_time.setEnabled(False)

    def __showRestartTooltip(self):
        """show restart tooltip"""
        InfoBar.success(
            self.tr("Updated successfully"),
            self.tr("Configuration takes effect after restart"),
            duration=1500,
            parent=self,
        )

    def __onADBPathCardClicked(self):
        """手动选择ADB.exe位置"""
        file_name, _ = QFileDialog.getOpenFileName(
            self, self.tr("Choose file"), "./", self.tr("All Files (*);;All Files (*)")
        )
        if not file_name:
            return

        data = Read_Config(cfg.get(cfg.Maa_config))
        data["adb"]["adb_path"] = file_name
        Save_Config(cfg.get(cfg.Maa_config), data)
        self.ADB_path.setContent(file_name)

    def __onEmuPathCardClicked(self):
        """手动选择模拟器位置"""
        file_name, _ = QFileDialog.getOpenFileName(
            self, self.tr("Choose file"), "./", self.tr("All Files (*);;All Files (*)")
        )
        if not file_name:
            return

        cfg.set(cfg.emu_path, file_name)
        self.emu_path.setContent(file_name)
        self.emu_wait_time.setEnabled(True)

    def __onExePathCardClicked(self):
        """手动选择启动程序位置"""
        file_name, _ = QFileDialog.getOpenFileName(
            self, self.tr("Choose file"), "./", self.tr("All Files (*);;All Files (*)")
        )
        if not file_name:
            return

        cfg.set(cfg.exe_path, file_name)
        self.exe_path.setContent(file_name)
        self.exe_parameter.setEnabled(True)
        self.exe_wait_time.setEnabled(True)

    def __onRunBeforeStartCardClicked(self):
        """手动选择启动前运行脚本位置"""
        file_name, _ = QFileDialog.getOpenFileName(
            self, self.tr("Choose file"), "./", self.tr("All Files (*);;All Files (*)")
        )
        if not file_name:
            return

        cfg.set(cfg.run_before_start, file_name)
        self.run_before_start.setContent(file_name)

    def __onRunAfterFinishCardClicked(self):
        """手动选择启动后运行脚本位置"""
        file_name, _ = QFileDialog.getOpenFileName(
            self, self.tr("Choose file"), "./", self.tr("All Files (*);;All Files (*)")
        )
        if not file_name:
            return

        cfg.set(cfg.run_after_finish, file_name)
        self.run_after_finish.setContent(file_name)

    def __connectSignalToSlot(self):
        """connect signal to slot"""
        cfg.appRestartSig.connect(self.__showRestartTooltip)

        # ADB信号
        self.ADB_port.text_change.connect(self._onADB_portCardChange)
        self.ADB_path.clicked.connect(self.__onADBPathCardClicked)
        self.emu_path.clicked.connect(self.__onEmuPathCardClicked)

        # Win32信号
        self.exe_path.clicked.connect(self.__onExePathCardClicked)

        # 启动信号
        self.run_before_start.clicked.connect(self.__onRunBeforeStartCardClicked)
        self.run_after_finish.clicked.connect(self.__onRunAfterFinishCardClicked)

        # 调试信号
        self.DEVmodeCard.checkedChanged.connect(self._onDEVmodeCardChange)
        # personalization
        cfg.themeChanged.connect(setTheme)
        self.themeColorCard.colorChanged.connect(lambda c: setThemeColor(c))
        self.micaCard.checkedChanged.connect(signalBus.micaEnableChanged)

        # about
        self.updateCard.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl(UPDATE_URL))
        )
        self.feedbackCard.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl(FEEDBACK_URL))
        )
        self.aboutCard.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(REPO_URL)))

    def _onADB_portCardChange(self):
        port = self.ADB_port.lineEdit.text()
        full_ADB_address = f"127.0.0.1:{port}"
        data = Read_Config(cfg.get(cfg.Maa_config))
        data["adb"]["address"] = full_ADB_address
        Save_Config(cfg.get(cfg.Maa_config), data)

    def _onDEVmodeCardChange(self):
        state = self.DEVmodeCard.isChecked()
        data = Read_Config(cfg.get(cfg.Maa_dev))
        data["save_draw"] = state
        Save_Config(cfg.get(cfg.Maa_dev), data)

    def update_adb(self, msg):
        self.ADB_path.setContent(msg["path"])
        self.ADB_port.lineEdit.setText(f'{msg["port"].split(":")[1]}')

    def Switch_Controller(self, controller):
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
