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
    FluentIcon as FIF,
)
from ..core.core import TaskItem, ConfigItem, CoreSignalBus


class ClickableLabel(BodyLabel):
    clicked = Signal()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


# 列表项基类
class BaseListItem(QWidget):
    item_selected = Signal(str)

    def __init__(self, item_id: str, signal_bus: CoreSignalBus, parent=None):
        super().__init__(parent)
        self.item_id = item_id
        self.signal_bus = signal_bus
        self._init_ui()
        self.connect_signals()

    def _init_ui(self):
        # 基础UI布局设置
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)

        # 创建标签（子类可以重写或扩展）
        self.name_label = self._create_name_label()
        layout.addWidget(self.name_label)

        # 创建设置按钮（子类可以重写或扩展）
        self.setting_button = self._create_setting_button()
        layout.addWidget(self.setting_button)

    def _create_name_label(self):
        # 子类可以重写此方法来自定义标签
        label = ClickableLabel("Item")
        label.setFixedHeight(34)
        label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        return label

    def _create_setting_button(self):
        # 子类可以重写此方法来自定义设置按钮
        button = TransparentToolButton(FIF.SETTING)
        button.setFixedSize(34, 34)
        return button

    def connect_signals(self):
        # 基础信号连接
        self.name_label.clicked.connect(self.on_select_item)

    def on_select_item(self):
        # 选择项的通用逻辑
        self.item_selected.emit(self.item_id)
        self._select_in_parent_list()

        self._emit_signal_to_bus()

    def _select_in_parent_list(self):
        # 在父列表中选择当前项的逻辑
        parent = self.parent()
        while parent is not None:
            if hasattr(parent, "findItems"):
                for i in range(parent.count()):  # type: ignore
                    list_item = parent.item(i)  # type: ignore
                    widget = parent.itemWidget(list_item)  # type: ignore
                    if widget == self:
                        parent.setCurrentItem(list_item)  # type: ignore
                        break
                break
            parent = parent.parent()

    def _emit_signal_to_bus(self):
        # 子类需要重写此方法以发送特定信号
        # 默认不直接向 signal_bus 发出选中信号，选中行为应由包含该 item 的列表组件集中处理
        return


# 任务列表项组件
class TaskListItem(BaseListItem):
    def __init__(self, task: TaskItem, signal_bus: CoreSignalBus, parent=None):
        self.task = task
        super().__init__(task.item_id, signal_bus, parent)
        # 通过 item_id 前缀判断是否为基础任务，禁用复选框
        if self.task.item_id.startswith(("c_", "r_", "f_")):
            self.checkbox.setChecked(True)
            self.checkbox.setDisabled(True)

    def _init_ui(self):
        # 创建水平布局
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)

        # 复选框 - 任务项特有的UI元素
        self.checkbox = CheckBox()
        self.checkbox.setFixedSize(34, 34)
        self.checkbox.setChecked(self.task.is_checked)
        layout.addWidget(self.checkbox)

        # 添加标签和设置按钮
        self.name_label = self._create_name_label()
        layout.addWidget(self.name_label)

        self.setting_button = self._create_setting_button()
        layout.addWidget(self.setting_button)

    def _create_name_label(self):
        # 重写创建标签的方法，使用任务名称
        label = ClickableLabel(self.task.name)
        label.setFixedHeight(34)
        label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        return label

    def connect_signals(self):
        # 调用基类的信号连接
        super().connect_signals()
        # 连接任务特有的信号
        self.checkbox.stateChanged.connect(self.on_checkbox_changed)
        self.setting_button.clicked.connect(self.on_open_task_settings)

    # 已无 task_type 字段，无需特殊处理

    def _emit_signal_to_bus(self):
        # 由父级列表统一处理选中并调用 ServiceCoordinator.select_task
        return

    def on_open_task_settings(self):
        # 打开任务设置的逻辑
        pass

    def on_checkbox_changed(self, state):
        # 复选框状态变更处理
        is_checked = state == Qt.CheckState.Checked
        self.task.is_checked = is_checked


# 配置列表项组件
class ConfigListItem(BaseListItem):
    def __init__(self, config: ConfigItem, signal_bus: CoreSignalBus, parent=None):
        self.config = config
        super().__init__(config.item_id, signal_bus, parent)

    def _create_name_label(self):
        # 重写创建标签的方法，使用配置名称
        label = ClickableLabel(self.config.name)
        label.setFixedHeight(34)
        label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        return label

    def _emit_signal_to_bus(self):
        # 由父级列表统一处理选中并调用 ServiceCoordinator.select_config
        return
