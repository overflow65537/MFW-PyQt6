"""
MFW-ChainFlow Assistant 全局常量定义
"""

# ==================== 基础任务固定 ID ==================== #
# 这些 ID 在整个系统中保持固定，便于识别和管理基础任务

# 资源设置任务的固定 ID
PRE_CONFIGURATION = "Pre-Configuration"

# 完成后操作任务的固定 ID
POST_ACTION = "Post-Action"

# ==================== 任务超时设置 ==================== #
# 任务超时控制相关常量

# 是否开启任务超时
TASK_TIMEOUT_ENABLED = False

# 任务超时时间（秒）
TASK_TIMEOUT_SECONDS = 300

# 任务超时后动作
# "notify" - 仅提醒
# "restart" - 重启任务
TASK_TIMEOUT_ACTION = "notify"
