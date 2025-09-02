from PySide6.QtCore import Signal, QObject


class CoreSignalBus(QObject):

    change_task_flow = Signal(dict) # 切换任务列表
    show_option = Signal(dict) # 显示选项
    need_save = Signal() # 配置文件需要保存




core_signalBus = CoreSignalBus()
