"""
消息类型定义和辅助函数

提供统一的消息类型常量和便捷的消息发送函数。
"""

from enum import Enum
from typing import Literal, Optional


class MessageType(str, Enum):
    """消息类型枚举"""
    
    # 通用消息类型
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    
    # MaaFW 核心相关
    CUSTOM_ACTION_LOADED = "custom_action_loaded"
    CUSTOM_RECOGNITION_LOADED = "custom_recognition_loaded"
    
    # Agent 相关
    AGENT_START = "agent_start"
    AGENT_STOP = "agent_stop"
    AGENT_CONNECTED = "agent_connected"
    AGENT_DISCONNECTED = "agent_disconnected"
    
    # 错误类型
    ERROR_RESOURCE = "error_resource"  # 资源未初始化
    ERROR_CONTROLLER = "error_controller"  # 控制器未初始化
    ERROR_TASKER = "error_tasker"  # Tasker 未初始化
    ERROR_AGENT_START = "error_agent_start"  # Agent 启动失败
    ERROR_AGENT_CONNECT = "error_agent_connect"  # Agent 连接失败


class MessageLevel(str, Enum):
    """消息级别枚举"""
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"


def create_message(
    message_type: str | MessageType,
    message: str,
    level: Optional[str | MessageLevel] = None,
) -> dict:
    """创建标准消息字典
    
    Args:
        message_type: 消息类型
        message: 消息内容
        level: 消息级别，如果不提供则根据 type 自动推断
    
    Returns:
        标准消息字典
    
    Examples:
        >>> create_message(MessageType.SUCCESS, "操作成功")
        {"type": "success", "message": "操作成功", "level": "success"}
        
        >>> create_message("custom_action_loaded", "加载自定义动作: MyAction")
        {"type": "custom_action_loaded", "message": "加载自定义动作: MyAction", "level": "info"}
    """
    if isinstance(message_type, MessageType):
        message_type = message_type.value
    
    # 自动推断消息级别
    if level is None:
        if message_type.startswith("error"):
            level = MessageLevel.ERROR
        elif message_type in ["success", "agent_connected"]:
            level = MessageLevel.SUCCESS
        elif message_type in ["warning"]:
            level = MessageLevel.WARNING
        else:
            level = MessageLevel.INFO
    
    if isinstance(level, MessageLevel):
        level = level.value
    
    return {
        "type": message_type,
        "message": message,
        "level": level,
    }


def emit_message(signal_bus, message_type: str | MessageType, message: str, level: Optional[str | MessageLevel] = None):
    """便捷函数：发送消息到 message_output 信号
    
    Args:
        signal_bus: SignalBus 实例
        message_type: 消息类型
        message: 消息内容
        level: 消息级别
    
    Examples:
        >>> from app.common.signal_bus import signalBus
        >>> emit_message(signalBus, MessageType.SUCCESS, "任务完成")
    """
    msg = create_message(message_type, message, level)
    signal_bus.message_output.emit(msg)


def emit_error(signal_bus, message: str, error_type: str = "error"):
    """便捷函数：发送错误消息
    
    Args:
        signal_bus: SignalBus 实例
        message: 错误消息
        error_type: 错误类型，默认为 "error"
    """
    emit_message(signal_bus, error_type, message, MessageLevel.ERROR)


def emit_success(signal_bus, message: str):
    """便捷函数：发送成功消息
    
    Args:
        signal_bus: SignalBus 实例
        message: 成功消息
    """
    emit_message(signal_bus, MessageType.SUCCESS, message, MessageLevel.SUCCESS)


def emit_info(signal_bus, message: str):
    """便捷函数：发送信息消息
    
    Args:
        signal_bus: SignalBus 实例
        message: 信息内容
    """
    emit_message(signal_bus, MessageType.INFO, message, MessageLevel.INFO)


def emit_warning(signal_bus, message: str):
    """便捷函数：发送警告消息
    
    Args:
        signal_bus: SignalBus 实例
        message: 警告内容
    """
    emit_message(signal_bus, MessageType.WARNING, message, MessageLevel.WARNING)
