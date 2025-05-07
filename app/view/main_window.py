import os
import sys

from PyQt6.QtCore import QSize, QTimer, Qt

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication

from qfluentwidgets import (
    NavigationItemPosition,
    FluentWindow,
    SplashScreen,
    SystemThemeListener,
    isDarkTheme,
    InfoBar

)
from qfluentwidgets import FluentIcon as FIF

from .setting_interface import SettingInterface
from .task_interface import TaskInterface
from .custom_setting_interface import CustomSettingInterface
from .scheduled_interface import ScheduledInterface
from ..common.config import cfg
from ..common.signal_bus import signalBus
from ..common import resource
from ..utils.logger import logger
from ..common.maa_config_data import maa_config_data


class MainWindow(FluentWindow):

    def __init__(self):
        super().__init__()
        self.initWindow()

        # 创建系统主题监听器
        self.themeListener = SystemThemeListener(self)

        # 创建子界面
        self.taskInterface = TaskInterface(self)
        self.settingInterface = SettingInterface(self)
        self.scheduledInterface = ScheduledInterface(self)
        self.customsettingInterface = CustomSettingInterface(self)

        # 启用Fluent主题效果
        self.navigationInterface.setAcrylicEnabled(True)

        self.connectSignalToSlot()

        # 添加导航项
        self.initNavigation()
        self.splashScreen.finish()

        # 启动主题监听器
        self.themeListener.start()
        if "adb" in self.taskInterface.Control_Combox.currentText().lower():
            signalBus.setting_Visible.emit("adb")
        elif "win32" in self.taskInterface.Control_Combox.currentText().lower():
            signalBus.setting_Visible.emit("win32")
        
        signalBus.start_finish.emit()

        logger.info(" 主界面初始化完成。")

    def show_info_bar(self, data_dict: dict):
        """显示信息栏"""
        duration = max(len(data_dict.get("msg", "")) * 100, 2000)
        if data_dict["status"] == "failed":
            InfoBar.error(
                title=self.tr("Error"),
                content=data_dict.get("msg",""),
                duration=duration,
                parent=self,
            )
        elif data_dict["status"] == "warning":
            InfoBar.warning(
                title=self.tr("Warning"),
                content=data_dict.get("msg",""),
                duration=duration,
                parent=self,
            )
        elif data_dict["status"] == "success":
            InfoBar.success(
                title=self.tr("Success"),
                content=data_dict.get("msg",""),
                duration=duration,
                parent=self,
            )
        elif data_dict["status"] == "info":
            InfoBar.info(
                title=self.tr("Info"),
                content=data_dict.get("msg",""),
                duration=duration,
                parent=self,
            )
        elif data_dict["status"] == "failed_info":
            InfoBar.error(
                title=self.tr("Error"),
                content=data_dict.get("msg",""),
                duration=duration,
                parent=self,
            
            )
        elif data_dict["status"] == "no_need":  
            InfoBar.success(
                title=self.tr("Success"),
                content=data_dict.get("msg",""),
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

    def initNavigation(self):
        """初始化导航界面。"""

        self.navigationInterface.addSeparator()

        # 判断是否存在自定义配置文件
        if os.path.exists(os.path.join(os.getcwd(), "config", "custom_setting.json")):
            self.addSubInterface(self.taskInterface, FIF.CHECKBOX, self.tr("Task"))
            self.addSubInterface(
                self.scheduledInterface, FIF.CALENDAR, self.tr("Scheduling tasks")
            )
            self.addSubInterface(
                self.customsettingInterface, FIF.APPLICATION, self.tr("Custom Setting")
            )
            self.addSubInterface(
                self.settingInterface,
                FIF.SETTING,
                self.tr("Setting"),
                NavigationItemPosition.BOTTOM,
            )
        else:
            logger.info(" 未检测到自定义配置文件，启用默认设置界面。")
            self.addSubInterface(self.taskInterface, FIF.CHECKBOX, self.tr("Task"))
            self.addSubInterface(
                self.scheduledInterface, FIF.CALENDAR, self.tr("Scheduling tasks")
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
            title +=f" {version}"
        if config_name != "":
            title += f" {config_name}"
        if self.is_admin():
            title += " " + self.tr("admin")
        if cfg.get(cfg.save_draw) or cfg.get(cfg.recording) or cfg.get(cfg.show_hit_draw):
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
