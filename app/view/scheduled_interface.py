from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt

from PyQt6.QtCore import QTimer, QDateTime
from PyQt6.QtGui import QIntValidator
from .UI_scheduled_interface import Ui_Scheduled_Interface
from ..common.config import cfg
from ..common.signal_bus import signalBus
from ..utils.tool import (
    Get_Values_list_Option,
    Save_Config,
)
from qfluentwidgets import (
    InfoBar,
    InfoBarPosition,
)
from ..components.choose_resource_button import CustomMessageBox
import os
import shutil

from datetime import datetime, timedelta
from copy import deepcopy
from ..utils.logger import logger
from ..common.maa_config_data import maa_config_data
import schedule
import asyncio


class ScheduledInterface(Ui_Scheduled_Interface, QWidget):
    tasker = {}
    task_need_update = False

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setupUi(self)

        signalBus.update_task_list.connect(self.update_task_list_passive)
        signalBus.switch_config.connect(self.switch_config)
        if cfg.get(cfg.resource_exist):
            self.initialize_config_combobox()
            self.List_widget.addItems(
                Get_Values_list_Option(maa_config_data.config_path, "task")
            )
            self.init_schedule()
        self.Add_cfg_Button.clicked.connect(self.add_config)
        self.Delete_cfg_Button.clicked.connect(self.cfg_delete)
        self.Cfg_Combox.currentIndexChanged.connect(self.cfg_changed)
        self.res_combox.currentTextChanged.connect(self.res_changed)
        self.add_res_button.clicked.connect(self.add_resource)
        self.delete_res_button.clicked.connect(self.res_delete)
        self.Trigger_Time_type.currentIndexChanged.connect(self.trigger_time_changed)
        self.confirm_button.clicked.connect(self.confirm_schedule)
        self.delete_button.clicked.connect(self.delete_schedule)
        self.use_res_combo.currentTextChanged.connect(self.use_res_changed)
        self.Trigger_interval.setValidator(QIntValidator(1, 999999))
        # asyncio.create_task(self.start_task_loop())

    async def start_task_loop(self):
        while True:
            self.task_need_update = False
            while not self.task_need_update:
                schedule.run_pending()
                await asyncio.sleep(1)

    def init_schedule(self):
        # 初始化定时任务
        schedule_data = cfg.get(cfg.schedule_task)
        trigger_interval_unit = {0: "hour", 1: "day", 2: "week"}
        for i in schedule_data:
            # 添加任务到 QListWidget
            if i.get("trigger_time_type") == 0:  # 一次性
                self.Schedule_list_widget.addItem(
                    f"{i.get('name')} "
                    + self.tr("Once")
                    + f" {i.get('trigger_time')} "
                    + f" {i.get('resource_name')} {i.get('config_name')}"
                )
            elif i.get("trigger_time_type") == 1:  # 循环
                self.Schedule_list_widget.addItem(
                    f"{i.get('name')} "
                    + self.tr("every")
                    + f" {i.get('trigger_interval')} "
                    + f" {trigger_interval_unit.get(i.get('trigger_interval_unit'))} "
                    + f" starting from {i.get('trigger_time')} "
                    + f" {i.get('resource_name')} {i.get('config_name')}"
                )

            # 启动定时器
            # self.tasker_timer(i)

    def use_res_changed(self):
        # 计划任务选择资源更新
        self.use_cfg_combo.clear()
        self.use_cfg_combo.addItems(maa_config_data.config_name_list)

    def confirm_schedule(self):
        # 确认定时任务
        name = self.Schedule_name_edit.text()
        trigger_time_type = self.Trigger_Time_type.currentIndex()
        trigger_time = self.Trigger_date_edit.dateTime().toString("yyyy-MM-dd hh:mm:ss")
        trigger_interval = self.Trigger_interval.text()
        trigger_interval_unit = self.Trigger_WeekMonth.currentIndex()
        resource_name = self.use_res_combo.currentText()
        config_name = self.use_cfg_combo.currentText()
        if not name or not trigger_time or not resource_name or not config_name:
            self.show_error(self.tr("Please fill in all fields"))
            return
        if name in [i.get("name") for i in cfg.get(cfg.schedule_task)]:
            self.show_error(self.tr("The name already exists"))
            return
        if trigger_time_type == 0:  # 一次性
            trigger_data = {
                "name": name,
                "trigger_time_type": trigger_time_type,
                "trigger_time": trigger_time,
                "trigger_interval": -1,
                "trigger_interval_unit": -1,
                "resource_name": resource_name,
                "config_name": config_name,
            }
            self.Schedule_list_widget.addItem(
                f"{name} "
                + self.tr("Once")
                + f" {trigger_time} "
                + f" {resource_name} {config_name}"
            )
            tasker_data = cfg.get(cfg.schedule_task)
            tasker_data.append(trigger_data)
            cfg.set(cfg.schedule_task, tasker_data)
        elif trigger_time_type == 1:  # 循环
            if not trigger_interval:
                self.show_error(self.tr("Please enter the interval"))
                return
            trigger_data = {
                "name": name,
                "trigger_time_type": trigger_time_type,
                "trigger_time": trigger_time,
                "trigger_interval": int(trigger_interval),
                "trigger_interval_unit": trigger_interval_unit,
                "resource_name": resource_name,
                "config_name": config_name,
            }
            self.Schedule_list_widget.addItem(
                f"{name} "
                + self.tr("every")
                + f" {trigger_interval} "
                + f" {trigger_interval_unit} "
                + f" {trigger_time} "
                + f" {resource_name} {config_name}"
            )
            tasker_data = cfg.get(cfg.schedule_task)
            tasker_data.append(trigger_data)
            cfg.set(cfg.schedule_task, tasker_data)
        logger.info(f" {trigger_data} 定时任务添加成功")
        cfg.set(cfg.force_update, not cfg.get(cfg.force_update))

    def delete_schedule(self):
        # 删除定时任务
        print("删除定时任务")
        schedule_data = cfg.get(cfg.schedule_task)
        for i in schedule_data:
            if (
                i.get("name")
                == self.Schedule_list_widget.currentItem().text().split()[0]
            ):
                self.Schedule_list_widget.takeItem(
                    self.Schedule_list_widget.currentRow()
                )
                tasker_data = cfg.get(cfg.schedule_task)
                tasker_data.remove(i)
                cfg.set(cfg.schedule_task, tasker_data)
                logger.info(f" {i.get('name')} 定时任务删除成功")
                cfg.set(cfg.force_update, not cfg.get(cfg.force_update))

    def trigger_time_changed(self, index):
        print(self.Trigger_WeekMonth.currentIndex())
        if index == 0:  # 一次性
            self.Trigger_interval.hide()
            self.Trigger_interval_title.hide()
            self.Trigger_WeekMonth.hide()
            self.Trigger_date_edit.show()
        elif index == 1:  # 循环
            self.Trigger_interval.show()
            self.Trigger_interval_title.show()
            self.Trigger_WeekMonth.show()

    """def tasker_timer(
        self,
        tasker_data: dict = {
            "name": "",  # 任务名称
            "trigger_time_type": 0,  # 触发类型 0:一次性 1:循环
            "trigger_time": "",  # 触发时间
            "trigger_interval": 0,  # 触发周期 一次性触发时无效
            "trigger_interval_unit": 0,  # 触发周期单位 0:小时 1:天 2:周
            "resource_name": "",  # 资源名称
            "config_name": "",  # 配置名称
        },
    ):
        


        task_name = tasker_data.get("name")
            if tasker_data.get("trigger_time_type") == 0:  # 一次性

                self.tasker[task_name] = QTimer()
                self.tasker[task_name].timeout.connect(
                    lambda: self.start_task_with_config(deepcopy(tasker_data))
                )

                # 计算当前时间和触发时间的差值
                trigger_datetime = QDateTime.fromString(
                    tasker_data.get("trigger_time"), "yyyy-MM-dd hh:mm:ss"
                )
                now = QDateTime.currentMSecsSinceEpoch()
                if now < trigger_datetime.toMSecsSinceEpoch():
                    logger.debug(f" {task_name} 定时器启动")
                    timer = trigger_datetime.toMSecsSinceEpoch() - now
                    self.tasker[task_name].start(timer)
                else:
                    logger.warning(f" {task_name} 已过期")
                    return
            elif tasker_data.get("trigger_time_type") == 1:  # 循环

                def start_task_and_reschedule():
                    self.start_task_with_config(deepcopy(tasker_data))
                    reschedule_timer()

                def reschedule_timer():
                    interval = tasker_data.get("trigger_interval")
                    unit = tasker_data.get("trigger_interval_unit")
                    initial_trigger_time = QDateTime.fromString(
                        tasker_data.get("trigger_time"), "yyyy-MM-dd hh:mm:ss"
                    ).toPyDateTime()

                    # 计算下一个触发时间
                    now = datetime.now()
                    next_trigger_time = initial_trigger_time
                    while next_trigger_time < now:
                        if unit == 0:  # 小时
                            next_trigger_time += timedelta(hours=interval)
                        elif unit == 1:  # 天
                            next_trigger_time += timedelta(days=interval)
                        elif unit == 2:  # 周
                            next_trigger_time += timedelta(weeks=interval)

                    next_trigger_time_msecs = QDateTime(
                        next_trigger_time
                    ).toMSecsSinceEpoch()
                    now_msecs = QDateTime.currentMSecsSinceEpoch()
                    timer_interval = next_trigger_time_msecs - now_msecs

                    self.tasker[task_name].start(timer_interval)

                self.tasker[task_name] = QTimer()
                self.tasker[task_name].timeout.connect(start_task_and_reschedule)

                # 启动时立即运行任务并重新安排定时器
                reschedule_timer()

        def start_task_with_config(self, tasker_data):
            # 启动任务并切换配置
            logger.debug(f" {tasker_data.get('name')} 启动")
            signalBus.switch_config.emit(
                {
                    "resource_name": tasker_data.get("resource_name"),
                    "config_name": tasker_data.get("config_name"),
                }
            )
            signalBus.start_task_inmediately.emit()"""

    def add_resource(self):
        """添加资源"""
        w = CustomMessageBox(self)
        if w.exec():
            logger.debug(f"添加资源{w.name_data}")
            self.res_combox.clear()
            self.Cfg_Combox.clear()
            logger.debug("add_resource发送信号")
            signalBus.resource_exist.emit(True)
            self.initialize_config_combobox()
            self.res_combox.setCurrentText(w.name_data)
            self.Cfg_Combox.setCurrentText("default")

    def initialize_config_combobox(self):
        """初始化配置下拉框"""
        self.Cfg_Combox.addItems(maa_config_data.config_name_list)
        self.Cfg_Combox.setCurrentText(maa_config_data.config_name)
        self.res_combox.addItems(maa_config_data.resource_name_list)
        self.res_combox.setCurrentText(maa_config_data.resource_name)
        self.Trigger_Time_type.addItems([self.tr("Once"), self.tr("Loop")])
        self.Trigger_WeekMonth.addItems(
            [self.tr("hour"), self.tr("day"), self.tr("week")]
        )
        self.use_res_combo.addItems(maa_config_data.resource_name_list)
        self.use_cfg_combo.addItems(maa_config_data.config_name_list)

    def get_list_items(self) -> list[str]:
        """获取列表中所有项的文本"""
        return [
            item.text()
            for i in range(self.List_widget.count())
            if (item := self.List_widget.item(i)) is not None
        ]

    def switch_config(self, data_dict: dict = {}) -> None:
        """主动切换配置"""

        if data_dict.get("resource_name", False) and data_dict.get(
            "config_name", False
        ):
            logger.debug(f"主动切换配置{data_dict}")
            self.res_combox.setCurrentText(data_dict.get("resource_name"))
            self.Cfg_Combox.setCurrentText(data_dict.get("config_name"))

        signalBus.start_task_inmediately.emit()

    def add_config(self, config_name=None):
        """添加新的配置"""
        if cfg.get(cfg.resource_exist):
            if config_name is None or type(config_name) in [int, bool]:
                config_name = self.Cfg_Combox.currentText()

            if config_name in ["default", "default".lower()]:
                logger.warning(" 不能添加主配置文件")
                cfg.set(cfg.maa_config_name, "default")
                maa_config_data.config_path = os.path.join(
                    os.getcwd(),
                    "config",
                    maa_config_data.resource_name,
                    "default",
                    "maa_pi_config.json",
                )
                cfg.set(cfg.maa_config_path, maa_config_data.config_path)
                maa_config_data.config_name = "default"

            elif config_name in maa_config_data.config_name_list:
                logger.warning(f" {config_name} 已存在")
                self.update_config_path(config_name)
            else:
                logger.debug(f" 创建 {config_name} 配置")
                self.create_new_config(config_name)

            self.cfg_changed()
        else:
            self.show_error(self.tr("Please add resources first."))

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

    def create_new_config(self, config_name):
        """创建新的配置文件"""
        self.Cfg_Combox.addItem(config_name)
        config_path = os.path.join(
            os.getcwd(),
            "config",
            maa_config_data.resource_name,
            config_name,
            "maa_pi_config.json",
        )

        logger.debug(f" 创建配置文件 {config_name} 于 {config_path}")

        maa_config_data.config_data[maa_config_data.resource_name][
            config_name
        ] = config_path
        cfg.set(cfg.maa_config_list, maa_config_data.config_data)
        cfg.set(cfg.maa_config_name, config_name)
        cfg.set(cfg.maa_config_path, config_path)
        maa_config_data.config_name = config_name
        maa_config_data.config_path = config_path
        maa_config_data.config_name_list = list(
            maa_config_data.config_data[maa_config_data.resource_name]
        )

        # 创建初始配置文件
        maa_config_data.config["task"] = []
        Save_Config(maa_config_data.config_path, maa_config_data.config)

    def update_config_path(self, config_name):
        """更新当前配置路径"""
        config_path = os.path.join(
            os.getcwd(),
            "config",
            maa_config_data.resource_name,
            config_name,
            "maa_pi_config.json",
        )
        cfg.set(cfg.maa_config_path, config_path)
        cfg.set(cfg.maa_config_name, config_name)
        maa_config_data.config_name = config_name
        maa_config_data.config_path = config_path

    def cfg_changed(self, config_name=None):
        """切换配置时刷新配置文件"""
        if config_name is None or type(config_name) in [int, bool]:
            config_name = self.Cfg_Combox.currentText()
        if config_name == "":
            return
        elif config_name in ["Default", "default".lower()]:
            logger.info(" 切换主配置")

            cfg.set(cfg.maa_config_name, "default")
            maa_config_path = os.path.join(
                os.getcwd(),
                "config",
                maa_config_data.resource_name,
                config_name,
                "maa_pi_config.json",
            )
            cfg.set(cfg.maa_config_path, maa_config_path)
            maa_config_data.config_name = "default"
            maa_config_data.config_path = maa_config_path
            self.use_cfg_combo.clear()
            self.use_cfg_combo.addItems(maa_config_data.config_name_list)
            self.use_res_combo.clear()
            self.use_res_combo.addItems(maa_config_data.resource_name_list)

        else:
            logger.info(f" 切换到 {config_name} 配置")
            self.update_config_path(config_name)

        self.update_task_list()
        logger.debug("cfg_changed发送信号")
        signalBus.resource_exist.emit(True)
        signalBus.title_changed.emit()
        signalBus.update_finished_action.emit()

    def res_changed(self, resource_name: str = ""):
        """资源下拉框改变时触发"""
        if resource_name == "" or None:
            resource_name = self.res_combox.currentText()

        cfg.set(cfg.maa_resource_name, resource_name)
        maa_config_data.resource_name = resource_name

        cfg.set(cfg.maa_config_name, "default")
        main_config_path = os.path.join(
            os.getcwd(),
            "config",
            maa_config_data.resource_name,
            "default",
            "maa_pi_config.json",
        )
        cfg.set(cfg.maa_config_path, main_config_path)
        maa_config_data.config_name = "default"
        maa_config_data.config_path = main_config_path

        maa_config_data.resource_path = maa_config_data.resource_data[
            maa_config_data.resource_name
        ]
        cfg.set(cfg.maa_resource_path, maa_config_data.resource_path)
        maa_config_data.config_name_list = list(
            maa_config_data.config_data[maa_config_data.resource_name]
        )  # 配置名称列表
        maa_config_data.resource_name_list = list(
            maa_config_data.resource_data
        )  # 资源名称列表
        logger.info(f" 切换到 {resource_name} 资源")
        self.refresh_combobox()

    def res_delete(self):
        """删除当前选定的资源"""
        if not cfg.get(cfg.resource_exist):
            self.show_error(self.tr("Please add resources first."))
            return

        resource_name = self.res_combox.currentText()
        logger.info(f" 删除资源 {resource_name}")

        # 删除资源文件夹
        file_path = os.path.join(os.getcwd(), "config", resource_name)
        shutil.rmtree(file_path)  # 删除资源目录
        logger.info(f" 删除资源 {file_path} 成功")
        del maa_config_data.resource_data[resource_name]
        del maa_config_data.config_data[resource_name]
        cfg.set(cfg.maa_resource_list, maa_config_data.resource_data)
        cfg.set(cfg.maa_config_list, maa_config_data.config_data)

        if not maa_config_data.resource_data and not maa_config_data.config_data:
            cfg.set(cfg.resource_exist, False)
            self.res_combox.clear()
            self.Cfg_Combox.clear()
            self.List_widget.clear()
            cfg.set(cfg.maa_config_name, "")
            cfg.set(cfg.maa_config_path, "")
            cfg.set(cfg.maa_resource_name, "")
            cfg.set(cfg.maa_resource_path, "")
            signalBus.resource_exist.emit(False)
        else:
            self.res_combox.removeItem(self.res_combox.currentIndex())
            maa_config_data.config_name_list = list(
                maa_config_data.config_data[maa_config_data.resource_name]
            )  # 配置名称列表
            maa_config_data.resource_name_list = list(
                maa_config_data.resource_data
            )  # 资源名称列表
            self.refresh_combobox()

    def cfg_delete(self, config_name=None):
        """删除当前选定的配置"""
        if not cfg.get(cfg.resource_exist):
            self.show_error(self.tr("Please add resources first."))
            return

        if config_name is None or type(config_name) in [int, bool]:
            config_name = self.Cfg_Combox.currentText()

        config_index = self.Cfg_Combox.currentIndex()

        if config_name in ["default", "default".lower()]:
            logger.warning(" 不能删除主配置文件")
        elif config_name == "" or None:
            return
        elif config_name in maa_config_data.config_name_list:
            logger.info(f" 删除配置文件 {config_name}")
            self.Cfg_Combox.removeItem(config_index)
            # 删除配置文件夹
            file_path = os.path.dirname(maa_config_data.config_path)
            shutil.rmtree(file_path)  # 删除配置文件目录
            logger.info(f" 删除配置文件 {file_path}")
            del maa_config_data.config_data[maa_config_data.resource_name][config_name]
            cfg.set(cfg.maa_config_list, maa_config_data.config_data)
            # 切换到主配置
            cfg.set(cfg.maa_config_name, "default")
            main_config_path = os.path.join(
                os.getcwd(),
                "config",
                maa_config_data.resource_name,
                "default",
                "maa_pi_config.json",
            )
            cfg.set(cfg.maa_config_path, main_config_path)
            maa_config_data.config_name = "default"
            maa_config_data.config_path = main_config_path
            maa_config_data.config_name_list = list(
                maa_config_data.config_data[maa_config_data.resource_name]
            )  # 配置名称列表
            self.refresh_combobox()
        else:
            logger.info(f" {config_name} 不存在")
            self.Cfg_Combox.clear()
            self.Cfg_Combox.addItems(maa_config_data.config_name_list)
            self.cfg_changed()

    def refresh_combobox(self):
        """刷新配置下拉框和任务列表"""
        self.Cfg_Combox.currentIndexChanged.disconnect()
        self.Cfg_Combox.clear()
        self.Cfg_Combox.currentIndexChanged.connect(self.cfg_changed)
        self.Cfg_Combox.addItems(maa_config_data.config_name_list)

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
