from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFileDialog, QHBoxLayout, QSizePolicy
from PyQt6.QtGui import QColor
from qfluentwidgets import (
    MessageBoxBase,
    SubtitleLabel,
    LineEdit,
    PushButton,
    InfoBar,
    InfoBarPosition,
)
from ..common.config import cfg
from ..utils.tool import Read_Config, Save_Config
import os


class CustomMessageBox(MessageBoxBase):
    """Custom message box"""

    def __init__(self, parent=None):
        super().__init__(parent)
        transparent_color = QColor(255, 255, 255, 0)
        self.setMaskColor(transparent_color)
        self.folder = None
        self.titleLabel = SubtitleLabel("输入资源名称", self)
        self.name_LineEdit = LineEdit(self)
        self.name_LineEdit.setPlaceholderText("输入资源的名称")
        self.name_LineEdit.setClearButtonEnabled(True)

        self.path_layout = QHBoxLayout()
        self.path_LineEdit = LineEdit(self)
        self.path_LineEdit.setPlaceholderText("输入资源的路径")
        self.path_LineEdit.setClearButtonEnabled(True)

        self.path_layout.addWidget(self.path_LineEdit)
        self.resourceButton = PushButton("选择资源", self)
        self.resourceButton.setSizePolicy(
            QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed
        )
        self.resourceButton.clicked.connect(self.type_resource_name)

        self.path_layout.addWidget(self.resourceButton)

        self.update_LineEdit = LineEdit(self)
        self.update_LineEdit.setPlaceholderText("输入更新链接")
        self.update_LineEdit.setClearButtonEnabled(True)

        self.path_layout.setStretch(0, 9)
        self.path_layout.setStretch(1, 1)

        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addLayout(self.path_layout)
        self.viewLayout.addWidget(self.name_LineEdit)
        self.viewLayout.addWidget(self.update_LineEdit)

        self.yesButton.setText("确定")
        self.cancelButton.setText("取消")

        self.widget.setMinimumWidth(350)
        self.yesButton.clicked.connect(self.click_yes_button)

    def type_resource_name(self):
        self.folder = QFileDialog.getExistingDirectory(
            self, self.tr("Choose folder"), "./"
        )
        self.path_LineEdit.setText(self.folder)
        interface_path = os.path.join(self.folder, "..", "interface.json")
        if not os.path.exists(interface_path):
            self.show_error(self.tr("该资源没有interface.json文件"))
            return
        elif os.path.basename(self.folder) != "resource":
            self.show_error(self.tr("该资源不是resource目录下的资源"))
            return
        self.interface_data = Read_Config(interface_path)
        project_name = self.interface_data.get("name", "")
        projece_url = self.interface_data.get("url", "")
        self.name_LineEdit.clear()
        self.name_LineEdit.setText(project_name)
        self.update_LineEdit.clear()
        self.update_LineEdit.setText(projece_url)

    def show_error(self, message):
        InfoBar.error(
            title=self.tr("Error"),
            content=message,
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.BOTTOM_RIGHT,
            duration=-1,
            parent=self,
        )

    def click_yes_button(self):
        print("点击确定按钮")
        name_data = self.name_LineEdit.text()
        path_data = self.path_LineEdit.text()
        update_data = self.update_LineEdit.text()
        interface_path = os.path.join(path_data, "..", "interface.json")
        resource_data = cfg.get(cfg.maa_resource_list)
        resource_list = list(resource_data)
        resource_path_list = list(resource_data.values())
        if self.name_LineEdit.text() == "":
            print("资源名称不能为空")
            self.show_error(self.tr("资源名称不能为空"))
            return
        elif path_data == "":
            print("资源路径不能为空")
            self.show_error(self.tr("资源路径不能为空"))
            return
        elif name_data in resource_list or path_data in resource_path_list:
            print("资源已存在")
            self.show_error(self.tr("资源已存在"))
            return
        elif update_data == "":
            print("更新链接不能为空")
            self.show_error(self.tr("更新链接不能为空"))
            return
        self.interface_data["name"] = name_data
        self.interface_data["url"] = update_data
        Save_Config(interface_path, self.interface_data)
        resource_data[name_data] = path_data
        cfg.set(cfg.maa_resource_list, resource_data)
        self.close()
