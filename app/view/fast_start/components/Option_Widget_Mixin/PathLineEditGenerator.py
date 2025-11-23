import json
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtCore import Qt
from qfluentwidgets import BodyLabel, ToolTipFilter
from app.widget.PathLineEdit import PathLineEdit
from app.utils.logger import logger

class PathLineEditGenerator:
    """
    带按钮的路径输入框生成器
    负责带浏览按钮的路径输入框的创建、配置和信号处理
    """

    def __init__(self, host):
        """
        初始化路径输入框生成器
        :param host: 宿主组件，需要包含widgets、child_layouts等属性
        """
        self.host = host

    def create_pathlineedit(self, key, config, parent_layout, parent_config):
        """创建带按钮的路径输入框"""
        # 创建控件容器布局
        container_layout = QVBoxLayout()
        container_layout.setContentsMargins(5, 5, 5, 5)
        container_layout.setSpacing(5)
        parent_layout.addLayout(container_layout)

        # 创建标签和图标容器
        label_container = QHBoxLayout()
        label_container.setSpacing(5)
        
        # 检查是否有图标配置
        icon_label = None
        if "icon" in config:
            try:
                from app.utils.gui_helper import IconLoader
                
                # 检查是否有icon_loader，如果没有则创建
                if not hasattr(self.host, '_icon_loader'):
                    if hasattr(self.host, 'service_coordinator'):
                        self.host._icon_loader = IconLoader(self.host.service_coordinator)
                
                # 使用IconLoader加载图标
                if hasattr(self.host, '_icon_loader'):
                    icon = self.host._icon_loader.load_icon(config["icon"], size=24)
                    if not icon.isNull():
                        icon_label = QLabel()
                        icon_label.setPixmap(icon.pixmap(24, 24))
                        icon_label.setFixedSize(24, 24)
                        
                        # 添加图标到容器
                        label_container.addWidget(icon_label)
            except Exception as e:
                # 尝试直接加载作为备选方案
                try:
                    icon_path = config["icon"]
                    icon_pixmap = QPixmap(icon_path)
                
                    # 检查图标是否加载成功
                    if not icon_pixmap.isNull():
                        # 缩放图标到合适大小
                        icon_pixmap = icon_pixmap.scaled(
                            24, 24, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
                        )
                        icon_label = QLabel()
                        icon_label.setPixmap(icon_pixmap)
                        icon_label.setFixedSize(24, 24)
                        
                        # 添加图标到容器
                        label_container.addWidget(icon_label)
                except Exception as fallback_e:
                    # 加载图标失败时忽略
                    logger.error(f"加载图标失败: {config['icon']}, 错误: {fallback_e}")

        # 处理标签，移除可能的$符号
        label_text = config["label"]
        if label_text.startswith("$"):
            pass
        label = BodyLabel(label_text)
        # 移除固定宽度，让标签自然显示
        
        # 添加标签到容器
        label_container.addWidget(label)
        
        # 将整个标签容器添加到主布局
        container_layout.addLayout(label_container)
        
        # 为选项标题添加tooltip（选项层级）
        if "description" in config:
            filter = ToolTipFilter(label)
            label.installEventFilter(filter)
            label.setToolTip(config["description"])

        # 创建带按钮的路径输入框
        path_line_edit = PathLineEdit()
        
        # 设置文件过滤器（如果有配置）
        if "file_filter" in config:
            path_line_edit.setFileFilter(config["file_filter"])
        
        if "default" in config:
            path_line_edit.setText(config["default"])

        container_layout.addWidget(path_line_edit)
        
        # 检查是否需要隐藏整个路径输入框行
        if "visible" in config and not config["visible"]:
            # 隐藏标签和路径输入框
            label.setVisible(False)
            path_line_edit.setVisible(False)
            
            # 如果有图标也隐藏
            if icon_label:
                icon_label.setVisible(False)
        
        # 为输入框控件添加tooltip（选项内部层级）
        if "description" in config:
            filter = ToolTipFilter(path_line_edit)
            path_line_edit.installEventFilter(filter)
            path_line_edit.setToolTip(config["description"])

        # 保存引用
        self.host.widgets[key] = path_line_edit

        # 初始化配置
        parent_config[key] = path_line_edit.text()

        # 连接信号（用户交互时保存配置）
        path_line_edit.textChanged.connect(
            lambda text, k=key, p_conf=parent_config: self._on_pathlineedit_changed(
                k, text, p_conf, save_config=True
            )
        )

    def _on_pathlineedit_changed(self, key, text, parent_config, save_config=True):
        """路径输入框值改变处理
        
        :param save_config: 是否保存配置，默认为True。初始化时可以设置为False避免保存默认值
        """
        parent_config[key] = text
        # 自动保存选项，只有当save_config为True且未禁用自动保存时才保存
        if save_config and (not hasattr(self.host, "_disable_auto_save") or not self.host._disable_auto_save):
            self._auto_save_options()

    def _auto_save_options(self):
        """自动保存当前选项"""
        # 检查是否禁用了自动保存
        if hasattr(self.host, "_disable_auto_save") and self.host._disable_auto_save:
            return
            
        # 检查是否有service_coordinator和option_service
        if hasattr(self.host, "service_coordinator") and hasattr(self.host.service_coordinator, "option_service"):  # type: ignore
            try:
                # 获取当前所有配置
                all_config = self.host.get_config()
                # 调用OptionService的update_options方法保存选项
                self.host.service_coordinator.option_service.update_options(all_config)  # type: ignore
            except Exception as e:
                # 如果保存失败，记录错误但不影响用户操作
                logger.error(f"自动保存选项失败: {e}")