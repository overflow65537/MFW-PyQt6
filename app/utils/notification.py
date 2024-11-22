from maa.notification_handler import NotificationHandler, NotificationType
from ..common.signal_bus import signalBus
from datetime import datetime


class MyNotificationHandler(NotificationHandler):

    def __init__(self, parent=None):
        self.callbackSignal = signalBus

    def on_resource_loading(
        self,
        noti_type: NotificationType,
        detail: NotificationHandler.ResourceLoadingDetail,
    ):
        print(f"on_resource_loading: {noti_type}, {detail}")

    def on_controller_action(
        self,
        noti_type: NotificationType,
        detail: NotificationHandler.ControllerActionDetail,
    ):
        self.callbackSignal.callback.emit("controller_action:" + str(noti_type.value))

    def on_tasker_task(
        self, noti_type: NotificationType, detail: NotificationHandler.TaskerTaskDetail
    ):

        self.callbackSignal.callback.emit("tasker_task:" + str(noti_type.value))

    def on_task_next_list(
        self,
        noti_type: NotificationType,
        detail: NotificationHandler.TaskNextListDetail,
    ):
        print(f"on_task_next_list: {noti_type}, {detail}")

    def on_task_recognition(
        self,
        noti_type: NotificationType,
        detail: NotificationHandler.TaskRecognitionDetail,
    ):
        print(f"on_task_recognition: {noti_type}, {detail}")

    def on_task_action(
        self, noti_type: NotificationType, detail: NotificationHandler.TaskActionDetail
    ):
        print(f"on_task_action: {noti_type}, {detail}")
