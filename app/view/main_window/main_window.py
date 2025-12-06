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


import asyncio
import shutil
import sys
import threading
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from PySide6.QtCore import QSize, QTimer, Qt, QUrl
from PySide6.QtGui import (
    QIcon,
    QShortcut,
    QKeySequence,
    QGuiApplication,
    QDesktopServices,
)
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


from app.view.task_interface.task_interface_logic import TaskInterface
from app.view.monitor_interface import MonitorInterface
from app.view.schedule_interface.schedule_interface import ScheduleInterface
from app.view.setting_interface.setting_interface import SettingInterface
from app.view.test_interface.test_interface import TestInterface
from app.common.config import cfg
from app.common.signal_bus import signalBus
from app.utils.hotkey_manager import GlobalHotkeyManager
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

    _LOCKED_LOG_NAMES = {"maa.log", "clash.log", "maa.log.bak"}

    def __init__(self, loop: asyncio.AbstractEventLoop | None = None):
        super().__init__()
        self._loop = loop

        # 使用自定义的主题监听器
        self.themeListener = CustomSystemThemeListener(self)

        # 初始化配置管理器
        multi_config_path = Path.cwd() / "config" / "multi_config.json"
        self.service_coordinator = ServiceCoordinator(multi_config_path)

        self._announcement_pending_show = False
        self._log_zip_running = False
        self._log_zip_infobar: InfoBar | None = None
        self._init_announcement()

        # 初始化窗口
        self.initWindow()
        # 创建子界面
        self.TaskInterface = TaskInterface(self.service_coordinator)
        self.addSubInterface(self.TaskInterface, FIF.CHECKBOX, self.tr("Task"))
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
        try:
            event_loop = self._loop or asyncio.get_event_loop()
        except RuntimeError:
            event_loop = None
        self._hotkey_manager = GlobalHotkeyManager(event_loop)
        self._hotkey_manager.setup(
            start_factory=lambda: self.service_coordinator.run_tasks_flow(),
            stop_factory=lambda: self.service_coordinator.stop_task(),
        )
        signalBus.hotkey_shortcuts_changed.connect(self._reload_global_hotkeys)
        self._reload_global_hotkeys()

        logger.info(" 主界面初始化完成。")

    def initWindow(self):
        """初始化窗口设置。"""
        self.resize(1170, 760)
        self.setMinimumWidth(1170)
        self.setMinimumHeight(760)
        self.set_title()
        self.setMicaEffectEnabled(cfg.get(cfg.micaEnabled))

        # 设置图标
        icon_path = self.service_coordinator.task.interface.get(
            "icon", "./app/assets/icons/logo.png"
        )
        icon_path = Path(icon_path)
        if not icon_path.is_absolute():
            icon_path = Path.cwd() / icon_path
        if not icon_path.exists():
            logger.warning(" 配置的图标不存在，使用默认图标：%s", icon_path)
            icon_path = Path.cwd() / "./app/assets/icons/logo.png"
        self.setWindowIcon(QIcon(str(icon_path)))

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
        signalBus.request_log_zip.connect(self._on_request_log_zip)

    def _reload_global_hotkeys(self):
        """配置变更后重新注册全局快捷键。"""
        if getattr(self, "_hotkey_manager", None):
            self._hotkey_manager.reload()

    def _on_request_log_zip(self):
        """处理日志打包请求，避免重复执行。"""
        if self._log_zip_running:
            signalBus.info_bar_requested.emit(
                "warning", self.tr("Log is being packaged, please wait...")
            )
            return

        self._log_zip_running = True
        signalBus.log_zip_started.emit()
        self._show_log_zip_progress_infobar()
        threading.Thread(target=self._generate_log_zip, daemon=True).start()

    def _generate_log_zip(self):
        """将 debug 目录打包为 zip，并兼容被占用的日志文件。"""
        debug_dir = Path.cwd() / "debug"
        if not debug_dir.exists() or not debug_dir.is_dir():
            self._close_log_zip_progress()
            signalBus.info_bar_requested.emit(
                "error", self.tr("Debug directory not found, cannot package logs.")
            )
            self._log_zip_running = False
            signalBus.log_zip_finished.emit()
            return

        zip_path = self._build_log_zip_path()
        errors: list[str] = []
        try:
            with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
                for file_path in debug_dir.rglob("*"):
                    if file_path.is_dir():
                        continue
                    arcname = f"{debug_dir.name}/{file_path.relative_to(debug_dir).as_posix()}"
                    if file_path.name in self._LOCKED_LOG_NAMES:
                        self._write_locked_log(zf, file_path, arcname, errors)
                    else:
                        self._write_file_to_zip(zf, file_path, arcname, errors)

            self._close_log_zip_progress()
            self._notify_log_zip_result(zip_path, errors)
            self._open_debug_dir(debug_dir)
            logger.info(" 日志压缩包生成完成：%s", zip_path)
        except Exception as exc:
            logger.exception("生成日志压缩包失败")
            self._close_log_zip_progress()
            signalBus.info_bar_requested.emit(
                "error", self.tr("Log packaging failed:") + str(exc)
            )
        finally:
            self._log_zip_running = False
            signalBus.log_zip_finished.emit()

    def _write_locked_log(
        self,
        zip_file: zipfile.ZipFile,
        file_path: Path,
        arcname: str,
        errors: list[str],
    ) -> None:
        """直接读取被占用的日志文件内容后写入压缩包。"""
        try:
            data = file_path.read_bytes()
            zip_file.writestr(arcname, data)
        except Exception as exc:
            errors.append(f"{arcname} ({exc})")
            logger.warning(" 读取占用日志失败：%s (%s)", file_path, exc)

    def _write_file_to_zip(
        self,
        zip_file: zipfile.ZipFile,
        file_path: Path,
        arcname: str,
        errors: list[str],
    ) -> None:
        """流式复制文件到压缩包，单个文件出错不影响整体。"""
        try:
            with file_path.open("rb") as src, zip_file.open(arcname, "w") as dest:
                shutil.copyfileobj(src, dest, length=1024 * 512)
        except Exception as exc:
            errors.append(f"{arcname} ({exc})")
            logger.warning(" 添加日志文件失败：%s (%s)", file_path, exc)

    def _build_log_zip_path(self) -> Path:
        """生成日志压缩包路径（放在 debug 目录内），如已存在则删除后重建。"""
        debug_dir = Path.cwd() / "debug"
        zip_path = debug_dir / "debug.zip"
        try:
            if zip_path.exists():
                zip_path.unlink()
        except Exception as exc:
            logger.warning(" 删除已有 debug.zip 失败：%s", exc)
        return zip_path

    def _notify_log_zip_result(self, zip_path: Path, errors: list[str]) -> None:
        """汇报日志打包结果并提示可能跳过的文件。"""
        if errors:
            preview = "; ".join(errors[:3])
            more_count = len(errors) - len(errors[:3])
            suffix = ""
            if more_count > 0:
                suffix = (
                    self.tr(", there are ")
                    + str(more_count)
                    + self.tr(" files not added")
                )
            signalBus.info_bar_requested.emit(
                "warning",
                self.tr("Log has been packaged, but some files failed to read:")
                + preview
                + suffix,
            )
            return

        signalBus.info_bar_requested.emit(
            "info", self.tr("Log has been packaged:") + str(zip_path.resolve())
        )

    def _show_log_zip_progress_infobar(self):
        """显示“正在压缩”提示。"""
        self._close_log_zip_progress()
        bar = InfoBar.info(
            title=self.tr("Packing logs"),
            content=self.tr("Please wait..."),
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP_RIGHT,
            duration=-1,
            parent=self,
        )
        self._log_zip_infobar = bar

    def _close_log_zip_progress(self):
        """关闭进度 InfoBar（切回主线程执行）。"""
        bar = self._log_zip_infobar
        if not bar:
            return

        def _close():
            if bar:
                bar.close()

        self._invoke_in_ui(_close)
        self._log_zip_infobar = None

    def _open_debug_dir(self, debug_dir: Path):
        """压缩完成后打开 debug 目录。"""
        if not debug_dir.exists():
            return

        def _open():
            try:
                QDesktopServices.openUrl(QUrl.fromLocalFile(str(debug_dir.resolve())))
            except Exception as exc:
                logger.warning(" 打开 debug 目录失败：%s", exc)

        self._invoke_in_ui(_open)

    def _invoke_in_ui(self, func):
        """在 UI 线程异步执行回调。"""
        QTimer.singleShot(0, self, func)

    def _init_announcement(self):
        self._announcement_title = self.tr("Announcement")
        self._announcement_content: Dict[str, str] = {}
        self._announcement_empty_hint = self.tr(
            "There is no announcement at the moment."
        )

        cfg_announcement = cfg.get(cfg.announcement)
        res_announcement = self.service_coordinator.task.interface.get("welcome", "")
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
        logger.info(f" 显示 InfoBar 提示：{message}")

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
        title = (
            self.service_coordinator.task.interface.get("title", "")
            or self.service_coordinator.task.interface.get("custom_title", "")
            or f"{self.service_coordinator.task.interface.get("name", "")} {self.service_coordinator.task.interface.get("version", "")}"
        )
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
        if getattr(self, "_hotkey_manager", None):
            self._hotkey_manager.shutdown()
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
