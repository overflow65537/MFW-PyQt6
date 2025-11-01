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
    BodyLabel,
    ScrollArea,
    SimpleCardWidget,
    StrongBodyLabel,
)
from app.utils.logger import logger
from ._mixin_base import MixinBase


class OptionWidgetBaseMixin(MixinBase):
    """选项面板基础 Mixin
    
    提供选项面板的核心功能：
    - UI 初始化（标题、选项区域）
    - 主入口方法（show_option）
    - 重置方法
    - 描述内容设置（在选项区域末尾显示，Markdown 支持）
    
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
        # type: ignore - Mixin 模式：运行时 self 是 OptionWidget(QWidget) 实例
        self.main_layout = QVBoxLayout(self)  # type: ignore[arg-type]

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

        # 添加标题和选项卡片到主布局
        self.main_layout.addWidget(self.title_widget)
        self.main_layout.addWidget(self.option_area_card)

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
                self._show_resource_setting_option(item)  # type: ignore[attr-defined]
            elif item.item_id.startswith("f_"):
                # 完成后操作基础任务
                self._show_post_task_setting_option(item)  # type: ignore[attr-defined]
            else:
                # 普通任务，使用默认显示
                self._show_task_option(item)  # type: ignore[attr-defined]

    def reset(self):
        """重置选项区域"""
        self._clear_options()
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

    def set_description(self, description: str):
        """在选项区域最后添加描述内容（支持 Markdown 格式）
        
        Args:
            description: Markdown 格式的描述文本
        """
        if not description:
            return
        
        # 添加分隔线和描述标题
        self.option_area_layout.addSpacing(20)  # 添加间距
        
        description_title = StrongBodyLabel()
        description_title.setText(self.tr("Description"))
        self.option_area_layout.addWidget(description_title)
        
        self.option_area_layout.addSpacing(10)  # 标题和内容之间的间距
        
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
        
        # 直接创建描述内容标签
        description_label = BodyLabel()
        description_label.setWordWrap(True)
        description_label.setText(html)
        
        # 添加到选项区域最后
        self.option_area_layout.addWidget(description_label)
