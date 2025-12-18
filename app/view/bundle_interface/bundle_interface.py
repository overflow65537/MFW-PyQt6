"""
MFW-ChainFlow Assistant
Bundle 管理界面
作者:overflow65537
"""

import jsonc
import time
from pathlib import Path
from typing import Dict, Any, Optional

from PySide6.QtCore import Qt, Signal, QMetaObject, QCoreApplication
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QListWidgetItem,
    QLabel,
    QSizePolicy,
)

from qfluentwidgets import (
    ScrollArea,
    ListWidget,
    BodyLabel,
    CardWidget,
    TitleLabel,
    SimpleCardWidget,
    ToolButton,
    ToolTipFilter,
    ToolTipPosition,
    FluentIcon as FIF,
    TogglePushButton,
)

from app.core.core import ServiceCoordinator
from app.core.service.interface_manager import get_interface_manager
from app.utils.logger import logger
from app.utils.update import Update, MultiResourceUpdate
from app.common.signal_bus import signalBus
from app.utils.markdown_helper import render_markdown


class BundleListItem(QWidget):
    """Bundle 列表项组件"""

    def __init__(
        self,
        bundle_name: str,
        bundle_version: str,
        icon_path: Optional[str],
        parent=None,
    ):
        super().__init__(parent)
        self.bundle_name = bundle_name
        self.bundle_version = bundle_version
        self.latest_version: Optional[str] = None

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(12)

        # 图标
        self.icon_label = QLabel(self)
        self.icon_label.setFixedSize(32, 32)
        self.icon_label.setScaledContents(True)
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        if icon_path:
            icon_file = Path(icon_path)
            if icon_file.exists():
                pixmap = QPixmap(str(icon_file))
                if not pixmap.isNull():
                    self.icon_label.setPixmap(
                        pixmap.scaled(
                            32,
                            32,
                            Qt.AspectRatioMode.KeepAspectRatio,
                            Qt.TransformationMode.SmoothTransformation,
                        )
                    )

        # 名称和版本
        text_layout = QVBoxLayout()
        text_layout.setSpacing(4)
        text_layout.setContentsMargins(0, 0, 0, 0)

        self.name_label = QLabel(bundle_name, self)
        self.name_label.setStyleSheet("font-weight: bold; font-size: 14px;")

        # 当前版本
        self.version_label = QLabel(bundle_version, self)
        self.version_label.setStyleSheet("font-size: 12px; color: gray;")
        self.version_label.setWordWrap(True)

        # 最新版本
        self.latest_version_label = QLabel("", self)
        self.latest_version_label.setStyleSheet("font-size: 12px; color: #0078d4;")
        self.latest_version_label.setWordWrap(True)
        self.latest_version_label.hide()  # 初始状态隐藏

        text_layout.addWidget(self.name_label)
        text_layout.addWidget(self.version_label)
        text_layout.addWidget(self.latest_version_label)

        layout.addWidget(self.icon_label)
        layout.addLayout(text_layout)
        layout.addStretch()

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
    
    def update_latest_version(self, latest_version: Optional[str]):
        """更新最新版本信息"""
        self.latest_version = latest_version
        if latest_version and latest_version != self.bundle_version:
            # 显示最新版本（蓝色表示有更新）
            self.latest_version_label.setText(f"最新版本: {latest_version}")
            self.latest_version_label.setStyleSheet("font-size: 12px; color: #0078d4;")
            self.latest_version_label.show()
        else:
            # 隐藏最新版本标签（已是最新或未检查到）
            self.latest_version_label.setText("")
            self.latest_version_label.hide()


