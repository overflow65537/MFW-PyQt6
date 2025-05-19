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
#     PyQt-Fluent-Widgets Copyright (C) 2023-2025 zhiyiYo
#     https://github.com/zhiyiYo/PyQt-Fluent-Widgets

"""
MFW-ChainFlow Assistant
MFW-ChainFlow Assistant 图标
原作者:zhiyiYo
修改:overflow65537
"""

from enum import Enum

from qfluentwidgets import FluentIconBase, getIconColor, Theme


class Icon(FluentIconBase, Enum):

    GRID = "Grid"
    MENU = "Menu"
    TEXT = "Text"
    PRICE = "Price"
    EMOJI_TAB_SYMBOLS = "EmojiTabSymbols"

    def path(self, theme=Theme.AUTO):
        return f":/gallery/images/icons/{self.value}_{getIconColor(theme)}.svg"
