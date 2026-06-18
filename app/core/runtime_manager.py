"""
MFW-ChainFlow Assistant
多实例运行时管理器

按 config_id 管理独立的运行体（TaskFlowRunner + MaaFW + RunnerEvents + 日志处理器 +
独立的 Config/Task 服务栈）。每个配置的启动/停止、日志、监控相互隔离。

架构约束：本文件位于 app/core/（与 core.py、log_processor.py 同级），允许像 core.py
那样向全局 signalBus 转发；但仍通过 RunnerEvents -> 桥接 -> signalBus 的链路，
不让 Runner 自身直接 import signalBus。
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable, Dict, List, Optional

from PySide6.QtCore import QObject, Qt, Slot

from app.common.signal_bus import signalBus
from app.utils.logger import logger

if TYPE_CHECKING:  # 避免循环导入
    from app.core.core import ServiceCoordinator
    from app.core.runner.task_flow import TaskFlowRunner
    from app.core.item import RunnerEvents, FromeServiceCoordinator
    from app.core.log_processor import CallbackLogProcessor
    from app.core.service.config_service import ConfigService
    from app.core.service.task_service import TaskService


class _TaggedRunnerBridge(QObject):
    """将某个配置专属运行体的事件转发到全局 signalBus。

    - 始终发射带 config_id 的信号（多实例隔离）。
    - 当该配置恰为当前激活配置时，额外发射无 config_id 的旧信号，
      使既有视图（按当前配置工作）保持原有行为。
    """

    def __init__(self, config_id: str, is_current: Callable[[str], bool], parent=None):
        super().__init__(parent)
        self.config_id = config_id
        self._is_current = is_current

    def _current(self) -> bool:
        try:
            return bool(self._is_current(self.config_id))
        except Exception:
            return False

    @Slot(dict)
    def forward_callback(self, payload: dict):
        if self._current():
            signalBus.callback.emit(payload)

    @Slot(str, str)
    def forward_log_output(self, level: str, text: str):
        signalBus.log_output_at.emit(self.config_id, level, text)
        if self._current():
            signalBus.log_output.emit(level, text)

    @Slot(str)
    def forward_set_window_title(self, title: str):
        if self._current():
            signalBus.set_window_title.emit(title)

    @Slot(str, str)
    def forward_task_status_changed(self, task_id: str, status: str):
        signalBus.task_status_changed_at.emit(self.config_id, task_id, status)
        if self._current():
            signalBus.task_status_changed.emit(task_id, status)

    @Slot(dict)
    def forward_task_flow_finished(self, payload: dict):
        signalBus.task_flow_finished_at.emit(self.config_id, payload)
        if self._current():
            signalBus.task_flow_finished.emit(payload)

    @Slot()
    def forward_log_clear_requested(self):
        signalBus.log_clear_requested_at.emit(self.config_id)
        if self._current():
            signalBus.log_clear_requested.emit()

    @Slot(str, str)
    def forward_info_bar_requested(self, level: str, message: str):
        if self._current():
            signalBus.info_bar_requested.emit(level, message)

    @Slot(str)
    def forward_focus_toast(self, message: str):
        if self._current():
            signalBus.focus_toast.emit(message)

    @Slot(str)
    def forward_focus_notification(self, message: str):
        # 系统级通知与配置是否为当前无关，始终发送
        signalBus.focus_notification.emit(message)

    @Slot(str)
    def forward_focus_dialog(self, message: str):
        if self._current():
            signalBus.focus_dialog.emit(message)

    @Slot(str)
    def forward_focus_modal(self, message: str):
        if self._current():
            signalBus.focus_modal.emit(message)

    @Slot(dict)
    def forward_controller_setup_hint_requested(self, payload: dict):
        if self._current():
            signalBus.controller_setup_hint_requested.emit(payload)

    @Slot(dict)
    def forward_monitor_recognition_roi(self, payload: dict):
        signalBus.monitor_recognition_roi_at.emit(self.config_id, payload)
        if self._current():
            signalBus.monitor_recognition_roi.emit(payload)


class RuntimeInstance:
    """单个配置的运行体（专属服务栈 + Runner + 事件桥接）。"""

    def __init__(
        self,
        config_id: str,
        runner: "TaskFlowRunner",
        runner_events: "RunnerEvents",
        fs_signal_bus: "FromeServiceCoordinator",
        log_processor: "CallbackLogProcessor",
        bridge: _TaggedRunnerBridge,
        config_service: "ConfigService",
        task_service: "TaskService",
    ):
        self.config_id = config_id
        self.runner = runner
        self.runner_events = runner_events
        self.fs_signal_bus = fs_signal_bus
        self.log_processor = log_processor
        self.bridge = bridge
        self.config_service = config_service
        self.task_service = task_service
        # 运行态由按钮状态信号与 run/stop 调用共同维护
        self.running: bool = False

    @property
    def is_running(self) -> bool:
        try:
            return bool(self.running or self.runner.is_running)
        except Exception:
            return self.running


class RuntimeInstanceManager:
    """按 config_id 管理多个并行运行体。

    仅在多实例模式开启时被协调器用于创建独立运行体；单实例模式下协调器仍使用
    其内置的主运行器（不经过本管理器）。
    """

    def __init__(self, coordinator: "ServiceCoordinator"):
        self._coordinator = coordinator
        self._instances: Dict[str, RuntimeInstance] = {}

    # ---- 查询 ----
    def get_instance(self, config_id: str) -> Optional[RuntimeInstance]:
        return self._instances.get(config_id)

    def is_running(self, config_id: str) -> bool:
        inst = self._instances.get(config_id)
        return bool(inst and inst.is_running)

    def any_running(self) -> bool:
        return any(inst.is_running for inst in self._instances.values())

    def running_config_ids(self) -> List[str]:
        return [cid for cid, inst in self._instances.items() if inst.is_running]

    # ---- 生命周期 ----
    def _get_or_create(self, config_id: str) -> RuntimeInstance:
        inst = self._instances.get(config_id)
        if inst is not None:
            return inst
        inst = self._coordinator._build_runtime_instance(config_id)
        # 关联按钮状态信号到管理器，转换为带 config_id 的状态广播
        inst.fs_signal_bus.fs_start_button_status.connect(
            lambda payload, cid=config_id: self._on_instance_button_status(cid, payload),
            Qt.ConnectionType.QueuedConnection,
        )
        self._instances[config_id] = inst
        return inst

    async def run(self, config_id: str, task_id: str | None = None, *, start_task_id: str | None = None):
        """启动指定配置的任务流（独立运行体）。"""
        if not config_id:
            logger.warning("RuntimeInstanceManager.run: 空的 config_id，忽略")
            return
        if self.is_running(config_id):
            logger.warning("配置 %s 已在运行，忽略重复启动", config_id)
            return
        inst = self._get_or_create(config_id)
        # 启动前刷新该配置的服务栈快照，确保读取最新磁盘数据
        try:
            self._coordinator._refresh_runtime_instance(inst)
        except Exception as exc:
            logger.warning("刷新运行体 %s 失败（继续尝试运行）: %s", config_id, exc)
        inst.running = True
        signalBus.config_run_state_changed.emit(config_id, True)
        try:
            return await inst.runner.run_tasks_flow(task_id, start_task_id=start_task_id)
        finally:
            # 运行结束后由按钮状态信号同步 running=False；此处兜底
            if not inst.runner.is_running:
                inst.running = False
                signalBus.config_run_state_changed.emit(config_id, False)

    async def stop(self, config_id: str, *, manual: bool = False):
        inst = self._instances.get(config_id)
        if not inst:
            return
        try:
            return await inst.runner.stop_task(manual=manual)
        finally:
            inst.running = False
            signalBus.config_run_state_changed.emit(config_id, False)

    async def stop_all(self, *, manual: bool = False):
        for config_id in list(self._instances.keys()):
            try:
                await self.stop(config_id, manual=manual)
            except Exception as exc:
                logger.warning("停止配置 %s 失败: %s", config_id, exc)

    def shutdown_sync(self):
        """应用退出时的同步兜底清理。"""
        for config_id, inst in list(self._instances.items()):
            try:
                shutdown = getattr(inst.runner, "shutdown_runtime_sync", None)
                if callable(shutdown):
                    shutdown()
            except Exception as exc:
                logger.warning("同步关闭运行体 %s 失败: %s", config_id, exc)
            inst.running = False

    # ---- 内部 ----
    def _on_instance_button_status(self, config_id: str, payload: dict):
        inst = self._instances.get(config_id)
        running = (
            isinstance(payload, dict)
            and payload.get("text") == "STOP"
            and payload.get("status") == "enabled"
        )
        if inst is not None:
            inst.running = running
        # 带 config_id 的按钮状态（供配置列表/各配置卡片）
        try:
            self._coordinator.fs_signal_bus.fs_start_button_status_at.emit(config_id, payload)
        except Exception:
            pass
        signalBus.config_run_state_changed.emit(config_id, running)
        # 若该配置为当前激活配置，则同步主开始按钮
        try:
            if self._coordinator.config_service.current_config_id == config_id:
                self._coordinator.fs_signal_bus.fs_start_button_status.emit(payload)
        except Exception:
            pass
