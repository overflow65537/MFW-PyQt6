from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QTimer
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
from ..utils.logger import logger
from ..common.maa_config_data import maa_config_data


class ScheduledInterface(Ui_Scheduled_Interface, QWidget):
    tasker = {}

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
        self.Add_cfg_Button.clicked.connect(self.add_config)
        self.Delete_cfg_Button.clicked.connect(self.cfg_delete)
        self.Cfg_Combox.currentTextChanged.connect(self.cfg_changed)
        self.res_combox.currentTextChanged.connect(self.res_changed)
        self.add_res_button.clicked.connect(self.add_resource)
        self.delete_res_button.clicked.connect(self.res_delete)
        self.Trigger_Time_type.currentIndexChanged.connect(self.trigger_time_changed)
        self.Trigger_date_edit.dateTimeChanged.connect(self.trigger_date_changed)
        self.Trigger_interval.setValidator(QIntValidator(1, 999999))

    def trigger_date_changed(self, date):
        print(date)

    def trigger_time_changed(self, index):
        if index == 0:  # 一次性
            self.Trigger_interval.hide()
            self.Trigger_interval_title.hide()
            self.Trigger_interval_title2.hide()
            self.Trigger_WeekMonth.hide()
            self.Trigger_time.hide()
            self.Trigger_WeekMonth.clear()
        elif index == 1:  # 每天
            self.Trigger_interval.show()
            self.Trigger_interval_title.show()
            self.Trigger_interval_title2.show()
            self.Trigger_interval_title2.setText(self.tr("Dalay"))
            self.Trigger_WeekMonth.clear()
            self.Trigger_WeekMonth.hide()
            self.Trigger_time.show()

        elif index == 2:  # 每周
            self.Trigger_interval.show()
            self.Trigger_interval_title.show()
            self.Trigger_interval_title2.show()
            self.Trigger_interval_title2.setText(self.tr("Weekly"))
            self.Trigger_time.hide()
            self.Trigger_WeekMonth.show()
            self.Trigger_WeekMonth.clear()
            self.Trigger_WeekMonth.addItems(
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
        elif index == 3:  # 每月
            self.Trigger_interval.show()
            self.Trigger_interval_title.show()
            self.Trigger_interval_title2.show()
            self.Trigger_interval_title2.setText(self.tr("Monthly"))
            self.Trigger_time.hide()
            self.Trigger_WeekMonth.show()
            self.Trigger_WeekMonth.clear()
            self.Trigger_WeekMonth.addItems(
                [
                    self.tr("1st"),
                    self.tr("2nd"),
                    self.tr("3rd"),
                    self.tr("4th"),
                    self.tr("5th"),
                    self.tr("6th"),
                    self.tr("7th"),
                    self.tr("8th"),
                    self.tr("9th"),
                    self.tr("10th"),
                    self.tr("11th"),
                    self.tr("12th"),
                    self.tr("13th"),
                    self.tr("14th"),
                    self.tr("15th"),
                    self.tr("16th"),
                    self.tr("17th"),
                    self.tr("18th"),
                    self.tr("19th"),
                    self.tr("20th"),
                    self.tr("21st"),
                    self.tr("22nd"),
                    self.tr("23rd"),
                    self.tr("24th"),
                    self.tr("25th"),
                    self.tr("26th"),
                    self.tr("27th"),
                    self.tr("28th"),
                    self.tr("29th"),
                    self.tr("30th"),
                    self.tr("31st"),
                ]
            )

    def tasker_timer(
        self,
        tasker_data: dict = {
            "name": "",
            "start_time": 0,
            "trigger_time_type": 0,
            "trigger_interval": 0,
            "trigger_week_month": 0,
            "resource_name": "",
            "config_name": "",
        },
    ):
        if tasker_data.get("trigger_time_type", False) == 0:  # 一次性

            self.tasker[tasker_data.get("name")] = QTimer()
            self.tasker[tasker_data.get("name")].timeout.connect(
                lambda: self.tasker_timer(tasker_data)
            )
            self.tasker[tasker_data.get("name")].start(
                tasker_data.get("trigger_interval") * 1000
            )

    def add_resource(self):
        """添加资源"""
        w = CustomMessageBox(self)
        if w.exec():
            logger.debug(f"添加资源{w.name_data}")
            self.res_combox.clear()
            self.Cfg_Combox.clear()
            logger.debug("add_resource发送信号")
            self.Cfg_Combox.currentTextChanged.disconnect(self.cfg_changed)
            self.res_combox.currentTextChanged.disconnect(self.res_changed)
            signalBus.resource_exist.emit(True)
            self.initialize_config_combobox()
            self.res_combox.setCurrentText(w.name_data)
            self.Cfg_Combox.setCurrentText("default")
            self.Cfg_Combox.currentTextChanged.connect(self.cfg_changed)
            self.res_combox.currentTextChanged.connect(self.res_changed)

    def initialize_config_combobox(self):
        """初始化配置下拉框"""
        self.Cfg_Combox.addItems(maa_config_data.config_name_list)
        self.Cfg_Combox.setCurrentText(maa_config_data.config_name)
        self.res_combox.addItems(maa_config_data.resource_name_list)
        self.res_combox.setCurrentText(maa_config_data.resource_name)
        self.Trigger_Time_type.addItems(
            [self.tr("Once"), self.tr("Daily"), self.tr("Weekly"), self.tr("Monthly")]
        )

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

    def add_config(self, config_name=None):
        """添加新的配置"""
        if cfg.get(cfg.resource_exist):
            if config_name is None:
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
        if config_name is None:
            config_name = self.Cfg_Combox.currentText()
        elif config_name == "":
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

        if config_name is None:
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
        self.Cfg_Combox.currentTextChanged.disconnect()
        self.Cfg_Combox.clear()
        self.Cfg_Combox.currentTextChanged.connect(self.cfg_changed)
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
