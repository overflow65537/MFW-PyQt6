"""选项数据管理模块

负责选项数据的保存、组织和转换。
"""

import json
from typing import TYPE_CHECKING

from qfluentwidgets import LineEdit, ComboBox, EditableComboBox, SwitchButton

from app.utils.logger import logger

if TYPE_CHECKING:
    from .....core.core import TaskItem, ServiceCoordinator


class OptionDataManager:
    """选项数据管理器
    
    负责:
    - 收集和保存控件值到任务选项
    - 组织控制器选项为 MAA 标准格式
    - 展平嵌套的控制器选项结构
    """

    def __init__(self, service_coordinator: "ServiceCoordinator"):
        self.service_coordinator = service_coordinator

    def save_options(self, task_item: "TaskItem", layout, is_resource_setting: bool = False):
        """收集当前所有选项控件的值并保存到配置
        
        Args:
            task_item: 当前任务项
            layout: 选项布局
            is_resource_setting: 是否是资源设置任务
        """
        # 递归查找所有控件的辅助函数
        def find_widgets_recursive(layout, widgets_list):
            """递归查找布局中的所有控件"""
            for i in range(layout.count()):
                item = layout.itemAt(i)
                if not item:
                    continue

                widget = item.widget()
                if widget:
                    widgets_list.append(widget)
                elif item.layout():
                    # 递归查找子布局
                    find_widgets_recursive(item.layout(), widgets_list)

        # 收集所有控件
        all_widgets = []
        find_widgets_recursive(layout, all_widgets)

        # 遍历所有控件，收集有 objectName 的选项控件
        updated_options = {}
        for widget in all_widgets:
            # 获取控件的 objectName
            obj_name = widget.objectName()
            if not obj_name:
                continue

            # 检查是否是多输入项格式(option$input_name)
            if "$" in obj_name:
                option_name, input_name = obj_name.split("$", 1)

                # 确保 option 存在
                if option_name not in updated_options:
                    updated_options[option_name] = {}

                # 获取值
                if isinstance(widget, LineEdit):
                    value = widget.text()

                    # 获取 pipeline_type 属性,根据类型转换值
                    pipeline_type = widget.property("pipeline_type")
                    if pipeline_type == "int":
                        # 尝试转换为整数,失败则保持字符串
                        try:
                            value = int(value) if value else 0
                        except ValueError:
                            logger.warning(
                                f"无法将 '{value}' 转换为整数,保持字符串格式"
                            )

                    updated_options[option_name][input_name] = value
            # 检查是否是嵌套选项格式(parent__nested__option_name)
            elif "__nested__" in obj_name:
                # 嵌套选项:作战关卡A__nested__是否进行信源回收
                # 提取真正的选项名(最后一部分)
                real_option_name = obj_name.split("__nested__")[-1]

                # 根据控件类型获取值
                if isinstance(widget, (ComboBox, EditableComboBox)):
                    value = widget.currentText()
                    updated_options[real_option_name] = value
                elif isinstance(widget, LineEdit):
                    updated_options[real_option_name] = widget.text()
            else:
                # 单个选项:普通格式
                # 根据控件类型获取值
                if isinstance(widget, (ComboBox, EditableComboBox)):
                    # 对于设备选择下拉框，不保存（它只用于触发自动填充）
                    if obj_name == "device":
                        # 设备选择框的值会通过自动填充逻辑保存到对应的字段
                        # (ADB: adb_path, adb_port, adb_device_name; Win32: hwnd, win32_device_name)
                        continue
                    # 对于资源选择和控制器类型下拉框，使用 userData
                    elif obj_name in ("controller_type", "resource"):
                        value = widget.currentData()
                        # 如果没有 userData（旧数据或手动输入），使用文本
                        if value is None:
                            value = widget.currentText()
                    # 对于 GPU 选择下拉框，使用 userData 并保存为整数
                    elif obj_name == "gpu":
                        value = widget.currentData()
                        # userData 应该已经是整数（-1, -2, 0, 1, ...）
                        if value is None:
                            # 如果没有 userData，默认使用 -1 (Auto)
                            value = -1
                    # 对于输入/截图方法下拉框，使用 userData 并保存为整数
                    elif obj_name in (
                        "adb_screenshot_method",
                        "adb_input_method",
                        "win32_screenshot_method",
                        "win32_input_method",
                    ):
                        # 检查是否有存储的原始值（用于不在映射表中的值）
                        original_value = widget.property("original_value")
                        if original_value is not None:
                            # 如果用户改变了选择，清除原始值，使用新选择的值
                            # 否则保持原始值
                            if widget.property("user_changed"):
                                value = widget.currentData()
                            else:
                                value = original_value
                        else:
                            value = widget.currentData()

                        # 如果有 userData，转换为整数
                        if value is not None:
                            try:
                                value = int(value)
                            except (ValueError, TypeError):
                                # 转换失败，使用文本
                                value = widget.currentText()
                        else:
                            # 没有 userData，使用文本
                            value = widget.currentText()
                    else:
                        value = widget.currentText()

                    updated_options[obj_name] = value
                elif isinstance(widget, LineEdit):
                    updated_options[obj_name] = widget.text()
                elif isinstance(widget, SwitchButton):
                    updated_options[obj_name] = widget.isChecked()

        # 更新任务的 task_option
        if updated_options:
            # 对于资源设置任务，需要重新组织 ADB 和 Win32 的选项
            if is_resource_setting:
                organized_options = self.organize_controller_options(updated_options)
                # 深度合并 adb 和 win32 组，避免覆盖未修改的字段
                for key, value in organized_options.items():
                    if key in ("adb", "win32") and isinstance(value, dict):
                        # 如果是 adb 或 win32 组，需要深度合并
                        if key not in task_item.task_option:
                            task_item.task_option[key] = {}
                        task_item.task_option[key].update(value)
                    else:
                        # 其他字段直接更新
                        task_item.task_option[key] = value
            else:
                task_item.task_option.update(updated_options)
            # 通过服务层保存
            self.service_coordinator.modify_task(task_item)

    def organize_controller_options(self, options: dict) -> dict:
        """将控制器选项组织为 MAA 标准格式

        将扁平的选项字典组织为:
        {
            "adb": {
                "adb_path": "...",
                "address": "...",
                "input_method": 0,
                "screen_method": 0,
                "config": {...}
            },
            "win32": {
                "hwnd": 0,
                "input_method": 0,
                "screen_method": 0
            },
            "controller": {...},
            "resource": "...",
            ...
        }
        """
        # ADB 相关字段映射（包括模拟器相关字段）
        adb_fields = {
            "adb_path": "adb_path",
            "adb_port": "address",  # adb_port 实际存储的是完整地址
            "adb_screenshot_method": "screen_method",
            "adb_input_method": "input_method",
            "adb_config": "config",
            # 模拟器相关字段
            "emulator_address": "emulator_address",
            "emulator_launch_args": "emulator_launch_args",
            "emulator_launch_timeout": "emulator_launch_timeout",
            # 设备名称（用于显示）
            "adb_device_name": "device_name",
        }

        # Win32 相关字段映射（包括应用相关字段）
        win32_fields = {
            "hwnd": "hwnd",
            "win32_screenshot_method": "screen_method",
            "win32_input_method": "input_method",
            # 应用相关字段
            "app_path": "app_path",
            "app_launch_args": "app_launch_args",
            "app_launch_timeout": "app_launch_timeout",
            # 设备相关字段
            "win32_device_name": "device_name",
        }

        # 通用字段（不属于 adb 或 win32）
        common_fields = [
            "controller_type",
            "resource",
            "gpu",
            "pre_launch_program",
            "pre_launch_program_args",
            "post_launch_program",
            "post_launch_program_args",
        ]

        result = {}
        adb_group = {}
        win32_group = {}

        for key, value in options.items():
            # 检查是否是 ADB 字段
            if key in adb_fields:
                target_key = adb_fields[key]
                # 特殊处理 config 字段（JSON 字符串转对象）
                if target_key == "config" and isinstance(value, str):
                    try:
                        adb_group[target_key] = json.loads(value) if value else {}
                    except:
                        adb_group[target_key] = {}
                else:
                    adb_group[target_key] = value
            # 检查是否是 Win32 字段
            elif key in win32_fields:
                target_key = win32_fields[key]
                win32_group[target_key] = value
            # 通用字段保持原样（直接保存值，不包装）
            elif key in common_fields:
                result[key] = value

        # 将分组后的选项添加到结果中（不包装 value/type）
        if adb_group:
            result["adb"] = adb_group
        if win32_group:
            result["win32"] = win32_group

        return result

    def flatten_controller_options(self, options: dict) -> dict:
        """将嵌套的控制器选项展平为扁平格式

        将 MAA 标准格式:
        {
            "adb": {
                "adb_path": "...",
                "address": "...",
                "input_method": 0,
                "screen_method": 0,
                "config": {...}
            },
            "win32": {
                "hwnd": 0,
                "input_method": 0,
                "screen_method": 0
            },
            ...
        }

        展平为内部使用的格式:
        {
            "adb_path": "...",
            "adb_port": "...",
            "adb_input_method": 0,
            "adb_screenshot_method": 0,
            "adb_config": "{...}",
            ...
        }
        """
        result = {}

        # 处理 ADB 配置
        if "adb" in options:
            adb_data = options["adb"]
            if isinstance(adb_data, dict):
                # 映射 ADB 基本字段
                if "adb_path" in adb_data:
                    result["adb_path"] = adb_data["adb_path"]
                if "address" in adb_data:
                    result["adb_port"] = adb_data["address"]
                if "input_method" in adb_data:
                    result["adb_input_method"] = adb_data["input_method"]
                if "screen_method" in adb_data:
                    result["adb_screenshot_method"] = adb_data["screen_method"]
                if "config" in adb_data:
                    # 将 config 对象转为 JSON 字符串
                    config_str = (
                        json.dumps(adb_data["config"]) if adb_data["config"] else ""
                    )
                    result["adb_config"] = config_str
                # 映射模拟器相关字段
                if "emulator_address" in adb_data:
                    result["emulator_address"] = adb_data["emulator_address"]
                if "emulator_launch_args" in adb_data:
                    result["emulator_launch_args"] = adb_data["emulator_launch_args"]
                if "emulator_launch_timeout" in adb_data:
                    result["emulator_launch_timeout"] = adb_data[
                        "emulator_launch_timeout"
                    ]
                # 映射设备名称字段
                if "device_name" in adb_data:
                    result["adb_device_name"] = adb_data["device_name"]

        # 处理 Win32 配置
        if "win32" in options:
            win32_data = options["win32"]
            if isinstance(win32_data, dict):
                # 映射 Win32 基本字段
                if "hwnd" in win32_data:
                    result["hwnd"] = win32_data["hwnd"]
                if "input_method" in win32_data:
                    result["win32_input_method"] = win32_data["input_method"]
                if "screen_method" in win32_data:
                    result["win32_screenshot_method"] = win32_data["screen_method"]
                # 映射应用相关字段
                if "app_path" in win32_data:
                    result["app_path"] = win32_data["app_path"]
                if "app_launch_args" in win32_data:
                    result["app_launch_args"] = win32_data["app_launch_args"]
                if "app_launch_timeout" in win32_data:
                    result["app_launch_timeout"] = win32_data["app_launch_timeout"]
                # 映射设备相关字段
                if "device_name" in win32_data:
                    result["win32_device_name"] = win32_data["device_name"]

        # 复制其他通用字段
        for key, value in options.items():
            if key not in ("adb", "win32"):
                result[key] = value

        return result
