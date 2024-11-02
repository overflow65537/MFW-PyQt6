from maa.toolkit import Toolkit

# from maa.custom_recognition import CustomRecognition
# from maa.custom_action import CustomAction

from maa.notification_handler import NotificationHandler, NotificationType
from PyQt6.QtNetwork import QLocalServer, QLocalSocket
from PyQt6.QtCore import QByteArray, QObject
from PyQt6.QtWidgets import QApplication


from datetime import datetime
import json
import sys


class MyNotificationHandler(NotificationHandler):

    def __init__(self, parent=None):
        self.socket = QLocalSocket()
        self.socket.connectToServer("MAA2GUI")
        self.sendData("MAA_runing")

    def sendData(self, msg):
        data = QByteArray(bytes(msg, "utf-8"))  # 要发送的数据
        self.socket.write(data)  # 发送数据

    def on_controller_action(
        self,
        noti_type: NotificationType,
        detail: NotificationHandler.ControllerActionDetail,
    ):
        now_time = datetime.now().strftime("%H:%M:%S")
        if noti_type.value == 1:
            self.sendData(f"{now_time}" + "  连接中")
        elif noti_type.value == 2:
            self.sendData(f"{now_time}" + "  连接成功")
        elif noti_type.value == 3:
            self.sendData(f"{now_time}" + "  连接失败")
        else:
            self.sendData(f"{now_time}" + "  连接状态未知")

    def on_tasker_task(
        self, noti_type: NotificationType, detail: NotificationHandler.TaskerTaskDetail
    ):
        now_time = datetime.now().strftime("%H:%M:%S")
        status_map = {0: "未知", 1: "运行中", 2: "成功", 3: "失败"}
        self.sendData(
            f"{now_time}"
            + "  "
            + f"{detail.entry}"
            + " "
            + f"{status_map[noti_type.value]}"
        )

    def on_resource_loading(
        self,
        noti_type: NotificationType,
        detail: NotificationHandler.ResourceLoadingDetail,
    ):
        pass
        # self.sendData(f"on_resource_loading: {noti_type}, {detail}")

    def on_task_next_list(
        self,
        noti_type: NotificationType,
        detail: NotificationHandler.TaskNextListDetail,
    ):
        self.sendData(f"on_task_next_list: {noti_type}, {detail}")

    def on_task_recognition(
        self,
        noti_type: NotificationType,
        detail: NotificationHandler.TaskRecognitionDetail,
    ):
        self.sendData(f"on_task_recognition: {noti_type}, {detail}")

    def on_task_action(
        self, noti_type: NotificationType, detail: NotificationHandler.TaskActionDetail
    ):
        self.sendData(f"on_task_action: {noti_type}, {detail}")


class MAA_Service(QObject):

    def __init__(self):
        super().__init__()

        self.server = QLocalServer(self)
        self.server.newConnection.connect(self.connection)
        self.server.listen("GUI2MAA")

        self.socket = QLocalSocket()
        self.socket.connectToServer("MAA2GUI")
        self.sendData("MAA_started")

    def connection(self):
        socket = self.server.nextPendingConnection()
        socket.readyRead.connect(lambda: self.signal_routing(socket))

    def signal_routing(self, socket):
        data = socket.readAll().data().decode("utf-8")
        # print("接受到的数据:", data)
        parameter = json.loads(data)  # 解析json数据
        keys_to_extract = ["resource_dir", "cfg_dir", "directly"]
        values_list = [parameter[key] for key in keys_to_extract if key in parameter]
        # 断开MAA2GUI连接 准备将连接转交给回调协议
        self.socket.disconnectFromServer()
        self.socket.waitForDisconnected()
        print("参数列表:", values_list[0], values_list[1], values_list[2])
        custom_maa(values_list[0], values_list[1], values_list[2])
        self.socket = QLocalSocket()
        self.socket.connectToServer("MAA2GUI")
        self.sendData("MAA_completed")

    def sendData(self, msg):
        data = QByteArray(bytes(msg, "utf-8"))  # 要发送的数据
        self.socket.write(data)  # 发送数据


class custom_maa:
    def __init__(self, resource_dir, cfg_dir, directly):
        """
        # 注册自定义识别器
        Toolkit.register_custom_recognition("MyReco", MyRecognition())

        # 注册自定义动作
        Toolkit.register_custom_action("MyAct", MyAction())
        """
        # 启动MAA
        self.MyNotificationHandler = MyNotificationHandler(self)
        Toolkit.pi_run_cli(
            resource_dir,
            cfg_dir,
            directly,
            notification_handler=self.MyNotificationHandler,
        )

    """
    class MyRecognition(CustomRecognition):
        def analyze(context, ...):
            # 获取图片，然后进行自己的图像操作
            image = context.tasker.controller.cached_image
            # 返回图像分析结果
            return AnalyzeResult(box=(10, 10, 100, 100))

    class MyAction(CustomAction):
        def run(context, ...):
            # 进行点击
            context.controller.post_click(100, 10).wait()
            # 重写接下来要执行的任务
            context.override_next(task_name, ["TaskA", "TaskB"])
    """


if __name__ == "__main__":
    app = QApplication(sys.argv)
    service = MAA_Service()  # 启动服务
    sys.exit(app.exec())
