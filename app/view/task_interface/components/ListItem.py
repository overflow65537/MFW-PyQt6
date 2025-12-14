import asyncio

from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QSizePolicy,
)

from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QPalette, QGuiApplication

from qfluentwidgets import (
    CheckBox,
    TransparentToolButton,
    BodyLabel,
    ListWidget,
    FluentIcon as FIF,
    isDarkTheme,
    qconfig,
    RoundMenu,
    Action,
)
from app.core.Item import TaskItem, ConfigItem
from app.common.constants import PRE_CONFIGURATION, POST_ACTION
from app.core.core import ServiceCoordinator


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
        # 默认允许的状态（某些子类可能在后续重设）
        self._interface_allowed: bool = True

        self._init_ui()
        self._apply_theme_colors()
        qconfig.themeChanged.connect(self._apply_theme_colors)

    def _resolve_text_color(self) -> str:
        """根据当前主题返回可读的文本颜色"""
        color = self.palette().color(QPalette.ColorRole.WindowText)
        if not isDarkTheme() and color.lightness() > 220:
            return "#202020"
        return color.name()

    def _apply_theme_colors(self, *_):
        """应用主题颜色到名称标签"""
        if hasattr(self, "_interface_allowed") and self._interface_allowed is False:
            return  # 禁用状态保持红色提示
        if hasattr(self, "name_label"):
            self.name_label.setStyleSheet(f"color: {self._resolve_text_color()};")

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

    def __init__(
        self,
        task: TaskItem,
        interface: dict | None = None,
        service_coordinator: ServiceCoordinator | None = None,
        parent=None,
    ):
        self.task = task
        self.interface = interface or {}
        self.service_coordinator = service_coordinator
        super().__init__(task, parent)

        self._apply_interface_constraints()

        # 基础任务（资源、完成后操作）的复选框始终勾选且禁用
        if self.task.is_base_task():
            self.checkbox.setChecked(True)
            self.checkbox.setDisabled(True)

        self.checkbox.stateChanged.connect(self.on_checkbox_changed)

    def _apply_interface_constraints(self):
        """根据 interface 中的 task 列表决定是否允许此任务勾选/显示为禁用状态。"""
        interface_task_defs = self.interface.get("task")
        self._interface_allowed = True
        if (
            isinstance(interface_task_defs, list)
            and not self.task.is_base_task()
        ):
            allowed_names = [
                task_def.get("name")
                for task_def in interface_task_defs
                if isinstance(task_def, dict) and task_def.get("name")
            ]
            self._interface_allowed = self.task.name in allowed_names
        if not self._interface_allowed:
            self.checkbox.setChecked(False)
            self.checkbox.setDisabled(True)
            self.name_label.setStyleSheet("color: #d32f2f;")
        else:
            # 只有非基础任务才需要解除禁用
            if not self.task.is_base_task():
                self.checkbox.setDisabled(False)
            self._apply_theme_colors()

    @property
    def interface_allows(self) -> bool:
        return self._interface_allowed

    def update_interface(self, interface: dict | None):
        """在接口数据变更时重新评估任务是否被允许显示。"""
        self.interface = interface or {}
        self._apply_interface_constraints()

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

        # 修改为
        if self.task.item_id == PRE_CONFIGURATION:
            return self.tr("Pre-Configuration")
        elif self.task.item_id == POST_ACTION:
            return self.tr("Post-Action")
        elif self.interface:
            for task in self.interface.get("task", []):
                if task["name"] == self.task.name:
                    display_label = task.get("label", task.get("name", self.task.name))
                    logger.info(f"任务显示: {self.task.name} -> {display_label}")
                    return display_label
        # 如果没有找到对应的 label，返回 name
        logger.warning(
            f"任务未找到 label，使用 name: {self.task.name} (interface={bool(self.interface)})"
        )
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

    def contextMenuEvent(self, event):
        """右键菜单：单独运行任务"""
        if not self.service_coordinator:
            return super().contextMenuEvent(event)

        menu = RoundMenu(parent=self)
        run_action = Action(FIF.PLAY, self.tr("Run this task"))
        run_action.triggered.connect(self._run_single_task)
        if self.task.is_base_task():
            run_action.setEnabled(False)
        menu.addAction(run_action)
        menu.popup(event.globalPos())
        event.accept()

    def _run_single_task(self):
        if not self.service_coordinator:
            return
        asyncio.create_task(self.service_coordinator.run_tasks_flow(self.task.item_id))


# 特殊任务列表项组件
class SpecialTaskListItem(TaskListItem):
    """特殊任务列表项：隐藏checkbox，点击整个item相当于点击checkbox，并切换到任务设置"""

    def __init__(
        self,
        task: TaskItem,
        interface: dict | None = None,
        service_coordinator: ServiceCoordinator | None = None,
        parent=None,
    ):
        # 先调用父类初始化，创建checkbox等UI元素
        super().__init__(task, interface, service_coordinator, parent)
        
        # 隐藏checkbox
        self.checkbox.hide()
        
        # 将整个item的点击事件绑定到checkbox逻辑
        # 点击name_label时触发选择
        self.name_label.clicked.connect(self._on_item_clicked)
        
        # 设置整个widget可点击
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def _on_item_clicked(self):
        """处理item点击事件：相当于点击checkbox，并切换到任务设置"""
        if not self._interface_allowed or self.task.is_base_task():
            return
        
        # 如果当前未选中，则选中（相当于点击checkbox）
        # 这会触发checkbox状态改变，发射checkbox_changed信号，进而触发单选逻辑
        if not self.task.is_checked:
            # 触发checkbox状态改变，这会发射checkbox_changed信号
            # 单选逻辑会在_on_task_checkbox_changed中处理
            self.checkbox.setChecked(True)
        
        # 无论是否已选中，都切换到对应的任务设置（触发任务选择）
        if self.service_coordinator:
            self.service_coordinator.select_task(self.task.item_id)
        
        # 在父列表中选择当前项
        self._select_in_parent_list()

    def mousePressEvent(self, event):
        """重写鼠标点击事件，使整个widget可点击"""
        if event.button() == Qt.MouseButton.LeftButton:
            # 如果点击的不是设置按钮，则触发item点击逻辑
            if not self.setting_button.geometry().contains(event.pos()):
                self._on_item_clicked()
        super().mousePressEvent(event)

    def contextMenuEvent(self, event):
        """重写右键菜单事件：特殊任务不显示右键菜单"""
        # 特殊任务不需要右键菜单，直接忽略事件
        event.ignore()


# 配置列表项组件
class ConfigListItem(BaseListItem):
    def __init__(self, config: ConfigItem, parent=None):
        super().__init__(config, parent)

    def contextMenuEvent(self, event):
        """右键菜单：复制配置 ID"""
        menu = RoundMenu(parent=self)
        copy_action = Action(FIF.COPY, self.tr("Copy config ID"))
        copy_action.triggered.connect(self._copy_config_id)
        menu.addAction(copy_action)
        menu.popup(event.globalPos())
        event.accept()

    def _copy_config_id(self):
        config_id = getattr(self.item, "item_id", "") or ""
        if not config_id:
            return
        QGuiApplication.clipboard().setText(str(config_id))
