"""
MFW-ChainFlow Assistant 全局常量定义
"""

# ==================== 基础任务固定 ID ==================== #
# 这些 ID 在整个系统中保持固定，便于识别和管理基础任务

# 资源设置任务的固定 ID
PRE_CONFIGURATION = "Pre-Configuration"

#控制器设置任务的固定 ID
_CONTROLLER_ = "Controller"

#资源设置任务的固定 ID
_RESOURCE_ = "Resource"

# 完成后操作任务的固定 ID
POST_ACTION = "Post-Action"

# ==================== 特殊任务类型常量 ==================== #
# 这些任务可以由用户自由添加、删除、移动和禁用

# 等待任务类型
SPECIAL_TASK_WAIT = "special_wait"

# 启动程序任务类型
SPECIAL_TASK_RUN_PROGRAM = "special_run_program"

# 通知任务类型
SPECIAL_TASK_NOTIFY = "special_notify"

# 所有特殊任务类型集合
SPECIAL_TASK_TYPES = frozenset({
    SPECIAL_TASK_WAIT,
    SPECIAL_TASK_RUN_PROGRAM,
    SPECIAL_TASK_NOTIFY,
})

# 基础任务 ID 集合（不可删除、不可移动）
BASE_TASK_IDS = frozenset({
    _CONTROLLER_,
    _RESOURCE_,
    POST_ACTION,
})
