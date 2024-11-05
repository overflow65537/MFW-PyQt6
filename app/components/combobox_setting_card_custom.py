import os

from typing import Union

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from qfluentwidgets import SettingCard, FluentIconBase, ComboBox
from ..utils.tool import (
    Read_Config,
    Save_Config,
    access_nested_dict,
    find_key_by_value,
    rewrite_contorller,
    delete_contorller,
)


class ComboBoxSettingCardCustom(SettingCard):
    """Setting card with a combo box"""

    def __init__(
        self,
        icon: Union[str, QIcon, FluentIconBase],
        title,
        path,
        target: list = None,
        controller=None,
        controller_type=None,
        content=None,
        texts=None,
        parent=None,
        mode: str = None,
        mapping: dict = None,
    ):
        super().__init__(icon, title, content, parent)
        self.path = path
        self.target = target
        self.mode = mode
        self.mapping = mapping
        self.controller = controller
        self.controller_type = controller_type
        self.comboBox = ComboBox(self)
        self.hBoxLayout.addWidget(self.comboBox, 0, Qt.AlignmentFlag.AlignRight)
        self.hBoxLayout.addSpacing(16)
        self.comboBox.addItems(texts)
        data = Read_Config(self.path)

        if self.mode == "setting":
            value = access_nested_dict(data, self.target)
            CurrentText = self.mapping[value]

        elif self.mode == "custom":
            value = access_nested_dict(data, self.target)
            CurrentText = value
        elif self.mode == "interface_setting":
            value = rewrite_contorller(data, controller, controller_type)

            if value is None or value == {}:
                CurrentText = self.tr("default")
            else:
                CurrentText = self.mapping[value]
        self.comboBox.setCurrentText(CurrentText)
        self.comboBox.currentIndexChanged.connect(self._onCurrentIndexChanged)

    def _onCurrentIndexChanged(self):
        text = self.comboBox.text()
        data = Read_Config(self.path)
        if self.mode == "setting":
            result = find_key_by_value(self.mapping, text)
            data = access_nested_dict(data, self.target, value=result)

        elif self.mode == "custom":
            data = access_nested_dict(data, self.target, value=text)
        elif self.mode == "interface_setting":
            result = find_key_by_value(self.mapping, text)
            if result == 0:
                data = delete_contorller(data, self.controller, self.controller_type)
            else:
                data = rewrite_contorller(
                    data, self.controller, self.controller_type, result
                )

        Save_Config(self.path, data)