class BundleDetailWidget(QWidget):
    """Bundle 详情显示组件（右侧滚动区域内容）"""

    def __init__(
        self,
        bundle_name: str,
        bundle_data: Dict[str, Any],
        interface_data: Dict[str, Any],
        parent=None,
    ):
        super().__init__(parent)
        self.bundle_name = bundle_name
        self.bundle_data = bundle_data
        self.interface_data = interface_data

        # 设置透明背景和边框
        self.setStyleSheet("background: transparent; border: none;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # 区域1：描述
        self._add_description_section(layout)

        # 区域2：联系方式
        self._add_contact_section(layout)

        layout.addStretch()

    def _add_description_section(self, parent_layout: QVBoxLayout):
        """添加描述区域"""
        _translate = QCoreApplication.translate
        section_layout = QVBoxLayout()
        section_layout.setSpacing(8)
        section_layout.setContentsMargins(0, 0, 0, 0)

        title = TitleLabel(_translate("BundleInterface", "描述"), self)
        section_layout.addWidget(title)

        description_text = (
            self.interface_data.get("description", "")
            or self.interface_data.get("welcome", "")
            or _translate("BundleInterface", "暂无描述")
        )
        description_label = BodyLabel(self)
        description_label.setWordWrap(True)
        # 支持 Markdown 格式
        description_label.setTextFormat(Qt.TextFormat.RichText)
        description_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.LinksAccessibleByMouse
        )
        description_label.setOpenExternalLinks(True)
        html_content = render_markdown(description_text)
        description_label.setText(html_content)
        section_layout.addWidget(description_label)

        parent_layout.addLayout(section_layout)

    def _add_contact_section(self, parent_layout: QVBoxLayout):
        """添加联系方式区域"""
        _translate = QCoreApplication.translate
        section_layout = QVBoxLayout()
        section_layout.setSpacing(8)
        section_layout.setContentsMargins(0, 0, 0, 0)

        title = TitleLabel(_translate("BundleInterface", "联系方式"), self)
        section_layout.addWidget(title)

        contact_text = self.interface_data.get("contact", "") or _translate(
            "BundleInterface", "暂无联系方式"
        )
        contact_label = BodyLabel(self)
        contact_label.setWordWrap(True)
        # 支持 Markdown 格式
        contact_label.setTextFormat(Qt.TextFormat.RichText)
        contact_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.LinksAccessibleByMouse
        )
        contact_label.setOpenExternalLinks(True)
        html_content = render_markdown(contact_text)
        contact_label.setText(html_content)
        section_layout.addWidget(contact_label)

        parent_layout.addLayout(section_layout)



