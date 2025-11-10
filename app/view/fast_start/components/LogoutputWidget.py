from PySide6.QtCore import Qt

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from qfluentwidgets import (
    BodyLabel,
    TextEdit,
    ComboBox,
    ToolButton,
    ToolTipFilter,
    ToolTipPosition,
    FluentIcon as FIF,
)

from app.common.signal_bus import signalBus


class LogoutputWidget(QWidget):
    """
    日志输出组件
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        # 内部缓存：[(level, text)]
        self._logs = []
        # 级别顺序与颜色映射
        self._levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        self._level_color = {
            "DEBUG": "#8c8c8c",
            "INFO": "#1f6feb",
            "WARNING": "#e3b341",
            "ERROR": "#f85149",
            "CRITICAL": "#b62324",
        }
        self._init_log_output()
        self.main_layout = QVBoxLayout(self)
        self.main_layout.addWidget(self.log_output_widget)
        self._connect_signals()


    def _init_log_output(self):
        """初始化日志输出区域"""
        self._log_output_title()
        # 日志输出区域
        self.log_output_area = TextEdit()
        self.log_output_area.setReadOnly(True)
        self.log_output_area.setDisabled(True)

        # 日志输出区域总体布局
        self.log_output_widget = QWidget()
        self.log_output_layout = QVBoxLayout(self.log_output_widget)
        self.log_output_layout.setContentsMargins(0, 6, 0, 10)
        self.log_output_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.log_output_layout.addLayout(self.log_output_title_layout)
        self.log_output_layout.addWidget(self.log_output_area)

    def _log_output_title(self):
        """初始化日志输出标题"""

        # 日志输出标题
        self.log_output_title = BodyLabel("日志输出")

        # 设置字体大小
        self.log_output_title.setStyleSheet("font-size: 20px;")

        # 生成日志压缩包按钮
        self.generate_log_zip_button = ToolButton(FIF.FEEDBACK, self)
        # 悬浮提示
        self.generate_log_zip_button.installEventFilter(
            ToolTipFilter(self.generate_log_zip_button, 0, ToolTipPosition.TOP)
        )
        # 日志等级下拉框
        self.log_level_combox = ComboBox(self)
        self.log_level_combox.installEventFilter(
            ToolTipFilter(self.log_level_combox, 0, ToolTipPosition.TOP)
        )
        self.log_level_combox.addItems(
            ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        )
        self.log_level_combox.setFixedWidth(120)

        # 日志输出区域标题栏总体布局
        self.log_output_title_layout = QHBoxLayout()
        self.log_output_title_layout.addWidget(self.log_output_title)
        self.log_output_title_layout.addWidget(self.generate_log_zip_button)
        self.log_output_title_layout.addWidget(self.log_level_combox)

        # 交互信号：由组件发射，外部处理
        self.generate_log_zip_button.clicked.connect(signalBus.request_log_zip)
        # 组件内部变更日志级别时，同步广播到总线
        self.log_level_combox.currentTextChanged.connect(self._on_level_changed)
        self.log_level_combox.currentTextChanged.connect(signalBus.log_level_changed)

    # --- 信号连接与槽 ---
    def _connect_signals(self):
        # 外部→组件：日志文本/等级/清空
        signalBus.log_append.connect(self.append_log)
        signalBus.log_set_text.connect(self.set_log_text)
        signalBus.log_clear.connect(self.clear_log)
        signalBus.log_level_changed.connect(self.set_log_level)
        signalBus.log_entry.connect(self.add_structured_log)

    def append_log(self, text: str):
        if not isinstance(text, str):
            text = str(text)
        # 兼容旧信号：按 INFO 级别处理
        self._logs.append(("INFO", text))
        self._render_logs()

    def set_log_text(self, text: str):
        if not isinstance(text, str):
            text = str(text)
        # 覆盖显示，按 INFO 级别整体处理
        self._logs = [("INFO", line) for line in text.splitlines()]
        self._render_logs()

    def clear_log(self):
        self._logs.clear()
        self.log_output_area.clear()

    def set_log_level(self, level: str):
        # 同步下拉框显示；若传入值不在列表中则忽略
        index = self.log_level_combox.findText(level)
        if index >= 0 and index != self.log_level_combox.currentIndex():
            self.log_level_combox.setCurrentIndex(index)
        # 重渲染（当外部变更等级时）
        self._render_logs()

    def _on_level_changed(self, level: str):
        # 下拉框改变本地阈值时，重渲染
        self._render_logs()

    def add_structured_log(self, level: str, text: str):
        # 规范化级别
        upper = (level or "INFO").upper()
        if upper not in self._levels:
            upper = "INFO"
        self._logs.append((upper, text))
        self._render_logs()

    def _render_logs(self):
        # 计算当前阈值
        current = self.log_level_combox.currentText()
        if current not in self._levels:
            current = "INFO"
        threshold_index = self._levels.index(current)

        # 生成 HTML（用 setHtml 支持颜色/加粗）
        parts = []
        for level, text in self._logs:
            lvl = level.upper() if level else "INFO"
            if lvl not in self._levels:
                lvl = "INFO"
            if self._levels.index(lvl) < threshold_index:
                continue
            color = self._level_color.get(lvl, "#ffffff")
            weight = "600" if lvl in ("WARNING", "ERROR", "CRITICAL") else "400"
            # 对文本进行简单 HTML 转义
            safe_text = (
                text.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
            )
            parts.append(f'<div style="color:{color}; font-weight:{weight}">[{lvl}] {safe_text}</div>')

        html = "\n".join(parts)
        if html:
            self.log_output_area.setHtml(html)
        else:
            self.log_output_area.clear()
