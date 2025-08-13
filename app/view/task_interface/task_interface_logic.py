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

"""
MFW-ChainFlow Assistant
MFW-ChainFlow Assistant 任务逻辑
作者:overflow65537
"""

from PySide6.QtWidgets import QWidget, QTableWidgetItem

from qfluentwidgets import CheckBox, TransparentToolButton, FluentIcon as FIF
from ..task_interface.task_interface_ui import Ui_Task_Interface

from ...widget.TaskWidgetItem import TaskWidgetItem


class TaskInterface(Ui_Task_Interface, QWidget):

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setupUi(self)
        self.task_list.add_button.clicked.connect(self.add_task)

    def add_task(self):
        """添加任务"""
        pass
