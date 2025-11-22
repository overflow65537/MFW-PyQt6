import json
import re
from pathlib import Path
from typing import List

import markdown
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QSplitter,
)

from qfluentwidgets import (
    SimpleCardWidget,
    ToolTipPosition,
    ToolTipFilter,
    BodyLabel,
    ScrollArea,
    ComboBox,
    EditableComboBox,
    SwitchButton,
    PrimaryPushButton,
    LineEdit,
    SpinBox,
    CheckBox,
)
from app.view.fast_start.animations.option_transition import OptionTransitionAnimator
from app.view.fast_start.components.Option_Widget_Mixin.DynamicFormMixin import (
    DynamicFormMixin,
)

from app.utils.logger import logger
from app.common.signal_bus import signalBus
from app.common.constants import RESOURCE_TASK_ID, POST_TASK_ID
from app.utils.gui_helper import IconLoader
from app.widget.PathLineEdit import PathLineEdit

from ....core.Core import TaskItem, ConfigItem, ServiceCoordinator


class OptionWidget(QWidget, DynamicFormMixin):
    def __init__(self, service_coordinator: ServiceCoordinator, parent=None):
        # 先调用QWidget的初始化
        QWidget.__init__(self, parent)
        # 再调用DynamicFormMixin的初始化
        DynamicFormMixin.__init__(self)

        self.service_coordinator = service_coordinator
        # 设置parent_layout为option_area_layout，供DynamicFormMixin使用
        self.parent_layout = None  # 将在_setup_ui中设置
        self._init_ui()
        self._toggle_description(visible=False)

        # 连接CoreSignalBus的options_loaded信号
        service_coordinator.signal_bus.options_loaded.connect(self._on_options_loaded)

    def _init_ui(self):
        """初始化UI"""
        self.main_layout = QVBoxLayout(self)

        self.title_widget = BodyLabel()
        self.title_widget.setStyleSheet("font-size: 20px;")
        self.title_widget.setAlignment(Qt.AlignmentFlag.AlignLeft)

        # ==================== 选项区域 ==================== #
        # 创建选项卡片
        self.option_area_card = SimpleCardWidget()
        self.option_area_card.setClickEnabled(False)
        self.option_area_card.setBorderRadius(8)

        # 创建滚动区域
        self.option_area_widget = ScrollArea()
        self.option_area_widget.setWidgetResizable(
            True
        )  # 重要:允许内部widget自动调整大小
        # 禁用横向滚动
        self.option_area_widget.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        # 设置透明无边框
        self.option_area_widget.setStyleSheet(
            "background-color: transparent; border: none;"
        )

        # 创建一个容器widget来承载布局
        option_container = QWidget()
        self.option_area_layout = QVBoxLayout(option_container)  # 将布局关联到容器
        self.option_area_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.option_area_layout.setContentsMargins(10, 10, 10, 10)  # 添加内边距

        # 设置DynamicFormMixin的parent_layout为option_area_layout
        self.parent_layout = self.option_area_layout

        # 将容器widget设置到滚动区域
        self.option_area_widget.setWidget(option_container)
        # 初始化过渡动画器
        self._option_animator = OptionTransitionAnimator(option_container)

        # 创建一个垂直布局给卡片,然后将滚动区域添加到这个布局中
        card_layout = QVBoxLayout()
        card_layout.addWidget(self.option_area_widget)
        card_layout.setContentsMargins(0, 0, 0, 0)
        self.option_area_card.setLayout(card_layout)
        # ==================== 描述区域 ==================== #
        # 创建描述标题（直接放在主布局中）
        self.description_title = BodyLabel("功能描述")
        self.description_title.setStyleSheet("font-size: 20px;")
        self.description_title.setAlignment(Qt.AlignmentFlag.AlignLeft)

        # 创建描述卡片
        self.description_area_card = SimpleCardWidget()
        self.description_area_card.setClickEnabled(False)
        self.description_area_card.setBorderRadius(8)

        # 正确的布局层次结构
        self.description_area_widget = (
            QWidget()
        )  # 使用普通Widget作为容器，而不是ScrollArea
        self.description_layout = QVBoxLayout(
            self.description_area_widget
        )  # 这个布局只属于widget
        self.description_layout.setContentsMargins(10, 10, 10, 10)  # 设置适当的边距

        # 描述内容区域
        self.description_content = BodyLabel()
        self.description_content.setWordWrap(True)
        self.description_layout.addWidget(self.description_content)

        self.description_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # 创建滚动区域来包裹内容
        self.description_scroll_area = ScrollArea()
        self.description_scroll_area.setWidget(self.description_area_widget)
        self.description_scroll_area.setWidgetResizable(True)
        self.description_scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.description_scroll_area.setStyleSheet(
            "background-color: transparent; border: none;"
        )

        # 将滚动区域添加到卡片
        card_layout = QVBoxLayout(self.description_area_card)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.addWidget(self.description_scroll_area)

        # ==================== 分割器 ==================== #
        # 创建垂直分割器，实现可调整比例功能
        self.splitter = QSplitter(Qt.Orientation.Vertical)
        self.splitter.setStyleSheet(
            """
            QSplitter::handle:vertical {
                background: transparent;   
            }
            """
        )

        # 创建选项区域容器（仅用于分割器）
        self.option_splitter_widget = QWidget()
        self.option_splitter_layout = QVBoxLayout(self.option_splitter_widget)
        self.option_splitter_layout.addWidget(self.option_area_card)
        self.option_splitter_layout.setContentsMargins(0, 0, 0, 0)

        # 创建描述区域容器（仅用于分割器）
        self.description_splitter_widget = QWidget()
        self.description_splitter_layout = QVBoxLayout(self.description_splitter_widget)
        self.description_splitter_layout.addWidget(self.description_title)
        self.description_splitter_layout.addWidget(self.description_area_card)
        # 设置占用比例
        self.description_splitter_layout.setStretch(0, 1)  # 标题占用1单位
        self.description_splitter_layout.setStretch(1, 99)  # 内容占用99单位
        self.description_splitter_layout.setContentsMargins(0, 0, 0, 0)

        # 添加到分割器
        self.splitter.addWidget(self.option_splitter_widget)  # 上方：选项区域
        self.splitter.addWidget(self.description_splitter_widget)  # 下方：描述区域

        # 设置初始比例
        self.splitter.setSizes([90, 10])  # 90% 和 10% 的初始比例

        # 添加到主布局
        self.main_layout.addWidget(self.title_widget)  # 直接添加标题
        self.main_layout.addWidget(self.splitter)  # 添加分割器
        # 添加主布局间距
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(5)

    # ==================== UI 辅助方法 ==================== #

    def _toggle_description(self, visible=None):
        """切换描述区域的显示/隐藏
        visible: True显示，False隐藏，None切换当前状态
        """
        if visible is None:
            # 切换当前状态
            visible = not self.description_splitter_widget.isVisible()

        if visible:
            self.description_splitter_widget.show()
            # 恢复初始比例
            self.splitter.setSizes([90, 10])
        else:
            self.description_splitter_widget.hide()
            # 让选项区域占据全部空间
            self.splitter.setSizes([100, 0])

    def set_description(self, description: str):
        """设置描述内容"""
        self.description_content.setText("")
        
        # 如果description为空，隐藏描述区域
        if not description.strip():
            self._toggle_description(visible=False)
            return
            
        html = markdown.markdown(description).replace("\n", "")
        html = re.sub(
            r"<code>(.*?)</code>",
            r"<span style='color: #009faa;'>\1</span>",
            html,
        )
        html = re.sub(
            r'(<a\s+[^>]*href="[^"]+"[^>]*)>', r'\1 style="color: #009faa;">', html
        )
        html = re.sub(r"<li><p>(.*?)</p></li>", r"<p><strong>◆ </strong>\1</p>", html)
        html = re.sub(r"<ul>(.*?)</ul>", r"\1", html)

        self.description_content.setText(html)

    # ==================== 公共方法 ====================

    def reset(self):
        """重置选项区域和描述区域"""
        self._clear_options()
        self._toggle_description(visible=False)
        # 显示选项区域，因为已经专门的方法清除选项
        self.option_splitter_widget.show()
        
        self.current_task = None
        # 重置DynamicFormMixin的状态
        if hasattr(self, "current_config"):
            self.current_config = {}
        if hasattr(self, "widgets"):
            self.widgets = {}
        if hasattr(self, "child_layouts"):
            self.child_layouts = {}

    def _on_config_changed(self, config_id: str):
        """配置切换时重置选项面板"""
        self.reset()

    def set_title(self, title: str):
        """设置标题"""
        self.title_widget.setText(title)

    def _clear_options(self):
        """清空选项区域"""
        self._clear_layout(self.option_area_layout)

    def update_form_from_structure(self, form_structure, config=None):
        """
        直接从表单结构更新表单
        :param form_structure: 表单结构定义
        :param config: 可选的配置对象，用于设置表单的当前选择
        """
        # 显示选项区域
        self.option_splitter_widget.show()
        
        # 使用DynamicFormMixin的update_form方法更新表单
        self.update_form(form_structure, config)
        # 控制器类型切换的逻辑已由DynamicFormMixin的_on_combobox_changed方法处理

    def get_current_form_config(self):
        """
        获取当前表单的配置
        :return: 当前选择的配置字典
        """
        # 使用DynamicFormMixin的get_config方法
        return self.get_config()

    def _on_options_loaded(self, data):
        """
        当选项被加载时触发
        :param data: 包含options和form_structure的字典
        """
        # 只处理form_structure格式
        options = data.get("options", {})
        form_structure = data.get("form_structure", None)

        # 记录日志
        logger.info(f"选项加载完成，共 {len(options)} 个选项")

        # 只使用form_structure更新表单
        if form_structure:
            self.update_form_from_structure(form_structure, options)
            logger.info(f"表单已使用form_structure更新")
        else:
            # 没有表单时清除界面
            self._clear_options()  # 使用专门的方法清除选项
            self.current_config = {}
            self.widgets = {}
            self.child_layouts = {}
            # 显示选项区域，因为已经用专门的方法清除选项
            self.option_splitter_widget.show()
            # 隐藏描述区域
            self._toggle_description(visible=False)
            logger.info("没有提供form_structure，已清除界面")
            

    def _set_layout_visibility(self, layout, visible):
        """
        递归设置布局中所有控件的可见性
        :param layout: 要设置的布局
        :param visible: 是否可见
        """
        for i in range(layout.count()):
            item = layout.itemAt(i)
            if item.widget():
                item.widget().setVisible(visible)
            elif item.layout():
                self._set_layout_visibility(item.layout(), visible)