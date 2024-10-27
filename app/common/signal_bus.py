from PyQt6.QtCore import QObject, pyqtSignal


class SignalBus(QObject):
    """pyqtSignal bus"""

    switchToSampleCard = pyqtSignal(str, int)
    micaEnableChanged = pyqtSignal(bool)
    supportSignal = pyqtSignal()
    adb_detected = pyqtSignal(list)  # 自动查找发送adb设备信息信号
    update_adb = pyqtSignal(dict)  # 更新设置界面adb设备信息信号
    callback = pyqtSignal(str)  # 回调协议信号
    update_task_list = pyqtSignal(list)  # 更新tasklist信息信号


signalBus = SignalBus()
