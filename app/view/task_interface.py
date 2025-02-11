import os
import subprocess
import platform
from qasync import asyncSlot
import asyncio
from pathlib import Path
import json
from typing import List, Dict
import re


from PyQt6.QtCore import Qt, QMimeData
from PyQt6.QtGui import QDrag, QDropEvent, QColor, QFont
from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QListWidgetItem,
    QSizePolicy,
    QVBoxLayout,
    QSpacerItem,
)
from qfluentwidgets import InfoBar, InfoBarPosition, BodyLabel, ComboBox

from ..view.UI_task_interface import Ui_Task_Interface
from ..utils.notification import MyNotificationHandler
from ..components.click_label import ClickableLabel
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
)
from ..utils.maafw import maafw
from ..common.config import cfg
from maa.toolkit import AdbDevice
from ..utils.logger import logger
from ..common.maa_config_data import maa_config_data
from ..utils.notice import dingtalk_send, lark_send, SMTP_send, WxPusher_send
from datetime import datetime


class TaskInterface(Ui_Task_Interface, QWidget):
    devices = []
    start_again = False
    need_runing = False

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setupUi(self)

        maafw.notification_handler = MyNotificationHandler()
        self.bind_signals()
        self.init_widget_text()
        if cfg.get(cfg.resource_exist):
            self.init_ui()

        else:
            logger.warning("资源缺失")
            self.show_error(self.tr("Resource file not detected"))
    def init_widget_text(self):
        """
        初始化文本
        """
        self.AddTask_Button.setText(self.tr("Add Task"))
        self.Resource_Title.setText(self.tr("Resource"))
        self.Control_Title.setText(self.tr("Controller"))
        self.AutoDetect_Button.setText(self.tr("Auto Detect"))
        self.Finish_title.setText(self.tr("Finish"))
        self.Delete_label.setText(self.tr("Delete"))
        self.S2_Button.setText(self.tr("Start"))

    def resizeEvent(self, event):
        """
        当窗口大小改变时，重新设置所有 任务选项下拉框和doc 的宽度。
        """
        super().resizeEvent(event)
        scroll_area_width = self.scroll_area.width()
        for i in range(self.Option_Label.count()):
            layout = self.Option_Label.itemAt(i).layout()
            if layout is not None:
                for j in range(layout.count()):
                    widget = layout.itemAt(j).widget()
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

        else:
            logger.info("资源缺失,清空界面")
            self.enable_widgets(False)
            self.clear_content()
            self.Finish_combox_cfg.hide()
            self.Finish_combox_res.hide()

    def init_ui(self):
        # 初始化组件
        self.Start_Status(
            interface_Path=maa_config_data.interface_config_path,
            maa_pi_config_Path=maa_config_data.config_path,
            resource_Path=maa_config_data.resource_path,
        )
        self.init_finish_combox()

    def clear_content(self):
        self.clear_layout()
        self.Task_List.clear()
        self.SelectTask_Combox_1.clear()
        self.Resource_Combox.clear()
        self.Control_Combox.clear()
        self.Autodetect_combox.clear()
        self.Finish_combox.clear()
        self.Autodetect_combox.clear()

    def enable_widgets(self, enable: bool):
        """启用或禁用所有可交互控件。"""
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
        signalBus.update_download_finished.connect(self.show_update_info)
        signalBus.custom_info.connect(self.show_custom_info)
        signalBus.resource_exist.connect(self.resource_exist)
        signalBus.Notice_msg.connect(self.print_notice)
        signalBus.callback.connect(self.callback)
        signalBus.update_task_list.connect(self.update_task_list_passive)
        signalBus.update_finished_action.connect(self.init_finish_combox)
        signalBus.start_finish.connect(self.ready_Start_Up)
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

    # endregion
    def show_update_info(self, msg):
        if msg["status"] == "success":
            InfoBar.success(
                self.tr("successful"),
                msg["msg"],
                duration=5000,
                parent=self,
            )
        elif msg["status"] == "failed":
            InfoBar.error(
                self.tr("Update failed"),
                msg["msg"],
                duration=10000,
                parent=self,
            )
        elif msg["status"] == "info":
            InfoBar.info(
                self.tr("info"),
                msg["msg"],
                duration=10000,
                parent=self,
            )

    def show_custom_info(self, msg):
        """
        自定义动作/识别器信息
        """
        if msg["type"] == "action":
            self.insert_colored_text(self.tr("Load Custom Action:") + " " + msg["name"])
        elif msg["type"] == "recognition":
            self.insert_colored_text(
                self.tr("Load Custom Recognition:") + " " + msg["name"]
            )

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

        # 找到并删除对应的 task
        Task_List: List[Dict[str, str]] = Get_Values_list2(
            maa_config_data.config_path, "task"
        )
        for index, task in enumerate(Task_List):
            if task.get("name") == dropped_text:
                del Task_List[index]
                self.Task_List.takeItem(
                    self.Task_List.currentRow()
                )  # 从列表中移除对应项
                break  # 找到并删除后退出循环
        maa_config_data.config["task"] = Task_List
        Save_Config(maa_config_data.config_path, maa_config_data.config)
        event.acceptProposedAction()
        self.update_task_list()
        self.Task_List.setCurrentRow(-1)
        self.AddTask_Button.setText(self.tr("Add Task"))
        self.Delete_label.setText("")
        self.Delete_label.setStyleSheet("background-color: rgba(255, 255, 255, 0);")

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
    def print_notice(self, message: str):
        """
        打印外部通知信息
        """
        if "DingTalk Failed".lower() in message.lower():
            self.insert_colored_text(self.tr("DingTalk Failed"))
        elif "Lark Failed".lower() in message.lower():
            self.insert_colored_text(self.tr("Lark Failed"))
        elif "SMTP Failed".lower() in message.lower():
            self.insert_colored_text(self.tr("SMTP Failed"))
        elif "WxPusher Failed".lower() in message.lower():
            self.insert_colored_text(self.tr("WxPusher Failed"))
        elif "DingTalk Success".lower() in message.lower():
            self.insert_colored_text(self.tr("DingTalk Success"))
        elif "Lark Success".lower() in message.lower():
            self.insert_colored_text(self.tr("Lark Success"))
        elif "SMTP Success".lower() in message.lower():
            self.insert_colored_text(self.tr("SMTP Success"))
        elif "WxPusher Success".lower() in message.lower():
            self.insert_colored_text(self.tr("WxPusher Success"))
        else:
            self.insert_colored_text(message)

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
                self.insert_colored_text(
                    message["task"] + " " + self.tr("Failed"), "red"
                )
                logger.debug(f"{message["task"]} 任务失败")
                self.send_notice("failed", message["task"])
        if message["name"] == "on_task_recognition":
            task = message["task"]
            pipeline: dict = self.pipeline_override.get(task)
            if pipeline:
                if message["status"] == 1 and pipeline.get("focus_tip"):
                    self.insert_colored_text(
                        pipeline["focus_tip"],
                        pipeline.get("focus_tip_color", "black"),
                    )

                elif message["status"] == 2 and pipeline.get("focus_succeeded"):
                    self.insert_colored_text(
                        pipeline["focus_succeeded"],
                        pipeline.get("focus_succeeded_color", "black"),
                    )

                elif message["status"] == 3 and pipeline.get("focus_failed"):
                    self.insert_colored_text(
                        pipeline["focus_failed"],
                        pipeline.get("focus_failed_color", "black"),
                    )

    def insert_colored_text(self, text, color_name: str = "black"):
        """
        插入带颜色的文本
        """
        color = QColor(color_name.lower())
        if not color.isValid():
            color = QColor("black")
            logger.error(f"无效颜色 '{color_name}', 使用默认颜色 'black'")

        now = datetime.now().strftime("%H:%M")
        time = ClickableLabel(self)
        time.setAlignment(Qt.AlignmentFlag.AlignTop)
        time.setText(now)

        message = ClickableLabel(self)
        message.setAlignment(Qt.AlignmentFlag.AlignTop)
        message.setText(text)
        message.setTextColor(color)

        count = self.right_layout.rowCount()
        index = count - 1 if count > 1 else 0
        self.right_layout.insertRow(index, time, message)
        scrollbar = self.scroll_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def clear_layout(self):
        while self.right_layout.rowCount() > 0:
            self.right_layout.removeRow(0)
        label = ClickableLabel()
        label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.right_layout.addRow(label, label)

    def Start_Status(
        self, interface_Path: str, maa_pi_config_Path: str, resource_Path: str
    ):
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
        return (
            os.path.exists(resource_Path)
            and os.path.exists(interface_Path)
            and os.path.exists(maa_pi_config_Path)
        )

    def load_config_and_resources(
        self, interface_Path, maa_pi_config_Path, resource_Path
    ):
        logger.info("配置文件存在")
        return_init = gui_init(resource_Path, maa_pi_config_Path, interface_Path)
        self.Task_List.addItems(Get_Values_list_Option(maa_pi_config_Path, "task"))
        self.Resource_Combox.addItems(Get_Values_list(interface_Path, key1="resource"))
        self.Control_Combox.addItems(Get_Values_list(interface_Path, key1="controller"))
        self.SelectTask_Combox_1.addItems(Get_Values_list(interface_Path, key1="task"))

        if return_init is not None:
            self.Resource_Combox.setCurrentIndex(
                return_init.get("init_Resource_Type", 0)
            )
            self.Control_Combox.setCurrentIndex(
                return_init.get("init_Controller_Type", 0)
            )
            print(return_init.get("init_Controller_Type", 0))
        self.add_Controller_combox()

    def load_interface_options(self, interface_Path):
        self.Resource_Combox.addItems(Get_Values_list(interface_Path, key1="resource"))
        self.Resource_Combox.setCurrentIndex(0)
        self.Control_Combox.addItems(Get_Values_list(interface_Path, key1="controller"))
        self.SelectTask_Combox_1.addItems(Get_Values_list(interface_Path, key1="task"))

    def rewrite_Completion_Options(self):
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
        finish_option_res = self.Finish_combox_res.currentIndex()
        maa_config_data.config["finish_option_res"] = finish_option_res
        Save_Config(maa_config_data.config_path, maa_config_data.config)

    def Save_Finish_Option_Cfg(self):
        finish_option_cfg = self.Finish_combox_cfg.currentIndex()
        maa_config_data.config["finish_option_cfg"] = finish_option_cfg
        Save_Config(maa_config_data.config_path, maa_config_data.config)

    # region 完成后的动作
    def close_application(self):
        """
        关闭模拟器
        """
        if maa_config_data.config.get("emu_path") != "":
            self.app_process.terminate()
            try:
                self.app_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.app_process.kill()
        adb_path = maa_config_data.config.get("adb").get("adb_path")

        emu_dict = get_console_path(adb_path)
        if emu_dict["type"] == "mumu":
            adb_port = maa_config_data.config.get("adb").get("address").split(":")[1]
            emu = subprocess.run(
                [emu_dict["path"], "info", "-v", "all"],
                shell=True,
                capture_output=True,
                text=True,
                check=True,
                encoding="utf-8",
            )
            multi_dict: Dict[str, Dict[str, str]] = json.loads(emu.stdout.strip())

            print(multi_dict.get("created_timestamp", False))
            if multi_dict.get("created_timestamp", False):
                logger.debug(f"单模拟器")
                logger.debug(f"MuMuManager.exe info -v all: {multi_dict}")

                logger.debug(f"关闭序号{str(multi_dict.get("index"))}")
                if str(multi_dict.get("adb_port")) == adb_port:
                    subprocess.run(
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
                    )
                    print(str(multi_dict.get("index")))
                return
            logger.debug(f"多模拟器")
            logger.debug(f"MuMuManager.exe info -v all: {multi_dict}")

            for emu_key, emu_data in multi_dict.items():
                logger.debug(f"设备信息: {emu_data}")
                if str(emu_data.get("adb_port")) == adb_port:

                    subprocess.run(
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
                    )
                    logger.debug(f"关闭序号{str(emu_data.get("index"))}")
            return
        elif emu_dict["type"] == "LD":
            ld_pid = (
                maa_config_data.config.get("adb")
                .get("config")
                .get("extras")
                .get("ld")
                .get("pid")
            )
            if ld_pid:
                logger.debug(f"关闭LD进程: {ld_pid}")
                subprocess.run(
                    [
                        "taskkill",
                        "/F",
                        "/PID",
                        str(ld_pid),
                    ],
                    shell=True,
                    check=True,
                    encoding="utf-8",
                )
            return

        elif emu_dict["type"] == "BlueStacks":
            pass
        elif emu_dict["type"] == "Nox":
            pass
        elif emu_dict["type"] == "Memu":
            pass

    def close_application_and_quit(self):
        self.close_application()
        QApplication.quit()

    def shutdown(self):
        shutdown_commands = {
            "Windows": "shutdown /s /t 1",
            "Linux": "shutdown now",
            "Darwin": "sudo shutdown -h now",  # macOS
        }
        os.system(shutdown_commands.get(platform.system(), ""))

    def run_other_config(self):
        data_dict = {
            "resource_name": self.Finish_combox_res.currentText(),
            "config_name": self.Finish_combox_cfg.currentText(),
        }
        signalBus.switch_config.emit(data_dict)

    # endregion
    def start_process(self, command):
        try:
            logger.debug(f"启动程序: {command}")
            return subprocess.Popen(command)
        except:
            logger.exception(f"启动程序失败:\n ")
            show_error_message()

    def ready_Start_Up(self):
        if cfg.get(cfg.resource_exist):
            if cfg.get(cfg.auto_update_resource):
                logger.info("启动GUI后自动更新")
                signalBus.auto_update.emit()

            if cfg.get(cfg.run_after_startup) or cfg.get(cfg.run_after_startup_arg):
                logger.info("启动GUI后运行任务")
                self.start_again = True
                signalBus.start_task_inmediately.emit()

    # region 任务逻辑
    @asyncSlot()
    async def Start_Up(self):
        """
        开始任务
        """
        if not cfg.get(cfg.resource_exist):
            return
        self.need_runing = True
        self.update_S2_Button("Stop", self.Stop_task, enable=False)
        self.clear_layout()

        PROJECT_DIR = maa_config_data.resource_path
        controller_type = get_controller_type(
            self.Control_Combox.currentText(), maa_config_data.interface_config_path
        )

        # 启动前脚本
        if not await self.run_before_start_script():
            return

        # 加载资源
        if not await self.load_resources(PROJECT_DIR):
            return

        # 连接控制器
        if not await self.connect_controller(controller_type):
            return

        # 运行任务
        await self.run_tasks()

        # 结束后脚本
        await self.run_after_finish_script()

        # 完成后运行
        await self.execute_finish_action()

        # 更改按钮状态
        self.update_S2_Button("Start", self.Start_Up)
        self.start_again = True

    # endregion
    def update_S2_Button(self, text, slot, enable=True):
        """
        更新按钮状态
        """
        self.S2_Button.setText(self.tr(text))
        self.S2_Button.clicked.disconnect()
        self.S2_Button.clicked.connect(slot)
        self.S2_Button.setEnabled(enable)

    async def run_before_start_script(self):
        """
        运行前脚本
        """
        run_before_start = []
        run_before_start_path = maa_config_data.config.get("run_before_start")
        if run_before_start_path and self.need_runing:
            run_before_start.append(run_before_start_path)
            run_before_start_args: str = maa_config_data.config.get(
                "run_before_start_args"
            )
            if run_before_start_args:
                run_before_start.extend(run_before_start_args.split())
            logger.info(f"运行前脚本{run_before_start}")
            try:
                self.run_before_start_process = self.start_process(run_before_start)
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

        for i in maa_config_data.interface_config["resource"]:
            if i["name"] == resource_target:
                logger.debug(f"加载资源: {i['path']}")
                resource_path = i["path"]

        if resource_path == "" and self.need_runing:
            logger.error(f"未找到目标资源: {resource_target}")
            await maafw.stop_task()
            self.update_S2_Button("Start", self.Start_Up)
            return False

        self.pipelines = {}
        for i in resource_path:
            resource = (
                i.replace("{PROJECT_DIR}", PROJECT_DIR)
                .replace("/", os.sep)
                .replace("\\", os.sep)
            )
            logger.debug(f"加载资源: {resource}")
            pipelines_path = os.path.join(resource, "pipeline")

            if not (os.path.exists(pipelines_path) and os.path.isdir(pipelines_path)):
                logger.error(f"资源目录不存在: {pipelines_path}")
                await maafw.stop_task()
                self.update_S2_Button("Start", self.Start_Up)
                return False

            if not await self.load_pipelines(pipelines_path):
                return False

            await maafw.load_resource(resource)
            logger.debug(f"资源加载完成: {resource}")
        return True

    async def load_pipelines(self, pipelines_path):
        """
        加载pipeline
        """
        for filename in os.listdir(pipelines_path):
            if filename.endswith(".json"):
                file_path = os.path.join(pipelines_path, filename)
                try:
                    with open(file_path, "r", encoding="utf-8") as file:
                        data = json.load(file)
                        self.pipelines.update(data)
                    logger.debug(f"成功读取并解析 JSON 文件: {file_path}")
                except json.JSONDecodeError as e:
                    logger.error(f"解析 JSON 文件时出错: {file_path}, 错误信息: {e}")
                    await maafw.stop_task()
                    self.update_S2_Button("Start", self.Start_Up)
                    return False
                except Exception as e:
                    logger.error(f"读取 JSON 文件时出错: {file_path}, 错误信息: {e}")
                    await maafw.stop_task()
                    self.update_S2_Button("Start", self.Start_Up)
                    return False
        return True

    async def connect_controller(self, controller_type):
        """
        连接控制器
        """
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
        if not await self.connect_adb():
            # 如果连接失败，尝试启动模拟器
            if not await self.start_emulator():
                self.send_notice("failed", self.tr("Connection"))
                self.insert_colored_text(self.tr("Connection Failed"))
                await maafw.stop_task()
                self.update_S2_Button("Start", self.Start_Up)
                return False
            # 再次尝试连接 ADB
            if not await self.connect_adb():
                logger.error(
                    f"连接adb失败\n{maa_config_data.config['adb']['adb_path']}\n{maa_config_data.config['adb']['address']}\n{maa_config_data.config['adb']['input_method']}\n{maa_config_data.config['adb']['screen_method']}\n{maa_config_data.config['adb']['config']}"
                )
                self.send_notice("failed", self.tr("Connection"))
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
        config = {} if self.start_again else maa_config_data.config["adb"]["config"]
        if (
            not await maafw.connect_adb(
                maa_config_data.config["adb"]["adb_path"],
                maa_config_data.config["adb"]["address"],
                maa_config_data.config["adb"]["input_method"],
                maa_config_data.config["adb"]["screen_method"],
                config,
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
            emu_wait_time = int(maa_config_data.config.get("emu_wait_time"))
            if emu_args:
                emu.extend(emu_args.split())
            logger.info(f"启动模拟器{emu}")
            try:
                self.app_process = self.start_process(emu)
                logger.info(f"模拟器启动成功，PID: {self.app_process.pid}")
            except FileNotFoundError as e:
                self.show_error(self.tr("File not found"))
                logger.error(f'启动模拟器"{e}"')
                await maafw.stop_task()
                return False
            self.insert_colored_text(self.tr("waiting for emulator start..."))
            self.update_S2_Button("Stop", self.Stop_task)
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
            emu_type = maa_config_data.config.get("adb").get("adb_path")
            if "LDPlayer" in emu_type:
                logger.debug("获取雷电模拟器pid")
                device = await maafw.detect_adb()
                for i in device:
                    if i.name == "LDPlayer":
                        if (
                            maa_config_data.config["adb"]["config"].get("extras")
                            is None
                        ):
                            logger.debug("extras不存在，创建")
                            maa_config_data.config["adb"]["config"] = i.config
                        else:
                            logger.debug("extras存在，更新pid")
                            maa_config_data.config["adb"]["config"]["extras"]["ld"][
                                "pid"
                            ] = (i.config.get("extras").get("ld").get("pid"))
                        logger.debug(
                            f"获取到pid: {maa_config_data.config['adb']['config']['extras']['ld']['pid']}"
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
            exe_wait_time = int(maa_config_data.config.get("exe_wait_time"))
            exe_args: str = maa_config_data.config.get("exe_args")
            if exe_args:
                exe.extend(exe_args.split())
            logger.info(f"启动游戏{exe}")
            try:
                self.app_process = self.start_process(exe)
                logger.info(f"游戏启动成功，PID: {self.app_process.pid}")
            except FileNotFoundError as e:
                self.show_error(self.tr("File not found"))
                logger.error(f'启动游戏"{e}"')
                await maafw.stop_task()
                return False
            self.insert_colored_text(self.tr("Starting game..."))
            self.update_S2_Button("Stop", self.Stop_task)
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
                maa_config_data.config["win32"]["hwnd"],
                maa_config_data.config["win32"]["input_method"],
                maa_config_data.config["win32"]["screen_method"],
            )
            and self.need_runing
        ):
            logger.error(
                f"连接Win32失败 \n{maa_config_data.config['win32']['hwnd']}\n{maa_config_data.config['win32']['input_method']}\n{maa_config_data.config['win32']['screen_method']}"
            )
            self.send_notice("failed", self.tr("Connection"))
            self.insert_colored_text(self.tr("Connection Failed"))
            await maafw.stop_task()
            self.update_S2_Button("Start", self.Start_Up)
            return False
        return True

    async def run_tasks(self):
        """
        运行任务
        """
        self.S2_Button.setEnabled(True)
        for task_list in maa_config_data.config["task"]:
            override_options = {}
            if not self.need_runing:
                await maafw.stop_task()
                return
            for index, task_enter in enumerate(
                maa_config_data.interface_config["task"]
            ):
                if task_enter["name"] == task_list["name"]:
                    self.entry = task_enter["entry"]
                    enter_index = index
                    break
            if maa_config_data.interface_config["task"][enter_index].get(
                "pipeline_override", False
            ):
                override_options.update(
                    maa_config_data.interface_config["task"][enter_index][
                        "pipeline_override"
                    ]
                )
                self.pipeline_override: dict = self.pipelines
                self.pipeline_override.update(override_options)
                logger.debug(
                    f"覆盖选项:\n{json.dumps(override_options, indent=4,ensure_ascii=False)}"
                )
            else:
                self.pipeline_override: dict = self.pipelines
            if task_list["option"] != []:
                for task_option in task_list["option"]:
                    for override in maa_config_data.interface_config["option"][
                        task_option["name"]
                    ]["cases"]:
                        if override["name"] == task_option["value"]:
                            override_options.update(override["pipeline_override"])
            logger.info(
                f"运行任务:{self.entry}\n任务选项:\n{json.dumps(override_options, indent=4,ensure_ascii=False)}"
            )
            self.pipeline_override.update(override_options)
            await maafw.run_task(self.entry, override_options)
        logger.info("任务完成")
        self.send_notice("completed")

    async def run_after_finish_script(self):
        """
        运行后脚本
        """
        run_after_finish = []
        run_after_finish_path = maa_config_data.config.get("run_after_finish")
        if run_after_finish_path and self.need_runing:
            run_after_finish.append(run_after_finish_path)
            run_after_finish_args: str = maa_config_data.config.get(
                "run_after_finish_args"
            )
            if run_after_finish_args:
                run_after_finish.extend(run_after_finish_args.split())
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
        actions = {
            1: self.close_application,
            2: QApplication.quit,
            3: self.close_application_and_quit,
            4: self.shutdown,
            5: self.run_other_config,
        }
        actions_text = {
            0: self.tr("Do Nothing"),
            1: self.tr("Close emulator"),
            2: self.tr("Quit Application"),
            3: self.tr("Close Application and Quit"),
            4: self.tr("Shutdown"),
            5: self.tr("Run Other Config"),
        }
        action = actions.get(target)
        logger.info(f"选择的动作: {actions_text[target]}")
        if action and self.need_runing:
            action()

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
        self.start_again = True
        await maafw.stop_task()

    def kill_adb_process(self):
        adb_path = maa_config_data.config["adb"]["adb_path"]
        if adb_path == "":
            return
        try:
            subprocess.run([adb_path, "kill-server"], check=True)
            logger.info("杀死ADB进程")
        except subprocess.CalledProcessError as e:
            logger.error(f"杀死ADB进程失败: {e}")

    def task_list_changed(self):
        self.Task_List.clear()
        self.Task_List.addItems(
            Get_Values_list_Option(maa_config_data.config_path, "task")
        )

    def dragging_finished(self):
        self.AddTask_Button.setText(self.tr("Add Task"))
        self.Task_List.setCurrentRow(-1)
        self.Delete_label.setText("")
        self.Delete_label.setStyleSheet("background-color: rgba(255, 0);")

    def Add_Task(self):
        if maa_config_data.config == {}:
            return
        # 如果选中了任务的某项,则修改该项任务
        if self.Task_List.currentRow() != -1:
            Select_index = self.Task_List.currentRow()
            Select_Target = self.SelectTask_Combox_1.currentText()
            Option = self.get_selected_options()
            del maa_config_data.config["task"][Select_index]
            maa_config_data.config["task"].insert(
                Select_index,
                {
                    "name": Select_Target,
                    "option": Option,
                },
            )

        else:
            Select_Target = self.SelectTask_Combox_1.currentText()
            Option = self.get_selected_options()
            maa_config_data.config["task"].append(
                {"name": Select_Target, "option": Option}
            )

        Save_Config(maa_config_data.config_path, maa_config_data.config)

        self.update_task_list()
        self.dragging_finished()

    def Add_All_Tasks(self):
        if maa_config_data.config == {}:
            return

        for task in maa_config_data.interface_config["task"]:
            selected_value = []
            task_name = task.get("name")
            options = task.get("option")
            if options:
                for pipeline_option in options:
                    target = maa_config_data.interface_config["option"][
                        pipeline_option
                    ]["cases"][0]["name"]
                    selected_value.append(target)

            options_dicts = []
            if options:
                for i, option_name in enumerate(options):
                    # 如果有option，则选择对应的项作为值
                    options_dicts.append(
                        {"name": option_name, "value": selected_value[i]}
                    )
            maa_config_data.config["task"].append(
                {"name": task_name, "option": options_dicts}
            )

        # 保存配置
        Save_Config(maa_config_data.config_path, maa_config_data.config)

        # 更新任务列表
        self.update_task_list()

    def update_task_list(self):
        """更新任务列表"""
        signalBus.update_task_list.emit()

    def update_task_list_passive(self):
        """更新任务列表(被动刷新)"""
        self.Task_List.clear()
        self.Task_List.addItems(
            Get_Values_list_Option(cfg.get(cfg.maa_config_path), "task")
        )

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
        self.Task_List.clear()
        maa_config_data.config["task"] = []
        Save_Config(maa_config_data.config_path, maa_config_data.config)
        self.dragging_finished()
        self.update_task_list()

    def Move_Up(self):
        self.move_task(direction=-1)

    def Move_Top(self):
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
        self.move_task(direction=1)

    def Move_Bottom(self):
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
        self.Delete_label.setText(self.tr("Drag to Delete"))
        self.Delete_label.setStyleSheet("background-color: rgba(255, 0, 0, 0.5);")

        self.AddTask_Button.setText(self.tr("Rewrite"))
        Select_Target = self.Task_List.currentRow()
        if Select_Target == -1:
            return
        # 将task_combox的内容设置为选中项目
        self.SelectTask_Combox_1.setCurrentText(
            maa_config_data.config["task"][Select_Target]["name"]
        )
        self.restore_options(maa_config_data.config["task"][Select_Target]["option"])

    def restore_options(self, selected_options: List[Dict[str, str]]):
        layout = self.Option_Label
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
                            if isinstance(combo_box, ComboBox):
                                combo_box.setCurrentText(value)
                                break
                        break

    def Save_Resource(self):
        self.update_config_value("resource", self.Resource_Combox.currentText())
        logger.info(f"保存资源配置: {self.Resource_Combox.currentText()}")

    def Save_Controller(self):
        self.Resource_Combox.currentData
        Controller_Type_Select = self.Control_Combox.currentText()
        controller_type = get_controller_type(
            Controller_Type_Select, maa_config_data.interface_config_path
        )
        if controller_type == "Adb":
            self.add_Controller_combox()

        elif controller_type == "Win32":
            self.Start_Detection()
        logger.info(f"保存控制器配置: {Controller_Type_Select}")
        # 更新配置并保存
        maa_config_data.config["controller"]["name"] = Controller_Type_Select
        Save_Config(maa_config_data.config_path, maa_config_data.config)  # 刷新保存

    def add_Controller_combox(self):
        controller_type = get_controller_type(
            self.Control_Combox.currentText(), maa_config_data.interface_config_path
        )
        self.Autodetect_combox.clear()
        if controller_type == "Adb":

            emulators_name = check_path_for_keyword(
                maa_config_data.config["adb"]["adb_path"]
            )
            self.Autodetect_combox.clear()
            self.Autodetect_combox.addItem(
                f"{emulators_name} ({maa_config_data.config['adb']['address'].split(':')[-1]})"
            )

    def update_config_value(self, key, value):
        maa_config_data.config[key] = value  # 更新实例变量
        Save_Config(maa_config_data.config_path, maa_config_data.config)  # 刷新保存

    def Add_Select_Task_More_Select(self):
        select_target = self.SelectTask_Combox_1.currentText()

        self.show_task_options(select_target, maa_config_data.interface_config)

    def show_task_options(
        self, select_target, MAA_Pi_Config: Dict[str, List[Dict[str, str]]]
    ):
        self.clear_extra_widgets()

        layout = self.Option_Label

        for task in MAA_Pi_Config["task"]:
            if task["name"] == select_target:
                # 处理 option 字段
                options = task.get("option")
                if options:
                    for option in options:
                        v_layout = QVBoxLayout()

                        label = BodyLabel(self)
                        label.setText(option)
                        label.setFont(QFont("Arial", 10))
                        v_layout.addWidget(label)

                        select_box = ComboBox(self)
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

                        layout.addLayout(v_layout)

                # 处理 doc 字段
                doc = task.get("doc")
                if doc:
                    if isinstance(doc, list):
                        doc = "\n".join(doc)
                    doc_layout = QVBoxLayout()
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
                    html_text = re.sub(r"\[/size\]", "</span>", html_text)

                    # 解析粗体
                    html_text = html_text.replace("[b]", "<b>").replace("[/b]", "</b>")

                    # 解析斜体
                    html_text = html_text.replace("[i]", "<i>").replace("[/i]", "</i>")

                    # 解析下划线
                    html_text = html_text.replace("[u]", "<u>").replace("[/u]", "</u>")

                    # 解析删除线
                    html_text = html_text.replace("[s]", "<s>").replace("[/s]", "</s>")

                    # 将换行符替换为 <br>
                    html_text = html_text.replace("\n", "<br>")

                    doc_label.setText(html_text)
                    doc_layout.addWidget(doc_label)
                    layout.addLayout(doc_layout)

                spacer = QSpacerItem(
                    0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
                )
                layout.addItem(spacer)

                break

    def get_selected_options(self):
        selected_options = []
        layout = self.Option_Label
        name = None
        selected_value = None

        for i in range(layout.count()):
            item = layout.itemAt(i)
            if not isinstance(item, QVBoxLayout):
                continue  # 如果item不是QVBoxLayout，跳过本次循环
            for j in range(item.count()):
                widget = item.itemAt(j).widget()
                if isinstance(widget, BodyLabel):
                    name = widget.text()
                elif isinstance(widget, ComboBox):
                    selected_value = widget.currentText()
            if name and selected_value:
                selected_options.append({"name": name, "value": selected_value})

        return selected_options

    def clear_extra_widgets(self):
        print("清除额外的控件")
        layout = self.Option_Label
        if layout is None:
            return

        while layout.count():
            item = layout.takeAt(0)
            if item is None:
                continue

            if isinstance(item, QSpacerItem):
                continue

            sub_layout = item.layout()
            if sub_layout is None:
                continue

            while sub_layout.count():
                sub_item = sub_layout.takeAt(0)
                if sub_item is None:
                    continue

                widget = sub_item.widget()
                if widget is not None:
                    print(f"{widget} 删除")
                    widget.deleteLater()

    @asyncSlot()
    async def Start_Detection(self):
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
            for i in maa_config_data.interface_config["controller"]:
                if i["type"] == "Win32":
                    self.win32_hwnd = await maafw.detect_win32hwnd(
                        i["win32"]["window_regex"]
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
            self.show_success(success_message)
            self.Autodetect_combox.clear()
            processed_list = list(set(processed_list))
            self.Autodetect_combox.addItems(processed_list)

        # 重新启用按钮
        self.AutoDetect_Button.setEnabled(True)
        self.S2_Button.setEnabled(True)

    async def Adb_detect_backup(self):
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
        """发送通知
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

        dingtalk_send(msg, cfg.get(cfg.Notice_DingTalk_status))
        lark_send(msg, cfg.get(cfg.Notice_Lark_status))
        SMTP_send(msg, cfg.get(cfg.Notice_SMTP_status))
        WxPusher_send(msg, cfg.get(cfg.Notice_WxPusher_status))

    def show_success(self, message):
        InfoBar.success(
            title=self.tr("Success"),
            content=message,
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.BOTTOM_RIGHT,
            duration=2000,
            parent=self,
        )

    def show_error(self, error_message):
        InfoBar.error(
            title=self.tr("Error"),
            content=error_message,
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.BOTTOM_RIGHT,
            duration=-1,
            parent=self,
        )

    def Save_device_Config(self):
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
                maa_config_data.config["adb"]["adb_path"] = str(result.adb_path)
                maa_config_data.config["adb"]["address"] = result.address
                maa_config_data.config["adb"]["config"] = result.config
                Save_Config(maa_config_data.config_path, maa_config_data.config)

                signalBus.update_adb.emit()
        elif controller_type == "Win32":
            for i in self.win32_hwnd:
                if i.window_name == target:
                    result = i
                    break
            if result:
                maa_config_data.config["win32"]["hwnd"] = result.hwnd
                Save_Config(maa_config_data.config_path, maa_config_data.config)
