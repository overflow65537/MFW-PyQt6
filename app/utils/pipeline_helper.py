"""Pipeline Override 辅助工具

提供从任务选项中提取 pipeline_override 的功能。
"""

from typing import Dict, Any
from ..utils.logger import logger


def get_pipeline_override_from_task_option(
    interface: Dict[str, Any],
    task_options: Dict[str, Any]
) -> Dict[str, Any]:
    """从任务选项中提取 pipeline_override
    
    Args:
        interface: interface.json 配置
        task_options: 任务选项字典，格式如：
            {
                "作战关卡": "4-20 厄险",
                "复现次数": "x1",
                "自定义关卡": {
                    "章节号": "4",
                    "难度": "Hard",
                    "超时时间": 20000
                }
            }
        
    Returns:
        Dict: 合并后的 pipeline_override
    """
    if not interface:
        logger.warning("Interface 配置为空")
        return {}
    
    merged_override = {}
    options = interface.get("option", {})
    
    for option_name, option_value in task_options.items():
        # 获取该选项的 pipeline_override
        option_override = _get_option_pipeline_override(
            options, option_name, option_value
        )
        
        # 深度合并
        _deep_merge_dict(merged_override, option_override)
    
    return merged_override


def _get_option_pipeline_override(
    options: Dict[str, Any],
    option_name: str,
    option_value: str | Dict[str, Any]
) -> Dict[str, Any]:
    """获取指定选项的 pipeline_override
    
    Args:
        options: interface.json 中的 option 字典
        option_name: 选项名称
        option_value: 选项值（select 类型为字符串，input 类型为字典）
        
    Returns:
        Dict: pipeline_override 字典
    """
    if option_name not in options:
        logger.debug(f"选项 '{option_name}' 不存在于 interface 配置中")
        return {}
    
    option_config = options[option_name]
    option_type = option_config.get("type", "select")
    
    if option_type == "select":
        if not isinstance(option_value, str):
            logger.error(f"Select 选项值必须是字符串，实际类型: {type(option_value)}")
            return {}
        return _get_select_pipeline_override(option_config, option_value)
    elif option_type == "input":
        if not isinstance(option_value, dict):
            logger.error(f"Input 选项值必须是字典，实际类型: {type(option_value)}")
            return {}
        return _get_input_pipeline_override(option_config, option_value)
    else:
        logger.warning(f"未知的选项类型: {option_type}")
        return {}


def _get_select_pipeline_override(
    option_config: Dict[str, Any],
    case_name: str
) -> Dict[str, Any]:
    """获取 select 类型选项的 pipeline_override
    
    Args:
        option_config: 选项配置
        case_name: case 名称
        
    Returns:
        Dict: pipeline_override 字典
    """
    cases = option_config.get("cases", [])
    for case in cases:
        if case.get("name") == case_name:
            return case.get("pipeline_override", {})
    
    logger.debug(f"未找到 case: {case_name}")
    return {}


def _get_input_pipeline_override(
    option_config: Dict[str, Any],
    input_values: Dict[str, Any]
) -> Dict[str, Any]:
    """获取 input 类型选项的 pipeline_override
    
    Args:
        option_config: 选项配置
        input_values: 输入值字典
        
    Returns:
        Dict: 处理后的 pipeline_override 字典
    """
    # 获取基础 pipeline_override
    base_override = option_config.get("pipeline_override", {})
    
    # 深拷贝以避免修改原始配置
    import copy
    result = copy.deepcopy(base_override)
    
    # 替换占位符
    result = _replace_placeholders(result, input_values)
    
    # 处理类型转换
    result = _convert_types(result, option_config, input_values)
    
    return result


def _replace_placeholders(
    pipeline_override: Dict[str, Any],
    input_values: Dict[str, Any]
) -> Dict[str, Any]:
    """替换 pipeline_override 中的占位符
    
    占位符格式: {输入名称}
    
    Args:
        pipeline_override: 原始 pipeline_override
        input_values: 输入值字典
        
    Returns:
        Dict: 替换后的 pipeline_override
    """
    def replace_recursive(obj):
        """递归替换占位符"""
        if isinstance(obj, dict):
            return {k: replace_recursive(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [replace_recursive(item) for item in obj]
        elif isinstance(obj, str):
            # 替换字符串中的占位符
            result = obj
            for input_name, input_value in input_values.items():
                placeholder = f"{{{input_name}}}"
                result = result.replace(placeholder, str(input_value))
            return result
        else:
            return obj
    
    result = replace_recursive(pipeline_override)
    # 确保返回字典类型
    return result if isinstance(result, dict) else {}


def _convert_types(
    pipeline_override: Dict[str, Any],
    option_config: Dict[str, Any],
    input_values: Dict[str, Any]
) -> Dict[str, Any]:
    """根据 pipeline_type 转换值的类型
    
    Args:
        pipeline_override: pipeline_override 字典（已替换占位符）
        option_config: 选项配置
        input_values: 输入值字典
        
    Returns:
        Dict: 类型转换后的 pipeline_override
    """
    inputs_config = option_config.get("inputs", [])
    
    # 创建输入值到类型的映射
    value_type_map = {}
    for input_config in inputs_config:
        input_name = input_config.get("name")
        pipeline_type = input_config.get("pipeline_type", "string")
        if input_name and input_name in input_values:
            # 将输入值的字符串形式映射到类型
            input_value = input_values[input_name]
            value_type_map[str(input_value)] = pipeline_type
    
    # 递归转换类型
    def convert_recursive(obj):
        if isinstance(obj, dict):
            return {k: convert_recursive(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_recursive(item) for item in obj]
        elif isinstance(obj, str) and obj in value_type_map:
            # 如果字符串匹配输入值，转换类型
            return _convert_value_type(obj, value_type_map[obj])
        else:
            return obj
    
    result = convert_recursive(pipeline_override)
    return result if isinstance(result, dict) else {}


def _convert_value_type(value, pipeline_type: str):
    """转换单个值的类型
    
    Args:
        value: 原始值
        pipeline_type: 目标类型 ("int", "float", "string", "bool")
        
    Returns:
        转换后的值
    """
    try:
        if pipeline_type == "int":
            return int(value)
        elif pipeline_type == "float":
            return float(value)
        elif pipeline_type == "bool":
            if isinstance(value, str):
                return value.lower() in ("true", "1", "yes")
            return bool(value)
        else:  # string
            return str(value)
    except (ValueError, TypeError) as e:
        logger.warning(f"类型转换失败: {value} -> {pipeline_type}, 错误: {e}")
        return value


def _deep_merge_dict(target: Dict, source: Dict) -> None:
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
            _deep_merge_dict(target[key], value)
        else:
            # 直接覆盖
            target[key] = value
