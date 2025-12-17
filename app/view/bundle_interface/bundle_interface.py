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
)

from app.core.core import ServiceCoordinator
from app.utils.logger import logger


class BundleListItem(QWidget):
    """Bundle 列表项组件"""

    def __init__(self, bundle_name: str, bundle_path: str, icon_path: Optional[str], parent=None):
        super().__init__(parent)
        self.bundle_name = bundle_name
        self.bundle_path = bundle_path
        
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
                    self.icon_label.setPixmap(pixmap.scaled(32, 32, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        
        # 名称和路径
        text_layout = QVBoxLayout()
        text_layout.setSpacing(4)
        text_layout.setContentsMargins(0, 0, 0, 0)
        
        self.name_label = QLabel(bundle_name, self)
        self.name_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        
        self.path_label = QLabel(bundle_path, self)
        self.path_label.setStyleSheet("font-size: 12px; color: gray;")
        self.path_label.setWordWrap(True)
        
        text_layout.addWidget(self.name_label)
        text_layout.addWidget(self.path_label)
        
        layout.addWidget(self.icon_label)
        layout.addLayout(text_layout)
        layout.addStretch()
        
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)


class BundleDetailWidget(CardWidget):
    """Bundle 详情显示组件（右侧滚动区域内容）"""

    def __init__(self, bundle_name: str, parent=None):
        super().__init__(parent)
        self.bundle_name = bundle_name
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        
        title = BodyLabel(self.tr("Bundle 详情"), self)
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)
        
        name_label = BodyLabel(f"{self.tr('名称')}: {bundle_name}", self)
        layout.addWidget(name_label)
        
        layout.addStretch()


class UI_BundleInterface(object):
    """Bundle 管理界面 UI 类"""
    
    def __init__(self, service_coordinator: ServiceCoordinator, parent=None):
        self.service_coordinator = service_coordinator
        self.parent = parent

    def setupUi(self, BundleInterface):
        BundleInterface.setObjectName("BundleInterface")
        
        # 主布局
        main_layout = QHBoxLayout(BundleInterface)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 左侧列表（30%）
        self.list_widget = ListWidget(BundleInterface)
        # 使用 stretch 比例实现 30:70
        main_layout.addWidget(self.list_widget, 3)  # stretch=3 对应 30%
        
        # 右侧滚动区域（70%）
        self.scroll_area = ScrollArea(BundleInterface)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.detail_widget = QWidget()
        self.detail_layout = QVBoxLayout(self.detail_widget)
        self.detail_layout.setContentsMargins(20, 20, 20, 20)
        self.detail_layout.setSpacing(12)
        
        # 默认提示
        _translate = QCoreApplication.translate
        self.default_label = BodyLabel(_translate("BundleInterface", "请从左侧选择一个 Bundle"), self.detail_widget)
        self.default_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.default_label.setStyleSheet("font-size: 16px; color: gray; padding: 40px;")
        self.detail_layout.addWidget(self.default_label)
        self.detail_layout.addStretch()
        
        self.scroll_area.setWidget(self.detail_widget)
        main_layout.addWidget(self.scroll_area, 7)  # stretch=7 对应 70%
        
        self.retranslateUi(BundleInterface)
        QMetaObject.connectSlotsByName(BundleInterface)

    def retranslateUi(self, BundleInterface):
        _translate = QCoreApplication.translate
        BundleInterface.setWindowTitle(_translate("BundleInterface", "Form"))


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
        
        # 连接信号
        self.list_widget.currentItemChanged.connect(self._on_bundle_selected)
        
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
                    bundle_info = self.service_coordinator.config.get_bundle(bundle_name)
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
                    if interface_path.exists():
                        try:
                            with open(interface_path, "r", encoding="utf-8") as f:
                                interface_data = jsonc.load(f)
                            icon_relative = interface_data.get("icon", "")
                            if icon_relative:
                                icon_path = bundle_path / icon_relative
                                if not icon_path.exists():
                                    icon_path = None
                        except Exception as e:
                            logger.warning(f"读取 interface 文件失败 {interface_path}: {e}")
                    
                    # 保存数据
                    self._bundle_data[bundle_name] = {
                        "name": bundle_display_name,
                        "path": str(bundle_path),
                        "icon": str(icon_path) if icon_path else None,
                    }
                    
                    # 创建列表项
                    item_widget = BundleListItem(
                        bundle_display_name,
                        str(bundle_path),
                        str(icon_path) if icon_path else None,
                    )
                    
                    list_item = QListWidgetItem(self.list_widget)
                    list_item.setSizeHint(item_widget.sizeHint())
                    list_item.setData(Qt.ItemDataRole.UserRole, bundle_name)  # 保存原始名称
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
        
        # 创建详情组件
        detail = BundleDetailWidget(bundle_name, self.detail_widget)
        self.detail_layout.addWidget(detail)
        self.detail_layout.addStretch()
