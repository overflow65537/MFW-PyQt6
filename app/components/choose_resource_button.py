from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFileDialog, QHBoxLayout, QSizePolicy
from PyQt6.QtGui import QColor
from qfluentwidgets import (
    MessageBoxBase,
    SubtitleLabel,
    LineEdit,
    InfoBar,
    InfoBarPosition,
    ToolButton,
)
from ..components.show_download import ShowDownload
from qfluentwidgets import FluentIcon as FIF
from ..common.config import cfg
from ..utils.tool import Read_Config, Save_Config
from ..utils.logger import logger
import os
from ..utils.update import download_bundle
from ..common.signal_bus import signalBus
from typing import Dict, List


class CustomMessageBox(MessageBoxBase):
    """Custom message box"""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.download_bundle = download_bundle()
        signalBus.bundle_download_stopped.connect(self.download_bundle.stop)
        transparent_color = QColor(255, 255, 255, 0)
        self.setMaskColor(transparent_color)
        self.folder = None
        self.status = 0
        self.titleLabel = SubtitleLabel(self.tr("choose Resource"), self)
        self.name_LineEdit = LineEdit(self)
        self.name_LineEdit.setPlaceholderText(self.tr("Enter the name of the resource"))
        self.name_LineEdit.setClearButtonEnabled(True)

        self.path_layout = QHBoxLayout()
        self.path_LineEdit = LineEdit(self)
        self.path_LineEdit.setPlaceholderText(self.tr("Enter the path of the resource"))
        self.path_LineEdit.setClearButtonEnabled(True)

        self.path_layout.addWidget(self.path_LineEdit)
        self.resourceButton = ToolButton(FIF.FOLDER_ADD, self)
        self.resourceButton.setSizePolicy(
            QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed
        )
        self.resourceButton.clicked.connect(self.type_resource_name)
        signalBus.download_finished.connect(self.download_finished)

        self.path_layout.addWidget(self.resourceButton)

        self.update_LineEdit = LineEdit(self)
        self.update_LineEdit.setPlaceholderText(self.tr("Enter update link (optional)"))
        self.update_LineEdit.setClearButtonEnabled(True)
        self.search_button = ToolButton(FIF.SEARCH, self)
        self.search_button.setSizePolicy(
            QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed
        )
        self.search_button.clicked.connect(self.search_bundle)
        self.update_layout = QHBoxLayout()
        self.update_layout.addWidget(self.update_LineEdit)
        self.update_layout.addWidget(self.search_button)

        self.path_layout.setStretch(0, 9)
        self.path_layout.setStretch(1, 1)

        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addLayout(self.path_layout)
        self.viewLayout.addWidget(self.name_LineEdit)
        self.viewLayout.addLayout(self.update_layout)

        self.yesButton.setText(self.tr("Confirm"))
        self.cancelButton.setText(self.tr("Cancel"))

        self.widget.setMinimumWidth(350)
        self.yesButton.clicked.connect(self.click_yes_button)

    def search_bundle(self) -> None:
        if self.update_LineEdit.text() == "":
            self.show_error(self.tr("Please enter the update link"))
            return
        self.search_button.setIcon(FIF.MORE)
        updata_link = self.update_LineEdit.text()
        logger.info(f"更新链接 {updata_link}")

        self.download_bundle.project_url = updata_link

        self.download_bundle.start()
        self.w = ShowDownload(self)
        self.w.show()

    def download_finished(self, message: Dict[str, str]) -> None:
        print(message)
        if message["update_status"] == "failed":

            if message.get("error_msg"):
                self.show_error(message["error_msg"])
                self.w.close()
            self.show_error(self.tr("Update not found"))
            self.w.close()
        else:
            self.show_info(self.tr("Update found"))
            self.folder = message["target_path"]
            if os.path.basename(self.folder) == "resource":
                interface_path = os.path.join(
                    os.path.dirname(self.folder), "interface.json"
                )
                resource_path = self.folder
                self.status = 0  # 0 直接选择resource目录，1选择resource目录的上级目录
            else:
                interface_path = os.path.join(self.folder, "interface.json")
                resource_path = os.path.join(self.folder, "resource")
                self.status = 1  # 0 直接选择resource目录，1选择resource目录的上级目录

            if not os.path.exists(interface_path):
                self.show_error(self.tr("The resource does not have an interface.json"))
                return
            elif not os.path.exists(resource_path):
                self.show_error(self.tr("The resource is not a resource directory"))
                return

            self.path_LineEdit.setText(self.folder)
            logger.info(f"资源路径 {self.folder}")
            logger.info(f"interface.json路径 {interface_path}")
            self.interface_data = Read_Config(interface_path)
            project_name = self.interface_data.get("name", "")
            self.name_LineEdit.clear()
            self.name_LineEdit.setText(project_name)

        self.search_button.setIcon(FIF.SEARCH)

    def show_info(self, message) -> None:
        InfoBar.info(
            title=self.tr("Info"),
            content=message,
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.BOTTOM_RIGHT,
            duration=-1,
            parent=self,
        )

    def type_resource_name(self) -> None:
        self.folder = QFileDialog.getExistingDirectory(
            self, self.tr("Choose folder"), "./"
        )
        if os.path.basename(self.folder) == "resource":
            interface_path = os.path.join(
                os.path.dirname(self.folder), "interface.json"
            )
            resource_path = self.folder
            self.status = 0  # 0 直接选择resource目录，1选择resource目录的上级目录
        else:
            interface_path = os.path.join(self.folder, "interface.json")
            resource_path = os.path.join(self.folder, "resource")
            self.status = 1  # 0 直接选择resource目录，1选择resource目录的上级目录

        if not os.path.exists(interface_path):
            self.show_error(self.tr("The resource does not have an interface.json"))
            return
        elif not os.path.exists(resource_path):
            self.show_error(self.tr("The resource is not a resource directory"))
            return

        self.path_LineEdit.setText(self.folder)
        logger.info(f"资源路径 {self.folder}")
        logger.info(f"interface.json路径 {interface_path}")
        self.interface_data = Read_Config(interface_path)
        project_name = self.interface_data.get("name", "")
        projece_url = self.interface_data.get("url", "")
        self.name_LineEdit.clear()
        self.name_LineEdit.setText(project_name)
        self.update_LineEdit.clear()
        self.update_LineEdit.setText(projece_url)

    def show_error(self, message) -> None:
        InfoBar.error(
            title=self.tr("Error"),
            content=message,
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.BOTTOM_RIGHT,
            duration=-1,
            parent=self,
        )

    def click_yes_button(self) -> None:
        self.name_data = self.name_LineEdit.text()
        path_data = self.path_LineEdit.text()
        interface_path = ""
        if self.status == 0:
            # 直接选择resource目录
            interface_path = os.path.join(os.path.dirname(path_data), "interface.json")
            path_data = os.path.dirname(path_data)
        elif self.status == 1:
            # 选择resource目录的上级目录
            interface_path = os.path.join(path_data, "interface.json")
            path_data = path_data

        update_data = self.update_LineEdit.text()
        resource_data = cfg.get(cfg.maa_resource_list)
        resource_list = list(resource_data)
        resource_path_list = list(resource_data.values())
        maa_config_list = cfg.get(cfg.maa_config_list)
        if self.name_data == "":
            self.show_error(self.tr("Resource name cannot be empty"))
            return
        elif path_data == "":
            self.show_error(self.tr("Resource path cannot be empty"))
            return
        elif self.name_data in resource_list or path_data in resource_path_list:
            self.show_error(self.tr("Resource already exists"))
            return

        # 将名字和更新链接写入interface.json文件
        self.interface_data["name"] = self.name_data
        if update_data != "":
            self.interface_data["url"] = update_data
        if interface_path == "":
            return
        Save_Config(interface_path, self.interface_data)

        # 将信息写入maa_resource_list
        resource_data[self.name_data] = path_data
        cfg.set(cfg.maa_resource_list, resource_data)
        maa_pi_config_Path = os.path.join(
            os.getcwd(), "config", self.name_data, "default", "maa_pi_config.json"
        )
        # 将信息写入maa_config_list
        maa_config_list[self.name_data] = {"default": maa_pi_config_Path}
        cfg.set(cfg.maa_config_list, maa_config_list)
        # 设置显示当前资源
        cfg.set(cfg.maa_config_name, "default")
        cfg.set(cfg.maa_config_path, maa_pi_config_Path)
        data = {
            "adb": {
                "adb_path": "",
                "address": "",
                "input_method": 0,
                "screen_method": 0,
                "config": {},
            },
            "win32": {
                "hwnd": 0,
                "input_method": 0,
                "screen_method": 0,
            },
            "controller": {"name": ""},
            "gpu": -1,
            "resource": "",
            "task": [],
            "finish_option": 0,
            "finish_option_res": 0,
            "finish_option_cfg": 0,
            "run_before_start": "",
            "run_before_start_args": "",
            "run_after_finish": "",
            "run_after_finish_args": "",
            "emu_path": "",
            "emu_args": "",
            "emu_wait_time": 10,
            "exe_path": "",
            "exe_args": "",
            "exe_wait_time": 10,
        }
        Save_Config(maa_pi_config_Path, data)
        cfg.set(cfg.maa_resource_name, self.name_data)
        cfg.set(cfg.maa_resource_path, path_data)
        cfg.set(cfg.resource_exist, True)
