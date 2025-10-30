"""选项面板基类模块

提供选项面板的 UI 初始化、主入口和通用方法。
"""

import json
import re
from pathlib import Path
import markdown
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout
from qfluentwidgets import (
    SimpleCardWidget,
    BodyLabel,
    ScrollArea,
)
from app.utils.logger import logger
from ._mixin_base import MixinBase


class OptionWidgetBaseMixin(MixinBase):
    """选项面板基础 Mixin
    
    提供选项面板的核心功能：
    - UI 初始化（标题、选项区域、描述区域）
    - 主入口方法（show_option）
    - 重置方法
    - 描述区域的显示/隐藏切换
    - 描述内容设置（Markdown 支持）
    
    继承自 MixinBase，获得通用的类型提示，避免 Pylance 报错。
    运行时 `self` 指向 OptionWidget 实例，可访问其所有属性/方法。
    
    需要配合 OptionWidget 使用，依赖：
    - self.service_coordinator
    - self.task
    - self.icon_loader
    - self.core_signalBus
    - self._show_resource_setting_option (在 ResourceSettingMixin 中)
    - self._show_post_task_setting_option (在 PostTaskOptionMixin 中)
    - self._show_task_option (在 TaskOptionsMixin 中)
    - self._clear_options (在 LayoutHelperMixin 中)
    - self.tr (翻译函数)
    """
    
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
        self.option_area_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        # 设置透明无边框
        self.option_area_widget.setStyleSheet(
            "background-color: transparent; border: none;"
        )

        # 创建一个容器widget来承载布局
        option_container = QWidget()
        self.option_area_layout = QVBoxLayout(option_container)  # 将布局关联到容器
        self.option_area_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.option_area_layout.setContentsMargins(10, 10, 10, 10)  # 添加内边距

        # 将容器widget设置到滚动区域
        self.option_area_widget.setWidget(option_container)

        # 创建一个垂直布局给卡片,然后将滚动区域添加到这个布局中
        card_layout = QVBoxLayout()
        card_layout.addWidget(self.option_area_widget)
        card_layout.setContentsMargins(0, 0, 0, 0)
        self.option_area_card.setLayout(card_layout)
        
        # ==================== 描述区域 ==================== #
        # 创建描述标题（直接放在主布局中）
        self.description_title = BodyLabel(self.tr("Function Description"))
        self.description_title.setStyleSheet("font-size: 20px;")
        self.description_title.setAlignment(Qt.AlignmentFlag.AlignLeft)

        # 创建描述卡片
        self.description_area_card = SimpleCardWidget()
        self.description_area_card.setClickEnabled(False)
        self.description_area_card.setBorderRadius(8)

        # 正确的布局层次结构
        self.description_area_widget = QWidget()  # 使用普通Widget作为容器
        self.description_layout = QVBoxLayout(self.description_area_widget)
        self.description_layout.setContentsMargins(10, 10, 10, 10)

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

        # 将滚动区域添加到描述卡片
        description_card_layout = QVBoxLayout()
        description_card_layout.addWidget(self.description_scroll_area)
        description_card_layout.setContentsMargins(0, 0, 0, 0)
        self.description_area_card.setLayout(description_card_layout)

        # ==================== 使用 QSplitter 实现可调整大小的分割 ==================== #
        from PySide6.QtWidgets import QSplitter, QVBoxLayout as QVBox
        
        # 创建上半部分的容器（包含标题和选项卡片）
        self.option_splitter_widget = QWidget()
        option_splitter_layout = QVBox(self.option_splitter_widget)
        option_splitter_layout.addWidget(self.title_widget)
        option_splitter_layout.addWidget(self.option_area_card)
        option_splitter_layout.setContentsMargins(0, 0, 0, 0)

        # 创建下半部分的容器（包含描述标题和描述卡片）
        self.description_splitter_widget = QWidget()
        description_splitter_layout = QVBox(self.description_splitter_widget)
        description_splitter_layout.addWidget(self.description_title)
        description_splitter_layout.addWidget(self.description_area_card)
        description_splitter_layout.setContentsMargins(0, 0, 0, 0)

        # 创建分割器并添加两个部分
        self.splitter = QSplitter(Qt.Orientation.Vertical)
        self.splitter.addWidget(self.option_splitter_widget)
        self.splitter.addWidget(self.description_splitter_widget)

        # 设置初始比例 (选项区域:描述区域 = 90:10)
        self.splitter.setSizes([90, 10])

        # 设置最小尺寸，确保用户可以调整
        self.splitter.setChildrenCollapsible(False)

        # 将分割器添加到主布局
        self.main_layout.addWidget(self.splitter)

    def show_option(self, item_or_id):
        """显示选项。参数可以是 task_id(str) 或 TaskItem/ConfigItem 对象。
        
        Args:
            item_or_id: TaskItem/ConfigItem 对象或任务 ID 字符串
        """
        self.reset()
        
        # 如果传入的是 id，获取对象
        item = item_or_id
        if isinstance(item_or_id, str):
            item = self.task.get_task(item_or_id)
        if not item:
            return
        
        # 需要导入 TaskItem 来做类型检查
        # 但为了避免循环导入，这里使用鸭子类型
        if hasattr(item, 'item_id'):
            # 保存当前任务引用
            self.current_task = item
            
            # 通过 item_id 前缀判断是否是基础任务
            # 基础任务 ID 前缀: r_ (资源设置), f_ (完成后操作)
            if item.item_id.startswith("r_"):
                # 资源设置基础任务（包含控制器和资源配置）
                self._show_resource_setting_option(item)
            elif item.item_id.startswith("f_"):
                # 完成后操作基础任务
                self._show_post_task_setting_option(item)
            else:
                # 普通任务，使用默认显示
                self._show_task_option(item)

    def reset(self):
        """重置选项区域和描述区域"""
        self._clear_options()
        self._toggle_description(visible=False)
        self.current_task = None

    def _on_config_changed(self, config_id: str):
        """配置切换时重置选项面板
        
        Args:
            config_id: 配置 ID
        """
        self.reset()

    def set_title(self, title: str):
        """设置标题
        
        Args:
            title: 标题文本
        """
        self.title_widget.setText(title)

    def _toggle_description(self, visible=None):
        """切换描述区域的显示/隐藏
        
        Args:
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
        """设置描述内容（支持 Markdown 格式）
        
        Args:
            description: Markdown 格式的描述文本
        """
        self.description_content.setText("")

        # 将 Markdown 转换为 HTML
        html = markdown.markdown(description).replace("\n", "")
        
        # 自定义样式
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
