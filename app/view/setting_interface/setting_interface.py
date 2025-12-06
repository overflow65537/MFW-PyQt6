"""
MFW-ChainFlow Assistant
MFW-ChainFlow Assistant 设置界面
作者:overflow65537
"""

import re
from typing import Callable, Optional
from time import perf_counter

from PySide6.QtCore import Qt, QSize, QUrl, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QDesktopServices, QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
    QHBoxLayout,
    QProgressBar,
    QLabel,
    QDialog,
    QDialogButtonBox,
    QStackedLayout,
    QGraphicsOpacityEffect,
)
from qfluentwidgets import (
    BodyLabel,
    ComboBoxSettingCard,
    CustomColorSettingCard,
    ExpandLayout,
    FluentIcon as FIF,
    OptionsSettingCard,
    PrimaryPushSettingCard,
    ScrollArea,
    SettingCardGroup,
    SwitchSettingCard,
    setTheme,
    setThemeColor,
    TransparentPushButton,
)

from app.utils.markdown_helper import render_markdown
from app.widget.notice_message import NoticeMessageBox

from app.common.__version__ import __version__
from app.common.config import cfg, isWin11
from app.common.signal_bus import signalBus
from app.core.core import ServiceCoordinator
from app.utils.crypto import crypto_manager
from app.utils.logger import logger
from app.utils.update import Update, UpdateCheckTask
from app.view.setting_interface.widget.ProxySettingCard import ProxySettingCard
from app.utils.hotkey_manager import GlobalHotkeyManager
from app.view.setting_interface.widget.LineEditCard import (
    LineEditCard,
    MirrorCdkLineEditCard,
)

_CONTACT_URL_PATTERN = re.compile(r"(?:https?://|www\.)[^\s，,]+")


