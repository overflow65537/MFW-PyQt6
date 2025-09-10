from maa.notification_handler import NotificationHandler, NotificationType


from .CoreSignalBus import core_signalBus,CoreSignalBus


class MyNotificationHandler(NotificationHandler):

    def __init__(self,callbackSignal:CoreSignalBus, parent=None):
        self.callbackSignal = callbackSignal.callback

    def on_controller_action(
        self,
        noti_type: NotificationType,
        detail: NotificationHandler.ControllerActionDetail,
    ):
        self.callbackSignal.emit(
            {"name": "on_controller_action", "status": noti_type.value}
        )

    def on_tasker_task(
        self, noti_type: NotificationType, detail: NotificationHandler.TaskerTaskDetail
    ):

        self.callbackSignal.emit(
            {"name": "on_tasker_task", "task": detail.entry, "status": noti_type.value}
        )

    def on_node_recognition(
        self,
        noti_type: NotificationType,
        detail: NotificationHandler.NodeRecognitionDetail,
    ):
        focus_mapping = {
            1: "start",
            2: "succeeded",
            3: "failed",
        }
        send_msg = {
            "name": "on_task_recognition",
            "task": detail.name,
            "status": noti_type.value,
            "focus": detail.focus.get(focus_mapping[noti_type.value], ""),
        }
        if (
            detail.focus.get("aborted")
            and not detail.focus.get(focus_mapping[1])
            and not detail.focus.get(focus_mapping[2])
            and not detail.focus.get(focus_mapping[3])
        ):
            send_msg["aborted"] = True
        self.callbackSignal.emit(send_msg)