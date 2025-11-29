from maa.controller import ControllerEventSink, Controller, NotificationType
from maa.resource import ResourceEventSink, Resource
from maa.tasker import TaskerEventSink, Tasker
from maa.context import ContextEventSink, Context

from app.common.signal_bus import signalBus


class MaaContextSink(ContextEventSink):
    def on_raw_notification(self, context: Context, msg: str, details: dict):
        signalBus.callback.emit({"name": "context", "status": "focus", "details": details})
        print(f"上下文原始信息:{msg},详细信息:{details}")

    def on_node_next_list(
        self,
        context: Context,
        noti_type: NotificationType,
        detail: ContextEventSink.NodeNextListDetail,
    ):
        pass

    def on_node_action(
        self,
        context: Context,
        noti_type: NotificationType,
        detail: ContextEventSink.NodeActionDetail,
    ):
        pass

    def on_node_recognition(
        self,
        context: Context,
        noti_type: NotificationType,
        detail: ContextEventSink.NodeRecognitionDetail,
    ):
        pass



class MaaControllerEventSink(ControllerEventSink):
    def on_raw_notification(self, controller: Controller, msg: str, details: dict):
        pass
        print(f"控制器原始信息:{msg},详细信息:{details}")

    def on_controller_action(
        self,
        controller: Controller,
        noti_type: NotificationType,
        detail: ControllerEventSink.ControllerActionDetail,
    ):
        signalBus.callback.emit(
            {"name": "controller", "task": detail.action, "status": noti_type.value}
        )


class MaaResourceEventSink(ResourceEventSink):
    def on_raw_notification(self, resource: Resource, msg: str, details: dict):
        pass
        print(f"资源原始信息:{msg},详细信息:{details}")

    def on_resource_loading(
        self,
        resource: Resource,
        noti_type: NotificationType,
        detail: ResourceEventSink.ResourceLoadingDetail,
    ):
        signalBus.callback.emit({"name": "resource", "status": noti_type.value})


class MaaTaskerEventSink(TaskerEventSink):
    def on_raw_notification(self, tasker: Tasker, msg: str, details: dict):
        pass
        print(f"任务器原始信息:{msg},详细信息:{details}")

    def on_tasker_task(
        self,
        tasker: Tasker,
        noti_type: NotificationType,
        detail: TaskerEventSink.TaskerTaskDetail,
    ):
        signalBus.callback.emit(
            {"name": "tasker_task", "task": detail.entry, "status": noti_type.value}
        )
