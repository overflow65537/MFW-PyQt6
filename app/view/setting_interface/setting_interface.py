"""
MFW-ChainFlow Assistant
MFW-ChainFlow Assistant 设置界面
作者:overflow65537
"""

from typing import Optional

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QFrame, QSizePolicy, QVBoxLayout, QWidget
from qfluentwidgets import (
    BodyLabel,
    ComboBoxSettingCard,
    CustomColorSettingCard,
    ExpandLayout,
    FluentIcon as FIF,
    InfoBar,
    OptionsSettingCard,
    PrimaryPushSettingCard,
    ScrollArea,
    SettingCardGroup,
    SwitchSettingCard,
    setTheme,
    setThemeColor,
)

from app.common.__version__ import __version__
from app.common.config import cfg, REPO_URL, isWin11
from app.common.signal_bus import signalBus
from app.core.core import ServiceCoordinator
from app.utils.logger import logger
from app.view.setting_interface.widget.DoubleButtonSettingCard import (
    DoubleButtonSettingCard,
)


class SettingInterface(QWidget):
    """
    设置界面，用于配置应用程序设置，主体以滚动区域 + ExpandLayout。
    """

    def __init__(
        self,
        service_coordinator: Optional[ServiceCoordinator] = None,
        parent=None,
    ):
        super().__init__(parent=parent)
        self.setObjectName("settingInterface")
        self._service_coordinator = service_coordinator
        self.project_name = ""
        self.project_version = ""
        self.project_url = ""
        self.Setting_scroll_widget = QWidget()
        self.Setting_expand_layout = ExpandLayout(self.Setting_scroll_widget)
        self.scroll_area = ScrollArea(self)
        self._setup_ui()

    def _setup_ui(self):
        """搭建整体结构：标题 + 滚动区域 + ExpandLayout + 底部留白。"""
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(24, 24, 24, 0)
        self.main_layout.setSpacing(8)

        self.title_label = BodyLabel(self.tr("Settings"), self)
        self.title_label.setStyleSheet("font-size: 24px; font-weight: 600;")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.main_layout.addWidget(self.title_label)

        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setStyleSheet("background-color: transparent; border: none;")
        self.scroll_area.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.scroll_area.setWidget(self.Setting_scroll_widget)

        self.Setting_expand_layout.setSpacing(28)
        self.Setting_expand_layout.setContentsMargins(24, 24, 24, 24)

        self.initialize_start_settings()
        self.initialize_personalization_settings()
        self.initialize_notice_settings()
        self.initialize_advanced_settings()
        self.initialize_about_settings()

        self.main_layout.addWidget(self.scroll_area)
        self.main_layout.setStretch(1, 1)

        self.bottom_label = BodyLabel("", self)
        self.bottom_label.setFixedHeight(10)
        self.bottom_label.setStyleSheet("background-color: transparent;")
        self.main_layout.addWidget(self.bottom_label)

        self.init_info()
        self.__connectSignalToSlot()
        self.setup_updater_interface()
        self._apply_theme_from_config()
        self._apply_interface_font()
        self.micaCard.setEnabled(isWin11())

    def add_setting_group(self, group_widget: QWidget):
        """
        向 ExpandLayout 插入设置卡片组。
        """
        self.Setting_expand_layout.addWidget(group_widget)

    def initialize_start_settings(self):
        """构建启动设置组，与旧版保持一致的外层包裹。"""
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
        self.add_setting_group(self.start_Setting)

    def initialize_personalization_settings(self):
        """构建个性化设置组。"""
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
        self.add_setting_group(self.personalGroup)

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
        self.add_setting_group(self.noticeGroup)

    def initialize_advanced_settings(self):
        """初始化高级设置。"""
        self.advancedGroup = SettingCardGroup(
            self.tr("Advanced"), self.Setting_scroll_widget
        )
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

        self.RecordingCard.switchButton.checkedChanged.connect(
            lambda: signalBus.title_changed.emit()
        )
        self.SaveDrawCard.switchButton.checkedChanged.connect(
            lambda: signalBus.title_changed.emit()
        )

        self.add_setting_group(self.advancedGroup)


    def initialize_about_settings(self):
        """初始化关于设置。"""
        MFW_update_channel = cfg.get(cfg.MFW_update_channel)
        resource_update_channel = cfg.get(cfg.resource_update_channel)
        self.aboutGroup = SettingCardGroup(
            self.tr("Feedback and About"), self.Setting_scroll_widget
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

        self.aboutGroup.addSettingCard(self.updateCard)
        self.aboutGroup.addSettingCard(self.aboutCard)
        self.add_setting_group(self.aboutGroup)

    def init_info(self):
        """
        初始化控件信息
        """
        interface_data = self._get_interface_metadata()
        self.project_name = interface_data.get("name", "")
        self.project_version = interface_data.get("version", "")
        self.project_url = (
            interface_data.get("github")
            or interface_data.get("url")
            or interface_data.get("repository")
            or ""
        )


        if hasattr(self, "updateCard"):
            self.updateCard.setContent(
                self.tr("Current")
                + " "
                + self.project_name
                + " "
                + self.tr("version:")
                + " "
                + self.project_version
            )

    def _get_interface_metadata(self):
        """从服务协调器的任务服务获取 interface 数据。"""
        if not self._service_coordinator:
            return {}
        interface_data = getattr(self._service_coordinator.task, "interface", None)
        return interface_data or {}

    def _apply_theme_from_config(self):
        """确保设置界面初始化时与全局主题同步。"""
        theme_mode = cfg.get(cfg.themeMode)
        if theme_mode:
            try:
                setTheme(theme_mode)
            except Exception as exc:
                logger.warning("应用主题模式失败: %s", exc)

        theme_color_item = getattr(cfg, "themeColor", None)
        if theme_color_item:
            theme_color = cfg.get(theme_color_item)
            if theme_color:
                try:
                    setThemeColor(theme_color)
                except Exception as exc:
                    logger.warning("应用主题色失败: %s", exc)

    def _apply_interface_font(self):
        """略微放大设置界面的默认字体以改善可读性。"""
        font = self.font()
        base_size = font.pointSize()
        if base_size <= 0:
            base_size = 10
        font.setPointSize(base_size + 2)
        self.setFont(font)

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
        cfg.appRestartSig.connect(self.__showRestartTooltip)
        self.updateCard.clicked2.connect(self._on_resource_update_requested)
        self.updateCard.clicked2.connect(lambda: cfg.set(cfg.start_complete, True))
        self.run_after_startup.checkedChanged.connect(self._onRunAfterStartupCardChange)

        cfg.themeChanged.connect(setTheme)
        self.themeColorCard.colorChanged.connect(lambda c: setThemeColor(c))
        self.micaCard.checkedChanged.connect(signalBus.micaEnableChanged)

        resource_issue_link = self.project_url
        if resource_issue_link:
            self.updateCard.clicked.connect(
                lambda: QDesktopServices.openUrl(QUrl(resource_issue_link))
            )
        else:
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

        self.aboutCard.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(REPO_URL)))
        self.aboutCard.clicked2.connect(self._on_self_update_requested)
        self._apply_theme_from_config()

    def setup_updater_interface(self):
        """占位方法，供未来重构更新器接口使用。"""
        pass

    def _on_resource_update_requested(self):
        """资源更新入口（暂时无实现）。"""
        pass

    def _on_self_update_requested(self):
        """应用更新入口（暂时无实现）。"""
        pass

    def _onRunAfterStartupCardChange(self):
        """根据输入更新启动前运行的程序脚本路径。"""
        cfg.set(cfg.run_after_startup, self.run_after_startup.isChecked())

