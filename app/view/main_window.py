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
from PySide6.QtGui import QIcon, QShortcut, QKeySequence
from PySide6.QtWidgets import QApplication

from qfluentwidgets import (
    NavigationItemPosition,
    FluentWindow,
    SplashScreen,
    SystemThemeListener,
    isDarkTheme,
    InfoBar,
)
from qfluentwidgets import FluentIcon as FIF


from .task_interface import TaskInterface
from .resource_setting_interface import ResourceSettingInterface
from .task_cooldown_interface import TaskCooldownInterface
from .assist_tool_task_interface import AssistToolTaskInterface
from .setting_interface import SettingInterface
from ..common.config import cfg
from ..common.signal_bus import signalBus
from ..common import resource
from ..utils.logger import logger
from ..common.maa_config_data import maa_config_data
from ..utils.notice_message import NoticeMessageBox
from..utils.notice_enum import NoticeErrorCode


class MainWindow(FluentWindow):

    def __init__(self):
        super().__init__()
        self.initWindow()

        # 创建系统主题监听器
        self.themeListener = SystemThemeListener(self)

        # 创建子界面
        self.taskInterface = TaskInterface(self)
        self.resourceSettingInterface = ResourceSettingInterface(self)
        self.TaskCooldownInterface = TaskCooldownInterface(self)
        self.AssistToolTaskInterface = AssistToolTaskInterface(self)
        self.settingInterface = SettingInterface(self)

        # 启用Fluent主题效果
        self.navigationInterface.setAcrylicEnabled(True)

        self.connectSignalToSlot()

        # 记录 AssistToolTaskInterface 导航项索引
        self.AssistTool_task_nav_index = None

        # 添加导航项
        self.initNavigation()
        self.splashScreen.finish()

        # 启动主题监听器
        self.themeListener.start()
        if "adb" in self.taskInterface.Control_Combox.currentText().lower():
            signalBus.setting_Visible.emit("adb")
        elif "win32" in self.taskInterface.Control_Combox.currentText().lower():
            signalBus.setting_Visible.emit("win32")
        self.initShortcuts()

        self.stara_finish()

        logger.info(" 主界面初始化完成。")

    def stara_finish(self):
        """启动完成后的操作"""
        if cfg.get(cfg.auto_update_MFW):
            self.settingInterface.update_self_func()
        if (
            maa_config_data.config.get("adb", {}).get("adb_path") == ""
            and "adb" not in self.taskInterface.Control_Combox.currentText()
        ):
            self.taskInterface.AutoDetect_Button.click()
        if cfg.get(cfg.resource_exist):

            if cfg.get(cfg.auto_update_resource) and (
                cfg.get(cfg.run_after_startup) or cfg.get(cfg.run_after_startup_arg)
            ):
                logger.info("启动GUI后自动更新,启动GUI后运行任务")
                signalBus.update_download_finished.connect(
                    self.taskInterface.Auto_update_Start_up
                )
                QTimer.singleShot(1000, lambda: signalBus.auto_update.emit())

            elif cfg.get(cfg.auto_update_resource):
                logger.info("启动GUI后自动更新")
                QTimer.singleShot(1000, lambda: signalBus.auto_update.emit())

            elif cfg.get(cfg.run_after_startup) or cfg.get(cfg.run_after_startup_arg):
                logger.info("启动GUI后运行任务")
                # Qtimer 延迟1秒启动signalBus.start_task_inmediately.emit()
                QTimer.singleShot(1000, lambda: signalBus.start_task_inmediately.emit())

    def initShortcuts(self):
        """初始化快捷键"""
        # ALT+R 切换下一个资源
        QShortcut(QKeySequence("Alt+R"), self).activated.connect(self.nextResource)

        # ALT+SHIFT+R 切换上一个资源
        QShortcut(QKeySequence("Alt+Shift+R"), self).activated.connect(
            self.prevResource
        )

        # ALT+C 切换下一个配置
        QShortcut(QKeySequence("Alt+C"), self).activated.connect(self.nextConfig)

        # ALT+SHIFT+C 切换上一个配置
        QShortcut(QKeySequence("Alt+Shift+C"), self).activated.connect(self.prevConfig)

    def nextResource(self):
        """切换到下一个资源"""
        current_index = self.resourceSettingInterface.res_setting.combox.currentIndex()
        count = self.resourceSettingInterface.res_setting.combox.count()
        if current_index < count - 1:
            self.resourceSettingInterface.res_setting.combox.setCurrentIndex(
                current_index + 1
            )

    def prevResource(self):
        """切换到上一个资源"""
        current_index = self.resourceSettingInterface.res_setting.combox.currentIndex()
        if current_index > 0:
            self.resourceSettingInterface.res_setting.combox.setCurrentIndex(
                current_index - 1
            )

    def nextConfig(self):
        """切换到下一个配置"""
        current_index = self.resourceSettingInterface.cfg_setting.combox.currentIndex()
        count = self.resourceSettingInterface.cfg_setting.combox.count()
        if current_index < count - 1:
            self.resourceSettingInterface.cfg_setting.combox.setCurrentIndex(
                current_index + 1
            )

    def prevConfig(self):
        """切换到上一个配置"""
        current_index = self.resourceSettingInterface.cfg_setting.combox.currentIndex()
        if current_index > 0:
            self.resourceSettingInterface.cfg_setting.combox.setCurrentIndex(
                current_index - 1
            )

    def show_info_bar(self, data_dict: dict):
        """显示信息栏"""
        duration = max(len(data_dict.get("msg", "")) * 100, 2000)
        if data_dict["status"] in ["failed", "failed_info"]:
            InfoBar.error(
                title=self.tr("Error"),
                content=data_dict.get("msg", ""),
                duration=duration,
                parent=self,
            )
        elif data_dict["status"] == "warning":
            InfoBar.warning(
                title=self.tr("Warning"),
                content=data_dict.get("msg", ""),
                duration=duration,
                parent=self,
            )
        elif data_dict["status"] in ["success", "no_need"]:
            InfoBar.success(
                title=self.tr("Success"),
                content=data_dict.get("msg", ""),
                duration=duration,
                parent=self,
            )
        elif data_dict["status"] == "info":
            InfoBar.info(
                title=self.tr("Info"),
                content=data_dict.get("msg", ""),
                duration=duration,
                parent=self,
            )

    def connectSignalToSlot(self):
        """连接信号到槽函数。"""
        signalBus.micaEnableChanged.connect(self.setMicaEffectEnabled)
        signalBus.title_changed.connect(self.set_title)
        signalBus.bundle_download_finished.connect(self.show_info_bar)
        signalBus.download_finished.connect(self.show_info_bar)
        signalBus.update_download_finished.connect(self.show_info_bar)
        signalBus.mirror_bundle_download_finished.connect(self.show_info_bar)
        signalBus.download_self_finished.connect(self.show_info_bar)
        signalBus.infobar_message.connect(self.show_info_bar)
        signalBus.show_AssistTool_task.connect(self.toggle_AssistTool_task)
        signalBus.notice_finished.connect(self.show_notice_finished)
    def show_notice_finished(self, error_code: NoticeErrorCode,name:str):
        """显示外部通知完成信息"""
        if error_code == NoticeErrorCode.SUCCESS:
            msg = self.tr("Send message success")
        elif error_code == NoticeErrorCode.DISABLED:
            msg = self.tr("Notification is disabled, cannot send message")
        elif error_code == NoticeErrorCode.PARAM_EMPTY:
            msg = self.tr("Required parameters are empty, send failed")
        elif error_code == NoticeErrorCode.PARAM_INVALID:
            msg = self.tr("Parameter format is invalid, send failed")
        elif error_code == NoticeErrorCode.NETWORK_ERROR:
            msg = self.tr("Network request failed, send failed")
        elif error_code == NoticeErrorCode.RESPONSE_ERROR:
            msg = self.tr("Server response error, send failed")
        elif error_code == NoticeErrorCode.SMTP_PORT_INVALID:
            msg = self.tr("SMTP port is invalid, send failed")
        elif error_code == NoticeErrorCode.SMTP_CONNECT_FAILED:
            msg = self.tr("SMTP connection failed, send failed")
        else:
            msg = self.tr("Unknown error, send failed")

        if error_code == NoticeErrorCode.SUCCESS:
            self.show_info_bar({"status": "success", "msg": name+":"+msg})
        else:
            self.show_info_bar({"status": "failed", "msg": name+":"+msg})

            
    def initNavigation(self):
        """初始化导航界面。"""

        self.navigationInterface.addSeparator()

        self.addSubInterface(self.taskInterface, FIF.CHECKBOX, self.tr("Task"))
        self.addSubInterface(
            self.resourceSettingInterface,
            FIF.FOLDER,
            self.tr("Resource Setting"),
        )
        TaskCooldown = self.addSubInterface(
            self.TaskCooldownInterface,
            FIF.CALENDAR,
            self.tr("TaskCooldown"),
        )
        TaskCooldown.clicked.connect(signalBus.TaskCooldownPageClicked)
        self.addSubInterface(
            self.AssistToolTaskInterface,
            FIF.ALBUM,
            self.tr("Assis Tool Task"),
            NavigationItemPosition.SCROLL,
        )
        self.navigationInterface.addItem(
            routeKey="Announcement",
            icon=FIF.MEGAPHONE,
            text=self.tr("Announcement"),
            onClick=self.show_announcement,
            selectable=False,
            tooltip=self.tr("Announcement"),
            position=NavigationItemPosition.BOTTOM,
        )

        self.addSubInterface(
            self.settingInterface,
            FIF.SETTING,
            self.tr("Setting"),
            NavigationItemPosition.BOTTOM,
        )

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
        version = maa_config_data.interface_config.get("version", "")
        version_file_path = os.path.join(os.getcwd(), "config", "version.txt")
        with open(version_file_path, "r", encoding="utf-8") as f:
            version_data = f.read().split()
        if version_data[2]:
            title += f" {version_data[2]}"
        if resource_name != "":
            title += f" {resource_name}"
        if version != "":
            title += f" {version}"
        if config_name != "":
            title += f" {config_name}"
        if self.is_admin():
            title += " " + self.tr("admin")
        if (
            cfg.get(cfg.save_draw)
            or cfg.get(cfg.recording)
            or cfg.get(cfg.show_hit_draw)
        ):
            title += " " + self.tr("Debug")

        logger.info(f" 设置窗口标题：{title}")
        self.setWindowTitle(title)

    def initWindow(self):
        """初始化窗口设置。"""
        self.resize(960, 780)
        self.setMinimumWidth(760)
        self.setWindowIcon(QIcon("./MFW_resource/icon/logo.png"))
        self.set_title()
        self.setMicaEffectEnabled(cfg.get(cfg.micaEnabled))

        # 创建启动画面
        self.splashScreen = SplashScreen(self.windowIcon(), self)
        self.splashScreen.setIconSize(QSize(106, 106))
        self.splashScreen.raise_()

        desktop = QApplication.screens()[0].availableGeometry()
        w, h = desktop.width(), desktop.height()
        self.move(w // 2 - self.width() // 2, h // 2 - self.height() // 2)
        self.show()
        QApplication.processEvents()

        # 显示公告 MessageBox
        if (
            cfg.get(cfg.show_notice)
            or maa_config_data.interface_config.get("show_notice")
        ) and not cfg.get(cfg.hide_notice):

            QTimer.singleShot(500, self.show_announcement)

    def show_announcement(self):
        """显示公告 MessageBox"""
        title = self.tr("Announcement")

        with open("./MFW_resource/doc/Announcement.md", "r", encoding="utf-8") as f:
            gui_announced = f.read()

        try:
            with open(
                os.path.join(maa_config_data.resource_path, "Announcement.md"),
                "r",
                encoding="utf-8",
            ) as f:
                resource = f.read()
        except Exception as e:
            resource = None
        content = {}
        content[self.tr("MFW Announcement")] = gui_announced
        if resource:
            content[self.tr("Resource Announcement")] = resource

        w = NoticeMessageBox(self, title, content)
        w.setClosableOnMaskClicked(True)

        # enable dragging
        w.setDraggable(True)

        if w.exec():
            print("OK clicked")
            cfg.set(cfg.hide_notice, True)

        cfg.set(cfg.show_notice, False)

    def resizeEvent(self, e):
        """重写尺寸事件。"""
        super().resizeEvent(e)
        if hasattr(self, "splashScreen"):
            self.splashScreen.resize(self.size())

    def closeEvent(self, e):
        """关闭事件"""
        self.themeListener.terminate()
        self.themeListener.deleteLater()
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

    def toggle_AssistTool_task(self, show: bool):
        """根据布尔值显示或隐藏 AssistToolTaskInterface 界面"""
        if show:
            self.addSubInterface(
                self.AssistToolTaskInterface,
                FIF.ALBUM,
                self.tr("AssistTool Task"),
                NavigationItemPosition.SCROLL,
            )
        else:
            self.removeInterface(self.AssistToolTaskInterface)
