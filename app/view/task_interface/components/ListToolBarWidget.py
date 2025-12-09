from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
)


from qfluentwidgets import (
    SimpleCardWidget,
    ToolTipPosition,
    ToolTipFilter,
    BodyLabel,
    ListWidget,
    ToolButton,
    FluentIcon as FIF,
)


from app.view.task_interface.components.ListWidget import TaskDragListWidget, ConfigListWidget
from app.view.task_interface.components.AddTaskMessageBox import AddConfigDialog, AddTaskDialog
from app.core.core import ServiceCoordinator
from app.view.task_interface.components.ListItem import TaskListItem, ConfigListItem
from app.common.signal_bus import signalBus


class BaseListToolBarWidget(QWidget):

    def __init__(self, service_coordinator: ServiceCoordinator, parent=None):
        super().__init__(parent)
        self.service_coordinator = service_coordinator

        self._init_title()
        self._init_selection()

        self.title_layout.setContentsMargins(0, 0, 2, 0)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.addLayout(self.title_layout)
        self.main_layout.addWidget(self.selection_widget)

    def _init_title(self):
        """初始化标题栏"""
        # 标题
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

        # 删除
        self.delete_button = ToolButton(FIF.DELETE)
        self.delete_button.installEventFilter(
            ToolTipFilter(self.delete_button, 0, ToolTipPosition.TOP)
        )
        self.delete_button.setToolTip(self.tr("Delete"))

        # 布局
        self.title_layout = QHBoxLayout()
        # 设置边距
        self.title_layout.addWidget(self.selection_title)
        self.title_layout.addWidget(self.select_all_button)
        self.title_layout.addWidget(self.deselect_all_button)
        self.title_layout.addWidget(self.delete_button)
        self.title_layout.addWidget(self.add_button)

    def _init_task_list(self):
        """初始化任务列表"""
        self.task_list = ListWidget(parent=self)

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
    def __init__(self, service_coordinator: ServiceCoordinator, parent=None):
        super().__init__(service_coordinator=service_coordinator, parent=parent)

        self.service_coordinator = service_coordinator

        self.select_all_button.hide()
        self.deselect_all_button.hide()

        self.add_button.clicked.connect(self.add_config)
        self.delete_button.clicked.connect(self.remove_config)

        # 设置配置列表标题
        self.set_title(self.tr("Configurations"))

    def _init_task_list(self):
        """初始化配置列表"""
        self.task_list = ConfigListWidget(
            service_coordinator=self.service_coordinator, parent=self
        )

    def add_config(self):
        """添加配置项。"""
        # 通过对话框创建新配置
        bundles = []
        main_cfg = getattr(self.service_coordinator.config, "_main_config", None)
        if main_cfg:
            bundle_source = main_cfg.get("bundle", [])
            if isinstance(bundle_source, dict):
                for name, value in bundle_source.items():
                    bundle_info = {"name": name}
                    if isinstance(value, dict):
                        bundle_info["path"] = value.get("path", "")
                    else:
                        bundle_info["path"] = str(value)
                    bundles.append(bundle_info)
            elif isinstance(bundle_source, list):
                bundles = bundle_source

        dlg = AddConfigDialog(resource_bundles=bundles, parent=self.window(), interface=self.service_coordinator.interface)
        if dlg.exec():
            cfg = dlg.get_config_item()
            if cfg:
                self.service_coordinator.add_config(cfg)

    def remove_config(self):
        """移除配置项"""
        config_list = self.service_coordinator.config.list_configs()
        if len(config_list) <= 1:
            from app.common.signal_bus import signalBus

            signalBus.info_bar_requested.emit(
                "warning", self.tr("Cannot delete the last configuration!")
            )
            signalBus.info_bar_requested.emit(
                "warning", self.tr("Cannot delete the last configuration!")
            )
            return False
        cur = self.task_list.currentItem()
        if not cur:
            return
        widget = self.task_list.itemWidget(cur)
        if not widget:
            return
        if isinstance(widget, ConfigListItem):
            cfg_id = widget.item.item_id
        else:
            cfg_id = None
        if not cfg_id:
            return
        # 调用服务删除即可,视图通过信号刷新
        self.service_coordinator.delete_config(cfg_id)


