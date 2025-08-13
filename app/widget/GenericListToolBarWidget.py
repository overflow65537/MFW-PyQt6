from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from qfluentwidgets import (
    SimpleCardWidget,
    ToolTipPosition,
    ToolTipFilter,
    BodyLabel,
    ListWidget,
    ToolButton,
    ScrollArea,
    FluentIcon as FIF,
)

from .DragListWidget import DragListWidget
from .TaskWidgetItem import TaskWidgetItem



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
        # 配置选择列表布局
        self.config_selection_widget = SimpleCardWidget()
        self.config_selection_widget.setClickEnabled(False)
        self.config_selection_widget.setBorderRadius(8)

        self.config_selection_layout = QVBoxLayout(self.config_selection_widget)
        self.config_selection_layout.addWidget(self.task_list)

    def select_all(self):
        """选择全部"""
        for i in range(self.task_list.main_layout.count()):
            item = self.task_list.main_layout.itemAt(i).widget()
            if isinstance(item, TaskWidgetItem):
                item.checkBox.setCheckState(Qt.CheckState.Checked)

    def deselect_all(self):
        """取消选择全部"""
        for i in range(self.task_list.main_layout.count()):
            item = self.task_list.main_layout.itemAt(i).widget()
            if isinstance(item, TaskWidgetItem):
                item.checkBox.setCheckState(Qt.CheckState.Unchecked)
