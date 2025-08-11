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


class LogoutputWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_log_output()
        self.main_layout = QVBoxLayout(self)
        self.main_layout.addWidget(self.log_output_widget)


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
        self.log_output_layout.setContentsMargins(0, 15, 0, 20)
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
