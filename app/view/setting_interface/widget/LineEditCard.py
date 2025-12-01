from PySide6.QtGui import (
    QIcon,
    QIntValidator,
)


from qfluentwidgets import (
    FluentIconBase,
    SettingCard,
    LineEdit,
    PasswordLineEdit,
    ToolButton,
)
from qfluentwidgets import FluentIcon as FIF

from app.view.setting_interface.widget.RightCheckPrimaryPushButton import (
    RightCheckPrimaryPushButton,
)
from app.utils.logger import logger

import os
from typing import Union


class LineEditCard(SettingCard):
    """设置中的输入框卡片"""

    def __init__(
        self,
        icon: Union[str, QIcon, FluentIconBase],
        title: str,
        holderText: str = "",
        content=None,
        parent=None,
        is_passwork: bool = False,
        num_only=True,
        button: bool = False,
        button_type: str = "",
        button_text: str = "",
    ):
        """
        初始化输入框卡片。

        :param icon: 图标
        :param title: 标题
        :param holderText: 占位符文本
        :param content: 内容
        :param parent: 父级控件
        :param is_passwork: 是否是密码输入框
        :param num_only: 是否只能输入数字
        :param button: 是否显示按钮
        :param button_type: 按钮类型
        :param button_text: 按钮文本
        """
        super().__init__(icon, title, content, parent)

        if is_passwork:
            self.lineEdit = PasswordLineEdit(self)
        else:
            self.lineEdit = LineEdit(self)
        if button_type == "primary":
            self.button = RightCheckPrimaryPushButton(button_text, self)
            self.button.rightClicked.connect(self._on_right_clicked)
        else:
            self.toolbutton = ToolButton(FIF.FOLDER_ADD, self)

        # 设置布局
        self.hBoxLayout.addWidget(self.lineEdit, 0)
        self.hBoxLayout.addSpacing(16)

        if button:
            if button_type == "primary":
                self.hBoxLayout.addWidget(self.button, 0)
            else:
                self.hBoxLayout.addWidget(self.toolbutton, 0)
            self.hBoxLayout.addSpacing(16)
            self.lineEdit.setFixedWidth(300)

        else:
            self.toolbutton.hide()
        # 设置占位符文本

        self.lineEdit.setText(str(holderText))

        # 设置输入限制
        if num_only:
            self.lineEdit.setValidator(QIntValidator())

    def _on_right_clicked(self):
        """处理右键点击事件"""
        self.lineEdit.setEnabled(True)
