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
    # 设置中的输入框

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
        self,
        icon: Union[str, QIcon, FluentIconBase],        图标
        title: str,                                     标题
        holderText: str = "",                           占位符文本
        configItem: OptionsConfigItem = None,           配置项
        target: str = None,                             修改目标,custom页面要用
        content=None,                                   内容
        parent=None,                                    父级
        num_only=True,                                  是否只能输入数字

        """

        super().__init__(icon, title, content, parent)

        self.target = target
        self.configItem = configItem
        self.lineEdit = LineEdit(self)
        self.hBoxLayout.addWidget(self.lineEdit, 0)
        self.hBoxLayout.addSpacing(16)
        self.lineEdit.setFixedWidth(118)
        self.lineEdit.setMinimumWidth(118)
        if self.configItem != None:
            holderText = self.configItem.value
        self.lineEdit.setPlaceholderText(holderText)
        if num_only:

            self.lineEdit.setValidator(QIntValidator())
        self.lineEdit.textChanged.connect(self.__ontextChanged)

    def __ontextChanged(self):
        if self.configItem:
            text = self.lineEdit.text()
            qconfig.set(self.configItem, text)
        else:
            text = self.lineEdit.text()
            data = Read_Config(
                (os.path.join(os.getcwd(), "config", "custom_config.json"))
            )
            data[self.target] = text
            Save_Config(
                (os.path.join(os.getcwd(), "config", "custom_config.json")), data
            )
