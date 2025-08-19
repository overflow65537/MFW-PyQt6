# -*- coding: utf-8 -*-#   This file is part of MFW-ChainFlow Assistant.

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
MFW-ChainFlow Assistant 计划任务界面
作者: overflow65537
"""

from PySide6.QtCore import QSize, QMetaObject, Qt
from PySide6.QtWidgets import (
    QSizePolicy,
    QVBoxLayout,
    QHBoxLayout,
    QFrame,
    QAbstractItemView,
    QWidget,
    QTreeWidgetItem,
)

from qfluentwidgets import (
    PrimaryPushButton,
    PushButton,
    BodyLabel,
    ComboBox,
    ScrollArea,
    ListWidget,
    ToolButton,
    FluentIcon as FIF,
    TreeWidget,
    SimpleCardWidget,
)

from app.widget import SimpleCardWidgetWithTitle

from ...widget.GenericListToolBarWidget import GenericListToolBarWidget
from ...widget.SimpleCardWidgetWithTitle import SimpleCardWidgetWithTitle


class Ui_Task_Interface(object):
    """任务界面UI类，负责定义计划任务界面的布局和组件"""

    def setupUi(self, Task_Interface):
        """设置UI界面"""
        Task_Interface.setObjectName("Task_Interface")
        self.task_list = GenericListToolBarWidget()

        self._init_option_area()

        self.main_layout = QHBoxLayout(Task_Interface)
        self.main_layout.addWidget(self.task_list)
        self.main_layout.addWidget(self.option_area)
        # 比例50:50
        self.main_layout.setStretch(0, 50)
        self.main_layout.setStretch(1, 50)

        Task_Interface.setLayout(self.main_layout)
        QMetaObject.connectSlotsByName(Task_Interface)

    def __init_resource_setting(self):
        """初始化资源设置"""

        self.resource_setting_area = SimpleCardWidgetWithTitle("资源设置", QVBoxLayout)

    def _init_option_area(self):
        """初始化选项区域"""

        self.option_area = SimpleCardWidgetWithTitle("任务选项", QVBoxLayout)

        for i in range(5):
            self.hbox = QHBoxLayout()
            self.hbox.addWidget(BodyLabel(f"任务{i}"))
            self.hbox.addWidget(ComboBox())
            self.option_area.main_widget_layout.addLayout(self.hbox)
