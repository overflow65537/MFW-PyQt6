from qfluentwidgets import SettingCard, PushButton, FluentIconBase,EditableComboBox
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from typing import Union


class ComboWithActionSettingCard(SettingCard):
    """Setting card with a push button"""

    def __init__(
        self,
        icon: Union[str, QIcon, FluentIconBase],
        title,
        content=None,
        parent=None,
    ):

        super().__init__(icon, title, content, parent)
        self.add_button = PushButton(self.tr("add"), self)
        self.delete_button = PushButton(self.tr("delete"), self)
        self.combox = EditableComboBox(self)

        self.hBoxLayout.addWidget(self.add_button, 0, Qt.AlignmentFlag.AlignRight)
        self.hBoxLayout.addSpacing(16)
        self.hBoxLayout.addWidget(self.delete_button, 0, Qt.AlignmentFlag.AlignRight)
        self.hBoxLayout.addSpacing(16)
        self.hBoxLayout.addWidget(self.combox, 0, Qt.AlignmentFlag.AlignRight)
        self.hBoxLayout.addSpacing(16)
