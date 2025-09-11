from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QAbstractItemView,
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
)


from .DragListWidget import TaskDragListWidget, ConfigDragListWidget
from .AddTaskMessageBox import AddConfigDialog,AddTaskDialog


class BaseListToolBarWidget(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self._init_config_title()
        self._init_config_selection()

        self.title_layout.setContentsMargins(0, 0, 2, 0)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.addLayout(self.title_layout)
        self.main_layout.addWidget(self.config_selection_widget)

    def _init_config_title(self):
        """初始化配置选择标题"""
        # 配置选择标题
        self.config_selection_title = BodyLabel()
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

    def _init_task_list(self):
        """初始化任务列表"""
        self.task_list = ListWidget(parent=self)
        self.task_list.setDragEnabled(True)
        self.task_list.setAcceptDrops(True)
        self.task_list.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.task_list.setDefaultDropAction(Qt.DropAction.MoveAction)

    def _init_config_selection(self):
        """初始化配置选择"""
        self._init_task_list()

        # 配置选择列表布局
        self.config_selection_widget = SimpleCardWidget()
        self.config_selection_widget.setClickEnabled(False)
        self.config_selection_widget.setBorderRadius(8)

        self.config_selection_layout = QVBoxLayout(self.config_selection_widget)
        self.config_selection_layout.addWidget(self.task_list)

    def set_config_title(self, title: str):
        """设置标题"""
        self.config_selection_title.setText(title)


class TaskListToolBarWidget(BaseListToolBarWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # 选择全部按钮
        self.select_all_button.clicked.connect(self.select_all)
        # 取消选择全部按钮
        self.deselect_all_button.clicked.connect(self.deselect_all)
        # 添加按钮
        self.add_button.clicked.connect(self.add_task)

    def _init_task_list(self):
        """初始化任务列表"""
        self.task_list = TaskDragListWidget(parent=self)

    def select_all(self):
        """选择全部"""
        self.task_list.select_all()

    def deselect_all(self):
        """取消选择全部"""
        self.task_list.deselect_all()

    def add_task(self):
        """添加任务"""

        if self.task_list.task_manager is None:
            return

        task_names = []
        for task_dict in self.task_list.task_manager.interface['task']:
                # 确保当前项是字典并且包含name键
                if isinstance(task_dict, dict) and 'name' in task_dict:
                    task_names.append(task_dict['name'])

        dialog = AddTaskDialog(task_names,parent=self.window())
        task_item = None
        if dialog.exec():
            task_item = dialog.get_task_item()
            if task_item is None:
                return
            self.task_list.add_task(task_item)
            



class ConfigListToolBarWidget(BaseListToolBarWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # 选择全部按钮
        self.select_all_button.clicked.connect(self.select_all)
        # 取消选择全部按钮
        self.deselect_all_button.clicked.connect(self.deselect_all)
        # 添加按钮
        self.add_button.clicked.connect(self.add_config)

    def _init_task_list(self):
        """初始化配置列表"""
        self.task_list = ConfigDragListWidget(parent=self)

    def select_all(self):
        """选择全部"""
        self.task_list.select_all()

    def deselect_all(self):
        """取消选择全部"""
        self.task_list.deselect_all()

    def add_config(self):
        """添加配置项"""
        if self.task_list.config_manager is None:
            return
        bundle_list = self.task_list.config_manager.all_config.bundle
        dialog = AddConfigDialog(bundle_list, parent=self.window())
        config_item = None
        if dialog.exec():
            config_item = dialog.get_config_item()
            if config_item is None:
                return
            self.task_list.config_manager.add_config(config_item)
            self.task_list.add_config(config_item)


class OptionWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        """初始化UI"""
        self.main_layout = QVBoxLayout(self)

        self.title_widget = BodyLabel()
        self.title_widget.setStyleSheet("font-size: 20px;")
        self.title_widget.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self.title_layout = QHBoxLayout()
        self.title_layout.addWidget(self.title_widget)

        self.option_area_card = SimpleCardWidget()
        self.option_area_card.setClickEnabled(False)
        self.option_area_card.setBorderRadius(8)

        self.option_area_widget = ScrollArea()
        self.option_area_layout = QVBoxLayout(self.option_area_widget)
        self.option_area_card.setLayout(self.option_area_layout)

        self.main_layout.addLayout(self.title_layout)
        self.main_layout.addWidget(self.option_area_card)

    def set_title(self, title: str):
        """设置标题"""
        self.title_widget.setText(title)
