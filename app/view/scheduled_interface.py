from PyQt6.QtWidgets import QWidget
from .UI_scheduled_interface import Ui_Scheduled_Interface
from ..common.config import cfg
from ..common.signal_bus import signalBus
from ..utils.tool import (
    Get_Values_list_Option,
    Save_Config,
    Read_Config,
)
from ..components.choose_resource_button import CustomMessageBox
import os
import shutil
from ..utils.logger import logger


class ScheduledInterface(Ui_Scheduled_Interface, QWidget):
    MAIN_CONFIG_NAME = "Main"
    MAIN_CONFIG_PATH = os.path.join(os.getcwd(), "config", "maa_pi_config.json")

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setupUi(self)

        signalBus.update_task_list.connect(self.update_task_list_passive)

        self.initialize_config_combobox()
        self.List_widget.addItems(
            Get_Values_list_Option(cfg.get(cfg.Maa_config), "task")
        )
        self.Add_cfg_Button.clicked.connect(self.add_config)
        self.Delete_cfg_Button.clicked.connect(self.cfg_delete)
        self.Cfg_Combox.currentIndexChanged.connect(self.cfg_changed)
        self.add_res_button.clicked.connect(self.add_resource)
        self.set_config()

    def add_resource(self):
        w = CustomMessageBox(self)
        if w.exec():
            print(w.name_LineEdit.text())

    def initialize_config_combobox(self):
        """初始化配置下拉框"""
        config_name_list = list(cfg.get(cfg.maa_config_list))
        self.Cfg_Combox.addItems(config_name_list)

    def get_list_items(self):
        """获取列表中所有项的文本"""
        return [
            self.List_widget.item(i).text()
            for i in range(self.List_widget.count())
            if self.List_widget.item(i) is not None
        ]

    def set_config(self):
        """启动后自动加载当前配置"""
        config_path = cfg.get(cfg.Maa_config)
        config_dict = cfg.get(cfg.maa_config_list)
        result = [k for k, v in config_dict.items() if v == config_path]
        if result:
            self.Cfg_Combox.setCurrentText(result[0])

    def add_config(self):
        """添加新的配置"""
        config_name = self.Cfg_Combox.currentText()
        config_name_list = list(cfg.get(cfg.maa_config_list))

        if config_name in [self.MAIN_CONFIG_NAME, self.MAIN_CONFIG_NAME.lower()]:
            logger.info("不能添加主配置文件")
            cfg.set(cfg.Maa_config, self.MAIN_CONFIG_PATH)
        elif config_name in config_name_list:
            logger.info(f"{config_name}已存在")
            self.update_config_path(config_name)
        else:
            self.create_new_config(config_name)

        self.cfg_changed()

    def create_new_config(self, config_name):
        """创建新的配置文件"""
        config_data = Read_Config(cfg.get(cfg.Maa_config))
        self.Cfg_Combox.addItem(config_name)
        config_list = cfg.get(cfg.maa_config_list)

        config_path = os.path.join(
            os.getcwd(),
            "config",
            "config_manager",
            config_name,
            "config",
            "maa_pi_config.json",
        )
        logger.info(f"创建配置文件{config_name}于{config_path}")

        config_list[config_name] = config_path
        cfg.set(cfg.maa_config_list, config_list)
        cfg.set(cfg.Maa_config, config_path)

        # 创建初始配置文件
        data = {
            "adb": config_data["adb"],
            "controller": config_data["controller"],
            "gpu": -1,
            "resource": config_data["resource"],
            "task": [],
            "win32": {"_placeholder": 0},
        }
        Save_Config(cfg.get(cfg.Maa_config), data)

    def update_config_path(self, config_name):
        """更新当前配置路径"""
        config_path = os.path.join(
            os.getcwd(),
            "config",
            "config_manager",
            config_name,
            "config",
            "maa_pi_config.json",
        )
        cfg.set(cfg.Maa_config, config_path)

    def cfg_changed(self):
        """切换配置时刷新配置文件"""
        config_name = self.Cfg_Combox.currentText()

        if config_name in [self.MAIN_CONFIG_NAME, self.MAIN_CONFIG_NAME.lower()]:
            logger.info("切换主配置")
            cfg.set(cfg.Maa_config, self.MAIN_CONFIG_PATH)

            dev_path = os.path.join(os.getcwd(), "config", "maa_option.json")
            cfg.set(cfg.Maa_dev, dev_path)
        else:
            logger.info(f"切换到{config_name}配置")
            self.update_config_path(config_name)

            dev_path = os.path.join(
                os.getcwd(),
                "config",
                "config_manager",
                config_name,
                "config",
                "maa_option.json",
            )
            cfg.set(cfg.Maa_dev, dev_path)

        self.update_task_list()

    def cfg_delete(self):
        """删除当前选定的配置"""
        config_name = self.Cfg_Combox.currentText()
        config_name_list = list(cfg.get(cfg.maa_config_list))

        if config_name in [self.MAIN_CONFIG_NAME, self.MAIN_CONFIG_NAME.lower()]:
            logger.info("不能删除主配置文件")
        elif config_name in config_name_list:
            logger.info(f"删除配置文件{config_name}")
            self.delete_config_folder(config_name)
        else:
            logger.info(f"{config_name}不存在")
            self.Cfg_Combox.clear()
            self.Cfg_Combox.addItems(config_name_list)
            self.cfg_changed()

    def delete_config_folder(self, config_name):
        """删除配置文件夹"""
        config_list = cfg.get(cfg.maa_config_list)
        file_path = os.path.dirname(os.path.dirname(config_list[config_name]))
        shutil.rmtree(file_path)  # 删除配置文件目录
        logger.info(f"删除配置文件{file_path}成功")
        del config_list[config_name]
        cfg.set(cfg.maa_config_list, config_list)

        # 切换到主配置
        cfg.set(cfg.Maa_config, self.MAIN_CONFIG_NAME)
        self.refresh_combobox()

    def refresh_combobox(self):
        """刷新配置下拉框和任务列表"""
        config_name_list = list(cfg.get(cfg.maa_config_list))
        self.Cfg_Combox.clear()
        self.Cfg_Combox.addItems(config_name_list)
        self.cfg_changed()

    def update_task_list(self):
        """更新任务列表"""
        signalBus.update_task_list.emit()

    def update_task_list_passive(self):
        """更新任务列表(被动刷新)"""
        self.List_widget.clear()
        self.List_widget.addItems(
            Get_Values_list_Option(cfg.get(cfg.Maa_config), "task")
        )

    def get_task_list_widget(self):
        """获取任务列表控件中的项"""
        return [
            self.List_widget.item(i).text()
            for i in range(self.List_widget.count())
            if self.List_widget.item(i) is not None
        ]
