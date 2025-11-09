#   This file is part of MFW-ChainFlow Assistant.

#   MFW-ChainFlow Assistant is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published
#   by the Free Software Foundation, either version 3 of the License,
#   or (at your option) any later version.

#   MFW-ChainFlow Assistant is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty
#   of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See
#   the GNU General Public License for more details.

#   You should have received a copy of the GNU General Public License
#   along with MFW-ChainFlow Assistant. If not, see <https://www.gnu.org/licenses/>.

#   Contact: err.overflow@gmail.com
#   Copyright (C) 2024-2025  MFW-ChainFlow Assistant. All rights reserved.


"""
MFW-ChainFlow Assistant
MFW-ChainFlow Assistant 信号总线
作者:overflow65537
"""

from re import S
from PySide6.QtCore import Signal, QObject


class SignalBus(QObject):
    """Signal bus"""

    micaEnableChanged = Signal(bool)  # Mica效果开关信号

    # 主布局中的配置切换和选项切换
    change_task_flow = Signal(dict) # 切换任务列表
    show_option = Signal(dict) # 显示选项
    agent_info = Signal(dict) # 智能体信息
    infobar_message = Signal(dict) # 信息栏消息
    infobar_signal = Signal(str, str) # InfoBar信号：正文, 类型(info/succeed/warning/error)
    title_changed = Signal(str) # 窗口标题改变

    # 日志/信息输出相关信号
    # 由外部模块发射，信息输出组件接收
    log_append = Signal(str)              # 追加一行日志文本
    log_set_text = Signal(str)            # 覆盖设置日志区域文本
    log_clear = Signal()                  # 清空日志
    log_level_changed = Signal(str)       # 设置/通知日志等级
    # 结构化日志：级别+文本（可按需扩展为 dict）
    log_entry = Signal(str, str)          # (level, text)
    # 统一事件：推荐使用（包含：正文、颜色、等级、选项）
    # payload: {
    #   "text": str,
    #   "level": str,          # DEBUG/INFO/WARNING/ERROR/CRITICAL
    #   "color": str|None,     # 文本颜色或#RRGGBB
    #   "output": bool,        # 是否输出到任务日志区域
    #   "infobar": bool,       # 是否弹出 InfoBar
    #   "infobar_type": str    # info/succeed/warning/error (若缺省按 level 映射)
    # }
    log_event = Signal(dict)

    # 由信息输出组件发射，外部模块处理
    request_log_zip = Signal()            # 请求生成日志压缩包

    # 任务/界面相关信号（根据当前使用处补齐声明）
    task_output_sync = Signal(dict)       # 任务输出同步
    update_task_list = Signal()           # 更新任务列表
    setting_Visible = Signal(str)         # 设置面板可见区域切换，如 "adb"/"win32"
    update_adb = Signal()                 # 更新 ADB 相关信息
    switch_config = Signal(dict)          # 切换配置
    start_task_inmediately = Signal()     # 立即开始任务
    run_sp_task = Signal(dict)            # 运行特殊任务 (单任务触发)
    custom_info = Signal(dict)            # 自定义信息 (动作/识别器等)
    resource_exist = Signal(bool)         # 资源存在状态
    callback = Signal(dict)               # 任务回调消息
    update_finished_action = Signal()     # 更新完成后动作下拉框
    dragging_finished = Signal()          # 拖动列表完成




signalBus = SignalBus()
