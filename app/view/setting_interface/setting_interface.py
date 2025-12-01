"""
MFW-ChainFlow Assistant
MFW-ChainFlow Assistant 设置界面
作者:overflow65537
"""

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QSizePolicy, QVBoxLayout, QWidget
from qfluentwidgets import (
    ExpandLayout,
    ScrollArea,
    SettingCardGroup,
    SwitchSettingCard,
    BodyLabel,
    FluentIcon as FIF,
)

from app.common.config import cfg
from app.core.core import ServiceCoordinator


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
        self.Setting_scroll_widget = QWidget()
        self.Setting_expand_layout = ExpandLayout(self.Setting_scroll_widget)
        self.scroll_area = ScrollArea(self)
        self._setup_ui()

    def _setup_ui(self):
        """搭建整体结构：标题 + 滚动区域 + ExpandLayout + 底部留白。"""
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(24, 24, 24, 0)
        self.main_layout.setSpacing(8)

        self.title_label = BodyLabel(self.tr("Setting"), self)
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

        self.Setting_expand_layout.setSpacing(24)
        self.Setting_expand_layout.setContentsMargins(24, 24, 24, 24)

        self._add_start_settings_group()

        self.main_layout.addWidget(self.scroll_area)
        self.main_layout.setStretch(1, 1)

        self.bottom_label = BodyLabel("", self)
        self.bottom_label.setFixedHeight(10)
        self.bottom_label.setStyleSheet("background-color: transparent;")
        self.main_layout.addWidget(self.bottom_label)

    def add_setting_group(self, group_widget: QWidget):
        """
        向 ExpandLayout 插入设置卡片组。
        """
        self.Setting_expand_layout.addWidget(group_widget)

    def _add_start_settings_group(self):
        """构建启动设置组，与旧版保持一致的外层包裹。"""
        group = SettingCardGroup(self.tr("Startup Settings"), self.Setting_scroll_widget)
        run_after = SwitchSettingCard(
            FIF.PLAY,
            self.tr("Run after startup"),
            self.tr("Launch the task immediately after starting the application."),
            configItem=cfg.run_after_startup,
            parent=group,
        )
        hide_notice = SwitchSettingCard(
            FIF.FEEDBACK,
            self.tr("Never show notice"),
            self.tr("Keep announcements hidden when the app launches."),
            configItem=cfg.hide_notice,
            parent=group,
        )
        group.addSettingCard(run_after)
        group.addSettingCard(hide_notice)

        self.add_setting_group(group)

