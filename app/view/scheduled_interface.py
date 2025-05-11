from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt,QTime,QDate
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
from datetime import datetime
import time


class ScheduledInterface(Ui_Scheduled_Interface, QWidget):

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setupUi(self)
        self.target_task = None
        

        self.bind_signals()
        self.init_widget_text()
        if cfg.get(cfg.resource_exist):
            self.List_widget.addItems(
                Get_Values_list_Option(maa_config_data.config_path, "task")
            )
            self.change_target_task()

    def bind_signals(self):
        signalBus.resource_exist.connect(self.change_target_task)
        signalBus.resource_exist.connect(self.update_task_list_passive)
        signalBus.update_task_list.connect(self.update_task_list_passive)
        self.daily_mode_radio.clicked.connect(lambda: self.change_layout("daily"))
        self.weekly_mode_radio.clicked.connect(lambda: self.change_layout("weekly"))
        self.monthly_mode_radio.clicked.connect(lambda: self.change_layout("monthly"))
        self.List_widget.itemClicked.connect(self.change_target_task)
        self.confirm_button.clicked.connect(self.save_speedrun_info)

    def change_target_task(self):
        """修改目标任务"""
        self.target_task_index = self.List_widget.currentIndex().row()
        if self.target_task_index == -1:
            self.target_task_index = 0

        try:
            title = maa_config_data.config["task"][self.target_task_index]["name"]
        except Exception:
            self.title_label.setText(
            ""
        )
            return
        self.title_label.setText(
            title
        )
        maa_config_data.config["task"][self.target_task_index]
        self.schedule_enabled = (
            maa_config_data.config["task"][self.target_task_index]
            .get("speedrun", {})
            .get("enabled", False)
        )
        self.schedule_data = (
            maa_config_data.config["task"][self.target_task_index]
            .get("speedrun", {})
            .get("schedule_time", datetime.now().strftime("%Y-%m-%d"))
        )
        self.schedule_time = (
            maa_config_data.config["task"][self.target_task_index]
            .get("speedrun", {})
            .get("schedule_time", datetime.now().strftime("%H:%M"))
        )
        self.last_run = (
            maa_config_data.config["task"][self.target_task_index]
            .get("speedrun", {})
            .get("last_run", "1970-01-01 00:00:00")
        )
    
        
        self.is_start.setChecked(self.schedule_enabled)
        self.schedule_mode = (
            maa_config_data.config["task"][self.target_task_index]
            .get("speedrun", {})
            .get("schedule_mode", "daily")
        )
        self.refresh_time = (
            maa_config_data.config["task"][self.target_task_index]
            .get("speedrun", {})
            .get("refresh_time", {"H": 0, "d": 0, "w": 0})
        )
        self.interval = (
            maa_config_data.config["task"][self.target_task_index]
            .get("speedrun", {})
            .get("interval", {"unit": 0, "item": 0, "loop_item": 0, "current_loop": 0})
        )


        print(
            f"任务{maa_config_data.config["task"][self.target_task_index]["name"]},index:{self.target_task_index}\n启用状态:{self.schedule_enabled}\n计划时间:{self.schedule_data}{self.schedule_time}\n计划模式:{self.schedule_mode}\n刷新时间:{self.refresh_time}\n间隔:{self.interval}"
        )
        self.is_start.setChecked(self.schedule_enabled)
        if self.schedule_mode == "daily":
            self.daily_mode_radio.setChecked(True)
            self.refresh_time_spinbox.setValue(self.refresh_time["H"])
        elif self.schedule_mode == "weekly":
            self.weekly_mode_radio.setChecked(True)
            self.weekly_mode_combox.setCurrentText(self.refresh_time["w"])
            self.refresh_time_spinbox.setValue(self.refresh_time["H"])

        elif self.schedule_mode == "monthly":
            self.monthly_mode_radio.setChecked(True)
            self.refresh_time_spinbox.setValue(self.refresh_time["d"])

        self.interval_input.setValue(self.interval["item"])
        self.interval_unit.setCurrentIndex(self.interval["unit"])
        self.loop_input.setValue(self.interval["current_loop"])
        self.date_label.setText(self.last_run)
    def save_speedrun_info(self):
        """保存计划任务信息"""
        if self.target_task_index is None:
            return

        # 获取当前UI设置的值

        speedrun_config = {
            "enabled": self.is_start.isChecked(),
            "schedule_mode": "daily" if self.daily_mode_radio.isChecked() else 
                           "weekly" if self.weekly_mode_radio.isChecked() else 
                           "monthly",
            "refresh_time": {
                "H": self.refresh_time_spinbox.value(),
                "d": self.refresh_time_mo_spinbox.value() if self.monthly_mode_radio.isChecked() else 1,
                "w": self.weekly_mode_combox.currentIndex() if self.weekly_mode_radio.isChecked() else 0
            },
            "interval": {# 单位: 0:分钟, 1:小时, 2:天
                "unit": self.interval_unit.currentIndex(),
                "item": self.interval_input.value(),
                "loop_item": self.loop_input.value(),
                "current_loop" : self.loop_input.value()
            },
            "last_run": self.last_run
        }

        # 更新配置数据
        if "speedrun" not in maa_config_data.config["task"][self.target_task_index]:
            maa_config_data.config["task"][self.target_task_index]["speedrun"] = {}
        maa_config_data.config["task"][self.target_task_index]["speedrun"].update(speedrun_config)
        Save_Config(maa_config_data.config_path, maa_config_data.config)
        
        # 显示保存成功提示
        InfoBar.success(
            title=self.tr("Success"),
            content=self.tr("Schedule settings saved successfully"),
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.BOTTOM_RIGHT,
            duration=2000,
            parent=self,
        )

    def init_widget_text(self):
        """初始化界面文本"""
        self.date_label.setText(self.tr("Start Date"))
        self.schedule_mode_title.setText(self.tr("Schedule Mode"))
        self.daily_mode_radio.setText(self.tr("Daily"))
        self.weekly_mode_radio.setText(self.tr("Weekly"))
        self.monthly_mode_radio.setText(self.tr("Monthly"))
        self.refresh_time_label.setText(self.tr("Refresh Time, Daily"))
        self.weekly_mode_combox.addItems(
            [
                self.tr("Monday"),
                self.tr("Tuesday"),
                self.tr("Wednesday"),
                self.tr("Thursday"),
                self.tr("Friday"),
                self.tr("Saturday"),
                self.tr("Sunday"),
            ]
        )
        self.refresh_time_unit_label.setText(self.tr("Hour"))
        self.interval_label.setText(self.tr("Interval"))
        self.interval_unit.addItems(
            [self.tr("Minutes"), self.tr("Hours"), self.tr("Days")]
        )
        self.loop_label.setText(self.tr("Loop"))
        self.loop_unit_label.setText(self.tr("Times"))
        self.confirm_button.setText(self.tr("Confirm"))
        self.is_start.setText(self.tr("Start Automatically"))
        self.refresh_time_mo_unit_label.setText(self.tr("Day")),
        self.loop_label.setText(self.tr("Loop item"))
        self.data_label1.setText(self.tr("Last Run"))
        #self.notic_label.setText(self.tr("The task will be executed at the specified time, and the interval will be executed for the specified number of times."))

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

            self.refresh_time_mo_spinbox.hide()
            self.refresh_time_mo_unit_label.hide()
        elif mode == "weekly":
            self.weekly_mode_combox.show()
            self.refresh_time_label.setText(self.tr("Refresh Time, Weekly"))
            self.refresh_time_mo_spinbox.hide()
            self.refresh_time_mo_unit_label.hide()

        elif mode == "monthly":
            self.weekly_mode_combox.hide()
            self.refresh_time_label.setText(self.tr("Refresh Time, Monthly"))
            self.refresh_time_mo_spinbox.show()
            self.refresh_time_mo_unit_label.show()