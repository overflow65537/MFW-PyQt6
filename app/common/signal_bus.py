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
from PySide6.QtCore import Signal, QObject


class SignalBus(QObject):
    """Signal bus"""

    micaEnableChanged = Signal(bool)  # Mica效果开关信号

    # 主布局中的配置切换和选项切换
    change_task_flow = Signal(dict)  # 切换任务列表
    show_option = Signal(dict)  # 显示选项
    agent_info = Signal(dict)  # 智能体信息
    title_changed = Signal(str)  # 窗口标题改变

    # maa sink 发送信号
    callback = Signal(dict)

    #输出到日志组件
    log_output = Signal(str,str) #(level,text)

    # 由信息输出组件发射，外部模块处理
    request_log_zip = Signal()  # 请求生成日志压缩包


signalBus = SignalBus()
