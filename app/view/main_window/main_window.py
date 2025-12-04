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

# This file incorporates work covered by the following copyright and
# permission notice:
#
#     PyQt-Fluent-Widgets Copyright (C) 2023-2025 zhiyiYo
#     https://github.com/zhiyiYo/PyQt-Fluent-Widgets

"""
MFW-ChainFlow Assistant
MFW-ChainFlow Assistant 主界面
原作者:zhiyiYo
修改:overflow65537
"""


import sys
from pathlib import Path
from typing import Dict, Optional

from PySide6.QtCore import QSize, QTimer, Qt
from PySide6.QtGui import QIcon, QShortcut, QKeySequence, QGuiApplication
from PySide6.QtWidgets import QApplication

from qfluentwidgets import (
    NavigationItemPosition,
    SplashScreen,
    SystemThemeListener,
    isDarkTheme,
    InfoBar,
    InfoBarPosition,
    MSFluentWindow,
)
from qfluentwidgets import FluentIcon as FIF


from app.view.fast_start.fast_start_logic import FastStartInterface
from app.view.monitor_interface import MonitorInterface
from app.view.schedule_interface.schedule_interface import ScheduleInterface
from app.view.setting_interface.setting_interface import SettingInterface
from app.view.test_interface.test_interface import TestInterface
from app.common.config import cfg
from app.common.signal_bus import signalBus
from app.utils.logger import logger
from app.common.__version__ import __version__
from app.core.core import ServiceCoordinator
from app.widget.notice_message import NoticeMessageBox


class CustomSystemThemeListener(SystemThemeListener):
    def run(self):
        try:
            super().run()
        except NotImplementedError:
            logger.error("当前环境不支持主题监听，已忽略")


ENABLE_TEST_INTERFACE_PAGE = cfg.get(cfg.enable_test_interface_page)


