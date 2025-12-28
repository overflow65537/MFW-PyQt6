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
)
from qfluentwidgets import FluentIcon as FIF


from app.view.task_interface.task_interface_logic import TaskInterface
from app.view.special_task_interface.special_task_interface import (
    SpecialTaskInterface,
)
from app.view.monitor_interface import MonitorInterface
from app.view.schedule_interface.schedule_interface import ScheduleInterface
from app.view.setting_interface.setting_interface import (
    SettingInterface,
)
from app.view.test_interface.test_interface import TestInterface
from app.view.bundle_interface.bundle_interface import BundleInterface
from app.common.config import cfg
from app.common.signal_bus import signalBus
from app.utils.hotkey_manager import GlobalHotkeyManager
from app.utils.logger import logger
from app.core.core import ServiceCoordinator
from app.widget.notice_message import NoticeMessageBox, DelayedCloseNoticeMessageBox


class CustomSystemThemeListener(SystemThemeListener):
    def run(self):
        try:
            super().run()
        except NotImplementedError:
            logger.error("当前环境不支持主题监听，已忽略")


ENABLE_TEST_INTERFACE_PAGE = cfg.get(cfg.enable_test_interface_page)


class MainWindow(MSFluentWindow):

    _LOCKED_LOG_NAMES = {"maa.log", "clash.log", "maa.log.bak"}
    _THEME_LISTENER_TIMEOUT_MS = (
        2000  # 2 seconds timeout for theme listener thread termination
    )

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
        self._auto_run_scheduled = False  # 标记是否已调度过启动后自动运行，避免重复触发
        self._bundle_interface_added_to_nav = False  # 标记 BundleInterface 是否已添加到导航栏
        self._setting_update_completed = False  # 设置更新是否完成
        self._bundle_update_in_progress = False  # bundle 更新是否正在进行

        cfg.set(cfg.save_screenshot, False)
        cfg.set(cfg.show_advanced_startup_options, False)

        # 使用自定义的主题监听器
        self.themeListener = CustomSystemThemeListener(self)

        # 初始化配置管理器
        multi_config_path = Path.cwd() / "config" / "multi_config.json"
        self.service_coordinator = ServiceCoordinator(multi_config_path)
        self._apply_cli_switch_config()

        self._announcement_pending_show = False
        self._announcement_enabled = True  # 标记公告是否启用
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
        """self.SpecialTaskInterface = SpecialTaskInterface(self.service_coordinator)
        self.addSubInterface(
            self.SpecialTaskInterface,
            FIF.TILES,
            self.tr("Special Task"),
        )"""
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
        # 总是初始化 BundleInterface，但不添加到导航栏（除非多资源适配已开启）
        try:
            logger.info("初始化 BundleInterface...")
            self.BundleInterface = BundleInterface(self.service_coordinator)
            logger.info("BundleInterface 创建成功")
        except Exception as exc:
            logger.error(f"创建 BundleInterface 失败: {exc}", exc_info=True)
            self.BundleInterface = None
        
        self.SettingInterface = SettingInterface(self.service_coordinator)
        
        # 根据多资源适配状态控制 Bundle 和 Announcement 的显示
        # 如果多资源适配已开启：显示 Bundle，不显示 Announcement
        # 如果多资源适配未开启：显示 Announcement，不显示 Bundle
        multi_res_enabled = cfg.get(cfg.multi_resource_adaptation)
        logger.info(f"检查多资源适配状态（启动时）: {multi_res_enabled}")
        if multi_res_enabled:
            logger.info("多资源适配已开启，添加 BundleInterface 到导航栏，隐藏 Announcement")
            # 添加 Bundle，确保它在 Setting 之前
            if hasattr(self, "BundleInterface") and self.BundleInterface is not None:
                self.addSubInterface(
                    self.BundleInterface,
                    FIF.FOLDER,
                    self.tr("Bundle"),
                    position=NavigationItemPosition.BOTTOM,
                )
                self._bundle_interface_added_to_nav = True
                logger.info("✓ BundleInterface 已添加到导航栏")
        else:
            logger.info("多资源适配未开启，显示 Announcement，BundleInterface 不会显示在导航栏")
        
        # 添加 SettingInterface
        self.addSubInterface(
            self.SettingInterface,
            FIF.SETTING,
            self.tr("Setting"),
            position=NavigationItemPosition.BOTTOM,
        )
        
        # 根据多资源适配状态决定是否插入 Announcement
        if not multi_res_enabled:
            # 多资源适配未开启时，插入 Announcement（使用 insertItem(0) 确保它在最前面）
            self._insert_announcement_nav_item()
            logger.info("✓ Announcement 已添加到导航栏")
        else:
            logger.info("多资源适配已开启，Announcement 不会显示在导航栏")
        
        # 添加导航项
        self.splashScreen.finish()
        self._maybe_show_pending_announcement()
        QTimer.singleShot(0, self.service_coordinator.schedule_service.start)

        # 启动主题监听器
        self.themeListener.start()

        # 连接公共信号
        self.connectSignalToSlot()
        
        # 检查是否有待显示的错误信息（配置加载错误等）
        pending_error = self.service_coordinator.get_pending_error_message()
        if pending_error:
            level, message = pending_error
            # 处理国际化：将英文消息转换为可翻译的格式
            translated_message = self._translate_config_error(message)
            signalBus.info_bar_requested.emit(level, translated_message)
        try:
            event_loop = self._loop or asyncio.get_event_loop()
        except RuntimeError:
            event_loop = None
        self._hotkey_manager = GlobalHotkeyManager(event_loop)
        self._hotkey_manager.setup(
            start_factory=lambda: self.service_coordinator.run_tasks_flow(),
            stop_factory=lambda: self.service_coordinator.stop_task_flow(),
        )
        signalBus.hotkey_shortcuts_changed.connect(self._reload_global_hotkeys)
        
        # 检测快捷键权限（macOS/Linux）
        self._check_hotkey_permission()
        self._reload_global_hotkeys()
        self._bootstrap_auto_update_and_run()
        self._apply_auto_minimize_on_startup()

        # 程序启动并完成主界面初始化后，如果已开启多资源适配，则执行一次后续操作钩子
        try:
            if cfg.get(cfg.multi_resource_adaptation):
                self.SettingInterface.run_multi_resource_post_enable_tasks()
        except Exception as exc:
            logger.warning(f"运行多资源适配启动钩子失败: {exc}")

        logger.info(" 主界面初始化完成。")

    def _add_bundle_interface_to_navigation(self) -> None:
        """将 BundleInterface 添加到导航栏，并隐藏 Announcement。

        如果已经添加过，则不会重复添加。
        当用户动态启用多资源适配时，会调用此方法添加 Bundle。
        注意：在初始化时，如果多资源适配已开启，Bundle 会在 Setting 之前自动添加。
        """
        try:
            logger.info("_add_bundle_interface_to_navigation 被调用")
            
            if not hasattr(self, "BundleInterface") or self.BundleInterface is None:
                logger.warning("BundleInterface 未初始化，无法添加到导航栏")
                return

            # 检查是否已经添加到导航栏
            if self._bundle_interface_added_to_nav:
                logger.info("BundleInterface 已存在于导航栏，跳过重复添加")
                return

            logger.info("开始添加 BundleInterface 到导航栏（动态启用多资源适配）...")
            logger.info(f"BundleInterface 对象: {self.BundleInterface}")
            
            # 隐藏 Announcement（如果存在）并禁用其功能
            try:
                # 禁用公告功能
                self._announcement_enabled = False
                logger.info("✓ Announcement 功能已禁用")
                
                # 尝试通过查找导航项并隐藏它
                # 由于 qfluentwidgets 的 NavigationBar 可能没有直接的隐藏方法，
                # 我们通过查找对应的导航项并设置其可见性
                nav_items = getattr(self.navigationInterface, "items", [])
                for item in nav_items:
                    if hasattr(item, "routeKey") and item.routeKey == "announcement_button":
                        if hasattr(item, "setVisible"):
                            item.setVisible(False)
                            logger.info("✓ Announcement 已隐藏")
                            break
                        elif hasattr(item, "hide"):
                            item.hide()
                            logger.info("✓ Announcement 已隐藏")
                            break
            except Exception as hide_exc:
                logger.debug(f"隐藏 Announcement 时出错（可能不存在或已隐藏）: {hide_exc}")
            
            # 首先确保 BundleInterface 被添加到 stackedWidget
            if self.stackedWidget.indexOf(self.BundleInterface) == -1:
                self.stackedWidget.addWidget(self.BundleInterface)
                logger.info("BundleInterface 已添加到 stackedWidget")
            
            # 添加 Bundle 到导航栏（在 Setting 之前）
            # 注意：由于多资源适配开启时公告不会显示，所以直接添加 Bundle 即可
            try:
                # 尝试在索引 0 位置插入 Bundle（原本公告的位置）
                self.navigationInterface.insertItem(
                    0,
                    "bundle_interface",
                    FIF.FOLDER,
                    self.tr("Bundle"),
                    onClick=lambda: self.stackedWidget.setCurrentWidget(self.BundleInterface),
                    selectable=True,
                    position=NavigationItemPosition.BOTTOM,
                )
                logger.info("使用 insertItem 在索引 0 位置插入 Bundle")
            except Exception as insert_exc:
                # 如果 insertItem 失败，使用 addSubInterface
                logger.warning(f"insertItem 失败，使用 addSubInterface: {insert_exc}")
                self.addSubInterface(
                    self.BundleInterface,
                    FIF.FOLDER,
                    self.tr("Bundle"),
                    position=NavigationItemPosition.BOTTOM,
                )
            
            self._bundle_interface_added_to_nav = True
            logger.info("✓ BundleInterface 已成功添加到导航栏！")
        except Exception as exc:
            logger.error(f"添加 BundleInterface 到导航栏失败: {exc}", exc_info=True)
            import traceback
            logger.error(f"详细错误信息: {traceback.format_exc()}")

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

    def _translate_config_error(self, message: str) -> str:
        """翻译配置错误消息
        
        Args:
            message: 英文错误消息
            
        Returns:
            str: 翻译后的消息
        """
        if "Config load failed, automatically reset to default" in message:
            if "Backup of corrupted config file completed" in message:
                # 提取错误详情
                if "Error details:" in message:
                    error_detail = message.split("Error details:")[-1].strip()
                    base_msg = self.tr("Config load failed, automatically reset to default. Backup of corrupted config file completed. Error details:")
                    return f"{base_msg} {error_detail}"
                return self.tr("Config load failed, automatically reset to default. Backup of corrupted config file completed.")
            elif "Failed to backup corrupted config file" in message:
                # 提取错误详情
                if "Error details:" in message:
                    error_detail = message.split("Error details:")[-1].strip()
                    base_msg = self.tr("Config load failed, automatically reset to default. Failed to backup corrupted config file. Error details:")
                    return f"{base_msg} {error_detail}"
                return self.tr("Config load failed, automatically reset to default. Failed to backup corrupted config file.")
        elif "Config load failed and error occurred while resetting config" in message:
            error_detail = message.split(":")[-1].strip() if ":" in message else ""
            if error_detail:
                base_msg = self.tr("Config load failed and error occurred while resetting config:")
                return f"{base_msg} {error_detail}"
            return self.tr("Config load failed and error occurred while resetting config.")
        return message
    
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
        signalBus.check_auto_run_after_update_cancel.connect(
            self._on_check_auto_run_after_update_cancel
        )
        signalBus.all_updates_completed.connect(self._on_all_updates_completed)
        # 多资源适配启用后，将 BundleInterface 添加到导航栏
        signalBus.multi_resource_adaptation_enabled.connect(
            self._on_multi_resource_adaptation_enabled
        )

    def _on_multi_resource_adaptation_enabled(self) -> None:
        """响应设置页开启多资源适配的信号，将 BundleInterface 添加到导航栏。"""
        self._add_bundle_interface_to_navigation()

    def _apply_cli_switch_config(self) -> None:
        """处理 CLI 请求的配置切换，在 UI 初始化前执行。"""
        if not self._cli_switch_config_id:
            return
        target = self._cli_switch_config_id
        if self.service_coordinator.select_config(target):
            logger.info("CLI 指定配置已切换: %s", target)
        else:
            logger.warning("CLI 指定配置不存在，保持原配置: %s", target)

    def _check_hotkey_permission(self):
        """检测全局快捷键权限，如果不可用则禁用设置。"""
        if not getattr(self, "_hotkey_manager", None):
            return
        
        # 检测权限
        has_permission = self._hotkey_manager.check_permission()
        
        # 仅在 macOS/Linux 平台且权限不足时禁用设置
        if sys.platform in ("darwin", "linux") and not has_permission:
            logger.warning("全局快捷键权限不足，已禁用快捷键设置")
            
            # 禁用快捷键设置界面
            self._disable_hotkey_settings()
    
    def _disable_hotkey_settings(self):
        """禁用快捷键设置界面。"""
        try:
            setting_interface = getattr(self, "SettingInterface", None)
            if setting_interface and hasattr(setting_interface, "start_shortcut_card"):
                # 禁用开始任务快捷键设置
                if hasattr(setting_interface, "start_shortcut_card"):
                    setting_interface.start_shortcut_card.setEnabled(False)
                    setting_interface.start_shortcut_card.lineEdit.setPlaceholderText(
                        self.tr("hotkey disabled due to permission issue")
                    )
                # 禁用停止任务快捷键设置
                if hasattr(setting_interface, "stop_shortcut_card"):
                    setting_interface.stop_shortcut_card.setEnabled(False)
                    setting_interface.stop_shortcut_card.lineEdit.setPlaceholderText(
                        self.tr("hotkey disabled due to permission issue")
                    )
                logger.info("已禁用快捷键设置界面")
        except Exception as exc:
            logger.warning("禁用快捷键设置界面失败: %s", exc)

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
        # 保存待更新的公告内容，只有在用户关闭对话框时才会更新配置
        self._pending_announcement_content = res_announcement
        if cfg_announcement != res_announcement:
            # 公告内容不一致，在界面准备好后弹出对话框
            # 注意：此时不更新配置，只有在用户关闭对话框时才更新
            self._announcement_pending_show = True

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
            QTimer.singleShot(0, lambda: self._on_announcement_button_clicked(auto_show=True))

    def _bootstrap_auto_update_and_run(self) -> None:
        """启动自动更新并串行等待，更新后再执行自动任务。"""
        self._pending_auto_run = bool(
            self._cli_auto_run or cfg.get(cfg.run_after_startup)
        )
        if cfg.get(cfg.auto_update):
            logger.info("自动更新已开启，准备启动自动更新线程")
            self._start_auto_update_thread()
            return
        # 未开启 UI 自动更新时，直接进入下一步：检查是否需要执行 bundle 自动更新
        logger.info("自动更新未开启，改为检查并执行 bundle 自动更新")
        self._check_and_start_bundle_update()

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
            logger.warning("自动更新未启动：更新器未就绪，改为检查并执行 bundle 自动更新")
            # UI 自动更新无法启动时，直接进入 bundle 自动更新阶段
            self._check_and_start_bundle_update()
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
        # UI 自动更新未成功启动，继续检查 bundle 自动更新
        logger.info("自动更新未成功启动，改为检查并执行 bundle 自动更新")
        self._check_and_start_bundle_update()

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

    def _on_check_auto_run_after_update_cancel(self) -> None:
        """当更新被取消后，按统一流水线继续后续任务（bundle 更新 → 自动运行）。"""
        logger.info(
            "收到更新取消信号，auto_update_in_progress=%s, bundle_update_in_progress=%s, pending_auto_run=%s",
            self._auto_update_in_progress,
            self._bundle_update_in_progress,
            self._pending_auto_run,
        )
        # 如果配置/CLI 不需要启动后自动运行，则仅保证更新状态收尾即可
        should_run = self._cli_auto_run or cfg.get(cfg.run_after_startup)
        if not should_run:
            logger.info("未开启启动后自动运行，取消更新后不再调度后续任务")
            return

        # 标记后续需要自动运行，让统一更新流水线在合适时机调度
        self._pending_auto_run = True

        # 如果当前没有任何 UI/bundle 更新在进行，则可以直接调度自动运行
        if not self._auto_update_in_progress and not self._bundle_update_in_progress:
            logger.info("当前无进行中的更新任务，取消后直接调度自动运行")
            self._schedule_auto_run()
            self._pending_auto_run = False

    def _on_update_stopped_main(self, status: int):
        """监听更新结束，串行触发自动运行或提示重启。"""
        logger.info(
            "收到更新结束信号，status=%s，pending_auto_run=%s，setting_update_completed=%s，bundle_update_in_progress=%s",
            status,
            self._pending_auto_run,
            self._setting_update_completed,
            self._bundle_update_in_progress,
        )
        
        # 判断是设置更新还是 bundle 更新
        if self._auto_update_in_progress and not self._bundle_update_in_progress:
            # 这是设置更新完成
            logger.info("设置更新完成，status=%s", status)
            self._setting_update_completed = True
            self._auto_update_in_progress = False
            self._auto_update_thread = None
            
            if status == 1:
                # 热更新完成后，重新设置窗口标题（延迟到下一个事件循环，确保 reinit 完成）
                QTimer.singleShot(0, self.set_title)
                # 检查是否需要启动 bundle 更新
                self._check_and_start_bundle_update()
                return
            elif status == 2:
                # 需要重启完成更新，触发立即更新提示
                self._auto_update_pending_restart = True
                self._pending_auto_run = False
                setting_interface = getattr(self, "SettingInterface", None)
                logger.info(
                    "设置更新需要重启完成更新，auto_update=%s，设置页存在=%s",
                    cfg.get(cfg.auto_update),
                    bool(setting_interface),
                )
                if setting_interface:
                    setting_interface.trigger_instant_update_prompt(
                        auto_accept=cfg.get(cfg.auto_update)
                    )
                else:
                    logger.warning("SettingInterface 不存在，无法触发立即更新提示")
                return
            
            # 其他 status，检查是否需要启动 bundle 更新
            self._check_and_start_bundle_update()
            return
        
        if self._bundle_update_in_progress:
            # 这是 bundle 更新完成（单个bundle）
            logger.info("Bundle 更新完成（单个），status=%s", status)
            # 注意：所有bundle更新完成信号由 bundle_interface 的 _start_next_update 发送
            # 这里不需要发送 all_updates_completed 信号
            return
        
        # 其他情况（可能是手动触发的更新）
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
                logger.warning("SettingInterface 不存在，无法触发立即更新提示")
            return
        if self._pending_auto_run:
            self._schedule_auto_run()
        self._pending_auto_run = False
    
    def _check_and_start_bundle_update(self):
        """检查并启动 bundle 更新"""
        # 检查 bundle 自动更新是否开启
        bundle_auto_update_enabled = cfg.get(cfg.bundle_auto_update)
        
        if not bundle_auto_update_enabled:
            logger.info("Bundle 自动更新未开启，直接发送所有更新完成信号")
            signalBus.all_updates_completed.emit()
            # 处理自动运行
            if self._pending_auto_run:
                self._schedule_auto_run()
            self._pending_auto_run = False
            return
        
        # 检查是否有 bundle 需要更新
        bundle_interface = getattr(self, "BundleInterface", None)
        if not bundle_interface:
            logger.warning("BundleInterface 不存在，无法启动 bundle 更新")
            signalBus.all_updates_completed.emit()
            if self._pending_auto_run:
                self._schedule_auto_run()
            self._pending_auto_run = False
            return
        
        # 启动 bundle 自动更新
        logger.info("Bundle 自动更新已开启，开始更新所有 bundle")
        self._bundle_update_in_progress = True
        try:
            bundle_interface.start_auto_update_all()
        except Exception as e:
            logger.error(f"启动 bundle 自动更新失败: {e}", exc_info=True)
            self._bundle_update_in_progress = False
            signalBus.all_updates_completed.emit()
            if self._pending_auto_run:
                self._schedule_auto_run()
            self._pending_auto_run = False
    
    def _on_all_updates_completed(self):
        """所有更新完成回调"""
        logger.info("收到所有更新完成信号")
        # 所有更新（UI + bundle）完成后，如果还有待执行的自动运行，则在此统一调度
        if self._pending_auto_run:
            logger.info("所有更新已完成，开始执行启动后自动运行任务")
            self._schedule_auto_run()
            self._pending_auto_run = False

    def _apply_auto_minimize_on_startup(self) -> None:
        """在启动完成后根据配置自动最小化窗口。"""
        if not cfg.get(cfg.auto_minimize_on_startup):
            return
        QTimer.singleShot(0, self.showMinimized)

    def _on_announcement_button_clicked(self, auto_show: bool = False):
        """处理公告按钮点击，弹出公告对话框或提示无内容。
        
        Args:
            auto_show: 如果为 True，表示是通过方法自动唤醒的（第一次打开或公告更新），
                      将使用带延迟关闭功能的对话框；如果为 False，表示用户手动点击，
                      使用普通对话框。
        """
        # 如果公告功能被禁用，直接返回
        if not getattr(self, "_announcement_enabled", True):
            return
        
        if not self._announcement_content:
            self.show_info_bar("info", self._announcement_empty_hint)
            return

        # 检查当前记录的公告和当前运行的公告是否一致
        cfg_announcement = cfg.get(cfg.announcement)
        res_announcement = getattr(self, "_pending_announcement_content", "")
        if not res_announcement:
            res_announcement = self.service_coordinator.task.interface.get("welcome", "")
        
        # 只有当公告内容不一致时，才需要5秒延迟
        announcement_mismatch = cfg_announcement != res_announcement
        
        # 根据公告内容是否一致决定使用哪个对话框类
        if announcement_mismatch:
            # 公告内容不一致，使用带延迟关闭功能的对话框
            dialog = DelayedCloseNoticeMessageBox(
                parent=self,
                title=self._announcement_title,
                content=self._announcement_content,
                enable_delay=True,
            )
        else:
            # 公告内容一致，使用普通对话框（无延迟）
            dialog = NoticeMessageBox(
                parent=self,
                title=self._announcement_title,
                content=self._announcement_content,
            )
        
        dialog.button_yes.hide()
        dialog.button_cancel.setText(self.tr("Close"))
        result = dialog.exec()
        
        # 只有在公告内容不一致且用户关闭对话框时，才更新配置
        # 这样如果用户不关闭对话框，下次启动时还会弹出
        if announcement_mismatch and hasattr(self, "_pending_announcement_content"):
            # 用户关闭了对话框，更新配置，下次不会再弹出
            cfg.set(cfg.announcement, self._pending_announcement_content)
            logger.info("用户关闭公告对话框，已更新公告配置")

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
        meta = self.service_coordinator.task.interface or {}
        base_title = (
            meta.get("title", "")
            or meta.get("custom_title", "")
            or f"{meta.get('name', '')} {meta.get('version', '')}".strip()
        )

        if cfg.get(cfg.multi_resource_adaptation):
            from app.common.__version__ import __version__

            # 多资源模式下：显示应用名 + 应用版本 + 资源标题
            prefix = f"{self.tr('MFW-ChainFlow Assistant')} {__version__}"
            title = f"{prefix} {base_title}".strip()
            self.setWindowIcon(QIcon("./app/assets/icons/logo.png"))
        else:
            title = base_title

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

        self.themeListener.terminate()
        self.themeListener.deleteLater()

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
        send_thread = getattr(self.service_coordinator.task_runner, "send_thread", None)
        try:

            self._clear_maafw_sync()
            self._stop_notice_thread(send_thread)
            self._stop_update_workers()
            # self._terminate_child_processes()
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

            # 不要误杀正在执行更新的外部更新器
            UPDATER_NAMES = {
                "MFWUpdater.exe",
                "MFWUpdater1.exe",
                "MFWUpdater",
                "MFWUpdater1",
            }

            current = psutil.Process(os.getpid())
            children = current.children(recursive=True)
            if not children:
                return
            logger.debug("检测到 %d 个子进程，正在关闭", len(children))
            for proc in children:
                try:
                    name = (proc.name() or "").lower()
                    cmdline = " ".join(proc.cmdline()).lower()
                    if any(up.lower() in name for up in UPDATER_NAMES) or any(
                        up.lower() in cmdline for up in UPDATER_NAMES
                    ):
                        logger.debug(
                            "检测到更新器进程，跳过终止: pid=%s, name=%s",
                            proc.pid,
                            proc.name(),
                        )
                        continue
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
