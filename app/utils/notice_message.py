#   This file is part of MFW-ChainFlow Assistant.

#   MFW-ChainFlow Assistant is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published
#   by the Free Software Foundation, either version 3 of the License,
#   or (at your option) any later version.

#   MFW-ChainFlow Assistant is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty
#   of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See
#   the GNU General Public License for more details.

#   You should have received a copy of the GNU General Public License
#   along with MFW-ChainFlow Assistant. If not, see <https://www.gnu.org/licenses/>.

#   Contact: err.overflow@gmail.com
#   Copyright (C) 2024-2025  MFW-ChainFlow Assistant. All rights reserved.

# This file incorporates work covered by the following copyright and
# permission notice:
#
#     AUTO_MAA Copyright (C) 2024-2025 DLmaster361
#     https://github.com/DLmaster361/AUTO_MAA


"""
MFW-ChainFlow Assistant
MFW-ChainFlow Assistant 公告面板
原作者:DLmaster361
地址:https://github.com/DLmaster361/AUTO_MAA
修改:overflow65537
"""

from PySide6.QtWidgets import (
    QHBoxLayout,
    QVBoxLayout,
)
from PySide6.QtCore import Qt
from qfluentwidgets import (
    MessageBoxBase,
    Signal,
    CardWidget,
    BodyLabel,
    PrimaryPushButton,
    HeaderCardWidget,
    ScrollArea,
)
import re
import markdown
from functools import partial
from typing import List, Dict

# 以下代码引用自 AUTO_MAA 项目的 ./app/ui/Widget.py 文件，用于创建公告对话框
class NoticeMessageBox(MessageBoxBase):
    """公告对话框"""

    def __init__(self, parent, title: str, content: Dict[str, str]):
        super().__init__(parent)

        self.index = self.NoticeIndexCard(title, content, self)

        # 原 BodyLabel 初始化（保持不变）
        self.text = BodyLabel(self)
        self.text.setOpenExternalLinks(True)
        self.text.setWordWrap(True)
        self.text.setAlignment(Qt.AlignmentFlag.AlignTop)

        # 新增：创建滚动区域并包裹 BodyLabel
        self.scroll_area = ScrollArea(self)
        #设置透明
        self.scroll_area.enableTransparentBackground()
        self.scroll_area.setWidgetResizable(True)  # 允许内容自适应大小
        self.scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )  # 隐藏水平滚动条
        self.scroll_area.setWidget(self.text)  # 将 BodyLabel 放入滚动区域

        self.button_yes = PrimaryPushButton(self.tr("Confirm and never show again"), self)
        self.button_cancel = PrimaryPushButton(self.tr("Confirm"), self)

        self.buttonGroup.hide()

        self.v_layout = QVBoxLayout()
        # 修改：将滚动区域添加到布局（原直接添加 text）
        self.v_layout.addWidget(self.scroll_area)
        self.button_layout = QHBoxLayout()
        self.button_layout.addWidget(self.button_yes)
        self.button_layout.addWidget(self.button_cancel)
        self.v_layout.addLayout(self.button_layout)

        self.h_layout = QHBoxLayout()
        self.h_layout.addWidget(self.index)
        self.h_layout.addLayout(self.v_layout)
        self.h_layout.setStretch(0, 1)
        self.h_layout.setStretch(1, 3)

        # 将组件添加到布局中
        self.viewLayout.addLayout(self.h_layout)
        self.widget.setFixedSize(800, 600)

        self.index.index_changed.connect(self.__update_text)
        self.button_yes.clicked.connect(self.yesButton.click)
        self.button_cancel.clicked.connect(self.cancelButton.click)
        self.index.index_cards[0].clicked.emit()

    def __update_text(self, text: str):

        html = markdown.markdown(text).replace("\n", "")
        html = re.sub(
            r"<code>(.*?)</code>",
            r"<span style='color: #009faa;'>\1</span>",
            html,
        )
        html = re.sub(
            r'(<a\s+[^>]*href="[^"]+"[^>]*)>', r'\1 style="color: #009faa;">', html
        )
        html = re.sub(r"<li><p>(.*?)</p></li>", r"<p><strong>◆ </strong>\1</p>", html)
        html = re.sub(r"<ul>(.*?)</ul>", r"\1", html)

        self.text.setText(f"<body>{html}</body>")

    class NoticeIndexCard(HeaderCardWidget):

        index_changed = Signal(str)

        def __init__(self, title: str, content: Dict[str, str], parent=None): # type: ignore
            super().__init__(parent)
            self.setTitle(title)

            self.Layout = QVBoxLayout()
            self.viewLayout.addLayout(self.Layout)
            self.viewLayout.setContentsMargins(3, 0, 3, 3)

            self.index_cards: List[QuantifiedItemCard] = []

            for index, text in content.items():

                self.index_cards.append(QuantifiedItemCard([index, ""]))
                self.index_cards[-1].clicked.connect(
                    partial(self.index_changed.emit, text)
                )
                self.Layout.addWidget(self.index_cards[-1])

            if not content:
                self.Layout.addWidget(QuantifiedItemCard(["暂无信息", ""]))

            self.Layout.addStretch(1)


class QuantifiedItemCard(CardWidget):

    def __init__(self, item: list, parent=None):
        super().__init__(parent)

        self.Layout = QHBoxLayout(self)

        self.Name = BodyLabel(item[0], self)
        self.Numb = BodyLabel(str(item[1]), self)

        self.Layout.addWidget(self.Name)
        self.Layout.addStretch(1)
        self.Layout.addWidget(self.Numb)
