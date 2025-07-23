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
from ..utils.notice_enum import NoticeErrorCode
from ..utils.widget import NoticeType, SendSettingCard, ShowDownload
from ..utils.tool import Save_Config, Get_Values_list
from ..utils.maafw import maafw
from ..common.__version__ import __version__


class CustomSystemThemeListener(SystemThemeListener):
    def run(self):
        try:
            # 调用原始的 run 方法
            super().run()
        except NotImplementedError:
            print("当前环境不支持主题监听，已忽略", file=sys.stderr)


class MainWindow(FluentWindow):

    def __init__(self):
        super().__init__()
        self.initWindow()

        # 使用自定义的主题监听器
        self.themeListener = CustomSystemThemeListener(self)

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

        # 初始化通知对象
        self.dingtalk = NoticeType(self, "DingTalk")
        self.lark = NoticeType(self, "Lark")
        self.smtp = NoticeType(self, "SMTP")
        self.wxpusher = NoticeType(self, "WxPusher")
        self.QYWX = NoticeType(self, "QYWX")
        self.send_setting = SendSettingCard(self)

        # 启动主题监听器
        self.themeListener.start()
        if "adb" in self.taskInterface.Control_Combox.currentText().lower():
            signalBus.setting_Visible.emit("adb")
        elif "win32" in self.taskInterface.Control_Combox.currentText().lower():
            signalBus.setting_Visible.emit("win32")
        self.initShortcuts()
        self.update_failed()
        self.stara_finish()

        QTimer.singleShot(5000, lambda: cfg.set(cfg.start_complete, True))
        maafw.change_log_path(maa_config_data.log_path)

        logger.info(" 主界面初始化完成。")

    def update_failed(self):
        cfg.set(cfg.update_ui_failed, False)
        if os.path.exists("ERROR.log"):
            cfg.set(cfg.update_ui_failed, True)
            self.show_info_bar(
                {
                    "status": "failed",
                    "msg": self.tr("Update Failed, Please Check Log File"),
                }
            )
            with open("ERROR.log", "r") as log_file:
                log_content = log_file.read()
                logger.error(f"更新UI失败: {log_content}")
            os.remove("ERROR.log")

    def dingtalk_setting(self):
        if self.dingtalk.exec():
            if cfg.get(cfg.Notice_DingTalk_status):
                self.settingInterface.dingtalk_noticeTypeCard.setContent(
                    self.tr("DingTalk Notification Enabled")
                )
            else:
                self.settingInterface.dingtalk_noticeTypeCard.setContent(
                    self.tr("DingTalk Notification Disabled")
                )

    def lark_setting(self):
        if self.lark.exec():
            if cfg.get(cfg.Notice_Lark_status):
                self.settingInterface.lark_noticeTypeCard.setContent(
                    self.tr("Lark Notification Enabled")
                )
            else:
                self.settingInterface.lark_noticeTypeCard.setContent(
                    self.tr("Lark Notification Disabled")
                )

    def smtp_setting(self):
        if self.smtp.exec():
            if cfg.get(cfg.Notice_SMTP_status):
                self.settingInterface.SMTP_noticeTypeCard.setContent(
                    self.tr("SMTP Notification Enabled")
                )
            else:
                self.settingInterface.SMTP_noticeTypeCard.setContent(
                    self.tr("SMTP Notification Disabled")
                )

    def wxpusher_setting(self):
        if self.wxpusher.exec():
            if cfg.get(cfg.Notice_WxPusher_status):
                self.settingInterface.WxPusher_noticeTypeCard.setContent(
                    self.tr("WXPusher Notification Enabled")
                )
            else:
                self.settingInterface.WxPusher_noticeTypeCard.setContent(
                    self.tr("WXPusher Notification Disabled")
                )

    def QYWX_setting(self):
        if self.QYWX.exec():
            if cfg.get(cfg.Notice_QYWX_status):
                self.settingInterface.QYWX_noticeTypeCard.setContent(
                    self.tr("QYWX Notification Enabled")
                )
            else:
                self.settingInterface.QYWX_noticeTypeCard.setContent(
                    self.tr("QYWX Notification Disabled")
                )

    def stara_finish(self):
        """启动完成后的操作"""
        if (
            maa_config_data.config.get("adb", {}).get("adb_path") == ""
            and "adb" not in self.taskInterface.Control_Combox.currentText()
        ):
            self.taskInterface.AutoDetect_Button.click()

        if cfg.get(cfg.resource_exist) and cfg.get(cfg.auto_update_resource):
            logger.info("启动GUI后自动更新资源")

            signalBus.update_download_finished.connect(self.on_resource_update_finished)
            # signalBus.update_download_stopped.connect(self.on_resource_update_finished)
            self.settingInterface.update_check()
        else:
            self.check_ui_update()

    def on_resource_update_finished(self, return_dict):
        """资源更新完成后的处理"""
        logger.info("资源更新完成")
        if return_dict.get("status") in ["success", "failed", "no_need"]:
            self.check_ui_update()

    def check_ui_update(self):
        """检查是否需要自动更新UI"""
        if cfg.get(cfg.auto_update_MFW):
            logger.info("启动GUI后自动更新UI")
            # 连接UI更新完成信号，更新完成后执行下一步
            signalBus.download_self_finished.connect(self.on_ui_update_finished)
            signalBus.download_self_stopped.connect(self.on_ui_update_stopped)
            if not cfg.get(cfg.update_ui_failed):
                self.settingInterface.update_self_func()
        else:
            # 若不需要更新UI，直接检查是否需要开始任务
            self.check_start_task()

    def on_ui_update_stopped(self):
        """UI更新完成后的处理"""
        logger.info("UI更新中断")

    def on_ui_update_finished(self, return_dict=None):
        """UI更新完成后的处理"""
        logger.info("UI更新完成")
        try:
            if return_dict is None:
                return_dict = {}
            if return_dict.get("status") in ["success", "failed", "no_need"]:
                if self.settingInterface.aboutCard.button2.text() == self.tr(
                    "Update Now"
                ):
                    self.settingInterface.aboutCard.button2.click()
                else:
                    self.check_start_task()
        except Exception as e:
            logger.error(f"UI更新完成后处理异常: {e}")

    def check_start_task(self):
        """检查是否需要开始任务"""
        if cfg.get(cfg.run_after_startup) or cfg.get(cfg.run_after_startup_arg):
            logger.info("启动GUI后运行任务")
            if self.taskInterface.S2_Button.text() in ["Start", "开始", "開始"]:
                QTimer.singleShot(500, self.taskInterface.Start_Up)

    def show_download(self):
        """显示下载窗口"""
        w = ShowDownload(self)
        w.show()

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
        elif data_dict["status"] == "error_sp":
            if data_dict["type"] == "advanced":
                error_msg = (
                    self.tr("advanced setting [")
                    + data_dict.get("msg", [])[0]
                    + self.tr("] value [")
                    + data_dict.get("msg", [])[1]
                    + self.tr("] not match regex [")
                    + data_dict.get("msg", [])[2]
                    + "]"
                )
                InfoBar.error(
                    title=self.tr("Error"),
                    content=error_msg,
                    duration=duration,
                    parent=self,
                )
                self.taskInterface.S2_Button.click()
    def connectSignalToSlot(self):
        """连接信号到槽函数。"""
        signalBus.show_download.connect(self.show_download)
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
        self.settingInterface.dingtalk_noticeTypeCard.button.clicked.connect(
            self.dingtalk_setting
        )
        self.settingInterface.lark_noticeTypeCard.button.clicked.connect(
            self.lark_setting
        )
        self.settingInterface.SMTP_noticeTypeCard.button.clicked.connect(
            self.smtp_setting
        )
        self.settingInterface.WxPusher_noticeTypeCard.button.clicked.connect(
            self.wxpusher_setting
        )
        self.settingInterface.QYWX_noticeTypeCard.button.clicked.connect(
            self.QYWX_setting
        )
        self.settingInterface.send_settingCard.button.clicked.connect(
            self.send_setting_setting
        )

    def send_setting_setting(self):
        if self.send_setting.exec():
            self.send_setting.save_setting()
            print("发送设置已更改")

    def show_notice_finished(self, error_code: NoticeErrorCode, name: str):
        """显示外部通知完成信息"""
        name_mapping = {
            "dingtalk_send": self.dingtalk,
            "lark_send": self.lark,
            "SMTP_send": self.smtp,
            "WxPusher_send": self.wxpusher,
            "QYWX_send": self.QYWX,
        }
        if name in name_mapping:
            name_mapping[name].notice_send_finished()
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
            self.show_info_bar({"status": "success", "msg": name + ":" + msg})
        else:
            self.show_info_bar({"status": "failed", "msg": name + ":" + msg})

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

        title += f" {__version__}"

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

    def read_announcement_file(self, file_path):
        """
        读取指定路径的公告文件，返回标题和内容。

        :param file_path: 公告文件的路径
        :return: 标题和内容，若文件读取失败则返回 None, None
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
                if lines:
                    title = lines[0].strip()
                    content = "".join(lines[1:])
                    return title, content
        except Exception as e:
            logger.error(f"读取文件 {file_path} 失败，错误信息：{e}")
        return None, None

    def show_announcement(self):
        """显示公告 MessageBox"""
        title = self.tr("Announcement")
        content = {}

        # 读取 MFW 公告
        gui_announce_path = os.path.join(".", "MFW_resource", "doc", "Announcement.md")
        gui_title, gui_announced = self.read_announcement_file(gui_announce_path)
        if gui_announced:
            content[self.tr("MFW Announcement")] = gui_announced

        # 读取 MFW 更新日志
        mfw_changelog_path = os.path.join(".", "MFW_changelog.md")
        mfw_changelog_title, MFW_Changelog = self.read_announcement_file(
            mfw_changelog_path
        )
        if MFW_Changelog:
            content[self.tr("MFW Changelog")] = MFW_Changelog

        # 读取资源公告文件夹里的所有 md 文件
        resource_announce_folder = os.path.join(
            maa_config_data.resource_path, "announcement"
        )
        if os.path.isdir(resource_announce_folder):
            for root, _, files in os.walk(resource_announce_folder):
                for file in sorted(files):
                    if file.lower().endswith(".md") and file != "resource_changelog.md":
                        file_path = os.path.join(root, file)
                        custom_title, custom_content = self.read_announcement_file(
                            file_path
                        )
                        if custom_content:
                            content[custom_title or file] = custom_content

        # 读取资源更新日志
        resource_changelog_path = os.path.join(
            maa_config_data.resource_path, "resource_changelog.md"
        )
        resource_changelog_title, resource_Changelog = self.read_announcement_file(
            resource_changelog_path
        )
        if resource_Changelog:
            content[self.tr("Resource Changelog")] = resource_Changelog

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
