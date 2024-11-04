import os

from typing import Union

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from qfluentwidgets import SettingCard, FluentIconBase, ComboBox
from ..utils.tool import Read_Config, Save_Config, access_nested_dict, find_key_by_value


class ComboBoxSettingCardCustom(SettingCard):
    """Setting card with a combo box"""

    def __init__(
        self,
        icon: Union[str, QIcon, FluentIconBase],
        title,
        target: list,
        path,
        content=None,
        texts=None,
        parent=None,
        is_setting: bool = False,
        mapping: dict = None,
    ):
        super().__init__(icon, title, content, parent)
        self.path = path
        self.target = target
        self.is_setting = is_setting
        self.mapping = mapping
        self.comboBox = ComboBox(self)
        self.hBoxLayout.addWidget(self.comboBox, 0, Qt.AlignmentFlag.AlignRight)
        self.hBoxLayout.addSpacing(16)
        self.comboBox.addItems(texts)
        data = Read_Config(self.path)
        value = access_nested_dict(data, self.target)

        if self.is_setting:
            CurrentText = self.mapping[value]

        else:
            CurrentText = value
        self.comboBox.setCurrentText(CurrentText)
        self.comboBox.currentIndexChanged.connect(self._onCurrentIndexChanged)

    def _onCurrentIndexChanged(self):
        text = self.comboBox.text()
        data = Read_Config(self.path)
        if self.is_setting:
            result = find_key_by_value(self.mapping, text)
            data = access_nested_dict(data, self.target, value=result)

        else:
            data = access_nested_dict(data, self.target, value=text)
        Save_Config(self.path, data)
