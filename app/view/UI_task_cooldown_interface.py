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
MFW-ChainFlow Assistant 任务界面
作者:overflow65537
"""

from PySide6.QtCore import Qt, QSize, QMetaObject, QCoreApplication
from PySide6.QtWidgets import QSizePolicy, QVBoxLayout, QHBoxLayout, QWidget, QFrame

from qfluentwidgets import (
    PushButton,
    BodyLabel,
    ComboBox,
    RadioButton,
    CheckBox,
    SpinBox,
    ListWidget,
    ScrollArea,
)


class Ui_TaskCooldown_Interface(object):
    def setupUi(self, Scheduled_Interface):
        Scheduled_Interface.setObjectName("TaskCooldown_Interface")
        Scheduled_Interface.resize(900, 600)
        Scheduled_Interface.setMinimumSize(QSize(0, 0))
        # 主窗口
        self.List_layout = QVBoxLayout()
        self.List_widget = ListWidget(Scheduled_Interface)
        self.List_layout.addWidget(self.List_widget)

        # 速通模式标题布局
        # 主垂直布局
        self.main_layout = QVBoxLayout()

        # 第一行：标题
        self.title_label = BodyLabel()
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addWidget(self.title_label)
        # 添加一个横线
        self.Hline2 = QFrame(Scheduled_Interface)
        self.Hline2.setFrameShape(QFrame.Shape.HLine)
        self.Hline2.setFrameShadow(QFrame.Shadow.Sunken)
        self.main_layout.addWidget(self.Hline2)

        # 第三行：复合水平布局
        self.row3_layout = QHBoxLayout()

        # 计划任务模式选择容器
        self.schedule_mode_widget = QWidget()
        self.schedule_mode_layout = QVBoxLayout(self.schedule_mode_widget)

        # 计划任务模式单选按钮
        self.schedule_mode_title = BodyLabel()
        self.daily_mode_radio = RadioButton()
        self.weekly_mode_radio = RadioButton()
        self.monthly_mode_radio = RadioButton()

        self.schedule_mode_layout.addWidget(self.schedule_mode_title)
        self.schedule_mode_layout.addWidget(self.daily_mode_radio)
        self.schedule_mode_layout.addWidget(self.weekly_mode_radio)
        self.schedule_mode_layout.addWidget(self.monthly_mode_radio)

        # 右侧：时间选择和操作按钮区域
        self.right_panel = QWidget(Scheduled_Interface)
        self.right_layout = QVBoxLayout(self.right_panel)

        # 按钮表格布局容器
        widget = QWidget(Scheduled_Interface)
        self.layout = QVBoxLayout(widget)

        self.refresh_time_layout = QHBoxLayout()
        self.refresh_time_label = BodyLabel()
        self.weekly_mode_combox = ComboBox()

        self.refresh_time_mo_spinbox = SpinBox()
        self.refresh_time_mo_spinbox.setMinimum(1)

        self.refresh_time_mo_unit_label = BodyLabel()
        self.refresh_time_mo_spinbox.hide()
        self.refresh_time_mo_unit_label.hide()

        self.refresh_time_spinbox = SpinBox()
        self.refresh_time_spinbox.setMinimum(-1)
        self.refresh_time_unit_label = BodyLabel()

        self.refresh_time_layout.addWidget(self.refresh_time_label)
        self.refresh_time_layout.addWidget(self.weekly_mode_combox)
        self.refresh_time_layout.addWidget(self.refresh_time_mo_spinbox)
        self.refresh_time_layout.addWidget(self.refresh_time_mo_unit_label)
        self.refresh_time_layout.addWidget(self.refresh_time_spinbox)
        self.refresh_time_layout.addWidget(self.refresh_time_unit_label)
        self.weekly_mode_combox.hide()

        self.interval_layout = QHBoxLayout()
        self.interval_label = BodyLabel()
        self.interval_input = SpinBox()
        self.interval_input.setMinimum(-1)
        self.interval_unit = ComboBox()
        self.loop_label = BodyLabel()
        self.loop_input = SpinBox()
        self.loop_input.setMinimum(-1)
        self.loop_unit_label = BodyLabel()

        self.interval_layout.addWidget(self.interval_label)
        self.interval_layout.addWidget(self.interval_input)
        self.interval_layout.addWidget(self.interval_unit)
        self.interval_layout.addWidget(self.loop_label)
        self.interval_layout.addWidget(self.loop_input)
        self.interval_layout.addWidget(self.loop_unit_label)

        self.layout.addLayout(self.refresh_time_layout)
        self.layout.addLayout(self.interval_layout)

        widget.setLayout(self.layout)

        self.current_layout = widget
        self.right_layout.addWidget(self.current_layout)

        self.row3_layout.addWidget(self.schedule_mode_widget)
        self.Vline1 = QFrame()
        self.Vline1.setFrameShape(QFrame.Shape.VLine)
        self.Vline1.setFrameShadow(QFrame.Shadow.Sunken)
        self.row3_layout.addWidget(self.Vline1)
        self.row3_layout.addWidget(self.right_panel)
        self.main_layout.addLayout(self.row3_layout)

        # 时间选择水平布局
        self.time_selection_layout = QHBoxLayout()

        # 目前循环次数
        self.current_loop_label = BodyLabel()
        self.current_loop_input = SpinBox()
        self.current_loop_input.setMinimum(-1)

        self.time_selection_layout.addWidget(self.current_loop_label)
        self.time_selection_layout.addWidget(self.current_loop_input)
        self.layout.addLayout(self.time_selection_layout)

        self.row4_layout = QHBoxLayout()

        # 是否启动
        self.is_start = CheckBox()
        # 日期
        self.date_label = BodyLabel()
        self.data_label1 = BodyLabel()
        self.row4_layout.addWidget(self.is_start)
        self.row4_layout.addWidget(self.data_label1)
        self.row4_layout.addWidget(self.date_label)
        self.main_layout.addLayout(self.row4_layout)

        # 第三行：三个按钮的水平布局
        self.button_layout = QHBoxLayout()
        self.confirm_button = PushButton()
        # 居中,固定大小
        self.confirm_button.setSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed
        )
        self.confirm_button.setFixedSize(QSize(100, 30))
        self.button_layout.addWidget(self.confirm_button)
        self.main_layout.addLayout(self.button_layout)

        # 添加一条横线
        self.Hline1 = QFrame()
        self.Hline1.setFrameShape(QFrame.Shape.HLine)
        self.Hline1.setFrameShadow(QFrame.Shadow.Sunken)
        self.main_layout.addWidget(self.Hline1)

        # 第四行：一个滚动区域,里面是垂直布局的Qwidget,里面有一个bodylabel叫notice_label
        self.scroll_area = ScrollArea(Scheduled_Interface)
        self.scroll_area.setStyleSheet("background-color: transparent;")
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.scroll_area_content = QWidget()
        self.scroll_area_content.setObjectName("scroll_area_content")
        self.scroll_area_content.setStyleSheet(
            "QWidget#scroll_area_content { background-color: transparent; }"
        )
        self.scroll_area_layout = QVBoxLayout(self.scroll_area_content)
        self.scroll_area_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll_area_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_area_layout.setSpacing(0)
        self.scroll_area.setWidget(self.scroll_area_content)
        self.notice_label = BodyLabel()
        self.notice_label.setWordWrap(True)
        self.scroll_area_layout.addWidget(self.notice_label)
        self.main_layout.addWidget(self.scroll_area)

        # 添加一条竖线
        self.Vline1 = QFrame()
        self.Vline1.setFrameShape(QFrame.Shape.VLine)
        self.Vline1.setFrameShadow(QFrame.Shadow.Sunken)
        self.VBoxLayout = QHBoxLayout()
        self.VBoxLayout.addWidget(self.List_widget)
        self.VBoxLayout.addWidget(self.Vline1)
        self.VBoxLayout.addLayout(self.main_layout)
        # 设置布局比例50:0:50
        self.VBoxLayout.setStretch(0, 50)
        self.VBoxLayout.setStretch(2, 50)

        Scheduled_Interface.setLayout(self.VBoxLayout)
        self.retranslateUi(Scheduled_Interface)
        QMetaObject.connectSlotsByName(Scheduled_Interface)

    def retranslateUi(self, Scheduled_Interface):
        _translate = QCoreApplication.translate
        Scheduled_Interface.setWindowTitle(_translate("Scheduled_Interface", "Form"))
