from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt
from .UI_scheduled_interface import Ui_Scheduled_Interface
from ..common.config import cfg
from ..common.signal_bus import signalBus
from ..utils.tool import Get_Values_list_Option, Save_Config, for_config_get_url
from qfluentwidgets import (
    InfoBar,
    InfoBarPosition,
)
from ..components.choose_resource_button import CustomMessageBox
from ..utils.update import Readme
import os
import shutil

from ..utils.logger import logger
from ..common.maa_config_data import maa_config_data
import re


class ScheduledInterface(Ui_Scheduled_Interface, QWidget):

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setupUi(self)
        self.bind_signals()
        self.init_widget_text()
        if cfg.get(cfg.resource_exist):
            self.List_widget.addItems(
                Get_Values_list_Option(maa_config_data.config_path, "task")
            )
    def bind_signals(self):
        signalBus.update_task_list.connect(self.update_task_list_passive)
        self.daily_mode_radio.clicked.connect(lambda: self.change_layout("daily"))
        self.weekly_mode_radio.clicked.connect(lambda: self.change_layout("weekly"))
        self.monthly_mode_radio.clicked.connect(lambda: self.change_layout("monthly"))
    def init_widget_text(self):
        """初始化界面文本"""
        self.date_label.setText(self.tr("Start Date"))
        self.schedule_mode_title.setText(self.tr("Schedule Mode"))
        self.daily_mode_radio.setText(self.tr("Daily"))
        self.weekly_mode_radio.setText(self.tr("Weekly"))
        self.monthly_mode_radio.setText(self.tr("Monthly"))
        self.refresh_time_label.setText(self.tr("Refresh Time, Daily"))
        self.weekly_mode_combox.addItems([self.tr("Monday"), self.tr("Tuesday"), self.tr("Wednesday"), self.tr("Thursday"), self.tr("Friday"), self.tr("Saturday"), self.tr("Sunday")])
        self.refresh_time_unit_label.setText(self.tr("Hour"))
        self.interval_label.setText(self.tr("Interval"))
        self.interval_unit.addItems([self.tr("Minutes"), self.tr("Hours"), self.tr("Days")])
        self.loop_label.setText(self.tr("Loop"))
        self.loop_unit_label.setText(self.tr("Times"))

    def get_list_items(self) -> list[str]:
        """获取列表中所有项的文本"""
        return [
            item.text()
            for i in range(self.List_widget.count())
            if (item := self.List_widget.item(i)) is not None
        ]

    def show_error(self, message):
        """显示错误信息"""
        InfoBar.error(
            title=self.tr("Error"),
            content=message,
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.BOTTOM_RIGHT,
            duration=-1,
            parent=self,
        )


    def update_task_list(self):
        """更新任务列表"""
        signalBus.update_task_list.emit()

    def update_task_list_passive(self):
        """更新任务列表(被动刷新)"""
        self.List_widget.clear()
        self.List_widget.addItems(
            Get_Values_list_Option(maa_config_data.config_path, "task")
        )

    def get_task_list_widget(self) -> list[str]:
        """获取任务列表控件中的项"""
        return [
            item.text()
            for item in (
                self.List_widget.item(i) for i in range(self.List_widget.count())
            )
            if item is not None
        ]
    def change_layout(self, mode):
        if mode == "daily":
            self.weekly_mode_combox.hide()
            self.refresh_time_label.setText(self.tr("Refresh Time, Daily"))
            self.refresh_time_unit_label.setText(self.tr("Hour"))
        elif mode == "weekly":
            self.weekly_mode_combox.show()
            self.refresh_time_label.setText(self.tr("Refresh Time, Weekly") )
        elif mode == "monthly":
            self.weekly_mode_combox.hide()
            self.refresh_time_label.setText(self.tr("Refresh Time, Monthly"))
            self.refresh_time_unit_label.setText(self.tr("Day"))