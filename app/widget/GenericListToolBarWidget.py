from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QListWidgetItem,
    QListWidget,
    QAbstractItemView,
    QSizePolicy,
)


from qfluentwidgets import (
    SimpleCardWidget,
    ToolTipPosition,
    ToolTipFilter,
    BodyLabel,
    ListWidget,
    ToolButton,
    ScrollArea,
    FluentIcon as FIF,
    CheckBox,
    TransparentToolButton,
)
from typing import Dict

from app.common.typeddict import InterfaceData

from .TaskWidgetItem import TaskListItem

from .DragListWidget import DragListWidget
from .SimpleCardWidgetWithTitle import SimpleCardWidgetWithTitle

from ..common.resource_config import res_cfg


class GenericListToolBarWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_config_title()
        self._init_config_selection()

        self.title_layout.setContentsMargins(0, 0, 2, 0)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.addLayout(self.title_layout)
        self.main_layout.addWidget(self.config_selection_widget)

        # 选择全部按钮
        self.select_all_button.clicked.connect(self.select_all)
        # 取消选择全部按钮
        self.deselect_all_button.clicked.connect(self.deselect_all)

    def _init_config_title(self):
        """初始化配置选择标题"""
        # 配置选择标题
        self.config_selection_title = BodyLabel("配置选择")
        self.config_selection_title.setStyleSheet("font-size: 20px;")
        self.config_selection_title.setAlignment(Qt.AlignmentFlag.AlignLeft)

        # 选择全部按钮
        self.select_all_button = ToolButton(FIF.CHECKBOX)
        self.select_all_button.installEventFilter(
            ToolTipFilter(self.select_all_button, 0, ToolTipPosition.TOP)
        )
        self.select_all_button.setToolTip(self.tr("Select All"))

        # 取消选择全部
        self.deselect_all_button = ToolButton(FIF.CLEAR_SELECTION)
        self.deselect_all_button.installEventFilter(
            ToolTipFilter(self.deselect_all_button, 0, ToolTipPosition.TOP)
        )
        self.deselect_all_button.setToolTip(self.tr("Deselect All"))

        # 添加
        self.add_button = ToolButton(FIF.ADD)
        self.add_button.installEventFilter(
            ToolTipFilter(self.add_button, 0, ToolTipPosition.TOP)
        )
        self.add_button.setToolTip(self.tr("Add"))

        # 布局
        self.title_layout = QHBoxLayout()
        # 设置边距
        self.title_layout.addWidget(self.config_selection_title)
        self.title_layout.addWidget(self.select_all_button)
        self.title_layout.addWidget(self.deselect_all_button)
        self.title_layout.addWidget(self.add_button)

    def _init_config_selection(self):
        """初始化配置选择"""
        self.task_list = DragListWidget()
        self.task_list.setDragEnabled(True)
        self.task_list.setAcceptDrops(True)
        self.task_list.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.task_list.setDefaultDropAction(Qt.DropAction.MoveAction)
        # 配置选择列表布局
        self.config_selection_widget = SimpleCardWidget()
        self.config_selection_widget.setClickEnabled(False)
        self.config_selection_widget.setBorderRadius(8)

        self.config_selection_layout = QVBoxLayout(self.config_selection_widget)
        self.config_selection_layout.addWidget(self.task_list)

    def add_item(self, config, can_move=True):

        # 创建自定义widget
        item_widget = TaskListItem(config)
        if (
            not self.is_option_exist(res_cfg.interface_config, config.get("name", ""))
            and not self.is_speedrun_exist(
                res_cfg.interface_config, config.get("name", "")
            )
            and can_move
        ):
            item_widget.hiden_setting_button()



        # 创建列表项
        list_item = QListWidgetItem(self.task_list)
        if not can_move:
            list_item.setFlags(list_item.flags() & ~Qt.ItemFlag.ItemIsDragEnabled)
            item_widget.checkbox.setChecked(True)
            item_widget.checkbox.setDisabled(True)




        list_item.setSizeHint(item_widget.sizeHint())

        # 将widget与列表项关联
        self.task_list.addItem(list_item)
        self.task_list.setItemWidget(list_item, item_widget)

    def select_all(self):
        """选择全部"""
        self.task_list.select_all()

    def deselect_all(self):
        """取消选择全部"""
        self.task_list.deselect_all()

    def is_option_exist(self, config: InterfaceData, key: str) -> bool:
        """检查配置字典中是否存在指定的键。

        Args:
            config (InterfaceData): interface配置。
            key (str): 要检查的键。

        Returns:
            bool: 如果键存在，返回True；否则返回False。
        """
        target_task = None
        for task in config.get("task", []):
            if task.get("name") == key:
                target_task = task
                break
        if not target_task:
            return False
        elif target_task.get("option", []):
            return True
        else:
            return False

    def is_speedrun_exist(self, config: InterfaceData, key: str) -> bool:
        """检查配置字典中是否存在指定的键。

        Args:
            config (InterfaceData): interface配置。
            key (str): 要检查的键。

        Returns:
            bool: 如果键存在，返回True；否则返回False。
        """
        target_task = None
        for task in config.get("task", []):
            if task.get("name") == key:
                target_task = task
                break
        if not target_task:
            return False
        elif target_task.get("speedrun", []):
            return True
        else:
            return False
