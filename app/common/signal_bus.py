from PyQt6.QtCore import QObject, pyqtSignal


class SignalBus(QObject):
    """pyqtSignal bus"""

    switchToSampleCard = pyqtSignal(str, int)
    micaEnableChanged = pyqtSignal(bool)
    supportSignal = pyqtSignal()
    update_adb = pyqtSignal()  # 更新设置界面adb设备信息信号
    callback = pyqtSignal(str)  # 回调协议信号
    update_task_list = pyqtSignal()  # 更新tasklist信息信号
    Notice_msg = pyqtSignal(str)  # 通知消息
    update_available = pyqtSignal(dict)  # 检查更新
    update_finished = pyqtSignal()  # 更新完成信号
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


signalBus = SignalBus()
