from datetime import datetime

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QTextCharFormat, QTextCursor

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from qfluentwidgets import (
    BodyLabel,
    TextEdit,
    ToolButton,
    ToolTipFilter,
    ToolTipPosition,
    FluentIcon as FIF,
)
from PySide6.QtGui import QFont

from app.common.signal_bus import signalBus


class LogoutputWidget(QWidget):
    """
    日志输出组件
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        # 级别颜色映射
        self._level_color = {
            "INFO": "#eeeeee",
            "WARNING": "#e3b341",
            "ERROR": "#f85149",
            "CRITICAL": "#b62324",
        }
        self._init_log_output()
        self.main_layout = QVBoxLayout(self)
        self.main_layout.addWidget(self.log_output_widget)

        # 连接 MAA Sink 回调信号
        signalBus.callback.connect(self._on_maa_callback)
        signalBus.log_output.connect(self._on_log_output)

    def _init_log_output(self):
        """初始化日志输出区域"""
        self._log_output_title()
        # 日志输出区域
        self.log_output_area = TextEdit()
        self.log_output_area.setReadOnly(True)
        self.log_output_area.setDisabled(True)
        font = QFont("Microsoft YaHei", 11)
        self.log_output_area.setFont(font)

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

        # 日志输出区域标题栏总体布局
        self.log_output_title_layout = QHBoxLayout()
        self.log_output_title_layout.addWidget(self.log_output_title)
        self.log_output_title_layout.addWidget(self.generate_log_zip_button)

        # 交互信号：由组件发射，外部处理
        self.generate_log_zip_button.clicked.connect(signalBus.request_log_zip)

    def clear_log(self):
        self.log_output_area.clear()

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
            action = signal.get("task", "")
            self._handle_controller_signal(status, action)

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
            self.add_structured_log("ERROR", self.tr("Resource loading failed"))

    def _handle_controller_signal(self, status: int, action: str):
        """处理控制器/模拟器连接信号 - 只输出开始和失败"""
        # status: 1=Starting, 2=Succeeded, 3=Failed
        action_text = action if action else self.tr("Connection operation")
        if status == 1:
            self.add_structured_log(
                "INFO", self.tr("Controller started operation: ") + action_text
            )
        elif status == 3:
            self.add_structured_log(
                "ERROR", self.tr("Controller operation failed: ") + action_text
            )

    def _handle_task_signal(self, status: int, task: str):
        """处理任务执行信号 - 只输出开始和失败"""
        # status: 1=Starting, 2=Succeeded, 3=Failed
        task_text = task if task else self.tr("Unknown task")
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
        color = self._level_color.get(upper, "#eeeeee")
        self.append_text_to_log(text, color)

    def _normalize_color(self, color: str) -> str:
        if isinstance(color, QColor):
            return color.name()
        raw = str(color).strip() if color else ""
        if raw and QColor(raw).isValid():
            return raw
        return self._level_color.get("INFO", "#eeeeee")

    def append_text_to_log(self, msg: str, color: str):
        """通用方法：将彩色文本写入日志面板"""
        text = str(msg)
        timestamp = datetime.now().strftime("%H:%M:%S")
        normalized_color = self._normalize_color(color)
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(normalized_color))
        cursor = self.log_output_area.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        lines = text.splitlines() or [""]
        for line in lines:
            cursor.insertText(f"{timestamp} {line}", fmt)
            cursor.insertBlock()
        self.log_output_area.setTextCursor(cursor)
        self.log_output_area.ensureCursorVisible()
