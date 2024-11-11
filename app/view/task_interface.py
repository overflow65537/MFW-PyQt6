import os
import json
import subprocess
import platform

from PyQt6.QtCore import Qt, QByteArray
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

        # 连接本地服务
        self.server = QLocalServer(self)
        self.server.newConnection.connect(self.connection)
        self.server.listen("MAA2GUI")

        self.MAA_Service_Process = subprocess.Popen(
            ["python", os.path.join(os.getcwd(), "MAA_Service.py")]
        )
        signalBus.update_task_list.connect(self.refresh_widget)
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
        if data == "MAA_started":
            print("开始按钮解锁")
            self.S2_Button.setEnabled(True)
        elif data == "MAA_runing":
            self.S2_Button.setEnabled(True)
        elif data == "MAA_completed":
            self.TaskOutput_Text.append("任务完成")
            self.Completion_Options()
            self.S2_Button.setText("开始")
        elif "连接失败" in data:
            self.Task_List
            self.TaskOutput_Text.append(data)
            self.Stop_task()
            InfoBar.error(
                title="错误",
                content="连接失败，请检查ADB配置",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.BOTTOM_RIGHT,
                duration=-1,
                parent=self,
            )
        elif "THIS_IS_ADB_DEVICES:" in data:
            data_string = (
                data.replace("THIS_IS_ADB_DEVICES:", "")
                .replace("WindowsPath(", "")
                .replace(")", "")
                .replace("'", '"')
                .replace("True", "true")
            )

            # 将字符串解析为 Python 对象
            data_list = json.loads(data_string)

            # 输出还原后的列表
            signalBus.adb_detected.emit(data_list)

        else:
            self.TaskOutput_Text.append(data)

    def sendData(self, msg):
        data = QByteArray(bytes(msg, "utf-8"))  # 要发送的数据
        self.socket.write(data)  # 发送数据

    def init_widget(self):
        # 在MAA_Service.exe启动前 禁用按钮
        self.S2_Button.setEnabled(False)
        print("锁定开始按钮")

        self.Finish_combox.setCurrentIndex(cfg.get(cfg.Finish_combox))

        # 隐藏任务选项
        self.SelectTask_Combox_2.hide()
        self.SelectTask_Combox_3.hide()
        self.SelectTask_Combox_4.hide()

        # 隐藏任务标签
        self.TaskName_Title_2.hide()
        self.TaskName_Title_3.hide()
        self.TaskName_Title_4.hide()
        self.Topic_Text.hide()

        # 绑定信号
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
        # 资源文件和配置文件全部存在
        if (
            os.path.exists(resource_Path)
            and os.path.exists(interface_Path)
            and os.path.exists(maa_pi_config_Path)
        ):
            print("配置文件存在")
            # 填充数据至组件并设置初始值
            self.Task_List.addItems(Get_Values_list_Option(maa_pi_config_Path, "task"))
            self.Resource_Combox.addItems(
                Get_Values_list(interface_Path, key1="resource")
            )
            self.Control_Combox.addItems(
                Get_Values_list(interface_Path, key1="controller")
            )
            self.SelectTask_Combox_1.addItems(
                Get_Values_list(interface_Path, key1="task")
            )
            return_init = gui_init(resource_Path, maa_pi_config_Path, interface_Path)
            self.Resource_Combox.setCurrentIndex(return_init["init_Resource_Type"])
            self.Control_Combox.setCurrentIndex(return_init["init_Controller_Type"])
            adb_data = Read_Config(maa_pi_config_Path)["adb"]
            if check_adb_path(adb_data):  # adb数据不存在
                self.Start_ADB_Detection()
            else:  # adb数据存在
                self.Autodetect_combox.addItem(
                    f'{check_path_for_keyword(adb_data["adb_path"])} ({adb_data["address"]})'
                )

        # 配置文件不完全存在
        elif (
            os.path.exists(resource_Path)
            and os.path.exists(interface_Path)
            and not (os.path.exists(maa_pi_config_Path))
        ):
            print("配置文件不存在")
            # 填充数据至组件
            data = {
                "adb": {"adb_path": "", "address": "127.0.0.1:0", "config": {}},
                "controller": {"name": ""},
                "gpu": -1,
                "resource": "",
                "task": [],
                "win32": {"_placeholder": 0},
            }
            Save_Config(maa_pi_config_Path, data)
            self.Resource_Combox.addItems(
                Get_Values_list(interface_Path, key1="resource")
            )
            self.Control_Combox.addItems(
                Get_Values_list(interface_Path, key1="controller")
            )
            self.SelectTask_Combox_1.addItems(
                Get_Values_list(interface_Path, key1="task")
            )
            self.Save_Resource()
            self.Save_Controller()
            self.Start_ADB_Detection()

        # 资源文件全部不存在
        else:
            InfoBar.error(
                title="错误",
                content="未检测到资源文件",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.BOTTOM_RIGHT,
                duration=-1,
                parent=self,
            )

    def refresh_widget(self, task_list=[]):
        # 刷新任务列表

        # 从组件获取配置的任务列表
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
        items = []
        for i in range(self.Task_List.count()):
            item = self.Task_List.item(i)
            if item is not None:
                items.append(item.text())
        return items

    def Completion_Options(self):
        target = self.Finish_combox.currentIndex()
        if target == 1:
            self.closeEmulator()
        elif target == 2:
            QApplication.quit()
        elif target == 3:
            self.closeEmulator()
            self.close()
        elif target == 4:
            self.shutdown()

    def closeEmulator(self):
        pass

    def shutdown(self):
        if platform.system() == "Windows":
            os.system("shutdown /s /t 1")
        elif platform.system() == "Linux":
            os.system("shutdown now")
        elif platform.system() == "macOS":
            os.system("sudo shutdown -h now")

    def Start_Up(self):
        self.S2_Button.setEnabled(False)
        self.S2_Button.setText("停止")
        self.TaskOutput_Text.clear()
        self.socket = QLocalSocket()
        self.socket.connectToServer("GUI2MAA")
        parameter = {
            "action_code": 1,  # 0,获取ADB设备 1:启动任务
            "resource_dir": os.getcwd(),  # 资源文件目录
            "cfg_dir": cfg.get(cfg.Maa_config).replace(
                os.path.join("config", "maa_pi_config.json"), ""
            ),  # 配置文件目录
            "directly": True,  # 是否直接启动任务
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
        self.MAA_Service_Process = subprocess.Popen(
            ["python", os.path.join(os.getcwd(), "MAA_Service.py")]
        )

    def task_list_changed(self):
        self.Task_List.clear()
        self.Task_List.addItems(Get_Values_list_Option(cfg.get(cfg.Maa_config), "task"))

    def Add_Task(self):
        # 添加任务
        Option = []
        Select_Target = self.SelectTask_Combox_1.currentText()
        MAA_Pi_Config = Read_Config(cfg.get(cfg.Maa_interface))
        Option_list = []

        for i in MAA_Pi_Config["task"]:
            # 将所有带有option的键值存进Option_list
            if i.get("option") is not None:
                Option_list.append(i)
        for i in Option_list:
            # 检查当前选中任务的是否为option_list中的元素
            if Select_Target == i["name"]:
                loop_count = len(i["option"])
                options_dicts = []
                # 根据option的长度，循环添加选项到列表中
                for index in range(loop_count):
                    select_box_name = f"SelectTask_Combox_{index + 2}"
                    selected_value = getattr(self, select_box_name).currentText()
                    options_dicts.append(
                        {"name": i["option"][index], "value": selected_value}
                    )
                Option.extend(options_dicts)
        MAA_Pi_Config = Read_Config(cfg.get(cfg.Maa_config))
        MAA_Pi_Config["task"].append({"name": Select_Target, "option": Option})
        Save_Config(cfg.get(cfg.Maa_config), MAA_Pi_Config)
        self.Task_List.clear()
        self.Task_List.addItems(Get_Values_list_Option(cfg.get(cfg.Maa_config), "task"))
        item = self.get_task_list_widget()
        signalBus.update_task_list.emit(item)

    def Delete_Task(self):

        Select_Target = self.Task_List.currentRow()

        self.Task_List.takeItem(Select_Target)
        Task_List = Get_Values_list2(cfg.get(cfg.Maa_config), "task")
        try:
            del Task_List[Select_Target]
        except IndexError:
            InfoBar.error(
                title="错误",
                content="没有任务可以被删除",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.BOTTOM_RIGHT,
                duration=2000,
                parent=self,
            )
        else:
            MAA_Pi_Config = Read_Config(cfg.get(cfg.Maa_config))
            del MAA_Pi_Config["task"]
            MAA_Pi_Config.update({"task": Task_List})
            Save_Config(cfg.get(cfg.Maa_config), MAA_Pi_Config)
        if Select_Target == 0:
            self.Task_List.setCurrentRow(Select_Target)
        elif Select_Target != -1:
            self.Task_List.setCurrentRow(Select_Target - 1)
        item = self.get_task_list_widget()
        signalBus.update_task_list.emit(item)

    def Move_Up(self):

        Select_Target = self.Task_List.currentRow()
        if Select_Target == 0:
            InfoBar.error(
                title="错误",
                content="已经是首位任务",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.BOTTOM_RIGHT,
                duration=2000,
                parent=self,
            )
        elif Select_Target != -1:
            MAA_Pi_Config = Read_Config(cfg.get(cfg.Maa_config))
            Select_Task = MAA_Pi_Config["task"].pop(Select_Target)
            MAA_Pi_Config["task"].insert(Select_Target - 1, Select_Task)
            Save_Config(cfg.get(cfg.Maa_config), MAA_Pi_Config)
            self.Task_List.clear()
            self.Task_List.addItems(
                Get_Values_list_Option(cfg.get(cfg.Maa_config), "task")
            )
            self.Task_List.setCurrentRow(Select_Target - 1)
        item = self.get_task_list_widget()
        signalBus.update_task_list.emit(item)

    def Move_Down(self):

        Select_Target = self.Task_List.currentRow()
        MAA_Pi_Config = Read_Config(cfg.get(cfg.Maa_config))
        if Select_Target >= len(MAA_Pi_Config["task"]) - 1:
            InfoBar.error(
                title="错误",
                content="已经是末位任务",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.BOTTOM_RIGHT,
                duration=2000,
                parent=self,
            )
        elif Select_Target < len(MAA_Pi_Config["task"]):
            Select_Task = MAA_Pi_Config["task"].pop(Select_Target)
            MAA_Pi_Config["task"].insert(Select_Target + 1, Select_Task)
            Save_Config(cfg.get(cfg.Maa_config), MAA_Pi_Config)
            self.Task_List.clear()
            self.Task_List.addItems(
                Get_Values_list_Option(cfg.get(cfg.Maa_config), "task")
            )
            self.Task_List.setCurrentRow(Select_Target + 1)
        item = self.get_task_list_widget()
        signalBus.update_task_list.emit(item)

    def Save_Resource(self):
        Resource_Type_Select = self.Resource_Combox.currentText()
        MAA_Pi_Config = Read_Config(cfg.get(cfg.Maa_config))
        MAA_Pi_Config["resource"] = Resource_Type_Select
        Save_Config(cfg.get(cfg.Maa_config), MAA_Pi_Config)

    def Save_Controller(self):
        Controller_Type_Select = self.Control_Combox.currentText()
        interface_Controller = Read_Config(cfg.get(cfg.Maa_interface))["controller"]

        for i in interface_Controller:
            if i["name"] == Controller_Type_Select:
                Controller_target = i["name"]
        MAA_Pi_Config = Read_Config(cfg.get(cfg.Maa_config))
        MAA_Pi_Config["controller"]["name"] = Controller_target
        Save_Config(cfg.get(cfg.Maa_config), MAA_Pi_Config)

    def Add_Select_Task_More_Select(self):

        self.clear_extra_widgets()

        select_target = self.SelectTask_Combox_1.currentText()

        MAA_Pi_Config = Read_Config(cfg.get(cfg.Maa_interface))

        for task in MAA_Pi_Config["task"]:
            if task["name"] == select_target and task.get("option") is not None:
                option_length = len(task["option"])

                # 根据option数量动态显示下拉框和标签
                for i in range(option_length):
                    select_box = getattr(self, f"SelectTask_Combox_{i+2}")
                    label = getattr(self, f"TaskName_Title_{i+2}")
                    option_name = task["option"][i]

                    # 填充下拉框数据
                    select_box.addItems(list(Get_Task_List(option_name)))
                    select_box.show()

                    # 显示标签
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
        self.S2_Button.clicked.disconnect()
        self.S2_Button.clicked.connect(self.Stop_task)
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

        if emu == []:
            InfoBar.error(
                title="错误",
                content="未检测到模拟器",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.BOTTOM_RIGHT,
                duration=-1,  # won't disappear automatically
                parent=self,
            )
        else:
            processed_list = []
            for i in emu:
                processed_s = i["name"]
                processed_list.append(processed_s)

            InfoBar.success(
                title="成功",
                content=f"检测到{processed_list[0]}",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.BOTTOM_RIGHT,
                duration=2000,
                parent=self,
            )
            self.Autodetect_combox.clear()
            self.Autodetect_combox.addItems(processed_list)

    def Save_ADB_Config(self):

        target = self.Autodetect_combox.text()
        for i in emu_data:
            if i["name"] == target:
                result = i

        data = Read_Config(cfg.get(cfg.Maa_config))
        data["adb"]["adb_path"] = result["adb_path"]
        data["adb"]["address"] = result["address"]
        data["adb"]["config"] = result["config"]
        Save_Config(cfg.get(cfg.Maa_config), data)

        signalBus.update_adb.emit(result)
