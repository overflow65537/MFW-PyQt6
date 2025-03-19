from PyQt6.QtCore import QObject, pyqtSignal


class SignalBus(QObject):
    """pyqtSignal bus"""

    switchToSampleCard = pyqtSignal(str, int)
    micaEnableChanged = pyqtSignal(bool)
    supportSignal = pyqtSignal()
    auto_update = pyqtSignal()  # 自动更新设置信号
    update_adb = pyqtSignal()  # 更新设置界面adb设备信息信号
    callback = pyqtSignal(dict)  # 回调协议信号
    update_task_list = pyqtSignal()  # 更新tasklist信息信号
    Notice_msg = pyqtSignal(str)  # 通知消息
    cfg_changed = pyqtSignal()  # 配置文件修改信号
    adb_detect_backup = pyqtSignal(list)  # 备份adb检测
    resource_exist = pyqtSignal(bool)  # 选择资源信号
    title_changed = pyqtSignal()  # 标题栏改变信号
    update_finished_action = pyqtSignal()  # 更新完成后操作信号
    switch_config = pyqtSignal(dict)  # 主动切换配置信号
    start_finish = pyqtSignal()  # 启动完成信号
    start_task_inmediately = pyqtSignal()  # 立即启动任务信号
    readme_available = pyqtSignal(str)  # readme文件信号
    download_finished = pyqtSignal(dict)  # 搜索资源完成信号
    dragging_finished = pyqtSignal()  # 拖拽完成信号
    bundle_download_progress = pyqtSignal(int, int)  # bundle下载进度信号
    bundle_download_finished = pyqtSignal(dict)  # bundle下载完成信号
    bundle_download_stopped = pyqtSignal()  # bundle下载停止信号
    update_download_progress = pyqtSignal(int, int)  # 更新下载进度信号
    update_download_finished = pyqtSignal(dict)  # 更新下载完成信号
    update_download_stopped = pyqtSignal()  # 更新下载停止信号
    download_self_progress = pyqtSignal(int, int)  # 下载自身进度信号
    download_self_finished = pyqtSignal(dict)  # 下载自身完成信号
    download_self_stopped = pyqtSignal()  # 下载自身停止信号
    mirror_bundle_download_progress = pyqtSignal(int, int)  # mirror bundle下载进度信号
    mirror_bundle_download_finished = pyqtSignal()  # mirror bundle下载完成信号
    mirror_bundle_download_stopped = pyqtSignal()  # mirror bundle下载停止信号
    custom_info = pyqtSignal(dict)  # 自定义动作/识别器成功信号
    setting_Visible = pyqtSignal(str)  # 设置界面可见信号
    speedrun = pyqtSignal()  # 速通模式信号
    lock_res_changed = pyqtSignal(bool)  # 锁定资源改变信号


signalBus = SignalBus()
