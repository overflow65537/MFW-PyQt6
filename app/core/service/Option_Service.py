from typing import Any, Dict, Optional
from venv import logger

from .Task_Service import TaskService
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
        """当任务被选中时加载选项和表单结构"""
        self.current_task_id = task_id
        task = self.task_service.get_task(task_id)
        if task:
            self.current_options = task.task_option
            # 获取表单结构
            form_structure = self.get_form_structure_by_task_name(task.name)
            # 发送选项和表单结构
            logger.info(f"加载任务选项: {self.current_options}")
            logger.info(f"加载任务表单结构: {form_structure}")
            self.signal_bus.options_loaded.emit(
                {"options": self.current_options, "form_structure": form_structure}
            )

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

    def process_option_def(
        self, option_def: Dict[str, Any], all_options: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        递归处理选项定义，处理select类型中cases的子选项(option参数)

        Args:
            option_def: 选项定义字典
            all_options: 所有选项定义的字典

        Returns:
            Dict: 处理后的字段配置，可能包含children属性存储子选项
        """
        field_config = {}
        option_type = option_def.get("type")

        # 设置字段标签，处理$前缀
        label = option_def.get("label")
        if not label:
            label = option_def.get("name", "")
        if label.startswith("$"):
            pass

        field_config["label"] = label

        # 处理不同类型的选项
        if option_type == "select" or "cases" in option_def:
            # 默认类型为combobox
            field_config["type"] = "combobox"
            options = []
            children = {}

            # 处理cases中的每个选项
            for case in option_def.get("cases", []):
                # 优先使用label，如果没有则使用name
                display_label = case.get("label", case.get("name", ""))
                if display_label.startswith("$"):
                    display_label = display_label[1:]
                options.append(display_label)

                # 递归处理cases中的子选项(option参数)
                if "option" in case:
                    # 处理option可能是字符串或列表的情况
                    option_value = case["option"]
                    if isinstance(option_value, str) and option_value in all_options:
                        sub_option_def = all_options[option_value]
                        child_field = self.process_option_def(
                            sub_option_def, all_options
                        )
                        children[display_label] = child_field
                    elif isinstance(option_value, list):
                        # 处理option是列表的情况，这里简化处理，只取第一个有效的选项
                        for opt in option_value:
                            if isinstance(opt, str) and opt in all_options:
                                sub_option_def = all_options[opt]
                                child_field = self.process_option_def(
                                    sub_option_def, all_options
                                )
                                children[display_label] = child_field
                                break

            field_config["options"] = options
            # 如果有子选项，添加children属性
            if children:
                field_config["children"] = children

        # 对于input类型的选项，创建lineedit
        elif option_type == "input" and "inputs" in option_def:
            field_config["type"] = "lineedit"
            # 如果有默认值，使用第一个input的默认值
            if option_def["inputs"] and "default" in option_def["inputs"][0]:
                field_config["default"] = option_def["inputs"][0]["default"]

        # 默认类型
        else:
            field_config["type"] = "combobox"  # 默认为下拉选择框

        return field_config

    def get_form_structure_by_task_name(
        self, task_name: str
    ) -> Optional[Dict[str, Dict[str, Any]]]:
        """
        根据任务名称从interface获取对应的表单结构

        Args:
            task_name: 任务名称

        Returns:
            Dict: 表单结构字典，用于DynamicFormMixin的update_form方法
                  如果未找到对应任务或选项，返回None
        """
        if (
            not hasattr(self.task_service, "interface")
            or not self.task_service.interface
        ):
            return None

        form_structure = {}
        interface = self.task_service.interface

        # 遍历interface中的任务
        for task in interface.get("task", []):
            if task.get("name") == task_name:
                # 获取任务的option字段（字符串数组）
                task_option_names = task.get("option", [])
                # 获取顶层的option定义
                all_options = interface.get("option", {})

                # 遍历任务需要的每个选项
                for option_name in task_option_names:
                    if option_name in all_options:
                        option_def = all_options[option_name]
                        # 使用process_option_def方法递归处理选项定义
                        field_config = self.process_option_def(option_def, all_options)
                        form_structure[option_name] = field_config
                break

        return form_structure if form_structure else None
