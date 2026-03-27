from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from qfluentwidgets import (
    SimpleCardWidget,
    LargeTitleLabel,
    StrongBodyLabel,
    IconWidget,
    FluentIcon,
    BodyLabel,
)


class DashboardCard(SimpleCardWidget):
    def __init__(
        self,
        title: str,
        value: str,
        unit: str,
        icon: FluentIcon | None = None,
        parent: QWidget | None = None,
        clicked=None,
    ):
        super().__init__(parent)

        # --- 基本设置 ---
        self.setBorderRadius(8)  # 稍大的半径以获得更柔和的外观

        # --- 主布局 ---
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(16, 12, 16, 12)  # 调整边距
        self.main_layout.setSpacing(8)  # 各部分之间保持一致的间距

        # --- 顶部区域：图标（可选）和标题 ---
        self.top_layout = QHBoxLayout()
        self.top_layout.setContentsMargins(0, 0, 0, 0)
        self.top_layout.setSpacing(8)  # 图标和标题之间的间距

        # 设置图标
        if icon:
            self.icon_widget = IconWidget(icon, self)
            self.icon_widget.setFixedSize(18, 18)  # 根据需要调整图标大小
            self.top_layout.addWidget(self.icon_widget)
        else:
            self.icon_widget = None  # 如果存在图标则进行跟踪

        self.title_label = BodyLabel(title, self)
        self.title_label.setTextColor("#665353")  # type: ignore
        self.top_layout.addWidget(self.title_label, 1)

        # --- 中间区域：数值和单位 ---
        self.value_label = LargeTitleLabel(value, self)
        self.unit_label = StrongBodyLabel(unit, self)
        self.unit_label.setAlignment(
            Qt.AlignmentFlag.AlignBottom
        )  # 将单位对齐到数值标签行的底部
        self.unit_label.setTextColor("#404040")  # type: ignore

        self.value_layout = QHBoxLayout()
        self.value_layout.setContentsMargins(0, 0, 0, 0)
        self.value_layout.setSpacing(4)
        self.value_layout.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )  # 水平居中数值和单位
        self.value_layout.addStretch(1)  # 在之前添加伸缩项
        self.value_layout.addWidget(self.value_label)
        self.value_layout.addWidget(self.unit_label)
        self.value_layout.addStretch(1)  # 在之后添加伸缩项

        # 添加进主布局
        self.main_layout.addLayout(self.top_layout)
        self.main_layout.addSpacing(4)  # 在数值前的少量间距
        self.main_layout.addLayout(self.value_layout, 1)

        # 连接信号
        if clicked:
            self.clicked.connect(clicked)  # 连接卡片的点击信号

        # 连接信号示例：带有图标的 CPU 使用率
        # cpu_card = DashboardCard(
        #    title="CPU 使用率",
        #    value="75",
        #    unit="%",
        #    icon=FluentIcon.ACCEPT_MEDIUM,
        #    parent=centralWidget,
        #    clicked=lambda: card_clicked_action("CPU 使用率")
        # )

    def set_value(self, value: str):
        """设置主数值文本。"""
        self.value_label.setText(str(value))  # 确保数值是字符串

    def set_unit(self, unit: str):
        """设置单位文本。"""
        self.unit_label.setText(unit)

    def set_title(self, title: str):
        """设置标题文本。"""
        self.title_label.setText(title)

    def set_icon(self, icon: FluentIcon):
        """设置或更新图标。"""
        if self.icon_widget:
            self.icon_widget.setIcon(icon)

    def set_value_color(self, color: str):
        """设置数值标签的颜色（例如，根据状态）。"""
        self.value_label.setStyleSheet(f"color: {color};")

        # 设置数值文本颜色
        # cpu_card.set_value_color("orange")
