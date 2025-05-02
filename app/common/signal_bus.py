from PySide6.QtCore import QObject, Signal


class SignalBus(QObject):
    """Signal bus"""

    switchToSampleCard = Signal(str, int)
    micaEnableChanged = Signal(bool)
    supportSignal = Signal()
    auto_update = Signal()  # 自动更新设置信号
    update_adb = Signal()  # 更新设置界面adb设备信息信号
    callback = Signal(dict)  # 回调协议信号
    update_task_list = Signal()  # 更新tasklist信息信号
    Notice_msg = Signal(str)  # 通知消息
    cfg_changed = Signal()  # 配置文件修改信号
    adb_detect_backup = Signal(list)  # 备份adb检测
    resource_exist = Signal(bool)  # 选择资源信号
    title_changed = Signal()  # 标题栏改变信号
    update_finished_action = Signal()  # 更新完成后操作信号
    switch_config = Signal(dict)  # 主动切换配置信号
    start_finish = Signal()  # 启动完成信号
    start_task_inmediately = Signal()  # 立即启动任务信号
    readme_available = Signal(str)  # readme文件信号
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
    speedrun = Signal()  # 速通模式信号
    lock_res_changed = Signal(bool)  # 锁定资源改变信号
    agent_info = Signal(str)  # agent信息信号
    infobar_message = Signal(dict)  # 信息栏消息信号


signalBus = SignalBus()
