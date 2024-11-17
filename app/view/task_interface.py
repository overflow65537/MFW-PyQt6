import os
import json
import subprocess
import platform

from PyQt6.QtCore import Qt, QByteArray, QTimer, pyqtSlot
from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtNetwork import QLocalServer, QLocalSocket
from qfluentwidgets import InfoBar, InfoBarPosition

from ..view.UI_task_interface import Ui_Task_Interface
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
    check_adb_path,
    get_controller_type,
)
from ..common.config import cfg


class TaskInterface(Ui_Task_Interface, QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setupUi(self)

        # 初始化本地服务和MAA服务进程
        self.server = QLocalServer(self)
        self.server.newConnection.connect(self.connection)
        self.server.listen("MAA2GUI")

        self.MAA_Service_Process = self.start_process(
            ["python", os.path.join(os.getcwd(), "MAA_Service.py")]
        )
        signalBus.update_task_list.connect(self.refresh_widget)
        self.MAA_started = False

        # 初始化组件
        print("TaskInterface init")
        self.Start_Status(
            interface_Path=cfg.get(cfg.Maa_interface),
            maa_pi_config_Path=cfg.get(cfg.Maa_config),
            resource_Path=cfg.get(cfg.Maa_resource),
        )
        self.init_widget()

    def connection(self):
        socket = self.server.nextPendingConnection()
        socket.readyRead.connect(lambda: self.signal_routing(socket))

    def signal_routing(self, socket):
        data = (socket.readAll()).data().decode("utf-8")
        print(f"Received signal: {data}")
        self.handle_signal(data)

    def handle_signal(self, data):
        if data == "MAA_started":
            print("Start button unlocked")
            self.MAA_started = True
            self.S2_Button.setEnabled(True)
        elif data == "MAA_runing":
            print("Stop button unlocked")
            self.S2_Button.setEnabled(True)
        elif "连接失败" in data:
            self.TaskOutput_Text.append("Task completed")
            self.Stop_task()
            self.S2_Button.setText(self.tr("Start"))
        elif data == "MAA_completed":
            self.TaskOutput_Text.append("Task completed")
            self.Stop_task()
            self.Completion_Options()
            self.S2_Button.setText(self.tr("Start"))
        elif "Connection failed" in data:
            self.TaskOutput_Text.append(data)
            self.Stop_task()
            self.show_error(
                self.tr("Connection failed, please check ADB configuration")
            )
        elif "THIS_IS_ADB_DEVICES:" in data:
            self.process_adb_devices(data)
        else:
            self.TaskOutput_Text.append(data)

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

    def process_adb_devices(self, data):
        data_string = (
            data.replace("THIS_IS_ADB_DEVICES:", "")
            .replace("WindowsPath(", "")
            .replace(")", "")
            .replace("'", '"')
            .replace("True", "true")
        )
        data_list = json.loads(data_string)
        signalBus.adb_detected.emit(data_list)

    def sendData(self, msg):
        data = QByteArray(bytes(msg, "utf-8"))
        self.socket.write(data)

    def init_widget(self):
        self.S2_Button.setEnabled(False)
        print("Locking start button")

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
        signalBus.adb_detected.connect(self.On_ADB_Detected)
        self.AddTask_Button.clicked.connect(self.Add_Task)
        self.Delete_Button.clicked.connect(self.Delete_Task)
        self.MoveUp_Button.clicked.connect(self.Move_Up)
        self.MoveDown_Button.clicked.connect(self.Move_Down)
        self.SelectTask_Combox_1.activated.connect(self.Add_Select_Task_More_Select)
        self.Resource_Combox.currentTextChanged.connect(self.Save_Resource)
        self.Control_Combox.currentTextChanged.connect(self.Save_Controller)
        self.AutoDetect_Button.clicked.connect(self.Start_ADB_Detection)
        self.S2_Button.clicked.connect(self.start_custom_process)
        self.Autodetect_combox.currentTextChanged.connect(self.Save_ADB_Config)
        self.Finish_combox.currentIndexChanged.connect(self.rewrite_Completion_Options)

    def Start_Status(self, interface_Path, maa_pi_config_Path, resource_Path):
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
        print("Configuration file exists")
        self.Task_List.addItems(Get_Values_list_Option(maa_pi_config_Path, "task"))
        self.Resource_Combox.addItems(Get_Values_list(interface_Path, key1="resource"))
        self.Control_Combox.addItems(Get_Values_list(interface_Path, key1="controller"))
        self.SelectTask_Combox_1.addItems(Get_Values_list(interface_Path, key1="task"))
        return_init = gui_init(resource_Path, maa_pi_config_Path, interface_Path)
        self.Resource_Combox.setCurrentIndex(return_init["init_Resource_Type"])
        self.Control_Combox.setCurrentIndex(return_init["init_Controller_Type"])
        adb_data = Read_Config(maa_pi_config_Path)["adb"]
        if check_adb_path(adb_data):
            print(adb_data)
            self.run_afert_MAA_started()
        else:
            self.Autodetect_combox.addItem(
                f'{check_path_for_keyword(adb_data["adb_path"])} ({adb_data["address"]})'
            )

    def handle_missing_files(self, resource_Path, interface_Path, maa_pi_config_Path):
        if os.path.exists(resource_Path) and os.path.exists(interface_Path):
            print("Configuration file is missing")
            self.create_default_config(maa_pi_config_Path)
            self.load_interface_options(interface_Path)
            self.run_afert_MAA_started()
        else:
            self.show_error(self.tr("Resource file not detected"))

    def create_default_config(self, maa_pi_config_Path):
        data = {
            "adb": {"adb_path": "", "address": "127.0.0.1:0", "config": {}},
            "controller": {"name": ""},
            "gpu": -1,
            "resource": "",
            "task": [],
            "win32": {"_placeholder": 0},
        }
        Save_Config(maa_pi_config_Path, data)

    def load_interface_options(self, interface_Path):
        self.Resource_Combox.addItems(Get_Values_list(interface_Path, key1="resource"))
        self.Control_Combox.addItems(Get_Values_list(interface_Path, key1="controller"))
        self.SelectTask_Combox_1.addItems(Get_Values_list(interface_Path, key1="task"))
        self.Save_Resource()
        self.Save_Controller()

    def run_afert_MAA_started(self):
        if self.MAA_started:
            self.Start_ADB_Detection()
        else:
            self.MAA_timer()

    def MAA_timer(self):
        self.detect_timer = QTimer(self)
        self.detect_timer.setInterval(100)
        self.detect_timer.timeout.connect(self.check_MAA_started)
        self.detect_timer.start()

    def check_MAA_started(self):
        if self.MAA_started:
            self.detect_timer.stop()
            print("MAA startup completed")
            self.Start_ADB_Detection()
        else:
            print("Waiting for MAA to start")

    def refresh_widget(self, task_list=[]):
        items = self.get_task_list_widget()
        if items != task_list:
            self.Task_List.clear()
            self.Start_Status(
                interface_Path=cfg.get(cfg.Maa_interface),
                maa_pi_config_Path=cfg.get(cfg.Maa_config),
                resource_Path=cfg.get(cfg.Maa_resource),
            )
            items = self.get_task_list_widget()
            signalBus.update_task_list.emit(items)

    def get_task_list_widget(self):
        return [self.Task_List.item(i).text() for i in range(self.Task_List.count())]

    def rewrite_Completion_Options(self):
        cfg.set(cfg.Finish_combox, self.Finish_combox.currentIndex())

    def Completion_Options(self):
        target = self.Finish_combox.currentIndex()
        actions = {
            -1: self.tr("Do nothing"),
            0: self.tr("Do nothing"),
            1: self.closeEmulator,
            2: QApplication.quit,
            3: self.shutdown,
        }

        action = actions.get(target)
        print(f"选择的动作: {actions[target]}")
        if action:
            action()

    def closeEmulator(self):
        self.exe_process.terminate()
        try:
            self.exe_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.exe_process.kill()

    def shutdown(self):
        shutdown_commands = {
            "Windows": "shutdown /s /t 1",
            "Linux": "shutdown now",
            "Darwin": "sudo shutdown -h now",  # macOS
        }
        os.system(shutdown_commands.get(platform.system(), ""))

    def start_process(self, command):
        print(f"Starting process: {command}")
        return subprocess.Popen(command)

    def Start_Up(self):
        self.S2_Button.setEnabled(False)
        self.S2_Button.setText(self.tr("Stop"))
        self.TaskOutput_Text.clear()
        self.socket = QLocalSocket()
        self.socket.connectToServer("GUI2MAA")

        parameter = {
            "action_code": 1,  # 0,获取设备列表，1，启动任务
            "resource_dir": os.getcwd(),
            "cfg_dir": cfg.get(cfg.Maa_config).replace(
                os.path.join("config", "maa_pi_config.json"), ""
            ),
            "directly": True,
        }
        msg = json.dumps(parameter)
        print(f"Sending signal: {msg}")
        self.sendData(msg)

        self.S2_Button.clicked.disconnect()
        self.S2_Button.clicked.connect(self.Stop_task)

    def Start_Up(self):
        self.S2_Button.setEnabled(False)
        self.TaskOutput_Text.clear()
        self.socket = QLocalSocket()
        self.socket.connectToServer("GUI2MAA")

        parameter = {
            "action_code": 1,  # 0: 获取设备列表, 1: 启动任务
            "resource_dir": os.getcwd(),
            "cfg_dir": cfg.get(cfg.Maa_config).replace(
                os.path.join("config", "maa_pi_config.json"), ""
            ),
            "directly": True,
        }
        msg = json.dumps(parameter)
        print(f"Sending signal: {msg}")
        self.sendData(msg)

        self.S2_Button.clicked.disconnect()
        self.S2_Button.clicked.connect(self.Stop_task)

    def start_custom_process(self):
        controller_type = get_controller_type(
            self.Control_Combox.currentText(), cfg.get(cfg.Maa_interface)
        )

        command = []
        wait_time = 0

        if controller_type == "Win32":
            exe_path = cfg.get(cfg.exe_path)
            exe_parameter = cfg.get(cfg.exe_parameter)
            wait_time = int(cfg.get(cfg.exe_wait_time))

            if exe_path:
                command.append(exe_path)
                if exe_parameter:
                    command.extend(exe_parameter.split())
                print(f"启动Win32程序: {command}")

        elif controller_type == "Adb":
            emu_path = cfg.get(cfg.emu_path)
            wait_time = int(cfg.get(cfg.emu_wait_time))

            if emu_path:
                command.append(emu_path)
                print(f"启动模拟器: {command}")

        run_before_start = cfg.get(cfg.run_before_start)
        if run_before_start:
            try:
                self.run_before_start_process = self.start_process(run_before_start)
            except FileNotFoundError as e:
                self.show_error(self.tr(f"File not found"))
                print(e)
            except OSError as e:
                self.show_error(self.tr(f"Can not start the file"))
                print(e)

        if command:
            try:
                self.exe_process = self.start_process(command)
            except FileNotFoundError as e:
                self.show_error(self.tr(f"File not found"))
                print(e)
            except OSError as e:
                self.show_error(self.tr(f"Can not start the file"))
                print(e)
            self.countdown(wait_time)
            self.S2_Button.setText(self.tr("Stop"))
            self.S2_Button.clicked.disconnect()
            self.S2_Button.clicked.connect(self.stop_countdown)
        else:
            self.Start_Up()

    def stop_countdown(self):
        self.countdown_timer.stop()
        self.S2_Button.setEnabled(True)
        self.S2_Button.setText(self.tr("Start"))
        self.TaskOutput_Text.append(self.tr("Stopping task..."))
        self.S2_Button.clicked.disconnect()
        self.S2_Button.clicked.connect(self.start_custom_process)

    def countdown(self, time):
        self.countdown_timer = QTimer(self)
        self.countdown_timer.setInterval(1000)  # 设置为1秒
        self.remaining_time = int(time) * 1000
        self.countdown_timer.timeout.connect(self.update_countdown)
        self.countdown_timer.start()

    @pyqtSlot()
    def update_countdown(self):
        if self.remaining_time > 0:
            self.TaskOutput_Text.append(
                self.tr("starting in ")
                + f"{self.remaining_time // 1000}"
                + self.tr(" seconds")
            )
            self.remaining_time -= 1000
            print(self.remaining_time)
        else:
            self.countdown_timer.stop()  # 时间归零后停止计时器
            print(self.remaining_time)
            self.Start_Up()  # 倒计时结束后启动

    def Stop_task(self):
        self.S2_Button.setEnabled(False)
        self.S2_Button.setText(self.tr("Start"))
        self.TaskOutput_Text.append(self.tr("Stopping task..."))
        self.socket.disconnectFromServer()
        self.socket.waitForDisconnected()

        self.MAA_Service_Process.terminate()
        try:
            self.MAA_Service_Process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.MAA_Service_Process.kill()

        self.S2_Button.clicked.disconnect()
        self.S2_Button.clicked.connect(self.start_custom_process)
        self.MAA_Service_Process = self.start_process(
            ["python", os.path.join(os.getcwd(), "MAA_Service.py")]
        )

    def run_after_finish(self):
        run_after_finish = cfg.get(cfg.run_after_finish)
        if run_after_finish != "":
            try:
                self.run_after_finish = self.start_process(run_after_finish)
            except FileNotFoundError as e:
                self.show_error(self.tr(f"File not found"))
                print(e)
            except OSError as e:
                self.show_error(self.tr(f"Can not start the file"))
                print(e)

    def task_list_changed(self):
        self.Task_List.clear()
        self.Task_List.addItems(Get_Values_list_Option(cfg.get(cfg.Maa_config), "task"))

    def Add_Task(self):
        Select_Target = self.SelectTask_Combox_1.currentText()
        MAA_Pi_Config = Read_Config(cfg.get(cfg.Maa_interface))
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
        self.Task_List.clear()
        self.Task_List.addItems(Get_Values_list_Option(cfg.get(cfg.Maa_config), "task"))
        items = self.get_task_list_widget()
        signalBus.update_task_list.emit(items)

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

    def Save_Controller(self):
        Controller_Type_Select = self.Control_Combox.currentText()
        MAA_Pi_Config = Read_Config(cfg.get(cfg.Maa_config))
        MAA_Pi_Config["controller"]["name"] = Controller_Type_Select
        Save_Config(cfg.get(cfg.Maa_config), MAA_Pi_Config)

    def update_config_value(self, key, value):
        MAA_Pi_Config = Read_Config(cfg.get(cfg.Maa_config))
        MAA_Pi_Config[key] = value
        Save_Config(cfg.get(cfg.Maa_config), MAA_Pi_Config)

    def Add_Select_Task_More_Select(self):
        self.clear_extra_widgets()
        select_target = self.SelectTask_Combox_1.currentText()
        MAA_Pi_Config = Read_Config(cfg.get(cfg.Maa_interface))
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

    def Start_ADB_Detection(self):
        self.socket = QLocalSocket()
        self.socket.connectToServer("GUI2MAA")
        parameter = {"action_code": 0}  # 0, 获取ADB设备 1: 启动任务
        msg = json.dumps(parameter)
        print(f"Sending signal: {msg}")
        self.sendData(msg)

        self.AutoDetect_Button.setEnabled(False)
        self.S2_Button.setEnabled(False)

        InfoBar.info(
            title=self.tr("Tip"),
            content=self.tr("Detecting emulator..."),
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.BOTTOM_RIGHT,
            duration=2000,
            parent=self,
        )

    def On_ADB_Detected(self, emu):
        global emu_data
        emu_data = emu

        self.AutoDetect_Button.setEnabled(True)
        self.S2_Button.setEnabled(True)

        if not emu:
            self.show_error(self.tr("No emulator detected"))
        else:
            processed_list = [i["name"] for i in emu]
            self.show_success(f"Detected {processed_list[0]}")
            self.Autodetect_combox.clear()
            self.Autodetect_combox.addItems(processed_list)

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

    def Save_ADB_Config(self):
        target = self.Autodetect_combox.currentText()
        for i in emu_data:
            if i["name"] == target:
                result = i
                break

        data = Read_Config(cfg.get(cfg.Maa_config))
        data["adb"]["adb_path"] = result["adb_path"]
        data["adb"]["address"] = result["address"]
        data["adb"]["config"] = result["config"]
        Save_Config(cfg.get(cfg.Maa_config), data)

        signalBus.update_adb.emit(result)
