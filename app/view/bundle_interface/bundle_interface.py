"""
MFW-ChainFlow Assistant
Bundle 管理界面
作者:overflow65537
"""

import jsonc
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
    PrimaryPushButton,
    SimpleCardWidget,
    ToolButton,
    ToolTipFilter,
    ToolTipPosition,
    FluentIcon as FIF,
    ComboBox,
    TogglePushButton,
)

from app.core.core import ServiceCoordinator
from app.core.service.interface_manager import get_interface_manager
from app.utils.logger import logger


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

        self.version_label = QLabel(bundle_version, self)
        self.version_label.setStyleSheet("font-size: 12px; color: gray;")
        self.version_label.setWordWrap(True)

        text_layout.addWidget(self.name_label)
        text_layout.addWidget(self.version_label)

        layout.addWidget(self.icon_label)
        layout.addLayout(text_layout)
        layout.addStretch()

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)


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

        # 区域3：功能按钮
        self._add_action_buttons_section(layout)

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
        description_label = BodyLabel(description_text, self)
        description_label.setWordWrap(True)
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
        contact_label = BodyLabel(contact_text, self)
        contact_label.setWordWrap(True)
        section_layout.addWidget(contact_label)

        parent_layout.addLayout(section_layout)

    def _add_action_buttons_section(self, parent_layout: QVBoxLayout):
        """添加功能按钮区域"""
        _translate = QCoreApplication.translate
        section_layout = QVBoxLayout()
        section_layout.setSpacing(8)
        section_layout.setContentsMargins(0, 0, 0, 0)

        title = TitleLabel(_translate("BundleInterface", "功能"), self)
        section_layout.addWidget(title)

        # 水平布局的按钮和下拉框
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(12)
        buttons_layout.setContentsMargins(0, 0, 0, 0)

        # 立刻更新按钮
        update_btn = PrimaryPushButton(_translate("BundleInterface", "立刻更新"), self)
        update_btn.clicked.connect(self._on_update_clicked)
        buttons_layout.addWidget(update_btn)

        # 下拉框：频道
        self.channel_combo = ComboBox(self)
        self.channel_combo.addItems(["Alpha", "Beta", "Stable"])
        # 从配置中读取当前频道并设置
        from app.common.config import cfg

        channel_value = cfg.get(cfg.resource_update_channel)
        channel_map = {0: 0, 1: 1, 2: 2}  # ALPHA=0, BETA=1, STABLE=2
        if channel_value in channel_map:
            self.channel_combo.setCurrentIndex(channel_map[channel_value])
        self.channel_combo.currentIndexChanged.connect(self._on_channel_changed)
        buttons_layout.addWidget(self.channel_combo)

        buttons_layout.addStretch()
        section_layout.addLayout(buttons_layout)

        parent_layout.addLayout(section_layout)

    def _on_update_clicked(self):
        """更新按钮点击事件"""
        # TODO: 实现更新功能
        logger.info(f"更新 Bundle: {self.bundle_name}")

    def _on_channel_changed(self, index: int):
        """频道下拉框改变事件"""
        from app.common.config import cfg

        channel_map = {0: 0, 1: 1, 2: 2}  # Alpha=0, Beta=1, Stable=2
        if index in channel_map:
            cfg.set(cfg.resource_update_channel, channel_map[index])
            logger.info(f"更新频道设置为: {['Alpha', 'Beta', 'Stable'][index]}")


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

        # 设置标题
        self.list_title.setText(self.tr("Bundle 列表"))
        self.detail_title.setText(self.tr("Bundle 详情"))

        # 连接信号
        self.list_widget.currentItemChanged.connect(self._on_bundle_selected)
        self.update_all_button.clicked.connect(self._on_update_all_bundles)
        self.auto_update_switch.toggled.connect(self._on_auto_update_changed)

        # 加载 bundle 列表
        self._load_bundles()

    def _load_bundles(self):
        """从 service_coordinator 加载所有 bundle"""
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
                            # 使用 InterfaceManager 的 preview_interface 方法加载并翻译 interface 文件
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
        # 清除现有内容
        while self.detail_layout.count():
            item = self.detail_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # 隐藏默认提示
        if self.default_label:
            self.default_label.hide()

        # 获取 bundle 数据
        bundle_data = self._bundle_data.get(bundle_name, {})
        interface_data = bundle_data.get("interface", {})

        # 创建详情组件
        detail = BundleDetailWidget(
            bundle_name, bundle_data, interface_data, self.detail_widget
        )
        self.detail_layout.addWidget(detail)
        self.detail_layout.addStretch()

    def _on_update_all_bundles(self):
        """更新所有bundle按钮点击事件"""
        # TODO: 实现更新所有bundle功能
        logger.info("开始更新所有bundle...")
        try:
            bundle_names = self.service_coordinator.config.list_bundles()
            if not bundle_names:
                logger.warning("没有找到任何bundle")
                return

            # 遍历所有bundle并更新
            for bundle_name in bundle_names:
                logger.info(f"更新bundle: {bundle_name}")
                # TODO: 调用实际的更新方法
                # 这里需要根据实际的更新逻辑来实现
        except Exception as e:
            logger.error(f"更新所有bundle失败: {e}", exc_info=True)

    def _on_auto_update_changed(self, checked: bool):
        """自动更新开关状态改变事件"""
        from app.common.config import cfg

        try:
            cfg.set(cfg.bundle_auto_update, checked)
            logger.info(f"Bundle 自动更新设置已更新: {'开启' if checked else '关闭'}")
        except Exception as e:
            logger.error(f"更新 Bundle 自动更新设置失败: {e}", exc_info=True)
