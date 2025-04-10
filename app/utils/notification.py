from maa.notification_handler import NotificationHandler, NotificationType
from ..common.signal_bus import signalBus
from ..utils.logger import logger


class MyNotificationHandler(NotificationHandler):

    def __init__(self, parent=None):
        self.callbackSignal = signalBus

    def on_controller_action(
        self,
        noti_type: NotificationType,
        detail: NotificationHandler.ControllerActionDetail,
    ):
        self.callbackSignal.callback.emit(
            {"name": "on_controller_action", "status": noti_type.value}
        )

    def on_tasker_task(
        self, noti_type: NotificationType, detail: NotificationHandler.TaskerTaskDetail
    ):

        self.callbackSignal.callback.emit(
            {"name": "on_tasker_task", "task": detail.entry, "status": noti_type.value}
        )

    def on_node_recognition(
        self,
        noti_type: NotificationType,
        detail: NotificationHandler.NodeRecognitionDetail,
    ):
        focus_mapping = {
            1:"start",
            2:"succeeded",
            3:"failed",
        }
        self.callbackSignal.callback.emit(
            {
                "name": "on_task_recognition",
                "task": detail.name,
                "status": noti_type.value,
                "focus": detail.focus[focus_mapping[noti_type.value]],
            }
        )