class MainWindow(MSFluentWindow):

    def __init__(self):
        super().__init__()

        # 使用自定义的主题监听器
        self.themeListener = CustomSystemThemeListener(self)

        # 初始化配置管理器
        multi_config_path = Path.cwd() / "config" / "multi_config.json"
        self.service_coordinator = ServiceCoordinator(multi_config_path)

        self._announcement_pending_show = False
        self._init_announcement()

        # 初始化窗口
        self.initWindow()
        # 创建子界面
        self.FastStartInterface = FastStartInterface(self.service_coordinator)
        self.addSubInterface(self.FastStartInterface, FIF.CHECKBOX, self.tr("Task"))
        self.MonitorInterface = MonitorInterface(self.service_coordinator)
        self.addSubInterface(
            self.MonitorInterface,
            FIF.PROJECTOR,
            self.tr("Monitor"),
        )
        self.ScheduleInterface = ScheduleInterface(self.service_coordinator)
        self.addSubInterface(
            self.ScheduleInterface,
            FIF.CALENDAR,
            self.tr("Schedule"),
        )
        if ENABLE_TEST_INTERFACE_PAGE:
            self.TestInterface = TestInterface(self.service_coordinator)
            self.addSubInterface(
                self.TestInterface,
                FIF.MEGAPHONE,
                self.tr("test_interface"),
            )
        self._insert_announcement_nav_item()
        self.SettingInterface = SettingInterface(self.service_coordinator)
        self.addSubInterface(
            self.SettingInterface,
            FIF.SETTING,
            self.tr("Setting"),
            position=NavigationItemPosition.BOTTOM,
        )
        # 添加导航项
        self.splashScreen.finish()
        self._maybe_show_pending_announcement()
        QTimer.singleShot(0, self.service_coordinator.schedule_service.start)

        # 启动主题监听器
        self.themeListener.start()

        # 连接公共信号
        self.connectSignalToSlot()

        logger.info(" 主界面初始化完成。")

    def initWindow(self):
        """初始化窗口设置。"""
        self.resize(1170, 760)
        self.setMinimumWidth(1170)
        self.setMinimumHeight(760)
        self.setWindowIcon(QIcon("./app/icons/logo.png"))
        self.set_title()
        self.setMicaEffectEnabled(cfg.get(cfg.micaEnabled))

        # 设置图标
        icon_path = self.service_coordinator.task.interface.get(
            "icon", "./app/icons/logo.png"
        )
        self.setWindowIcon(QIcon(icon_path))

        # 创建启动画面
        self.splashScreen = SplashScreen(self.windowIcon(), self)
        self.splashScreen.setIconSize(QSize(106, 106))
        self.splashScreen.raise_()

        self._set_initial_geometry()
        self.show()
        QApplication.processEvents()

    def _set_initial_geometry(self):
        """在首次展示前恢复之前的窗口几何，或居中显示。"""
        if not self._restore_window_geometry():
            self._center_window()

    def _restore_window_geometry(self) -> bool:
        """尝试从配置中恢复上次记录的位置与大小。"""
        if not cfg.get(cfg.remember_window_geometry):
            return False
        geometry_value = cfg.get(cfg.last_window_geometry)
        if not geometry_value:
            return False
        try:
            x, y, width, height = map(int, geometry_value.split(","))
        except ValueError:
            logger.warning("无法解析保存的窗口几何尺寸: %s", geometry_value)
            return False
        if width <= 0 or height <= 0:
            return False
        self.setGeometry(x, y, width, height)
        return True

    def _center_window(self):
        """默认居中显示主窗口。"""
        screens = QApplication.screens()
        if not screens:
            return
        desktop = screens[0].availableGeometry()
        w, h = desktop.width(), desktop.height()
        self.move(w // 2 - self.width() // 2, h // 2 - self.height() // 2)

    def connectSignalToSlot(self):
        """连接信号到槽函数。"""
        signalBus.micaEnableChanged.connect(self.setMicaEffectEnabled)
        signalBus.title_changed.connect(self.set_title)
        signalBus.info_bar_requested.connect(self.show_info_bar)

    def _init_announcement(self):
        self._announcement_title = self.tr("Announcement")
        self._announcement_content: Dict[str, str] = {}
        self._announcement_empty_hint = self.tr(
            "There is no announcement at the moment."
        )

        cfg_announcement = cfg.get(cfg.announcement)
        res_announcement = self.service_coordinator.task.interface.get("wellcome", "")
        self.set_announcement_content(self.tr("Announcement"), res_announcement)
        if cfg_announcement != res_announcement:
            # 公告内容不一致，更新配置并在界面准备好后弹出对话框
            self._announcement_pending_show = True
            cfg.set(cfg.announcement, res_announcement)

    def _insert_announcement_nav_item(self):
        """在设置入口上方插入公告按钮，并挂载点击行为。"""
        self.navigationInterface.insertItem(
            0,
            "announcement_button",
            FIF.MEGAPHONE,
            self.tr("Announcement"),
            onClick=self._on_announcement_button_clicked,
            selectable=False,
            position=NavigationItemPosition.BOTTOM,
        )

    def _maybe_show_pending_announcement(self):
        """在主界面完成初始化后延迟展示公告对话框。"""
        if self._announcement_pending_show:
            self._announcement_pending_show = False
            QTimer.singleShot(0, self._on_announcement_button_clicked)

    def _on_announcement_button_clicked(self):
        """处理公告按钮点击，弹出公告对话框或提示无内容。"""
        if not self._announcement_content:
            self.show_info_bar("info", self._announcement_empty_hint)
            return

        dialog = NoticeMessageBox(
            parent=self,
            title=self._announcement_title,
            content=self._announcement_content,
        )
        dialog.button_yes.hide()
        dialog.button_cancel.setText(self.tr("Close"))
        dialog.exec()

    def set_announcement_content(self, title: Optional[str], content) -> None:
        """更新公告数据，外部可以通过调用该方法传入内容。"""
        self._announcement_title = title or self.tr("Announcement")
        self._announcement_content = self._normalize_announcement_content(content)

    def _normalize_announcement_content(self, content) -> Dict[str, str]:
        """将各种形式的公告内容规整为路由标题字典。"""
        if not content:
            return {}
        if isinstance(content, dict):
            return {
                str(key): str(value)
                for key, value in content.items()
                if value is not None
            }

        if isinstance(content, (list, tuple, set)):
            normalized = {}
            for index, entry in enumerate(content, start=1):
                label = self.tr("Item ") + str(index)
                normalized[label] = str(entry)
            return normalized

        return {self.tr("Detail"): str(content)}

    def show_info_bar(self, level: str, message: str):
        """根据等级显示 InfoBar 提示。"""
        level_name = (level or "").lower()
        show_method = {
            "info": InfoBar.info,
            "warning": InfoBar.warning,
            "error": InfoBar.error,
        }.get(level_name, InfoBar.info)
        level_title = {
            "info": self.tr("Info"),
            "warning": self.tr("Warning"),
            "error": self.tr("Error"),
        }.get(level_name, self.tr("Info"))

        show_method(
            title=level_title,
            content=message,
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP_RIGHT,
            duration=(
                -1
                if level_name == "error"
                else self._calculate_info_bar_duration(message)
            ),
            parent=self,
        )

    def _calculate_info_bar_duration(self, message: str) -> int:
        """根据消息长度计算 InfoBar 显示时长，最少 1.5s。"""
        if not message:
            return 1500
        duration = len(message) * 150
        return max(1500, duration)

    def is_admin(self):
        """判断是否为管理员权限"""
        if not sys.platform.startswith("win32"):
            return False
        import ctypes

        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except Exception as e:
            logger.error(f" 检查权限失败，错误信息：{e}")
            return False

    def set_title(self):
        """设置窗口标题"""
        title = self.service_coordinator.task.interface.get("custom_title", "")
        if title:
            self.setWindowTitle(title)
            return
        project_name = self.service_coordinator.task.interface.get("name")
        if project_name:
            title += f" {project_name}"
        version = self.service_coordinator.task.interface.get("version")
        if version:
            title += f" {version}"
        if self.is_admin():
            title += " " + self.tr("admin")
        logger.info(f" 设置窗口标题：{title}")
        self.setWindowTitle(title)

    def resizeEvent(self, e):
        """重写尺寸事件。"""
        super().resizeEvent(e)
        if hasattr(self, "splashScreen"):
            self.splashScreen.resize(self.size())

    def _save_window_geometry_if_needed(self):
        """在关闭时保存当前窗口的位置与大小，用于下次恢复。"""
        if not cfg.get(cfg.remember_window_geometry):
            return
        geo = self.geometry()
        cfg.set(
            cfg.last_window_geometry,
            f"{geo.x()},{geo.y()},{geo.width()},{geo.height()}",
        )

    def closeEvent(self, e):
        """关闭事件"""
        self._save_window_geometry_if_needed()
        self.themeListener.terminate()
        self.themeListener.deleteLater()
        e.accept()
        super().closeEvent(e)

    def _onThemeChangedFinished(self):
        """主题更改完成时的处理。"""
        super()._onThemeChangedFinished()

        # 重试
        if self.isMicaEffectEnabled():
            QTimer.singleShot(
                100,
                lambda: self.windowEffect.setMicaEffect(self.winId(), isDarkTheme()),
            )
