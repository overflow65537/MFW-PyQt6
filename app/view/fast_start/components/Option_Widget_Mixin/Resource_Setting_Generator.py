"""
资源设置表单生成器模块
用于为resource_base_task生成动态表单结构
"""

from typing import Dict, Any
from PySide6.QtCore import QObject


class ResourceSettingGenerator(QObject):
    """
    资源设置表单生成器类
    用于为resource_base_task生成动态表单结构
    继承自QObject，支持i18n翻译
    """

    def __init__(self, host):
        """
        初始化资源设置表单生成器
        :param host: 宿主组件，需要包含widgets、child_layouts等属性
        """
        super().__init__()
        self.host = host

    def create_resource_setting_form_structure(
        self, interface: Dict[str, Any]
    ) -> Dict[str, Dict[str, Any]]:
        """
        为资源设置任务创建动态表单结构
        Args:
            interface: 从interface.json加载的接口数据
        Returns:
            Dict: 表单结构字典，包含所有资源设置字段
        """
        form_structure = {}

        # 1. 设备类型选择
        controller_options = []
        controller_types = {}

        # 遍历控制器列表
        for controller in interface.get("controller", []):
            controller_name = controller.get("name", "")  # 保存时使用的键
            controller_label = controller.get(
                "label", controller_name
            )  # 显示的翻译后的label
            controller_type = controller.get("type", [])
            # 处理type可能是列表的情况
            if isinstance(controller_type, list):
                # 如果是列表，使用第一个元素作为类型
                controller_type = controller_type[0] if controller_type else ""
            # 将controller_type转换为小写
            controller_type_lower = str(controller_type).lower()
            # 处理Windows和Android的类型转换
            if controller_type_lower == "win32":
                controller_type_lower = "win32"  # 保持win32
            elif controller_type_lower == "adb":
                controller_type_lower = "adb"  # 保持adb
            else:
                # 其他类型尝试转换
                controller_type_lower = str(controller_type).lower()

            # 使用转换后的类型
            controller_type = controller_type_lower
            option_key = controller_name  # 使用controller的name作为唯一标识
            # 使用新格式: {"name": "唯一标识", "label": "显示内容"}
            controller_options.append({"name": option_key, "label": controller_label})
            controller_types[option_key] = controller_type  # 更新controller_types字典

        # 创建controller_type结构，为每个选项创建对应的子选项
        form_structure["controller_type"] = {
            "label": self.tr("Device Type"),
            "description": self.tr("Select the controller type"),
            "type": "combobox",
            "options": controller_options,
            "default": controller_options[0] if controller_options else "",
            "children": {},
        }

        # 2. 资源选择
        resource_options = []
        for resource in interface.get("resource", []):
            resource_name = resource.get("name", "")
            resource_label = resource.get(
                "label", resource_name
            )  # 优先使用label，没有则使用name
            # 使用新格式: {"name": "唯一标识", "label": "显示内容"}
            resource_options.append({"name": resource_name, "label": resource_label})

        form_structure["resource"] = {
            "label": self.tr("Resource"),
            "description": self.tr("Select the resource"),
            "type": "combobox",
            "options": resource_options,
            "default": resource_options[0] if resource_options else "",
        }

        # 3. GPU选择（默认隐藏）
        # 导入GPU缓存模块
        from app.utils.gpu_cache import gpu_cache

        # 初始化GPU信息缓存
        gpu_cache.initialize()

        # 构建选项列表，将GPU id和名称组合
        # 格式: [{ "display": "GPU名称", "value": "gpu_id" }, ...]
        gpu_options = []

        gpu_info = gpu_cache.get_gpu_info()

        # 直接将GPU名称作为选项值，后面会处理保存
        # gpu_info是{id: name}格式的字典

        # 构建选项列表，将GPU id和名称组合成一个字符串
        # 格式: "{name} (ID: {id})"
        # 保存时我们可以通过正则表达式提取实际的id
        gpu_options = []

        # 添加自动和CPU选项
        gpu_options.append(self.tr("Auto (ID: -1)"))  # 键值-1
        gpu_options.append(self.tr("CPU (ID: -2)"))  # 键值-2

        # 添加检测到的GPU设备
        for gpu_id, gpu_name in sorted(gpu_info.items()):
            # 创建包含id的显示字符串
            option_text = f"{gpu_name} (ID: {gpu_id})"
            gpu_options.append(option_text)

        # 保存GPU信息到form_structure中，以便ComboBoxGenerator使用
        form_structure["gpu"] = {
            "label": self.tr("GPU"),
            "description": self.tr("Select the GPU device"),
            "type": "gpu_combobox",  # 使用专门的GPU下拉框类型
            "options": gpu_options,  # 显示的名称列表，包含id信息
            "default": self.tr("Auto (ID: -1)"),  # 默认值为-1
            "visible": False,  # 默认隐藏
        }

        # 4. 启动前执行程序
        form_structure["pre_launch_program"] = {
            "label": self.tr("Pre-launch Program"),
            "description": self.tr("Path to the program to execute before launch"),
            "type": "pathlineedit",
            "default": "",
        }

        form_structure["pre_launch_args"] = {
            "label": self.tr("Pre-launch Arguments"),
            "description": self.tr("Arguments for the pre-launch program"),
            "type": "lineedit",
            "default": "",
        }

        # 5. 启动后执行程序
        form_structure["post_launch_program"] = {
            "label": self.tr("Post-launch Program"),
            "description": self.tr("Path to the program to execute after launch"),
            "type": "pathlineedit",
            "default": "",
        }

        form_structure["post_launch_args"] = {
            "label": self.tr("Post-launch Arguments"),
            "description": self.tr("Arguments for the post-launch program"),
            "type": "lineedit",
            "default": "",
        }

        # 定义子选项配置模板
        adb_path_config = {
            "label": self.tr("ADB Path"),
            "description": self.tr("Path to the ADB executable"),
            "type": "pathlineedit",
            "default": "",
            "visible": True,
        }

        device_address_config = {
            "label": self.tr("Device Address"),
            "description": self.tr("Address of the device"),
            "type": "lineedit",
            "default": "",
            "visible": True,
        }

        hwnd_config = {
            "label": self.tr("Window Handle (HWND)"),
            "description": self.tr("Window handle of the target program"),
            "type": "lineedit",
            "default": "",
            "visible": True,
        }

        program_path_config = {
            "label": self.tr("Program Path"),
            "description": self.tr("Path to the program executable"),
            "type": "pathlineedit",
            "default": "",
            "visible": True,
        }

        # 创建新的配置模板
        emulator_path_config = {
            "label": self.tr("Emulator Path"),
            "description": self.tr("Path to the emulator executable"),
            "type": "pathlineedit",
            "default": "",
            "visible": True,
        }

        emulator_args_config = {
            "label": self.tr("Emulator Arguments"),
            "description": self.tr("Arguments for the emulator"),
            "type": "lineedit",
            "default": "",
            "visible": True,
        }

        emulator_wait_time_config = {
            "label": self.tr("Emulator Wait Time"),
            "description": self.tr("Time to wait for the emulator to start"),
            "type": "lineedit",
            "default": "",
            "visible": True,
        }

        program_args_config = {
            "label": self.tr("Program Arguments"),
            "description": self.tr("Arguments for the program"),
            "type": "lineedit",
            "default": "",
            "visible": True,
        }

        program_wait_time_config = {
            "label": self.tr("Program Wait Time"),
            "description": self.tr("Time to wait for the program to start"),
            "type": "lineedit",
            "default": "",
            "visible": True,
        }

        # 创建搜索设备配置 - 只需指定类型和位置，内容已硬编码
        adb_search_device_config = {
            "type": "adb_search_device",
            "visible": True,
        }
        
        win32_search_device_config = {
            "type": "win32_search_device",
            "visible": True,
        }

        # controller_type选项的子选项配置 - 直接提供子选项配置，不使用form_group嵌套
        controller_children_types = {
            "adb": {
                "search_device": adb_search_device_config,
                "adb_path": adb_path_config,
                "device_address": device_address_config,
                "emulator_path": emulator_path_config,
                "emulator_args": emulator_args_config,
                "emulator_wait_time": emulator_wait_time_config,
            },
            "win32": {
                "search_device": win32_search_device_config,
                "hwnd": hwnd_config,
                "program_path": program_path_config,
                "program_args": program_args_config,
                "program_wait_time": program_wait_time_config,
            },
        }

        # 为每个controller选项创建对应的子配置
        for option_key, controller_type in controller_types.items():
            # 确定当前控制器类型对应的子配置
            for key, config in controller_children_types.items():
                # 使用精确匹配，确保每个设备类型都能正确关联对应的子选项
                if controller_type == key:
                    # 确保子选项配置有正确的结构，每个子选项都包含必要的键
                    form_structure["controller_type"]["children"][option_key] = config
                    break

        return form_structure


# 保持向后兼容性，提供一个函数接口
def create_resource_setting_form_structure(
    interface: Dict[str, Any],
) -> Dict[str, Dict[str, Any]]:
    """
    为资源设置任务创建动态表单结构（向后兼容函数接口）
    Args:
        interface: 从interface.json加载的接口数据
    Returns:
        Dict: 表单结构字典，包含所有资源设置字段
    """
    generator = ResourceSettingGenerator(None)
    return generator.create_resource_setting_form_structure(interface)