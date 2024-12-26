import os
import subprocess
import platform
from qasync import asyncSlot
import asyncio
from pathlib import Path
import json

from PyQt6.QtCore import Qt, QMimeData
from PyQt6.QtGui import QDrag
from PyQt6.QtWidgets import QApplication, QWidget
from qfluentwidgets import InfoBar, InfoBarPosition

from ..view.UI_task_interface import Ui_Task_Interface
from ..utils.notification import MyNotificationHandler
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
)
from ..utils.maafw import maafw
from ..common.config import cfg
from maa.toolkit import AdbDevice
from ..utils.logger import logger
from ..common.maa_config_data import maa_config_data
from ..utils.notice import dingtalk_send, lark_send, SMTP_send, WxPusher_send


class TaskInterface(Ui_Task_Interface, QWidget):
    devices = []
    run_mode = "adb"
    start_again = False
    need_runing = False

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setupUi(self)

        maafw.notification_handler = MyNotificationHandler()
        self.bind_signals()

        if cfg.get(cfg.resource_exist):
            self.init_ui()

        else:
            logger.warning("资源缺失")
            self.show_error(self.tr("Resource file not detected"))

        self.toggle_task_options(False)

        # 隐藏不需要的组件
        self.MoveUp_Button.hide()
        self.MoveDown_Button.hide()
        self.Delete_Button.hide()

    def resource_exist(self, status: bool):
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
        # 读取配置文件并存储在实例变量中
        # 初始化组件
        self.Start_Status(
            interface_Path=maa_config_data.interface_config_path,
            maa_pi_config_Path=maa_config_data.config_path,
            resource_Path=maa_config_data.resource_path,
        )
        self.init_finish_combox()

    def clear_content(self):
        self.TaskOutput_Text.clear()
        self.Task_List.clear()
        self.SelectTask_Combox_1.clear()
        self.SelectTask_Combox_2.clear()
        self.SelectTask_Combox_3.clear()
        self.SelectTask_Combox_4.clear()
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
        self.Finish_combox.clear()
        self.Finish_combox_res.clear()
        self.Finish_combox_cfg.clear()
        finish_list = [
            self.tr("Do nothing"),
            self.tr("Close emulator"),
            self.tr("Close emulator and Quit app"),
            self.tr("Shutdown"),
            self.tr("Run Other Config"),
        ]
        finish_combox = maa_config_data.config.get("finish_option", 0)
        self.Finish_combox.addItems(finish_list)
        self.Finish_combox.setCurrentIndex(finish_combox)
        logger.info(f"完成选项初始化完成,当前选择项为{finish_combox}")
        if not finish_combox == 4:
            self.Finish_combox_cfg.hide()
            self.Finish_combox_res.hide()

        finish_combox_res = maa_config_data.config.get("finish_option_res", 0)
        self.Finish_combox_res.addItems(maa_config_data.resource_name_list)
        self.Finish_combox_res.setCurrentIndex(finish_combox_res)

        finish_combox_cfg = maa_config_data.config.get("finish_option_cfg", 0)
        self.Finish_combox_cfg.addItems(maa_config_data.config_name_list)
        self.Finish_combox_cfg.setCurrentIndex(finish_combox_cfg)

    def toggle_task_options(self, visible: bool):
        task_comboxes = [
            self.SelectTask_Combox_2,
            self.SelectTask_Combox_3,
            self.SelectTask_Combox_4,
        ]
        task_titles = [
            self.TaskName_Title_2,
            self.TaskName_Title_3,
            self.TaskName_Title_4,
        ]
        for combox in task_comboxes:
            combox.setVisible(visible)
        for title in task_titles:
            title.setVisible(visible)

    def bind_signals(self):
        signalBus.resource_exist.connect(self.resource_exist)
        signalBus.Notice_msg.connect(self.print_notice)
        signalBus.callback.connect(self.callback)
        signalBus.update_task_list.connect(self.update_task_list_passive)
        signalBus.update_finished_action.connect(self.init_finish_combox)
        signalBus.start_finish.connect(self.ready_Start_Up)
        signalBus.start_task_inmediately.connect(self.Start_Up)
        signalBus.dragging_finished.connect(self.Add_Task)
        self.AddTask_Button.clicked.connect(self.Add_Task)
        self.AddTask_Button.rightClicked.connect(self.Add_All_Tasks)
        self.Delete_Button.clicked.connect(self.Delete_Task)
        self.Delete_Button.rightClicked.connect(self.Delete_all_task)
        self.MoveUp_Button.clicked.connect(self.Move_Up)
        self.MoveUp_Button.rightClicked.connect(self.Move_Top)
        self.MoveDown_Button.clicked.connect(self.Move_Down)
        self.MoveDown_Button.rightClicked.connect(self.Move_Bottom)
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
        # self.Task_List.itemPressed.connect(self.startDrag)
        self.Delete_label.dragEnterEvent = self.dragEnter
        self.Delete_label.dropEvent = self.drop

    def dragEnter(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()
        else:
            event.ignore()

    def drop(self, event):
        dropped_text = event.mimeData().text()
        self.Delete_label.setText(self.tr("Delete: ") + dropped_text)
        if " " in dropped_text:
            dropped_text = dropped_text.split(" ")[0]

        # 找到并删除对应的 task
        Task_List = Get_Values_list2(maa_config_data.config_path, "task")
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
        self.Task_List.setCurrentRow(-1)
        self.AddTask_Button.setText(self.tr("Add Task"))

    def startDrag(self, item):
        drag = QDrag(self)
        mimeData = QMimeData()
        mimeData.setText(item.text())
        drag.setMimeData(mimeData)
        drag.exec(Qt.DropAction.MoveAction)

    def print_notice(self, message: str):
        if "DingTalk Failed".lower() in message.lower():
            self.TaskOutput_Text.append(self.tr("DingTalk Failed"))
        elif "Lark Failed".lower() in message.lower():
            self.TaskOutput_Text.append(self.tr("Lark Failed"))
        elif "SMTP Failed".lower() in message.lower():
            self.TaskOutput_Text.append(self.tr("SMTP Failed"))
        elif "WxPusher Failed".lower() in message.lower():
            self.TaskOutput_Text.append(self.tr("WxPusher Failed"))
        elif "DingTalk Success".lower() in message.lower():
            self.TaskOutput_Text.append(self.tr("DingTalk Success"))
        elif "Lark Success".lower() in message.lower():
            self.TaskOutput_Text.append(self.tr("Lark Success"))
        elif "SMTP Success".lower() in message.lower():
            self.TaskOutput_Text.append(self.tr("SMTP Success"))
        elif "WxPusher Success".lower() in message.lower():
            self.TaskOutput_Text.append(self.tr("WxPusher Success"))
        else:
            self.TaskOutput_Text.append(message)

    def callback(self, message: str):
        if "controller_action" in message:
            message_data = message.replace("controller_action:", "")
            if message_data == "1":
                self.TaskOutput_Text.append(self.tr("Starting Connection"))
            elif message_data == "2":
                self.TaskOutput_Text.append(self.tr("Connection Success"))
            elif message_data == "3":
                self.TaskOutput_Text.append(self.tr("Connection Failed"))
            elif message_data == "4":
                self.TaskOutput_Text.append(self.tr("Unknown Error"))
        elif "tasker_task" in message:
            message_data = message.replace("tasker_task:", "")
            if message_data == "3":
                self.TaskOutput_Text.append(self.entry + self.tr(" Failed"))
                logger.debug(f"{self.entry} 任务失败")
                self.send_notice("failed", self.entry)

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
            self.handle_missing_files(resource_Path, interface_Path, maa_pi_config_Path)

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

    def handle_missing_files(self, resource_Path, interface_Path, maa_pi_config_Path):
        if os.path.exists(resource_Path) and os.path.exists(interface_Path):
            logger.info("配置文件缺失")
            self.create_default_config(maa_pi_config_Path)
            self.load_interface_options(interface_Path)
        else:
            logger.warning("资源缺失")
            self.show_error(self.tr("Resource file not detected"))

    def create_default_config(self, maa_pi_config_Path):
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
            "run_after_finish": "",
            "emu_path": "",
            "emu_wait_time": 10,
            "exe_path": "",
            "exe_wait_time": 10,
            "exe_parameter": "",
        }
        Save_Config(maa_pi_config_Path, data)
        maa_config_data.config = data

    def load_interface_options(self, interface_Path):
        self.Resource_Combox.addItems(Get_Values_list(interface_Path, key1="resource"))
        self.Resource_Combox.setCurrentIndex(0)
        self.Control_Combox.addItems(Get_Values_list(interface_Path, key1="controller"))
        self.SelectTask_Combox_1.addItems(Get_Values_list(interface_Path, key1="task"))

    def rewrite_Completion_Options(self):
        finish_option = self.Finish_combox.currentIndex()
        maa_config_data.config["finish_option"] = finish_option
        if finish_option == 4:
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

    def close_application(self):
        if maa_config_data.config.get("emu_path") == "":
            return
        self.app_process.terminate()
        try:
            self.app_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.app_process.kill()

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

    def start_process(self, command):
        try:
            logger.debug(f"启动程序: {command}")
            return subprocess.Popen(command)
        except:
            logger.exception(f"启动程序失败:\n ")
            show_error_message()

    def ready_Start_Up(self):
        if cfg.get(cfg.resource_exist):
            if cfg.get(cfg.run_after_startup):
                logger.info("启动GUI后运行任务")
                self.start_again = True
                signalBus.start_task_inmediately.emit()

    @asyncSlot()
    async def Start_Up(self):
        if not cfg.get(cfg.resource_exist):
            return
        self.need_runing = True
        self.S2_Button.setEnabled(False)
        self.S2_Button.setText(self.tr("Stop"))
        self.S2_Button.clicked.connect(self.Stop_task)
        self.TaskOutput_Text.clear()

        PROJECT_DIR = maa_config_data.resource_path
        controller_type = get_controller_type(
            self.Control_Combox.currentText(), maa_config_data.interface_config_path
        )
        # 启动前脚本
        run_before_start = maa_config_data.config.get("run_before_start")
        if run_before_start != "" and self.need_runing:
            logger.info("运行前脚本")
            try:
                self.run_before_start_process = self.start_process(run_before_start)
            except FileNotFoundError as e:
                self.show_error(self.tr(f"File not found"))
                logger.error(f'运行前脚本"{e}"')
                await maafw.stop_task()
                return
            except OSError as e:
                self.show_error(self.tr(f"Can not start the file"))
                logger.error(f'运行前脚本"{e}"')
                await maafw.stop_task()
                return
        # 加载资源
        await maafw.load_resource("", True)
        resource_path = ""
        resource_target = self.Resource_Combox.currentText()

        for i in maa_config_data.interface_config["resource"]:
            if i["name"] == resource_target:
                logger.debug(f"加载资源: {i['path']}")
                resource_path = i["path"]

        if resource_path == "" and self.need_runing:
            logger.error(f"未找到目标资源: {resource_target}")
            await maafw.stop_task()
            self.S2_Button.setEnabled(True)
            self.S2_Button.setText(self.tr("Start"))
            self.S2_Button.clicked.disconnect()
            self.S2_Button.clicked.connect(self.Start_Up)
            return

        for i in resource_path:
            resource = (
                i.replace("{PROJECT_DIR}", PROJECT_DIR)
                .replace("/", os.sep)
                .replace("\\", os.sep)
            )
            logger.debug(f"加载资源: {resource}")
            await maafw.load_resource(resource)
            logger.debug(f"资源加载完成: {resource}")
        gpu_index = maa_config_data.config["gpu"]
        if gpu_index == -2 and self.need_runing:
            logger.debug("设置CPU推理")
            maafw.resource.set_cpu()
        elif gpu_index == -1 and self.need_runing:
            logger.debug("设置自动")
            maafw.resource.set_auto_device()
        else:
            logger.debug(f"设置GPU推理: {gpu_index}")
            maafw.resource.set_gpu(gpu_index)
        # 连接控制器
        if controller_type == "Adb" and self.need_runing:  # adb控制
            # 启动模拟器
            emu_path = maa_config_data.config.get("emu_path")
            if emu_path == "":
                logger.warning("未设置模拟器路径")
            emu_wait_time = int(maa_config_data.config.get("emu_wait_time"))
            if emu_path != "" and self.need_runing:
                logger.info(f"启动模拟器")
                self.app_process = self.start_process(emu_path)
                self.TaskOutput_Text.append(self.tr("waiting for emulator start..."))
                self.S2_Button.setEnabled(True)
                self.S2_Button.clicked.disconnect()
                self.S2_Button.clicked.connect(self.Stop_task)
                for i in range(int(emu_wait_time)):
                    if not self.need_runing:
                        await maafw.stop_task()
                        self.S2_Button.setEnabled(True)
                        self.S2_Button.setText(self.tr("Start"))
                        self.S2_Button.clicked.disconnect()
                        self.S2_Button.clicked.connect(self.Start_Up)
                        return
                    else:
                        self.TaskOutput_Text.append(
                            self.tr("Starting task in ") + f"{int(emu_wait_time) - i}"
                        )
                        await asyncio.sleep(1)

            # 连接adb失败
            if self.start_again:
                device = await maafw.detect_adb()
                config = {}
                for i in device:
                    if (
                        i.adb_path == maa_config_data.config["adb"]["adb_path"]
                        and i.address == maa_config_data.config["adb"]["address"]
                    ):
                        config = i.config
                        break
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
                    logger.error(
                        f"连接adb失败\n{maa_config_data.config['adb']['adb_path']}\n{maa_config_data.config['adb']['address']}\n{maa_config_data.config['adb']['input_method']}\n{maa_config_data.config['adb']['screen_method']}\n{maa_config_data.config['adb']['config']}"
                    )
                    self.TaskOutput_Text.append(self.tr("Connection Failed"))
                    await maafw.stop_task()
                    self.S2_Button.setEnabled(True)
                    self.S2_Button.setText(self.tr("Start"))
                    self.S2_Button.clicked.disconnect()
                    self.S2_Button.clicked.connect(self.Start_Up)
                    return
            else:
                if (
                    not await maafw.connect_adb(
                        maa_config_data.config["adb"]["adb_path"],
                        maa_config_data.config["adb"]["address"],
                        maa_config_data.config["adb"]["input_method"],
                        maa_config_data.config["adb"]["screen_method"],
                        maa_config_data.config["adb"]["config"],
                    )
                    and self.need_runing
                ):
                    logger.error(
                        f"连接adb失败\n{maa_config_data.config['adb']['adb_path']}\n{maa_config_data.config['adb']['address']}\n{maa_config_data.config['adb']['input_method']}\n{maa_config_data.config['adb']['screen_method']}\n{maa_config_data.config['adb']['config']}"
                    )
                    self.TaskOutput_Text.append(self.tr("Connection Failed"))
                    await maafw.stop_task()
                    self.S2_Button.setEnabled(True)
                    self.S2_Button.setText(self.tr("Start"))
                    self.S2_Button.clicked.disconnect()
                    self.S2_Button.clicked.connect(self.Start_Up)
                    return
        elif controller_type == "Win32" and self.need_runing:  # win32控制
            # 启动游戏
            exe_path = maa_config_data.config.get("exe_path")
            exe_wait_time = int(maa_config_data.config.get("exe_wait_time"))
            exe_parameter = maa_config_data.config.get("exe_parameter")
            if exe_path != "" and self.need_runing:
                logger.info(f"启动游戏")
                self.app_process = self.start_process(f"{exe_path} {exe_parameter}")
                self.TaskOutput_Text.append(self.tr("Starting game..."))
                self.S2_Button.setEnabled(True)
                self.S2_Button.clicked.disconnect()
                self.S2_Button.clicked.connect(self.Stop_task)
                for i in range(int(exe_wait_time)):
                    if not self.need_runing:
                        await maafw.stop_task()
                        self.S2_Button.setEnabled(True)
                        self.S2_Button.setText(self.tr("Start"))
                        self.S2_Button.clicked.disconnect()
                        self.S2_Button.clicked.connect(self.Start_Up)
                        return
                    else:
                        self.TaskOutput_Text.append(
                            self.tr("Starting game in ") + f"{int(exe_wait_time) - i}"
                        )
                        await asyncio.sleep(1)

            # 连接Win32失败
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
                self.TaskOutput_Text.append(self.tr("Connection Failed"))
                await maafw.stop_task()
                self.S2_Button.setEnabled(True)
                self.S2_Button.setText(self.tr("Start"))
                self.S2_Button.clicked.disconnect()
                self.S2_Button.clicked.connect(self.Start_Up)
                return

        # 任务过程
        self.S2_Button.setEnabled(True)
        # 遍历配置任务列表
        for task_list in maa_config_data.config["task"]:
            override_options = {}
            # 检查是否需要运行任务，如果不需要则停止当前任务并返回
            if not self.need_runing:
                await maafw.stop_task()
                return
            # 遍历interface任务列表
            for index, task_enter in enumerate(
                maa_config_data.interface_config["task"]
            ):
                if task_enter["name"] == task_list["name"]:
                    self.entry = task_enter["entry"]  # 找到任务入口
                    enter_index = index
                    break
            # 如果interface中有覆盖选项，则更新覆盖选项字典
            if maa_config_data.interface_config["task"][enter_index].get(
                "pipeline_override", False
            ):
                override_options.update(
                    maa_config_data.interface_config["task"][enter_index][
                        "pipeline_override"
                    ]
                )
                logger.debug(
                    f"覆盖选项:\n{json.dumps(override_options, indent=4,ensure_ascii=False)}"
                )
            if task_list["option"] != []:
                # 如果任务列表中有选项，则遍历每个选项
                for task_option in task_list["option"]:
                    # 遍历 MAA_Pi_Config 中与当前任务选项名称对应的 cases
                    for override in maa_config_data.interface_config["option"][
                        task_option["name"]
                    ]["cases"]:
                        # 找到与任务选项值匹配的覆盖情况
                        if override["name"] == task_option["value"]:
                            # 更新覆盖选项字典，添加当前覆盖情况的 pipeline_override
                            override_options.update(override["pipeline_override"])
                # 记录日志信息，包括任务名称和覆盖选项
            logger.info(
                f"运行任务:{self.entry}\n任务选项:\n{json.dumps(override_options, indent=4,ensure_ascii=False)}"
            )
            # 在任务输出文本框中添加任务运行信息
            self.TaskOutput_Text.append(self.tr("running task:") + f" {self.entry}")
            # 异步运行任务，并传入覆盖选项
            await maafw.run_task(self.entry, override_options)

        self.TaskOutput_Text.append(self.tr("Task finished"))
        logger.info("任务完成")
        # 发送外部通知
        self.send_notice("completed")
        # 结束后脚本
        run_after_finish = maa_config_data.config.get("run_after_finish")
        if run_after_finish != "" and self.need_runing:
            logger.info(f"运行后脚本")
            self.run_after_finish_process = self.start_process(run_after_finish)
        # 完成后运行
        target = self.Finish_combox.currentIndex()
        actions = {
            0: logger.info("Do nothing"),
            1: self.close_application,
            2: QApplication.quit,
            3: self.shutdown,
            4: self.run_other_config,
        }

        action = actions.get(target)
        logger.info(f"选择的动作: {target}")
        if action and self.need_runing:
            action()
        # 更改按钮状态
        self.S2_Button.setEnabled(True)
        self.S2_Button.setText(self.tr("Start"))
        self.S2_Button.clicked.disconnect()
        self.S2_Button.clicked.connect(self.Start_Up)
        self.start_again = True

    @asyncSlot()
    async def Stop_task(self):
        self.S2_Button.setEnabled(False)
        self.S2_Button.setText(self.tr("Start"))
        self.TaskOutput_Text.append(self.tr("Stopping task..."))
        logger.info("停止任务")
        # 停止MAA
        self.need_runing = False
        self.start_again = True
        await maafw.stop_task()
        maafw.resource.clear()

        self.S2_Button.clicked.disconnect()
        self.S2_Button.clicked.connect(self.Start_Up)
        self.S2_Button.setEnabled(True)

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

    def Add_Task(self):
        if maa_config_data.config == {}:
            return
        # 如果选中了任务的某项,则修改该项任务
        if self.Task_List.currentRow() != -1:
            Select_index = self.Task_List.currentRow()
            Select_Target = self.SelectTask_Combox_1.currentText()
            Option = self.extract_task_options(
                Select_Target, maa_config_data.interface_config
            )
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
            Option = self.extract_task_options(
                Select_Target, maa_config_data.interface_config
            )
            maa_config_data.config["task"].append(
                {"name": Select_Target, "option": Option}
            )

        Save_Config(maa_config_data.config_path, maa_config_data.config)

        self.update_task_list()
        self.AddTask_Button.setText(self.tr("Add Task"))
        self.Task_List.setCurrentRow(-1)

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

    def extract_task_options(self, Select_Target, interface_Config):
        options_dicts = []
        for task in interface_Config["task"]:
            if task.get("name") == Select_Target and task.get("option"):
                for index, option_name in enumerate(task["option"]):
                    select_box_name = f"SelectTask_Combox_{index + 2}"
                    selected_value = getattr(self, select_box_name).currentText()
                    options_dicts.append({"name": option_name, "value": selected_value})
        return options_dicts

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

    def Delete_all_task(self):
        self.Task_List.clear()
        maa_config_data.config["task"] = []
        Save_Config(maa_config_data.config_path, maa_config_data.config)
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
        self.AddTask_Button.setText(self.tr("Rewrite"))
        Select_Target = self.Task_List.currentRow()
        if Select_Target == -1:
            return
        # 将task_combox的内容设置为选中项目
        self.SelectTask_Combox_1.setCurrentText(
            maa_config_data.config["task"][Select_Target]["name"]
        )
        # 填充任务选项
        option_data = maa_config_data.config["task"][Select_Target]["option"]
        option_length = len(option_data)
        for i in range(option_length):
            select_box = getattr(self, f"SelectTask_Combox_{i + 2}")
            label = getattr(self, f"TaskName_Title_{i + 2}")
            select_box.setCurrentText(option_data[i]["value"])
            label.setText(option_data[i]["name"])

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
            self.TaskOutput_Text.append(self.tr("save ADB config..."))
            self.add_Controller_combox()

        elif controller_type == "Win32":
            self.TaskOutput_Text.append(self.tr("save Win32 config..."))
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
        self.clear_extra_widgets()
        select_target = self.SelectTask_Combox_1.currentText()

        self.show_task_options(select_target, maa_config_data.interface_config)

    def show_task_options(self, select_target, MAA_Pi_Config):
        for task in MAA_Pi_Config["task"]:
            if task["name"] == select_target and task.get("option"):
                option_length = len(task["option"])
                for i in range(option_length):
                    select_box = getattr(self, f"SelectTask_Combox_{i + 2}")
                    label = getattr(self, f"TaskName_Title_{i + 2}")
                    option_name = task["option"][i]

                    select_box.addItems(
                        list(
                            Get_Task_List(
                                maa_config_data.interface_config_path, option_name
                            )
                        )
                    )
                    select_box.show()

                    label.setText(option_name)
                    label.show()
                break  # 找到匹配的任务后退出循环

    def clear_extra_widgets(self):
        for i in range(2, 5):
            select_box = getattr(self, f"SelectTask_Combox_{i}")
            select_box.clear()
            select_box.hide()

            label = getattr(self, f"TaskName_Title_{i}")
            label.setText(self.tr("Task"))
            label.hide()

    def change_output(self, msg):
        self.TaskOutput_Text.append(msg)

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
