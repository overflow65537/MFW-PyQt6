from qfluentwidgets import (
    SettingCard,
    PushButton,
    FluentIconBase,
    EditableComboBox,
    ComboBox,
    ToolButton
)
from qfluentwidgets import FluentIcon as FIF
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QSizePolicy
from typing import Union


class ComboWithActionSettingCard(SettingCard):
    """Setting card with a push button"""

    def __init__(
        self,
        icon: Union[str, QIcon, FluentIconBase],
        title,
        res=False,
        content=None,
        parent=None,
    ):

        super().__init__(icon, title, content, parent)
        self.add_button = ToolButton(FIF.ADD, self)
        self.delete_button = ToolButton(FIF.DELETE, self)
        if res:
            self.combox = ComboBox(self)
            self.combox.setObjectName("combox")
            self.delete_button.setObjectName("delete_button")
            self.add_button.setObjectName("add_button")
        else:
            self.combox = EditableComboBox(self)
            #设置占用最小宽度
            self.combox.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        self.hBoxLayout.addWidget(self.add_button, 0, Qt.AlignmentFlag.AlignRight)
        self.hBoxLayout.addSpacing(16)
        self.hBoxLayout.addWidget(self.combox, 0, Qt.AlignmentFlag.AlignRight)
        self.hBoxLayout.addSpacing(16)
        self.hBoxLayout.addWidget(self.delete_button, 0, Qt.AlignmentFlag.AlignRight)
        self.hBoxLayout.addSpacing(16)
