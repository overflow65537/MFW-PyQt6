from maa.controller import ControllerEventSink, Controller, NotificationType
from maa.resource import ResourceEventSink, Resource
from maa.tasker import TaskerEventSink, Tasker
from maa.context import ContextEventSink, Context

from app.common.signal_bus import signalBus


class MaaContextSink(ContextEventSink):

    def on_node_recognition(
        self,
        context: Context,
        noti_type: NotificationType,
        detail: ContextEventSink.NodeRecognitionDetail,
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
        signalBus.callback.emit(send_msg)


class MaaControllerEventSink(ControllerEventSink):
    def on_controller_action(
        self,
        controller: Controller,
        noti_type: NotificationType,
        detail: ControllerEventSink.ControllerActionDetail,
    ):
        pass


class MaaResourceEventSink(ResourceEventSink):

    def on_resource_loading(
        self,
        resource: Resource,
        noti_type: NotificationType,
        detail: ResourceEventSink.ResourceLoadingDetail,
    ):
        pass


class MaaTaskerEventSink(TaskerEventSink):

    def on_tasker_task(
        self,
        tasker: Tasker,
        noti_type: NotificationType,
        detail: TaskerEventSink.TaskerTaskDetail,
    ):
        signalBus.callback.emit(
            {"name": "on_tasker_task", "task": detail.entry, "status": noti_type.value}
        )
