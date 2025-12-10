import hashlib
import re
import tempfile
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Dict, Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QSplitter, QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget
from qfluentwidgets import BodyLabel, ScrollArea, SimpleCardWidget, SegmentedWidget

from app.utils.logger import logger
from app.utils.markdown_helper import render_markdown
from app.view.task_interface.animations.optionwidget import (
    DescriptionTransitionAnimator,
    OptionTransitionAnimator,
)
from app.view.task_interface.components.ImagePreviewDialog import ImagePreviewDialog
from app.view.task_interface.components.Option_Framework import (
    OptionFormWidget,
    SpeedrunConfigWidget,
)
from app.view.task_interface.components.Option_Widget_Mixin.PostActionSettingMixin import (
    PostActionSettingMixin,
)
from app.view.task_interface.components.Option_Widget_Mixin.ResourceSettingMixin import (
    ResourceSettingMixin,
)
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
        self.speedrun_widget.config_changed.connect(self._on_speedrun_changed)

        # 连接CoreSignalBus的options_loaded信号
        service_coordinator.signal_bus.options_loaded.connect(self._on_options_loaded)
        service_coordinator.signal_bus.config_changed.connect(self._on_config_changed)

    def _init_ui(self):
        """初始化UI"""
        self.main_layout = QVBoxLayout(self)

        self.title_widget = BodyLabel(self.tr("Options"))
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
        self.option_area_widget.enableTransparentBackground()
        # 设置透明无边框
        self.option_area_widget.setStyleSheet(
            "background-color: transparent; border: none;"
        )

        # 创建一个容器widget来承载布局
        option_container = QWidget()
        self.option_area_layout = QVBoxLayout(option_container)  # 将布局关联到容器
        self.option_area_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.option_area_layout.setContentsMargins(10, 10, 10, 10)  # 添加内边距

        # 堆叠页面：0 选项；1 速通规则
        self.option_stack = QStackedWidget()
        self.option_area_layout.addWidget(self.option_stack)

        # 选项页
        self.option_page = QWidget()
        self.option_page_layout = QVBoxLayout(self.option_page)
        self.option_page_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.option_page_layout.setContentsMargins(0, 0, 0, 0)

        # 保存布局引用（某些 Mixin 可能需要）
        self.parent_layout = self.option_page_layout

        # 创建新的选项表单组件
        self.option_form_widget = OptionFormWidget()
        self.option_page_layout.addWidget(self.option_form_widget)

        # 速通配置页
        self.speedrun_widget = SpeedrunConfigWidget()
        speedrun_page = QWidget()
        speedrun_layout = QVBoxLayout(speedrun_page)
        speedrun_layout.setContentsMargins(0, 0, 0, 0)
        speedrun_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        speedrun_layout.addWidget(self.speedrun_widget)
        speedrun_layout.addStretch()

        self.option_stack.addWidget(self.option_page)
        self.option_stack.addWidget(speedrun_page)
        self.option_stack.setCurrentIndex(0)

        # 底部分段切换（不再使用下拉框）
        self.segmented_switcher = SegmentedWidget(self)
        self.segmented_switcher.addItem(routeKey="options", text=self.tr("Options"))
        self.segmented_switcher.addItem(routeKey="speedrun", text=self.tr("Speedrun"))
        self.segmented_switcher.currentItemChanged.connect(self._on_segmented_changed)
        self.option_area_layout.addWidget(self.segmented_switcher, alignment=Qt.AlignmentFlag.AlignBottom)
        self.segmented_switcher.setCurrentItem("options")
        # 初始化时隐藏，待任务加载后按需显示
        self.segmented_switcher.setVisible(False)

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
        self.description_title = BodyLabel(self.tr("Function Description"))
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
        # 启用链接点击交互（用于图片点击）
        self.description_content.setTextInteractionFlags(
            Qt.TextInteractionFlag.LinksAccessibleByMouse
        )
        self.description_content.setOpenExternalLinks(False)  # 不自动打开外部链接
        self.description_content.linkActivated.connect(self._on_link_activated)
        self.description_content.setContextMenuPolicy(
            Qt.ContextMenuPolicy.NoContextMenu
        )
        self.description_content.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.description_layout.addWidget(self.description_content)

        self.description_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # 创建滚动区域来包裹内容
        self.description_scroll_area = ScrollArea()
        self.description_scroll_area.setWidget(self.description_area_widget)
        self.description_scroll_area.setWidgetResizable(True)
        self.description_scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.description_scroll_area.enableTransparentBackground()
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
        self.option_splitter_layout.setContentsMargins(0, 13, 0, 0)

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
            content_widget=self.description_content,  # 传入内容控件用于计算实际高度
            max_ratio=0.5,  # 默认最大比例50%
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

    def _on_segmented_changed(self, key: str) -> None:
        """通过分段控件切换主选项/速通页"""
        if key == "speedrun":
            self.option_stack.setCurrentIndex(1)
        else:
            self.option_stack.setCurrentIndex(0)

    def _set_speedrun_visible(self, visible: bool) -> None:
        """控制速通页显隐（资源/完成后任务隐藏）"""
        self.segmented_switcher.setVisible(visible)
        if not visible:
            # 只显示常规选项页
            self.option_stack.setCurrentIndex(0)
            self.segmented_switcher.setCurrentItem("options")
            self.speedrun_widget.set_config(None, emit=False)

    def _apply_speedrun_config(self) -> None:
        """加载当前任务的速通配置到 UI"""
        option_service = self.service_coordinator.option
        task_service = self.service_coordinator.task
        task_id = getattr(option_service, "current_task_id", None)
        task = task_service.get_task(task_id) if task_id else None
        if not task:
            self.speedrun_widget.set_config(None, emit=False)
            return

        # 特殊任务不显示速通配置
        if getattr(task, "is_special", False):
            self._set_speedrun_visible(False)
            return

        existing_cfg = (
            task.task_option.get("_speedrun_config")
            if isinstance(task.task_option, dict)
            else None
        )
        merged_cfg = task_service.build_speedrun_config(task.name, existing_cfg)

        # 如果缺失或需要修正，持久化到任务
        if not isinstance(task.task_option, dict):
            task.task_option = {}
        if task.task_option.get("_speedrun_config") != merged_cfg:
            task.task_option["_speedrun_config"] = merged_cfg
            task_service.update_task(task)

        try:
            option_service.current_options["_speedrun_config"] = merged_cfg
        except Exception:
            pass

        state = {}
        if isinstance(task.task_option, dict):
            state = task.task_option.get("_speedrun_state", {}) or {}

        self.speedrun_widget.set_config(merged_cfg, emit=False)
        try:
            self.speedrun_widget.set_runtime_state(state, merged_cfg)
        except Exception as exc:
            logger.warning(f"设置速通运行时信息失败: {exc}")

    def _on_speedrun_changed(self, config: Dict[str, Any]) -> None:
        """速通配置修改后立即保存到当前任务"""
        try:
            self.service_coordinator.option.update_option("_speedrun_config", config)
        except Exception as exc:
            logger.error(f"保存速通配置失败: {exc}")

    def set_description(self, description: str, has_options: bool = True):
        """设置描述内容
        
        :param description: 描述内容
        :param has_options: 是否有选项内容，用于确定公告最大占比
                           - True: 最大占比50%
                           - False: 最大占比100%
        """
        # 处理 None 或空字符串
        if not description:
            description = ""
        
        # 如果description为空，隐藏描述区域
        if not description.strip():
            self.description_content.setText("")
            self._toggle_description(visible=False)
            return

        # 计算新的最大比例
        new_max_ratio = 0.5 if has_options else 1.0
        # 获取旧的最大比例来判断是否有变化
        old_max_ratio = self._description_animator.max_ratio
        ratio_changed = abs(new_max_ratio - old_max_ratio) > 0.1
        
        # 设置最大比例：有选项时50%，无选项时100%
        self._description_animator.set_max_ratio(new_max_ratio)

        html = render_markdown(description)
        html = self._process_remote_images(html)
        
        # 检查公告是否已经展开
        was_expanded = self._description_animator.is_expanded()
        
        # 设置内容
        self.description_content.setText(html)
        
        if was_expanded:
            # 如果已经展开，直接平滑过渡到新高度（不收回再展开）
            # 如果比例发生了变化，强制播放动画
            self._description_animator.update_size(force_animation=ratio_changed)
        else:
            # 如果之前是隐藏的，正常展开
            # 如果没有选项（100%），强制从零开始动画，防止瞬间占满
            self._description_animator.expand(force_from_zero=not has_options)

    def _process_remote_images(self, html: str) -> str:
        """下载公告中的网络图片到本地缓存，并替换为本地路径以保证可显示/预览。"""
        if not html:
            return html
        
        urls = set(re.findall(r"https?://[^\s\"'>]+", html))
        if not urls:
            return html
        
        for url in urls:
            local_path = self._cache_remote_image(url)
            if not local_path:
                continue
            local_uri = Path(local_path).as_uri()
            html = html.replace(url, local_uri)
        return html

    def _cache_remote_image(self, url: str) -> str | None:
        """缓存网络图片到临时目录，返回本地路径。失败则返回None。"""
        try:
            parsed = urllib.parse.urlparse(url)
            if parsed.scheme not in ("http", "https"):
                return None
            
            cache_dir = Path(tempfile.gettempdir()) / "mfw_remote_images"
            cache_dir.mkdir(parents=True, exist_ok=True)
            
            ext = Path(parsed.path).suffix
            # 简单兜底，避免过长或缺少后缀
            if not ext or len(ext) > 5:
                ext = ".img"
            
            filename = hashlib.sha1(url.encode("utf-8")).hexdigest() + ext
            file_path = cache_dir / filename
            if file_path.exists():
                return str(file_path)
            
            req = urllib.request.Request(url, headers={"User-Agent": "MFW-PyQt6"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = resp.read()
            file_path.write_bytes(data)
            return str(file_path)
        except Exception as e:
            logger.warning(f"下载网络图片失败: {url}, {e}")
            return None

    
    def _on_link_activated(self, link: str):
        """处理链接点击事件"""
        if link.startswith("image:"):
            # 提取图片路径
            image_path = link[6:]  # 移除 "image:" 前缀
            # 打开图片预览对话框
            dialog = ImagePreviewDialog(image_path, self)
            dialog.exec()

    # ==================== 公共方法 ====================

    def reset(self):
        """重置选项区域和描述区域"""
        self._clear_options()
        self.description_content.setText("")
        self._toggle_description(visible=False)
        self.segmented_switcher.setCurrentItem("options")
        self.segmented_switcher.setVisible(False)
        self.option_stack.setCurrentIndex(0)
        self.speedrun_widget.set_config(None, emit=False)
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

        # 移除选项页中除 option_form_widget 之外的控件/布局
        items_to_remove = []
        for i in reversed(range(self.option_page_layout.count())):
            item = self.option_page_layout.itemAt(i)
            if not item:
                continue
            if item.widget() == self.option_form_widget:
                continue
            items_to_remove.append(i)

        for i in items_to_remove:
            item = self.option_page_layout.takeAt(i)
            if not item:
                continue
            if item.widget():
                widget = item.widget()
                widget.hide()
                widget.setParent(None)
                widget.deleteLater()
            elif item.layout():
                layout = item.layout()
                while layout and layout.count() > 0:
                    child_item = layout.takeAt(0)
                    if child_item and child_item.widget():
                        child_widget = child_item.widget()
                        child_widget.hide()
                        child_widget.setParent(None)
                        child_widget.deleteLater()
                if layout:
                    layout.deleteLater()

        # 强制更新布局和几何结构
        self.option_page_layout.update()
        self.updateGeometry()

    def update_form_from_structure(self, form_structure, config=None):
        """
        直接从表单结构更新表单
        :param form_structure: 表单结构定义
        :param config: 可选的配置对象，用于设置表单的当前选择
        """
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
        
        # 处理表单结构中的描述字段（传入是否有选项的信息）
        description = None
        if isinstance(form_structure, dict) and "description" in form_structure:
            description = form_structure["description"]
        
        # 如果有有效选项，构建表单；否则清空
        if has_valid_options:
            self.option_splitter_widget.show()
            self._option_animator.play(
                lambda: self._apply_form_structure_with_animation(
                    form_structure_copy, config
                )
            )
        else:
            # 没有有效选项，使用动画清空选项区域
            self._option_animator.play(
                lambda: self._clear_options()
            )
            # 保持选项区域可见
            self.option_splitter_widget.show()
        
        # 设置描述内容（set_description会处理显示/隐藏和动画过渡）
        # 放在最后确保选项区域已经正确设置可见性
        self.set_description(description or "", has_options=has_valid_options)

    def _apply_form_structure_with_animation(self, form_structure, config):
        """异步更新选项表单并连接信号（用于动画回调）。"""
        # 先清空旧选项
        self._clear_options()
        # 构建新选项
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

        # 只使用form_structure更新表单
        if form_structure:
            self.current_config = self.service_coordinator.option.get_options()

            # 记录日志
            logger.info(f"选项加载完成，共 {len(self.current_config)} 个选项")

            # 判断是否为资源类型的配置
            form_type = form_structure.get("type")
            is_resource = form_type == "resource"
            is_post_action = form_type == "post_action"

            if is_resource:
                # 前置配置 - 使用动画过渡
                self._option_animator.play(
                    lambda: self._apply_resource_settings_with_animation()
                )
                # 资源类型没有公告，隐藏公告区域
                self.set_description("", has_options=True)

            elif is_post_action:
                # 完成后操作 - 使用动画过渡
                self._option_animator.play(
                    lambda: self._apply_post_action_settings_with_animation()
                )
                # 完成后操作类型没有公告，隐藏公告区域
                self.set_description("", has_options=True)

            else:
                # 正常的表单更新逻辑（update_form_from_structure会处理公告）
                self.update_form_from_structure(form_structure, self.current_config)
        else:
            # 没有表单时清除界面
            self.reset()
            logger.info("没有提供form_structure，已清除界面")

        # 同步速通配置到堆叠页（资源/完成后/特殊任务隐藏速通页）
        option_service = self.service_coordinator.option
        task_service = self.service_coordinator.task
        task_id = getattr(option_service, "current_task_id", None)
        task = task_service.get_task(task_id) if task_id else None
        is_special_task = getattr(task, "is_special", False) if task else False
        
        speedrun_visible = not (
            form_structure and form_structure.get("type") in ["resource", "post_action"]
        ) and not is_special_task

        if not speedrun_visible:
            # 资源/完成后/特殊任务：隐藏分段与速通
            self._set_speedrun_visible(False)
            self.segmented_switcher.setVisible(False)
            self.option_stack.setCurrentIndex(0)
            self.segmented_switcher.setCurrentItem("options")
            return

        # 普通任务：根据是否有选项决定是否显示分段控件
        has_valid_options = False
        if isinstance(form_structure, dict):
            for k, v in form_structure.items():
                if k == "description":
                    continue
                if isinstance(v, dict) and ("type" in v):
                    has_valid_options = True
                    break

        if has_valid_options:
            # 有选项：显示分段，默认落在选项页
            self.segmented_switcher.setVisible(True)
            self._set_speedrun_visible(True)
            self._apply_speedrun_config()
            self.option_stack.setCurrentIndex(0)
            self.segmented_switcher.setCurrentItem("options")
        else:
            # 无选项：隐藏分段，直接展示速通配置
            self.segmented_switcher.setVisible(False)
            self.option_stack.setCurrentIndex(1)
            self._apply_speedrun_config()
            self.segmented_switcher.setCurrentItem("speedrun")

    def _apply_resource_settings_with_animation(self):
        """在动画回调中应用资源设置"""
        self._clear_options()
        self.create_resource_settings()
        logger.info("资源设置表单已创建")

    def _apply_post_action_settings_with_animation(self):
        """在动画回调中应用完成后操作设置"""
        self._clear_options()
        self.create_post_action_setting()
        logger.info("完成后操作设置表单已创建")

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