class SettingInterface(QWidget):
    """
    设置界面，用于配置应用程序设置，主体以滚动区域 + ExpandLayout。
    """

    _DETAIL_BUTTON_STYLE = """
        TransparentPushButton {
            color: rgba(255, 255, 255, 0.85);
            border: 1px solid rgba(255, 255, 255, 0.3);
            border-radius: 12px;
            padding: 6px 14px;
            background-color: rgba(255, 255, 255, 0.04);
            text-align: left;
        }
        TransparentPushButton:hover {
            background-color: rgba(255, 255, 255, 0.08);
        }
    """

    def __init__(
        self,
        service_coordinator: ServiceCoordinator,
        parent=None,
    ):
        super().__init__(parent=parent)
        self.setObjectName("settingInterface")
        self._service_coordinator = service_coordinator
        self.interface_data = self._service_coordinator.task.interface

        self._license_content = self.interface_data.get("license", "")
        self._github_url = self.interface_data.get(
            "github", self.interface_data.get("url", "")
        )
        self.description = self.interface_data.get("description", "")
        self._updater: Optional[Update] = None
        self._update_checker: Optional[UpdateCheckTask] = None
        self._latest_update_check_result: str | bool | None = None
        self._updater_started = False
        self._update_button_handler: Callable | None = None
        self._last_progress_time: float | None = None
        self._last_downloaded_bytes = 0
        self._detail_progress_animation: Optional[QPropertyAnimation] = None
        self._progress_content_animation: Optional[QPropertyAnimation] = None
        self.Setting_scroll_widget = QWidget()
        self.Setting_expand_layout = ExpandLayout(self.Setting_scroll_widget)
        self.scroll_area = ScrollArea(self)
        self._setup_ui()
        self._init_updater()
        self._init_update_checker()

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
        self.initialize_hotkey_settings()
        self.initialize_update_settings()
        self._refresh_update_header()

        self.main_layout.addWidget(self.scroll_area)
        self.main_layout.setStretch(1, 1)

        self.bottom_label = BodyLabel("", self)
        self.bottom_label.setFixedHeight(10)
        self.bottom_label.setStyleSheet("background-color: transparent;")
        self.main_layout.addWidget(self.bottom_label)

        self.__connectSignalToSlot()
        self._apply_theme_from_config()
        self._apply_interface_font()
        self.micaCard.setEnabled(isWin11())

    def _apply_markdown_to_label(self, label: QLabel, content: str | None) -> None:
        """把 Markdown 文本渲染到标签并开启链接交互。"""
        label.setTextFormat(Qt.TextFormat.RichText)
        label.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        label.setOpenExternalLinks(True)
        label.setText(render_markdown(content))

    def _linkify_contact_urls(self, contact: str) -> str:
        """把联系方式中的网址转换成 Markdown 超链接。"""
        if not contact:
            return contact

        def replace(match: re.Match[str]) -> str:
            url = match.group(0)
            href = url if url.startswith(("http://", "https://")) else f"http://{url}"
            return f"[{url}]({href})"

        return _CONTACT_URL_PATTERN.sub(replace, contact)

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
        self.icon_label.setFixedSize(72, 72)
        self._apply_header_icon("app/assets/icons/logo.png")
        top_row.addWidget(self.icon_label)

        info_column = QVBoxLayout()
        info_column.setSpacing(6)

        self.resource_name_label = BodyLabel(self.tr("ChainFlow Assistant"), self)
        self.resource_name_label.setStyleSheet("font-size: 24px; font-weight: 600;")
        default_contact = self.interface_data.get("contact", "")
        self.contact_label = BodyLabel("", self)
        self.contact_label.setStyleSheet("color: rgba(255, 255, 255, 0.7);")
        self.contact_label.setWordWrap(True)
        self._apply_markdown_to_label(
            self.contact_label, self._linkify_contact_urls(default_contact)
        )

        info_column.addWidget(self.resource_name_label)
        info_column.addWidget(self.contact_label)
        top_row.addLayout(info_column)
        header_layout.addLayout(top_row)

        self.version_label = BodyLabel(
            self.tr("Version:") + " " + self.interface_data.get("version", "0.0.1"),
            self,
        )
        self.version_label.setStyleSheet("color: rgba(255, 255, 255, 0.7);")
        self.last_version_label = BodyLabel("", self)
        self.last_version_label.setStyleSheet("color: rgba(255, 255, 255, 0.7);")

        self.detail_progress = QProgressBar(self)
        self.detail_progress.setRange(0, 100)
        self.detail_progress.setValue(0)
        self.detail_progress.setTextVisible(False)
        self.detail_progress.setFixedHeight(6)
        self.detail_progress_effect = QGraphicsOpacityEffect(self.detail_progress)
        self.detail_progress.setGraphicsEffect(self.detail_progress_effect)
        self.detail_progress_effect.setOpacity(0.0)


        version_layout = QHBoxLayout()
        version_layout.setSpacing(12)
        version_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        version_column = QVBoxLayout()
        version_column.setSpacing(4)
        version_column.addWidget(self.version_label)
        version_column.addWidget(self.last_version_label)
        version_layout.addLayout(version_column)
        self.detail_progress_placeholder = QWidget(self)
        self.detail_progress_placeholder.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        self.detail_progress_placeholder.setFixedHeight(self.detail_progress.height())
        self.detail_progress_container = QWidget(self)
        self.detail_progress_container.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        self.detail_progress_stack = QStackedLayout(self.detail_progress_container)
        self.detail_progress_stack.setContentsMargins(0, 0, 0, 0)
        self.detail_progress_stack.addWidget(self.detail_progress_placeholder)
        self.detail_progress_stack.addWidget(self.detail_progress)
        self.detail_progress_stack.setCurrentWidget(self.detail_progress_placeholder)
        version_layout.addWidget(self.detail_progress_container, 1)
        header_layout.addLayout(version_layout)

        detail_row = QHBoxLayout()
        detail_row.setSpacing(12)
        detail_row.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )

        self.license_button = self._create_detail_button(
            self.tr("License"), FIF.CERTIFICATE
        )
        self.github_button = self._create_detail_button(
            self.tr("GitHub URL"), FIF.GITHUB
        )
        self.update_button = self._create_detail_button(self.tr("Update"), FIF.UPDATE)
        self.update_log_button = self._create_detail_button(
            self.tr("Open update log"), FIF.QUICK_NOTE
        )

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        self.progress_bar.setVisible(True)
        self.progress_info_label = BodyLabel("", self)
        self.progress_info_label.setStyleSheet("color: rgba(255, 255, 255, 0.7);")
        self.progress_info_label.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        self.progress_info_label.setSizePolicy(
            QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed
        )
        self.progress_info_label.setVisible(True)
        self.progress_container = QWidget(self)
        self.progress_container.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        self.progress_stack = QStackedLayout(self.progress_container)
        self.progress_stack.setContentsMargins(0, 0, 0, 0)
        self.progress_content_widget = QWidget()
        self.progress_content_layout = QHBoxLayout(self.progress_content_widget)
        self.progress_content_layout.setContentsMargins(0, 0, 0, 0)
        self.progress_content_layout.setSpacing(8)
        self.progress_content_layout.addWidget(self.progress_bar, 1)
        self.progress_content_layout.addWidget(self.progress_info_label)
        self.progress_content_effect = QGraphicsOpacityEffect(self.progress_content_widget)
        self.progress_content_widget.setGraphicsEffect(self.progress_content_effect)
        self.progress_content_effect.setOpacity(0.0)
        self.progress_placeholder = QWidget()
        self.progress_placeholder.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        self.progress_placeholder.setFixedHeight(self.progress_bar.height())
        self.progress_stack.addWidget(self.progress_placeholder)
        self.progress_stack.addWidget(self.progress_content_widget)
        self.progress_stack.setCurrentWidget(self.progress_placeholder)

        self.license_button.clicked.connect(self._open_license_dialog)
        self.github_button.clicked.connect(self._open_github_home)
        self.update_log_button.clicked.connect(self._open_update_log)
        self._bind_start_button(enable=True)

        detail_row.addWidget(self.license_button)
        detail_row.addWidget(self.github_button)
        detail_row.addWidget(self.update_button)
        detail_row.addWidget(self.update_log_button)
        detail_row.addWidget(self.progress_container, 1)
        header_layout.addLayout(detail_row)

        default_description = self.tr("Description: ") + self.interface_data.get(
            "description", ""
        )

        self.description_label = BodyLabel("", self)
        self.description_label.setStyleSheet("color: rgba(255, 255, 255, 0.7);")
        self.description_label.setWordWrap(True)
        self._apply_markdown_to_label(self.description_label, default_description)
        header_layout.addWidget(self.description_label)

        return header_card

    def _create_detail_button(self, text: str, icon) -> TransparentPushButton:
        button = TransparentPushButton(text, self, icon)
        button.setIconSize(QSize(18, 18))
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setStyleSheet(self._DETAIL_BUTTON_STYLE)
        button.setFixedHeight(42)
        button.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        return button

    def _open_license_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle(self.tr("License"))
        dialog.setModal(True)
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        content_label = BodyLabel(self._license_content, dialog)
        content_label.setWordWrap(True)
        content_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.LinksAccessibleByMouse
        )

        scroll_area = ScrollArea(dialog)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.enableTransparentBackground()
        scroll_area.setWidget(content_label)
        scroll_area.setMinimumHeight(280)

        layout.addWidget(scroll_area)

        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Close, parent=dialog
        )
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)

        dialog.resize(480, 280)
        dialog.exec()

    def _open_github_home(self):
        if not self._github_url:
            return
        QDesktopServices.openUrl(QUrl(self._github_url))

    def _apply_header_icon(self, icon_path: Optional[str] = None) -> None:
        """加载 interface 中提供的图标路径，失败时回退到默认 logo。"""
        path = icon_path or "app/assets/icons/logo.png"
        pixmap = QPixmap(path)
        if pixmap.isNull():
            pixmap = QPixmap("app/assets/icons/logo.png")
        if pixmap.isNull():
            return
        self.icon_label.setPixmap(
            pixmap.scaled(
                72,
                72,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )

    def _open_update_log(self):
        """打开更新日志对话框"""
        release_notes = self._load_release_notes()

        if not release_notes:
            # 如果没有本地更新日志，显示提示信息
            release_notes = {
                self.tr("No update log"): self.tr(
                    "No update log found locally.\n\n"
                    "Please check for updates first, or visit the GitHub releases page."
                )
            }

        # 使用 NoticeMessageBox 显示更新日志
        dialog = NoticeMessageBox(
            parent=self,
            title=self.tr("Update Log"),
            content=release_notes,
        )
        # 隐藏"确认且不再显示"按钮，只保留确认按钮
        dialog.button_yes.hide()
        dialog.exec()

    def _start_detail_progress(self):
        """启动不确定进度条（用于检查更新）"""
        self.detail_progress.setRange(0, 0)
        self._fade_detail_progress(show=True)

    def _stop_detail_progress(self):
        """停止不确定进度条"""
        self._fade_detail_progress(show=False)

    def _show_progress_bar(self):
        """显示下载进度条"""
        self.progress_bar.setValue(0)
        self.progress_bar.setRange(0, 100)
        self.progress_info_label.setText("0.00/0.00 MB   0.00 MB/s")
        self._last_progress_time = perf_counter()
        self._last_downloaded_bytes = 0
        self._fade_progress_content(show=True)

    def _lock_update_button_temporarily(self) -> None:
        self.update_button.setEnabled(False)
        QTimer.singleShot(
            500,
            lambda: self.update_button.setEnabled(True),
        )

    def _disconnect_update_button(self) -> None:
        if handler := self._update_button_handler:
            try:
                self.update_button.clicked.disconnect(handler)
            except (TypeError, RuntimeError):
                pass
            finally:
                self._update_button_handler = None

    def _bind_start_button(self, *, enable: bool = True) -> None:
        self._disconnect_update_button()
        self.update_button.clicked.connect(self._on_update_start_clicked)
        self.update_button.setText(self.tr("Update"))
        self.update_button.setEnabled(enable)
        self._update_button_handler = self._on_update_start_clicked

    def _bind_stop_button(self, text: str, *, enable: bool = True) -> None:
        self._disconnect_update_button()
        self.update_button.clicked.connect(self._on_update_stop_clicked)
        self.update_button.setText(text)
        self.update_button.setEnabled(enable)
        self._update_button_handler = self._on_update_stop_clicked

    def _bind_instant_update_button(self, *, enable: bool = True) -> None:
        self._disconnect_update_button()
        self.update_button.clicked.connect(self._on_instant_update_clicked)
        self.update_button.setText(self.tr("Update Now"))
        self.update_button.setEnabled(enable)
        self._update_button_handler = self._on_instant_update_clicked

    def _hide_progress_indicators(self) -> None:
        self._fade_detail_progress(show=False)
        self._fade_progress_content(show=False)
        self._last_progress_time = None
        self._last_downloaded_bytes = 0

    def _create_opacity_animation(
        self,
        effect: QGraphicsOpacityEffect,
        start: float,
        end: float,
        on_finished: Optional[Callable[[], None]] = None,
        duration: int = 220,
    ) -> QPropertyAnimation:
        animation = QPropertyAnimation(effect, b"opacity", self)
        animation.setDuration(duration)
        animation.setStartValue(start)
        animation.setEndValue(end)
        animation.setEasingCurve(QEasingCurve.Type.InOutCubic)
        if on_finished:
            animation.finished.connect(on_finished)
        animation.start()
        return animation

    def _fade_detail_progress(self, show: bool) -> None:
        target = 1.0 if show else 0.0
        effect = self.detail_progress_effect
        start = effect.opacity()
        if start == target:
            if not show:
                self.detail_progress_stack.setCurrentWidget(
                    self.detail_progress_placeholder
                )
            return
        if self._detail_progress_animation is not None:
            self._detail_progress_animation.stop()
        if show:
            if self.detail_progress_stack.currentWidget() != self.detail_progress:
                self.detail_progress_stack.setCurrentWidget(self.detail_progress)
            start = 0.0
            effect.setOpacity(0.0)

        def on_finished():
            if not show:
                self.detail_progress_stack.setCurrentWidget(
                    self.detail_progress_placeholder
                )
                self.detail_progress.setRange(0, 100)
                self.detail_progress.setValue(0)

        self._detail_progress_animation = self._create_opacity_animation(
            effect, start, target, on_finished=on_finished
        )

    def _fade_progress_content(self, show: bool) -> None:
        target = 1.0 if show else 0.0
        effect = self.progress_content_effect
        start = effect.opacity()
        if start == target:
            if not show:
                self.progress_stack.setCurrentWidget(self.progress_placeholder)
            return
        if self._progress_content_animation is not None:
            self._progress_content_animation.stop()
        if show:
            if self.progress_stack.currentWidget() != self.progress_content_widget:
                self.progress_stack.setCurrentWidget(self.progress_content_widget)
            start = 0.0
            effect.setOpacity(0.0)

        def on_finished():
            if not show:
                self.progress_stack.setCurrentWidget(self.progress_placeholder)
                self.progress_bar.setValue(0)
                self.progress_bar.setRange(0, 100)
                self.progress_info_label.setText("")
                effect.setOpacity(0.0)

        self._progress_content_animation = self._create_opacity_animation(
            effect, start, target, on_finished=on_finished
        )

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
        self.speedrun_mode_card = SwitchSettingCard(
            FIF.SPEED_HIGH,
            self.tr("Speedrun Mode"),
            self.tr("Open to skip some tasks already run"),
            configItem=cfg.speedrun_mode,
            parent=self.start_Setting,
        )
        self.start_Setting.addSettingCard(self.run_after_startup)
        self.start_Setting.addSettingCard(self.never_show_notice)
        self.start_Setting.addSettingCard(self.speedrun_mode_card)
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

        self.remember_geometry_card = SwitchSettingCard(
            FIF.PIN,
            self.tr("Restore window position"),
            self.tr(
                "When enabled, the application reopens at the last recorded size and position"
            ),
            cfg.remember_window_geometry,
            self.personalGroup,
        )
        self.advanced_settings_card = SwitchSettingCard(
            FIF.SETTING,
            self.tr("Advanced Settings"),
            self.tr("Enable to show more options in Pre-configuration"),
            cfg.show_advanced_startup_options,
            self.personalGroup,
        )

        self.personalGroup.addSettingCard(self.micaCard)
        self.personalGroup.addSettingCard(self.themeCard)
        self.personalGroup.addSettingCard(self.themeColorCard)
        self.personalGroup.addSettingCard(self.zoomCard)
        self.personalGroup.addSettingCard(self.languageCard)
        self.personalGroup.addSettingCard(self.remember_geometry_card)
        self.personalGroup.addSettingCard(self.advanced_settings_card)
        self.add_setting_group(self.personalGroup)

    def initialize_hotkey_settings(self):
        """添加全局快捷键配置入口，可自定义开始/结束任务组合键。"""
        self.hotkeyGroup = SettingCardGroup(
            self.tr("Global Shortcuts"), self.Setting_scroll_widget
        )

        start_value = str(cfg.get(cfg.start_task_shortcut) or "")
        stop_value = str(cfg.get(cfg.stop_task_shortcut) or "")

        self.start_shortcut_card = LineEditCard(
            FIF.RIGHT_ARROW,
            self.tr("Start task shortcut"),
            holderText=start_value,
            content=self.tr("Default Ctrl+`, can also trigger when focus is not on the main window"),
            parent=self.hotkeyGroup,
            num_only=False,
        )
        self._decorate_shortcut_card(self.start_shortcut_card, self.tr("Ctrl+"))
        self._set_shortcut_line_text(self.start_shortcut_card, start_value)
        self.start_shortcut_card.lineEdit.setPlaceholderText(
            self.tr("Format: Modifier+[Key], e.g. Ctrl+`")
        )
        self.start_shortcut_card.lineEdit.editingFinished.connect(
            lambda: self._on_shortcut_card_edited(
                cfg.start_task_shortcut,
                self.start_shortcut_card,
                required_modifier="ctrl",
            )
        )

        self.stop_shortcut_card = LineEditCard(
            FIF.RIGHT_ARROW,
            self.tr("Stop task shortcut"),
            holderText=stop_value,
            content=self.tr("Default Alt+`, used to interrupt tasks in advance"),
            parent=self.hotkeyGroup,
            num_only=False,
        )
        self._decorate_shortcut_card(self.stop_shortcut_card, self.tr("Alt+"))
        self._set_shortcut_line_text(self.stop_shortcut_card, stop_value)
        self.stop_shortcut_card.lineEdit.setPlaceholderText(
            self.tr("Format: Modifier+[Key], e.g. Alt+`")
        )
        self.stop_shortcut_card.lineEdit.editingFinished.connect(
            lambda: self._on_shortcut_card_edited(
                cfg.stop_task_shortcut,
                self.stop_shortcut_card,
                required_modifier="alt",
            )
        )

        self.hotkeyGroup.addSettingCard(self.start_shortcut_card)
        self.hotkeyGroup.addSettingCard(self.stop_shortcut_card)
        self.add_setting_group(self.hotkeyGroup)

    def _on_shortcut_card_edited(
        self,
        config_item,
        card: LineEditCard,
        required_modifier: str | None = None,
    ):
        key_text = card.lineEdit.text().strip()
        current = cfg.get(config_item)
        if not key_text:
            self._set_shortcut_line_text(card, current)
            signalBus.info_bar_requested.emit(
                "warning", self.tr("Key cannot be empty")
            )
            return

        raw = (
            f"{required_modifier}+{key_text}"
            if required_modifier
            else key_text
        )
        normalized = GlobalHotkeyManager._normalize(raw)
        if not normalized:
            self._set_shortcut_line_text(card, current)
            signalBus.info_bar_requested.emit(
                "warning", self.tr("Key format is invalid, restored to previous configuration.")
            )
            return

        if required_modifier:
            modifiers = normalized.split("+")[:-1]
            if required_modifier not in modifiers:
                self._set_shortcut_line_text(card, current)
                modifier_name = (
                    self.tr("Ctrl")
                    if required_modifier == "ctrl"
                    else self.tr("Alt")
                )
                action_name = (
                    self.tr("Start task")
                    if required_modifier == "ctrl"
                    else self.tr("Stop task")
                )
                signalBus.info_bar_requested.emit(
                    "warning",
                    self.tr("Shortcut must start with %1+, used for %2.")
                    .replace("%1", modifier_name)
                    .replace("%2", action_name),
                )
                return

        if normalized == current:
            self._set_shortcut_line_text(card, normalized)
            return

        cfg.set(config_item, normalized)
        self._set_shortcut_line_text(card, normalized)
        signalBus.hotkey_shortcuts_changed.emit()

        if normalized == current:
            self._set_shortcut_line_text(card, normalized)
            return

        cfg.set(config_item, normalized)
        self._set_shortcut_line_text(card, normalized)
        signalBus.hotkey_shortcuts_changed.emit()

    def _set_shortcut_line_text(self, card: LineEditCard, value: str | None):
        normalized = GlobalHotkeyManager._normalize(str(value or "")) or str(value or "")
        key_only = normalized.split("+")[-1] if normalized else ""
        card.lineEdit.blockSignals(True)
        card.lineEdit.setText(key_only)
        card.lineEdit.blockSignals(False)

    def _decorate_shortcut_card(self, card: LineEditCard, prefix: str):
        """在输入框前加上不可编辑的前缀 BodyLabel，例如 Ctrl+ 或 Alt+。"""
        label = BodyLabel(prefix, card)
        label.setWordWrap(False)
        label.setObjectName("shortcutPrefixLabel")
        label.setAlignment(
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight
        )
        label.setFixedWidth(48)
        layout = card.hBoxLayout
        idx = layout.indexOf(card.lineEdit)
        if idx >= 0:
            layout.insertWidget(idx, label)
            layout.insertSpacing(idx + 1, 4)

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

        self.MirrorCard = MirrorCdkLineEditCard(
            icon=FIF.APPLICATION,
            title=self.tr("mirrorchyan CDK"),
            content=self.tr("Enter mirrorchyan CDK for stable update path"),
            holderText=self._get_mirror_holder_text(),
            button_text=self.tr("About Mirror"),
            parent=self.updateGroup,
        )

        self.auto_update = SwitchSettingCard(
            FIF.UPDATE,
            self.tr("Automatically update after startup"),
            self.tr("Automatically download and apply updates once available"),
            configItem=cfg.auto_update,
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

        self.github_api_key_card = LineEditCard(
            FIF.LINK,
            self.tr("GitHub API Key"),
            content=self.tr(
                "Personal access tokens increase GitHub API rate limits for update checks."
            ),
            parent=self.updateGroup,
            is_passwork=True,
            num_only=False,
        )
        self.github_api_key_card.lineEdit.setPlaceholderText(
            self.tr("Optional token for authenticated GitHub requests")
        )
        self.github_api_key_card.lineEdit.setText(cfg.get(cfg.github_api_key) or "")
        self.github_api_key_card.lineEdit.textChanged.connect(
            self._on_github_api_key_change
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
        self.updateGroup.addSettingCard(self.github_api_key_card)
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

    def _on_github_api_key_change(self, text: str):
        cfg.set(cfg.github_api_key, str(text).strip())

    def _refresh_update_header(self):
        metadata = self.interface_data or {}
        icon_path = metadata.get("icon", "")
        name = metadata.get("name", "")
        version = metadata.get("version", "0.0.1")
        last_version = cfg.get(cfg.latest_update_version)
        license_value = metadata.get("license", "None License")
        github = metadata.get("github", metadata.get("url", ""))
        description = metadata.get("description", "")
        contact = metadata.get("contact", "")

        self.resource_name_label.setText(name)
        self.version_label.setText(self.tr("Version:") + " " + version)
        self._set_last_version_label(last_version)
        self.license_button.setToolTip(self.tr("License:") + " " + license_value)
        self.update_button.setToolTip(self.tr("Check for resource updates"))
        self.update_log_button.setToolTip(self.tr("View update log"))
        self._apply_markdown_to_label(self.description_label, description)
        self._apply_markdown_to_label(
            self.contact_label, self._linkify_contact_urls(contact)
        )
        self._github_url = github
        self._license_content = license_value
        self.license_button.setText(self.tr("License"))
        self._apply_header_icon(icon_path)

    def _set_last_version_label(self, version: str | None):
        version_text = version or self.tr("N/A")
        self.last_version_label.setText(self.tr("Last version:") + " " + version_text)

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
        signalBus.info_bar_requested.emit(
            "info", self.tr("Configuration takes effect after restart")
        )

    def __connectSignalToSlot(self):
        """连接信号到对应的槽函数。"""
        cfg.appRestartSig.connect(self.__showRestartTooltip)

        self.run_after_startup.checkedChanged.connect(self._onRunAfterStartupCardChange)

        cfg.themeChanged.connect(setTheme)
        self.themeColorCard.colorChanged.connect(lambda c: setThemeColor(c))
        self.micaCard.checkedChanged.connect(signalBus.micaEnableChanged)
        self._apply_theme_from_config()

    def _onRunAfterStartupCardChange(self):
        """根据输入更新启动前运行的程序脚本路径。"""
        cfg.set(cfg.run_after_startup, self.run_after_startup.isChecked())

    def _init_updater(self):
        """初始化更新器对象并绑定信号"""
        if not self._service_coordinator:
            logger.warning("service_coordinator 未初始化，跳过更新器初始化")
            return

        # 创建更新器
        self._updater = Update(
            service_coordinator=self._service_coordinator,
            stop_signal=signalBus.update_stopped,
            progress_signal=signalBus.update_progress,
            info_bar_signal=signalBus.info_bar_requested,
        )

        # 绑定信号
        signalBus.update_progress.connect(self._on_download_progress)
        signalBus.update_stopped.connect(self._on_update_stopped)

        logger.info("更新器初始化完成")

    def _init_update_checker(self):
        """在后台检查资源更新，并在完成后回传结果"""
        if not self._service_coordinator:
            logger.warning("service_coordinator 未初始化，跳过更新检查器")
            return

        self._update_checker = UpdateCheckTask(
            service_coordinator=self._service_coordinator
        )
        self._update_checker.result_ready.connect(self._on_update_check_result)
        self._update_checker.start()

    def _on_update_check_result(self, result: dict):
        """预留的接口，用于接收后台检查结果"""
        if result.get("enable"):
            release_note = result.get("release_note", "")
            latest_version = result.get("latest_update_version", "")
            if latest_version:
                # 更新设置页面的最新版本号显示
                self._set_last_version_label(latest_version)
                # 发送 InfoBar 通知用户有新版本
                signalBus.info_bar_requested.emit(
                    "info", self.tr("New version available: ") + latest_version
                )
                logger.info(f"检测到新版本: {latest_version}")
            if release_note and latest_version:
                self._save_release_note(latest_version, release_note)

    def _save_release_note(self, version: str, content: str):
        """保存更新日志到文件"""
        import os

        release_notes_dir = "./release_notes"
        os.makedirs(release_notes_dir, exist_ok=True)

        # 清理版本号中的非法字符作为文件名
        safe_version = version.replace("/", "-").replace("\\", "-").replace(":", "-")
        file_path = os.path.join(release_notes_dir, f"{safe_version}.md")

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            logger.info(f"更新日志已保存到: {file_path}")
        except Exception as e:
            logger.error(f"保存更新日志失败: {e}")

    def _load_release_notes(self) -> dict:
        """加载所有已保存的更新日志"""
        import os

        release_notes_dir = "./release_notes"
        notes = {}

        if not os.path.exists(release_notes_dir):
            return notes

        try:
            for filename in os.listdir(release_notes_dir):
                if filename.endswith(".md"):
                    version = filename[:-3]  # 移除 .md 后缀
                    file_path = os.path.join(release_notes_dir, filename)
                    with open(file_path, "r", encoding="utf-8") as f:
                        notes[version] = f.read()
        except Exception as e:
            logger.error(f"加载更新日志失败: {e}")

        # 按版本号排序（降序，最新版本在前）
        sorted_notes = dict(sorted(notes.items(), key=lambda x: x[0], reverse=True))
        return sorted_notes

    def _on_update_start_clicked(self):
        """点击开始更新"""
        if not self._updater:
            logger.warning("更新器未初始化")
            if self._github_url:
                QDesktopServices.openUrl(QUrl(self._github_url))
            return

        self._show_progress_bar()
        self._bind_stop_button(self.tr("Stop update"), enable=False)
        self._lock_update_button_temporarily()
        self._updater.start()

    def _on_update_stop_clicked(self):
        """点击停止更新"""
        if self._updater and self._updater.isRunning():
            self._lock_update_button_temporarily()
            self._on_stop_update_requested()

    def _on_update_stopped(self, status: int):
        """更新器停止信号统一处理 UI"""
        self._hide_progress_indicators()
        self._lock_update_button_temporarily()
        if status == 2:
            self._bind_instant_update_button(enable=False)
            return
        self._bind_start_button(enable=False)

    def _on_instant_update_clicked(self):
        """立即更新"""
        # 如果已经启动过更新程序，忽略重复调用（幂等保护）
        if self._updater_started:
            logger.info("更新程序已启动，忽略重复调用。")
            return

        # 标记为已启动，防止并发重复调用
        self._updater_started = True

        # 重命名更新程序防止占用
        import sys

        try:
            if sys.platform.startswith("win32"):
                self._rename_updater("MFWUpdater.exe", "MFWUpdater1.exe")
            elif sys.platform.startswith("darwin") or sys.platform.startswith("linux"):
                self._rename_updater("MFWUpdater", "MFWUpdater1")
        except Exception as e:
            # 如果重命名失败，重置启动标志并报告错误
            self._updater_started = False
            logger.error(f"重命名更新程序失败: {e}")
            signalBus.info_bar_requested.emit("error", e)
            return

        # 启动更新程序（子进程）
        try:
            self._start_updater()
        except Exception as e:
            # 启动失败则重置标志并报告错误
            self._updater_started = False
            logger.error(f"启动更新程序失败: {e}")
            signalBus.info_bar_requested.emit("error", e)
            return

        # 启动成功后退出主程序
        from PySide6.QtWidgets import QApplication

        QApplication.quit()

    def _rename_updater(self, old_name, new_name):
        """重命名更新程序。"""
        import os

        if os.path.exists(old_name) and os.path.exists(new_name):
            os.remove(new_name)
        if os.path.exists(old_name):
            os.rename(old_name, new_name)

    def _start_updater(self):
        """启动更新程序。"""
        import sys
        import subprocess

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
            signalBus.info_bar_requested.emit("error", e)
            return

        logger.info("正在启动更新程序")

    def _on_download_progress(self, downloaded: int, total: int):
        """下载进度回调"""
        if total <= 0:
            self.progress_bar.setRange(0, 0)  # 不确定进度模式
            self._update_progress_info_label(downloaded, total)
            return
        self.progress_bar.setRange(0, 100)
        value = min(100, int(downloaded / total * 100))
        self.progress_bar.setValue(value)
        # 确保进度条可见（取消透明）
        self.progress_bar.setStyleSheet("")
        self._update_progress_info_label(downloaded, total)

    def _update_progress_info_label(self, downloaded: int, total: int) -> None:
        """更新进度信息标签（显示当前大小、总大小和速度）。"""
        previous_time = self._last_progress_time
        now = perf_counter()
        elapsed = None if previous_time is None else now - previous_time
        delta_bytes = max(downloaded - self._last_downloaded_bytes, 0)
        self._last_progress_time = now
        self._last_downloaded_bytes = downloaded

        speed_bytes_per_sec = 0.0
        if elapsed and elapsed > 0:
            speed_bytes_per_sec = delta_bytes / elapsed
        downloaded_mb = downloaded / (1024 * 1024)
        total_text = f"{total / (1024 * 1024):.2f}" if total > 0 else "--"
        speed_mb_per_sec = speed_bytes_per_sec / (1024 * 1024)
        self.progress_info_label.setText(
            f"{downloaded_mb:.2f}/{total_text} MB   {speed_mb_per_sec:.2f} MB/s"
        )

    def _on_stop_update_requested(self):
        """停止更新"""
        if self._updater and self._updater.isRunning():
            self._updater.stop()
