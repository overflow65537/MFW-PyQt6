import re
from pathlib import Path
from typing import Dict, Any

import markdown
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QSplitter,
)

from qfluentwidgets import (
    SimpleCardWidget,
    BodyLabel,
    ScrollArea,
)
from app.view.fast_start.animations.optionwidget import (
    DescriptionTransitionAnimator,
    OptionTransitionAnimator,
)
from app.view.fast_start.components.Option_Widget_Mixin.ResourceSettingMixin import (
    ResourceSettingMixin,
)
from app.view.fast_start.components.Option_Widget_Mixin.PostActionSettingMixin import (
    PostActionSettingMixin,
)
from app.view.fast_start.components.Option_Framework import OptionFormWidget
from app.utils.logger import logger


from ....core.core import ServiceCoordinator


class OptionWidget(QWidget, ResourceSettingMixin, PostActionSettingMixin):
    current_config: Dict[str, Any]
    parent_layout: QVBoxLayout

    def __init__(self, service_coordinator: ServiceCoordinator, parent=None):
        # 先调用QWidget的初始化
        self.service_coordinator = service_coordinator
        QWidget.__init__(self, parent)
        # 调用ResourceSettingMixin的初始化
        ResourceSettingMixin.__init__(self)
        # 调用PostActionSettingMixin的初始化
        PostActionSettingMixin.__init__(self)

        # 初始化UI组件
        self._init_ui()
        self._toggle_description(visible=False, animate=False)

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

        # 保存布局引用（某些 Mixin 可能需要）
        self.parent_layout = self.option_area_layout

        # 创建新的选项表单组件
        self.option_form_widget = OptionFormWidget()
        self.option_area_layout.addWidget(self.option_form_widget)

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
        self.description_content.setTextFormat(Qt.TextFormat.RichText)
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
        self._description_animator = DescriptionTransitionAnimator(
            self.splitter,
            self.description_splitter_widget,
            expanded_ratio=0.4,
            min_height=90,
        )

        # 添加到主布局
        self.main_layout.addWidget(self.title_widget)  # 直接添加标题
        self.main_layout.addWidget(self.splitter)  # 添加分割器
        # 添加主布局间距
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(5)

    # ==================== UI 辅助方法 ==================== #

    def _toggle_description(self, visible: bool|None = None, animate: bool = True) -> None:
        """切换描述区域的显示/隐藏
        visible: True显示，False隐藏，None切换当前状态
        """
        if visible is None:
            # 切换当前状态
            visible = not self._description_animator.is_expanded()

        if visible:
            if animate:
                self._description_animator.expand()
            else:
                self._description_animator.set_visible_immediate(True)
        else:
            if animate:
                self._description_animator.collapse()
            else:
                self._description_animator.set_visible_immediate(False)

    def set_description(self, description: str):
        """设置描述内容"""
        # 处理 None 或空字符串
        if not description:
            description = ""
        self.description_content.setText("")

        # 如果description为空，隐藏描述区域
        if not description.strip():
            self._toggle_description(visible=False)
            return

        html = self._prepare_description_html(description)
        self.description_content.setText(html)

    @staticmethod
    def _prepare_description_html(description: str) -> str:
        """根据传入内容决定是否直接使用 HTML 或将 Markdown 转为 HTML"""
        stripped = description.strip()
        if stripped.startswith("<") and stripped.endswith(">"):
            return description
        return markdown.markdown(
            description, extensions=["extra", "sane_lists"]
        )

    # ==================== 公共方法 ====================

    def reset(self):
        """重置选项区域和描述区域"""
        self._clear_options()
        self._toggle_description(visible=False)
        # 显示选项区域，因为已经专门的方法清除选项
        self.option_splitter_widget.show()

        self.current_task = None
        self.current_config = {}

    def _on_config_changed(self, config_id: str):
        """配置切换时重置选项面板"""
        self.reset()

    def set_title(self, title: str):
        """设置标题"""
        self.title_widget.setText(title)

    def _clear_options(self):
        """清空选项区域"""
        # 清空两个固定UI的字典（资源设置和完成后操作）
        if hasattr(self, 'resource_setting_widgets'):
            self.resource_setting_widgets.clear()
        if hasattr(self, 'post_action_widgets'):
            self.post_action_widgets.clear()
        
        # 使用新框架清空选项
        self.option_form_widget._clear_options()

        # 移除布局中所有不是 option_form_widget 的项（包括控件、间距、子布局等）
        # 从后往前遍历，避免索引变化
        items_to_remove = []
        for i in reversed(range(self.option_area_layout.count())):
            item = self.option_area_layout.itemAt(i)
            if item:
                # 保留 option_form_widget
                if item.widget() == self.option_form_widget:
                    continue
                # 移除其他所有项
                items_to_remove.append(i)

        # 移除所有找到的项
        for i in items_to_remove:
            item = self.option_area_layout.takeAt(i)
            if item:
                if item.widget():
                    widget = item.widget()
                    widget.hide()
                    widget.setParent(None)
                    widget.deleteLater()
                elif item.layout():
                    # 如果有子布局，递归清理
                    layout = item.layout()
                    while layout.count() > 0:
                        child_item = layout.takeAt(0)
                        if child_item.widget():
                            child_widget = child_item.widget()
                            child_widget.hide()
                            child_widget.setParent(None)
                            child_widget.deleteLater()
                    layout.deleteLater()
                # 间距项会被 takeAt 自动清理
        
        # 确保布局只包含 option_form_widget
        while self.option_area_layout.count() > 1:
            item = self.option_area_layout.itemAt(0)
            if item and item.widget() == self.option_form_widget:
                break
            item = self.option_area_layout.takeAt(0)
            if item and item.widget():
                widget = item.widget()
                widget.hide()
                widget.setParent(None)
                widget.deleteLater()
        
        # 强制更新布局和几何结构
        self.option_area_layout.update()
        self.updateGeometry()

    def update_form_from_structure(self, form_structure, config=None):
        """
        直接从表单结构更新表单
        :param form_structure: 表单结构定义
        :param config: 可选的配置对象，用于设置表单的当前选择
        """
        # 处理表单结构中的描述字段
        description = None
        if isinstance(form_structure, dict) and "description" in form_structure:
            description = form_structure["description"]
            self.set_description(description or "")
            if description and description.strip():
                self._toggle_description(visible=True)
            else:
                self._toggle_description(visible=False)
        
        # 构建表单（排除 description 字段）
        form_structure_copy = {
            k: v for k, v in form_structure.items() if k != "description"
        }
        
        # 检查是否有有效的选项项（有 type 字段的字典项）
        has_valid_options = False
        for key, item_config in form_structure_copy.items():
            if isinstance(item_config, dict) and "type" in item_config:
                has_valid_options = True
                break
        
        # 如果有有效选项，构建表单；否则清空
        if has_valid_options:
            self.option_splitter_widget.show()
            self._option_animator.play(
                lambda: self._apply_form_structure_with_animation(
                    form_structure_copy, config
                )
            )
        else:
            # 没有有效选项，清空选项区域
            self.option_form_widget._clear_options()
            # 如果没有描述，可以隐藏整个选项区域（可选）
            if not (description and description.strip()):
                self.option_splitter_widget.hide()

    def _apply_form_structure_with_animation(self, form_structure, config):
        """异步更新选项表单并连接信号（用于动画回调）。"""
        self.option_form_widget.build_from_structure(form_structure, config)
        self._connect_option_signals()
        logger.info("表单已使用 form_structure 完成更新")

    def get_current_form_config(self):
        """
        获取当前表单的配置
        :return: 当前选择的配置字典
        """
        # 使用新的OptionFormWidget框架获取配置
        return self.option_form_widget.get_options()

    def _connect_option_signals(self):
        """
        连接选项变化信号以实现自动保存
        """
        # 遍历所有选项项，连接它们的信号
        for option_item in self.option_form_widget.option_items.values():
            # 连接选项变化信号
            option_item.option_changed.connect(self._on_option_changed)

            # 递归连接子选项的信号
            self._connect_child_option_signals(option_item)

    def _connect_child_option_signals(self, option_item):
        """
        递归连接子选项的信号

        :param option_item: 选项项组件
        """
        for child_widget in option_item.child_options.values():
            child_widget.option_changed.connect(self._on_option_changed)
            # 递归连接子选项的子选项
            self._connect_child_option_signals(child_widget)

    def _on_option_changed(self, key: str, value: Any):
        """
        选项变化时的回调函数，用于自动保存

        :param key: 选项键名
        :param value: 选项值
        """
        try:
            # 获取当前所有配置
            all_config = self.get_current_form_config()
            # 调用OptionService的update_options方法保存选项
            self.service_coordinator.option_service.update_options(all_config)
        except Exception as e:
            # 如果保存失败，记录错误但不影响用户操作
            logger.error(f"自动保存选项失败: {e}")

    def _on_options_loaded(self):
        """
        当选项被加载时触发
        """
        # 先从OptionService获取form_structure
        form_structure = self.service_coordinator.option.get_form_structure()
        
        # 无论什么情况，都先清理所有旧的UI（固定UI、选项和公告）
        # 这样可以确保切换任务时，旧的UI不会残留
        self._clear_options()
        # 清空并隐藏公告
        self.set_description("")  # 这会清空内容并隐藏公告区域

        # 只使用form_structure更新表单
        if form_structure:
            self.current_config = self.service_coordinator.option.get_options()

            # 记录日志
            logger.info(f"选项加载完成，共 {len(self.current_config)} 个选项")

            # 判断是否为资源类型的配置
            if form_structure.get("type") == "resource":
                # 前置配置
                self.create_resource_settings()
                logger.info("资源设置表单已创建")

            elif form_structure.get("type") == "post_action":
                # 完成后操作
                self.create_post_action_setting()
                logger.info("完成后操作设置表单已创建")

            else:
                # 正常的表单更新逻辑
                self.update_form_from_structure(form_structure, self.current_config)
        else:
            # 没有表单时清除界面（已经在上面清理过了，这里只需要重置）
            self.reset()
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
