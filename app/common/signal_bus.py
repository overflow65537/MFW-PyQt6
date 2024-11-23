from PyQt6.QtCore import QObject, pyqtSignal

from maa.toolkit import AdbDevice


class SignalBus(QObject):
    """pyqtSignal bus"""

    switchToSampleCard = pyqtSignal(str, int)
    micaEnableChanged = pyqtSignal(bool)
    supportSignal = pyqtSignal()
    update_adb = pyqtSignal(AdbDevice)  # 更新设置界面adb设备信息信号
    callback = pyqtSignal(str)  # 回调协议信号
    update_task_list = pyqtSignal()  # 更新tasklist信息信号
    Notice_msg = pyqtSignal(str)  # 通知消息
    update_available = pyqtSignal(dict)  # 检查更新
    update_finished = pyqtSignal()  # 更新完成信号
    cfg_changed = pyqtSignal()  # 配置文件修改信号
    adb_detect_backup = pyqtSignal(list)  # 备份adb检测


signalBus = SignalBus()
