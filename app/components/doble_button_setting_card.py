from qfluentwidgets import SettingCard, PrimaryPushButton, FluentIconBase

from PySide6.QtCore import Qt


from qfluentwidgets import SettingCard, PrimaryPushButton

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from typing import Union
from PySide6.QtCore import Signal


class DoubleButtonSettingCard(SettingCard):
    """Setting card with a push button"""

    clicked = Signal()
    clicked2 = Signal()

    def __init__(
        self,
        text,
        text2,
        icon: Union[str, QIcon, FluentIconBase],
        title,
        content=None,
        parent=None,
    ):
        """
        Parameters
        ----------
        text: str
            the text of push button
        text2: str
            the text of push button
        icon: str | QIcon | FluentIconBase
            the icon to be drawn

        title: str
            the title of card

        content: str
            the content of card

        parent: QWidget
            parent widget
        """
        super().__init__(icon, title, content, parent)
        self.button = PrimaryPushButton(text, self)
        self.button2 = PrimaryPushButton(text2, self)
        self.hBoxLayout.addWidget(self.button2, 0, Qt.AlignmentFlag.AlignRight)
        self.hBoxLayout.addSpacing(16)
        self.hBoxLayout.addWidget(self.button, 0, Qt.AlignmentFlag.AlignRight)
        self.hBoxLayout.addSpacing(16)
        self.button.clicked.connect(self.clicked)
        self.button2.clicked.connect(self.clicked2)
