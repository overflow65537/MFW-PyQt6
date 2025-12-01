from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices, QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QProgressBar,
    QVBoxLayout,
    QWidget,
    QTextEdit,
    QLabel,
)
from qfluentwidgets import (
    BodyLabel,
    ComboBox,
    FluentIcon as FIF,
    PrimaryPushButton,
    PrimaryPushSettingCard,
    ScrollArea,
    SettingCardGroup,
)

from app.common.__version__ import __version__
from app.common.config import REPO_URL
from app.core.core import ServiceCoordinator
from app.view.update_interface.widget.UpdateSettingsSection import (
    UpdateSettingsSection,
)


class UpdatePage(QWidget):
    """组合型更新页：顶部卡片 + 设置滚动区 + 更新日志。"""

    def __init__(
        self,
        service_coordinator: Optional[ServiceCoordinator] = None,
        parent=None,
    ):
        super().__init__(parent=parent)
        self.service_coordinator = service_coordinator
        self.interface_data = {}
        self.setObjectName("updatePage")
        self._setup_ui()

    def _setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(24, 24, 24, 24)
        self.main_layout.setSpacing(16)

        self.scroll_area = ScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setStyleSheet("background-color: transparent; border: none;")

        self.content_widget = QWidget(self)
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(16)

        self._build_header(self.content_layout)
        self._build_settings_area(self.content_layout)

        self.scroll_area.setWidget(self.content_widget)
        self.main_layout.addWidget(self.scroll_area)

    def _build_header(self, parent_layout):
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
        self.resource_name_label.setStyleSheet(
            "font-size: 24px; font-weight: 600;"
        )
        self.contact_label = BodyLabel(
            self.tr("Contact: support@chainflow.io / Twitter @overflow65537"), self
        )
        self.contact_label.setStyleSheet("color: rgba(255, 255, 255, 0.7);")

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

        self.description_label = BodyLabel(
            self.tr(
                "Description: A powerful automation assistant for MaaS tasks with flexible update options."
            ),
            self,
        )
        self.description_label.setStyleSheet("color: rgba(255, 255, 255, 0.7);")
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

        right_layout = QHBoxLayout()
        right_layout.setSpacing(8)

        self.update_button = PrimaryPushButton(self.tr("Check for updates"), self)
        self.update_button.clicked.connect(self._on_check_updates)
        right_layout.addWidget(self.update_button)

        self.channel_selector = ComboBox(self)
        self.channel_selector.addItems(
            [self.tr("Alpha"), self.tr("Beta"), self.tr("Stable")]
        )
        self.channel_selector.setCurrentIndex(2)
        right_layout.addWidget(self.channel_selector)
        action_layout.addLayout(right_layout)

        header_layout.addLayout(action_layout)
        parent_layout.addWidget(header_card)

    def _build_settings_area(self, parent_layout):
        self.interface_data = self._get_interface_metadata()
        self.update_settings_section = UpdateSettingsSection(
            parent=self, interface_data=self.interface_data
        )

        self.settings_container = QWidget(self)
        settings_layout = QVBoxLayout(self.settings_container)
        settings_layout.setContentsMargins(0, 0, 0, 0)
        settings_layout.setSpacing(12)
        settings_layout.addWidget(self.update_settings_section.group)


        parent_layout.addWidget(self.settings_container)
        self._refresh_header()

    def _get_interface_metadata(self) -> dict:
        if not self.service_coordinator:
            return {}
        interface_data = getattr(self.service_coordinator.task, "interface", None)
        return interface_data or {}

    def _refresh_header(self):
        name = (
            self.interface_data.get("name")
            or self.tr("ChainFlow Assistant")
        )
        version = self.interface_data.get("version") or __version__
        license_name = self.interface_data.get("license") or self.tr("MIT")
        github_label = self.interface_data.get("github") or self.tr("GitHub")
        custom_badge = self.interface_data.get("badge") or self.tr("Stable Channel")
        description = (
            self.interface_data.get("description")
            or self.tr(
                "Description: A powerful automation assistant for MaaS tasks with flexible update options."
            )
        )
        contact = (
            self.interface_data.get("contact")
            or self.tr("Contact: support@chainflow.io / Twitter @overflow65537")
        )

        self.resource_name_label.setText(name)
        self.version_label.setText(self.tr("Version:") + " " + version)
        self.license_badge.setText(self.tr("License:") + " " + license_name)
        self.github_badge.setText(github_label)
        self.custom_badge.setText(custom_badge)
        self.description_label.setText(description)
        self.contact_label.setText(contact)

    def _on_check_updates(self):
        if REPO_URL:
            QDesktopServices.openUrl(QUrl(REPO_URL))


    def set_progress(self, value: int):
        self.progress_bar.setVisible(0 < value < 100)
        self.progress_bar.setValue(max(0, min(100, value)))

