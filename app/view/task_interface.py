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


class TaskInterface(Ui_Task_Interface, QWidget):
    devices = []
    run_mode = "adb"

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setupUi(self)
        maafw.notification_handler = MyNotificationHandler()
        self.maa_interface_path = os.path.join(
            cfg.get(cfg.Maa_resource), "interface.json"
        )
        self.maa_resource_path = os.path.join(cfg.get(cfg.Maa_resource), "resource")
        # 初始化组件
        logger.info("TaskInterface init")
        self.Start_Status(
            interface_Path=self.maa_interface_path,
            maa_pi_config_Path=cfg.get(cfg.Maa_config),
            resource_Path=self.maa_resource_path,
        )
        self.init_widget()

    def show_error(self, message):
        InfoBar.error(
            title=self.tr("Error"),
            content=message,
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.BOTTOM_RIGHT,
            duration=-1,
            parent=self,
        )

    def init_widget(self):
        finish_list = [
            self.tr("Do nothing"),
            self.tr("Close emulator"),
            self.tr("Close emulator and Quit app"),
            self.tr("Shutdown"),
        ]
        self.Finish_combox.addItems(finish_list)
        self.Finish_combox.setCurrentIndex(cfg.get(cfg.Finish_combox))
        self.toggle_task_options(False)

        # 绑定信号
        self.bind_signals()

    def toggle_task_options(self, visible):
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

    def callback(self, message):
        if "controller_action" in message:
            message_data = message.replace("controller_action:", "")
            if message_data == "1":
                self.TaskOutput_Text.append(self.tr("Starting Connection"))
                logger.info("开始连接")
            elif message_data == "2":
                self.TaskOutput_Text.append(self.tr("Connection Success"))
                logger.info("连接成功")
            elif message_data == "3":
                self.TaskOutput_Text.append(self.tr("Connection Failed"))
                logger.info("连接失败")
            elif message_data == "4":
                self.TaskOutput_Text.append(self.tr("Unknow Error"))
                logger.info("未知错误")
        elif "tasker_task" in message:
            message_data = message.replace("tasker_task:", "")
            if message_data == "3":
                self.TaskOutput_Text.append(self.entry + self.tr("Failed"))
                logger.info(f"{self.entry} 任务失败")

    def Start_Status(self, interface_Path, maa_pi_config_Path, resource_Path):
        print(interface_Path, maa_pi_config_Path, resource_Path)
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
        }
        Save_Config(maa_pi_config_Path, data)

    def load_interface_options(self, interface_Path):
        self.Resource_Combox.addItems(Get_Values_list(interface_Path, key1="resource"))
        self.Control_Combox.addItems(Get_Values_list(interface_Path, key1="controller"))
        self.SelectTask_Combox_1.addItems(Get_Values_list(interface_Path, key1="task"))
        self.Save_Resource()
        self.Save_Controller()

    def rewrite_Completion_Options(self):
        cfg.set(cfg.Finish_combox, self.Finish_combox.currentIndex())

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
        logger.info(f"启动程序: {command}")
        return subprocess.Popen(command)

    @asyncSlot()
    async def Start_Up(self):
        self.need_runing = True
        self.S2_Button.setEnabled(False)
        self.S2_Button.setText(self.tr("Stop"))
        self.S2_Button.clicked.connect(self.Stop_task)
        self.TaskOutput_Text.clear()

        PROJECT_DIR = os.getcwd()
        controller_type = get_controller_type(
            self.Control_Combox.currentText(), self.maa_interface_path
        )
        # 启动前脚本
        run_before_start = cfg.get(cfg.run_before_start)
        if run_before_start != "" and self.need_runing:
            logger.info(f"运行前脚本: {run_before_start}")
            try:
                self.run_before_start_process = self.start_process(run_before_start)
            except FileNotFoundError as e:
                self.show_error(self.tr(f"File not found"))
                logger.error(e)
                await maafw.stop_task()
                return
            except OSError as e:
                self.show_error(self.tr(f"Can not start the file"))
                logger.error(e)
                await maafw.stop_task()
                return
        # 加载资源
        resource_path = None
        resource_target = self.Resource_Combox.currentText()
        interface = Read_Config(self.maa_interface_path)
        config = Read_Config(cfg.get(cfg.Maa_config))

        for i in interface["resource"]:
            if i["name"] == resource_target:
                logger.info(f"加载资源: {i['path']}")
                resource_path = i["path"]

        if resource_path is None and self.need_runing:
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
            logger.info(f"加载资源: {resource}")
            await maafw.load_resource(resource)
            logger.info(f"资源加载完成: {resource}")
        gpu_index = config["gpu"]
        if gpu_index == -2 and self.need_runing:
            logger.info("设置CPU推理")
            maafw.resource.set_cpu()
        elif gpu_index == -1 and self.need_runing:
            logger.info("设置自动")
            maafw.resource.set_auto_device()
        else:
            logger.info(f"设置GPU推理: {gpu_index}")
            maafw.resource.set_gpu(gpu_index)
        # 连接控制器
        if controller_type == "Adb" and self.need_runing:  # adb控制
            # 启动模拟器
            emu_path = cfg.get(cfg.emu_path)
            emu_wait_time = int(cfg.get(cfg.emu_wait_time))
            if emu_path != "" and self.need_runing:
                logger.info(f"启动模拟器: {emu_path}")
                self.app_process = self.start_process(emu_path)
                logger.info("模拟器启动成功")
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
            if (
                not await maafw.connect_adb(
                    config["adb"]["adb_path"],
                    config["adb"]["address"],
                    config["adb"]["input_method"],
                    config["adb"]["screen_method"],
                    config["adb"]["config"],
                )
                and self.need_runing
            ):
                logger.error(
                    f"连接adb失败\n{config["adb"]["adb_path"]}\n{config['adb']['address']}\n{config['adb']['input_method']}\n{config['adb']['screen_method']}\n{config['adb']['config']}"
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
            exe_path = cfg.get(cfg.exe_path)
            exe_wait_time = int(cfg.get(cfg.exe_wait_time))
            exe_parameter = cfg.get(cfg.exe_parameter)
            if exe_path != "" and self.need_runing:
                logger.info(f"启动游戏: {exe_path}")
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
                    config["win32"]["hwnd"],
                    config["win32"]["input_method"],
                    config["win32"]["screen_method"],
                )
                and self.need_runing
            ):
                logger.error(
                    f"连接Win32失败 \n{config['win32']['hwnd']}\n{config['win32']['input_method']}\n{config['win32']['screen_method']}"
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
        for task_list in config["task"]:
            if not self.need_runing:
                await maafw.stop_task()
                return
            for task_enter in interface["task"]:
                if task_enter["name"] == task_list["name"]:
                    self.entry = task_enter["entry"]
            if task_list["option"] == []:
                logger.info(f"运行任务:{self.entry}")
                self.TaskOutput_Text.append(self.tr("运行任务:") + f" {self.entry}")
                await maafw.run_task(self.entry)
            else:
                override_options = {}
                for task_option in task_list["option"]:
                    # 遍历pi_config中task的option
                    for override in interface["option"][task_option["name"]]["cases"]:
                        if override["name"] == task_option["value"]:
                            override_options.update(override["pipeline_override"])
                logger.info(f"运行任务:{self.entry}\n任务选项: {override_options}")
                self.TaskOutput_Text.append(self.tr("running task:") + f" {self.entry}")
                await maafw.run_task(self.entry, override_options)
        self.TaskOutput_Text.append(self.tr("Task finished"))
        logger.info("任务完成")

        # 结束后脚本
        run_after_finish = cfg.get(cfg.run_after_finish)
        if run_after_finish != "" and self.need_runing:
            logger.info(f"运行后脚本: {run_after_finish}")
            self.run_after_finish_process = self.start_process(run_after_finish)
        # 完成后运行
        target = self.Finish_combox.currentIndex()
        actions = {
            -1: logger.info("Do nothing"),
            0: logger.info("Do nothing"),
            1: self.close_application,
            2: QApplication.quit,
            3: self.shutdown,
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

    @asyncSlot()
    async def Stop_task(self):
        self.S2_Button.setEnabled(False)
        self.S2_Button.setText(self.tr("Start"))
        self.TaskOutput_Text.append(self.tr("Stopping task..."))
        logger.info("停止任务")
        # 停止MAA
        self.need_runing = False
        await maafw.stop_task()
        maafw.resource.clear()

        self.S2_Button.clicked.disconnect()
        self.S2_Button.clicked.connect(self.Start_Up)
        self.S2_Button.setEnabled(True)

    def task_list_changed(self):
        self.Task_List.clear()
        self.Task_List.addItems(Get_Values_list_Option(cfg.get(cfg.Maa_config), "task"))

    def Add_Task(self):
        Select_Target = self.SelectTask_Combox_1.currentText()
        MAA_Pi_Config = Read_Config(self.maa_interface_path)
        Option = self.extract_task_options(Select_Target, MAA_Pi_Config)

        MAA_Pi_Config = Read_Config(cfg.get(cfg.Maa_config))
        MAA_Pi_Config["task"].append({"name": Select_Target, "option": Option})
        Save_Config(cfg.get(cfg.Maa_config), MAA_Pi_Config)

        self.update_task_list()

    def extract_task_options(self, Select_Target, MAA_Pi_Config):
        options_dicts = []
        for task in MAA_Pi_Config["task"]:
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
        self.Task_List.addItems(Get_Values_list_Option(cfg.get(cfg.Maa_config), "task"))

    def Delete_Task(self):
        Select_Target = self.Task_List.currentRow()
        if Select_Target == -1:
            self.show_error(self.tr("No task can be deleted"))
            return

        self.Task_List.takeItem(Select_Target)
        Task_List = Get_Values_list2(cfg.get(cfg.Maa_config), "task")
        if 0 <= Select_Target < len(Task_List):
            del Task_List[Select_Target]
            MAA_Pi_Config = Read_Config(cfg.get(cfg.Maa_config))
            MAA_Pi_Config["task"] = Task_List
            Save_Config(cfg.get(cfg.Maa_config), MAA_Pi_Config)

            self.update_task_list()
            if Select_Target == 0:
                self.Task_List.setCurrentRow(Select_Target)
            elif Select_Target != -1:
                self.Task_List.setCurrentRow(Select_Target - 1)

    def Move_Up(self):
        self.move_task(direction=-1)

    def Move_Down(self):
        self.move_task(direction=1)

    def move_task(self, direction):
        Select_Target = self.Task_List.currentRow()
        MAA_Pi_Config = Read_Config(cfg.get(cfg.Maa_config))

        if direction == -1 and Select_Target == 0:
            self.show_error(self.tr("Already the first task"))
            return
        elif direction == 1 and Select_Target >= len(MAA_Pi_Config["task"]) - 1:
            self.show_error(self.tr("Already the last task"))
            return

        Select_Task = MAA_Pi_Config["task"].pop(Select_Target)
        MAA_Pi_Config["task"].insert(Select_Target + direction, Select_Task)
        Save_Config(cfg.get(cfg.Maa_config), MAA_Pi_Config)

        self.update_task_list()
        self.Task_List.setCurrentRow(Select_Target + direction)

    def Save_Resource(self):
        self.update_config_value("resource", self.Resource_Combox.currentText())
        logger.info(f"保存资源配置: {self.Resource_Combox.currentText()}")

    @asyncSlot()
    async def Save_Controller(self):
        Controller_Type_Select = self.Control_Combox.currentText()
        controller_type = get_controller_type(
            Controller_Type_Select, self.maa_interface_path
        )
        if controller_type == "Adb":
            self.TaskOutput_Text.append(self.tr("Saving ADB configuration..."))
            self.add_Controller_combox()

        elif controller_type == "Win32":
            await self.Start_Detection()
            self.TaskOutput_Text.append(self.tr("Saving Win32 configuration..."))

        MAA_Pi_Config = Read_Config(cfg.get(cfg.Maa_config))
        MAA_Pi_Config["controller"]["name"] = Controller_Type_Select
        Save_Config(cfg.get(cfg.Maa_config), MAA_Pi_Config)

    def add_Controller_combox(self):
        controller_type = get_controller_type(
            self.Control_Combox.currentText(), self.maa_interface_path
        )
        self.Autodetect_combox.clear()
        if controller_type == "Adb":
            config = Read_Config(cfg.get(cfg.Maa_config))
            emulators_name = check_path_for_keyword(config["adb"]["adb_path"])
            self.Autodetect_combox.clear()
            self.Autodetect_combox.addItem(
                f"{emulators_name} ({config['adb']['address'].split(':')[-1]})"
            )

    def update_config_value(self, key, value):
        MAA_Pi_Config = Read_Config(cfg.get(cfg.Maa_config))
        MAA_Pi_Config[key] = value
        Save_Config(cfg.get(cfg.Maa_config), MAA_Pi_Config)

    def Add_Select_Task_More_Select(self):
        self.clear_extra_widgets()
        select_target = self.SelectTask_Combox_1.currentText()
        MAA_Pi_Config = Read_Config(self.maa_interface_path)
        self.show_task_options(select_target, MAA_Pi_Config)

    def show_task_options(self, select_target, MAA_Pi_Config):
        for task in MAA_Pi_Config["task"]:
            if task["name"] == select_target and task.get("option"):
                option_length = len(task["option"])
                for i in range(option_length):
                    select_box = getattr(self, f"SelectTask_Combox_{i + 2}")
                    label = getattr(self, f"TaskName_Title_{i + 2}")
                    option_name = task["option"][i]

                    select_box.addItems(list(Get_Task_List(option_name)))
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
        self.AutoDetect_Button.setEnabled(False)
        self.S2_Button.setEnabled(False)

        controller_type = get_controller_type(
            self.Control_Combox.currentText(), self.maa_interface_path
        )

        if controller_type == "Win32":
            content = self.tr("Detecting game...")
            detect_function = maafw.detect_win32hwnd
            error_message = self.tr("No game detected")
            success_message = self.tr("Game detected")
        elif controller_type == "Adb":
            content = self.tr("Detecting emulator...")
            detect_function = maafw.detect_adb
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
            interface_config = Read_Config(self.maa_interface_path)
            for i in interface_config["controller"]:
                if i["type"] == "Win32":
                    self.win32_hwnd = await detect_function(i["win32"]["window_regex"])
            processed_list = (
                [hwnd.window_name for hwnd in self.win32_hwnd]
                if self.win32_hwnd
                else []
            )
        elif controller_type == "Adb":
            self.devices = await detect_function()
            if not self.devices:
                logger.info("备用ADB检测")
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
                # 判断程序是否正在运行,是进行下一步,否则放弃
                may_path = [os.path.join(*i) for i in app["may_path"]]
                info_dict = {"exe_path": process_path, "may_path": may_path}
                ADB_path = find_existing_file(info_dict)

                if ADB_path:
                    # 判断ADB地址是否存在,是进行下一步,否则放弃
                    port_data = await check_port(
                        app["port"]
                    )  # 使用 await 调用 check_port

                    if port_data:
                        # 判断端口是否存在,是则组合字典,否则放弃
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

    def Save_device_Config(self):
        controller_type = get_controller_type(
            self.Control_Combox.currentText(), self.maa_interface_path
        )
        target = self.Autodetect_combox.currentText()
        if controller_type == "Adb":
            for i in self.devices:
                logger.info(i)
                if f"{i.name} ({i.address.split(':')[-1]})" == target:
                    result = i
                    break
            data = Read_Config(cfg.get(cfg.Maa_config))
            data["adb"]["adb_path"] = str(result.adb_path)
            data["adb"]["address"] = result.address
            data["adb"]["config"] = result.config
            Save_Config(cfg.get(cfg.Maa_config), data)
            signalBus.update_adb.emit(result)
        elif controller_type == "Win32":
            for i in self.win32_hwnd:
                if i.window_name == target:
                    result = i
                    break
            data = Read_Config(cfg.get(cfg.Maa_config))
            data["win32"]["hwnd"] = result.hwnd
            Save_Config(cfg.get(cfg.Maa_config), data)
