from PyQt6.QtWidgets import QWidget
from .UI_scheduled_interface import Ui_Scheduled_Interface
from ..common.config import cfg
from ..common.signal_bus import signalBus
from ..utils.tool import (
    Get_Values_list_Option,
    Save_Config,
    Read_Config,
)
import os
import shutil


class ScheduledInterface(Ui_Scheduled_Interface, QWidget):

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setupUi(self)

        signalBus.update_task_list.connect(self.update_task_list)


        config_name_list = list(cfg.get(cfg.maa_config_list))
        self.Cfg_Combox.addItems(config_name_list)
        self.List_widget.addItems(
            Get_Values_list_Option(cfg.get(cfg.Maa_config), "task")
        )
        self.Add_cfg_Button.clicked.connect(self.add_config)
        self.Delete_cfg_Button.clicked.connect(self.cfg_delete)
        self.Cfg_Combox.currentIndexChanged.connect(self.cfg_changed)

    def get_list_items(self):
        items = []
        for i in range(self.List_widget.count()):
            item = self.List_widget.item(i)
            if item is not None:
                items.append(item.text())  # 获取项的文本并添加到列表中
        return items

    def set_config(self):
        # 启动后自动加载当前配置
        config_name = cfg.get(cfg.Maa_config)
        if config_name in ["Main", "main"]:
            print("加载主配置")
            self.Cfg_Combox.setCurrentText("Main")
        else:
            print("加载配置")
            self.Cfg_Combox.setCurrentText(config_name)
            self.cfg_changed()

    def add_config(self):
        config_name = self.Cfg_Combox.currentText()
        config_name_list = list(cfg.get(cfg.maa_config_list))
        print(config_name)
        if config_name in ["Main", "main"]:
            print("不能添加主配置文件")
            config_path = os.path.join(
                os.getcwd(),
                "config",
                "maa_pi_config.json",
            )
            main_config = cfg.get(cfg.Maa_config)
            main_config = config_path
            cfg.set(cfg.Maa_config, main_config)

        elif config_name in config_name_list:
            print(f"{config_name}已存在")
            config_path = os.path.join(
                os.getcwd(),
                "config",
                "config_manager",
                config_name,
                "config",
                "maa_pi_config.json",
            )
            main_config = cfg.get(cfg.Maa_config)
            main_config = config_path
            cfg.set(cfg.Maa_config, main_config)

        else:
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

            self.cfg_changed()

    def cfg_changed(self):
        # 切换配置时刷新配置文件
        config_name = self.Cfg_Combox.currentText()
        if config_name in ["Main", "main"]:
            print("切换主配置")
            config_path = os.path.join(
                os.getcwd(),
                "config",
                "maa_pi_config.json",
            )
            main_config = cfg.get(cfg.Maa_config)
            main_config = config_path
            cfg.set(cfg.Maa_config, main_config)
            self.update_task_list()

        else:
            print(f"切换到{config_name}配置")
            config_path = os.path.join(
                os.getcwd(),
                "config",
                "config_manager",
                config_name,
                "config",
                "maa_pi_config.json",
            )
            main_config = cfg.get(cfg.Maa_config)
            main_config = config_path
            cfg.set(cfg.Maa_config, main_config)
            self.update_task_list()

    def cfg_delete(self):
        config_name = self.Cfg_Combox.currentText()
        config_name_list = list(cfg.get(cfg.maa_config_list))
        if config_name in ["Main", "main"]:
            print("不能删除主配置文件")
        elif config_name in config_name_list:
            print(f"删除配置文件{config_name}")
            # 删除配置文件
            config_list = cfg.get(cfg.maa_config_list)
            file_path = os.path.dirname(os.path.dirname(config_list[config_name]))
            shutil.rmtree(file_path)  # 删除配置文件目录
            print(f"删除配置文件{file_path}成功")
            del config_list[config_name]
            cfg.set(cfg.maa_config_list, config_list)

            # 切换到主配置
            main_config = cfg.get(cfg.Maa_config)
            main_config = "Main"
            cfg.set(cfg.Maa_config, main_config)
            # 刷新下拉框和配置文件
            config_list = cfg.get(cfg.maa_config_list)
            self.Cfg_Combox.clear()
            self.Cfg_Combox.addItems(config_name_list)
            self.cfg_changed()
        else:
            print(f"{config_name}不存在")
            self.Cfg_Combox.clear()
            self.Cfg_Combox.addItems(config_name_list)
            self.cfg_changed()

    def update_task_list(self, task_list=[]):
        # 刷新配置文件列表

        # 从组件获取配置的任务列表
        items = self.get_task_list_widget()

        if items != task_list:
            self.List_widget.clear()
            self.List_widget.addItems(
                Get_Values_list_Option(cfg.get(cfg.Maa_config), "task")
            )
            items = self.get_task_list_widget()
            signalBus.update_task_list.emit(items)


    def get_task_list_widget(self):
        items = []
        for i in range(self.List_widget.count()):
            item = self.List_widget.item(i)
            if item is not None:
                items.append(item.text())
        return items
