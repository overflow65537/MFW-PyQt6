from enum import IntEnum, auto

class NoticeErrorCode(IntEnum):
    """通知模块错误码枚举"""
    SUCCESS = 0                # 成功
    DISABLED = auto()          # 通知未启用
    PARAM_EMPTY = auto()       # 关键参数为空（如URL/密钥）
    PARAM_INVALID = auto()     # 参数格式错误（如URL格式不符）
    NETWORK_ERROR = auto()     # 网络请求异常
    RESPONSE_ERROR = auto()    # 接口返回状态码错误
    # SMTP专属错误
    SMTP_PORT_INVALID = auto() # SMTP端口非整数
    SMTP_CONNECT_FAILED = auto()# SMTP连接失败
    # 可根据需要扩展其他通知类型专属错误