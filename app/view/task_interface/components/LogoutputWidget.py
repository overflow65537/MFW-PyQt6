from datetime import datetime
from html import escape
import re

from PySide6.QtCore import Qt, QSize, QTimer
from PySide6.QtGui import QFont, QPalette
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QSizePolicy,
    QSpacerItem,
    QWidget,
    QVBoxLayout,
)
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


class LogoutputWidget(QWidget):
    """
    日志输出组件
    """

    def __init__(self, service_coordinator: ServiceCoordinator | None = None, parent=None):
        super().__init__(parent)
        self.service_coordinator = service_coordinator
        # 级别颜色映射（随主题自动更新）
        self._level_color: dict[str, str] = {}
        self._log_entries: list[tuple[BodyLabel, str, bool]] = []
        self._log_row_index = 0
        self._tail_spacer_item: QSpacerItem | None = None
        self._tail_spacer_row: int | None = None
        self._init_log_output()
        self._add_tail_spacer()
        self._apply_theme_colors()
        qconfig.themeChanged.connect(self._apply_theme_colors)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 8,0, 20)
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
            monitor_card_policy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            self.monitor_card.setSizePolicy(monitor_card_policy)
            
            # 创建监控组件
            self.monitor_widget = MonitorWidget(
                self.service_coordinator, 
                self
            )
            
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
        fallback = self._level_color.get("INFO", self._resolve_base_text_color())
        base_color = self._resolve_base_text_color()
        for label, level, has_rich_content in self._log_entries:
            if has_rich_content:
                # 富文本内容使用基础颜色（内部可能有自己的颜色设置）
                label.setStyleSheet(f"color: {base_color};")
            else:
                color = self._level_color.get(level, fallback)
                label.setStyleSheet(f"color: {color};")

    def _resolve_base_text_color(self) -> str:
        """获取当前可读的基础文本颜色，亮色主题下避免纯白"""
        # 优先使用日志容器的调色板，如果不存在则退回自身调色板
        palette = self.log_container.palette() if hasattr(self, "log_container") else self.palette()
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
        self.log_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.log_scroll_area.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.log_scroll_area.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        self.log_scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.log_scroll_area.setStyleSheet("background: transparent; border: none;")
        self.log_scroll_area.viewport().setStyleSheet(
            "background: transparent; border: none;"
        )

        # 容器与表格布局（左侧时间，右侧内容）
        self.log_container = QWidget()
        self.log_grid_layout = QGridLayout(self.log_container)
        self.log_grid_layout.setContentsMargins(0, 0, 0, 0)
        self.log_grid_layout.setHorizontalSpacing(12)
        self.log_grid_layout.setVerticalSpacing(6)
        self.log_grid_layout.setColumnStretch(1, 1)
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
        while self.log_grid_layout.count():
            item = self.log_grid_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        self._log_entries.clear()
        self._log_row_index = 0
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
        if re.search(r'<[a-zA-Z][^>]*(?:/>|>[^<]*</[a-zA-Z]+>|>)', text, re.DOTALL | re.IGNORECASE):
            return True
        
        # 检测 Markdown 语法
        md_patterns = [
            r'#{1,6}\s',  # 标题
            r'\*\*[^*]+\*\*',  # 粗体
            r'(?<!\*)\*(?!\*)[^*]+\*(?!\*)',  # 斜体
            r'`[^`]+`',  # 行内代码
            r'```',  # 代码块
            r'\[[^\]]+\]\([^\)]+\)',  # 链接
            r'^\s*[-*+]\s+',  # 无序列表
            r'^\s*\d+\.\s+',  # 有序列表
            r'\|.*\|',  # 表格
            r'^\s*>\s+',  # 引用
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
        """新增一行日志（左时间，右内容）"""
        formatted_text, has_rich_content = self._format_colored_text(text)
        base_color = self._resolve_base_text_color()
        color = self._level_color.get(level, base_color)

        # 保证底部仅一个填充项，防止行被均分
        self._remove_tail_spacer()

        time_label = BodyLabel(timestamp)
        time_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        time_policy = time_label.sizePolicy()
        time_policy.setHorizontalPolicy(QSizePolicy.Policy.Minimum)
        time_policy.setVerticalPolicy(QSizePolicy.Policy.Minimum)
        time_label.setSizePolicy(time_policy)

        content_label = BodyLabel(formatted_text)
        # 如果有富文本内容（Markdown、HTML 或颜色标记），使用 RichText 格式
        content_label.setTextFormat(
            Qt.TextFormat.RichText if has_rich_content else Qt.TextFormat.PlainText
        )
        content_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        content_label.setWordWrap(True)
        content_policy = content_label.sizePolicy()
        content_policy.setHorizontalPolicy(QSizePolicy.Policy.Expanding)
        content_policy.setVerticalPolicy(QSizePolicy.Policy.Minimum)
        content_policy.setHeightForWidth(True)
        content_label.setSizePolicy(content_policy)
        if has_rich_content:
            # 对于富文本内容，使用基础颜色（富文本内部可能有自己的颜色设置）
            content_label.setStyleSheet(f"color: {base_color};")
        else:
            content_label.setStyleSheet(f"color: {color};")

        self.log_grid_layout.addWidget(
            time_label,
            self._log_row_index,
            0,
            alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft,
        )
        self.log_grid_layout.addWidget(
            content_label,
            self._log_row_index,
            1,
            alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft,
        )
        self._log_entries.append((content_label, level, has_rich_content))
        self._log_row_index += 1
        self._add_tail_spacer()
        self._sync_row_heights()
        self._scroll_to_bottom()

    def resizeEvent(self, event):
        """在尺寸变化时重新计算每行高度，避免文本被截断"""
        super().resizeEvent(event)
        self._sync_row_heights()

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
        color_pattern = re.compile(r"\[color:([^\]]+)\](.*?)\[/color\]", re.IGNORECASE | re.DOTALL)
        has_color_markup = bool(color_pattern.search(text))
        
        # 快速检测是否可能包含 Markdown 或 HTML 内容
        # 检查 HTML 标签（包括自闭合标签如 <br>, <hr> 和成对标签）
        html_tag_pattern = re.compile(r'<[a-zA-Z][^>]*(?:/>|>[^<]*</[a-zA-Z]+>|>)', re.DOTALL | re.IGNORECASE)
        has_html = bool(html_tag_pattern.search(text))
        
        # 检查常见的 Markdown 语法特征
        md_indicators = [
            r'#{1,6}\s',  # 标题
            r'\*\*[^*]+\*\*',  # 粗体
            r'(?<!\*)\*(?!\*)[^*]+\*(?!\*)',  # 斜体（避免与粗体冲突）
            r'`[^`]+`',  # 行内代码
            r'```',  # 代码块标记
            r'\[[^\]]+\]\([^\)]+\)',  # 链接
            r'^\s*[-*+]\s+',  # 无序列表（必须以行首开始）
            r'^\s*\d+\.\s+',  # 有序列表（必须以行首开始）
            r'^\s*>\s+',  # 引用
        ]
        # 使用MULTILINE模式，使^能够匹配每行的开始
        has_markdown = any(re.search(pattern, text, re.MULTILINE) for pattern in md_indicators)
        
        # 表格检测：需要包含至少两列（至少两个|）和分隔行
        # 表格模式：包含|的行，且后面跟着包含-或=的分隔行
        table_pattern = re.compile(
            r'\|[^\|]+\|[^\|]+.*\n.*\|[\s\-\=:]+\|', 
            re.MULTILINE
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
                prefix = text[last_index:match.start()]
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
            has_rich_result = bool(re.search(r'<[a-zA-Z]', result))
            return result, has_rich_result
        elif has_rich_content:
            # 有 Markdown/HTML 但没有颜色标记，直接渲染
            html_content = render_markdown(text)
            # 验证渲染后确实包含HTML标签（确保渲染成功）
            if re.search(r'<[a-zA-Z]', html_content):
                return html_content, True
            else:
                # 如果渲染后没有HTML标签，说明可能是纯文本，回退到纯文本处理
                if '\n' in text:
                    escaped_text = escape(text)
                    escaped_text = escaped_text.replace('\n', '<br>')
                    return escaped_text, True
                else:
                    return escape(text), False
        else:
            # 纯文本：如果有换行符，需要转换为HTML的<br>标签以正确显示
            if '\n' in text:
                escaped_text = escape(text)
                # 将换行符转换为<br>标签
                escaped_text = escaped_text.replace('\n', '<br>')
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
        self._tail_spacer_row = self._log_row_index
        self._tail_spacer_item = QSpacerItem(
            0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding
        )
        # 跨两列，确保填充在网格底部
        self.log_grid_layout.addItem(self._tail_spacer_item, self._tail_spacer_row, 0, 1, 2)
        self.log_grid_layout.setRowStretch(self._tail_spacer_row, 1)

    def _remove_tail_spacer(self):
        """移除已有的底部占位"""
        if self._tail_spacer_item:
            if self._tail_spacer_row is not None:
                # 清理旧行拉伸，避免上方日志被平均分散
                self.log_grid_layout.setRowStretch(self._tail_spacer_row, 0)
            self.log_grid_layout.removeItem(self._tail_spacer_item)
            self._tail_spacer_item = None
            self._tail_spacer_row = None

    def _sync_row_heights(self):
        """根据可用宽度调整每行内容标签的最小高度，防止换行被裁剪"""
        viewport_width = self.log_scroll_area.viewport().width()
        spacing = self.log_grid_layout.horizontalSpacing()
        if viewport_width <= 0:
            return

        for row in range(self._log_row_index):
            content_item = self.log_grid_layout.itemAtPosition(row, 1)
            time_item = self.log_grid_layout.itemAtPosition(row, 0)
            content_label = content_item.widget() if content_item else None
            time_label = time_item.widget() if time_item else None
            if not content_label:
                continue

            available_width = viewport_width - spacing
            if time_label:
                available_width -= time_label.sizeHint().width()
            if available_width <= 0:
                continue

            # 强制内容列占满可用宽度，避免被压缩后文字被裁剪
            if content_label.minimumWidth() != available_width:
                content_label.setMinimumWidth(available_width)

            if content_label.hasHeightForWidth():
                required_height = content_label.heightForWidth(available_width)
            else:
                required_height = content_label.sizeHint().height()

            if content_label.minimumHeight() != required_height:
                content_label.setMinimumHeight(required_height)
    