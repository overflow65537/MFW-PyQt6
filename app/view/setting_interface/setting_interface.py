"""
MFW-ChainFlow Assistant
MFW-ChainFlow Assistant 设置界面
作者:overflow65537
"""

from typing import Optional

from PySide6.QtCore import Qt, QUrl, Signal
from PySide6.QtGui import QDesktopServices, QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
    QHBoxLayout,
    QProgressBar,
    QLabel,
    QGridLayout,
)
from qfluentwidgets import (
    BodyLabel,
    ComboBoxSettingCard,
    CustomColorSettingCard,
    ExpandLayout,
    FluentIcon as FIF,
    InfoBar,
    IndeterminateProgressRing,
    OptionsSettingCard,
    PrimaryPushButton,
    PrimaryPushSettingCard,
    ProgressRing,
    ScrollArea,
    SettingCardGroup,
    SwitchSettingCard,
    setTheme,
    setThemeColor,
)

from app.utils.markdown_helper import render_markdown

from app.common.__version__ import __version__
from app.common.config import cfg, REPO_URL, isWin11
from app.common.signal_bus import signalBus
from app.core.core import ServiceCoordinator
from app.utils.crypto import crypto_manager
from app.utils.logger import logger
from app.view.setting_interface.widget.DoubleButtonSettingCard import (
    DoubleButtonSettingCard,
)
from app.view.setting_interface.widget.ProxySettingCard import ProxySettingCard
from app.view.setting_interface.widget.LineEditCard import LineEditCard


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
        self.interface_data = {}
        self.Setting_scroll_widget = QWidget()
        self.Setting_expand_layout = ExpandLayout(self.Setting_scroll_widget)
        self.scroll_area = ScrollArea(self)
        self._setup_ui()

    def _setup_ui(self):
        """搭建整体结构：标题 + 更新详情 + 滚动区域 + ExpandLayout。"""
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(24, 24, 24, 0)
        self.main_layout.setSpacing(8)

        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setStyleSheet("background-color: transparent; border: none;")
        self.scroll_area.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.interface_data = self._get_interface_metadata()

        self.Setting_expand_layout.setSpacing(28)
        self.Setting_expand_layout.setContentsMargins(24, 24, 24, 24)

        self.scroll_content = QWidget()
        self.scroll_content_layout = QVBoxLayout(self.scroll_content)
        self.scroll_content_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_content_layout.setSpacing(16)

        self.scroll_content_layout.addWidget(self._build_update_header())
        self.scroll_content_layout.addWidget(self.Setting_scroll_widget)
        self.scroll_area.setWidget(self.scroll_content)

        self.initialize_start_settings()
        self.initialize_notice_settings()
        self.initialize_personalization_settings()
        self.initialize_update_settings()
        self._refresh_update_header()

        self.main_layout.addWidget(self.scroll_area)
        self.main_layout.setStretch(1, 1)

        self.bottom_label = BodyLabel("", self)
        self.bottom_label.setFixedHeight(10)
        self.bottom_label.setStyleSheet("background-color: transparent;")
        self.main_layout.addWidget(self.bottom_label)

        self.__connectSignalToSlot()
        self.setup_updater_interface()
        self._apply_theme_from_config()
        self._apply_interface_font()
        self.micaCard.setEnabled(isWin11())

    def _apply_markdown_to_label(self, label: QLabel, content: str | None) -> None:
        """把 Markdown 文本渲染到标签并开启链接交互。"""
        label.setTextFormat(Qt.TextFormat.RichText)
        label.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        label.setOpenExternalLinks(True)
        label.setText(render_markdown(content))

    def _build_update_header(self) -> QWidget:

        header_card = QFrame(self)
        header_card.setFrameShape(QFrame.Shape.StyledPanel)
        header_card.setObjectName("updateHeaderCard")
        header_card.setStyleSheet("border-radius: 12px;")
        header_card.setMinimumHeight(220)

        header_layout = QVBoxLayout(header_card)
        header_layout.setContentsMargins(20, 20, 20, 20)
        header_layout.setSpacing(16)

        top_row = QHBoxLayout()
        top_row.setSpacing(16)

        self.icon_label = QLabel(self)
        pixmap = QPixmap("app/assets/icons/logo.png")
        if not pixmap.isNull():
            self.icon_label.setPixmap(
                pixmap.scaled(
                    72,
                    72,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
        self.icon_label.setFixedSize(72, 72)
        top_row.addWidget(self.icon_label)

        info_column = QVBoxLayout()
        info_column.setSpacing(6)

        self.resource_name_label = BodyLabel(self.tr("ChainFlow Assistant"), self)
        self.resource_name_label.setStyleSheet("font-size: 24px; font-weight: 600;")
        default_contact = self.tr(
            "Contact: support@chainflow.io / Twitter @overflow65537"
        )
        self.contact_label = BodyLabel("", self)
        self.contact_label.setStyleSheet("color: rgba(255, 255, 255, 0.7);")
        self.contact_label.setWordWrap(True)
        self._apply_markdown_to_label(self.contact_label, default_contact)

        info_column.addWidget(self.resource_name_label)
        info_column.addWidget(self.contact_label)
        top_row.addLayout(info_column)
        header_layout.addLayout(top_row)

        self.version_label = BodyLabel(self.tr("Version:") + " " + __version__, self)
        self.version_label.setStyleSheet("color: rgba(255, 255, 255, 0.7);")
        header_layout.addWidget(self.version_label)

        badge_row = QHBoxLayout()
        badge_row.setSpacing(12)

        badge_style = (
            "border-radius: 10px; padding: 4px 12px; font-size: 12px; font-weight: 600;"
            "background-color: rgba(255, 255, 255, 0.12);"
        )
        self.license_badge = BodyLabel(self.tr("License: MIT"), self)
        self.license_badge.setStyleSheet(badge_style)
        self.github_badge = BodyLabel(self.tr("GitHub"), self)
        self.github_badge.setStyleSheet(badge_style)
        self.custom_badge = BodyLabel(self.tr("Stable"), self)
        self.custom_badge.setStyleSheet(badge_style)

        badge_row.addWidget(self.license_badge)
        badge_row.addWidget(self.github_badge)
        badge_row.addWidget(self.custom_badge)
        badge_row.addStretch()
        header_layout.addLayout(badge_row)

        default_description = self.tr(
            "Description: A powerful automation assistant for MaaS tasks with flexible update options."
        )
        self.description_label = BodyLabel("", self)
        self.description_label.setStyleSheet("color: rgba(255, 255, 255, 0.7);")
        self.description_label.setWordWrap(True)
        self._apply_markdown_to_label(self.description_label, default_description)
        header_layout.addWidget(self.description_label)

        action_layout = QHBoxLayout()
        action_layout.setSpacing(12)
        action_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.setFixedWidth(220)
        self.progress_bar.setVisible(False)

        progress_layout = QVBoxLayout()
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addStretch()
        action_layout.addLayout(progress_layout, 1)

        action_layout.addStretch()

        header_layout.addLayout(action_layout)
        return header_card

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

    def initialize_update_settings(self):
        """插入更新设置卡片组（跟原先的 UpdateSettingsSection 等价）。"""
        self.updateGroup = SettingCardGroup(
            self.tr("Update"), self.Setting_scroll_widget
        )

        self.MirrorCard = LineEditCard(
            icon=FIF.APPLICATION,
            title=self.tr("mirrorchyan CDK"),
            content=self.tr("Enter mirrorchyan CDK for stable update path"),
            is_passwork=True,
            num_only=False,
            holderText=self._get_mirror_holder_text(),
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

        channel_parent = getattr(self, "personalGroup", None) or self.updateGroup
        self.channel_selector = ComboBoxSettingCard(
            cfg.resource_update_channel,
            FIF.UPDATE,
            self.tr("select update channel for resource"),
            self.tr("select the update channel for the resource"),
            texts=["Alpha", "Beta", "Stable"],
            parent=channel_parent,
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

        self._initialize_proxy_controls()
        self._configure_mirror_card()
        self.MirrorCard.lineEdit.textChanged.connect(self._onMirrorCardChange)

        self.updateGroup.addSettingCard(self.MirrorCard)
        self.updateGroup.addSettingCard(self.auto_update)
        self.updateGroup.addSettingCard(self.channel_selector)
        self.updateGroup.addSettingCard(self.force_github)
        self.updateGroup.addSettingCard(self.proxy)

        self.add_setting_group(self.updateGroup)

    def _initialize_proxy_controls(self):
        """初始化代理控制器展示及默认值。"""
        combox_index = cfg.get(cfg.proxy)
        self.proxy.combobox.setCurrentIndex(combox_index)

        if combox_index == 0:
            self.proxy.input.setText(cfg.get(cfg.http_proxy))
        elif combox_index == 1:
            self.proxy.input.setText(cfg.get(cfg.socks5_proxy))

        self.proxy.combobox.currentIndexChanged.connect(self.proxy_com_change)
        self.proxy.input.textChanged.connect(self.proxy_inp_change)

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

    def _configure_mirror_card(self):
        """根据接口能力打开/关闭 mirror CDK 文本域。"""
        metadata = self.interface_data or {}
        mirror_supported = bool(metadata.get("mirrorchyan_rid"))
        if mirror_supported:
            self.MirrorCard.setContent(
                self.tr("Enter mirrorchyan CDK for stable update path")
            )
            self.MirrorCard.lineEdit.setEnabled(True)
        else:
            self.MirrorCard.setContent(
                self.tr(
                    "Resource does not support Mirrorchyan, right-click about mirror to unlock input"
                )
            )
            self.MirrorCard.lineEdit.setEnabled(False)

    def _get_mirror_holder_text(self) -> str:
        encrypted = cfg.get(cfg.Mcdk)
        if not encrypted:
            return ""
        try:
            decrypted = crypto_manager.decrypt_payload(encrypted)
            if isinstance(decrypted, bytes):
                decrypted = decrypted.decode("utf-8", errors="ignore")
            return decrypted
        except Exception as exc:
            logger.warning("解密 Mirror CDK 失败: %s", exc)
            return ""

    def _onMirrorCardChange(self):
        try:
            encrypted = crypto_manager.encrypt_payload(self.MirrorCard.lineEdit.text())
            encrypted_value = (
                encrypted.decode("utf-8", errors="ignore")
                if isinstance(encrypted, bytes)
                else str(encrypted)
            )
            cfg.set(cfg.Mcdk, encrypted_value)
        except Exception as exc:
            logger.error("加密 Mirror CDK 失败: %s", exc)
            return
        cfg.set(cfg.is_change_cdk, True)

    def _refresh_update_header(self):
        metadata = self.interface_data or {}
        name = metadata.get("name") or self.tr("ChainFlow Assistant")
        version = metadata.get("version") or __version__
        license_name = metadata.get("license") or self.tr("MIT")
        github_label = metadata.get("github") or self.tr("GitHub")
        custom_badge = metadata.get("badge") or self.tr("Stable Channel")
        description = metadata.get("description") or self.tr(
            "Description: A powerful automation assistant for MaaS tasks with flexible update options."
        )
        contact = metadata.get("contact") or self.tr(
            "Contact: support@chainflow.io / Twitter @overflow65537"
        )

        self.resource_name_label.setText(name)
        self.version_label.setText(self.tr("Version:") + " " + version)
        self.license_badge.setText(self.tr("License:") + " " + license_name)
        self.github_badge.setText(github_label)
        self.custom_badge.setText(custom_badge)
        self._apply_markdown_to_label(self.description_label, description)
        self._apply_markdown_to_label(self.contact_label, contact)

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

        self.run_after_startup.checkedChanged.connect(self._onRunAfterStartupCardChange)

        cfg.themeChanged.connect(setTheme)
        self.themeColorCard.colorChanged.connect(lambda c: setThemeColor(c))
        self.micaCard.checkedChanged.connect(signalBus.micaEnableChanged)
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

    def _on_check_updates(self):
        if REPO_URL:
            QDesktopServices.openUrl(QUrl(REPO_URL))

    def _on_stop_update_requested(self):
        signalBus.update_download_stopped.emit()
