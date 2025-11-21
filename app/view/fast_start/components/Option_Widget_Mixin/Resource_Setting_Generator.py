"""
资源设置表单生成器模块
用于为resource_base_task生成动态表单结构
"""

from typing import Dict, Any, Optional


def create_resource_setting_form_structure(
    interface: Dict[str, Any],
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
    for controller in interface.get("controller", []):
        controller_options.append(controller.get("name", ""))

    form_structure["controller_type"] = {
        "label": "设备类型",
        "type": "combobox",
        "options": controller_options,
        "default": controller_options[0] if controller_options else "",
    }

    # 2. 资源选择
    resource_options = []
    for resource in interface.get("resource", []):
        resource_options.append(resource.get("name", ""))

    form_structure["resource"] = {
        "label": "资源选择",
        "type": "combobox",
        "options": resource_options,
        "default": resource_options[0] if resource_options else "",
    }

    # 3. GPU选择（默认隐藏）
    form_structure["gpu"] = {
        "label": "GPU选择",
        "type": "lineedit",
        "default": "",
        "visible": False,
    }

    # 4. 启动前执行程序
    form_structure["pre_launch_program"] = {
        "label": "启动前执行程序路径",
        "type": "lineedit",
        "default": "",
    }

    form_structure["pre_launch_args"] = {
        "label": "启动前执行程序参数",
        "type": "lineedit",
        "default": "",
    }

    # 5. 启动后执行程序
    form_structure["post_launch_program"] = {
        "label": "启动后执行程序路径",
        "type": "lineedit",
        "default": "",
    }

    form_structure["post_launch_args"] = {
        "label": "启动后执行程序参数",
        "type": "lineedit",
        "default": "",
    }

    # 6. 安卓端特有配置
    form_structure["adb_path"] = {
        "label": "ADB路径",
        "type": "lineedit",
        "default": "",
        "visible": False,  # 初始隐藏，根据controller_type动态显示
    }

    form_structure["device_address"] = {
        "label": "设备链接地址",
        "type": "lineedit",
        "default": "",
        "visible": False,  # 初始隐藏，根据controller_type动态显示
    }

    # 7. 桌面端特有配置
    form_structure["hwnd"] = {
        "label": "窗口句柄",
        "type": "lineedit",
        "default": "",
        "visible": False,  # 初始隐藏，根据controller_type动态显示
    }

    form_structure["program_path"] = {
        "label": "程序启动路径",
        "type": "lineedit",
        "default": "",
        "visible": False,  # 初始隐藏，根据controller_type动态显示
    }

    return form_structure
