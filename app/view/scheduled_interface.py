from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt
from .UI_scheduled_interface import Ui_Scheduled_Interface
from ..common.config import cfg
from ..common.signal_bus import signalBus
from ..utils.tool import (
    Get_Values_list_Option,
    Save_Config,
    Read_Config,
)
from qfluentwidgets import (
    InfoBar,
    InfoBarPosition,
)
from ..components.choose_resource_button import CustomMessageBox
import os
import shutil
from ..utils.logger import logger
from ..common.maa_config_data import maa_config_data, init_maa_config_data


class ScheduledInterface(Ui_Scheduled_Interface, QWidget):

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setupUi(self)

        signalBus.update_task_list.connect(self.update_task_list_passive)
        if cfg.get(cfg.resource_exist):
            self.initialize_config_combobox()
            self.List_widget.addItems(
                Get_Values_list_Option(maa_config_data.config_path, "task")
            )
        self.Add_cfg_Button.clicked.connect(self.add_config)
        self.Delete_cfg_Button.clicked.connect(self.cfg_delete)
        self.Cfg_Combox.currentIndexChanged.connect(self.cfg_changed)
        self.add_res_button.clicked.connect(self.add_resource)
        self.res_combox.currentIndexChanged.connect(self.res_changed)
        self.delete_res_button.clicked.connect(self.res_delete)

    def add_resource(self):
        """添加资源"""
        w = CustomMessageBox(self)
        if w.exec():
            logger.debug(f"scheduled_interface.py:添加资源{w.name_data}")
            self.res_combox.clear()
            self.Cfg_Combox.clear()
            init_maa_config_data(True)
            self.initialize_config_combobox()
            self.res_combox.setCurrentText(w.name_data)

    def initialize_config_combobox(self):
        """初始化配置下拉框"""
        self.Cfg_Combox.addItems(maa_config_data.config_name_list)
        self.Cfg_Combox.setCurrentText(maa_config_data.config_name)
        self.res_combox.addItems(maa_config_data.resource_name_list)
        self.res_combox.setCurrentText(maa_config_data.resource_name)

    def get_list_items(self):
        """获取列表中所有项的文本"""
        return [
            self.List_widget.item(i).text()
            for i in range(self.List_widget.count())
            if self.List_widget.item(i) is not None
        ]

    def add_config(self):
        """添加新的配置"""
        if cfg.get(cfg.resource_exist):
            config_name = self.Cfg_Combox.currentText()

            if config_name in ["default", "default".lower()]:
                logger.warning("scheduled_interface.py:不能添加主配置文件")
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
                logger.warning(f"scheduled_interface.py:{config_name}已存在")
                self.update_config_path(config_name)
            else:
                logger.debug(f"scheduled_interface.py:创建{config_name}配置")
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

        logger.debug(f"scheduled_interface.py:创建配置文件{config_name}于{config_path}")

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

    def cfg_changed(self):
        """切换配置时刷新配置文件"""
        config_name = self.Cfg_Combox.currentText()

        if config_name in ["Default", "default".lower()]:
            logger.info("scheduled_interface.py:切换主配置")

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
            logger.info(f"scheduled_interface.py:切换到{config_name}配置")
            self.update_config_path(config_name)

        self.update_task_list()

    def res_changed(self):
        """资源下拉框改变时触发"""
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
        logger.info(f"scheduled_interface.py:切换到{resource_name}资源")
        signalBus.resource_exist.emit(True)
        self.refresh_combobox()

    def res_delete(self):
        """删除当前选定的资源"""
        resource_name = self.res_combox.currentText()
        resource_index = self.res_combox.currentIndex()
        logger.info(f"scheduled_interface.py:删除资源{resource_name}")
        if len(maa_config_data.resource_name_list) == 1:
            cfg.set(cfg.resource_exist, False)
            self.res_combox.clear()
            self.Cfg_Combox.clear()
            self.List_widget.clear()
            logger.info("scheduled_interface.py:删除最后一个资源")
        self.res_combox.removeItem(resource_index)

        # 删除资源文件夹
        file_path = os.path.join(os.getcwd(), "config", resource_name)
        shutil.rmtree(file_path)  # 删除资源目录
        logger.info(f"scheduled_interface.py:删除资源{file_path}成功")
        del maa_config_data.resource_data[resource_name]
        del maa_config_data.config_data[resource_name]
        cfg.set(cfg.maa_resource_list, maa_config_data.resource_data)
        cfg.set(cfg.maa_config_list, maa_config_data.config_data)
        if maa_config_data.resource_data == {} and maa_config_data.config_data == {}:
            signalBus.resource_exist.emit(False)
        else:
            maa_config_data.config_name_list = list(
                maa_config_data.config_data[maa_config_data.resource_name]
            )  # 配置名称列表
            maa_config_data.resource_name_list = list(
                maa_config_data.resource_data
            )  # 资源名称列表
            self.refresh_combobox()

    def cfg_delete(self):
        """删除当前选定的配置"""
        config_name = self.Cfg_Combox.currentText()
        config_index = self.Cfg_Combox.currentIndex()

        if config_name in ["default", "default".lower()]:
            logger.warning("scheduled_interface.py:不能删除主配置文件")
        elif config_name == "" or None:
            return
        elif config_name in maa_config_data.config_name_list:
            logger.info(f"scheduled_interface.py:删除配置文件{config_name}")
            self.Cfg_Combox.removeItem(config_index)
            # 删除配置文件夹
            file_path = os.path.dirname(maa_config_data.config_path)
            shutil.rmtree(file_path)  # 删除配置文件目录
            logger.info(f"scheduled_interface.py:删除配置文件{file_path}")
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
            cfg.set(cfg.maa_config_path, maa_config_data.config_path)
            maa_config_data.config_name = "default"
            maa_config_data.config_path = main_config_path
            maa_config_data.config_name_list = list(
                maa_config_data.config_data[maa_config_data.resource_name]
            )  # 配置名称列表
            self.refresh_combobox()
        else:
            logger.info(f"scheduled_interface.py:{config_name}不存在")
            self.Cfg_Combox.clear()
            self.Cfg_Combox.addItems(maa_config_data.config_name_list)
            self.cfg_changed()

    def refresh_combobox(self):
        """刷新配置下拉框和任务列表"""
        self.Cfg_Combox.clear()
        self.Cfg_Combox.addItems(maa_config_data.config_name_list)
        self.cfg_changed()

    def update_task_list(self):
        """更新任务列表"""
        signalBus.update_task_list.emit()

    def update_task_list_passive(self):
        """更新任务列表(被动刷新)"""
        self.List_widget.clear()
        self.List_widget.addItems(
            Get_Values_list_Option(maa_config_data.config_path, "task")
        )

    def get_task_list_widget(self):
        """获取任务列表控件中的项"""
        return [
            self.List_widget.item(i).text()
            for i in range(self.List_widget.count())
            if self.List_widget.item(i) is not None
        ]
