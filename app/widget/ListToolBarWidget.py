from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QAbstractItemView,
)
from PySide6.QtGui import QIcon


from qfluentwidgets import (
    SimpleCardWidget,
    ToolTipPosition,
    ToolTipFilter,
    BodyLabel,
    ListWidget,
    ToolButton,
    ScrollArea,
    ComboBox,
    EditableComboBox,
    LineEdit,
    SwitchButton,
    
    
    FluentIcon as FIF,
)


from .DragListWidget import TaskDragListWidget, ConfigDragListWidget
from .AddTaskMessageBox import AddConfigDialog, AddTaskDialog
from ..core.CoreSignalBus import core_signalBus, CoreSignalBus
from ..core.ItemManager import TaskItem, ConfigItem, TaskManager, ConfigManager


class BaseListToolBarWidget(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self._init_title()
        self._init_selection()

        self.title_layout.setContentsMargins(0, 0, 2, 0)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.addLayout(self.title_layout)
        self.main_layout.addWidget(self.selection_widget)

    def _init_title(self):
        """初始化配置选择标题"""
        # 配置选择标题
        self.selection_title = BodyLabel()
        self.selection_title.setStyleSheet("font-size: 20px;")
        self.selection_title.setAlignment(Qt.AlignmentFlag.AlignLeft)

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
        self.title_layout.addWidget(self.selection_title)
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

    def _init_selection(self):
        """初始化配置选择"""
        self._init_task_list()

        # 配置选择列表布局
        self.selection_widget = SimpleCardWidget()
        self.selection_widget.setClickEnabled(False)
        self.selection_widget.setBorderRadius(8)

        self.selection_layout = QVBoxLayout(self.selection_widget)
        self.selection_layout.addWidget(self.task_list)

    def set_title(self, title: str):
        """设置标题"""
        self.selection_title.setText(title)


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



class TaskListToolBarWidget(BaseListToolBarWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # 选择全部按钮
        self.select_all_button.clicked.connect(self.select_all)
        # 取消选择全部按钮
        self.deselect_all_button.clicked.connect(self.deselect_all)
        # 添加按钮
        self.add_button.clicked.connect(self.add_task)
        core_signalBus.show_option.connect(self._change_title)

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
        for task_dict in self.task_list.task_manager.interface["task"]:
            # 确保当前项是字典并且包含name键
            if isinstance(task_dict, dict) and "name" in task_dict:
                task_names.append(task_dict["name"])

        dialog = AddTaskDialog(task_names, parent=self.window())
        task_item = None
        if dialog.exec():
            task_item = dialog.get_task_item()
            if task_item is None:
                return
            self.task_list.add_task(task_item)

    def _change_title(self, item: TaskItem | ConfigItem):
        """改变标题"""
        if isinstance(item, ConfigItem):
            self.set_title(item.name)


class OptionWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        
    #传入外部对象
    def _init_obj(self, task_manager: TaskManager, core_signalBus: CoreSignalBus):
        self.task_manager = task_manager
        self.core_signalBus = core_signalBus
        core_signalBus.show_option.connect(self.show_option)
    
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
     
        self.option_area_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.option_area_card.setLayout(self.option_area_layout)

        self.main_layout.addLayout(self.title_layout)
        self.main_layout.addWidget(self.option_area_card)

        self.main_layout.setStretch(0, 1)
        self.main_layout.setStretch(1, 99)

    def set_title(self, title: str):
        """设置标题"""
        self.title_widget.setText(title)

    def show_option(self, item: TaskItem | ConfigItem):
        """显示选项"""
        if isinstance(item, TaskItem):
            self.set_title(item.name)
            print(f"显示选项: {item.name}")
            print(f"任务类型: {item.task_type}")

            if item.task_type == "task":
                self._show_task_option(item)
            elif item.task_type == "resource":
                self._show_resource_option(item)
            elif item.task_type == "controller":
                self._show_controller_option(item)


    def _show_task_option(self, item: TaskItem):
        """显示任务选项"""
        interfere=self.task_manager.interface
        target_task=None
        for task_template in interfere["task"]:
            if task_template["name"] == item.name:
                target_task=task_template
                break
        if target_task is None:
            print(f"未找到任务模板: {item.name}")
            return


        

    def _show_resource_option(self, item: TaskItem):
        """显示资源选项"""
        self._clear_options()

    def _show_controller_option(self, item: TaskItem):
        self._clear_options()
            
    def _add_combox_option(self, name: str, options: list[str], current: str, icon_path: str = "",
                          editable: bool = False, tooltip: str = "", option_tooltips: dict[str, str] | None = None):
        """添加下拉选项"""
        v_layout = QVBoxLayout()
        
        # 创建水平布局用于放置图标和标签
        h_layout = QHBoxLayout()
        h_layout.setContentsMargins(0, 0, 0, 0)  # 可选：设置边距
        h_layout.setSpacing(5)  # 可选：设置图标和文字之间的间距
        
        # 创建图标标签
        icon_label = BodyLabel()
        # 尝试加载PNG格式的图标
        icon = QIcon(icon_path)
        if not icon.isNull():
            # 如果图标存在，设置到标签上
            icon_label.setPixmap(icon.pixmap(16, 16))  # 设置图标大小
        
        # 创建文本标签
        text_label = BodyLabel(name)
        
        # 添加到水平布局
        h_layout.addWidget(icon_label)
        h_layout.addWidget(text_label)
        h_layout.addStretch(1)  # 可选：添加伸缩项使内容靠左对齐
        
        # 将水平布局添加到垂直布局
        v_layout.addLayout(h_layout)
 
        if editable:
            combo_box = EditableComboBox()
        else:
            combo_box = ComboBox()
        combo_box.setObjectName(name)
        v_layout.setObjectName(f"{name}_layout")
        combo_box.addItems(options)
        combo_box.setCurrentText(current)
        v_layout.addWidget(combo_box)
        
        # 设置标签的工具提示（第一种工具提示：任务介绍）
        if tooltip:
            text_label.setToolTip(tooltip)
            text_label.installEventFilter(ToolTipFilter(text_label, 0, ToolTipPosition.TOP))
        
        # 设置下拉框的初始工具提示和连接信号（第二种工具提示：选项介绍）
        if option_tooltips and isinstance(option_tooltips, dict):
            # 设置初始工具提示
            if current in option_tooltips:
                combo_box.setToolTip(option_tooltips[current])
            combo_box.installEventFilter(ToolTipFilter(combo_box, 0, ToolTipPosition.TOP))
            
            # 连接currentTextChanged信号，当选项改变时更新工具提示
            combo_box.currentTextChanged.connect(lambda text: 
                combo_box.setToolTip(option_tooltips.get(text, "")) if option_tooltips else None
            )
        elif tooltip:  # 如果没有提供选项级工具提示但有整体工具提示
            combo_box.setToolTip(tooltip)
            combo_box.installEventFilter(ToolTipFilter(combo_box, 0, ToolTipPosition.TOP))
        
        self.option_area_layout.addLayout(v_layout)

    def _add_lineedit_option(self, name: str, current: str, tooltip: str = "", obj_name: str = ""):
        """添加文本输入选项"""
        v_layout = QVBoxLayout()
        label = BodyLabel(name)
        line_edit = LineEdit()
        line_edit.setText(current)
        if obj_name:
            line_edit.setObjectName(obj_name)
            v_layout.setObjectName(f"{obj_name}_layout")
        v_layout.addWidget(label)
        v_layout.addWidget(line_edit)
        if tooltip:
            label.setToolTip(tooltip)
            label.installEventFilter(ToolTipFilter(label, 0, ToolTipPosition.TOP))
            line_edit.setToolTip(tooltip)
            line_edit.installEventFilter(
                ToolTipFilter(line_edit, 0, ToolTipPosition.TOP)
            )
        self.option_area_layout.addLayout(v_layout)

    def _add_switch_option(self, name: str, current: bool, tooltip: str = "", obj_name: str = ""):
        """添加开关选项"""
        v_layout = QVBoxLayout()
        label = BodyLabel(name)
        switch = SwitchButton()
        switch.setChecked(current)
        if obj_name:
            switch.setObjectName(obj_name)
            v_layout.setObjectName(f"{obj_name}_layout")
        v_layout.addWidget(label)
        v_layout.addWidget(switch)
        if tooltip:
            label.setToolTip(tooltip)
            label.installEventFilter(ToolTipFilter(label, 0, ToolTipPosition.TOP))
            switch.setToolTip(tooltip)
            switch.installEventFilter(
                ToolTipFilter(switch, 0, ToolTipPosition.TOP)
            )
        self.option_area_layout.addLayout(v_layout)

    def _clear_options(self):
        """清除所有选项"""
        """清除所有选项"""
        for i in reversed(range(self.option_area_layout.count())):
            widget = self.option_area_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()
            layout = self.option_area_layout.itemAt(i)
            if layout:
                layout.deleteLater()