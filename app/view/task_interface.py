import os
import subprocess
import platform
from qasync import asyncSlot
import asyncio
from pathlib import Path

from PyQt6.QtCore import Qt
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

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setupUi(self)
        signalBus.resource_exist.connect(self.resource_exist)
        maafw.notification_handler = MyNotificationHandler()
        if cfg.get(cfg.resource_exist):
            self.init_ui()
            self.bind_signals()
        else:
            logger.warning("task_interface.py:资源缺失")
            self.show_error(self.tr("Resource file not detected"))

        self.toggle_task_options(False)

    def resource_exist(self, status: bool):
        if status:
            logger.info("task_interface.py:收到信号,初始化界面和信号连接")
            self.clear_content()
            self.init_ui()
            self.disconnect_signals()
            self.bind_signals()
        else:
            logger.info("task_interface.py:资源缺失,清空界面")
            self.uninit_ui()

    def init_ui(self):
        # 读取配置文件并存储在实例变量中
        # 初始化组件
        self.Start_Status(
            interface_Path=maa_config_data.interface_config_path,
            maa_pi_config_Path=maa_config_data.config_path,
            resource_Path=maa_config_data.resource_path,
        )
        self.init_finish_combox()

    def uninit_ui(self):
        self.disconnect_signals()
        self.clear_content()

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
        self.Topic_Text.clear()
        self.Autodetect_combox.clear()

    def disconnect_signals(self):
        try:
            signalBus.Notice_msg.disconnect(self.print_notice)
            signalBus.callback.disconnect(self.callback)
            signalBus.update_task_list.disconnect(self.update_task_list_passive)
            self.AddTask_Button.clicked.disconnect(self.Add_Task)
            self.Delete_Button.clicked.disconnect(self.Delete_Task)
            self.MoveUp_Button.clicked.disconnect(self.Move_Up)
            self.MoveDown_Button.clicked.disconnect(self.Move_Down)
            self.SelectTask_Combox_1.activated.disconnect(
                self.Add_Select_Task_More_Select
            )
            self.Resource_Combox.currentTextChanged.disconnect(self.Save_Resource)
            self.Control_Combox.currentTextChanged.disconnect(self.Save_Controller)
            self.AutoDetect_Button.clicked.disconnect(self.Start_Detection)
            self.S2_Button.clicked.disconnect(self.Start_Up)
            self.Autodetect_combox.currentTextChanged.disconnect(
                self.Save_device_Config
            )
            self.Finish_combox.currentIndexChanged.disconnect(
                self.rewrite_Completion_Options
            )
        except:
            pass

    def init_finish_combox(self):
        finish_list = [
            self.tr("Do nothing"),
            self.tr("Close emulator"),
            self.tr("Close emulator and Quit app"),
            self.tr("Shutdown"),
        ]
        self.Finish_combox.addItems(finish_list)
        finish_combox = maa_config_data.config["finish_option"]
        self.Finish_combox.setCurrentIndex(finish_combox)

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
            self.Topic_Text,
        ]
        for combox in task_comboxes:
            combox.setVisible(visible)
        for title in task_titles:
            title.setVisible(visible)

    def bind_signals(self):
        signalBus.Notice_msg.connect(self.print_notice)
        signalBus.callback.connect(self.callback)
        signalBus.update_task_list.connect(self.update_task_list_passive)
        self.AddTask_Button.clicked.connect(self.Add_Task)
        self.Delete_Button.clicked.connect(self.Delete_Task)
        self.MoveUp_Button.clicked.connect(self.Move_Up)
        self.MoveDown_Button.clicked.connect(self.Move_Down)
        self.SelectTask_Combox_1.activated.connect(self.Add_Select_Task_More_Select)
        self.Resource_Combox.currentTextChanged.connect(self.Save_Resource)
        self.Control_Combox.currentTextChanged.connect(self.Save_Controller)
        self.AutoDetect_Button.clicked.connect(self.Start_Detection)
        self.S2_Button.clicked.connect(self.Start_Up)
        self.Autodetect_combox.currentTextChanged.connect(self.Save_device_Config)
        self.Finish_combox.currentIndexChanged.connect(self.rewrite_Completion_Options)

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
                logger.debug(f"task_interface.py:{self.entry} 任务失败")
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
        logger.info("task_interface.py:配置文件存在")
        self.Task_List.addItems(Get_Values_list_Option(maa_pi_config_Path, "task"))
        self.Resource_Combox.addItems(Get_Values_list(interface_Path, key1="resource"))
        self.Control_Combox.addItems(Get_Values_list(interface_Path, key1="controller"))
        self.SelectTask_Combox_1.addItems(Get_Values_list(interface_Path, key1="task"))
        return_init = gui_init(resource_Path, maa_pi_config_Path, interface_Path)
        self.Resource_Combox.setCurrentIndex(return_init["init_Resource_Type"])
        self.Control_Combox.setCurrentIndex(return_init["init_Controller_Type"])
        self.add_Controller_combox()

    def handle_missing_files(self, resource_Path, interface_Path, maa_pi_config_Path):
        if os.path.exists(resource_Path) and os.path.exists(interface_Path):
            logger.info("task_interface.py:配置文件缺失")
            self.create_default_config(maa_pi_config_Path)
            self.load_interface_options(interface_Path)
        else:
            logger.warning("task_interface.py:资源缺失")
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
            "save_draw": False,
            "finish_option": 0,
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
        self.Control_Combox.addItems(Get_Values_list(interface_Path, key1="controller"))
        self.SelectTask_Combox_1.addItems(Get_Values_list(interface_Path, key1="task"))
        self.Save_Resource()
        self.Save_Controller()

    def rewrite_Completion_Options(self):
        maa_config_data.config["finish_option"] = (
            self.Finish_combox.currentIndex()
        )  # 更新保存的配置
        Save_Config(maa_config_data.config_path, maa_config_data.config)  # 刷新配置文件

    def close_application(self):
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

    def start_process(self, command):
        logger.debug(f"task_interface.py:启动程序: {command}")
        return subprocess.Popen(command)

    @asyncSlot()
    async def Start_Up(self):
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
            logger.info("task_interface.py:运行前脚本")
            try:
                self.run_before_start_process = self.start_process(run_before_start)
            except FileNotFoundError as e:
                self.show_error(self.tr(f"File not found"))
                logger.error(f'task_interface.py:运行前脚本"{e}"')
                await maafw.stop_task()
                return
            except OSError as e:
                self.show_error(self.tr(f"Can not start the file"))
                logger.error(f'task_interface.py:运行前脚本"{e}"')
                await maafw.stop_task()
                return
        # 加载资源
        resource_path = None
        resource_target = self.Resource_Combox.currentText()

        for i in maa_config_data.interface_config["resource"]:
            if i["name"] == resource_target:
                logger.debug(f"task_interface.py:加载资源: {i['path']}")
                resource_path = i["path"]

        if resource_path is None and self.need_runing:
            logger.error(f"task_interface.py:未找到目标资源: {resource_target}")
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
            logger.debug(f"task_interface.py:加载资源: {resource}")
            await maafw.load_resource(resource)
            logger.debug(f"task_interface.py:资源加载完成: {resource}")
        gpu_index = maa_config_data.config["gpu"]
        if gpu_index == -2 and self.need_runing:
            logger.debug("task_interface.py:设置CPU推理")
            maafw.resource.set_cpu()
        elif gpu_index == -1 and self.need_runing:
            logger.debug("task_interface.py:设置自动")
            maafw.resource.set_auto_device()
        else:
            logger.debug(f"task_interface.py:设置GPU推理: {gpu_index}")
            maafw.resource.set_gpu(gpu_index)
        # 连接控制器
        if controller_type == "Adb" and self.need_runing:  # adb控制
            # 启动模拟器
            emu_path = maa_config_data.config.get("emu_path")
            emu_wait_time = int(maa_config_data.config.get("emu_wait_time"))
            if emu_path != "" and self.need_runing:
                logger.info(f"task_interface.py:启动模拟器")
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
                        maa_config_data.config["adb"]["config"] = i.config
                        break
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
                        f"task_interface.py:连接adb失败\n{maa_config_data.config['adb']['adb_path']}\n{maa_config_data.config['adb']['address']}\n{maa_config_data.config['adb']['input_method']}\n{maa_config_data.config['adb']['screen_method']}\n{maa_config_data.config['adb']['config']}"
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
                        f"task_interface.py:连接adb失败\n{maa_config_data.config['adb']['adb_path']}\n{maa_config_data.config['adb']['address']}\n{maa_config_data.config['adb']['input_method']}\n{maa_config_data.config['adb']['screen_method']}\n{maa_config_data.config['adb']['config']}"
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
                logger.info(f"task_interface.py:启动游戏")
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
                    f"task_interface.py:连接Win32失败 \n{maa_config_data.config['win32']['hwnd']}\n{maa_config_data.config['win32']['input_method']}\n{maa_config_data.config['win32']['screen_method']}"
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
        for task_list in maa_config_data.config["task"]:
            if not self.need_runing:
                await maafw.stop_task()
                return
            for task_enter in maa_config_data.interface_config["task"]:
                if task_enter["name"] == task_list["name"]:
                    self.entry = task_enter["entry"]
            if task_list["option"] == []:
                logger.info(f"task_interface.py:运行任务:{self.entry}")
                self.TaskOutput_Text.append(self.tr("task running:") + f" {self.entry}")
                await maafw.run_task(self.entry)
            else:
                override_options = {}
                for task_option in task_list["option"]:
                    # 遍历 MAA_Pi_Config 中 task 的 option
                    for override in maa_config_data.interface_config["option"][
                        task_option["name"]
                    ]["cases"]:
                        if override["name"] == task_option["value"]:
                            override_options.update(override["pipeline_override"])
                logger.info(
                    f"task_interface.py:运行任务:{self.entry}\n任务选项: {override_options}"
                )
                self.TaskOutput_Text.append(self.tr("running task:") + f" {self.entry}")
                await maafw.run_task(self.entry, override_options)
        self.TaskOutput_Text.append(self.tr("Task finished"))
        logger.info("task_interface.py:任务完成")
        # 发送外部通知
        self.send_notice("completed")
        # 结束后脚本
        run_after_finish = maa_config_data.config.get("run_after_finish")
        if run_after_finish != "" and self.need_runing:
            logger.info(f"task_interface.py:运行后脚本")
            self.run_after_finish_process = self.start_process(run_after_finish)
        # 完成后运行
        target = self.Finish_combox.currentIndex()
        actions = {
            -1: logger.info("task_interface.py:Do nothing"),
            0: logger.info("task_interface.py:Do nothing"),
            1: self.close_application,
            2: QApplication.quit,
            3: self.shutdown,
        }

        action = actions.get(target)
        logger.info(f"task_interface.py:选择的动作: {target}")
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
        logger.info("task_interface.py:停止任务")
        # 停止MAA
        self.need_runing = False
        self.start_again = True
        await maafw.stop_task()
        maafw.resource.clear()

        self.S2_Button.clicked.disconnect()
        self.S2_Button.clicked.connect(self.Start_Up)
        self.S2_Button.setEnabled(True)

    def task_list_changed(self):
        self.Task_List.clear()
        self.Task_List.addItems(
            Get_Values_list_Option(maa_config_data.config_path, "task")
        )

    def Add_Task(self):
        Select_Target = self.SelectTask_Combox_1.currentText()
        Option = self.extract_task_options(
            Select_Target, maa_config_data.interface_config
        )

        maa_config_data.config["task"].append({"name": Select_Target, "option": Option})
        Save_Config(maa_config_data.config_path, maa_config_data.config)

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

    def Move_Up(self):
        self.move_task(direction=-1)

    def Move_Down(self):
        self.move_task(direction=1)

    def move_task(self, direction: int):
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

    def Save_Resource(self):
        self.update_config_value("resource", self.Resource_Combox.currentText())
        logger.info(
            f"task_interface.py:保存资源配置: {self.Resource_Combox.currentText()}"
        )

    def Save_Controller(self):
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
        logger.info(f"task_interface.py:保存控制器配置: {Controller_Type_Select}")
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
        logger.info("task_interface.py:开始检测")
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
                logger.info("task_interface.py:备用 ADB 检测")
                self.devices = await self.Adb_detect_backup()
            processed_list = [
                f"{device.name} ({device.address.split(':')[-1]})"
                for device in (self.devices or [])
            ]

        # 处理结果
        if not processed_list:
            logger.error("task_interface.py:未检测到设备")
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

                signalBus.update_adb.emit(result)
        elif controller_type == "Win32":
            for i in self.win32_hwnd:
                if i.window_name == target:
                    result = i
                    break
            if result:
                maa_config_data.config["win32"]["hwnd"] = result.hwnd
                Save_Config(maa_config_data.config_path, maa_config_data.config)
