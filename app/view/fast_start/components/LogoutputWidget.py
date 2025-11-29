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
        
        # 连接 MAA Sink 回调信号
        signalBus.callback.connect(self._on_maa_callback)


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

    def _on_maa_callback(self, signal: dict):
        """处理 MAA Sink 发送的回调信号"""
        if not isinstance(signal, dict):
            return
        
        signal_name = signal.get("name", "")
        status = signal.get("status", 0)  # 1=Starting, 2=Succeeded, 3=Failed
        
        # 根据不同的信号类型处理
        if signal_name == "resource":
            # 资源加载状态
            self._handle_resource_signal(status)
        
        elif signal_name == "controller":
            # 控制器/模拟器连接状态
            action = signal.get("task", "")
            self._handle_controller_signal(status, action)
        
        elif signal_name == "tasker_task":
            # 任务执行状态
            task = signal.get("task", "")
            self._handle_tasker_task_signal(status, task)
        
        elif signal_name == "task":
            # 任务识别/执行状态
            task = signal.get("task", "")
            focus = signal.get("focus", "")
            aborted = signal.get("aborted", False)
            self._handle_task_signal(status, task, focus, aborted)

    def _handle_resource_signal(self, status: int):
        """处理资源加载信号"""
        # status: 1=Starting, 2=Succeeded, 3=Failed
        if status == 1:
            self.add_structured_log("INFO", "[资源] 开始加载资源...")
        elif status == 2:
            self.add_structured_log("INFO", "[资源] ✅ 资源加载成功")
        elif status == 3:
            self.add_structured_log("ERROR", "[资源] ❌ 资源加载失败")

    def _handle_controller_signal(self, status: int, action: str):
        """处理控制器/模拟器连接信号"""
        # status: 1=Starting, 2=Succeeded, 3=Failed
        action_text = action if action else "连接操作"
        if status == 1:
            self.add_structured_log("INFO", f"[控制器] 开始执行操作: {action_text}")
        elif status == 2:
            self.add_structured_log("INFO", f"[控制器] ✅ 操作成功: {action_text}")
        elif status == 3:
            self.add_structured_log("ERROR", f"[控制器] ❌ 操作失败: {action_text}")

    def _handle_tasker_task_signal(self, status: int, task: str):
        """处理任务执行信号"""
        # status: 1=Starting, 2=Succeeded, 3=Failed
        task_name = task if task else "未知任务"
        if status == 1:
            self.add_structured_log("INFO", f"[任务] 开始执行任务: {task_name}")
        elif status == 2:
            self.add_structured_log("INFO", f"[任务] ✅ 任务执行成功: {task_name}")
        elif status == 3:
            self.add_structured_log("ERROR", f"[任务] ❌ 任务执行失败: {task_name}")

    def _handle_task_signal(self, status: int, task: str, focus: str, aborted: bool):
        """处理任务识别/执行信号"""
        # status: 1=start, 2=succeeded, 3=failed
        task_name = task if task else "未知任务"
        
        if aborted:
            self.add_structured_log("WARNING", f"[识别] ⚠️ 任务已中止: {task_name}")
            return
        
        status_map = {
            1: ("INFO", "开始识别", "start"),
            2: ("INFO", "✅ 识别成功", "succeeded"),
            3: ("ERROR", "❌ 识别失败", "failed"),
        }
        
        level, prefix, status_key = status_map.get(status, ("INFO", "", ""))
        
        if focus:
            message = f"[识别] {prefix}: {task_name} - {focus}"
        else:
            message = f"[识别] {prefix}: {task_name}"
        
        self.add_structured_log(level, message)

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
