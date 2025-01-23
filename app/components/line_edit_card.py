import os
from typing import Union
from PyQt6.QtGui import QIcon, QIntValidator
from qfluentwidgets import (
    SettingCard,
    FluentIconBase,
    LineEdit,
    ToolButton,
    PrimaryPushButton,
    PasswordLineEdit,
)
from qfluentwidgets import FluentIcon as FIF
from ..utils.tool import Read_Config, Save_Config
from ..utils.logger import logger
from ..common.maa_config_data import maa_config_data


class LineEditCard(SettingCard):
    """设置中的输入框卡片"""

    def __init__(
        self,
        icon: Union[str, QIcon, FluentIconBase],
        title: str,
        holderText: str = "",
        target: str = "",
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
        :param target: 修改目标（custom页面要用）
        :param content: 内容
        :param parent: 父级控件
        :param num_only: 是否只能输入数字
        """
        super().__init__(icon, title, content, parent)

        self.target = target
        if is_passwork:
            self.lineEdit = PasswordLineEdit(self)
        else:
            self.lineEdit = LineEdit(self)
        if button_type == "primary":
            self.button = PrimaryPushButton(button_text, self)
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

        # 连接文本变化信号
        self.lineEdit.textChanged.connect(self._on_text_changed)

    def _on_text_changed(self):
        """处理文本变化事件"""
        text = self.lineEdit.text()

        if self.target != "":
            self._save_text_to_config(text)

    def _save_text_to_config(self, text: str):
        """将文本保存到配置文件"""
        try:
            config_path = os.path.join(
                os.getcwd(), "config", "custom_setting_config.json"
            )
            data = Read_Config(config_path)
            data[self.target] = text
            Save_Config(config_path, data)
        except Exception as e:
            logger.warning(f"保存配置时出错: {e}")
