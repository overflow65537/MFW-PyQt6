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

import os
import sys

from PySide6.QtCore import QSize, QTimer
from PySide6.QtGui import QIcon, QShortcut, QKeySequence, QGuiApplication
from PySide6.QtWidgets import QApplication

from qfluentwidgets import (
    NavigationItemPosition,
    FluentWindow,
    SplashScreen,
    SystemThemeListener,
    isDarkTheme,
    InfoBar,
    MSFluentWindow
)
from qfluentwidgets import FluentIcon as FIF


from .fast_start_interface.fast_start_logic import FastStartInterface

import atexit
from ..common.config import cfg
from ..common.signal_bus import signalBus
from ..utils.logger import logger
from ..common.__version__ import __version__
from ..core.TaskManager import TaskManager


class CustomSystemThemeListener(SystemThemeListener):
    def run(self):
        try:
            super().run()
        except NotImplementedError:
            logger.error("当前环境不支持主题监听，已忽略")


class MainWindow(MSFluentWindow):

    def __init__(self):
        super().__init__()
        self.initWindow()
        # 使用自定义的主题监听器
        self.themeListener = CustomSystemThemeListener(self)

        # 初始化任务管理器
        self.task_manager = TaskManager(cfg.get(cfg.maa_config_name), cfg.get(cfg.maa_config_list))

        # 创建子界面
        self.FastStartInterface = FastStartInterface(parent=self)
        self.FastStartInterface.task_info.task_list.set_task_manager(self.task_manager)
        self.task_manager.tasks_changed.emit()



        self.addSubInterface(self.FastStartInterface, FIF.CHECKBOX, self.tr("Task"))


        # 添加导航项
        self.splashScreen.finish()

        # 启动主题监听器
        self.themeListener.start()

        logger.info(" 主界面初始化完成。")

    def initWindow(self):
        """初始化窗口设置。"""
        self.resize(1170, 760)
        self.setMinimumWidth(1170)
        self.setMinimumHeight(760)
        self.setWindowIcon(QIcon("./MFW_resource/icon/logo.png"))
        self.set_title()
        self.setMicaEffectEnabled(cfg.get(cfg.micaEnabled))

        # 创建启动画面
        self.splashScreen = SplashScreen(self.windowIcon(), self)
        self.splashScreen.setIconSize(QSize(106, 106))
        self.splashScreen.raise_()

        # 设置启动位置
        desktop = QApplication.screens()[0].availableGeometry()
        w, h = desktop.width(), desktop.height()
        self.move(w // 2 - self.width() // 2, h // 2 - self.height() // 2)
        self.show()
        QApplication.processEvents()


    def connectSignalToSlot(self):
        """连接信号到槽函数。"""
        signalBus.micaEnableChanged.connect(self.setMicaEffectEnabled)
        signalBus.title_changed.connect(self.set_title)

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
        title = cfg.get(cfg.title)
        if not title:
            title = self.tr("ChainFlow Assistant")
        resource_name = cfg.get(cfg.maa_resource_name)
        config_name = cfg.get(cfg.maa_config_name)
        #version = res_cfg.interface_config.get("version", "")

        title += f" {__version__}"

        if resource_name != "":
            title += f" {resource_name}"
        """if version != "":
            title += f" {version}"""
        if config_name != "":
            title += f" {config_name}"
        if self.is_admin():
            title += " " + self.tr("admin")
        if cfg.get(cfg.save_draw) or cfg.get(cfg.recording):
            title += " " + self.tr("Debug")

        logger.info(f" 设置窗口标题：{title}")
        self.setWindowTitle(title)

    def resizeEvent(self, e):
        """重写尺寸事件。"""
        super().resizeEvent(e)
        if hasattr(self, "splashScreen"):
            self.splashScreen.resize(self.size())

    def closeEvent(self, e):
        """关闭事件"""
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
