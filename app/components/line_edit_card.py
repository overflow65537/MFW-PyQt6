import os
from typing import Union
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QIcon, QIntValidator
from qfluentwidgets import (
    SettingCard,
    FluentIconBase,
    LineEdit,
    OptionsConfigItem,
    qconfig,
)
from ..utils.tool import Read_Config, Save_Config


class LineEditCard(SettingCard):
    """设置中的输入框卡片"""

    text_change = pyqtSignal()

    def __init__(
        self,
        icon: Union[str, QIcon, FluentIconBase],
        title: str,
        holderText: str = "",
        configItem: OptionsConfigItem = None,
        target: str = None,
        content=None,
        parent=None,
        num_only=True,
    ):
        """
        初始化输入框卡片。

        :param icon: 图标
        :param title: 标题
        :param holderText: 占位符文本
        :param configItem: 配置项
        :param target: 修改目标（custom页面要用）
        :param content: 内容
        :param parent: 父级控件
        :param num_only: 是否只能输入数字
        """
        super().__init__(icon, title, content, parent)

        self.target = target
        self.configItem = configItem
        self.lineEdit = LineEdit(self)

        # 设置布局
        self.hBoxLayout.addWidget(self.lineEdit, 0)
        self.hBoxLayout.addSpacing(16)

        # 设置占位符文本
        if self.configItem is not None:
            holderText = self.configItem.value
        self.lineEdit.setPlaceholderText(holderText)

        # 设置输入限制
        if num_only:
            self.lineEdit.setValidator(QIntValidator())

        # 连接文本变化信号
        self.lineEdit.textChanged.connect(self._on_text_changed)

    def _on_text_changed(self):
        """处理文本变化事件"""
        text = self.lineEdit.text()

        if self.configItem:
            qconfig.set(self.configItem, text)
        else:
            self._save_text_to_config(text)

    def _save_text_to_config(self, text: str):
        """将文本保存到配置文件"""
        try:
            config_path = os.path.join(os.getcwd(), "config", "custom_config.json")
            data = Read_Config(config_path)
            data[self.target] = text
            Save_Config(config_path, data)
        except Exception as e:
            print(f"保存配置时出错: {e}")
