from typing import Any, Dict

from .task_service import TaskService
from app.core.Item import CoreSignalBus



class OptionService:
    """选项服务实现"""

    def __init__(self, task_service: TaskService, signal_bus: CoreSignalBus):
        self.task_service = task_service
        self.signal_bus = signal_bus
        self.current_task_id = None
        self.current_options = {}

        # 连接信号
        self.signal_bus.task_selected.connect(self._on_task_selected)
        self.signal_bus.option_updated.connect(self._on_option_updated)

    def _on_task_selected(self, task_id: str):
        """当任务被选中时加载选项"""
        self.current_task_id = task_id
        task = self.task_service.get_task(task_id)
        if task:
            self.current_options = task.task_option
            self.signal_bus.options_loaded.emit(self.current_options)

    def _on_option_updated(self, option_data: Dict[str, Any]):
        """当选项更新时保存到当前任务"""
        if not self.current_task_id:
            return

        task = self.task_service.get_task(self.current_task_id)
        if not task:
            return

        # 更新任务中的选项
        task.task_option.update(option_data)
        # 发出任务更新信号（对象形式）
        self.signal_bus.task_updated.emit(task)

    def get_options(self) -> Dict[str, Any]:
        """获取当前任务的选项"""
        return self.current_options

    def get_option(self, option_key: str) -> Any:
        """获取特定选项"""
        return self.current_options.get(option_key)

    def update_option(self, option_key: str, option_value: Any) -> bool:
        """更新选项"""
        # 发出选项更新信号
        self.signal_bus.option_updated.emit({option_key: option_value})
        return True

    def update_options(self, options: Dict[str, Any]) -> bool:
        """批量更新选项"""
        # 发出选项更新信号
        self.signal_bus.option_updated.emit(options)
        return True
