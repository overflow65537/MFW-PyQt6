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
MFW-ChainFlow Assistant 任务逻辑
作者:overflow65537
"""


import os
import subprocess
import platform

from qasync import asyncSlot, asyncio
from pathlib import Path
import json
from typing import List, Dict, Union
import re
import shlex
import chardet


from PySide6.QtCore import Qt, QMimeData, QDateTime, QTime, QDate, QTimer
from PySide6.QtGui import QDrag, QDropEvent, QColor, QFont
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QListWidgetItem,
    QSizePolicy,
    QVBoxLayout,
    QSpacerItem,
)


from qfluentwidgets import (
    InfoBar,
    InfoBarPosition,
    BodyLabel,
    ComboBox,
    EditableComboBox,ToolTipFilter, ToolTipPosition
)

from ..view.UI_task_interface import Ui_Task_Interface

from ..utils.widget import ClickableLabel
from ..common.signal_bus import signalBus
from ..utils.tool import (
    Get_Values_list_Option,
    Get_Values_list,
    gui_init,
    Save_Config,
    Read_Config,
    Get_Values_list2,
    Get_Task_List,
    check_path_for_keyword,
    get_controller_type,
    check_port,
    find_existing_file,
    find_process_by_name,
    show_error_message,
    get_console_path,
    MyNotificationHandler,
)
from ..utils.maafw import maafw
from ..common.config import cfg
from maa.toolkit import AdbDevice
from ..utils.logger import logger
from ..common.maa_config_data import maa_config_data
from ..common.typeddict import (
    TaskItem,
    Interval,
    RefreshTime,
    SpeedrunConfig,
    InterfaceData,
)
from ..utils.notice import send_thread
from datetime import datetime, timedelta


class TaskInterface(Ui_Task_Interface, QWidget):

    devices = []  # 用于存储设备信息的列表
    need_runing = False  # 是否需要运行任务
    task_failed = None  # 是否有任务失败

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setupUi(self)

        maafw.notification_handler = MyNotificationHandler()
        self.bind_signals()
        self.init_widget_text()
        if cfg.get(cfg.resource_exist):
            self.init_ui()
            self.check_task_consistency()

        else:
            logger.warning("资源缺失")
            self.show_error(self.tr("Resource file not detected"))

    def get_option_case_names(
        self, interface_data: Union[dict, InterfaceData], option_key: str
    ) -> list:
        """
        提取interface.json中指定option键名的选项name列表

        :param interface_data: 加载后的interface.json字典数据 或 InterfaceData对象
        :param option_key: 需要查询的option键名（如"选择区域"、"跳过剧情"等）
        :return: 该键名对应cases中的name列表
        """
        # 安全获取option下的目标键值（处理键不存在的情况）
        target_option = interface_data.get("option", {}).get(option_key, {})
        # 提取cases列表（处理cases不存在或非列表的情况）
        cases = target_option.get("cases", [])

        # 遍历cases提取name（过滤非字典或无name的情况）
        return [
            case["name"] for case in cases if isinstance(case, dict) and "name" in case
        ]

    def check_task_consistency(self):
        """
        检查配置任务与接口模板的一致性（任务存在性+选项匹配）
        """
        # 获取 interface 模板任务列表和完整数据
        interface_data = maa_config_data.interface_config
        config_tasks = maa_config_data.config.get("task", [])
        option_keys = list(interface_data.get("option", {}).keys())
        task_keys = list(
            task["name"] for task in interface_data.get("task", []) if "name" in task
        )

        inconsistent_tasks = []  # 存储不一致的任务名称

        # 遍历配置任务，检查每个任务和选项是否与 interface 模板一致
        for i, cfg_task in enumerate(config_tasks):
            task_name = cfg_task.get("name", "")
            task_option = cfg_task.get("option", [])
            if not task_name:
                continue

            if cfg_task.get("advanced", False):
                item = self.Task_List.item(i)
                item.setBackground(QColor(200, 220, 255, 75))  # 淡蓝色背景
                font = item.font()
                font.setBold(True)  # 字体加粗增强区分
                item.setFont(font)
                continue

            # 检查任务是否存在于 interface 模板
            if task_name not in task_keys:
                inconsistent_tasks.append(task_name)
                maa_config_data.config["task"][i]["disabled"] = True
                Save_Config(maa_config_data.config_path, maa_config_data.config)
                item = self.Task_List.item(i)
                item.setBackground(QColor(255, 0, 0))
                continue
            for cfg_option in task_option:
                # 检查选项是否存在于 interface 模板
                if cfg_option.get("name", "") not in option_keys:
                    inconsistent_tasks.append(
                        task_name + "-" + cfg_option.get("name", "")
                    )
                    maa_config_data.config["task"][i]["disabled"] = True
                    Save_Config(maa_config_data.config_path, maa_config_data.config)
                    item = self.Task_List.item(i)
                    item.setBackground(QColor(255, 0, 0))
                    continue
                case_list = self.get_option_case_names(
                    interface_data, cfg_option.get("name", "")
                )
                # 检查选项的 value 是否存在于 interface 模板
                if cfg_option.get("value", "") not in case_list:
                    inconsistent_tasks.append(
                        task_name
                        + "-"
                        + cfg_option.get("name", "")
                        + "-"
                        + cfg_option.get("value", "")
                    )
                    maa_config_data.config["task"][i]["disabled"] = True
                    Save_Config(maa_config_data.config_path, maa_config_data.config)
                    item = self.Task_List.item(i)
                    item.setBackground(QColor(255, 0, 0))
                    continue

        # 输出结果
        if inconsistent_tasks:
            error_msg = (
                self.tr(
                    "Inconsistent items between configuration tasks and interface templates"
                )
                + "：\n"
                + "\n".join(inconsistent_tasks)
            )
            logger.warning(error_msg)
            for info_bar in self.findChildren(InfoBar):
                info_bar.close()

            InfoBar.error(
                title=self.tr("ERROR"),
                content=error_msg,
                isClosable=True,
                position=InfoBarPosition.BOTTOM_RIGHT,
                duration=10000,
                parent=self,
            )
        else:
            logger.info("所有配置任务与接口模板一致")

    def init_widget_text(self):
        """
        初始化文本
        """
        self.TaskName_Title_1.setText(self.tr("Task"))
        self.AddTask_Button.setText(self.tr("Add Task"))
        self.Resource_Title.setText(self.tr("Resource"))
        self.Control_Title.setText(self.tr("Controller"))
        self.AutoDetect_Button.setText(self.tr("Auto Detect"))
        self.Finish_title.setText(self.tr("Finish"))
        self.S2_Button.setText(self.tr("Start"))

    def resizeEvent(self, event):
        """
        当窗口大小改变时，重新设置所有 任务选项下拉框和doc 的宽度。
        """
        super().resizeEvent(event)
        scroll_area_width = self.scroll_area.width()
        for i in range(self.option_layout.count()):
            layout = self.option_layout.itemAt(i).layout()
            if layout is not None:
                for j in range(layout.count()):
                    # 检查 item 是否为 None
                    item = layout.itemAt(j)
                    if item is not None:
                        widget = item.widget()
                        if isinstance(widget, ComboBox):
                            widget.setFixedWidth(scroll_area_width - 20)
                        if isinstance(widget, BodyLabel):
                            widget.setFixedWidth(scroll_area_width - 20)

    def resource_exist(self, status: bool):
        """
        资源文件是否存在
        """
        if status:
            logger.info("收到信号,初始化界面和信号连接")
            self.enable_widgets(True)
            self.clear_content()
            self.init_ui()
            self.check_task_consistency()

        else:
            logger.info("资源缺失,清空界面")
            self.enable_widgets(False)
            self.clear_content()
            self.Finish_combox_cfg.hide()
            self.Finish_combox_res.hide()

    def init_ui(self):
        """
        初始化界面
        """
        self.Start_Status(
            interface_Path=maa_config_data.interface_config_path,
            maa_pi_config_Path=maa_config_data.config_path,
            resource_Path=maa_config_data.resource_path,
        )
        self.init_finish_combox()

    def clear_content(self):
        """
        清空界面
        """
        self.clear_layout()
        self.Task_List.clear()
        self.SelectTask_Combox_1.clear()
        self.Resource_Combox.clear()
        self.Control_Combox.clear()
        self.Autodetect_combox.clear()
        self.Finish_combox.clear()
        self.Autodetect_combox.clear()

    def enable_widgets(self, enable: bool):
        """
        启用或禁用所有可交互控件。
        """
        # 遍历所有子控件
        if enable:
            logger.info("setting_interface.py:启用所有可交互控件")
        else:
            logger.info("setting_interface.py:禁用所有可交互控件")
        for widget in self.main_layout.findChildren(QWidget):
            # 启用或禁用控件
            widget.setEnabled(enable)

    def init_finish_combox(self):
        """
        初始化 完成后运行 下拉框
        """
        self.Finish_combox.clear()
        self.Finish_combox_res.clear()
        self.Finish_combox_cfg.clear()
        finish_list = [
            self.tr("Do nothing"),  # 无动作
            self.tr("Close emulator"),  # 关闭模拟器
            self.tr("Quit app"),  # 退出应用
            self.tr("Close emulator and Quit app"),  # 关闭模拟器并退出应用
            self.tr("Shutdown"),  # 关机
            self.tr("Run Other Config"),  # 运行其他配置
        ]
        finish_combox = maa_config_data.config.get("finish_option", 0)
        self.Finish_combox.addItems(finish_list)
        self.Finish_combox.setCurrentIndex(finish_combox)
        logger.info(f"完成选项初始化完成,当前选择项为{finish_combox}")
        if not finish_combox == 5:
            self.Finish_combox_cfg.hide()
            self.Finish_combox_res.hide()

        finish_combox_res = maa_config_data.config.get("finish_option_res", 0)
        self.Finish_combox_res.addItems(maa_config_data.resource_name_list)
        self.Finish_combox_res.setCurrentIndex(finish_combox_res)

        finish_combox_cfg = maa_config_data.config.get("finish_option_cfg", 0)
        self.Finish_combox_cfg.addItems(maa_config_data.config_name_list)
        self.Finish_combox_cfg.setCurrentIndex(finish_combox_cfg)

    # region 信号槽
    def bind_signals(self):
        """
        绑定信号槽
        """
        signalBus.task_output_sync.connect(self.sync_button)
        signalBus.run_sp_task.connect(self.Start_Up)
        signalBus.agent_info.connect(self.show_agnet_info)
        signalBus.custom_info.connect(self.show_custom_info)
        signalBus.resource_exist.connect(self.resource_exist)
        signalBus.callback.connect(self.callback)
        signalBus.update_task_list.connect(self.update_task_list_passive)
        signalBus.update_finished_action.connect(self.init_finish_combox)
        signalBus.start_task_inmediately.connect(self.Start_Up)
        signalBus.dragging_finished.connect(self.dragging_finished)
        self.AddTask_Button.clicked.connect(self.Add_Task)
        self.AddTask_Button.rightClicked.connect(self.Add_All_Tasks)
        self.SelectTask_Combox_1.currentTextChanged.connect(
            self.Add_Select_Task_More_Select
        )
        self.Resource_Combox.currentTextChanged.connect(self.Save_Resource)
        self.Control_Combox.currentTextChanged.connect(self.Save_Controller)
        self.AutoDetect_Button.clicked.connect(self.Start_Detection)
        self.S2_Button.clicked.connect(self.Start_Up)
        self.Autodetect_combox.currentTextChanged.connect(self.Save_device_Config)
        self.Finish_combox.currentIndexChanged.connect(self.rewrite_Completion_Options)
        self.Finish_combox_res.currentIndexChanged.connect(self.Save_Finish_Option_Res)
        self.Finish_combox_cfg.currentIndexChanged.connect(self.Save_Finish_Option_Cfg)
        self.Task_List.itemSelectionChanged.connect(self.Select_Task)
        self.Delete_label.dragEnterEvent = self.dragEnter
        self.Delete_label.dropEvent = self.drop

    @asyncSlot(dict)
    async def sync_button(self, status: dict):
        """
        同步按钮状态
        """
        if status.get("type") == "stoptask":
            await self.Stop_task()

    # endregion
    def show_agnet_info(self, msg: str):
        """
        显示Agent信息
        """
        if msg.startswith("| INFO |"):
            self.insert_colored_text(msg, "forestgreen")
        elif msg.startswith("| WARNING |"):
            self.insert_colored_text(msg, "orange")
        elif msg.startswith("| ERROR |"):
            self.insert_colored_text(msg, "Tomato")

    def show_custom_info(self, msg):
        """
        自定义动作/识别器信息
        """
        match msg["type"]:
            case "action":
                self.insert_colored_text(
                    self.tr("Load Custom Action:") + " " + msg["name"]
                )
            case "recognition":
                self.insert_colored_text(
                    self.tr("Load Custom Recognition:") + " " + msg["name"]
                )
            case "error_c":
                self.insert_colored_text(
                    self.tr("Agent server connect failed"), "Tomato"
                )
            case "error_a":
                self.insert_colored_text(
                    self.tr("Agent server registration failed"), "Tomato"
                )
            case "error_t":
                self.insert_colored_text(
                    self.tr("Failed to init MaaFramework instance"), "Tomato"
                )
            case "error_r":
                self.insert_colored_text(
                    self.tr("Resource or Controller not initialized"), "Tomato"
                )
            case "agent_start":
                self.insert_colored_text(self.tr("Agent service start"))
            case "agent_info":
                self.insert_colored_text(msg["data"])
            case _:
                logger.warning(f"Unknown message type: {msg}")

    # region 拖动事件
    def dragEnter(self, event: QDropEvent):
        """
        拖动进入事件
        """
        if event.mimeData().hasText():
            event.acceptProposedAction()
        else:
            event.ignore()

    def drop(self, event: QDropEvent):
        """
        拖动释放事件
        """
        dropped_text = event.mimeData().text()
        self.Delete_label.setText(self.tr("Delete: ") + dropped_text)
        if " " in dropped_text:
            dropped_text = dropped_text.split(" ")[0]

        dragged_item = self.Task_List.currentItem()
        if not dragged_item:
            event.ignore()
            return

        task_index = dragged_item.data(Qt.ItemDataRole.UserRole)
        if task_index is None or not isinstance(task_index, int):
            event.ignore()
            return

        Task_List = maa_config_data.config.get("task", [])
        if 0 <= task_index < len(Task_List):
            del Task_List[task_index]
            self.update_task_list_passive()
            maa_config_data.config["task"] = Task_List
            Save_Config(maa_config_data.config_path, maa_config_data.config)
            self.update_task_list()
            self.Task_List.setCurrentRow(-1)
            self.AddTask_Button.setText(self.tr("Add Task"))
            self.Delete_label.setText("")
            self.Delete_label.setStyleSheet("background-color: rgba(255, 255, 255, 0);")
            event.acceptProposedAction()
        else:
            event.ignore()

    def startDrag(self, item: QListWidgetItem):
        """
        开始拖动
        """
        drag = QDrag(self)
        mimeData = QMimeData()
        mimeData.setText(item.text())
        drag.setMimeData(mimeData)
        drag.exec(Qt.DropAction.MoveAction)

    # endregion

    def callback(self, message: Dict):
        """
        任务回调
        """
        if message["name"] == "on_controller_action":
            if message["status"] == 1:
                self.insert_colored_text(self.tr("Starting Connection"))
            elif message["status"] == 2:
                self.insert_colored_text(self.tr("Connection Success"))
            elif message["status"] == 3:
                self.insert_colored_text(self.tr("Connection Failed"), "red")
            elif message["status"] == 4:
                self.insert_colored_text(self.tr("Unknown Error"), "red")
        elif message["name"] == "on_tasker_task":
            if not self.need_runing or message["task"] == "MaaNS::Tasker::post_stop":
                return
            elif message["status"] == 1:
                self.insert_colored_text(message["task"] + " " + self.tr("Started"))
            elif message["status"] == 2:
                self.insert_colored_text(message["task"] + " " + self.tr("Succeeded"))
                logger.debug(f"{message['task']} 任务成功")
            elif message["status"] == 3:
                self.task_failed = message["task"]
                self.insert_colored_text(
                    message["task"] + " " + self.tr("Failed"), "red"
                )
                logger.debug(f"{message["task"]} 任务失败")
                if cfg.get(cfg.when_task_failed):
                    self.send_notice("failed", message["task"])
        if message["name"] == "on_task_recognition":
            # 新的focus通知
            if message.get("focus"):
                if isinstance(message["focus"], str):  # 单条 直接输出
                    self.insert_colored_text(
                        message["focus"],
                    )
                elif isinstance(message["focus"], list):
                    for i in message["focus"]:
                        self.insert_colored_text(
                            i,
                        )
            if message.get("aborted"):
                self.task_failed = message["task"]
                self.insert_colored_text(
                    message["task"] + " " + self.tr("aborted"), "red"
                )
                logger.debug(f"{message['task']} 任务中止")
                if cfg.get(cfg.when_task_failed):
                    self.send_notice("failed", message["task"])

    def insert_colored_text(self, text, color_name="black"):
        """
        插入带颜色的文本
        """

        message = ClickableLabel(self)
        # 初始化 HTML 文本
        html_text = text

        # 解析颜色
        if "[color:" in html_text:
            html_text = re.sub(
                r"\[color:(.*?)\]", r'<span style="color:\1">', html_text
            )
            html_text = re.sub(r"\[/color\]", "</span>", html_text)
        else:
            color = QColor(color_name)
            if not color.isValid():
                color_name = "black"
            message.setTextColor(QColor(color_name))

        # 解析字号
        html_text = re.sub(
            r"\[size:(.*?)\]", r'<span style="font-size:\1px">', html_text
        )
        html_text = re.sub(r"\[/size\]", "</span>", html_text)

        # 解析粗体
        html_text = html_text.replace("[b]", "<b>").replace("[/b]", "</b>")

        # 解析斜体
        html_text = html_text.replace("[i]", "<i>").replace("[/i]", "</i>")

        # 解析下划线
        html_text = html_text.replace("[u]", "<u>").replace("[/u]", "</u>")

        # 解析删除线
        html_text = html_text.replace("[s]", "<s>").replace("[/s]", "</s>")

        html_text = re.sub(
            r"\[align:left\]", '<div style="text-align: left;">', html_text
        )
        html_text = re.sub(
            r"\[align:center\]", '<div style="text-align: center;">', html_text
        )
        html_text = re.sub(
            r"\[align:right\]", '<div style="text-align: right;">', html_text
        )
        html_text = re.sub(r"\[/align\]", "</div>", html_text)

        # 将换行符替换为 <br>
        html_text = html_text.replace("\n", "<br>")

        now = datetime.now().strftime("%H:%M")

        html_text = f'<span style="color:gray">{now}</span> {html_text}'

        message.setWordWrap(True)
        message.setText(html_text)
        message.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )  # 水平扩展，垂直自适应

        # 插入到布局
        count = self.right_layout.count()
        if count >= 2:
            # 插入到倒数第二个位置
            self.right_layout.insertWidget(count - 1, message)
        else:
            # 插入到第一个位置
            self.right_layout.insertWidget(0, message)

        # 将滑动区域滚动到最后
        QTimer.singleShot(
            10,
            lambda: self.scroll_area.verticalScrollBar().setValue(
                self.scroll_area.verticalScrollBar().maximum()
            ),
        )
        sent_dict = {
            "type": "task_output_add",
            "msg": {"text": text, "color": color_name},
        }
        signalBus.task_output_sync.emit(sent_dict)

    def clear_layout(self):
        """
        清除布局
        """
        while self.right_layout.count():
            item = self.right_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self.right_layout.addStretch()
        sent_dict = {"type": "task_output_clear"}
        signalBus.task_output_sync.emit(sent_dict)

    def Start_Status(
        self, interface_Path: str, maa_pi_config_Path: str, resource_Path: str
    ):
        """
        根据当前资源状态初始化界面
        """
        if self.check_file_paths_exist(
            resource_Path, interface_Path, maa_pi_config_Path
        ):
            self.load_config_and_resources(
                interface_Path, maa_pi_config_Path, resource_Path
            )
        else:
            logger.warning("资源缺失")
            self.show_error(self.tr("Resource file not detected"))

    def check_file_paths_exist(self, resource_Path, interface_Path, maa_pi_config_Path):
        """
        检查文件路径是否存在
        """
        return (
            os.path.exists(resource_Path)
            and os.path.exists(interface_Path)
            and os.path.exists(maa_pi_config_Path)
        )

    def load_config_and_resources(
        self, interface_Path, maa_pi_config_Path, resource_Path
    ):
        """
        加载配置和资源
        """
        logger.info("配置文件存在")
        return_init = gui_init(resource_Path, maa_pi_config_Path, interface_Path)
        self.update_task_list()
        self.Resource_Combox.addItems(Get_Values_list(interface_Path, key1="resource"))
        self.Control_Combox.addItems(Get_Values_list(interface_Path, key1="controller"))
        self.SelectTask_Combox_1.addItems(
            Get_Values_list(interface_Path, key1="task", sp=True)
        )

        if return_init is not None:
            self.Resource_Combox.setCurrentIndex(
                return_init.get("init_Resource_Type", 0)
            )
            self.Control_Combox.setCurrentIndex(
                return_init.get("init_Controller_Type", 0)
            )
        self.add_Controller_combox()

    def load_interface_options(self, interface_Path):
        """
        加载interface接口选项
        """
        self.Resource_Combox.addItems(Get_Values_list(interface_Path, key1="resource"))
        self.Resource_Combox.setCurrentIndex(0)
        self.Control_Combox.addItems(Get_Values_list(interface_Path, key1="controller"))
        self.SelectTask_Combox_1.addItems(
            Get_Values_list(interface_Path, key1="task", sp=True)
        )

    def rewrite_Completion_Options(self):
        """
        重写 完成后的动作 下拉框 用来展示 运行其他配置 的选项
        """
        finish_option = self.Finish_combox.currentIndex()
        maa_config_data.config["finish_option"] = finish_option
        if finish_option == 5:
            self.Finish_combox_cfg.show()
            self.Finish_combox_res.show()
        else:
            self.Finish_combox_cfg.hide()
            self.Finish_combox_res.hide()
        Save_Config(maa_config_data.config_path, maa_config_data.config)

    def Save_Finish_Option_Res(self):
        """
        保存 完成后的动作 下拉框 选项
        """
        finish_option_res = self.Finish_combox_res.currentIndex()
        maa_config_data.config["finish_option_res"] = finish_option_res
        Save_Config(maa_config_data.config_path, maa_config_data.config)

    def Save_Finish_Option_Cfg(self):
        """
        保存 完成后的动作 下拉框 选项
        """
        finish_option_cfg = self.Finish_combox_cfg.currentIndex()
        maa_config_data.config["finish_option_cfg"] = finish_option_cfg
        Save_Config(maa_config_data.config_path, maa_config_data.config)

    # region 完成后的动作
    def close_application(self):
        """
        关闭模拟器
        """
        adb_path = maa_config_data.config.get("adb", {}).get("adb_path")
        if not adb_path:
            return
        emu_dict = get_console_path(adb_path)
        if emu_dict is None:
            return
        match emu_dict["type"]:
            case "mumu":
                adb_port = (
                    maa_config_data.config.get("adb", {})
                    .get("address", "")
                    .split(":")[1]
                )
                emu = subprocess.run(
                    [emu_dict["path"], "info", "-v", "all"],
                    shell=True,
                    capture_output=True,
                    text=True,
                    check=True,
                    encoding="utf-8",
                )
                multi_dict: Dict[str, Dict[str, str]] = json.loads(emu.stdout.strip())

                if multi_dict.get("created_timestamp", False):
                    logger.debug(f"单模拟器")
                    logger.debug(f"MuMuManager.exe info -v all: {multi_dict}")

                    logger.debug(f"关闭序号{str(multi_dict.get('index'))}")
                    if str(multi_dict.get("adb_port")) == adb_port:
                        startupinfo = subprocess.STARTUPINFO()
                        if platform.system() == "Windows":
                            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                            startupinfo.wShowWindow = subprocess.SW_HIDE

                        try:
                            result = subprocess.run(
                                [
                                    emu_dict["path"],
                                    "control",
                                    "-v",
                                    str(multi_dict.get("index")),
                                    "shutdown",
                                ],
                                shell=True,
                                check=True,
                                encoding="utf-8",
                                capture_output=True,
                                startupinfo=startupinfo,
                            )
                            logger.info(
                                f"关闭模拟器命令执行成功，输出: {result.stdout.strip()}"
                            )
                        except subprocess.CalledProcessError as e:
                            logger.error(
                                f"关闭模拟器命令执行失败，错误信息: {e.stderr.strip()}"
                            )
                    return
                logger.debug(f"多模拟器")
                logger.debug(f"MuMuManager.exe info -v all: {multi_dict}")

                for emu_key, emu_data in multi_dict.items():
                    logger.debug(f"设备信息: {emu_data}")
                    if str(emu_data.get("adb_port")) == adb_port:
                        try:
                            startupinfo = subprocess.STARTUPINFO()
                            if platform.system() == "Windows":
                                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                                startupinfo.wShowWindow = subprocess.SW_HIDE

                            result = subprocess.run(
                                [
                                    emu_dict["path"],
                                    "control",
                                    "-v",
                                    str(emu_data.get("index")),
                                    "shutdown",
                                ],
                                shell=True,
                                check=True,
                                encoding="utf-8",
                                capture_output=True,
                                startupinfo=startupinfo,
                            )
                            logger.debug(
                                f"关闭序号{str(emu_data.get('index'))}，输出: {result.stdout.strip()}"
                            )
                        except subprocess.CalledProcessError as e:
                            logger.error(
                                f"关闭序号{str(emu_data.get('index'))}失败，错误信息: {e.stderr.strip()}"
                            )
                return
            case "LD":
                ld_pid = (
                    maa_config_data.config.get("adb", {})
                    .get("config", {})
                    .get("extras", {})
                    .get("ld", {})
                    .get("pid")
                )
                if ld_pid:
                    logger.debug(f"关闭LD进程: {ld_pid}")
                    try:
                        startupinfo = subprocess.STARTUPINFO()
                        if platform.system() == "Windows":
                            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                            startupinfo.wShowWindow = subprocess.SW_HIDE
                        taskkill_command = [
                            "taskkill",
                            "/F",
                            "/PID",
                            str(ld_pid),
                        ]
                        result = subprocess.run(
                            taskkill_command,
                            check=True,
                            encoding="utf-8",
                            capture_output=True,
                            startupinfo=startupinfo,
                        )
                        logger.info(
                            f"成功关闭 LD 进程 {ld_pid}，输出: {result.stdout.strip()}"
                        )
                    except subprocess.CalledProcessError as e:
                        logger.error(
                            f"关闭 LD 进程 {ld_pid} 失败，错误信息: {e.stderr.strip()}"
                        )
                return
            case "BlueStacks":
                pass
            case "Nox":
                pass
            case "Memu":
                pass
        if (
            maa_config_data.config.get("emu_path") != ""
            and self.app_process is not None
        ):
            self.app_process.terminate()
            try:
                self.app_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.app_process.kill()

    def shutdown(self):
        """
        关机
        """
        shutdown_commands = {
            "Windows": "shutdown /s /t 1",
            "Linux": "shutdown now",
            "Darwin": "sudo shutdown -h now",  # macOS
        }
        os.system(shutdown_commands.get(platform.system(), ""))

    def run_other_config(self):
        """
        运行其他配置
        """
        data_dict = {
            "resource_name": self.Finish_combox_res.currentText(),
            "config_name": self.Finish_combox_cfg.currentText(),
            "start_task_inmediately": True,
        }
        signalBus.switch_config.emit(data_dict)

    # endregion
    def start_process(self, command):
        """
        启动程序
        """
        try:
            logger.debug(f"启动程序: {command}")
            return subprocess.Popen(command)
        except:
            logger.exception(f"启动程序失败:\n ")
            show_error_message()

    def Auto_update_Start_up(self, status_dict):
        """
        启动任务启动后进行自动更新
        """
        if cfg.get(cfg.start_complete):
            return
        if status_dict.get("status") != "info":
            signalBus.start_task_inmediately.emit()
            logger.info("启动任务启动后进行自动更新")

    # region 任务逻辑
    @asyncSlot()
    async def Start_Up(self, task: dict | None = None):
        """
        开始任务
        """
        if not cfg.get(cfg.resource_exist):
            return
        elif task:
            pass
        elif self.Task_List.count() == 0:
            self.show_error(self.tr("No task selected"))
            return
        self.need_runing = True
        self.update_S2_Button(self.tr("Stop"), self.Stop_task, enable=False)
        self.clear_layout()

        PROJECT_DIR = maa_config_data.resource_path
        controller_type = get_controller_type(
            self.Control_Combox.currentText(), maa_config_data.interface_config_path
        )
        if cfg.get(cfg.when_start_up):
            self.send_notice("info", self.tr("Start Up"))

        # 启动前脚本
        if task:
            pass
        elif not await self.run_before_start_script():
            return

        # 加载资源
        if not await self.load_resources(PROJECT_DIR):
            return

        # 连接控制器
        if not await self.connect_controller(controller_type):
            if cfg.get(cfg.when_connect_failed):
                self.send_notice(
                    "failed",
                    self.tr("Connection failed,please check the program"),
                )
            return
        fast_name, cost = self.get_speed_test()
        if fast_name and cost:
            logger.info(f"截图速度最快的方法是{fast_name},耗时{cost}ms")
            if 0 < cost < 50:
                self.insert_colored_text(
                    "[color:ForestGreen]"
                    + self.tr("fastest screenshot method cost:")
                    + str(cost)
                    + "ms("
                    + fast_name
                    + ")[/color]"
                )
            elif 51 < cost < 100:
                self.insert_colored_text(
                    "[color:DeepSkyBlue]"
                    + self.tr("fastest screenshot method cost:")
                    + str(cost)
                    + "ms("
                    + fast_name
                    + ")[/color]"
                )
            elif 101 < cost < 300:
                self.insert_colored_text(
                    "[color:LightSalmon]"
                    + self.tr("fastest screenshot method cost:")
                    + str(cost)
                    + "ms("
                    + fast_name
                    + ")\n"
                    + self.tr("May have an impact on the operation.")
                    + "[/color]"
                )
            elif 301 < cost:
                self.insert_colored_text(
                    "[color:Tomato]"
                    + self.tr("fastest screenshot method cost:")
                    + str(cost)
                    + "ms("
                    + fast_name
                    + ")\n"
                    + self.tr("May have an impact on the operation.")
                    + "[/color]"
                )
        if cfg.get(cfg.when_connect_success):
            self.send_notice("info", self.tr("Connection success"))

        # 运行任务
        if task:
            await self.run_task_sp(task)
        else:
            await self.run_tasks()

        # 结束后脚本
        if task:
            pass
        else:
            await self.run_after_finish_script()

        # 完成后运行
        if task:
            pass
        elif self.S2_Button.text() == self.tr("Stop"):
            await self.execute_finish_action()

        maafw.tasker = None
        if maafw.agent:
            maafw.agent.disconnect()
            maafw.agent = None

        # 更改按钮状态
        self.update_S2_Button("Start", self.Start_Up)

    # endregion

    def get_speed_test(self):
        """
        获取截图速度
        """
        try:
            log_path = os.path.join(maa_config_data.log_path, "maa.log")
            # 读取文件的前部分内容以检测编码
            with open(log_path, "rb") as raw_file:
                raw_data = raw_file.read(1024)
                result = chardet.detect(raw_data)
                encoding = result["encoding"]
            logger.debug(f"检测到的编码: {encoding}")

            # 使用检测到的编码读取文件
            with open(log_path, "r", encoding=encoding, errors="replace") as file:
                lines = file.readlines()
                # 倒序
                lines.reverse()
                for line in lines:
                    if "The fastest method is" in line:
                        # 提取最快方法
                        method_part = line.split("The fastest method is")[1].strip()
                        method = method_part.split(" ")[0]
                        # 提取耗时
                        cost_part = (
                            method_part.split("[cost=")[1].split("ms")[0].strip()
                        )
                        try:
                            cost = int(cost_part)
                        except ValueError:
                            cost = 0
                        return method, cost
            return None, None

        except Exception as e:
            logger.error(f"获取截图速度失败:{e}")
            return None, None

    def update_S2_Button(self, text, slot, enable=True):
        """
        更新按钮状态
        """
        self.S2_Button.setText(self.tr(text))
        self.S2_Button.clicked.disconnect()
        self.S2_Button.clicked.connect(slot)
        self.S2_Button.setEnabled(enable)
        signalBus.task_output_sync.emit(
            {
                "type": "change_button",
                "text": text,
                "status": enable,
            }
        )

    async def run_before_start_script(self):
        """
        运行前脚本
        """
        run_before_start = []
        run_before_start_path = maa_config_data.config.get("run_before_start")
        if run_before_start_path and self.need_runing:
            run_before_start.append(run_before_start_path)
            run_before_start_args: str = maa_config_data.config.get(
                "run_before_start_args", ""
            )
            if run_before_start_args:
                run_before_start.extend(shlex.split(run_before_start_args))
            logger.info(f"运行前脚本{run_before_start}")
            try:
                self.run_before_start_process = self.start_process(run_before_start)
                if not self.run_before_start_process:
                    return False
                logger.info(f"程序启动成功，PID: {self.run_before_start_process.pid}")
            except FileNotFoundError as e:
                self.show_error(self.tr("File not found"))
                logger.error(f'运行前脚本"{e}"')
                await maafw.stop_task()
                return False
            except OSError as e:
                self.show_error(self.tr("Can not start the file"))
                logger.error(f'运行前脚本"{e}"')
                await maafw.stop_task()
                return False
            finally:
                await asyncio.sleep(3)
        return True

    async def load_resources(self, PROJECT_DIR):
        """
        加载资源
        """
        if maafw.resource:
            maafw.resource.clear()  # 清除资源
        resource_path = ""
        resource_target = self.Resource_Combox.currentText()

        for i in maa_config_data.interface_config.get("resource", {}):
            if i["name"] == resource_target:
                logger.debug(f"加载资源: {i['path']}")
                resource_path = i["path"]

        if resource_path == "" and self.need_runing:
            logger.error(f"未找到目标资源: {resource_target}")
            await maafw.stop_task()
            self.update_S2_Button("Start", self.Start_Up)
            return False

        for i in resource_path:
            resource = (
                i.replace("{PROJECT_DIR}", PROJECT_DIR)
                .replace("/", os.sep)
                .replace("\\", os.sep)
            )
            logger.debug(f"加载资源: {resource}")
            await maafw.load_resource(resource)
            logger.debug(f"资源加载完成: {resource}")
        return True

    async def connect_controller(self, controller_type):
        """
        连接控制器
        """
        self.app_process = None
        if controller_type == "Adb" and self.need_runing:
            return await self.connect_adb_controller()
        elif controller_type == "Win32" and self.need_runing:
            return await self.connect_win32_controller()
        return True

    @asyncSlot()
    async def connect_adb_controller(self):
        """
        连接 ADB 控制器
        """
        # 尝试连接 ADB
        if maa_config_data.config.get("adb", {}).get("adb_path", "") == "":
            await self.Start_Detection()
        if not await self.connect_adb():
            # 如果连接失败，尝试启动模拟器
            if not await self.start_emulator():
                self.insert_colored_text(self.tr("Connection Failed"))
                await maafw.stop_task()
                self.update_S2_Button("Start", self.Start_Up)
                return False
            # 再次尝试连接 ADB
            if not await self.connect_adb():
                self.insert_colored_text(
                    self.tr("Connection Failed,try to kill ADB process")
                )
                if not self.kill_adb_process():
                    self.insert_colored_text(self.tr("kill ADB Failed"))
                if not await self.connect_adb():
                    logger.error(
                        f'连接adb失败\n{maa_config_data.config.get("adb", {}).get("adb_path", "")}\n{maa_config_data.config.get("adb", {}).get("address", "")}\n{maa_config_data.config.get("adb", {})["input_method"]}\n{maa_config_data.config.get("adb", {})["screen_method"]}\n{maa_config_data.config.get("adb", {})["config"]}'
                    )
                    self.insert_colored_text(self.tr("Connection Failed"))
                    await maafw.stop_task()
                    self.update_S2_Button("Start", self.Start_Up)
                    return False
        return True

    @asyncSlot()
    async def connect_adb(self):
        """
        连接 ADB
        """
        # 雷电模拟器特殊方法,重新获取pid
        emu_type = maa_config_data.config.get("adb", {}).get("adb_path", "")
        if "LDPlayer" in emu_type:
            logger.debug("获取雷电模拟器pid")
            device = await maafw.detect_adb()
            for i in device:
                if i.name == "LDPlayer":
                    if (
                        maa_config_data.config.get("adb", {})["config"].get("extras")
                        is None
                    ):
                        logger.debug("extras不存在，创建")
                        maa_config_data.config.get("adb", {})["config"] = i.config
                    else:
                        logger.debug("extras存在，更新pid")
                        maa_config_data.config.get("adb", {})["config"]["extras"]["ld"][
                            "pid"
                        ] = (i.config.get("extras", {}).get("ld", {}).get("pid", 0))
                    logger.debug(
                        f"获取到pid: {maa_config_data.config.get("adb",{})['config']['extras']['ld']['pid']}"
                    )
                    Save_Config(maa_config_data.config_path, maa_config_data.config)
                    break
        if (
            not await maafw.connect_adb(
                maa_config_data.config.get("adb", {})["adb_path"],
                maa_config_data.config.get("adb", {})["address"],
                maa_config_data.config.get("adb", {})["input_method"],
                maa_config_data.config.get("adb", {})["screen_method"],
                maa_config_data.config.get("adb", {}).get("config", {}),
            )
            and self.need_runing
        ):
            return False
        return True

    @asyncSlot()
    async def start_emulator(self):
        """
        启动模拟器
        """

        emu = []
        emu_path = maa_config_data.config.get("emu_path")
        if emu_path and self.need_runing:
            emu.append(emu_path)
            emu_args = maa_config_data.config.get("emu_args")
            emu_wait_time = int(maa_config_data.config.get("emu_wait_time", "0"))
            if emu_args:
                emu.extend(shlex.split(emu_args))
            logger.info(f"启动模拟器{emu}")
            try:
                self.app_process = self.start_process(emu)
                if not self.app_process:
                    return False
                logger.info(f"模拟器启动成功，PID: {self.app_process.pid}")
            except FileNotFoundError as e:
                self.show_error(self.tr("File not found"))
                logger.error(f'启动模拟器"{e}"')
                await maafw.stop_task()
                return False
            self.insert_colored_text(self.tr("waiting for emulator start..."))
            self.update_S2_Button(self.tr("Stop"), self.Stop_task)
            for i in range(int(emu_wait_time)):
                if not self.need_runing:
                    await maafw.stop_task()
                    self.update_S2_Button("Start", self.Start_Up)
                    return False
                else:
                    self.insert_colored_text(
                        self.tr("Starting task in ") + f"{int(emu_wait_time) - i}"
                    )
                    await asyncio.sleep(1)
            self.clear_layout()
            # 雷电模拟器特殊方法,重新获取pid
            emu_type = maa_config_data.config.get("adb", {}).get("adb_path", "")
            if "LDPlayer" in emu_type:
                logger.debug("获取雷电模拟器pid")
                device = await maafw.detect_adb()
                for i in device:
                    if i.name == "LDPlayer":
                        if (
                            maa_config_data.config.get("adb", {})["config"].get(
                                "extras"
                            )
                            is None
                        ):
                            logger.debug("extras不存在，创建")
                            maa_config_data.config.get("adb", {})["config"] = i.config
                        else:
                            logger.debug("extras存在，更新pid")
                            maa_config_data.config.get("adb", {})["config"]["extras"][
                                "ld"
                            ]["pid"] = (
                                i.config.get("extras", {}).get("ld", {}).get("pid", 0)
                            )
                        logger.debug(
                            f"获取到pid: {maa_config_data.config.get("adb",{})['config']['extras']['ld']['pid']}"
                        )
                        Save_Config(maa_config_data.config_path, maa_config_data.config)
                        break
        return True

    async def connect_win32_controller(self):
        """
        连接 Win32 控制器
        """
        exe = []
        exe_path = maa_config_data.config.get("exe_path")
        if exe_path and self.need_runing:
            exe.append(exe_path)
            exe_wait_time = int(maa_config_data.config.get("exe_wait_time", "0"))
            exe_args: str = maa_config_data.config.get("exe_args", "")
            if exe_args:
                exe.extend(shlex.split(exe_args))
            logger.info(f"启动游戏{exe}")
            try:
                self.app_process = self.start_process(exe)
                if not self.app_process:
                    return False
                logger.info(f"游戏启动成功，PID: {self.app_process.pid}")
            except FileNotFoundError as e:
                self.show_error(self.tr("File not found"))
                logger.error(f'启动游戏"{e}"')
                await maafw.stop_task()
                return False
            self.insert_colored_text(self.tr("Starting game..."))
            self.update_S2_Button(self.tr("Stop"), self.Stop_task)
            for i in range(int(exe_wait_time)):
                if not self.need_runing:
                    await maafw.stop_task()
                    self.update_S2_Button("Start", self.Start_Up)
                    return False
                else:
                    self.insert_colored_text(
                        self.tr("Starting game in ") + f"{int(exe_wait_time) - i}"
                    )
                    await asyncio.sleep(1)
        self.clear_layout()
        if (
            not await maafw.connect_win32hwnd(
                maa_config_data.config.get("win32", {}).get("hwnd", 0),
                maa_config_data.config.get("win32", {}).get("input_method", 0),
                maa_config_data.config.get("win32", {}).get("screen_method", 0),
            )
            and self.need_runing
        ):
            logger.error(
                f"连接Win32失败 \n{maa_config_data.config.get('win32',{}).get('hwnd',0)}\n{maa_config_data.config.get('win32',{}).get('input_method',0)}\n{maa_config_data.config.get('win32',{}).get('screen_method',0)}"
            )
            await maafw.stop_task()
            self.update_S2_Button("Start", self.Start_Up)
            return False
        return True

    @asyncSlot(dict)
    async def run_task_sp(self, task: dict | None = None):
        """
        运行任务_特殊任务:类似肉鸽类的,在interface中标记spt:true的任务
        """
        if task is None:
            return
        self.task_failed = None
        self.S2_Button.setEnabled(True)
        if not self.need_runing:
            await maafw.stop_task()
            return
        elif task.get("entry", "") == "":
            await maafw.stop_task()
            return

        await maafw.run_task(task.get("entry", ""), task.get("pipeline_override", {}))

        # 找到task的entry

    def merge_advanced_options(self, option):

        # 存储合并结果的字典
        advanced_groups = {}
        # 存储没有 advanced 字段的选项
        non_advanced_options = []

        # 遍历 option 列表，按 advanced 值分组
        for item in option:
            if "advanced" in item:
                advanced_key = item["advanced"]
                if advanced_key not in advanced_groups:
                    advanced_groups[advanced_key] = []
                advanced_groups[advanced_key].append(item["value"])
            else:
                non_advanced_options.append(item)

        # 创建包含合并后高级选项的列表
        merged_advanced_options = [
            {"name": advanced_key, "value": value_list, "advanced": True}
            for advanced_key, value_list in advanced_groups.items()
        ]

        # 合并非高级选项和合并后的高级选项
        new_option = non_advanced_options + merged_advanced_options
        return new_option

    async def run_tasks(self):
        """
        运行任务
        """

        self.task_failed = None
        self.S2_Button.setEnabled(True)
        restore_task_list = []
        for task_object in maa_config_data.config.get("task", []):
            if task_object.get("advanced"):
                task_object["option"] = self.merge_advanced_options(
                    task_object["option"]
                )
                restore_task_list.append(task_object)
            else:
                restore_task_list.append(task_object)
        print(restore_task_list)

        for task_list in maa_config_data.config.get("task", []):

            override_options = {}
            if not self.need_runing:
                await maafw.stop_task()
                return
            elif task_list.get("disabled"):
                logger.debug(f"任务{task_list.get('name')}已禁用")
                continue
            # 找到task的entry
            enter_index = 0
            for index, task_enter in enumerate(
                maa_config_data.interface_config.get("task", [])
            ):
                if task_enter.get("name", "M1") == task_list.get("name", "M2"):
                    self.entry = task_enter.get("entry", "")
                    if not self.entry:
                        logger.error(f"未找到任务入口: {task_list.get('name')}")
                        if cfg.get(cfg.when_task_failed):
                            self.send_notice("failed", self.tr("Task Entry") + ":")
                        self.insert_colored_text(self.tr("Task Entry Failed"))
                        return
                    enter_index = index
                    break

            # 解析task中的pipeline_override
            if maa_config_data.interface_config.get("task", [])[enter_index].get(
                "pipeline_override", False
            ):
                update_data = maa_config_data.interface_config.get("task", [])[
                    enter_index
                ].get("pipeline_override", {})
                override_options.update(update_data)

            # 解析task中的option
            if task_list.get("option", []) != []:
                for task_option in task_list.get("option", []):
                    # 解析advanced
                    if task_option.get("advanced", False):
                        for (
                            advanced_key,
                            advanced_value,
                        ) in maa_config_data.interface_config.get(
                            "advanced", {}
                        ).items():
                            if advanced_key == task_option.get("name", ""):
                                if (
                                    maa_config_data.interface_config.get("advanced", {})
                                    .get(advanced_key, {})
                                    .get("mode", "combox")
                                    == "combox"
                                ):
                                    """
                                    可输入的下拉框模式
                                    """
                                    template_pipeline = advanced_value.get(
                                        "pipeline_override", {}
                                    )
                                    field = advanced_value.get("field", "")
                                    value_list = task_option.get("value", [])
                                    types = advanced_value.get(
                                        "type", []
                                    )  # 获取类型信息

                                    # 处理多字段/多类型场景（field和type可能是列表）
                                    if isinstance(field, list):
                                        field_list = field
                                    else:
                                        field_list = [field]

                                    if isinstance(types, list):
                                        type_list = types
                                    else:
                                        type_list = [types]

                                    if isinstance(value_list, str):
                                        value_list = value_list.split(",")

                                    # 确保字段、类型、值数量匹配
                                    if len(field_list) != len(type_list) or len(
                                        field_list
                                    ) != len(value_list):
                                        logger.warning(
                                            f"高级设置 [{advanced_key}] 字段/类型/值数量不匹配，field: {field_list}, type: {type_list}, value: {value_list}"
                                        )
                                        continue

                                    # 类型转换
                                    converted_values = []
                                    for v, t in zip(value_list, type_list):
                                        try:
                                            if t == "int":
                                                converted = int(v.strip())  # 转为整数
                                            elif t == "string":
                                                converted = v.strip()  # 转为字符串
                                            elif t == "double":
                                                converted = float(
                                                    v.strip()
                                                )  # 转为浮点数
                                            elif t == "bool":
                                                converted = (
                                                    v.strip().lower() == "true"
                                                )  # 转为布尔值
                                            else:
                                                converted = v.strip()  # 未知类型
                                            converted_values.append(converted)
                                        except ValueError:
                                            logger.warning(
                                                f"高级设置 [{advanced_key}] 值 [{v}] 转换为类型 [{t}] 失败"
                                            )
                                            converted_values.append(v.strip())

                                    # 替换占位符
                                    resolved_pipeline = {}
                                    for (
                                        task_name,
                                        task_config,
                                    ) in template_pipeline.items():
                                        resolved_task_config = {}
                                        for key, val in task_config.items():
                                            # 初始化解析值为原始值
                                            resolved_val = val

                                            # 遍历所有字段-值对进行替换 f:roi cv:[1,2,3,4]
                                            for f, cv in zip(
                                                field_list, converted_values
                                            ):
                                                placeholder = f"{{{f}}}"

                                                def replace_placeholder(obj):
                                                    """
                                                    递归替换占位符
                                                    :param obj: 要处理的对象
                                                    :return: 替换后的对象
                                                    """
                                                    if isinstance(obj, str) and (
                                                        placeholder in obj
                                                    ):  # 如果是字符串且等于占位符
                                                        return obj.replace(
                                                            placeholder, str(cv)
                                                        )

                                                    elif isinstance(
                                                        obj, (list, tuple)
                                                    ):  # 如果是列表或者元组
                                                        return [
                                                            replace_placeholder(item)
                                                            for item in obj
                                                        ]

                                                    elif isinstance(
                                                        obj, dict
                                                    ):  # 如果是字典
                                                        return {
                                                            key: replace_placeholder(
                                                                value
                                                            )
                                                            for key, value in obj.items()
                                                        }

                                                    else:  # 这啥玩意
                                                        logger.debug(
                                                            f"高级设置 [{advanced_key}] 未处理的类型: {type(obj)}"
                                                        )
                                                        return obj

                                                resolved_val = replace_placeholder(
                                                    resolved_val
                                                )

                                            resolved_task_config[key] = resolved_val
                                        resolved_pipeline[task_name] = (
                                            resolved_task_config
                                        )

                                    override_options.update(resolved_pipeline)
                                    logger.debug(
                                        f"高级设置 [{advanced_key}] 解析后的 pipeline_override: {resolved_pipeline}"
                                    )

                                elif (
                                    maa_config_data.interface_config.get("advanced", {})
                                    .get(advanced_key, {})
                                    .get("mode", "combox")
                                    == "checkbox"
                                ):
                                    """
                                    多选框模式
                                    """
                                    pass

                    else:
                        for override in maa_config_data.interface_config.get(
                            "option", []
                        )[task_option["name"]]["cases"]:
                            if override["name"] == task_option["value"]:

                                override_options.update(
                                    override.get("pipeline_override", {})
                                )

            logger.info(
                f"运行任务:{self.entry}\n任务选项:\n{json.dumps(override_options, indent=4,ensure_ascii=False)}"
            )
            # 提取公共配置（简化嵌套访问）
            speedrun_cfg = task_list.get("speedrun", {})
            if speedrun_cfg.get("enabled", False):
                logger.info(f"{self.entry}速通启用")

                # 通用配置提取
                schedule_mode = speedrun_cfg.get("schedule_mode")
                interval_cfg = speedrun_cfg.get("interval", {})
                refresh_time_cfg = speedrun_cfg.get("refresh_time", {})
                last_run_str = speedrun_cfg.get("last_run", "1970-01-01 00:00:00")

                # 下次运行时间
                next_run = self.calculate_next_run_time(last_run_str, interval_cfg)
                # 刷新时间
                refresh_time = self.calculate_refresh_time(
                    schedule_mode, refresh_time_cfg, last_run_str
                )

                logger.info(f"任务[{self.entry}]上次运行时间: {last_run_str}")
                logger.info(
                    f"任务[{self.entry}]下次运行时间: {next_run.toString('yyyy-MM-dd HH:mm:ss')}"
                )
                logger.info(
                    f"任务[{self.entry}]刷新时间: {refresh_time.toString('yyyy-MM-dd HH:mm:ss')}"
                )

                # 重置循环次数逻辑
                if QDateTime.currentDateTime() > refresh_time:
                    interval_cfg["current_loop"] = interval_cfg.get("loop_item", 1)
                    logger.info(
                        f"任务[{self.entry}]重置循环次数: {interval_cfg['current_loop']}"
                    )

                # 处理循环次数（封装状态更新）
                remaining_loops = interval_cfg.get("current_loop", 0)
                if remaining_loops > 0 and self.entry:
                    if cfg.get(cfg.when_post_task):
                        self.send_notice("info", self.tr("Post Task :") + self.entry)
                    await maafw.run_task(self.entry, override_options)
                    if self.task_failed:
                        if cfg.get(cfg.when_task_failed):
                            self.send_notice(
                                "failed", str(self.task_failed) + self.tr("Failed")
                            )
                    else:
                        self.update_speedrun_state(speedrun_cfg, remaining_loops)
                else:
                    self.handle_exhausted_loops(refresh_time)
                    continue
            elif self.entry:
                logger.info(f"{self.entry}速通未启用")
                if cfg.get(cfg.when_post_task):
                    self.send_notice("info", self.tr("Post Task :") + self.entry)
                await maafw.run_task(self.entry, override_options)

        logger.info("任务完成")
        if cfg.get(cfg.when_task_finished):
            self.send_notice("completed")

    def calculate_next_run_time(
        self, last_run_str: str, interval_cfg: Interval
    ) -> QDateTime:
        """
        计算下次运行时间
        """
        last_run = QDateTime.fromString(last_run_str, "yyyy-MM-dd HH:mm:ss")
        unit = interval_cfg.get("unit", 2)  # 默认每天
        item = interval_cfg.get("item", 1)  # 默认间隔1个单位

        if unit == 0:  # 每分
            return last_run.addSecs(item * 60)
        elif unit == 1:  # 每小时
            return last_run.addSecs(item * 60 * 60)
        else:  # 每天（默认）
            return last_run.addSecs(item * 60 * 60 * 24)

    def calculate_refresh_time(
        self,
        schedule_mode: str | None,
        refresh_time_cfg: RefreshTime,
        last_run_str: str,
    ) -> QDateTime:
        """
        计算刷新时间
        """
        last_run: QDateTime = QDateTime.fromString(last_run_str, "yyyy-MM-dd HH:mm:ss")
        if schedule_mode == "daily":
            refresh_hour = refresh_time_cfg.get("H", 0)
            if last_run.time().hour() >= refresh_time_cfg.get(
                "H", 0
            ):  # 如果当前时间已经过了刷新时间
                refresh_time = last_run.addDays(1)
            else:
                refresh_time = last_run
            refresh_time.setTime(QTime(refresh_hour, 0))
            return refresh_time
        elif schedule_mode == "weekly":
            return self.get_date_time_for_week_day_and_hour(
                refresh_time_cfg.get("w", 0), refresh_time_cfg.get("H", 0)
            )
        elif schedule_mode == "monthly":
            refresh_day = refresh_time_cfg.get("d", 1)
            refresh_hour = refresh_time_cfg.get("H", 0)
            if (
                last_run.date().day() >= refresh_day
                and last_run.time().hour() >= refresh_hour
            ):
                refresh_time = last_run.addMonths(1)
            else:
                refresh_time = last_run
            refresh_time.setTime(QTime(refresh_hour, 0))
            refresh_time.setDate(
                QDate(
                    refresh_time.date().year(), refresh_time.date().month(), refresh_day
                )
            )
            return refresh_time
        return last_run

    def update_speedrun_state(self, speedrun_cfg: SpeedrunConfig, remaining_loops: int):
        """
        更新速通状态
        """
        speedrun_cfg.get("interval", {})["current_loop"] = remaining_loops - 1
        speedrun_cfg["last_run"] = QDateTime.currentDateTime().toString(
            "yyyy-MM-dd HH:mm:ss"
        )
        logger.info(f"任务[{self.entry}]剩余循环次数: {remaining_loops}")
        Save_Config(maa_config_data.config_path, maa_config_data.config)  # 更新配置文件

    def handle_exhausted_loops(self, refresh_time: QDateTime):
        """
        处理循环次数耗尽
        """
        logger.info(f"任务[{self.entry}]当前循环次数已耗尽")
        self.insert_colored_text(f"{self.entry} {self.tr('Loop count exhausted')}")  # type: ignore
        self.insert_colored_text(
            self.tr("Waiting for next run: ")
            + refresh_time.toString("yyyy-MM-dd HH:mm:ss")
        )

    def get_date_time_for_week_day_and_hour(self, target_week_day, target_hour):
        """

        获取指定周几和时间的QDateTime对象。

        :param target_week_day: 目标周几，0代表星期一，6代表星期日
        :param target_hour: 目标小时数，0-23
        :return: QDateTime对象，表示指定周几和时间的日期时间

        """
        # 获取当前日期和时间
        current_date_time = QDateTime.currentDateTime()

        # 获取当前日期是星期几 (1=周一,7=周日)
        current_day_of_week = current_date_time.date().dayOfWeek() - 1

        # 计算目标周几与当前周几的差异天数
        days_diff = (target_week_day - current_day_of_week) % 7

        # 计算目标周几的日期
        target_date_time = current_date_time.addDays(days_diff)

        # 设置时间为指定的小时数
        target_date_time.setTime(QTime(target_hour, 0))

        return target_date_time

    async def run_after_finish_script(self):
        """
        运行后脚本
        """
        run_after_finish = []
        run_after_finish_path = maa_config_data.config.get("run_after_finish")
        if run_after_finish_path and self.need_runing:
            run_after_finish.append(run_after_finish_path)
            run_after_finish_args: str = maa_config_data.config.get(
                "run_after_finish_args", ""
            )
            if run_after_finish_args:
                run_after_finish.extend(shlex.split(run_after_finish_args))
            logger.info(f"运行后脚本{run_after_finish}")
            try:
                self.run_after_finish_process = self.start_process(run_after_finish)
            except FileNotFoundError as e:
                self.show_error(self.tr("File not found"))
                logger.error(f'运行后脚本"{e}"')
            finally:
                await asyncio.sleep(3)

    async def execute_finish_action(self):
        """
        执行完成后的动作
        """
        target = self.Finish_combox.currentIndex()
        if target == 0:
            logger.debug("选择的动作: 不做任何操作")
            return
        elif target == 1:
            logger.debug("选择的动作: 关闭模拟器")
            try:
                self.close_application()
            except Exception as e:
                logger.error(f"关闭应用程序失败: {e}")
        elif target == 2:
            logger.debug("选择的动作: 退出应用程序")
            QApplication.quit()
        elif target == 3:
            logger.debug("选择的动作: 关闭应用程序并退出")
            try:
                self.close_application()
                QApplication.quit()
            except Exception as e:
                logger.error(f"关闭应用程序失败: {e}")
                QApplication.quit()
        elif target == 4:
            logger.debug("选择的动作: 关机")
            self.shutdown()
        elif target == 5:
            logger.debug("选择的动作: 运行其他配置")
            self.run_other_config()

    @asyncSlot()
    async def Stop_task(self):
        """
        停止任务
        """
        self.update_S2_Button("Start", self.Start_Up)
        self.insert_colored_text(self.tr("Stopping task..."))
        logger.info("停止任务")
        # 停止MAA
        self.need_runing = False
        await maafw.stop_task()

    def kill_adb_process(self):
        """
        杀死 ADB 进程
        """
        system = platform.system()
        try:
            startupinfo = None
            if system == "Windows":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

                subprocess.run(
                    ["taskkill", "/F", "/IM", "adb.exe"],
                    check=True,
                    startupinfo=startupinfo,
                )
                logger.info("使用 taskkill 杀死 ADB 进程成功")
                return True
            elif system in ("Darwin", "Linux"):
                subprocess.run(["pkill", "-f", "adb"], check=True)
                logger.info("使用 pkill 杀死 ADB 进程成功")
                return True
            else:
                logger.warning(f"不支持的操作系统: {system}")

        except subprocess.CalledProcessError as e:
            try:
                if system == "Windows":
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                    subprocess.run(
                        [
                            "wmic",
                            "process",
                            "where",
                            "name='adb.exe'",
                            "call",
                            "terminate",
                        ],
                        check=True,
                        startupinfo=startupinfo,
                    )
                    logger.info("使用 wmic 杀死 ADB 进程成功")
                elif system in ("Darwin", "Linux"):
                    subprocess.run(["killall", "adb"], check=True)
                    logger.info("使用 killall 杀死 ADB 进程成功")
                return True
            except subprocess.CalledProcessError as e:
                logger.error(f"最终杀死 ADB 进程失败: {e}")
                return False

    def dragging_finished(self):
        self.AddTask_Button.setText(self.tr("Add Task"))
        self.Task_List.setCurrentRow(-1)
        self.Delete_label.setText("")
        self.Delete_label.setStyleSheet(
            "background-color: rgba(255, 0); border-radius: 8px;"
        )
        self.check_task_consistency()

    def Add_Task(self):
        if maa_config_data.config == {}:
            return
        # 如果选中了任务的某项,则修改该项任务
        if self.Task_List.currentRow() != -1:
            Select_index = self.Task_List.currentRow()
            Select_Target = self.SelectTask_Combox_1.currentText()
            Option = self.get_selected_options()
            maa_config_data.config.get("task", [])[Select_index]["name"] = Select_Target
            maa_config_data.config.get("task", [])[Select_index]["option"] = Option[1]
            maa_config_data.config.get("task", [])[Select_index]["advanced"] = Option[0]

        else:
            Select_Target = self.SelectTask_Combox_1.currentText()
            Option = self.get_selected_options()
            speedrun = self.get_speedrun_value(Select_Target)

            task_data: TaskItem = {
                "name": Select_Target,
                "option": Option[1],
                "speedrun": speedrun,  # type: ignore
                "advanced": Option[0],
            }
            if maa_config_data.config.get("task") is None:
                raise ValueError("config['task'] is None")
            maa_config_data.config["task"].append(task_data)

        Save_Config(maa_config_data.config_path, maa_config_data.config)

        self.update_task_list()
        self.dragging_finished()
        self.check_task_consistency()

    def get_speedrun_value(self, Select_Target: str = ""):
        for i in maa_config_data.interface_config.get("task", []):
            if i.get("name", "") == Select_Target:
                return i.get("speedrun", {})
            else:
                return {}

    def Add_All_Tasks(self):
        if maa_config_data.config == {}:
            return

        for task in maa_config_data.interface_config.get("task", []):
            if task.get("spt"):
                continue
            selected_value = []
            task_name = task.get("name", "")
            options = task.get("option", [])
            speedrun = task.get("speedrun", {})

            if options:
                for pipeline_option in options:
                    # 获取 option 配置，使用空字典作为默认值
                    option_config = maa_config_data.interface_config.get("option", {})
                    # 检查 option_config 是否为字典，并且 pipeline_option 是否为有效的键
                    if (
                        isinstance(option_config, dict)
                        and pipeline_option in option_config
                    ):
                        cases = option_config[pipeline_option].get("cases")
                        # 检查 cases 是否为列表，并且列表不为空
                        if isinstance(cases, list) and cases:
                            target = cases[0].get("name", "")
                        else:
                            target = ""
                    else:
                        target = ""
                    selected_value.append(target)
                options_dicts = []
                for i, option_name in enumerate(options):
                    # 如果有option，则选择对应的项作为值
                    options_dicts.append(
                        {"name": option_name, "value": selected_value[i]}
                    )
            else:
                options_dicts = []

            maa_config_data.config["task"].append(
                {"name": task_name, "option": options_dicts, "speedrun": speedrun}  # type: ignore
            )

        # 保存配置
        Save_Config(maa_config_data.config_path, maa_config_data.config)

        # 更新任务列表
        self.update_task_list()

    def update_task_list(self):
        """
        更新任务列表
        """
        signalBus.update_task_list.emit()

    def update_task_list_passive(self):
        """
        更新任务列表(被动刷新)
        """
        self.Task_List.clear()
        tasks = maa_config_data.config.get("task", [])

        for index, task in enumerate(tasks):
            name_list = []
            name_list.append(task.get("name", ""))
            for i in task.get("option", []):
                value = i.get("value", "")
                if isinstance(value, list):
                    name_list.extend(value)
                else:
                    name_list.append(value)
            name = " ".join(name_list)

            item = QListWidgetItem(name)
            item.setData(Qt.ItemDataRole.UserRole, index)
            self.Task_List.addItem(item)

    def Delete_Task(self):
        Select_Target = self.Task_List.currentRow()
        if Select_Target == -1:
            self.show_error(self.tr("No task can be deleted"))
            return

        self.Task_List.takeItem(Select_Target)
        Task_List = Get_Values_list2(maa_config_data.config_path, "task")
        if 0 <= Select_Target < len(Task_List):
            del Task_List[Select_Target]
            maa_config_data.config["task"] = Task_List
            Save_Config(maa_config_data.config_path, maa_config_data.config)

            self.update_task_list()
            if Select_Target == 0:
                self.Task_List.setCurrentRow(Select_Target)
            elif Select_Target != -1:
                self.Task_List.setCurrentRow(Select_Target - 1)
        self.dragging_finished()

    def Delete_all_task(self):
        """
        删除所有任务
        """
        self.Task_List.clear()
        maa_config_data.config["task"] = []
        Save_Config(maa_config_data.config_path, maa_config_data.config)
        self.dragging_finished()
        self.update_task_list()

    def Move_Up(self):
        """
        移动任务至上一个位置
        """
        self.move_task(direction=-1)

    def Move_Top(self):
        """
        移动到最上层
        """
        if maa_config_data.config == {}:
            return
        Select_Target = self.Task_List.currentRow()

        if Select_Target == -1:
            return  # 如果没有选中的任务，则直接返回

        # 获取所选任务
        task_to_move = maa_config_data.config["task"][Select_Target]

        # 将所选任务从当前位置移除
        maa_config_data.config["task"].pop(Select_Target)

        # 将所选任务添加到最上层
        maa_config_data.config["task"].insert(0, task_to_move)

        # 保存配置
        Save_Config(maa_config_data.config_path, maa_config_data.config)

        # 更新任务列表
        self.update_task_list()

        # 设置当前选中行为最上层
        self.Task_List.setCurrentRow(0)

    def Move_Down(self):
        """
        移动任务至下一个位置
        """
        self.move_task(direction=1)

    def Move_Bottom(self):
        """
        移动到最下层
        """
        if maa_config_data.config == {}:
            return
        Select_Target = self.Task_List.currentRow()

        if Select_Target == -1:
            return  # 如果没有选中的任务，则直接返回

        # 获取所选任务
        task_to_move = maa_config_data.config["task"][Select_Target]

        # 将所选任务从当前位置移除
        maa_config_data.config["task"].pop(Select_Target)

        # 将所选任务添加到最下层
        maa_config_data.config["task"].append(task_to_move)

        # 保存配置
        Save_Config(maa_config_data.config_path, maa_config_data.config)

        # 更新任务列表
        self.update_task_list()

        # 设置当前选中行为最下层
        self.Task_List.setCurrentRow(len(maa_config_data.config["task"]) - 1)

    def move_task(self, direction: int):
        """
        移动任务至指定方向

        Args:
            direction: 移动方向，取值范围为[-1, 1]。
                      -1表示向上移动，1表示向下移动。
        """
        if maa_config_data.config == {}:
            return
        Select_Target = self.Task_List.currentRow()

        if direction == -1 and Select_Target == 0:
            self.show_error(self.tr("Already the first task"))
            return
        elif (
            direction == 1 and Select_Target >= len(maa_config_data.config["task"]) - 1
        ):
            self.show_error(self.tr("Already the last task"))
            return

        Select_Task = maa_config_data.config["task"].pop(Select_Target)
        maa_config_data.config["task"].insert(Select_Target + direction, Select_Task)
        Save_Config(maa_config_data.config_path, maa_config_data.config)

        self.update_task_list()
        self.Task_List.setCurrentRow(Select_Target + direction)

    def Select_Task(self):
        """
        选择任务后展示删除区域及重写按钮
        """
        self.Delete_label.setText(self.tr("Drag to Delete"))
        self.Delete_label.setStyleSheet(
            "background-color: rgba(255, 0, 0, 0.5); border-radius: 8px;"
        )

        self.AddTask_Button.setText(self.tr("Rewrite"))
        Select_Target = self.Task_List.currentRow()
        if Select_Target == -1:
            return
        # 将task_combox的内容设置为选中项目
        try:
            self.SelectTask_Combox_1.setCurrentText(
                maa_config_data.config["task"][Select_Target].get("name")
            )

            self.restore_options(
                maa_config_data.config["task"][Select_Target].get("option", [])
            )
        except IndexError:
            pass

    def restore_options(self, selected_options: List[Dict[str, str]]):
        """
        展示任务的选项
        """
        layout = self.option_layout

        for option in selected_options:
            name = option.get("name")
            value = option.get("value")
            if not name or not value:
                continue  # 如果name或value不存在，跳过本次循环
            for i in range(layout.count()):
                item = layout.itemAt(i)
                if not isinstance(item, QVBoxLayout):
                    continue  # 如果item不是QVBoxLayout，跳过本次循环
                for j in range(item.count()):
                    widget = item.itemAt(j).widget()
                    if isinstance(widget, BodyLabel) and widget.text() == name:
                        for k in range(item.count()):
                            combo_box = item.itemAt(k).widget()
                            if (
                                isinstance(combo_box, ComboBox)
                                and combo_box.objectName() == name
                            ):
                                combo_box.setCurrentText(value)
                                break
                            elif (
                                isinstance(combo_box, EditableComboBox)
                                and combo_box.objectName() == name
                            ):
                                combo_box.setText(value)
                                break
                        break

    def Save_Resource(self):
        """
        保存资源配置
        """
        self.update_config_value("resource", self.Resource_Combox.currentText())
        logger.info(f"保存资源配置: {self.Resource_Combox.currentText()}")

    def Save_Controller(self):
        """
        保存控制器配置
        """
        Controller_Type_Select = self.Control_Combox.currentText()
        controller_type = get_controller_type(
            Controller_Type_Select, maa_config_data.interface_config_path
        )
        if controller_type == "Adb":
            self.add_Controller_combox()
            signalBus.setting_Visible.emit("adb")

        elif controller_type == "Win32":
            asyncio.create_task(self.Start_Detection())
            signalBus.setting_Visible.emit("win32")
        logger.info(f"保存控制器配置: {Controller_Type_Select}")
        # 更新配置并保存
        maa_config_data.config["controller"]["name"] = Controller_Type_Select
        Save_Config(maa_config_data.config_path, maa_config_data.config)  # 刷新保存

    def add_Controller_combox(self):
        """
        启动后自动识别模拟器名字至控制器下拉框
        """
        controller_type = get_controller_type(
            self.Control_Combox.currentText(), maa_config_data.interface_config_path
        )
        self.Autodetect_combox.clear()
        if controller_type == "Adb":

            emulators_name = check_path_for_keyword(
                maa_config_data.config.get("adb", {})["adb_path"]
            )
            self.Autodetect_combox.clear()
            self.Autodetect_combox.addItem(
                f"{emulators_name} ({maa_config_data.config.get("adb",{})['address'].split(':')[-1]})"
            )

    def update_config_value(self, key, value):
        """
        保存配置值

        """
        maa_config_data.config[key] = value  # 更新实例变量
        Save_Config(maa_config_data.config_path, maa_config_data.config)  # 刷新保存

    def Add_Select_Task_More_Select(self):
        """
        动态添加更多选项到任务下拉框,用来展示option和doc
        """
        select_target = self.SelectTask_Combox_1.currentText()
        MAA_Pi_Config = maa_config_data.interface_config

        self.clear_extra_widgets()

        option_layout = self.option_layout
        doc_layout = self.doc_layout

        for task in MAA_Pi_Config.get("task", []):
            if task.get("name") == select_target:
                # 处理 option 字段
                options = task.get("option")
                if options:
                    for option in options:

                        advanced_list = task.get("advanced", [])

                        if option in advanced_list:
                            continue
                        v_layout = QVBoxLayout()

                        label = BodyLabel(self)
                        label.setText(option)
                        label.setFont(QFont("Arial", 10))
                        v_layout.addWidget(label)

                        select_box = ComboBox(self)
                        select_box.setObjectName(option)

                        select_box.addItems(
                            list(
                                Get_Task_List(
                                    maa_config_data.interface_config_path, option
                                )
                            )
                        )
                        select_box.setSizePolicy(
                            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
                        )
                        scroll_area_width = self.scroll_area.width()
                        select_box.setFixedWidth(scroll_area_width - 20)

                        v_layout.addWidget(select_box)

                        option_layout.addLayout(v_layout)

                # 处理advanced字段
                advanced_list = task.get("advanced", [])
                if advanced_list:
                    for advanced in advanced_list:
                        advanced_layout = QVBoxLayout()
                        advanced_layout.setObjectName(advanced)
                        advanced_dict = maa_config_data.interface_config.get(
                            "advanced", {}
                        ).get(advanced)
                        if (
                            isinstance(advanced_dict.get("field"), str)
                            or len(advanced_dict.get("field", [])) == 1
                        ):
                            advanced_label = BodyLabel(self)
                            advanced_select_box = EditableComboBox(self)
                            if isinstance(advanced_dict.get("field"), str):
                                # 如果是字符串，则直接设置文本
                                advanced_label.setText(advanced_dict.get("field"))
                                advanced_label.setToolTip(advanced_dict.get("doc"))
                                advanced_label.installEventFilter(ToolTipFilter(advanced_label, 0, ToolTipPosition.TOP))
                                advanced_select_box.setObjectName(
                                    advanced_dict.get("field")
                                )
                                advanced_select_box.setToolTip(advanced_dict.get("doc"))
                                advanced_select_box.installEventFilter(ToolTipFilter(advanced_select_box, 0, ToolTipPosition.TOP))
                            else:
                                advanced_label.setText(advanced_dict.get("field")[0])
                                advanced_label.setToolTip(advanced_dict.get("doc")[0])
                                advanced_label.installEventFilter(ToolTipFilter(advanced_label, 0, ToolTipPosition.TOP))

                                advanced_select_box.setObjectName(
                                    advanced_dict.get("field")[0]
                                )
                                advanced_select_box.setToolTip(advanced_dict.get("doc")[0]) 
                                advanced_select_box.installEventFilter(ToolTipFilter(advanced_select_box, 0, ToolTipPosition.TOP))
                            advanced_layout.addWidget(advanced_label)

                            advanced_select_box.addItems(
                                advanced_dict.get("default", [])
                            )

                            advanced_select_box.setSizePolicy(
                                QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
                            )
                            scroll_area_width = self.scroll_area.width()
                            advanced_select_box.setFixedWidth(scroll_area_width - 20)
                            advanced_layout.addWidget(advanced_select_box)

                        elif isinstance(advanced_dict.get("field"), list):
                            for idx, field in enumerate(advanced_dict.get("field", [])):
                                # 如果是列表，则逐个添加标签和选择框
                                advanced_label = BodyLabel(self)
                                advanced_label.setText(field)
                                advanced_label.setToolTip(advanced_dict.get("doc")[idx])
                                advanced_label.installEventFilter(ToolTipFilter(advanced_label, 0, ToolTipPosition.TOP))
                                advanced_layout.addWidget(advanced_label)

                                advanced_select_box = EditableComboBox(self)
                                advanced_select_box.setObjectName(field)
                                advanced_select_box.setToolTip(advanced_dict.get("doc")[idx])
                                advanced_select_box.installEventFilter(ToolTipFilter(advanced_select_box, 0, ToolTipPosition.TOP))


                                advanced_select_box.addItems(
                                    advanced_dict.get("default", [])[idx]
                                )
                                advanced_select_box.setSizePolicy(
                                    QSizePolicy.Policy.Expanding,
                                    QSizePolicy.Policy.Fixed,
                                )
                                scroll_area_width = self.scroll_area.width()
                                advanced_select_box.setFixedWidth(
                                    scroll_area_width - 20
                                )
                                advanced_layout.addWidget(advanced_select_box)

                        option_layout.addLayout(advanced_layout)

                # 处理 doc 字段
                doc = task.get("doc")
                if doc:
                    if isinstance(doc, list):
                        doc = "\n".join(doc)
                    doc_label = ClickableLabel(self)
                    doc_label.setWordWrap(True)

                    # 初始化 HTML 文本
                    html_text = doc

                    # 解析颜色
                    html_text = re.sub(
                        r"\[color:(.*?)\]", r'<span style="color:\1">', html_text
                    )
                    html_text = re.sub(r"\[/color\]", "</span>", html_text)

                    # 解析字号
                    html_text = re.sub(
                        r"\[size:(.*?)\]", r'<span style="font-size:\1px">', html_text
                    )
                    html_text = re.sub(r"\[/size]", "</span>", html_text)

                    # 解析粗体
                    html_text = html_text.replace("[b]", "<b>").replace("[/b]", "</b>")

                    # 解析斜体
                    html_text = html_text.replace("[i]", "<i>").replace("[/i]", "</i>")

                    # 解析下划线
                    html_text = html_text.replace("[u]", "<u>").replace("[/u]", "</u>")

                    # 解析删除线
                    html_text = html_text.replace("[s]", "<s>").replace("[/s]", "</s>")

                    # 解析对齐方式
                    html_text = re.sub(
                        r"\[align:left\]", '<div style="text-align: left;">', html_text
                    )
                    html_text = re.sub(
                        r"\[align:center\]",
                        '<div style="text-align: center;">',
                        html_text,
                    )
                    html_text = re.sub(
                        r"\[align:right\]",
                        '<div style="text-align: right;">',
                        html_text,
                    )
                    html_text = re.sub(r"\[/align\]", "</div>", html_text)

                    # 将换行符替换为 <br>
                    html_text = html_text.replace("\n", "<br>")

                    doc_label.setText(html_text)
                    doc_layout.addWidget(doc_label)

                spacer = QSpacerItem(
                    0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
                )
                self.main_scroll_layout.addItem(spacer)

                break

    def get_selected_options(self):
        """
        获取选中任务的所有选项
        """
        selected_options = []
        layout = self.option_layout
        name = None
        selected_value = None
        advanced_glabal = False

        for i in range(layout.count()):
            advanced = False
            item = layout.itemAt(i)
            if not isinstance(item, QVBoxLayout):
                continue  # 如果item不是QVBoxLayout，跳过本次循环
            widget_name = item.objectName()
            for j in range(item.count()):
                widget = item.itemAt(j).widget()
                if isinstance(widget, BodyLabel):
                    name = widget.text()
                elif isinstance(widget, ComboBox):
                    selected_value = widget.currentText()
                elif isinstance(widget, EditableComboBox):
                    selected_value = widget.currentText()
                    advanced = True
                    advanced_glabal = True

                if name and selected_value:
                    if advanced:
                        selected_options.append(
                            {
                                "name": name,
                                "value": selected_value,
                                "advanced": widget_name,
                            }
                        )

                    else:
                        selected_options.append({"name": name, "value": selected_value})

                    # 重置变量
                    name = None
                    selected_value = None
                    advanced = False

        return advanced_glabal, selected_options

    def clear_extra_widgets(self):
        """
        清除额外的控件
        """
        for layout in [self.option_layout, self.doc_layout]:
            if not layout:
                continue

            def recursive_clear(layout: QVBoxLayout):
                while layout.count():
                    item = layout.takeAt(0)
                    widget = item.widget()
                    if widget:  # 处理普通控件
                        widget.deleteLater()
                    elif item.layout():  # 处理嵌套布局
                        nested_layout = item.layout()
                        if isinstance(nested_layout, QVBoxLayout):
                            recursive_clear(nested_layout)
                    elif item.spacerItem():  # 处理间隔项
                        layout.removeItem(item)

            recursive_clear(layout)
            # 清空self.main_scroll_layout中的spacerItem
            for i in reversed(range(self.main_scroll_layout.count())):
                item = self.main_scroll_layout.itemAt(i)
                if isinstance(item, QSpacerItem):
                    self.main_scroll_layout.removeItem(item)

    @asyncSlot()
    async def Start_Detection(self):
        """
        启动检测adb或者win32窗口
        """
        if not cfg.get(cfg.resource_exist):
            return
        logger.info("开始检测")
        self.AutoDetect_Button.setEnabled(False)
        self.S2_Button.setEnabled(False)

        controller_type = get_controller_type(
            self.Control_Combox.currentText(), maa_config_data.interface_config_path
        )

        if controller_type == "Win32":
            content = self.tr("Detecting game...")
            error_message = self.tr("No game detected")
            success_message = self.tr("Game detected")
        elif controller_type == "Adb":
            content = self.tr("Detecting emulator...")
            error_message = self.tr("No emulator detected")
            success_message = self.tr("Emulator detected")
        else:
            return

        InfoBar.info(
            title=self.tr("Tip"),
            content=content,
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.BOTTOM_RIGHT,
            duration=2000,
            parent=self,
        )

        # 调用相应的检测函数
        processed_list = []  # 初始化处理列表
        if controller_type == "Win32":
            for i in maa_config_data.interface_config.get("controller", {}):
                if i["type"] == "Win32":
                    self.win32_hwnd = await maafw.detect_win32hwnd(
                        i.get("win32", {})["window_regex"]
                    )
            processed_list = (
                [hwnd.window_name for hwnd in self.win32_hwnd]
                if self.win32_hwnd
                else []
            )
        elif controller_type == "Adb":
            self.devices = await maafw.detect_adb()
            if not self.devices:
                logger.info("备用 ADB 检测")
                self.devices = await self.Adb_detect_backup()
            processed_list = [
                f"{device.name} ({device.address.split(':')[-1]})"
                for device in (self.devices or [])
            ]

        # 处理结果
        if not processed_list:
            logger.error("未检测到设备")
            self.show_error(error_message)
        else:
            signalBus.infobar_message.emit(
                {"status": "success", "msg": success_message}
            )
            self.Autodetect_combox.clear()
            processed_list = list(set(processed_list))
            self.Autodetect_combox.addItems(processed_list)

        # 重新启用按钮
        self.AutoDetect_Button.setEnabled(True)
        self.S2_Button.setEnabled(True)

    async def Adb_detect_backup(self):
        """备用adb识别"""
        emulator_list = Read_Config(
            os.path.join(os.getcwd(), "config", "emulator.json")
        )
        emulator_results = []

        for app in emulator_list:
            process_path = find_process_by_name(app["exe_name"])

            if process_path:
                # 判断程序是否正在运行, 是进行下一步, 否则放弃
                may_path = [os.path.join(*i) for i in app["may_path"]]
                info_dict = {"exe_path": process_path, "may_path": may_path}
                ADB_path = find_existing_file(info_dict)

                if ADB_path:
                    # 判断 ADB 地址是否存在, 是进行下一步, 否则放弃
                    port_data = await check_port(
                        app["port"]
                    )  # 使用 await 调用 check_port

                    if port_data:
                        # 判断端口是否存在, 是则组合字典, 否则放弃
                        for i in port_data:
                            emulator_result = AdbDevice(
                                name=app["name"],
                                adb_path=Path(ADB_path),
                                address=i,
                                screencap_methods=0,
                                input_methods=0,
                                config={},
                            )
                            emulator_results.append(
                                emulator_result
                            )  # 将对象添加到列表中

        return emulator_results  # 返回包含所有 AdbDevice 对象的列表

    def send_notice(self, msg_type: str = "", filed_task: str = "") -> None:
        """
        发送通知
                参数:
                msg_type (str): 消息的类型，用于区分通知的内容或来源。
                filed_task (str): 发送失败的任务名。

        """
        if msg_type == "completed":
            msg = {
                "title": self.tr("task completed"),
                "text": maa_config_data.resource_name
                + " "
                + maa_config_data.config_name
                + " "
                + self.tr("task completed"),
            }
        elif msg_type == "info":
            msg = {
                "title": self.tr("task info"),
                "text": maa_config_data.resource_name
                + " "
                + maa_config_data.config_name
                + " "
                + filed_task,
            }
        elif msg_type == "failed":
            msg = {
                "title": self.tr("task failed"),
                "text": maa_config_data.resource_name
                + " "
                + maa_config_data.config_name
                + " "
                + filed_task
                + " "
                + self.tr("task failed"),
            }
        else:
            return

        # 动态创建并启动线程
        for sender, status_key in [
            ("dingtalk", cfg.Notice_DingTalk_status),
            ("lark", cfg.Notice_Lark_status),
            ("smtp", cfg.Notice_SMTP_status),
            ("WxPusher", cfg.Notice_WxPusher_status),
            ("qywx", cfg.Notice_QYWX_status),
        ]:
            if cfg.get(status_key):  # 仅启用状态为 True 时发送
                logger.info(f"发送通知: {sender}, 状态: {status_key}")
                send_thread.add_task(sender, msg, True)

    def show_error(self, error_message):
        signalBus.infobar_message.emit({"status": "failed", "msg": error_message})

    def Save_device_Config(self):
        """
        保存设备连接信息
        """
        controller_type = get_controller_type(
            self.Control_Combox.currentText(), maa_config_data.interface_config_path
        )
        target = self.Autodetect_combox.currentText()
        result = None
        if controller_type == "Adb":
            for i in self.devices:
                if f"{i.name} ({i.address.split(':')[-1]})" == target:
                    result = i
                    break
            if result:
                maa_config_data.config.get("adb", {})["adb_path"] = str(result.adb_path)
                maa_config_data.config.get("adb", {})["address"] = result.address
                maa_config_data.config.get("adb", {})["config"] = result.config
                Save_Config(maa_config_data.config_path, maa_config_data.config)
                signalBus.update_adb.emit()
        elif controller_type == "Win32":
            for i in self.win32_hwnd:
                if i.window_name == target:
                    result = i
                    break
            if result:
                hwid = int(result.hwnd)
                maa_config_data.config["win32"]["hwnd"] = hwid
                Save_Config(maa_config_data.config_path, maa_config_data.config)

    def _format_hour(self, hour: int) -> str:
        """
        将小时数格式化为中文时间
        """
        return f"{hour:02d}:00"

    def _format_weekday(self, weekday: int) -> str:
        """
        将数字转换为中文星期
        """
        weekdays = [
            self.tr("Sunday"),
            self.tr("Monday"),
            self.tr("Tuesday"),
            self.tr("Wednesday"),
            self.tr("Thursday"),
            self.tr("Friday"),
            self.tr("Saturday"),
        ]
        return weekdays[weekday % 7]

    def get_this_monday_5am(self):
        """
        获取本周一上午5点的时间

                Returns:
                    QDateTime: 本周一上午5点的QDateTime对象

        """
        today = datetime.now()
        # 计算到本周一的天数差 (周一的weekday()是0)
        days_until_monday = (0 - today.weekday()) % 7
        monday = today + timedelta(days=days_until_monday)
        monday_5am = datetime(monday.year, monday.month, monday.day, 5, 0)
        return QDateTime.fromSecsSinceEpoch(int(monday_5am.timestamp()))
