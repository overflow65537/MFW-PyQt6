from PySide6.QtCore import QObject, Signal



class CoreSignalBus(QObject):

    change_task_flow = Signal()  # 切换任务列表
    show_option = Signal(dict)  # 显示选项
    need_save = Signal()  # 配置文件需要保存
    task_update = Signal(list)  # 任务列表更新

    callback = Signal()  # maafw回调信号


core_signalBus = CoreSignalBus()
