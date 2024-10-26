from PyQt6.QtCore import QObject, pyqtSignal


class SignalBus(QObject):
    """pyqtSignal bus"""

    switchToSampleCard = pyqtSignal(str, int)
    micaEnableChanged = pyqtSignal(bool)
    supportSignal = pyqtSignal()
    adb_detected = pyqtSignal(list)  # 自动查找发送adb设备信息信号
    update_adb = pyqtSignal(dict)  # 设置界面接收adb设备信息更新界面信号
    callback = pyqtSignal(str)  # 回调协议信号
    update_signal = pyqtSignal()  # 更新组件信息信号


signalBus = SignalBus()