class TaskListToolBarWidget(BaseListToolBarWidget):

    def __init__(
        self,
        service_coordinator: ServiceCoordinator,
        parent=None,
        task_filter_mode: str = "all",
    ):
        self._task_filter_mode = (
            task_filter_mode if task_filter_mode in ("all", "normal", "special") else "all"
        )
        super().__init__(service_coordinator=service_coordinator, parent=parent)
        self.core_signalBus = self.service_coordinator.signal_bus
        if self._task_filter_mode == "special":
            self._apply_special_mode_ui()
        # 选择全部按钮
        self.select_all_button.clicked.connect(self.select_all)
        # 取消选择全部按钮
        self.deselect_all_button.clicked.connect(self.deselect_all)
        # 添加按钮
        self.add_button.clicked.connect(self.add_task)
        # 删除按钮
        self.delete_button.clicked.connect(self.remove_selected_task)

        # 设置任务列表标题
        self.set_title(self.tr("Tasks"))

        # 初始填充任务列表
        # 不在工具栏直接刷新列表：视图会订阅 ServiceCoordinator 的信号自行更新

    def _init_task_list(self):
        """初始化任务列表"""
        self.task_list = TaskDragListWidget(
            service_coordinator=self.service_coordinator,
            parent=self,
            filter_mode=self._task_filter_mode,
        )

    def select_all(self):
        """选择全部"""
        self.task_list.select_all()

    def deselect_all(self):
        """取消选择全部"""
        self.task_list.deselect_all()

    def add_task(self):
        """添加任务"""
        # 打开添加任务对话框
        task_map = getattr(self.service_coordinator.task, "default_option", {})
        interface = getattr(self.service_coordinator.task, "interface", {})
        filtered_task_map = self._filter_task_map_by_mode(task_map, interface)
        if not filtered_task_map:
            signalBus.info_bar_requested.emit(
                "warning", self.tr("No available tasks to add.")
            )
            return
        dlg = AddTaskDialog(
            task_map=filtered_task_map, interface=interface, parent=self.window()
        )
        if dlg.exec():
            new_task = dlg.get_task_item()
            if new_task:
                # 持久化到服务层
                self.service_coordinator.modify_task(new_task)

    def _filter_task_map_by_mode(
        self, task_map: dict[str, dict], interface: dict | None
    ) -> dict[str, dict]:
        """根据当前任务过滤模式筛选可添加的任务."""
        if not isinstance(task_map, dict):
            return {}

        interface = interface or {}
        task_special_map: dict[str, bool] = {}
        for task_def in interface.get("task", []):
            name = task_def.get("name")
            if name:
                task_special_map[name] = task_def.get("spt", False)

        def _include(task_name: str) -> bool:
            is_special = task_special_map.get(task_name, False)
            if self._task_filter_mode == "special":
                return is_special
            if self._task_filter_mode == "normal":
                return not is_special
            return True

        return {name: opts for name, opts in task_map.items() if _include(name)}

    def _apply_special_mode_ui(self):
        """特殊任务界面隐藏批量与增删按钮"""
        for btn in (
            self.select_all_button,
            self.deselect_all_button,
            self.add_button,
            self.delete_button,
        ):
            btn.hide()

    def remove_selected_task(self):
        cur = self.task_list.currentItem()
        if not cur:
            return
        widget = self.task_list.itemWidget(cur)
        if not widget or not isinstance(widget, TaskListItem):
            return
        task_id = getattr(widget.task, "item_id", None)
        if not task_id:
            return
        elif widget.task.is_base_task():
            from app.common.signal_bus import signalBus

            signalBus.info_bar_requested.emit(
                "warning",
                self.tr(
                    "Base tasks (Resource, Post-Task) cannot be deleted (ID: {id})"
                ).format(id=task_id),
            )
            return False
        # 删除通过服务层执行，视图会通过fs系列信号刷新
        self.service_coordinator.delete_task(task_id)