class UI_BundleInterface(object):
    """Bundle 管理界面 UI 类"""

    def __init__(self, service_coordinator: ServiceCoordinator, parent=None):
        self.service_coordinator = service_coordinator
        self.parent = parent

    def setupUi(self, BundleInterface):
        BundleInterface.setObjectName("BundleInterface")

        # 主布局（水平布局）
        main_layout = QHBoxLayout()

        # 左侧列表区域（30%）
        self._init_list_panel(BundleInterface)
        main_layout.addWidget(self.list_panel, 3)  # stretch=3 对应 30%

        # 右侧详情区域（70%）
        self._init_detail_panel(BundleInterface)
        main_layout.addWidget(self.detail_panel, 7)  # stretch=7 对应 70%

        # 将水平布局设置为 QWidget 的主布局
        BundleInterface.setLayout(main_layout)

        self.retranslateUi(BundleInterface)
        QMetaObject.connectSlotsByName(BundleInterface)

    def _init_list_panel(self, parent):
        """初始化左侧列表面板（带标题和卡片）"""
        _translate = QCoreApplication.translate

        # 列表面板容器
        self.list_panel = QWidget(parent)
        list_panel_layout = QVBoxLayout(self.list_panel)

        # 标题布局
        self.list_title_layout = QHBoxLayout()
        self.list_title_layout.setContentsMargins(0, 0, 2, 0)

        # 标题
        self.list_title = BodyLabel()
        self.list_title.setStyleSheet("font-size: 20px;")
        self.list_title.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.list_title_layout.addWidget(self.list_title)

        # 自动更新开关按钮
        self.auto_update_switch = TogglePushButton(parent)
        self.auto_update_switch.setIcon(FIF.UPDATE)
        self.auto_update_switch.setText(_translate("BundleInterface", "Auto Update"))
        self.auto_update_switch.installEventFilter(
            ToolTipFilter(self.auto_update_switch, 0, ToolTipPosition.TOP)
        )
        self.auto_update_switch.setToolTip(_translate("BundleInterface", "Auto Update"))
        # 从配置读取自动更新状态
        from app.common.config import cfg

        auto_update_enabled = cfg.get(cfg.bundle_auto_update)  # type: ignore
        self.auto_update_switch.setChecked(auto_update_enabled)
        self.list_title_layout.addWidget(self.auto_update_switch)

        # 更新所有bundle按钮
        self.update_all_button = ToolButton(FIF.SYNC, parent)
        self.update_all_button.installEventFilter(
            ToolTipFilter(self.update_all_button, 0, ToolTipPosition.TOP)
        )
        self.update_all_button.setToolTip(
            _translate("BundleInterface", "Update All Bundles")
        )
        self.list_title_layout.addWidget(self.update_all_button)

        list_panel_layout.addLayout(self.list_title_layout)

        # 列表卡片
        self.list_card = SimpleCardWidget()
        self.list_card.setClickEnabled(False)
        self.list_card.setBorderRadius(8)
        list_card_layout = QVBoxLayout(self.list_card)

        # 列表组件
        self.list_widget = ListWidget(self.list_card)
        list_card_layout.addWidget(self.list_widget)

        list_panel_layout.addWidget(self.list_card)

    def _init_detail_panel(self, parent):
        """初始化右侧详情面板（带标题和卡片）"""
        _translate = QCoreApplication.translate

        # 详情面板容器
        self.detail_panel = QWidget(parent)
        detail_panel_layout = QVBoxLayout(self.detail_panel)

        # 标题布局
        self.detail_title_layout = QHBoxLayout()

        # 标题
        self.detail_title = BodyLabel()
        self.detail_title.setStyleSheet("font-size: 20px;")
        self.detail_title.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.detail_title_layout.addWidget(self.detail_title)

        detail_panel_layout.addLayout(self.detail_title_layout)

        # 详情卡片
        self.detail_card = SimpleCardWidget()
        self.detail_card.setClickEnabled(False)
        self.detail_card.setBorderRadius(8)
        detail_card_layout = QVBoxLayout(self.detail_card)

        # 滚动区域
        self.scroll_area = ScrollArea(self.detail_card)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        # 设置滚动区域透明背景和边框
        self.scroll_area.setStyleSheet("background: transparent; border: none;")

        self.detail_widget = QWidget()
        # 设置透明背景和边框
        self.detail_widget.setStyleSheet("background: transparent; border: none;")
        self.detail_layout = QVBoxLayout(self.detail_widget)

        # 默认提示
        self.default_label = BodyLabel(
            _translate("BundleInterface", "请从左侧选择一个 Bundle"), self.detail_widget
        )
        self.default_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.default_label.setStyleSheet("font-size: 16px; color: gray; padding: 40px;")
        self.detail_layout.addWidget(self.default_label)
        self.detail_layout.addStretch()

        self.scroll_area.setWidget(self.detail_widget)
        detail_card_layout.addWidget(self.scroll_area)

        detail_panel_layout.addWidget(self.detail_card)

    def retranslateUi(self, BundleInterface):
        _translate = QCoreApplication.translate
        BundleInterface.setWindowTitle(_translate("BundleInterface", "Form"))
        # 设置标题文本
        if hasattr(self, "list_title"):
            self.list_title.setText(_translate("BundleInterface", "Bundle 列表"))
        if hasattr(self, "detail_title"):
            self.detail_title.setText(_translate("BundleInterface", "Bundle 详情"))


