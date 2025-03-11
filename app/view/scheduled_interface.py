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
        self.readme = Readme()
        signalBus.update_task_list.connect(self.update_task_list_passive)
        signalBus.switch_config.connect(self.switch_config)
        signalBus.readme_available.connect(self.update_readme)
        self.init_widget_text()
        if cfg.get(cfg.resource_exist):
            self.initialize_config_combobox()
            self.List_widget.addItems(
                Get_Values_list_Option(maa_config_data.config_path, "task")
            )
            self.init_text_browser()
        self.Add_cfg_Button.clicked.connect(self.add_config)
        self.Delete_cfg_Button.clicked.connect(self.cfg_delete)
        self.Cfg_Combox.currentIndexChanged.connect(self.cfg_changed)
        self.res_combox.currentTextChanged.connect(self.res_changed)
        self.add_res_button.clicked.connect(self.add_resource)
        self.delete_res_button.clicked.connect(self.res_delete)

    def init_widget_text(self):
        """初始化界面文本"""
        self.Cfg_Combox_title.setText(self.tr("Configuration"))
        self.res_title.setText(self.tr("Resource"))
        self.Add_cfg_Button.setText(self.tr("Add"))
        self.Delete_cfg_Button.setText(self.tr("Delete"))
        self.add_res_button.setText(self.tr("Add"))
        self.delete_res_button.setText(self.tr("Delete"))

    def init_text_browser(self):
        """初始化文本浏览器"""
        Readme_path = os.path.join(maa_config_data.resource_path, "README.md")
        if os.path.exists(Readme_path):
            with open(Readme_path, "r", encoding="utf-8") as f:
                content = f.read()
                content = re.sub(r"<[^>]*>", "", content)
                self.text_browser.setMarkdown(content)
                return
        update_url = maa_config_data.interface_config.get("url", "")
        if update_url == "":
            return

        markdown_url = for_config_get_url(update_url, "readme")
        self.readme.readme_url = markdown_url
        self.readme.start()

    def update_readme(self, msg):
        """更新README"""
        self.text_browser.clear()
        with open(
            os.path.join(maa_config_data.resource_path, "README.md"),
            "w",
            encoding="utf-8",
        ) as f:
            f.write(msg)
        # 在QTextBrowser中显示HTML内容
        msg = re.sub(r"<[^>]*>", "", msg)
        self.text_browser.setMarkdown(msg)

    def add_resource(self):
        """添加资源"""
        w = CustomMessageBox(self)
        if w.exec():
            if w.name_data =="":
                return
            logger.debug(f"添加资源{w.name_data}")
            self.res_combox.clear()
            self.Cfg_Combox.clear()
            logger.debug("add_resource发送信号")
            signalBus.resource_exist.emit(True)
            self.initialize_config_combobox()
            self.res_combox.setCurrentText(w.name_data)
            self.Cfg_Combox.setCurrentText("default")
            self.init_text_browser()

    def initialize_config_combobox(self):
        """初始化配置下拉框"""
        self.Cfg_Combox.addItems(maa_config_data.config_name_list)
        self.Cfg_Combox.setCurrentText(maa_config_data.config_name)
        self.res_combox.addItems(maa_config_data.resource_name_list)
        self.res_combox.setCurrentText(maa_config_data.resource_name)

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
        self.init_text_browser()

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
            "config",
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
            "config",
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
                "config",
                config_name,
                "maa_pi_config.json",
            )
            cfg.set(cfg.maa_config_path, maa_config_path)
            maa_config_data.config_name = "default"
            maa_config_data.config_path = maa_config_path
            """self.use_cfg_combo.clear()
            self.use_cfg_combo.addItems(maa_config_data.config_name_list)
            self.use_res_combo.clear()
            self.use_res_combo.addItems(maa_config_data.resource_name_list)"""

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
            "config",
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
        self.init_text_browser()
        if cfg.get(cfg.auto_update_resource):
            logger.debug("res_changed发送信号")
            signalBus.auto_update.emit()
        

    def res_delete(self):
        """删除当前选定的资源"""
        if not cfg.get(cfg.resource_exist):
            self.show_error(self.tr("Please add resources first."))
            return
        self.text_browser.clear()
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

        if config_name in ["default", "default".lower()]:
            logger.warning(" 不能删除主配置文件")
        elif config_name == "" or None:
            return
        elif config_name in maa_config_data.config_name_list:
            logger.info(f" 删除配置文件 {config_name}")

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
                "config",
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
