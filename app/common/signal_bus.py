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
    auto_update = Signal()  # 自动更新设置信号
    update_adb = (
        Signal()
    )  # 更新设置界面adb设备信息信号 从task_interface中获取adb信息,传到setting_interface中同步显示
    callback = Signal(dict)  # maafw回调协议信号
    update_task_list = Signal()  # 更新tasklist信息信号
    Notice_msg = Signal(str)  # 将外部通知的执行结果显示在任务输出中
    cfg_changed = Signal()  # 配置文件修改信号
    adb_detect_backup = Signal(list)  # 备份adb检测信号
    resource_exist = Signal(bool)  # 资源是否存在信号,可以在运行中更改
    title_changed = Signal()  # 标题栏改变信号
    update_finished_action = Signal()  # 更新完成后操作信号
    switch_config = Signal(dict)  # 主动切换配置信号
    start_task_inmediately = Signal()  # 立即启动任务信号
    download_finished = Signal(dict)  # 搜索资源完成信号
    dragging_finished = Signal()  # 拖拽完成信号
    bundle_download_progress = Signal(int, int)  # bundle下载进度信号
    bundle_download_finished = Signal(dict)  # bundle下载完成信号
    bundle_download_stopped = Signal()  # bundle下载停止信号
    update_download_progress = Signal(int, int)  # 更新下载进度信号
    update_download_finished = Signal(dict)  # 更新下载完成信号
    update_download_stopped = Signal()  # 更新下载停止信号
    download_self_progress = Signal(int, int)  # 下载自身进度信号
    download_self_finished = Signal(dict)  # 下载自身完成信号
    download_self_stopped = Signal()  # 下载自身停止信号
    mirror_bundle_download_progress = Signal(int, int)  # mirror bundle下载进度信号
    mirror_bundle_download_finished = Signal()  # mirror bundle下载完成信号
    mirror_bundle_download_stopped = Signal()  # mirror bundle下载停止信号
    custom_info = Signal(dict)  # 自定义动作/识别器成功信号
    setting_Visible = Signal(str)  # 设置界面可见信号
    lock_res_changed = Signal(bool)  # 锁定资源改变信号
    agent_info = Signal(str)  # agent信息信号
    infobar_message = Signal(dict)  # 信息栏消息信号
    run_sp_task = Signal(dict)  # 运行sp任务信号
    task_output_sync = Signal(dict)  # 任务输出同步信号
    show_AssistTool_task = Signal(bool)  # 显示隐藏子面板信号
    TaskCooldownPageClicked = Signal()  # 子面板点击信号


signalBus = SignalBus()
