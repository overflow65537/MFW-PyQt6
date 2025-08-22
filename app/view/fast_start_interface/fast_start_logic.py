from PySide6.QtWidgets import (
    QWidget,
    QTableWidgetItem,
    QListWidgetItem,
    QHBoxLayout,
    QSizePolicy,
)
from qfluentwidgets import CheckBox, TransparentToolButton, FluentIcon as FIF


from ..fast_start_interface.fast_start_ui import UI_FastStartInterface
from ...common.resource_config import res_cfg
from ...common.signal_bus import signalBus
from ...utils.logger import logger




class FastStartInterface(UI_FastStartInterface, QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setupUi(self)

        self._init_task_info()

    def _init_task_info(self):
        """填充信息至组件"""
        #填充控制器和资源设置
        controller_setting = {

            "name": "控制器",
            "type": "controller",
            
        }
        resource_setting = {
            "name": "资源",
            "type": "resource",

            
        }
        self.task_info.add_item(controller_setting,False)
        self.task_info.add_item(resource_setting,False)
        for task_config in res_cfg.config.get("task",[]):
            self.task_info.add_item(task_config)

