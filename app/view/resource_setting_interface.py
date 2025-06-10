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
MFW-ChainFlow Assistant 资源包设置界面
作者:overflow65537
"""


from qfluentwidgets import (
    SettingCardGroup,
    ScrollArea,
    ExpandLayout,
    InfoBar,
    InfoBarPosition,
)
import os
import shutil
from qfluentwidgets import FluentIcon as FIF
from qfluentwidgets import InfoBar
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QWidget, QLabel, QFileDialog

from ..common.config import cfg
from ..common.signal_bus import signalBus
from ..common.style_sheet import StyleSheet
from ..utils.widget import (
    LineEditCard,
    ComboWithActionSettingCard,
    CustomMessageBox,
    ComboBoxSettingCardCustom,
)
from ..utils.tool import Save_Config, get_gpu_info
from ..utils.logger import logger
from ..common.maa_config_data import maa_config_data


class ResourceSettingInterface(ScrollArea):
    """资源切换界面，用于配置资源。"""

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.resource_scrollWidget = QWidget()
        self.resource_expandLayout = ExpandLayout(self.resource_scrollWidget)
        # 初始化界面
        signalBus.resource_exist.connect(self.resource_exist)
        self.create_mapping()

        self.init_ui()
        self.__connectSignalToSlot()
        if not cfg.get(cfg.resource_exist):
            self.enable_widgets(False)

    def create_mapping(self):
        self.win32_input_mapping = {
            0: self.tr("default"),
            1: "seize",
            2: "SendMessage",
        }
        self.win32_input_combox_list = [
            self.tr("default"),
            "seize",
            "SendMessage",
        ]

        self.win32_screencap_mapping = {
            0: self.tr("default"),
            1: "GDI",
            2: "FramePool",
            4: "DXGI_DesktopDup",
        }

        self.ADB_input_mapping = {
            0: self.tr("default"),
            1: "AdbShell",
            2: "MinitouchAndAdbKey",
            4: "Maatouch",
            8: "EmulatorExtras",
        }

        self.ADB_screencap_mapping = {
            0: self.tr("default"),
            1: "EncodeToFileAndPull",
            2: "Encode",
            4: "RawWithGzip",
            8: "RawByNetcat",
            16: "MinicapDirect",
            32: "MinicapStream",
            64: "EmulatorExtras",
        }
        self.gpu_mapping = get_gpu_info()
        self.gpu_combox_list = self.get_unique_gpu_mapping(self.gpu_mapping)
        self.gpu_mapping[-1] = self.tr("Auto")
        self.gpu_mapping[-2] = self.tr("Disabled")

        print("gpu_mapping: ", self.gpu_mapping)

    def resource_exist(self, status: bool):
        """
        当资源存在时触发该函数，更新界面状态和内容。
        """
        if status:
            logger.info("收到信号,初始化界面并连接信号")
            self.init_info()
            self.enable_widgets(True)
        else:
            logger.info("收到信号,清空界面并断开信号")
            self.enable_widgets(False)
            self.clear_content()

    def init_ui(self):
        """初始化界面内容。"""
        # 设置标签
        self.resource_setting_Label = QLabel(self.tr("Resource Settings"), self)

        # 初始化设置
        self.initialize_res_cfg_setting()
        self.initialize_adb_settings()
        self.initialize_win32_settings()
        self.initialize_start_settings()
        self.initialize_VI_settings()
        self.__initWidget()
        self.init_info()

    def init_info(self):
        """初始化控件信息。"""
        # 从配置中读取数据并填充到控件
        if maa_config_data.interface_config:
            self.project_name = maa_config_data.interface_config.get("name", "")
            self.project_version = maa_config_data.interface_config.get("version", "")
            self.project_url = maa_config_data.interface_config.get("url", "")
        else:
            self.project_name = ""
            self.project_version = ""
            self.project_url = ""

        self.ADB_port.lineEdit.setText(
            maa_config_data.config.get("adb", {}).get("address", "")
        )
        self.ADB_path.lineEdit.setText(
            maa_config_data.config.get("adb", {}).get("adb_path", "")
        )
        self.emu_path.lineEdit.setText(maa_config_data.config.get("emu_path", ""))
        self.emu_args.lineEdit.setText(maa_config_data.config.get("emu_args", ""))
        self.emu_wait_time.lineEdit.setText(
            str(maa_config_data.config.get("emu_wait_time", ""))
        )
        self.exe_path.lineEdit.setText(maa_config_data.config.get("exe_path", ""))
        self.exe_args.lineEdit.setText(maa_config_data.config.get("exe_args", ""))
        self.exe_wait_time.lineEdit.setText(
            str(maa_config_data.config.get("exe_wait_time", ""))
        )
        self.run_before_start.lineEdit.setText(
            maa_config_data.config.get("run_before_start", "")
        )
        self.run_before_start_args.lineEdit.setText(
            maa_config_data.config.get("run_before_start_args", "")
        )
        self.run_after_finish.lineEdit.setText(
            maa_config_data.config.get("run_after_finish", "")
        )
        self.run_after_finish_args.lineEdit.setText(
            maa_config_data.config.get("run_after_finish_args", "")
        )
        self.use_GPU.path = maa_config_data.config_path
        self.win32_input_mode.path = maa_config_data.config_path
        self.win32_screencap_mode.path = maa_config_data.config_path
        self.ADB_input_mode.path = maa_config_data.config_path
        self.ADB_screencap_mode.path = maa_config_data.config_path

        choose_gpu_text = self.gpu_mapping[maa_config_data.config.get("gpu", -1)]
        self.use_GPU.comboBox.setCurrentText(choose_gpu_text)
        win32_input = self.win32_input_mapping[
            maa_config_data.config.get("win32", {}).get("input_method", 0)
        ]
        self.win32_input_mode.comboBox.setCurrentText(win32_input)
        win32_screen = self.win32_screencap_mapping[
            maa_config_data.config.get("win32", {}).get("screen_method", 0)
        ]
        self.win32_screencap_mode.comboBox.setCurrentText(win32_screen)
        adb_input = self.ADB_input_mapping[
            maa_config_data.config.get("adb", {}).get("input_method", 0)
        ]
        self.ADB_input_mode.comboBox.setCurrentText(adb_input)
        adb_screencap = self.ADB_screencap_mapping[
            maa_config_data.config.get("adb", {}).get("screen_method", 0)
        ]
        self.ADB_screencap_mode.comboBox.setCurrentText(adb_screencap)

    def clear_content(self):
        """清空输入框和设置内容"""

        self.ADB_port.lineEdit.textChanged.disconnect()
        self.ADB_path.lineEdit.textChanged.disconnect()
        self.emu_path.lineEdit.textChanged.disconnect()
        self.emu_args.lineEdit.textChanged.disconnect()
        self.emu_wait_time.lineEdit.textChanged.disconnect()
        self.exe_path.lineEdit.textChanged.disconnect()
        self.exe_args.lineEdit.textChanged.disconnect()
        self.exe_wait_time.lineEdit.textChanged.disconnect()
        self.run_before_start.lineEdit.textChanged.disconnect()
        self.run_before_start_args.lineEdit.textChanged.disconnect()
        self.run_after_finish.lineEdit.textChanged.disconnect()
        self.run_after_finish_args.lineEdit.textChanged.disconnect()

        self.ADB_port.lineEdit.clear()
        self.ADB_path.lineEdit.clear()
        self.emu_path.lineEdit.clear()
        self.emu_args.lineEdit.clear()
        self.emu_wait_time.lineEdit.clear()
        self.exe_path.lineEdit.clear()
        self.exe_args.lineEdit.clear()
        self.exe_wait_time.lineEdit.clear()
        self.run_before_start.lineEdit.clear()
        self.run_before_start_args.lineEdit.clear()
        self.run_after_finish.lineEdit.clear()
        self.run_after_finish_args.lineEdit.clear()

        self.ADB_port.lineEdit.textChanged.connect(self._onADB_portCardChange)
        self.ADB_path.lineEdit.textChanged.connect(self._onADB_pathCardChange)
        self.emu_path.lineEdit.textChanged.connect(self._onEmuPathCardChange)
        self.emu_args.lineEdit.textChanged.connect(self._onEmuArgsCardChange)
        self.emu_wait_time.lineEdit.textChanged.connect(self._onEmuWaitTimeCardChange)
        self.exe_path.lineEdit.textChanged.connect(self._onExePathCardChange)
        self.exe_args.lineEdit.textChanged.connect(self._onExeParameterCardChange)
        self.exe_wait_time.lineEdit.textChanged.connect(self._onExeWaitTimeCardChange)
        self.run_before_start.lineEdit.textChanged.connect(
            self._onRunBeforeStartCardChange
        )
        self.run_before_start_args.lineEdit.textChanged.connect(
            self._onRunBeforeStartArgsCardChange
        )
        self.run_after_finish.lineEdit.textChanged.connect(
            self._onRunAfterFinishCardChange
        )
        self.run_after_finish_args.lineEdit.textChanged.connect(
            self._onRunAfterFinishArgsCardChange
        )

    def enable_widgets(self, enable: bool):
        """启用或禁用所有可交互控件。"""
        if enable:
            logger.info("启用所有可交互控件")
        else:
            logger.info("禁用所有可交互控件")
        for widget in self.resource_scrollWidget.findChildren(QWidget):
            # 启用或禁用控件
            widget.setEnabled(enable)
        # 确保可以添加资源
        self.res_cfg_group.setEnabled(True)
        self.res_setting.combox.setEnabled(True)
        self.res_setting.add_button.setEnabled(True)
        self.res_setting.delete_button.setEnabled(True)
        self.res_cfg_group.setEnabled(True)
        self.res_setting.setEnabled(True)

    def lock_res_changed(self, status):
        """在更新的时候锁定资源包选择框"""
        if status:
            self.res_setting.combox.setEnabled(False)
            self.res_setting.add_button.setEnabled(False)
            self.res_setting.delete_button.setEnabled(False)

        else:
            self.res_setting.combox.setEnabled(True)
            self.res_setting.add_button.setEnabled(True)
            self.res_setting.delete_button.setEnabled(True)

    def add_resource(self):
        """添加资源"""
        w = CustomMessageBox(self)
        if w.exec():
            if w.name_data == "":
                return
            logger.debug(f"添加资源{w.name_data}")
            self.res_setting.combox.clear()
            self.cfg_setting.combox.clear()
            logger.debug("add_resource发送信号")
            signalBus.resource_exist.emit(True)
            self.initialize_config_combobox()
            self.res_setting.combox.setCurrentText(w.name_data)
            self.cfg_setting.combox.setCurrentText("default")

    def initialize_config_combobox(self):
        """初始化配置下拉框"""
        self.cfg_setting.combox.addItems(maa_config_data.config_name_list)
        self.cfg_setting.combox.setCurrentText(maa_config_data.config_name)
        self.res_setting.combox.addItems(maa_config_data.resource_name_list)
        self.res_setting.combox.setCurrentText(maa_config_data.resource_name)

    def switch_config(self, data_dict: dict = {}) -> None:
        """主动切换配置"""

        if data_dict.get("resource_name", False) and data_dict.get(
            "config_name", False
        ):
            logger.debug(f"主动切换配置{data_dict}")
            self.res_setting.combox.setCurrentText(data_dict.get("resource_name"))
            self.cfg_setting.combox.setCurrentText(data_dict.get("config_name"))
        if data_dict.get("start_task_inmediately", False):
            signalBus.start_task_inmediately.emit()
            logger.debug("主动切换配置发送信号")

    def lock_cfg(self):
        self.res_setting.combox.setDisabled(True)
        self.cfg_setting.combox.setDisabled(True)
        QTimer.singleShot(500, self.unlock_cfg)

    def unlock_cfg(self):
        self.res_setting.combox.setDisabled(False)
        self.cfg_setting.combox.setDisabled(False)

    def add_config(self, config_name=None):
        """添加新的配置"""
        if cfg.get(cfg.resource_exist):
            if config_name is None or type(config_name) in [int, bool]:
                config_name = self.cfg_setting.combox.currentText()

            if config_name in ["default", "default".lower()]:
                logger.warning(" 不能添加主配置文件")
                signalBus.infobar_message.emit(
                    {"status":"warning","msg":self.tr("default config can't be added.")}
                )
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
                signalBus.infobar_message.emit(
                    {"status":"warning","msg":config_name+self.tr(" already exists.")}
                )
                self.update_config_path(config_name)
            else:
                logger.debug(f" 创建 {config_name} 配置")
                signalBus.infobar_message.emit(
                    {"status":"info","msg":self.tr("Creating config ")+config_name}
                )
                self.create_new_config(config_name)

            self.cfg_changed()
            self.lock_cfg()
        else:
            signalBus.infobar_message.emit(
                {"status":"failed","msg":self.tr("Please add resources first.")}
            )


    def create_new_config(self, config_name):
        """创建新的配置文件"""
        self.cfg_setting.combox.addItem(config_name)
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
            config_name = self.cfg_setting.combox.currentText()
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

        signalBus.resource_exist.emit(True)
        signalBus.title_changed.emit()
        signalBus.update_finished_action.emit()
        self.clear_content()
        self.init_info()

    def res_changed(self, resource_name: str = ""):
        """资源下拉框改变时触发"""
        if resource_name == "" or None:
            resource_name = self.res_setting.combox.currentText()

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

        maa_config_data.resource_path = maa_config_data.resource_data.get(
            maa_config_data.resource_name, ""
        )

        cfg.set(cfg.maa_resource_path, maa_config_data.resource_path)
        maa_config_data.config_name_list = list(
            maa_config_data.config_data[maa_config_data.resource_name]
        )  # 配置名称列表
        maa_config_data.resource_name_list = list(
            maa_config_data.resource_data
        )  # 资源名称列表
        logger.info(f" 切换到 {resource_name} 资源")
        self.refresh_combobox()
        if cfg.get(cfg.auto_update_resource):
            logger.debug("res_changed发送信号")
            signalBus.auto_update.emit()
        signalBus.task_output_sync.emit({"type": "reinit"})
        self.lock_cfg()

    def res_delete(self):
        """删除当前选定的资源"""
        if not cfg.get(cfg.resource_exist):
            signalBus.infobar_message.emit(
                {"status":"failed","msg":self.tr("Please add resources first.")}
            )
            return
        resource_name = self.res_setting.combox.currentText()
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
            self.res_setting.combox.clear()
            self.cfg_setting.combox.clear()
            cfg.set(cfg.maa_config_name, "")
            cfg.set(cfg.maa_config_path, "")
            cfg.set(cfg.maa_resource_name, "")
            cfg.set(cfg.maa_resource_path, "")
            signalBus.resource_exist.emit(False)
        else:
            self.res_setting.combox.removeItem(self.res_setting.combox.currentIndex())
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
            signalBus.infobar_message.emit(
                {"status":"failed","msg":self.tr("Please add resources first.")}
            )
            return

        if config_name is None or type(config_name) in [int, bool]:
            config_name = self.cfg_setting.combox.currentText()

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
            self.lock_cfg()
            self.refresh_combobox()

        else:
            logger.info(f" {config_name} 不存在")
            self.cfg_setting.combox.clear()
            self.cfg_setting.combox.addItems(maa_config_data.config_name_list)
            self.cfg_changed()

    def refresh_combobox(self):
        """刷新配置下拉框和任务列表"""
        self.cfg_setting.combox.currentIndexChanged.disconnect()
        self.cfg_setting.combox.clear()
        self.cfg_setting.combox.currentIndexChanged.connect(self.cfg_changed)
        self.cfg_setting.combox.addItems(maa_config_data.config_name_list)
        

    def initialize_res_cfg_setting(self):
        """资源配置设置"""
        self.res_cfg_group = SettingCardGroup(
            self.tr("resource and config"), self.resource_scrollWidget
        )
        self.res_setting = ComboWithActionSettingCard(
            icon=FIF.FOLDER,
            title=self.tr("Resource Path"),
            content=self.tr(
                "You can quickly switch to the next resource with ALT+R, and return to the previous resource with ALT+SHIFT+R"
            ),
            parent=self.res_cfg_group,
            res=True,
        )
        self.cfg_setting = ComboWithActionSettingCard(
            icon=FIF.FOLDER,
            title=self.tr("Config Path"),
            content=self.tr(
                "You can quickly switch to the next config with ALT+C, and return to the previous config with ALT+SHIFT+C"
            ),
            parent=self.res_cfg_group,
        )
        self.initialize_config_combobox()
        self.res_cfg_group.addSettingCard(self.res_setting)
        self.res_cfg_group.addSettingCard(self.cfg_setting)
        self.resource_expandLayout.addWidget(self.res_cfg_group)

    def initialize_adb_settings(self):
        """初始化 ADB 设置。"""
        self.ADB_Setting = SettingCardGroup(self.tr("ADB"), self.resource_scrollWidget)

        # 读取 ADB 配置（默认为空）
        address_data = maa_config_data.config.get("adb", {}).get("address", "")
        path_data = maa_config_data.config.get("adb", {}).get("adb_path", "")
        emu_path = maa_config_data.config.get("emu_path", "")
        emu_wait_time = maa_config_data.config.get("emu_wait_time", "")

        self.ADB_port = LineEditCard(
            icon=FIF.COMMAND_PROMPT,
            holderText=address_data,
            title=self.tr("ADB Port"),
            num_only=False,
            parent=self.ADB_Setting,
        )
        self.ADB_path = LineEditCard(
            icon=FIF.APPLICATION,
            title=self.tr("ADB Path"),
            num_only=False,
            holderText=path_data,
            content=self.tr("Select ADB Path"),
            button=True,
            parent=self.ADB_Setting,
        )
        self.emu_path = LineEditCard(
            icon=FIF.APPLICATION,
            title=self.tr("Select Emulator Path"),
            num_only=False,
            holderText=emu_path,
            content=self.tr("Select Emulator Path"),
            button=True,
            parent=self.ADB_Setting,
        )
        self.emu_args = LineEditCard(
            icon=FIF.LABEL,
            holderText="",
            title=self.tr("Run Parameters"),
            num_only=False,
            parent=self.ADB_Setting,
        )
        self.emu_wait_time = LineEditCard(
            icon=FIF.STOP_WATCH,
            holderText=emu_wait_time,
            title=self.tr("Wait Time for Emulator Startup"),
            num_only=True,
            parent=self.ADB_Setting,
        )

        self.ADB_Setting.addSettingCard(self.ADB_port)
        self.ADB_Setting.addSettingCard(self.ADB_path)
        self.ADB_Setting.addSettingCard(self.emu_path)
        self.ADB_Setting.addSettingCard(self.emu_args)
        self.ADB_Setting.addSettingCard(self.emu_wait_time)

    def initialize_win32_settings(self):
        """初始化 Win32 设置。"""

        exe_path = maa_config_data.config.get("exe_path", "")
        exe_args = maa_config_data.config.get("exe_args", "")
        exe_wait_time = maa_config_data.config.get("exe_wait_time", "")
        self.Win32_Setting = SettingCardGroup(
            self.tr("Win32"), self.resource_scrollWidget
        )
        self.exe_path = LineEditCard(
            icon=FIF.APPLICATION,
            title=self.tr("Executable Path"),
            content=self.tr("Select Executable Path"),
            num_only=False,
            holderText=exe_path,
            button=True,
            parent=self.Win32_Setting,
        )
        self.exe_args = LineEditCard(
            icon=FIF.LABEL,
            holderText=exe_args,
            title=self.tr("Run Parameters"),
            num_only=False,
            parent=self.Win32_Setting,
        )
        self.exe_wait_time = LineEditCard(
            icon=FIF.STOP_WATCH,
            holderText=exe_wait_time,
            title=self.tr("Wait Time for Program Startup"),
            parent=self.Win32_Setting,
        )

        self.Win32_Setting.addSettingCard(self.exe_path)
        self.Win32_Setting.addSettingCard(self.exe_args)
        self.Win32_Setting.addSettingCard(self.exe_wait_time)

    def initialize_start_settings(self):
        """初始化启动设置。"""

        run_before_start = maa_config_data.config.get("run_before_start", "")
        run_after_finish = maa_config_data.config.get("run_after_finish", "")

        self.start_Setting = SettingCardGroup(
            self.tr("Custom Startup"), self.resource_scrollWidget
        )

        self.run_before_start = LineEditCard(
            icon=FIF.APPLICATION,
            title=self.tr("Run Program Before Start"),
            content=self.tr("Select Program"),
            num_only=False,
            holderText=run_before_start,
            button=True,
            parent=self.start_Setting,
        )
        self.run_before_start_args = LineEditCard(
            icon=FIF.LABEL,
            holderText="",
            title=self.tr("Run Parameters"),
            num_only=False,
            parent=self.start_Setting,
        )

        self.run_after_finish = LineEditCard(
            icon=FIF.APPLICATION,
            title=self.tr("Run Program After Finish"),
            content=self.tr("Select Program"),
            num_only=False,
            holderText=run_after_finish,
            button=True,
            parent=self.start_Setting,
        )
        self.run_after_finish_args = LineEditCard(
            icon=FIF.LABEL,
            holderText="",
            title=self.tr("Run Parameters"),
            num_only=False,
            parent=self.start_Setting,
        )
        self.start_Setting.addSettingCard(self.run_before_start)
        self.start_Setting.addSettingCard(self.run_before_start_args)
        self.start_Setting.addSettingCard(self.run_after_finish)
        self.start_Setting.addSettingCard(self.run_after_finish_args)

    def initialize_VI_settings(self):
        """初始化开发者设置。"""
        self.VisionAndInputGroup = SettingCardGroup(
            self.tr("Vision & Input"), self.resource_scrollWidget
        )

        self.use_GPU = ComboBoxSettingCardCustom(
            icon=FIF.IOT,
            title=self.tr("Select GPU"),
            content=self.tr("Use GPU to accelerate inference"),
            texts=self.gpu_combox_list,
            target=["gpu"],
            path=maa_config_data.config_path,
            parent=self.VisionAndInputGroup,
            mode="setting",
            mapping=self.gpu_mapping,
        )

        self.win32_input_mode = ComboBoxSettingCardCustom(
            icon=FIF.SAVE_AS,
            title=self.tr("Select Win32 Input Mode"),
            texts=[self.tr("default"), "seize", "SendMessage"],
            target=["win32", "input_method"],
            path=maa_config_data.config_path,
            parent=self.VisionAndInputGroup,
            mode="setting",
            mapping=self.win32_input_mapping,
        )

        self.win32_screencap_mode = ComboBoxSettingCardCustom(
            icon=FIF.SAVE_AS,
            title=self.tr("Select Win32 Screencap Mode"),
            texts=[self.tr("default"), "GDI", "FramePool", "DXGI_DesktopDup"],
            target=["win32", "screen_method"],
            path=maa_config_data.config_path,
            parent=self.VisionAndInputGroup,
            mode="setting",
            mapping=self.win32_screencap_mapping,
        )

        self.ADB_input_mode = ComboBoxSettingCardCustom(
            icon=FIF.SAVE_AS,
            title=self.tr("Select ADB Input Mode"),
            texts=[
                self.tr("default"),
                "AdbShell",
                "MinitouchAndAdbKey",
                "Maatouch",
                "EmulatorExtras",
            ],
            target=["adb", "input_method"],
            path=maa_config_data.config_path,
            parent=self.VisionAndInputGroup,
            mode="setting",
            mapping=self.ADB_input_mapping,
        )

        self.ADB_screencap_mode = ComboBoxSettingCardCustom(
            icon=FIF.SAVE_AS,
            title=self.tr("Select ADB Screencap Mode"),
            texts=[
                self.tr("default"),
                "EncodeToFileAndPull",
                "Encode",
                "RawWithGzip",
                "RawByNetcat",
                "MinicapDirect",
                "MinicapStream",
                "EmulatorExtras",
            ],
            target=["adb", "screen_method"],
            path=maa_config_data.config_path,
            parent=self.VisionAndInputGroup,
            mode="setting",
            mapping=self.ADB_screencap_mapping,
        )

        self.VisionAndInputGroup.addSettingCard(self.use_GPU)
        self.VisionAndInputGroup.addSettingCard(self.win32_input_mode)
        self.VisionAndInputGroup.addSettingCard(self.win32_screencap_mode)
        self.VisionAndInputGroup.addSettingCard(self.ADB_input_mode)
        self.VisionAndInputGroup.addSettingCard(self.ADB_screencap_mode)
        try:
            gpu_index = maa_config_data.config.get("gpu", -1)
            if isinstance(gpu_index, int):
                self.gpu_mapping[gpu_index]
            else:
                raise TypeError("gpu 配置值不是整数类型")
        except:
            self.use_GPU.comboBox.setCurrentText(self.tr("Auto"))
            maa_config_data.config["gpu"] = -1
            Save_Config(maa_config_data.config_path, maa_config_data.config)

    def get_unique_gpu_mapping(self, gpu_mapping: dict) -> list:
        """获取唯一的 GPU 名称列表。"""
        gpu_combox_list = list(set(gpu_mapping.values()))
        gpu_combox_list.insert(0, self.tr("Auto"))
        gpu_combox_list.insert(1, self.tr("Disabled"))

        return gpu_combox_list

    def __initWidget(self):
        """初始化界面元素。"""
        self.resize(1000, 800)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setViewportMargins(0, 80, 0, 20)
        self.setWidget(self.resource_scrollWidget)
        self.setWidgetResizable(True)
        self.setObjectName("Resource_setting_Interface")

        # 初始化样式表
        self.resource_scrollWidget.setObjectName("scrollWidget")
        self.resource_setting_Label.setObjectName("settingLabel")
        StyleSheet.SETTING_INTERFACE.apply(self)

        # 初始化布局
        self.__initLayout()

    def __initLayout(self):
        """初始化设置卡片的布局。"""
        self.resource_setting_Label.move(36, 30)

        # 将卡片组添加到布局中
        self.resource_expandLayout.setSpacing(28)
        self.resource_expandLayout.setContentsMargins(36, 10, 36, 0)
        self.resource_expandLayout.addWidget(self.res_cfg_group)
        self.resource_expandLayout.addWidget(self.ADB_Setting)
        self.resource_expandLayout.addWidget(self.Win32_Setting)
        self.resource_expandLayout.addWidget(self.start_Setting)
        self.resource_expandLayout.addWidget(self.VisionAndInputGroup)

    def __showRestartTooltip(self):
        """显示重启提示。"""
        InfoBar.success(
            self.tr("Updated successfully"),
            self.tr("Configuration takes effect after restart"),
            duration=1500,
            parent=self,
        )

    def __onADBPathCardClicked(self):
        """手动选择 ADB.exe 的位置。"""
        self.__select_file(self.ADB_path, "adb")

    def __onEmuPathCardClicked(self):
        """手动选择模拟器的位置。"""
        self.__select_file(self.emu_path, "emu")

    def __onExePathCardClicked(self):
        """手动选择可执行文件的路径。"""
        self.__select_file(self.exe_path, "exe")

    def __onRunBeforeStartCardClicked(self):
        """手动选择启动前运行的程序脚本。"""
        self.__select_file(self.run_before_start, "run_before")

    def __onRunAfterFinishCardClicked(self):
        """手动选择完成后运行的程序脚本。"""
        self.__select_file(self.run_after_finish, "run_after")

    def __select_file(self, setting_card: LineEditCard, config_key):
        """帮助方法，用于处理文件选择和设置内容。"""
        file_name, _ = QFileDialog.getOpenFileName(
            self, self.tr("Choose file"), "./", "All Files (*)"
        )
        if not file_name:
            return

        # 更新配置并设置卡片内容
        if config_key == "adb":
            maa_config_data.config["adb"]["adb_path"] = file_name  # type: ignore
            logger.debug(f"选择的 ADB 路径: {file_name}")
        elif config_key == "emu":
            maa_config_data.config["emu_path"] = file_name
            logger.debug(f"选择的模拟器路径: {file_name}")
        elif config_key == "exe":
            maa_config_data.config["exe_path"] = file_name
            logger.debug(f"选择的可执行文件路径: {file_name}")
        elif config_key == "run_before":
            maa_config_data.config["run_before_start"] = file_name
            logger.debug(f"选择的启动前运行程序脚本路径: {file_name}")
        elif config_key == "run_after":
            maa_config_data.config["run_after_finish"] = file_name
            logger.debug(f"选择的完成后运行程序脚本路径: {file_name}")

        Save_Config(maa_config_data.config_path, maa_config_data.config)
        logger.info(f"保存至{maa_config_data.config_path}")

        setting_card.lineEdit.setText(file_name)

    def __connectSignalToSlot(self):
        """连接信号到对应的槽函数。"""
        signalBus.setting_Visible.connect(self.Switch_Controller)
        cfg.appRestartSig.connect(self.__showRestartTooltip)
        signalBus.update_adb.connect(self.update_adb)
        # 链接资源配置信号
        signalBus.switch_config.connect(self.switch_config)
        signalBus.lock_res_changed.connect(self.lock_res_changed)
        self.cfg_setting.add_button.clicked.connect(self.add_config)
        self.cfg_setting.delete_button.clicked.connect(self.cfg_delete)
        self.cfg_setting.combox.currentIndexChanged.connect(self.cfg_changed)
        self.res_setting.combox.currentTextChanged.connect(self.res_changed)
        self.res_setting.add_button.clicked.connect(self.add_resource)
        self.res_setting.delete_button.clicked.connect(self.res_delete)
        # 连接 ADB 信号
        self.ADB_port.lineEdit.textChanged.connect(self._onADB_portCardChange)
        self.ADB_path.toolbutton.clicked.connect(self.__onADBPathCardClicked)
        self.ADB_path.lineEdit.textChanged.connect(self._onADB_pathCardChange)
        self.emu_path.toolbutton.clicked.connect(self.__onEmuPathCardClicked)
        self.emu_path.lineEdit.textChanged.connect(self._onEmuPathCardChange)
        self.emu_args.lineEdit.textChanged.connect(self._onEmuArgsCardChange)
        self.emu_wait_time.lineEdit.textChanged.connect(self._onEmuWaitTimeCardChange)

        # 连接 Win32 信号
        self.exe_path.toolbutton.clicked.connect(self.__onExePathCardClicked)
        self.exe_path.lineEdit.textChanged.connect(self._onExePathCardChange)
        self.exe_args.lineEdit.textChanged.connect(self._onExeParameterCardChange)
        self.exe_wait_time.lineEdit.textChanged.connect(self._onExeWaitTimeCardChange)

        # 连接启动信号
        self.run_before_start.toolbutton.clicked.connect(
            self.__onRunBeforeStartCardClicked
        )
        self.run_before_start.lineEdit.textChanged.connect(
            self._onRunBeforeStartCardChange
        )
        self.run_before_start_args.lineEdit.textChanged.connect(
            self._onRunBeforeStartArgsCardChange
        )
        self.run_after_finish.toolbutton.clicked.connect(
            self.__onRunAfterFinishCardClicked
        )
        self.run_after_finish.lineEdit.textChanged.connect(
            self._onRunAfterFinishCardChange
        )
        self.run_after_finish_args.lineEdit.textChanged.connect(
            self._onRunAfterFinishArgsCardChange
        )

    def _update_config(self, card: LineEditCard, config_key: str):
        if maa_config_data.config_path == "":
            return
        value = card.lineEdit.text()
        maa_config_data.config[config_key] = value
        Save_Config(maa_config_data.config_path, maa_config_data.config)

    def _onADB_portCardChange(self):
        """根据端口更改更新 ADB 地址。"""
        if maa_config_data.config_path == "":
            return
        port = self.ADB_port.lineEdit.text()
        maa_config_data.config["adb"]["address"] = port  # type: ignore
        Save_Config(maa_config_data.config_path, maa_config_data.config)

    def _onADB_pathCardChange(self):
        """根据输入更新 ADB 路径。"""
        if maa_config_data.config_path == "":
            return
        adb_path = self.ADB_path.lineEdit.text()
        maa_config_data.config["adb"]["adb_path"] = adb_path  # type: ignore
        Save_Config(maa_config_data.config_path, maa_config_data.config)

    def _onEmuPathCardChange(self):
        """根据输入更新模拟器路径。"""
        self._update_config(self.emu_path, "emu_path")

    def _onEmuWaitTimeCardChange(self):
        """根据输入更新启动模拟器等待时间。"""
        self._update_config(self.emu_wait_time, "emu_wait_time")

    def _onExePathCardChange(self):
        """根据输入更新可执行文件路径。"""
        self._update_config(self.exe_path, "exe_path")

    def _onExeWaitTimeCardChange(self):
        """根据输入更新启动可执行文件等待时间。"""
        self._update_config(self.exe_wait_time, "exe_wait_time")

    def _onExeParameterCardChange(self):
        """根据输入更新可执行文件的参数。"""
        self._update_config(self.exe_args, "exe_args")

    def _onEmuArgsCardChange(self):
        """根据输入更新模拟器参数。"""
        self._update_config(self.emu_args, "emu_args")

    def _onRunBeforeStartArgsCardChange(self):
        """根据输入更新启动前运行的程序脚本参数。"""
        self._update_config(self.run_before_start_args, "run_before_start_args")

    def _onRunAfterFinishArgsCardChange(self):
        """根据输入更新完成后运行的程序脚本参数。"""
        self._update_config(self.run_after_finish_args, "run_after_finish_args")

    def _onRunBeforeStartCardChange(self):
        """根据输入更新启动前运行的程序脚本路径。"""
        self._update_config(self.run_before_start, "run_before_start")

    def _onRunAfterFinishCardChange(self):
        """根据输入更新完成后运行的程序脚本路径。"""
        self._update_config(self.run_after_finish, "run_after_finish")

    def update_adb(self):
        """根据外部消息更新 ADB 路径和端口。"""
        logger.info(f"adb_信息更新")
        self.ADB_path.lineEdit.setText(
            maa_config_data.config.get("adb", {}).get("adb_path", "")
        )
        self.ADB_port.lineEdit.setText(
            maa_config_data.config.get("adb", {}).get("address", "")
        )

    def Switch_Controller(self, controller):
        """在 ADB 和 Win32 控制器设置之间切换。"""
        if controller == "win32":
            self.ADB_Setting.setHidden(True)
            # self.ADB_input_mode.setHidden(True)
            # self.ADB_screencap_mode.setHidden(True)

            self.Win32_Setting.setHidden(False)
            # self.win32_input_mode.setHidden(False)
            # self.win32_screencap_mode.setHidden(False)

        elif controller == "adb":
            self.ADB_Setting.setHidden(False)
            # self.ADB_input_mode.setHidden(False)
            # self.ADB_screencap_mode.setHidden(False)

            self.Win32_Setting.setHidden(True)
            # self.win32_input_mode.setHidden(True)
            # self.win32_screencap_mode.setHidden(True)
