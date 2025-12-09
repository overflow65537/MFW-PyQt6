from datetime import datetime
from html import escape
import re
from venv import logger

from PySide6.QtCore import Qt
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
    ToolButton,
    ToolTipFilter,
    ToolTipPosition,
    FluentIcon as FIF,
    isDarkTheme,
    qconfig,
)

from app.common.signal_bus import signalBus


class LogoutputWidget(QWidget):
    """
    日志输出组件
    """

    def __init__(self, parent=None):
        super().__init__(parent)
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
        self.main_layout.setContentsMargins(0, 12, 0, 18)
        self.main_layout.setSpacing(8)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.main_layout.addLayout(self.log_output_title_layout)
        self.main_layout.addWidget(self.log_output_widget)

        # 连接 MAA Sink 回调信号
        signalBus.callback.connect(self._on_maa_callback)
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
        for label, level, has_custom_color in self._log_entries:
            if has_custom_color:
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
        self.generate_log_zip_button = ToolButton(FIF.FEEDBACK, self)
        self.generate_log_zip_button.setToolTip(self.tr("generate log zip"))
        # 悬浮提示
        self.generate_log_zip_button.installEventFilter(
            ToolTipFilter(self.generate_log_zip_button, 0, ToolTipPosition.TOP)
        )

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
        self.add_structured_log(level, text)

    def _on_maa_callback(self, signal: dict):
        """处理 MAA Sink 发送的回调信号"""
        if not isinstance(signal, dict):
            return

        signal_name = signal.get("name", "")
        status = signal.get("status", 0)  # 1=Starting, 2=Succeeded, 3=Failed
        if signal_name == "speed_test":
            latency_ms = int(signal.get("details", 0) * 1000)
            level = self._latency_level(latency_ms)
            message = self.tr("screenshot test success, time: ") + f"{latency_ms}ms"
            self.add_structured_log(level, message)
            return

        # 根据不同的信号类型处理
        if signal_name == "resource":
            # 资源加载状态
            self._handle_resource_signal(status)

        elif signal_name == "controller":
            # 控制器/模拟器连接状态
            self._handle_controller_signal(status)

        elif signal_name == "task":
            # 任务执行状态
            task = signal.get("task", "")
            self._handle_task_signal(status, task)

        elif signal_name == "context":
            # 上下文信息原样输出
            details = signal.get("details", "")
            if details:
                self.add_structured_log("INFO", details)

    def _handle_resource_signal(self, status: int):
        """处理资源加载信号 - 只输出失败"""
        # status: 1=Starting, 2=Succeeded, 3=Failed
        if status == 3:
            self.add_structured_log("ERROR", self.tr("Resource Loading Failed"))

    def _handle_controller_signal(self, status: int):
        """处理控制器/模拟器连接信号 - 只输出开始和失败"""
        # status: 1=Starting, 2=Succeeded, 3=Failed
        if status == 1:
            self.add_structured_log("INFO", self.tr("Controller Started Connect"))
        elif status == 3:
            self.add_structured_log("ERROR", self.tr("Controller Connect Failed"))

    def _handle_task_signal(self, status: int, task: str):
        """处理任务执行信号 - 只输出开始和失败"""
        # status: 1=Starting, 2=Succeeded, 3=Failed
        task_text = task if task else self.tr("Unknown Task")
        if task_text == "MaaNS::Tasker::post_stop":
            return
        elif status == 1:
            self.add_structured_log(
                "INFO", self.tr("Task started execution: ") + task_text
            )
        elif status == 3:
            self.add_structured_log(
                "ERROR", self.tr("Task execution failed: ") + task_text
            )

    def _latency_level(self, latency_ms: int) -> str:
        if latency_ms <= 30:
            return "INFO"
        elif latency_ms <= 100:
            return "WARNING"
        elif latency_ms <= 200:
            return "ERROR"
        return "CRITICAL"

    def add_structured_log(self, level: str, text: str):
        # 规范化级别
        upper = (level or "INFO").upper()
        if upper not in self._level_color:
            upper = "INFO"
        self.append_text_to_log(text, upper)
        logger.info(f"[{level}] {text}")

    def append_text_to_log(self, msg: str, level: str):
        """将日志内容追加到滚动区域"""
        raw_text = str(msg)
        timestamp = datetime.now().strftime("%H:%M:%S")
        lines = raw_text.splitlines() or [""]
        for line in lines:
            self._add_log_row(timestamp, line, level)

    def _add_log_row(self, timestamp: str, text: str, level: str):
        """新增一行日志（左时间，右内容）"""
        formatted_text, has_custom_color = self._format_colored_text(text)
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
        content_label.setTextFormat(
            Qt.TextFormat.RichText if has_custom_color else Qt.TextFormat.PlainText
        )
        content_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        content_label.setWordWrap(True)
        content_policy = content_label.sizePolicy()
        content_policy.setHorizontalPolicy(QSizePolicy.Policy.Expanding)
        content_policy.setVerticalPolicy(QSizePolicy.Policy.Minimum)
        content_policy.setHeightForWidth(True)
        content_label.setSizePolicy(content_policy)
        if has_custom_color:
            # 忽略日志级别颜色，按自定义颜色渲染
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
        self._log_entries.append((content_label, level, has_custom_color))
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
        解析 [color:xxx]...[/color] 结构，生成富文本以支持多色展示
        返回 (富文本字符串, 是否包含自定义颜色)
        """
        pattern = re.compile(r"\[color:([^\]]+)\](.*?)\[/color\]", re.IGNORECASE | re.DOTALL)
        has_custom_color = False
        parts: list[str] = []
        last_index = 0

        for match in pattern.finditer(text):
            has_custom_color = True
            # 处理前置纯文本
            prefix = text[last_index:match.start()]
            if prefix:
                parts.append(escape(prefix))

            color = self._sanitize_color(match.group(1))
            content = escape(match.group(2))
            parts.append(f'<span style="color: {color};">{content}</span>')
            last_index = match.end()

        if not has_custom_color:
            return escape(text), False

        # 追加剩余纯文本
        if last_index < len(text):
            parts.append(escape(text[last_index:]))

        return "".join(parts), True

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
