import copy
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
        self.current_options: Dict[str, Any] = {}
        self.form_structure: Optional[Dict[str, Any]] = {}  # 保存当前表单结构

        # 连接信号
        self.signal_bus.task_selected.connect(self._on_task_selected)
        self.signal_bus.option_updated.connect(self._on_option_updated)

    def _on_task_selected(self, task_id: str):
        """当任务被选中时加载选项和表单结构"""
        self.current_task_id = task_id
        task = self.task_service.get_task(task_id)
        if task:
            self.current_options = task.task_option

            if task.item_id == "resource_base_task":

                self.form_structure = {"type": "resource"}
            else:
                # 获取表单结构
                self.form_structure = self.get_form_structure_by_task_name(
                    task.name, self.task_service.interface
                )
            self.signal_bus.options_loaded.emit()

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
        # 更新本地选项字典
        self.current_options[option_key] = option_value
        # 发出选项更新信号
        self.signal_bus.option_updated.emit({option_key: option_value})
        return True

    def update_options(self, options: Dict[str, Any]) -> bool:
        """批量更新选项"""
        # 批量更新本地选项字典
        self.current_options.update(options)
        # 发出选项更新信号
        self.signal_bus.option_updated.emit(options)
        return True

    def get_form_structure(self) -> Optional[Dict[str, Any]]:
        """获取当前表单结构"""
        return self.form_structure

    def get_form_field(self, field_name: str) -> Optional[Dict[str, Any]]:
        """获取特定表单字段的配置"""
        if isinstance(self.form_structure, dict):
            field_value = self.form_structure.get(field_name)
            # 确保返回的是字典类型，如果不是则返回None
            return field_value if isinstance(field_value, dict) else None
        return None

    def process_option_def(
        self,
        option_def: Dict[str, Any],
        all_options: Dict[str, Dict[str, Any]],
        option_key: str = "",
    ) -> Dict[str, Any]:
        """
        递归处理选项定义，处理select类型中cases的子选项(option参数)

        Args:
            option_def: 选项定义字典
            all_options: 所有选项定义的字典
            option_key: 选项的键名，当没有name和label时使用

        Returns:
            Dict: 处理后的字段配置，可能包含children属性存储子选项
        """
        field_config = {}
        option_type = option_def.get("type")

        # 设置字段标签，处理$前缀
        # 优先使用label，其次是name，如果都没有则使用option_key
        label = option_def.get("label", option_def.get("name", option_key))
        if label.startswith("$"):
            pass
        field_config["label"] = label

        # 处理description字段
        if "description" in option_def:
            field_config["description"] = option_def["description"]

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
                option_name = case.get("name", display_label)

                # 以字典形式保存name和label，用于i18n支持
                options.append({"name": option_name, "label": display_label})

                # 递归处理cases中的子选项(option参数)
                if "option" in case:
                    # 处理option可能是字符串或列表的情况
                    option_value = case["option"]
                    if isinstance(option_value, str) and option_value in all_options:
                        sub_option_def = all_options[option_value]
                        child_field = self.process_option_def(
                            sub_option_def, all_options, option_value
                        )
                        children[option_name] = (
                            child_field  # 使用name而不是label作为key
                        )
                    elif isinstance(option_value, list):
                        # 处理option是列表的情况，这里简化处理，只取第一个有效的选项
                        for opt in option_value:
                            if isinstance(opt, str) and opt in all_options:
                                sub_option_def = all_options[opt]
                                child_field = self.process_option_def(
                                    sub_option_def, all_options, opt
                                )
                                children[option_name] = (
                                    child_field  # 使用name而不是label作为key
                                )
                                break

            field_config["options"] = options
            # 如果有子选项，添加children属性
            if children:
                field_config["children"] = children

        # 对于input类型的选项，处理多个输入框
        elif option_type == "input" and "inputs" in option_def:
            # 对于input类型，我们将其视为一个组合类型
            # 每个input项将作为一个独立的lineedit字段
            # 但为了简化实现，这里创建一个lineedit作为主字段，实际使用时需要特殊处理
            field_config["type"] = "lineedit"
            # 保存inputs数组，供后续处理
            field_config["inputs"] = option_def["inputs"]

            # 传递verify字段到表单结构中
            if "verify" in option_def:
                field_config["verify"] = option_def["verify"]
            # 如果有默认值，使用第一个input的默认值
            if option_def["inputs"] and "default" in option_def["inputs"][0]:
                field_config["default"] = option_def["inputs"][0]["default"]

            # 为每个input项传递verify字段
            for input_item in field_config["inputs"]:
                # 如果input项没有自己的verify字段，使用父级的verify字段
                if "verify" not in input_item and "verify" in option_def:
                    input_item["verify"] = option_def["verify"]

        # 默认类型
        else:
            field_config["type"] = "combobox"  # 默认为下拉选择框

        return field_config

    def get_form_structure_by_task_name(
        self, task_name: str, interface: dict
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

        # 遍历interface中的任务
        for task in interface.get("task", []):
            if task.get("name") == task_name:
                # 获取任务的option字段（字符串数组）
                task_option_names = task.get("option", [])
                # 检查任务是否有description字段
                if "description" in task:
                    form_structure["description"] = task["description"]
                # 获取顶层的option定义
                all_options = interface.get("option", {})

                # 遍历任务需要的每个选项
                for option_name in task_option_names:
                    if option_name in all_options:
                        option_def = all_options[option_name]
                        # 使用process_option_def方法递归处理选项定义，传入option_name作为键名
                        field_config = self.process_option_def(
                            option_def, all_options, option_name
                        )
                        form_structure[option_name] = field_config
                break

        return form_structure if form_structure else None
