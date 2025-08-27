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
MFW-ChainFlow Assistant 计划任务逻辑
作者:overflow65537
"""

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt
from .UI_task_cooldown_interface import Ui_TaskCooldown_Interface
from ..common.config import cfg, Language
from ..common.signal_bus import signalBus
from ..utils.tool import Get_Values_list_Option, Save_Config
from qfluentwidgets import (
    InfoBar,
    InfoBarPosition,
)

from ..common.resource_config import (
    maa_config_data,
)
from ..common.typeddict import (
    RefreshTime,
    Interval,
    SpeedrunConfig,
    TaskItem,
    TaskItem,
)


class TaskCooldownInterface(Ui_TaskCooldown_Interface, QWidget):

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setupUi(self)
        self.target_task = None

        self.bind_signals()
        self.init_widget_text()
        self.init_notice()
        if cfg.get(cfg.resource_exist):
            self.resource_exist(True)

    def init_notice(self):
        """初始化通知标签"""
        notice = ""
        try:
            if cfg.get(cfg.language) is Language.CHINESE_SIMPLIFIED:
                with open(
                    "./MFW_resource/doc/task_cooldown_instructions_zh_cn.html",
                    "r",
                    encoding="utf-8",
                ) as f:
                    notice = f.read()
            elif cfg.get(cfg.language) is Language.CHINESE_TRADITIONAL:
                with open(
                    "./MFW_resource/doc/task_cooldown_instructions_zh_hk.html",
                    "r",
                    encoding="utf-8",
                ) as f:
                    notice = f.read()

            else:
                with open(
                    "./MFW_resource/doc/task_cooldown_instructions_en_us.html",
                    "r",
                    encoding="utf-8",
                ) as f:
                    notice = f.read()

        except Exception as e:
            print(f"Failed to load notice: {e}")
        self.notice_label.setText(notice)

    def bind_signals(self):
        """绑定信号槽函数"""
        signalBus.resource_exist.connect(self.resource_exist)
        signalBus.TaskCooldownPageClicked.connect(self.change_target_task)
        self.daily_mode_radio.clicked.connect(lambda: self.change_layout("daily"))
        self.weekly_mode_radio.clicked.connect(lambda: self.change_layout("weekly"))
        self.monthly_mode_radio.clicked.connect(lambda: self.change_layout("monthly"))
        self.List_widget.itemClicked.connect(self.change_target_task)
        self.confirm_button.clicked.connect(self.save_speedrun_info)
        signalBus.update_task_list.connect(self.update_task_list_passive)

    def resource_exist(self, status: bool):
        if status:
            self.List_widget.clear()
            self.List_widget.addItems(
                Get_Values_list_Option(maa_config_data.config_path, "task")
            )
            self.change_target_task()
        else:
            self.List_widget.clear()
            self.List_widget.addItem("No task found")
            self.List_widget.setEnabled(False)
            self.List_widget.setStyleSheet("color: red;")

    def change_target_task(self):
        """修改目标任务"""
        self.target_task_index = self.List_widget.currentIndex().row()
        if self.target_task_index == -1:
            self.target_task_index = 0

        tasks = maa_config_data.config.get("task", [])
        task = TaskItem()
        if self.target_task_index < len(tasks):
            task: TaskItem = tasks[self.target_task_index]

        title = task.get("name", "")

        self.title_label.setText(title)
        self.schedule_enabled: bool = task.get("speedrun", {}).get("enabled", False)
        self.last_run: str = task.get("speedrun", {}).get(
            "last_run", "1970-01-01 00:00:00"
        )

        self.is_start.setChecked(self.schedule_enabled)
        self.schedule_mode: str = task.get("speedrun", {}).get("schedule_mode", "daily")
        self.refresh_time: RefreshTime = task.get("speedrun", {}).get(
            "refresh_time", {"H": 0, "d": 0, "w": 0}
        )
        self.interval: Interval = task.get("speedrun", {}).get(
            "interval", {"unit": 0, "item": 0, "loop_item": 1, "current_loop": 1}
        )

        self.is_start.setChecked(self.schedule_enabled)
        if self.schedule_mode == "daily":
            self.daily_mode_radio.setChecked(True)
            self.refresh_time_spinbox.setValue(self.refresh_time.get("H", 0))
        elif self.schedule_mode == "weekly":
            self.weekly_mode_radio.setChecked(True)
            self.weekly_mode_combox.setCurrentText(self.refresh_time.get("w", 0))
            self.refresh_time_spinbox.setValue(self.refresh_time.get("H", 0))

        elif self.schedule_mode == "monthly":
            self.monthly_mode_radio.setChecked(True)
            self.refresh_time_spinbox.setValue(self.refresh_time.get("d", 0))

        self.interval_input.setValue(self.interval.get("item", 0))
        self.interval_unit.setCurrentIndex(self.interval.get("unit", 0))
        self.loop_input.setValue(self.interval.get("loop_item", 1))
        self.current_loop_input.setValue(self.interval.get("current_loop", 1))

        self.date_label.setText(self.last_run)

    def save_speedrun_info(self):
        """保存计划任务信息"""
        if self.target_task_index is None:
            return

        # 获取当前UI设置的值

        speedrun_config: SpeedrunConfig = {
            "enabled": self.is_start.isChecked(),
            "schedule_mode": (
                "daily"
                if self.daily_mode_radio.isChecked()
                else "weekly" if self.weekly_mode_radio.isChecked() else "monthly"
            ),
            "refresh_time": {
                "H": self.refresh_time_spinbox.value(),
                "d": (
                    self.refresh_time_mo_spinbox.value()
                    if self.monthly_mode_radio.isChecked()
                    else 1
                ),
                "w": (
                    self.weekly_mode_combox.currentIndex()
                    if self.weekly_mode_radio.isChecked()
                    else 0
                ),
            },
            "interval": {  # 单位: 0:分钟, 1:小时, 2:天
                "unit": self.interval_unit.currentIndex(),
                "item": self.interval_input.value(),
                "loop_item": self.loop_input.value(),
                "current_loop": self.current_loop_input.value(),
            },
            "last_run": self.last_run,
        }

        # 更新配置数据
        tasks = maa_config_data.config.get("task", [])
        if self.target_task_index < len(tasks):
            task = tasks[self.target_task_index]
            if "speedrun" not in task:
                task["speedrun"] = {}
            task["speedrun"].update(speedrun_config)
            maa_config_data.config["task"] = tasks

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
        self.refresh_time_mo_unit_label.setText(self.tr("Day"))
        self.current_loop_label.setText(self.tr("Loop item"))
        self.data_label1.setText(self.tr("Last Run"))

    def get_list_items(self) -> list[str]:
        """获取列表中所有项的文本"""
        return [
            item.text()
            for i in range(self.List_widget.count())
            if (item := self.List_widget.item(i)) is not None
        ]

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
