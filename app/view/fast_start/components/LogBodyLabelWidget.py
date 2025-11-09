from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout
from qfluentwidgets import ScrollArea, BodyLabel, ComboBox

from app.common.signal_bus import signalBus


class LogBodyLabelWidget(QWidget):
    """使用 BodyLabel 逐行渲染的日志输出组件

    特性:
    - 结构化日志级别过滤 (DEBUG/INFO/WARNING/ERROR/CRITICAL)
    - 颜色与加粗样式区分级别
    - 与 signalBus 的 log_entry / log_append / log_clear 等信号对接
    - 使用 ScrollArea + 动态添加 BodyLabel 达到自然的排版效果
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        self._level_color = {
            "DEBUG": "#8c8c8c",
            "INFO": "#1f6feb",
            "WARNING": "#e3b341",
            "ERROR": "#f85149",
            "CRITICAL": "#b62324",
        }
        self._logs = []  # [(level, text)]
        self._init_ui()
        self._connect_signals()

    def _init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(6)

        # 级别选择下拉框
        self.level_filter = ComboBox(self)
        self.level_filter.addItems(self._levels)
        self.level_filter.setCurrentText("INFO")  # 默认从 INFO 开始过滤
        self.level_filter.currentTextChanged.connect(self._rerender)
        self.main_layout.addWidget(self.level_filter, 0, Qt.AlignmentFlag.AlignTop)

        # 滚动区域
        self.scroll_area = ScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet("background-color: transparent; border: none;")
        self.main_layout.addWidget(self.scroll_area, 1)

        # 内容容器
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.content_layout.setContentsMargins(4, 4, 4, 4)
        self.content_layout.setSpacing(2)
        self.scroll_area.setWidget(self.content_widget)

        self.content_layout.addStretch()  # 占位伸展，保持顶对齐

    def _connect_signals(self):
        signalBus.log_event.connect(self._on_log_event)
        signalBus.log_clear.connect(self.clear)
        signalBus.log_level_changed.connect(self.set_filter_level)

    # ---- 外部信号槽 ----
    def _on_log_event(self, payload: dict):
        """统一入口：payload = {text, level, color, output, infobar}

        仅当 output=True 时，写入本组件；颜色通过 color 指定（可覆盖默认级别颜色）。
        """
        if not isinstance(payload, dict):
            return
        text = str(payload.get("text", ""))
        level = str(payload.get("level", "INFO")).upper()
        color = payload.get("color")
        output = bool(payload.get("output", True))

        if not output:
            return
        if level not in self._levels:
            level = "INFO"

        # 存储
        self._logs.append((level, text))
        # 渲染（如果可见）
        self._add_label_if_visible(level, text, color)

    def clear(self):
        self._logs.clear()
        # 移除除最后一个 stretch 之外的所有 label
        for i in reversed(range(self.content_layout.count())):
            item = self.content_layout.itemAt(i)
            if item and item.widget() and isinstance(item.widget(), BodyLabel):
                w = item.widget()
                w.setParent(None)
        # 清空后不重新渲染任何行

    def set_filter_level(self, level: str):
        idx = self.level_filter.findText(level)
        if idx >= 0:
            self.level_filter.setCurrentIndex(idx)
        self._rerender()

    # ---- 渲染逻辑 ----
    def _add_label_if_visible(self, level: str, text: str, color_override: str | None = None):
        # 判断是否满足当前过滤阈值
        current = self.level_filter.currentText()
        if current not in self._levels:
            current = "INFO"
        if self._levels.index(level) < self._levels.index(current):
            return  # 不显示

        label = BodyLabel(self._format_line(level, text, color_override), self.content_widget)
        label.setTextFormat(Qt.TextFormat.RichText)
        label.setWordWrap(True)
        self.content_layout.insertWidget(self.content_layout.count() - 1, label)

    def _format_line(self, level: str, text: str, color_override: str | None = None) -> str:
        color = color_override or self._level_color.get(level, "#ffffff")
        weight = "600" if level in ("WARNING", "ERROR", "CRITICAL") else "400"
        # 简单 HTML 转义
        safe = (
            (text or "")
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )
        return f'<span style="color:{color}; font-weight:{weight}">[{level}] {safe}</span>'

    def _rerender(self):
        # 全量重渲染：清空现有可见行再按过滤规则重新添加
        for i in reversed(range(self.content_layout.count())):
            item = self.content_layout.itemAt(i)
            if item and item.widget() and isinstance(item.widget(), BodyLabel):
                item.widget().setParent(None)
        current = self.level_filter.currentText()
        if current not in self._levels:
            current = "INFO"
        threshold = self._levels.index(current)
        for lvl, txt in self._logs:
            if self._levels.index(lvl) >= threshold:
                self._add_label_if_visible(lvl, txt)
