from PyQt6.QtWidgets import QWidget
from .UI_scheduled_interface import Ui_Scheduled_Interface
from ..common.config import cfg
from ..utils.tool import (
    Get_Values_list_Option,
    Save_Config,
    Read_Config,
)
import os
from ..view.task_interface import TaskInterface


class ScheduledInterface(Ui_Scheduled_Interface, QWidget):

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.setupUi(self)
        config_name_list = list(cfg.get(cfg.maa_config_list))
        self.Cfg_Combox.addItems(config_name_list)
        self.List_widget.addItems(
            Get_Values_list_Option(cfg.get(cfg.Maa_config), "task")
        )
        self.Add_cfg_Button.clicked.connect(self.add_config)

    def add_config(self):
        config_name = self.Cfg_Combox.currentText()
        config_name_list = list(cfg.get(cfg.maa_config_list))
        if config_name in config_name_list:
            pass
            print(f"{config_name}已存在")
        else:
            config_data = Read_Config(cfg.get(cfg.Maa_config))
            config_list = cfg.get(cfg.maa_config_list)
            config_path = os.path.join(
                os.getcwd(),
                "config",
                "config_manager",
                config_name,
                "config",
                "maa_pi_config.json",
            )
            print(f"创建配置文件{config_name}于{config_path}")
            config_list[config_name] = config_path
            cfg.set(cfg.maa_config_list, config_list)
            main_config = cfg.get(cfg.Maa_config)
            main_config = config_path
            cfg.set(cfg.Maa_config, main_config)
            # 创建初始配置文件

            print(config_data["adb"])
            data = {
                "adb": config_data["adb"],
                "controller": config_data["controller"],
                "gpu": -1,
                "resource": config_data["resource"],
                "task": [],
                "win32": {"_placeholder": 0},
            }
            Save_Config(cfg.get(cfg.Maa_config), data)
            self.List_widget.clear()
            TaskInterface(self).Task_List.clear()

    def refresh_list(self):
        # 刷新列表
        self.List_widget.addItems(
            Get_Values_list_Option(cfg.get(cfg.Maa_config), "task")
        )
        TaskInterface(self).Task_List.addItems(
            Get_Values_list_Option(cfg.get(cfg.Maa_config), "task")
        )
