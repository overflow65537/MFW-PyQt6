from typing import Any, Dict
from pathlib import Path
from .MaaFW import MaaFW
from .MaaSink import (
    MaaContextSink,
    MaaControllerEventSink,
    MaaResourceEventSink,
    MaaTaskerEventSink,
)
from ..Item import TaskItem
from ...utils.logger import logger


class Runner:
    """任务运行器"""

    need_stop = False

    def __init__(self, interface: dict):
        # 初始化 MaaFW
        self.maafw = MaaFW(
            maa_context_sink=MaaContextSink,
            maa_controller_sink=MaaControllerEventSink,
            maa_resource_sink=MaaResourceEventSink,
            maa_tasker_sink=MaaTaskerEventSink,
        )
        self.interface = interface

    async def connect_device(self, controller_raw: Dict[str, Any]):
        """连接 MaaFW"""
        if self._get_contrller_type(controller_raw) == "adb":
            return await self._connect_adb_controller(controller_raw)

        elif self._get_contrller_type(controller_raw) == "win":
            return await self._connect_win32_controller(controller_raw)
        else:
            raise ValueError("不支持的控制器类型")

    async def load_resources(self, resource_raw: Dict[str, Any]):
        """加载资源"""
        if self.maafw.resource:
            self.maafw.resource.clear()  # 清除资源
        resource_path = ""
        resource_target = resource_raw.get("resource", "")

        for i in self.interface.get("resource", {}):
            if i["name"] == resource_target:
                logger.debug(f"加载资源: {i['path']}")
                resource_path = i["path"]

        if resource_path == "" and not self.need_stop:
            logger.error(f"未找到目标资源: {resource_target}")
            await self.maafw.stop_task()
            return False

        for i in resource_path:
            resource = Path(i.replace("{PROJECT_DIR}", "./"))
            logger.debug(f"加载资源: {resource}")
            await self.maafw.load_resource(resource, resource_raw.get("gpu_index", -1))
            logger.debug(f"资源加载完成: {resource}")
        return True

    async def start_task(self, task_list: list[TaskItem]):
        """运行任务列表"""
        for task_item in task_list:
            if self.need_stop:
                break
            elif not task_item.is_checked:
                continue

            raw_info = self._get_task_execution_info(task_item)
            if not raw_info:
                continue

            entry, pipeline_override = raw_info.get("entry", ""), raw_info.get(
                "pipeline_override", {}
            )

            await self.maafw.run_task(entry, pipeline_override)

    async def stop_task(self):
        """停止当前任务"""
        self.need_stop = True
        await self.maafw.stop_task()

    async def _connect_adb_controller(self, controller_raw: Dict[str, Any]):
        """
        连接 ADB 控制器
        """
        # 从 controller_raw 中提取 ADB 配置
        adb_path = controller_raw.get("adb_path", "")
        address = controller_raw.get("address", "")
        input_method = controller_raw.get("input_method", "")
        screen_method = controller_raw.get("screen_method", "")
        config = controller_raw.get("config", {})

        # 尝试连接 ADB
        if (
            not await self.maafw.connect_adb(
                adb_path,
                address,
                input_method,
                screen_method,
                config,
            )
            and not self.need_stop
        ):
            return False
        return True

    async def _connect_win32_controller(self, controller_raw: Dict[str, Any]):
        """
        连接 Win32 控制器
        """
        hwnd: int = controller_raw.get("hwnd", 0)
        screencap_method: int = controller_raw.get("screencap_method", 0)
        mouse_method: int = controller_raw.get("screencap_method", 0)
        keyboard_method: int = controller_raw.get("keyboard_method", 0)

        # 直接调用 MaaFW 的连接方法
        if (
            not await self.maafw.connect_win32hwnd(
                hwnd,
                screencap_method,
                mouse_method,
                keyboard_method,
            )
            and not self.need_stop
        ):
            return False
        return True

    def _get_contrller_type(self, controller_raw: Dict[str, Any]) -> str:
        """获取控制器类型"""
        controller_name = controller_raw.get("controller_type", "").lower()
        for controller in self.interface.get("controller", []):
            if controller_name == controller.get("name", "").lower():
                return controller.get("type", "").lower()
        else:
            raise ValueError(f"未找到名称为 '{controller_name}' 的控制器")

    def _get_task_execution_info(self, task: TaskItem) -> Dict[str, Any] | None:
        """获取任务的执行信息（entry 和 pipeline_override）

        Args:
            task: 任务项

        Returns:
            Dict: 包含 entry 和 pipeline_override，格式为：
                {
                    "entry": "任务入口名称",
                    "pipeline_override": {...}
                }
            如果任务不存在或 interface 未加载，返回 None
        """

        # 从 interface 中查找任务的 entry
        entry = None
        task_pipeline_override = {}

        for interface_task in self.interface.get("task", []):
            if interface_task.get("name") == task.name:
                entry = interface_task.get("entry", "")
                # 获取任务级别的 pipeline_override
                task_pipeline_override = interface_task.get("pipeline_override", {})
                break

        if not entry:
            logger.warning(f"任务 '{task.name}' 在 interface 中未找到 entry")
            return None

        # 从 task_option 中提取 pipeline_override
        from app.core.utils.pipeline_helper import (
            get_pipeline_override_from_task_option,
        )

        option_pipeline_override = get_pipeline_override_from_task_option(
            self.interface, task.task_option
        )

        # 深度合并：任务级 pipeline_override + 选项级 pipeline_override
        merged_override = {}

        # 先添加任务级的
        self._deep_merge_dict(merged_override, task_pipeline_override)

        # 再添加选项级的（选项级优先级更高）
        self._deep_merge_dict(merged_override, option_pipeline_override)

        return {"entry": entry, "pipeline_override": merged_override}

    def _deep_merge_dict(self, target: Dict, source: Dict) -> None:
        """深度合并两个字典

        Args:
            target: 目标字典（会被修改）
            source: 源字典
        """
        for key, value in source.items():
            if (
                key in target
                and isinstance(target[key], dict)
                and isinstance(value, dict)
            ):
                # 递归合并
                self._deep_merge_dict(target[key], value)
            else:
                # 直接覆盖
                target[key] = value
