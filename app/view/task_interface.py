import os
import json
import subprocess
import platform


from PyQt6.QtCore import Qt, QByteArray, QTimer
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

        self.MAA_Service_Process = self.start_MAA_service()
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
        print(f"收到信号：{data}")
        self.handle_signal(data)

    def handle_signal(self, data):
        if data == "MAA_started":
            print("开始按钮解锁")
            self.MAA_started = True
            self.S2_Button.setEnabled(True)
        elif data == "MAA_runing":
            print("停止按钮解锁")
            self.S2_Button.setEnabled(True)
        elif data == "MAA_completed":
            self.TaskOutput_Text.append("任务完成")
            self.Completion_Options()
            self.S2_Button.setText("开始")
        elif "连接失败" in data:
            self.TaskOutput_Text.append(data)
            self.Stop_task()
            self.show_error("连接失败，请检查ADB配置")
        elif "THIS_IS_ADB_DEVICES:" in data:
            self.process_adb_devices(data)
        else:
            self.TaskOutput_Text.append(data)

    def show_error(self, message):
        InfoBar.error(
            title="错误",
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
        print("锁定开始按钮")

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
        self.S2_Button.clicked.connect(self.Start_Up)
        self.Autodetect_combox.currentTextChanged.connect(self.Save_ADB_Config)

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
        print("配置文件存在")
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
            print("配置文件不存在")
            self.create_default_config(maa_pi_config_Path)
            self.load_interface_options(interface_Path)
            self.run_afert_MAA_started()
        else:
            self.show_error("未检测到资源文件")

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
        self.timer = QTimer(self)
        self.timer.setInterval(100)
        self.timer.timeout.connect(self.check_MAA_started)
        self.timer.start()

    def check_MAA_started(self):
        if self.MAA_started:
            self.timer.stop()
            print("MAA启动完成")
            self.Start_ADB_Detection()
        else:
            print("等待MAA启动")

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

    def Completion_Options(self):
        target = self.Finish_combox.currentIndex()
        actions = {
            1: self.closeEmulator,
            2: QApplication.quit,
            3: lambda: (self.closeEmulator(), self.close()),
            4: self.shutdown,
        }
        action = actions.get(target)
        if action:
            action()

    def closeEmulator(self):
        pass

    def shutdown(self):
        shutdown_commands = {
            "Windows": "shutdown /s /t 1",
            "Linux": "shutdown now",
            "Darwin": "sudo shutdown -h now",  # macOS
        }
        os.system(shutdown_commands.get(platform.system(), ""))

    def start_MAA_service(self):
        print("启动MAA服务进程")
        return subprocess.Popen(["python", os.path.join(os.getcwd(), "MAA_Service.py")])

    def Start_Up(self):
        self.S2_Button.setEnabled(False)
        self.S2_Button.setText("停止")
        self.TaskOutput_Text.clear()
        self.socket = QLocalSocket()
        self.socket.connectToServer("GUI2MAA")

        parameter = {
            "action_code": 1,  # 0,获取ADB设备 1:启动任务
            "resource_dir": os.getcwd(),
            "cfg_dir": cfg.get(cfg.Maa_config).replace(
                os.path.join("config", "maa_pi_config.json"), ""
            ),
            "directly": True,
        }
        msg = json.dumps(parameter)
        print(f"发送信号：{msg}")
        self.sendData(msg)

        self.S2_Button.clicked.disconnect()
        self.S2_Button.clicked.connect(self.Stop_task)

    def Stop_task(self):
        self.S2_Button.setEnabled(False)
        self.S2_Button.setText("开始")
        self.TaskOutput_Text.append("正在停止任务...")
        self.socket.disconnectFromServer()
        self.socket.waitForDisconnected()

        self.MAA_Service_Process.terminate()
        try:
            self.MAA_Service_Process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.MAA_Service_Process.kill()

        self.S2_Button.clicked.disconnect()
        self.S2_Button.clicked.connect(self.Start_Up)
        self.MAA_Service_Process = self.start_MAA_service()

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
            self.show_error("没有任务可以被删除")
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
            self.show_error("已经是首位任务")
            return
        elif direction == 1 and Select_Target >= len(MAA_Pi_Config["task"]) - 1:
            self.show_error("已经是末位任务")
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
            label.setText("任务")
            label.hide()

    def change_output(self, msg):
        self.TaskOutput_Text.append(msg)

    def Start_ADB_Detection(self):
        self.socket = QLocalSocket()
        self.socket.connectToServer("GUI2MAA")
        parameter = {"action_code": 0}  # 0,获取ADB设备 1:启动任务
        msg = json.dumps(parameter)
        print(f"发送信号：{msg}")
        self.sendData(msg)

        self.AutoDetect_Button.setEnabled(False)
        self.S2_Button.setEnabled(False)

        InfoBar.info(
            title="提示",
            content="正在检测模拟器",
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.BOTTOM_RIGHT,
            duration=2000,  # won't disappear automatically
            parent=self,
        )

    def On_ADB_Detected(self, emu):
        global emu_data
        emu_data = emu

        self.AutoDetect_Button.setEnabled(True)
        self.S2_Button.setEnabled(True)

        if not emu:
            self.show_error("未检测到模拟器")
        else:
            processed_list = [i["name"] for i in emu]
            self.show_success(f"检测到{processed_list[0]}")
            self.Autodetect_combox.clear()
            self.Autodetect_combox.addItems(processed_list)

    def show_success(self, message):
        InfoBar.success(
            title="成功",
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