class BundleInterface(UI_BundleInterface, QWidget):
    """Bundle 管理界面"""

    bundle_selected = Signal(str)  # 发送选中的 bundle 名称

    def __init__(self, service_coordinator: ServiceCoordinator, parent=None):
        QWidget.__init__(self, parent=parent)
        UI_BundleInterface.__init__(
            self, service_coordinator=service_coordinator, parent=parent
        )
        self.setupUi(self)
        self.service_coordinator = service_coordinator
        self._bundle_data: Dict[str, Dict[str, Any]] = {}
        self._latest_versions: Dict[str, Optional[str]] = {}  # bundle_name -> latest_version
        self._update_checkers: Dict[str, Update] = {}  # bundle_name -> Update checker
        self._current_updater: Optional[Update] = None  # 当前正在运行的更新器
        self._current_bundle_name: Optional[str] = None  # 当前正在更新的bundle名称
        self._update_queue: list[str] = []  # 更新队列
        self._is_updating_all = False

        # 设置标题
        self.list_title.setText(self.tr("Bundle 列表"))
        self.detail_title.setText(self.tr("Bundle 详情"))

        # 连接信号
        self.list_widget.currentItemChanged.connect(self._on_bundle_selected)
        self.update_all_button.clicked.connect(self._on_update_all_bundles)
        self.auto_update_switch.toggled.connect(self._on_auto_update_changed)
        
        # 监听更新停止信号（Update 类会自动发送，用于通知主界面）
        signalBus.update_stopped.connect(self._on_update_stopped)

        # 加载 bundle 列表
        self._load_bundles()
        
        # 启动时自动检查所有资源的更新
        self._check_all_updates()

    def _load_bundles(self, force_refresh: bool = False):
        """从 service_coordinator 加载所有 bundle
        
        Args:
            force_refresh: 是否强制刷新（更新后使用，直接读取文件而不使用缓存）
        """
        self.list_widget.clear()
        self._bundle_data.clear()

        try:
            bundle_names = self.service_coordinator.config.list_bundles()
            if not bundle_names:
                logger.warning("未找到任何 bundle")
                return

            for bundle_name in bundle_names:
                try:
                    bundle_info = self.service_coordinator.config.get_bundle(
                        bundle_name
                    )
                    bundle_path_str = bundle_info.get("path", "")
                    bundle_display_name = bundle_info.get("name", bundle_name)

                    if not bundle_path_str:
                        logger.warning(f"Bundle '{bundle_name}' 没有路径信息")
                        continue

                    # 解析路径
                    bundle_path = Path(bundle_path_str)
                    if not bundle_path.is_absolute():
                        bundle_path = Path.cwd() / bundle_path

                    # 读取 interface.json 或 interface.jsonc
                    interface_path = bundle_path / "interface.jsonc"
                    if not interface_path.exists():
                        interface_path = bundle_path / "interface.json"

                    icon_path = None
                    interface_data = {}
                    if interface_path.exists():
                        try:
                            if force_refresh:
                                # 强制刷新模式：直接读取文件，不使用缓存
                                # 这样可以确保读取到更新后的最新内容
                                logger.debug(f"强制刷新模式：直接读取 interface 文件: {interface_path}")
                                # 多次尝试读取，确保文件系统同步
                                max_retries = 3
                                for retry in range(max_retries):
                                    try:
                                        with open(interface_path, "r", encoding="utf-8") as f:
                                            interface_data = jsonc.load(f)
                                        if interface_data:
                                            break
                                    except (IOError, jsonc.JSONDecodeError) as e:
                                        if retry < max_retries - 1:
                                            logger.debug(f"读取 interface 文件失败，重试 {retry + 1}/{max_retries}: {e}")
                                            time.sleep(0.1)  # 等待文件系统同步
                                        else:
                                            logger.error(f"读取 interface 文件失败: {e}")
                                            raise
                                
                                # 如果需要翻译，再使用 InterfaceManager 进行翻译
                                if interface_data:
                                    interface_manager = get_interface_manager()
                                    current_language = interface_manager.get_language()
                                    # 使用 preview_interface 进行翻译（会重新读取文件，但我们已经确保文件是最新的）
                                    translated_data = interface_manager.preview_interface(
                                        interface_path, language=current_language
                                    )
                                    if translated_data:
                                        interface_data = translated_data
                                    else:
                                        logger.warning(f"preview_interface 返回空数据，使用直接读取的数据")
                            else:
                                # 正常模式：使用 InterfaceManager 的 preview_interface 方法加载并翻译 interface 文件
                                # 这样可以支持 i18n 功能
                                interface_manager = get_interface_manager()
                                current_language = interface_manager.get_language()
                                
                                # 预览并翻译该 bundle 的 interface 文件
                                interface_data = interface_manager.preview_interface(
                                    interface_path, language=current_language
                                )
                                
                                # 如果预览失败（返回空字典），回退到直接读取
                                if not interface_data:
                                    logger.warning(
                                        f"使用 preview_interface 加载失败，回退到直接读取: {interface_path}"
                                    )
                                    with open(interface_path, "r", encoding="utf-8") as f:
                                        interface_data = jsonc.load(f)
                            
                            icon_relative = interface_data.get("icon", "")
                            if icon_relative:
                                icon_path = bundle_path / icon_relative
                                if not icon_path.exists():
                                    icon_path = None
                        except Exception as e:
                            logger.warning(
                                f"读取 interface 文件失败 {interface_path}: {e}"
                            )
                            # 如果出错，尝试直接读取原始文件
                            try:
                                with open(interface_path, "r", encoding="utf-8") as f:
                                    interface_data = jsonc.load(f)
                            except Exception as e2:
                                logger.error(
                                    f"直接读取 interface 文件也失败: {e2}"
                                )

                    # 获取版本信息
                    bundle_version = interface_data.get("version", "未知版本")

                    # 保存数据
                    self._bundle_data[bundle_name] = {
                        "name": bundle_display_name,
                        "path": str(bundle_path),
                        "icon": str(icon_path) if icon_path else None,
                        "interface": interface_data,
                    }

                    # 创建列表项
                    item_widget = BundleListItem(
                        bundle_display_name,
                        bundle_version,
                        str(icon_path) if icon_path else None,
                    )
                    
                    # 如果有已检查到的最新版本，立即显示
                    if bundle_name in self._latest_versions:
                        latest_version = self._latest_versions[bundle_name]
                        item_widget.update_latest_version(latest_version)

                    list_item = QListWidgetItem(self.list_widget)
                    list_item.setSizeHint(item_widget.sizeHint())
                    list_item.setData(
                        Qt.ItemDataRole.UserRole, bundle_name
                    )  # 保存原始名称
                    self.list_widget.setItemWidget(list_item, item_widget)
                    self.list_widget.addItem(list_item)

                except Exception as e:
                    logger.error(f"加载 bundle '{bundle_name}' 失败: {e}")
                    continue

        except Exception as e:
            logger.error(f"加载 bundle 列表失败: {e}")

    def _on_bundle_selected(self, current: QListWidgetItem, previous: QListWidgetItem):
        """处理 bundle 选择事件"""
        if not current:
            return

        bundle_name = current.data(Qt.ItemDataRole.UserRole)
        if not bundle_name:
            return

        # 发送信号
        self.bundle_selected.emit(bundle_name)

        # 更新右侧显示
        self._update_detail_view(bundle_name)

    def _update_detail_view(self, bundle_name: str):
        """更新右侧详情视图"""
        # 清除现有内容（但保留 default_label）
        items_to_remove = []
        for i in range(self.detail_layout.count()):
            item = self.detail_layout.itemAt(i)
            if item:
                widget = item.widget()
                if widget and widget != self.default_label:
                    items_to_remove.append(i)
        
        # 从后往前删除，避免索引变化
        for i in reversed(items_to_remove):
            item = self.detail_layout.takeAt(i)
            if item:
                widget = item.widget()
                if widget:
                    widget.setParent(None)  # 先移除父级关系
                    widget.deleteLater()

        # 处理 stretch 项
        # 查找并移除所有 stretch 项
        for i in range(self.detail_layout.count() - 1, -1, -1):
            item = self.detail_layout.itemAt(i)
            if item and not item.widget():  # stretch 项没有 widget
                self.detail_layout.takeAt(i)

        # 隐藏默认提示（如果仍然有效）
        try:
            if hasattr(self, 'default_label') and self.default_label:
                # 检查对象是否仍然有效
                try:
                    if self.default_label.isVisible():
                        self.default_label.hide()
                except RuntimeError:
                    # 对象已被删除，忽略错误
                    pass
        except (AttributeError, RuntimeError):
            # default_label 不存在或已被删除，忽略错误
            pass

        # 获取 bundle 数据
        bundle_data = self._bundle_data.get(bundle_name, {})
        if not bundle_data:
            logger.warning(f"Bundle '{bundle_name}' 数据不存在")
            return
        
        interface_data = bundle_data.get("interface", {})
        if not interface_data:
            logger.warning(f"Bundle '{bundle_name}' interface 数据不存在")
            return

        # 创建详情组件
        detail = BundleDetailWidget(
            bundle_name, bundle_data, interface_data, self.detail_widget
        )
        self.detail_layout.addWidget(detail)
        self.detail_layout.addStretch()

    def _check_all_updates(self):
        """检查所有bundle的更新"""
        try:
            bundle_names = self.service_coordinator.config.list_bundles()
            if not bundle_names:
                return

            for bundle_name in bundle_names:
                bundle_data = self._bundle_data.get(bundle_name)
                if not bundle_data:
                    continue
                
                interface_data = bundle_data.get("interface", {})
                if not interface_data:
                    continue
                
                # 创建更新检查器
                checker = Update(
                    service_coordinator=self.service_coordinator,
                    stop_signal=signalBus.update_stopped,
                    progress_signal=signalBus.update_progress,
                    info_bar_signal=signalBus.info_bar_requested,
                    interface=interface_data,
                    check_only=True,
                )
                
                # 连接检查结果信号
                checker.check_result_ready.connect(
                    lambda result, name=bundle_name: self._on_update_check_result(name, result)
                )
                checker.finished.connect(checker.deleteLater)
                
                self._update_checkers[bundle_name] = checker
                checker.start()
                logger.info(f"开始检查 bundle '{bundle_name}' 的更新")
                
        except Exception as e:
            logger.error(f"检查所有bundle更新失败: {e}", exc_info=True)
    
    def _on_update_check_result(self, bundle_name: str, result: dict):
        """处理单个bundle的更新检查结果"""
        try:
            latest_version = result.get("latest_update_version", "")
            if latest_version:
                self._latest_versions[bundle_name] = latest_version
                # 更新列表项的显示
                self._update_bundle_item_version(bundle_name, latest_version)
                logger.info(f"Bundle '{bundle_name}' 最新版本: {latest_version}")
            else:
                self._latest_versions[bundle_name] = None
                # 如果没有找到更新，使用当前版本
                bundle_data = self._bundle_data.get(bundle_name, {})
                interface_data = bundle_data.get("interface", {})
                current_version = interface_data.get("version", "未知版本")
                self._update_bundle_item_version(bundle_name, current_version)
        except Exception as e:
            logger.error(f"处理 bundle '{bundle_name}' 更新检查结果失败: {e}", exc_info=True)
    
    def _update_bundle_item_version(self, bundle_name: str, latest_version: Optional[str]):
        """更新列表项的版本显示"""
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item and item.data(Qt.ItemDataRole.UserRole) == bundle_name:
                item_widget = self.list_widget.itemWidget(item)
                if isinstance(item_widget, BundleListItem):
                    item_widget.update_latest_version(latest_version)
                break

    def start_auto_update_all(self):
        """供主界面调用的自动更新所有bundle入口"""
        if self._current_updater:
            logger.warning("已有更新任务正在进行中")
            return
        
        logger.info("开始自动更新所有bundle...")
        try:
            bundle_names = self.service_coordinator.config.list_bundles()
            if not bundle_names:
                logger.warning("没有找到任何bundle")
                # 没有bundle，直接发送完成信号
                signalBus.all_updates_completed.emit()
                return

            # 过滤出有更新的bundle
            bundles_to_update = []
            for bundle_name in bundle_names:
                latest_version = self._latest_versions.get(bundle_name)
                bundle_data = self._bundle_data.get(bundle_name, {})
                interface_data = bundle_data.get("interface", {})
                current_version = interface_data.get("version", "")
                
                # 如果有最新版本且与当前版本不同，加入更新队列
                if latest_version and latest_version != current_version:
                    bundles_to_update.append(bundle_name)
            
            if not bundles_to_update:
                logger.info("所有bundle都是最新版本，无需更新")
                # 没有需要更新的bundle，直接发送完成信号
                signalBus.all_updates_completed.emit()
                return
            
            # 将需要更新的bundle加入队列
            self._update_queue = bundles_to_update
            self._is_updating_all = True
            self._start_next_update()
            
        except Exception as e:
            logger.error(f"自动更新所有bundle失败: {e}", exc_info=True)
            self._is_updating_all = False
            # 发生错误，发送完成信号
            signalBus.all_updates_completed.emit()
    
    def _on_update_all_bundles(self):
        """更新所有bundle按钮点击事件"""
        if self._current_updater:
            logger.warning("已有更新任务正在进行中")
            return
        
        logger.info("开始更新所有bundle...")
        try:
            bundle_names = self.service_coordinator.config.list_bundles()
            if not bundle_names:
                logger.warning("没有找到任何bundle")
                return

            # 过滤出有更新的bundle
            bundles_to_update = []
            for bundle_name in bundle_names:
                latest_version = self._latest_versions.get(bundle_name)
                bundle_data = self._bundle_data.get(bundle_name, {})
                interface_data = bundle_data.get("interface", {})
                current_version = interface_data.get("version", "")
                
                # 如果有最新版本且与当前版本不同，加入更新队列
                if latest_version and latest_version != current_version:
                    bundles_to_update.append(bundle_name)
            
            if not bundles_to_update:
                logger.info("所有bundle都是最新版本，无需更新")
                signalBus.info_bar_requested.emit("info", self.tr("All bundles are up to date"))
                return
            
            # 将需要更新的bundle加入队列
            self._update_queue = bundles_to_update
            self._is_updating_all = True
            self._start_next_update()
            
        except Exception as e:
            logger.error(f"更新所有bundle失败: {e}", exc_info=True)
            self._is_updating_all = False
    
    def _on_single_bundle_update(self, bundle_name: str):
        """处理单个bundle的更新"""
        if self._current_updater:
            logger.warning("已有更新任务正在进行中")
            return
        
        logger.info(f"开始更新单个bundle: {bundle_name}")
        self._update_queue = [bundle_name]
        self._is_updating_all = False
        self._start_next_update()
    
    def _start_next_update(self):
        """开始下一个更新任务"""
        if not self._update_queue:
            # 所有更新完成
            is_auto_update_all = self._is_updating_all  # 保存状态
            self._is_updating_all = False
            self._current_updater = None
            
            if not is_auto_update_all:
                # 如果不是自动更新所有模式，显示通知
                signalBus.info_bar_requested.emit("success", self.tr("All updates completed"))
            logger.info("所有更新任务完成")
            # 等待文件系统同步（确保文件写入完成）
            time.sleep(0.5)
            QCoreApplication.processEvents()  # 确保UI更新
            # 重新加载bundles以刷新版本信息（强制刷新）
            self._load_bundles(force_refresh=True)
            # 重新检查更新以获取最新的版本信息
            QCoreApplication.processEvents()  # 确保UI更新
            self._check_all_updates()
            
            # 如果是自动更新所有模式，发送所有更新完成信号
            if is_auto_update_all:
                signalBus.all_updates_completed.emit()
                logger.info("Bundle 自动更新完成，已发送 all_updates_completed 信号")
            return
        
        bundle_name = self._update_queue.pop(0)
        bundle_data = self._bundle_data.get(bundle_name)
        if not bundle_data:
            # 如果bundle数据不存在，继续下一个
            self._start_next_update()
            return
        
        interface_data = bundle_data.get("interface", {})
        if not interface_data:
            # 如果interface数据不存在，继续下一个
            self._start_next_update()
            return
        
        # 创建更新器（使用 MultiResourceUpdate 子类处理多资源更新）
        updater = MultiResourceUpdate(
            service_coordinator=self.service_coordinator,
            stop_signal=signalBus.update_stopped,
            progress_signal=signalBus.update_progress,
            info_bar_signal=signalBus.info_bar_requested,
            interface=interface_data,
            force_full_download=False,
        )
        
        # 连接更新完成信号
        updater.finished.connect(
            lambda: self._on_update_finished(bundle_name)
        )
        
        self._current_updater = updater
        self._current_bundle_name = bundle_name  # 保存当前更新的bundle名称
        updater.start()
        logger.info(f"开始更新 bundle: {bundle_name}")
        signalBus.info_bar_requested.emit("info", self.tr(f"Updating bundle: {bundle_name}"))
    
    def _on_update_finished(self, bundle_name: str):
        """更新线程完成回调（线程结束，但不一定表示更新成功）"""
        logger.info(f"Bundle '{bundle_name}' 更新线程完成")
        # 注意：实际的更新状态通过 update_stopped 信号处理
    
    def _on_update_stopped(self, status: int):
        """更新停止信号处理（Update 类自动发送，用于通知主界面和更新 UI）"""
        if not self._current_updater or not self._current_bundle_name:
            # 如果不是当前 bundle 的更新，忽略（可能是其他地方的更新）
            return
        
        bundle_name = self._current_bundle_name
        is_auto_update_all = self._is_updating_all  # 保存状态
        logger.info(f"Bundle '{bundle_name}' 更新停止，状态码: {status}")
        
        if status == 1:
            # 热更新完成
            logger.info(f"Bundle '{bundle_name}' 热更新成功完成")
            if not is_auto_update_all:
                # 如果不是自动更新所有，显示通知
                signalBus.info_bar_requested.emit("success", self.tr(f"Bundle '{bundle_name}' updated successfully"))
        elif status == 0:
            # 用户取消
            logger.warning(f"Bundle '{bundle_name}' 更新被取消")
            if not is_auto_update_all:
                signalBus.info_bar_requested.emit("warning", self.tr(f"Update cancelled: {bundle_name}"))
        elif status == 2:
            # 需要重启
            logger.info(f"Bundle '{bundle_name}' 需要重启以完成更新")
            if not is_auto_update_all:
                signalBus.info_bar_requested.emit("info", self.tr(f"Restart required for bundle: {bundle_name}"))
        else:
            # 其他错误
            logger.error(f"Bundle '{bundle_name}' 更新失败，状态码: {status}")
            if not is_auto_update_all:
                signalBus.info_bar_requested.emit("error", self.tr(f"Update failed for bundle: {bundle_name}"))
        
        # 清理当前更新器
        self._current_updater = None
        self._current_bundle_name = None
        
        # 继续下一个更新（所有更新完成后再重新加载）
        self._start_next_update()

    def _on_auto_update_changed(self, checked: bool):
        """自动更新开关状态改变事件"""
        from app.common.config import cfg

        try:
            cfg.set(cfg.bundle_auto_update, checked)
            logger.info(f"Bundle 自动更新设置已更新: {'开启' if checked else '关闭'}")
        except Exception as e:
            logger.error(f"更新 Bundle 自动更新设置失败: {e}", exc_info=True)
