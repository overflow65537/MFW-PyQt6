from datetime import datetime
from html import escape
import re
from pathlib import Path

from PySide6.QtCore import Qt, QSize, QTimer, QByteArray, QBuffer, QIODevice
from PySide6.QtGui import QFont, QPalette, QImage, QIcon
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QSizePolicy,
    QSpacerItem,
    QWidget,
    QVBoxLayout,
)
from PySide6.QtWidgets import QApplication
from qfluentwidgets import (
    BodyLabel,
    ScrollArea,
    SimpleCardWidget,
    PushButton,
    FluentIcon as FIF,
    isDarkTheme,
    qconfig,
)

from app.common.signal_bus import signalBus
from app.utils.logger import logger
from app.core.core import ServiceCoordinator
from app.view.task_interface.components.MonitorWidget import MonitorWidget
from app.utils.markdown_helper import render_markdown
from app.view.task_interface.components.LogItemWidget import LogItemWidget, LogItemData


class LogoutputWidget(QWidget):
    """
    日志输出组件
    """

    def __init__(
        self, service_coordinator: ServiceCoordinator | None = None, parent=None
    ):
        super().__init__(parent)
        self.service_coordinator = service_coordinator
        self._max_log_entries = 500
        # 缩略图预览框（自动保持比例：16:9 或 9:16）
        self._thumb_box = QSize(72, 72)
        # 图片压缩：目标小于50KB，图像细节不重要
        self._thumb_jpg_quality = 60  # 降低质量以减小文件大小
        self._target_max_size_kb = 50  # 目标最大50KB
        self._min_resolution = (640, 360)  # 降低到360P（640x360）以减小文件大小
        # 图片去重：与上一张相似度 >= 阈值则复用上一张，不新增存储
        self._image_similarity_threshold = 0.99
        self._last_image_bytes: QByteArray | None = None
        self._last_image_small_gray = None  # numpy.ndarray(uint8) | None
        self._placeholder_icon: QIcon = self._load_placeholder_icon()
        # 级别颜色映射（随主题自动更新）
        self._level_color: dict[str, str] = {}
        self._log_items: list[LogItemWidget] = []
        self._tail_spacer_item: QSpacerItem | None = None
        self._init_log_output()
        self._add_tail_spacer()
        self._apply_theme_colors()
        qconfig.themeChanged.connect(self._apply_theme_colors)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 8, 0, 20)
        self.main_layout.setSpacing(8)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # 添加监控组件（如果有 service_coordinator）
        if self.service_coordinator:
            # 监控标题栏
            monitor_title_layout = QHBoxLayout()
            monitor_title_layout.setContentsMargins(0, 22, 0, 0)  # 上部避让12px
            monitor_title_layout.setSpacing(8)

            self.monitor_title_label = BodyLabel(self.tr("Monitor"))
            self.monitor_title_label.setStyleSheet("font-size: 20px;")
            monitor_title_layout.addWidget(self.monitor_title_label)

            self.main_layout.addLayout(monitor_title_layout)

            # 创建监控卡片外壳（和日志组件一样的外壳包裹）
            # 16:9比例，宽度344px，高度 = 344 * 9 / 16 = 194px
            self._monitor_width = 344
            self._monitor_height = 194

            self.monitor_card = SimpleCardWidget()
            self.monitor_card.setClickEnabled(False)
            self.monitor_card.setBorderRadius(8)
            # 设置监控卡片为固定大小（344x194，16:9比例，与监控组件内部尺寸一致）
            self.monitor_card.setFixedSize(self._monitor_width, self._monitor_height)
            # 设置大小策略为固定，不影响其他组件
            monitor_card_policy = QSizePolicy(
                QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed
            )
            self.monitor_card.setSizePolicy(monitor_card_policy)

            # 创建监控组件
            self.monitor_widget = MonitorWidget(self.service_coordinator, self)

            # 将监控组件添加到卡片中
            monitor_card_layout = QVBoxLayout(self.monitor_card)
            monitor_card_layout.setContentsMargins(0, 0, 0, 0)
            monitor_card_layout.addWidget(self.monitor_widget)
            # 卡片内容居中对齐
            monitor_card_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            # 监控组件使用固定尺寸，不使用拉伸因子
            self.main_layout.addWidget(self.monitor_card, 0)

        self.main_layout.addLayout(self.log_output_title_layout)
        # 日志区域占据较少空间（拉伸因子为 1）
        self.main_layout.addWidget(self.log_output_widget, 1)

        # 连接日志输出信号
        signalBus.log_output.connect(self._on_log_output)

        signalBus.log_clear_requested.connect(self.clear_log)
        signalBus.log_zip_started.connect(
            lambda: self.generate_log_zip_button.setEnabled(False)
        )
        signalBus.log_zip_finished.connect(
            lambda: self.generate_log_zip_button.setEnabled(True)
        )

    def _apply_theme_colors(self, *_):
        """根据当前主题调整日志文本颜色"""
        base_text_color = self._resolve_base_text_color()
        if isDarkTheme():
            self._level_color = {
                "INFO": base_text_color,
                "WARNING": "#e3b341",
                "ERROR": "#ff4b42",
                "CRITICAL": "#b63923",
            }
        else:
            self._level_color = {
                "INFO": base_text_color,
                "WARNING": "#a05a00",
                "ERROR": "#c62828",
                "CRITICAL": "#8b1f16",
            }
        self._refresh_log_colors()

    def _refresh_log_colors(self):
        """主题变化时刷新已有日志颜色"""
        base_color = self._resolve_base_text_color()
        for item in self._log_items:
            level = item.level
            color = self._level_color.get(
                level, self._level_color.get("INFO", base_color)
            )
            item.apply_theme(base_text_color=base_color, level_color=color)

    def _resolve_base_text_color(self) -> str:
        """获取当前可读的基础文本颜色，亮色主题下避免纯白"""
        # 优先使用日志容器的调色板，如果不存在则退回自身调色板
        palette = (
            self.log_container.palette()
            if hasattr(self, "log_container")
            else self.palette()
        )
        color = palette.color(QPalette.ColorRole.WindowText)
        # 当亮度过高时（接近白色），在浅色主题下使用较深的默认色
        if not isDarkTheme() and color.lightness() > 220:
            return "#202020"
        return color.name()

    def _init_log_output(self):
        """初始化日志输出区域"""
        self._log_output_title()
        self.log_scroll_area = ScrollArea()
        self.log_scroll_area.setWidgetResizable(True)
        self.log_scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.log_scroll_area.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.log_scroll_area.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        self.log_scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.log_scroll_area.setStyleSheet("background: transparent; border: none;")
        self.log_scroll_area.viewport().setStyleSheet(
            "background: transparent; border: none;"
        )

        # 容器：纵向列表布局（每条日志是一个独立控件）
        self.log_container = QWidget()
        self.log_list_layout = QVBoxLayout(self.log_container)
        self.log_list_layout.setContentsMargins(0, 0, 0, 0)
        self.log_list_layout.setSpacing(10)
        self.log_list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        font = QFont("Microsoft YaHei", 11)
        self.log_container.setFont(font)
        self.log_scroll_area.setWidget(self.log_container)

        # 日志卡片
        self.log_output_widget = SimpleCardWidget()
        self.log_output_widget.setClickEnabled(False)
        self.log_output_widget.setBorderRadius(8)

        # 卡片内容布局（含标题与滚动区域）
        content_widget = QWidget()
        self.log_output_layout = QVBoxLayout(content_widget)
        self.log_output_layout.setContentsMargins(10, 10, 10, 10)
        self.log_output_layout.setSpacing(8)
        self.log_output_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.log_output_layout.addWidget(self.log_scroll_area)

        card_layout = QVBoxLayout(self.log_output_widget)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.addWidget(content_widget)

    def _log_output_title(self):
        """初始化日志输出标题"""

        # 日志输出标题
        self.log_output_title = BodyLabel("日志输出")

        # 设置字体大小
        self.log_output_title.setStyleSheet("font-size: 20px;")

        # 生成日志压缩包按钮
        self.generate_log_zip_button = PushButton(self.tr("generate log zip"), self)
        self.generate_log_zip_button.setIcon(FIF.FEEDBACK)
        self.generate_log_zip_button.setIconSize(QSize(18, 18))

        # 日志输出区域标题栏总体布局
        self.log_output_title_layout = QHBoxLayout()
        self.log_output_title_layout.addWidget(self.log_output_title)
        self.log_output_title_layout.addWidget(self.generate_log_zip_button)

        # 交互信号：由组件发射，外部处理
        self.generate_log_zip_button.clicked.connect(signalBus.request_log_zip)

    def clear_log(self):
        """清空日志内容"""
        self._remove_tail_spacer()
        while self.log_list_layout.count():
            item = self.log_list_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        self._log_items.clear()
        # 清理“上一张图片”缓存，避免跨 session 复用旧图
        self._last_image_bytes = None
        self._last_image_small_gray = None
        self._add_tail_spacer()

    def _on_log_output(self, level: str, text: str):
        """处理日志输出信号"""
        self.add_structured_log(level, text)

    def add_structured_log(self, level: str, text: str):
        # 规范化级别
        upper = (level or "INFO").upper()
        if upper not in self._level_color:
            upper = "INFO"
        self.append_text_to_log(text, upper)
        logger.info(f"[{level}] {text}")

    def _has_rich_content_quick_check(self, text: str) -> bool:
        """快速检测文本是否包含富文本内容（Markdown/HTML/颜色标记）"""
        # 检测颜色标记
        if re.search(r"\[color:[^\]]+\].*?\[/color\]", text, re.IGNORECASE | re.DOTALL):
            return True

        # 检测 HTML 标签
        if re.search(
            r"<[a-zA-Z][^>]*(?:/>|>[^<]*</[a-zA-Z]+>|>)",
            text,
            re.DOTALL | re.IGNORECASE,
        ):
            return True

        # 检测 Markdown 语法
        md_patterns = [
            r"#{1,6}\s",  # 标题
            r"\*\*[^*]+\*\*",  # 粗体
            r"(?<!\*)\*(?!\*)[^*]+\*(?!\*)",  # 斜体
            r"`[^`]+`",  # 行内代码
            r"```",  # 代码块
            r"\[[^\]]+\]\([^\)]+\)",  # 链接
            r"^\s*[-*+]\s+",  # 无序列表
            r"^\s*\d+\.\s+",  # 有序列表
            r"\|.*\|",  # 表格
            r"^\s*>\s+",  # 引用
        ]
        return any(re.search(pattern, text, re.MULTILINE) for pattern in md_patterns)

    def append_text_to_log(self, msg: str, level: str):
        """将日志内容追加到滚动区域"""
        raw_text = str(msg)
        timestamp = datetime.now().strftime("%H:%M:%S")

        # 将整个文本作为一条日志处理，这样可以：
        # 1. 保持表格、代码块等Markdown结构的完整性
        # 2. 正确处理换行符（在同一个日志条目内换行显示）
        self._add_log_row(timestamp, raw_text, level)

    def _add_log_row(self, timestamp: str, text: str, level: str):
        """新增一条日志（LogItemWidget）"""
        formatted_text, has_rich_content = self._format_colored_text(text)
        self._remove_tail_spacer()

        # 任务名：使用 TaskFlowRunner 当前任务映射（可靠，不依赖翻译后的文本）
        task_name = self._get_current_task_name()

        # System 任务：不捕获图片，使用图标 icon，不占用 500 张配额
        # 其他任务：正常捕获图片
        if task_name == self.tr("System"):
            image_bytes = None
        else:
            # 日志出现时抓取一帧作为预览（优先 cached_image；None 则不显示）
            image_bytes = self._try_capture_cached_image_bytes()
            if image_bytes is not None and image_bytes.isEmpty():
                image_bytes = None

        data = LogItemData(
            level=level,
            task_name=task_name,
            message=formatted_text,
            has_rich_content=has_rich_content,
            timestamp=timestamp,
            image_bytes=image_bytes,
        )

        item = LogItemWidget(
            data,
            thumb_box=self._thumb_box,
            placeholder_icon=self._placeholder_icon,
            parent=self.log_container,
        )
        self._log_items.append(item)
        self.log_list_layout.addWidget(item, 0)

        # 上限淘汰：删除最旧条目
        if len(self._log_items) > self._max_log_entries:
            oldest = self._log_items.pop(0)
            self.log_list_layout.removeWidget(oldest)
            oldest.deleteLater()

        self._add_tail_spacer()
        self._refresh_log_colors()
        self._scroll_to_bottom()

    def _sanitize_color(self, raw: str) -> str:
        """过滤颜色字符串，防止注入并保留常见格式"""
        color = (raw or "").strip()
        if re.fullmatch(r"[#a-zA-Z0-9(),.%/\s-]{1,64}", color):
            return color
        return self._resolve_base_text_color()

    def _format_colored_text(self, text: str) -> tuple[str, bool]:
        """
        解析文本内容，支持 Markdown、HTML 和 [color:xxx]...[/color] 结构
        返回 (富文本字符串, 是否包含富文本内容)
        """
        # 检测是否包含颜色标记
        color_pattern = re.compile(
            r"\[color:([^\]]+)\](.*?)\[/color\]", re.IGNORECASE | re.DOTALL
        )
        has_color_markup = bool(color_pattern.search(text))

        # 快速检测是否可能包含 Markdown 或 HTML 内容
        # 检查 HTML 标签（包括自闭合标签如 <br>, <hr> 和成对标签）
        html_tag_pattern = re.compile(
            r"<[a-zA-Z][^>]*(?:/>|>[^<]*</[a-zA-Z]+>|>)", re.DOTALL | re.IGNORECASE
        )
        has_html = bool(html_tag_pattern.search(text))

        # 检查常见的 Markdown 语法特征
        md_indicators = [
            r"#{1,6}\s",  # 标题
            r"\*\*[^*]+\*\*",  # 粗体
            r"(?<!\*)\*(?!\*)[^*]+\*(?!\*)",  # 斜体（避免与粗体冲突）
            r"`[^`]+`",  # 行内代码
            r"```",  # 代码块标记
            r"\[[^\]]+\]\([^\)]+\)",  # 链接
            r"^\s*[-*+]\s+",  # 无序列表（必须以行首开始）
            r"^\s*\d+\.\s+",  # 有序列表（必须以行首开始）
            r"^\s*>\s+",  # 引用
        ]
        # 使用MULTILINE模式，使^能够匹配每行的开始
        has_markdown = any(
            re.search(pattern, text, re.MULTILINE) for pattern in md_indicators
        )

        # 表格检测：需要包含至少两列（至少两个|）和分隔行
        # 表格模式：包含|的行，且后面跟着包含-或=的分隔行
        table_pattern = re.compile(
            r"\|[^\|]+\|[^\|]+.*\n.*\|[\s\-\=:]+\|", re.MULTILINE
        )
        if table_pattern.search(text):
            has_markdown = True

        has_rich_content = has_color_markup or has_markdown or has_html

        # 处理颜色标记：先提取颜色标记，对标记内的内容分别处理
        if has_color_markup:
            parts: list[str] = []
            last_index = 0

            for match in color_pattern.finditer(text):
                # 处理前置文本（可能包含 Markdown/HTML）
                prefix = text[last_index : match.start()]
                if prefix:
                    prefix_html = render_markdown(prefix)
                    parts.append(prefix_html)

                # 处理颜色标记内的内容（可能包含 Markdown/HTML）
                color = self._sanitize_color(match.group(1))
                content = match.group(2)
                content_html = render_markdown(content)
                # 在渲染后的 HTML 上应用颜色样式
                parts.append(f'<span style="color: {color};">{content_html}</span>')
                last_index = match.end()

            # 处理剩余文本
            if last_index < len(text):
                suffix = text[last_index:]
                suffix_html = render_markdown(suffix)
                parts.append(suffix_html)

            result = "".join(parts)
            # 如果渲染后包含 HTML 标签，说明有富文本内容
            has_rich_result = bool(re.search(r"<[a-zA-Z]", result))
            return result, has_rich_result
        elif has_rich_content:
            # 有 Markdown/HTML 但没有颜色标记，直接渲染
            html_content = render_markdown(text)
            # 验证渲染后确实包含HTML标签（确保渲染成功）
            if re.search(r"<[a-zA-Z]", html_content):
                return html_content, True
            else:
                # 如果渲染后没有HTML标签，说明可能是纯文本，回退到纯文本处理
                if "\n" in text:
                    escaped_text = escape(text)
                    escaped_text = escaped_text.replace("\n", "<br>")
                    return escaped_text, True
                else:
                    return escape(text), False
        else:
            # 纯文本：如果有换行符，需要转换为HTML的<br>标签以正确显示
            if "\n" in text:
                escaped_text = escape(text)
                # 将换行符转换为<br>标签
                escaped_text = escaped_text.replace("\n", "<br>")
                return escaped_text, True  # 需要RichText格式来渲染<br>
            else:
                # 纯文本单行，直接返回转义后的内容
                return escape(text), False

    def _scroll_to_bottom(self):
        """自动滚动到底部"""
        v_bar = self.log_scroll_area.verticalScrollBar()
        if v_bar:
            v_bar.setValue(v_bar.maximum())

    def _add_tail_spacer(self):
        """在底部添加占位以吸收剩余空间"""
        if self._tail_spacer_item:
            # 已有则先移除，确保放在最后一行（-1 行）
            self._remove_tail_spacer()
        self._tail_spacer_item = QSpacerItem(
            0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding
        )
        self.log_list_layout.addItem(self._tail_spacer_item)

    def _remove_tail_spacer(self):
        """移除已有的底部占位"""
        if self._tail_spacer_item:
            self.log_list_layout.removeItem(self._tail_spacer_item)
            self._tail_spacer_item = None

    def _get_controller(self):
        """获取控制器：优先使用任务流的控制器。"""
        if not self.service_coordinator:
            return None
        try:
            if hasattr(self.service_coordinator, "run_manager"):
                task_flow = self.service_coordinator.run_manager
                if task_flow and hasattr(task_flow, "maafw"):
                    controller = getattr(task_flow.maafw, "controller", None)
                    if controller is not None:
                        return controller
        except Exception:
            return None
        return None

    def _try_capture_cached_image_bytes(self) -> QByteArray | None:
        """尝试从 controller.cached_image 获取一帧，并压缩为 JPG bytes。"""
        controller = self._get_controller()
        if controller is None:
            logger.debug("[LogImage] No controller available")
            return None
        try:
            cached_attr = getattr(controller, "cached_image", None)
            if cached_attr is None:
                logger.debug("[LogImage] controller has no cached_image attribute")
                return None
            cached = cached_attr() if callable(cached_attr) else cached_attr
            if cached is None:
                logger.debug("[LogImage] cached_image returned None")
                return None
        except Exception as e:
            logger.debug(f"[LogImage] Failed to get cached_image: {e}")
            return None

        # 兼容：cached 期望是 numpy.ndarray（BGR）
        try:
            import numpy as np  # type: ignore

            if not isinstance(cached, np.ndarray):
                logger.debug(f"[LogImage] cached is not numpy array, type: {type(cached)}")
                return None
            if cached.ndim < 2:
                logger.debug(f"[LogImage] cached ndim < 2, ndim: {cached.ndim}")
                return None
            h, w = int(cached.shape[0]), int(cached.shape[1])
            if h <= 0 or w <= 0:
                logger.debug(f"[LogImage] Invalid dimensions: {w}x{h}")
                return None
            logger.debug(f"[LogImage] Got frame: {w}x{h}, ndim={cached.ndim}, dtype={cached.dtype}")

            # 常见情况：HWC, 3 通道 BGR
            if cached.ndim == 3 and cached.shape[2] >= 3:
                # 先做相似度去重：缩小成灰度图比较
                curr_small = self._to_small_gray(cached, size=(64, 64))
                if (
                    curr_small is not None
                    and self._last_image_small_gray is not None
                    and self._last_image_bytes is not None
                ):
                    similarity = self._image_similarity(curr_small, self._last_image_small_gray)
                    logger.info(f"[图片相似度] 当前相似度: {similarity:.2%} (阈值: {self._image_similarity_threshold:.2%})")
                    if similarity >= self._image_similarity_threshold:
                        logger.info(f"[图片相似度] 检测到相同图片（相似度 {similarity:.2%} >= {self._image_similarity_threshold:.2%}），复用上一张图片，不新增存储")
                        return self._last_image_bytes

                bgr = cached[:, :, :3]
                rgb = bgr[..., ::-1]
                # 确保是 uint8，避免 QImage/save 因 dtype 异常导致编码失败
                if rgb.dtype != np.uint8:
                    rgb = np.clip(rgb, 0, 255).astype(np.uint8)
                
                # 智能缩放：如果大于目标分辨率，缩放到目标分辨率（保持比例）
                max_w, max_h = self._min_resolution
                if w > max_w or h > max_h:
                    # 计算缩放比例（保持宽高比）
                    scale_w = max_w / w
                    scale_h = max_h / h
                    scale = min(scale_w, scale_h)  # 取较小的比例，确保不超出边界
                    new_w = int(w * scale)
                    new_h = int(h * scale)
                    # 使用快速缩放（BILINEAR 插值，细节不重要）
                    from PIL import Image
                    pil_img = Image.fromarray(rgb)
                    pil_resized = pil_img.resize((new_w, new_h), Image.Resampling.BILINEAR)
                    rgb = np.array(pil_resized, dtype=np.uint8)
                    w, h = new_w, new_h
                    logger.debug(f"[图片压缩] 原图 {cached.shape[1]}x{cached.shape[0]} 缩放到 {w}x{h} (360P)")
                else:
                    logger.debug(f"[图片压缩] 原图 {w}x{h} 小于 360P，保持原尺寸")
                
                rgb = np.ascontiguousarray(rgb)
                bytes_per_line = 3 * w
                qimg = QImage(
                    rgb.data, w, h, bytes_per_line, QImage.Format.Format_RGB888
                ).copy()
            else:
                # 其他格式不处理（避免误解码）
                return None

            # 使用 QImageWriter 更可靠（避免 QImage.save 的参数顺序/类型问题）
            from PySide6.QtGui import QImageWriter
            
            ba = QByteArray()
            buf = QBuffer(ba)
            buf.open(QIODevice.OpenModeFlag.WriteOnly)
            
            # 尝试压缩，如果文件太大则进一步降低质量
            target_size_bytes = self._target_max_size_kb * 1024
            quality = self._thumb_jpg_quality
            ba = None
            
            for attempt in range(3):  # 最多尝试3次
                ba = QByteArray()
                buf = QBuffer(ba)
                buf.open(QIODevice.OpenModeFlag.WriteOnly)
                
                writer = QImageWriter()
                writer.setDevice(buf)
                writer.setFormat(b"JPG")
                writer.setQuality(quality)
                ok = writer.write(qimg)
                buf.close()
                
                if (not ok) or ba.isEmpty():
                    logger.debug(f"[LogImage] JPG save failed: {writer.errorString()}, trying PNG")
                    # 有些环境缺少 JPG 编码插件，fallback 到 PNG
                    ba = QByteArray()
                    buf = QBuffer(ba)
                    buf.open(QIODevice.OpenModeFlag.WriteOnly)
                    
                    writer = QImageWriter()
                    writer.setDevice(buf)
                    writer.setFormat(b"PNG")
                    ok = writer.write(qimg)
                    buf.close()
                    if (not ok) or ba.isEmpty():
                        logger.warning(f"[LogImage] Both JPG and PNG save failed: {writer.errorString()}")
                        return None
                    logger.debug(f"[LogImage] PNG save succeeded, size: {ba.size()} bytes")
                    break
                
                # 检查文件大小
                if ba.size() <= target_size_bytes:
                    logger.debug(f"[图片压缩] JPG 保存成功，大小: {ba.size()} bytes ({ba.size()/1024:.1f}KB), 质量: {quality}")
                    break
                
                # 文件太大，降低质量重试
                if attempt < 2:  # 还有重试机会
                    quality = max(30, quality - 15)  # 每次降低15，最低30
                    logger.debug(f"[图片压缩] 文件大小 {ba.size()} bytes ({ba.size()/1024:.1f}KB) 超过目标 {target_size_bytes} bytes，降低质量到 {quality} 重试")
                else:
                    logger.debug(f"[图片压缩] JPG 保存成功，大小: {ba.size()} bytes ({ba.size()/1024:.1f}KB), 质量: {quality} (已达到最低质量)")
            
            if ba is None or ba.isEmpty():
                return None

            # 更新“上一张图片”缓存（用于后续去重复用）
            try:
                self._last_image_bytes = ba
                if "curr_small" not in locals() or curr_small is None:
                    curr_small = self._to_small_gray(cached, size=(64, 64))
                self._last_image_small_gray = curr_small
            except Exception:
                pass

            return ba
        except Exception as e:
            logger.exception(f"[LogImage] Exception during image processing: {e}")
            return None

    def _to_small_gray(self, frame_bgr, *, size: tuple[int, int]):
        """将 BGR numpy 图像缩小并转为灰度 uint8，用于相似度比较。"""
        try:
            import numpy as np  # type: ignore

            if frame_bgr is None or not isinstance(frame_bgr, np.ndarray):
                return None
            if frame_bgr.ndim != 3 or frame_bgr.shape[2] < 3:
                return None
            h, w = int(frame_bgr.shape[0]), int(frame_bgr.shape[1])
            th, tw = int(size[0]), int(size[1])
            if h <= 1 or w <= 1 or th <= 0 or tw <= 0:
                return None

            ys = np.linspace(0, h - 1, th).astype(np.int32)
            xs = np.linspace(0, w - 1, tw).astype(np.int32)
            small = frame_bgr[np.ix_(ys, xs)]  # (th, tw, c)
            b = small[..., 0].astype(np.float32)
            g = small[..., 1].astype(np.float32)
            r = small[..., 2].astype(np.float32)
            gray = (0.114 * b + 0.587 * g + 0.299 * r).clip(0, 255).astype(np.uint8)
            return gray
        except Exception:
            return None

    def _image_similarity(self, a_gray, b_gray) -> float:
        """返回 [0,1] 相似度；1 表示完全相同。"""
        try:
            import numpy as np  # type: ignore

            if a_gray is None or b_gray is None:
                return 0.0
            if not isinstance(a_gray, np.ndarray) or not isinstance(b_gray, np.ndarray):
                return 0.0
            if a_gray.shape != b_gray.shape:
                return 0.0
            diff = np.abs(a_gray.astype(np.int16) - b_gray.astype(np.int16)).mean()
            sim = 1.0 - float(diff) / 255.0
            if sim < 0.0:
                return 0.0
            if sim > 1.0:
                return 1.0
            return sim
        except Exception:
            return 0.0

    def _get_current_task_name(self) -> str:
        """获取当前正在执行的任务名（如果无法获取则返回 'System'）。"""
        if not self.service_coordinator:
            return self.tr("System")
        try:
            runner = getattr(self.service_coordinator, "run_manager", None)
            task_id = getattr(runner, "_current_running_task_id", None)
            if not task_id:
                return self.tr("System")
            task_service = getattr(self.service_coordinator, "task", None)
            tasks = task_service.get_tasks() if task_service else []
            for t in tasks or []:
                if getattr(t, "item_id", None) == task_id:
                    return str(getattr(t, "name", "")) or self.tr("System")
        except Exception:
            return self.tr("System")
        return self.tr("System")

    def _load_placeholder_icon(self) -> QIcon:
        """加载日志条目的占位图标：优先 interface.icon，其次应用 window icon。"""
        # 1) interface.icon（相对于 interface 文件目录）
        try:
            if self.service_coordinator:
                iface = getattr(self.service_coordinator, "interface", None) or {}
                icon_rel = iface.get("icon") if isinstance(iface, dict) else None
                if isinstance(icon_rel, str) and icon_rel.strip():
                    base_path = getattr(
                        self.service_coordinator, "_interface_path", None
                    )
                    base_dir = Path(base_path).parent if base_path else Path.cwd()
                    icon_path = Path(icon_rel.strip())
                    if not icon_path.is_absolute():
                        icon_path = (base_dir / icon_path).resolve()
                    if icon_path.exists():
                        ico = QIcon(str(icon_path))
                        if not ico.isNull():
                            return ico
        except Exception:
            pass

        # 2) 应用 window icon
        try:
            app = QApplication.instance()
            if isinstance(app, QApplication):
                ico = app.windowIcon()
                if ico and not ico.isNull():
                    return ico
        except Exception:
            pass

        return QIcon()

    def collect_log_images(self) -> dict[str, tuple[QByteArray, list[int]]]:
        """
        收集所有日志条目中的图片，建立图片到日志索引的映射。
        
        Returns:
            dict: key 为图片的唯一标识（hash），value 为 (image_bytes, [日志索引列表])
        """
        from hashlib import md5
        
        image_map: dict[str, tuple[QByteArray, list[int]]] = {}
        
        for idx, item in enumerate(self._log_items):
            data = getattr(item, "_data", None)
            if not data or not data.image_bytes or data.image_bytes.isEmpty():
                continue
            
            # 使用图片 bytes 的 MD5 作为唯一标识
            raw_bytes = data.image_bytes.data()
            img_hash = md5(raw_bytes).hexdigest()
            
            if img_hash in image_map:
                # 同一张图片，追加日志索引
                image_map[img_hash][1].append(idx)
            else:
                # 新图片，创建映射
                image_map[img_hash] = (data.image_bytes, [idx])
        
        return image_map
