from PyQt6.QtWidgets import QFileDialog
from PyQt6.QtGui import QColor
from qfluentwidgets import (
    MessageBoxBase,
    SubtitleLabel,
    LineEdit,
)
from ..common.config import cfg


class CustomMessageBox(MessageBoxBase):
    """Custom message box"""

    def __init__(self, parent=None):
        super().__init__(parent)
        transparent_color = QColor(255, 255, 255, 0)
        self.setMaskColor(transparent_color)
        self.folder = None
        self.type_resource_name()
        self.titleLabel = SubtitleLabel("输入资源名称", self)
        self.name_LineEdit = LineEdit(self)

        self.name_LineEdit.setPlaceholderText("输入资源的名称")
        self.name_LineEdit.setClearButtonEnabled(True)

        # 添加控件到布局
        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addWidget(self.name_LineEdit)

        # 更改按钮文本
        self.yesButton.setText("确定")
        self.cancelButton.setText("取消")

        self.widget.setMinimumWidth(350)

    def type_resource_name(self):
        self.folder = QFileDialog.getExistingDirectory(
            self, self.tr("Choose folder"), "./"
        )

    def click_yes_button(self):
        res_name = self.name_LineEdit.text()
        self.folder = self.folder
