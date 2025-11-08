from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QSizePolicy,
)

from PySide6.QtCore import Signal, Qt

from qfluentwidgets import (
    CheckBox,
    TransparentToolButton,
    BodyLabel,
    ListWidget,
    FluentIcon as FIF,
)
from ....core.core import TaskItem, ConfigItem, CoreSignalBus


class ClickableLabel(BodyLabel):
    clicked = Signal()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


# 列表项基类
class BaseListItem(QWidget):

    def __init__(self, item: ConfigItem | TaskItem, parent=None):
        super().__init__(parent)
        self.item = item

        self._init_ui()

    def _init_ui(self):
        # 基础UI布局设置
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)

        # 创建标签（子类可以重写或扩展）
        self.name_label = self._create_name_label()
        layout.addWidget(self.name_label)

        # 创建设置按钮（子类可以重写或扩展）
        self.setting_button = self._create_setting_button()
        self.setting_button.clicked.connect(self._select_in_parent_list)
        layout.addWidget(self.setting_button)

    def _create_name_label(self):
        # 子类可以重写此方法来自定义标签
        label = ClickableLabel(self.item.name)
        label.setFixedHeight(34)
        label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        return label
    
    def _get_display_name(self):
        """获取显示名称（优先使用 label，否则使用 name）
        
        仅在 TaskListItem 中重写，用于从 interface 获取 label
        """
        return self.item.name

    def _create_setting_button(self):
        # 子类可以重写此方法来自定义设置按钮
        button = TransparentToolButton(FIF.SETTING)
        button.setFixedSize(34, 34)
        return button

    def _select_in_parent_list(self):
        # 在父列表中选择当前项的逻辑
        parent = self.parent()
        while parent is not None:
            if isinstance(parent, ListWidget):
                for i in range(parent.count()):
                    list_item = parent.item(i)
                    widget = parent.itemWidget(list_item)
                    if widget == self:
                        parent.setCurrentItem(list_item)
                        break
                break
            parent = parent.parent()


# 任务列表项组件
class TaskListItem(BaseListItem):
    checkbox_changed = Signal(object)  # 发射 TaskItem 对象

    def __init__(self, task: TaskItem, interface: dict | None = None, parent=None):
        self.task = task
        self.interface = interface or {}
        super().__init__(task, parent)
        
        # 通过 item_id 前缀判断是否为基础任务，禁用复选框
        if self.task.item_id.startswith(("c_", "r_", "f_")):
            self.checkbox.setChecked(True)
            self.checkbox.setDisabled(True)

        self.checkbox.stateChanged.connect(self.on_checkbox_changed)

    def _init_ui(self):
        # 创建水平布局
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)

        # 复选框 - 任务项特有的UI元素
        self.checkbox = CheckBox()
        self.checkbox.setFixedSize(34, 34)
        self.checkbox.setChecked(self.task.is_checked)
        self.checkbox.setTristate(False)
        layout.addWidget(self.checkbox)

        # 添加标签
        self.name_label = self._create_name_label()
        layout.addWidget(self.name_label)

        # 添加设置按钮
        self.setting_button = self._create_setting_button()
        self.setting_button.clicked.connect(self._select_in_parent_list)
        layout.addWidget(self.setting_button)

    def _get_display_name(self):
        """获取显示名称（从 interface 获取 label，否则使用 name）
        
        注意：保留 $ 前缀，它用于国际化标记
        """
        from app.utils.logger import logger
        
        if self.interface:
            for task in self.interface.get("task", []):
                if task["name"] == self.task.name:
                    display_label = task.get("label", task.get("name", self.task.name))
                    logger.info(f"任务显示: {self.task.name} -> {display_label}")
                    return display_label
        # 如果没有找到对应的 label，返回 name
        logger.warning(f"任务未找到 label，使用 name: {self.task.name} (interface={bool(self.interface)})")
        return self.task.name
    
    def _create_name_label(self):
        """创建名称标签（使用 label 而不是 name）"""
        label = ClickableLabel(self._get_display_name())
        label.setFixedHeight(34)
        label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        return label

    def on_checkbox_changed(self, state):
        # 复选框状态变更处理
        is_checked = state == 2
        self.task.is_checked = is_checked
        # 发射信号通知父组件更新
        self.checkbox_changed.emit(self.task)


# 配置列表项组件
class ConfigListItem(BaseListItem):
    def __init__(self, config: ConfigItem, parent=None):
        super().__init__(config, parent)
