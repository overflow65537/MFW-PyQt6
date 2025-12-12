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

from pathlib import Path
from typing import Dict, Optional

from PySide6.QtCore import QSize, QTimer, Qt, QUrl
from PySide6.QtGui import (
    QIcon,
    QShortcut,
    QKeySequence,
    QGuiApplication,
    QDesktopServices,
    QPixmap,
)
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QLabel,
    QWidget,
    QGraphicsOpacityEffect,
    QSizePolicy,
    QHBoxLayout,
    QVBoxLayout,
)

from qfluentwidgets import (
    NavigationItemPosition,
    SplashScreen,
    SystemThemeListener,
    isDarkTheme,
    InfoBar,
    InfoBarPosition,
    MSFluentWindow,
    MessageBoxBase,
    BodyLabel,
)
from qfluentwidgets import FluentIcon as FIF


from app.view.task_interface.task_interface_logic import TaskInterface
from app.view.special_task_interface.special_task_interface import (
    SpecialTaskInterface,
)
from app.view.monitor_interface import MonitorInterface
from app.view.schedule_interface.schedule_interface import ScheduleInterface
from app.view.setting_interface.setting_interface import SettingInterface
from app.view.test_interface.test_interface import TestInterface
from app.common.config import cfg
from app.common.signal_bus import signalBus
from app.utils.hotkey_manager import GlobalHotkeyManager
from app.utils.logger import logger
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
    _THEME_LISTENER_TIMEOUT_MS = 2000  # 2 seconds timeout for theme listener thread termination

    def __init__(
        self,
        loop: asyncio.AbstractEventLoop | None = None,
        auto_run: bool = False,
        switch_config_id: str | None = None,
        force_enable_test: bool = False,
    ):
        super().__init__()
        self._loop = loop
        self._cli_auto_run = bool(auto_run)
        self._cli_switch_config_id = (switch_config_id or "").strip() or None
        self._cli_force_enable_test = bool(force_enable_test)
        self._auto_update_thread = None
        self._auto_update_in_progress = False
        self._auto_update_pending_restart = False
        self._pending_auto_run = False
        self._auto_run_scheduled = False
        self._external_updater_started = False

        cfg.set(cfg.save_screenshot,False)

        # 使用自定义的主题监听器
        self.themeListener = CustomSystemThemeListener(self)

        # 初始化配置管理器
        multi_config_path = Path.cwd() / "config" / "multi_config.json"
        self.service_coordinator = ServiceCoordinator(multi_config_path)
        self._apply_cli_switch_config()

        self._announcement_pending_show = False
        self._log_zip_running = False
        self._log_zip_infobar: InfoBar | None = None
        self._background_label: QLabel | None = None
        self._background_pixmap_original: QPixmap | None = None
        self._background_opacity_effect: QGraphicsOpacityEffect | None = None
        self._init_announcement()

        # 初始化窗口
        self.initWindow()
        # 创建子界面
        self.TaskInterface = TaskInterface(self.service_coordinator)
        self.addSubInterface(self.TaskInterface, FIF.CHECKBOX, self.tr("Task"))
        self.SpecialTaskInterface = SpecialTaskInterface(self.service_coordinator)
        self.addSubInterface(
            self.SpecialTaskInterface,
            FIF.CHECKBOX,
            self.tr("Special Task"),
        )
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
        enable_test_page = self._cli_force_enable_test or ENABLE_TEST_INTERFACE_PAGE
        if enable_test_page:
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
        self._bootstrap_auto_update_and_run()
        self._apply_auto_minimize_on_startup()

        logger.info(" 主界面初始化完成。")

    def initWindow(self):
        """初始化窗口设置。"""
        self.resize(1170, 760)
        self.setMinimumWidth(1170)
        self.setMinimumHeight(760)
        self.set_title()
        self.setMicaEffectEnabled(cfg.get(cfg.micaEnabled))
        self._adjust_title_bar_for_macos()

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
        self._init_background_layer()
        QApplication.processEvents()

    def _set_initial_geometry(self):
        """在首次展示前恢复之前的窗口几何，或居中显示。"""
        if not self._restore_window_geometry():
            self._center_window()

    def _adjust_title_bar_for_macos(self):
        """在 macOS 上将窗口按钮移动到左侧并居中标题。"""
        if sys.platform != "darwin":
            return

        title_bar = getattr(self, "titleBar", None)
        if title_bar is None:
            return

        h_layout = getattr(title_bar, "hBoxLayout", None)
        btn_layout = getattr(title_bar, "buttonLayout", None)
        v_layout = getattr(title_bar, "vBoxLayout", None)
        if (
            not isinstance(h_layout, QHBoxLayout)
            or not isinstance(btn_layout, QHBoxLayout)
            or not isinstance(v_layout, QVBoxLayout)
        ):
            return

        def _clear_layout(layout):
            while layout.count():
                item = layout.takeAt(0)
                if item.layout():
                    _clear_layout(item.layout())

        # 调整按钮布局为 macOS 顺序：关闭、最小化、最大化
        _clear_layout(btn_layout)
        btn_layout.setContentsMargins(4, 6, 4, 6)
        btn_layout.setSpacing(6)
        btn_layout.setAlignment(
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft
        )
        for btn in (title_bar.closeBtn, title_bar.minBtn, title_bar.maxBtn):
            btn_layout.addWidget(btn, 0, Qt.AlignmentFlag.AlignVCenter)

        # 预留一个与按钮区等宽的占位，确保标题区域真正居中
        mirror_width = max(
            btn_layout.sizeHint().width(),
            title_bar.closeBtn.sizeHint().width()
            + title_bar.minBtn.sizeHint().width()
            + title_bar.maxBtn.sizeHint().width()
            + btn_layout.spacing() * 2
            + btn_layout.contentsMargins().left()
            + btn_layout.contentsMargins().right(),
        )
        mirror_placeholder = QWidget(title_bar)
        mirror_placeholder.setFixedWidth(mirror_width)
        mirror_placeholder.setSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred
        )

        _clear_layout(v_layout)
        v_layout.setContentsMargins(0, 0, 0, 0)
        v_layout.setSpacing(0)
        v_layout.addLayout(btn_layout)
        v_layout.addStretch(1)

        center_layout = QHBoxLayout()
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(6)
        center_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        center_layout.addWidget(title_bar.iconLabel, 0, Qt.AlignmentFlag.AlignVCenter)
        title_bar.titleLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_bar.titleLabel.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )
        center_layout.addWidget(title_bar.titleLabel, 0, Qt.AlignmentFlag.AlignVCenter)

        center_widget = QWidget(title_bar)
        center_widget.setLayout(center_layout)
        center_widget.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )

        _clear_layout(h_layout)
        h_layout.setContentsMargins(10, 0, 12, 0)
        h_layout.setSpacing(8)
        h_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        h_layout.addLayout(v_layout, 0)
        h_layout.addStretch(1)
        h_layout.addWidget(center_widget, 0, Qt.AlignmentFlag.AlignCenter)
        h_layout.addStretch(1)
        h_layout.addWidget(mirror_placeholder, 0, Qt.AlignmentFlag.AlignVCenter)

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

    def _init_background_layer(self):
        """创建并应用自定义背景层。"""
        if self._background_label is not None:
            return

        self._background_label = QLabel(self)
        self._background_label.setObjectName("appBackgroundLabel")
        self._background_label.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents, True
        )
        self._background_label.setScaledContents(True)
        self._background_opacity_effect = QGraphicsOpacityEffect(self._background_label)
        self._background_label.setGraphicsEffect(self._background_opacity_effect)
        self._apply_background_from_config()
        self._update_background_geometry()
        self._background_label.lower()

    def _apply_background_from_config(self):
        """根据配置加载背景图与透明度。"""
        if self._background_label is None:
            return
        opacity_value = cfg.get(cfg.background_image_opacity)
        self._apply_background_opacity(opacity_value)
        self._load_background_pixmap(cfg.get(cfg.background_image_path))

    def _apply_background_opacity(self, value: int | float | None):
        """更新背景透明度，传入百分比。"""
        if self._background_opacity_effect is None:
            return
        if value is None:
            opacity = 100.0
        else:
            try:
                opacity = float(value)
            except (TypeError, ValueError):
                opacity = 100.0
        opacity = max(0.0, min(100.0, opacity))
        self._background_opacity_effect.setOpacity(opacity / 100.0)

    def _load_background_pixmap(self, path: str | None):
        """加载并应用背景图，若路径为空或无效则隐藏背景。"""
        if self._background_label is None:
            return

        path = str(path or "").strip()
        if not path:
            self._background_pixmap_original = None
            self._background_label.hide()
            return

        candidate = Path(path)
        if not candidate.is_file():
            logger.warning(" 背景图不存在：%s", path)
            self._background_pixmap_original = None
            self._background_label.hide()
            return

        pixmap = QPixmap(str(candidate))
        if pixmap.isNull():
            logger.warning(" 无法加载背景图：%s", path)
            self._background_pixmap_original = None
            self._background_label.hide()
            return

        self._background_pixmap_original = pixmap
        self._background_label.show()
        self._update_background_pixmap()
        self._background_label.lower()

    def _update_background_pixmap(self):
        """缩放并填充背景图。"""
        if self._background_label is None:
            return

        self._background_label.setGeometry(self.rect())
        if not self._background_pixmap_original:
            self._background_label.clear()
            return

        scaled = self._background_pixmap_original.scaled(
            self.size(),
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation,
        )
        self._background_label.setPixmap(scaled)
        self._background_label.lower()

    def _update_background_geometry(self):
        """在窗口尺寸变化时同步背景尺寸。"""
        if self._background_label is None:
            return
        self._background_label.setGeometry(self.rect())
        if self._background_pixmap_original:
            self._update_background_pixmap()

    def _on_background_image_changed(self, path: str):
        """响应设置界面的背景图变更。"""
        self._load_background_pixmap(path)

    def _on_background_opacity_changed(self, value: int):
        """响应设置界面的背景透明度变更。"""
        self._apply_background_opacity(value)

    def connectSignalToSlot(self):
        """连接信号到槽函数。"""
        signalBus.micaEnableChanged.connect(self.setMicaEffectEnabled)
        signalBus.title_changed.connect(self.set_title)
        signalBus.info_bar_requested.connect(self.show_info_bar)
        signalBus.request_log_zip.connect(self._on_request_log_zip)
        signalBus.background_image_changed.connect(self._on_background_image_changed)
        signalBus.background_opacity_changed.connect(
            self._on_background_opacity_changed
        )
        signalBus.update_stopped.connect(self._on_update_stopped_main)

    def _apply_cli_switch_config(self) -> None:
        """处理 CLI 请求的配置切换，在 UI 初始化前执行。"""
        if not self._cli_switch_config_id:
            return
        target = self._cli_switch_config_id
        if self.service_coordinator.select_config(target):
            logger.info("CLI 指定配置已切换: %s", target)
        else:
            logger.warning("CLI 指定配置不存在，保持原配置: %s", target)

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

    def _bootstrap_auto_update_and_run(self) -> None:
        """启动自动更新并串行等待，更新后再执行自动任务。"""
        self._pending_auto_run = bool(
            self._cli_auto_run or cfg.get(cfg.run_after_startup)
        )
        if cfg.get(cfg.auto_update):
            logger.info("自动更新已开启，准备启动自动更新线程")
            self._start_auto_update_thread()
            return
        logger.info("自动更新未开启，直接检查是否需要自动运行任务")
        if self._pending_auto_run:
            self._schedule_auto_run()
            self._pending_auto_run = False

    def _start_auto_update_thread(self) -> None:
        """启动自动更新，复用设置页的更新器并避免重复。"""
        logger.info(
            "进入 _start_auto_update_thread，in_progress=%s",
            self._auto_update_in_progress,
        )
        if self._auto_update_in_progress:
            logger.info("自动更新已在进行，跳过启动")
            return

        setting_interface = getattr(self, "SettingInterface", None)
        if not self.service_coordinator or setting_interface is None:
            logger.warning("自动更新未启动：更新器未就绪")
            if self._pending_auto_run:
                self._schedule_auto_run()
                self._pending_auto_run = False
            return

        started = False
        self._auto_update_in_progress = True
        try:
            started = setting_interface.start_auto_update()
        except Exception as exc:
            logger.error("自动更新启动失败: %s", exc)
            started = False

        if started:
            self._auto_update_thread = getattr(setting_interface, "_updater", None)
            logger.info("自动更新线程已启动，线程对象=%s", self._auto_update_thread)
            return

        self._auto_update_in_progress = False
        self._auto_update_thread = None
        if self._pending_auto_run:
            self._schedule_auto_run()
            self._pending_auto_run = False

    def _schedule_auto_run(self) -> None:
        """根据 CLI 或配置决定是否在启动后自动运行任务。"""
        if self._auto_run_scheduled:
            return
        should_run = self._cli_auto_run or cfg.get(cfg.run_after_startup)
        if not should_run:
            return
        self._auto_run_scheduled = True

        async def _start_flow():
            try:
                await self.service_coordinator.run_tasks_flow()
            except Exception as exc:
                logger.error("启动后自动运行失败: %s", exc)

        QTimer.singleShot(0, lambda: asyncio.create_task(_start_flow()))

    def _on_update_stopped_main(self, status: int):
        """监听更新结束，串行触发自动运行或提示重启。"""
        logger.info(
            "收到更新结束信号，status=%s，pending_auto_run=%s",
            status,
            self._pending_auto_run,
        )
        self._auto_update_in_progress = False
        self._auto_update_thread = None
        if status == 1:
            # 热更新完成后，重新设置窗口标题（延迟到下一个事件循环，确保 reinit 完成）
            QTimer.singleShot(0, self.set_title)
            if self._pending_auto_run:
                self._schedule_auto_run()
            self._pending_auto_run = False
            return
        if status == 2:
            self._auto_update_pending_restart = True
            self._pending_auto_run = False
            setting_interface = getattr(self, "SettingInterface", None)
            logger.info(
                "检测到需要重启完成更新，auto_update=%s，设置页存在=%s",
                cfg.get(cfg.auto_update),
                bool(setting_interface),
            )
            if setting_interface:
                setting_interface.trigger_instant_update_prompt(
                    auto_accept=cfg.get(cfg.auto_update)
                )
            else:
                self._show_restart_prompt(auto_accept=cfg.get(cfg.auto_update))
            return
        if self._pending_auto_run:
            self._schedule_auto_run()
        self._pending_auto_run = False

    def _show_restart_prompt(self, auto_accept: bool) -> None:
        """非热更新完成后弹出重启确认，支持自动确认。"""
        dialog = MessageBoxBase(self)
        dialog.widget.setMinimumWidth(420)
        dialog.yesButton.setText(self.tr("Restart now"))
        dialog.cancelButton.setText(self.tr("Later"))

        title = BodyLabel(self.tr("Restart required to finish update"), dialog)
        title.setStyleSheet("font-weight: 600;")
        desc = BodyLabel(
            self.tr("Update package downloaded. Restart to apply changes."),
            dialog,
        )
        desc.setWordWrap(True)

        dialog.viewLayout.addWidget(title)
        dialog.viewLayout.addSpacing(6)
        dialog.viewLayout.addWidget(desc)

        if auto_accept:
            logger.info("自动更新场景：启动重启确认倒计时 10s")
            countdown_label = BodyLabel("", dialog)
            countdown_label.setWordWrap(True)
            dialog.viewLayout.addSpacing(4)
            dialog.viewLayout.addWidget(countdown_label)
            self._start_auto_confirm_countdown(
                dialog,
                countdown_label,
                10,
                dialog.yesButton,
                self.tr("Auto restarting in %1 s"),
            )

        result = dialog.exec()
        if result == QDialog.DialogCode.Accepted:
            self._start_external_updater()

    def _start_auto_confirm_countdown(
        self,
        dialog: MessageBoxBase,
        label: BodyLabel,
        seconds: int,
        yes_button,
        template: str,
    ) -> None:
        """自动确认倒计时，用于自动更新场景。"""

        base_yes_text = yes_button.text() if yes_button else ""
        logger.info("倒计时开始: %ss, 文案模板=%s", seconds, template)

        def tick(remaining: int):
            if not dialog.isVisible():
                logger.debug("倒计时终止：对话框已关闭")
                return
            label.setText(template.replace("%1", str(remaining)))
            if yes_button:
                yes_button.setText(
                    f"{base_yes_text} ({remaining}s)"
                    if remaining >= 0
                    else base_yes_text
                )
            if remaining <= 0:
                if yes_button:
                    yes_button.setText(base_yes_text)
                logger.info("倒计时结束，自动点击确认")
                dialog.accept()
                return
            QTimer.singleShot(1000, lambda: tick(remaining - 1))

        QTimer.singleShot(0, lambda: tick(seconds))

    def _start_external_updater(self) -> None:
        """调用外部更新器完成非热更新并退出主程序。"""
        if self._external_updater_started:
            return
        self._external_updater_started = True
        try:
            if sys.platform.startswith("win32"):
                self._rename_updater("MFWUpdater.exe", "MFWUpdater1.exe")
            elif sys.platform.startswith(("darwin", "linux")):
                self._rename_updater("MFWUpdater", "MFWUpdater1")
        except Exception as exc:
            self._external_updater_started = False
            logger.error("重命名更新程序失败: %s", exc)
            signalBus.info_bar_requested.emit("error", str(exc))
            return

        try:
            self._launch_updater_process()
        except Exception as exc:
            self._external_updater_started = False
            logger.error("启动更新程序失败: %s", exc)
            signalBus.info_bar_requested.emit("error", str(exc))
            return

        QApplication.quit()

    def _rename_updater(self, old_name: str, new_name: str) -> None:
        """重命名更新器以避免占用。"""
        import os

        if os.path.exists(old_name) and os.path.exists(new_name):
            os.remove(new_name)
        if os.path.exists(old_name):
            os.rename(old_name, new_name)

    def _launch_updater_process(self) -> None:
        """启动外部更新器进程。"""
        import subprocess

        if sys.platform.startswith("win32"):
            from subprocess import CREATE_NEW_PROCESS_GROUP, DETACHED_PROCESS

            subprocess.Popen(
                ["./MFWUpdater1.exe", "-update"],
                creationflags=CREATE_NEW_PROCESS_GROUP | DETACHED_PROCESS,
            )
        elif sys.platform.startswith(("darwin", "linux")):
            subprocess.Popen(["./MFWUpdater1", "-update"], start_new_session=True)
        else:
            raise NotImplementedError("Unsupported platform")

    def _apply_auto_minimize_on_startup(self) -> None:
        """在启动完成后根据配置自动最小化窗口。"""
        if not cfg.get(cfg.auto_minimize_on_startup):
            return
        QTimer.singleShot(0, self.showMinimized)

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

    def show_info_bar(self, level: str, message: str, position: int | None = None):
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

        if position is None:
            position = InfoBarPosition.TOP_RIGHT.value

        show_method(
            title=level_title,
            content=message,
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition(position),
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
        self._update_background_geometry()

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
        
        # Shutdown hotkey manager first to unhook keyboard listeners
        if getattr(self, "_hotkey_manager", None):
            self._hotkey_manager.shutdown()
        
        # Terminate and wait for theme listener thread to finish
        try:
            if self.themeListener.isRunning():
                self.themeListener.terminate()
                # Wait for the thread to finish with a timeout
                if not self.themeListener.wait(self._THEME_LISTENER_TIMEOUT_MS):
                    logger.warning("主题监听器线程未在超时时间内终止")
            self.themeListener.deleteLater()
        except Exception as ex:
            logger.warning(f"终止主题监听器时出错: {ex}")
        
        e.accept()
        QTimer.singleShot(0, self.clear_thread_async)
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

    def clear_thread_async(self):
        """异步清理线程和资源"""
        send_thread = getattr(
            self.service_coordinator.task_runner, "send_thread", None
        )
        try:

            self._clear_maafw_sync()
            self._stop_notice_thread(send_thread)
            self._stop_update_workers()
            self._terminate_child_processes()
        except Exception as e:
            logger.exception("异步清理失败", exc_info=e)

    def _clear_maafw_sync(self):
        """同步清理 maafw（回退逻辑）"""
        maafw = self.service_coordinator.task_runner.maafw
        try:
            if maafw.tasker and maafw.tasker.running:
                logger.debug("停止任务线程")
                maafw.tasker.post_stop().wait()
                logger.debug("停止任务线程完成")
            maafw.tasker = None
            if maafw.resource:
                maafw.resource.clear()
            maafw.resource = None
            maafw.controller = None
            if maafw.agent:
                maafw.agent.disconnect()
            maafw.agent = None
            agent_proc = getattr(maafw, "agent_thread", None)
            if agent_proc:
                try:
                    agent_proc.terminate()
                    try:
                        agent_proc.wait(timeout=5)
                    except Exception:
                        agent_proc.kill()
                    logger.debug("终止 maafw agent 子进程")
                except Exception as agent_err:
                    logger.warning("终止 maafw agent 失败: %s", agent_err)
                finally:
                    maafw.agent_thread = None
        except Exception as e:
            logger.exception("清理 maafw 失败", exc_info=e)

    def _stop_notice_thread(self, send_thread):
        """关闭通知线程，确保队列循环退出。"""
        if not send_thread:
            return
        try:
            stop_fn = getattr(send_thread, "stop", None)
            if callable(stop_fn):
                stop_fn()
            else:
                send_thread.quit()
                if not send_thread.wait(5000):
                    send_thread.terminate()
            logger.debug("关闭发送线程")
        except Exception as e:
            logger.exception("关闭发送线程失败", exc_info=e)

    def _stop_update_workers(self):
        """停止更新相关线程/进程，避免退出时残留。"""
        setting_interface = getattr(self, "settingInterface", None)
        if not setting_interface:
            return

        updater = getattr(setting_interface, "_updater", None)
        if updater and updater.isRunning():
            try:
                if hasattr(updater, "stop"):
                    updater.stop()
                if not updater.wait(5000):
                    updater.terminate()
                logger.debug("关闭资源更新线程")
            except Exception as e:
                logger.exception("关闭资源更新线程失败", exc_info=e)

        checker = getattr(setting_interface, "_update_checker", None)
        if checker and checker.isRunning():
            try:
                checker.requestInterruption()
                checker.quit()
                if not checker.wait(3000):
                    checker.terminate()
                logger.debug("关闭更新检查线程")
            except Exception as e:
                logger.exception("关闭更新检查线程失败", exc_info=e)

        legacy_updater = getattr(setting_interface, "Updatethread", None)
        if legacy_updater:
            try:
                legacy_updater.quit()
                if hasattr(legacy_updater, "wait") and not legacy_updater.wait(5000):
                    legacy_updater.terminate()
                logger.debug("关闭更新线程")
            except Exception as e:
                logger.exception("关闭更新线程失败", exc_info=e)

        legacy_self = getattr(setting_interface, "update_self", None)
        if legacy_self:
            try:
                quit_fn = getattr(legacy_self, "quit", None)
                if callable(quit_fn):
                    quit_fn()
                term_fn = getattr(legacy_self, "terminate", None)
                wait_fn = getattr(legacy_self, "wait", None)
                if callable(wait_fn) and not wait_fn(5000) and callable(term_fn):
                    term_fn()
                elif callable(term_fn) and not callable(wait_fn):
                    term_fn()
                logger.debug("关闭更新自身进程")
            except Exception as e:
                logger.exception("关闭更新自身进程失败", exc_info=e)

    def _terminate_child_processes(self):
        """终止所有子进程，防止主程序退出后残留。"""
        try:
            import os
            import psutil

            current = psutil.Process(os.getpid())
            children = current.children(recursive=True)
            if not children:
                return
            logger.debug("检测到 %d 个子进程，正在关闭", len(children))
            for proc in children:
                try:
                    proc.terminate()
                except Exception:
                    logger.debug("发送终止信号失败: pid=%s", proc.pid)
            gone, alive = psutil.wait_procs(children, timeout=3)
            for proc in alive:
                try:
                    proc.kill()
                except Exception:
                    logger.debug("强制结束子进程失败: pid=%s", proc.pid)
        except ImportError:
            logger.debug("未安装 psutil，跳过子进程强制终止")
        except Exception as e:
            logger.exception("终止子进程时出错", exc_info=e)
