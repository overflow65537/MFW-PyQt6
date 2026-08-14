from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
)


from qfluentwidgets import (
    SimpleCardWidget,
    BodyLabel,
    ListWidget,
    ToolButton,
    IconWidget,
    FluentIcon as FIF,
)

from app.common.fluent_tooltip import apply_fluent_tooltip

from app.view.task_interface.components.list_widget import (
    TaskDragListWidget,
    ConfigListWidget,
)
from app.view.task_interface.components.add_task_message_box import (
    AddConfigDialog,
    AddTaskDialog,
)
from app.core.core import ServiceCoordinator
from app.view.task_interface.components.panel_splitter import PANEL_SECTION_SPACING
from app.view.task_interface.components.list_item import TaskListItem, ConfigListItem
from app.common.signal_bus import signalBus
from app.common.config import cfg
from app.common.constants import _RESOURCE_, _CONTROLLER_, PRE_CONFIGURATION


class BaseListToolBarWidget(QWidget):

    def __init__(
        self,
        service_coordinator: ServiceCoordinator,
        parent=None,
        title_icon=None,
    ):
        super().__init__(parent)
        self.service_coordinator = service_coordinator
        self._title_icon = title_icon if title_icon is not None else FIF.FOLDER

        self._init_title()
        self._init_selection()

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(PANEL_SECTION_SPACING)
        self.main_layout.addWidget(self.title_bar)
        self.main_layout.addWidget(self.selection_widget)

    def _init_title(self):
        """初始化标题栏"""
        # 标题（图标 + 文案）
        self.selection_title_icon = IconWidget(self._title_icon, self)
        self.selection_title_icon.setFixedSize(QSize(22, 22))
        self.selection_title = BodyLabel()
        self.selection_title.setStyleSheet("font-size: 20px;")
        self.selection_title.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.selection_title_row = QHBoxLayout()
        self.selection_title_row.setSpacing(8)
        self.selection_title_row.setContentsMargins(0, 0, 0, 0)
        self.selection_title_row.addWidget(self.selection_title_icon, 0, Qt.AlignmentFlag.AlignVCenter)
        self.selection_title_row.addWidget(self.selection_title, 1, Qt.AlignmentFlag.AlignVCenter)

        # 选择全部按钮
        self.select_all_button = ToolButton(FIF.CHECKBOX)
        apply_fluent_tooltip(self.select_all_button, self.tr("Select All"))

        # 取消选择全部
        self.deselect_all_button = ToolButton(FIF.CLEAR_SELECTION)
        apply_fluent_tooltip(self.deselect_all_button, self.tr("Deselect All"))

        # 添加
        self.add_button = ToolButton(FIF.ADD)
        apply_fluent_tooltip(self.add_button, self.tr("Add"))

        # 删除
        self.delete_button = ToolButton(FIF.DELETE)
        apply_fluent_tooltip(self.delete_button, self.tr("Delete"))

        self.title_bar = QWidget()
        self.title_bar.setFixedHeight(22)
        self.title_layout = QHBoxLayout(self.title_bar)
        self.title_layout.setContentsMargins(0, 0, 0, 0)
        self.title_layout.setSpacing(4)
        self.title_layout.addLayout(self.selection_title_row, 1)
        for button in (
            self.select_all_button,
            self.deselect_all_button,
            self.delete_button,
            self.add_button,
        ):
            button.setFixedSize(22, 22)
            self.title_layout.addWidget(button)

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
        super().__init__(
            service_coordinator=service_coordinator,
            parent=parent,
            title_icon=FIF.FOLDER,
        )

        self.service_coordinator = service_coordinator
        self._locked: bool = False
        self._runtime_running: bool = False

        self.select_all_button.hide()
        self.deselect_all_button.hide()

        self.add_button.clicked.connect(self.add_config)
        self.delete_button.clicked.connect(self.remove_config)

        # 设置配置列表标题
        self.set_title(self.tr("Configurations"))

        # 任务运行中锁定配置列表（禁止切换/增删）
        signalBus.start_button_status.connect(self._on_start_button_status_changed)
        cfg.multi_instance_enabled.valueChanged.connect(
            self._on_multi_instance_enabled_changed
        )
        self.service_coordinator.view_signals.runtime_state_changed.connect(
            self._on_runtime_state_changed
        )

    def _on_start_button_status_changed(self, status: dict):
        """Refresh the configuration lock when the active runtime changes."""
        self._runtime_running = status.get("text") == "STOP"
        self._refresh_runtime_lock()

    def _on_multi_instance_enabled_changed(self, _enabled):
        """Apply the setting immediately while a runtime is active."""
        self._refresh_runtime_lock()

    def _on_runtime_state_changed(self, _config_id: str, _state: str):
        """Refresh locking when a background configuration starts or stops."""
        self._refresh_runtime_lock()

    def _refresh_runtime_lock(self):
        """Lock configuration switching only when multi-instance is disabled."""
        running_config_ids = self.service_coordinator.get_running_config_ids()
        is_running = self._runtime_running or bool(running_config_ids)
        self.set_locked(is_running and not cfg.get(cfg.multi_instance_enabled))

    def set_locked(self, locked: bool):
        """锁定后禁止新增/删除配置，并通知列表组件拦截点击切换。"""
        locked = bool(locked)
        if self._locked == locked:
            return
        self._locked = locked

        self.add_button.setEnabled(not locked)
        self.delete_button.setEnabled(not locked)

        if (
            hasattr(self, "task_list")
            and self.task_list
            and hasattr(self.task_list, "set_locked")
        ):
            try:
                self.task_list.set_locked(locked)
            except Exception:
                pass

    def _init_task_list(self):
        """初始化配置列表"""
        self.task_list = ConfigListWidget(
            service_coordinator=self.service_coordinator, parent=self
        )

    def add_config(self):
        """添加配置项。"""
        if self._locked:
            signalBus.info_bar_requested.emit(
                "warning", self.tr("Task is running, configurations are locked.")
            )
            return
        # 通过对话框创建新配置
        bundles = []
        config_api = self.service_coordinator.configs
        try:
            # 通过配置 Facade 获取 bundle 列表，避免依赖内部结构
            bundle_names = config_api.list_bundles()
            for name in bundle_names:
                try:
                    info = config_api.get_bundle(name)
                except FileNotFoundError:
                    continue
                bundle_info = {
                    "name": str(info.get("name", name)),
                    "path": str(info.get("path", "")),
                }
                bundles.append(bundle_info)
        except Exception:
            bundles = []

        dlg = AddConfigDialog(
            resource_bundles=bundles,
            parent=self.window(),
            interface=self.service_coordinator.interface_api.data,
            service_coordinator=self.service_coordinator,
        )
        if dlg.exec():
            cfg = dlg.get_config_item()
            if cfg:
                preset_name = dlg.get_selected_preset_name()
                shared_tasks = dlg.get_shared_tasks()
                self.service_coordinator.add_config(
                    cfg, preset_name=preset_name, shared_tasks=shared_tasks
                )
                version_mismatch = dlg.get_share_version_mismatch()
                if version_mismatch is not None:
                    shared_ver, target_ver = version_mismatch
                    shared_label = shared_ver or self.tr("unknown")
                    target_label = target_ver or self.tr("unknown")
                    signalBus.info_bar_requested.emit(
                        "warning",
                        self.tr(
                            "Shared config version ({0}) differs from current "
                            "resource version ({1}); imported anyway."
                        ).format(shared_label, target_label),
                    )

    def remove_config(self):
        """移除配置项"""
        if self._locked:
            signalBus.info_bar_requested.emit(
                "warning", self.tr("Task is running, configurations are locked.")
            )
            return
        config_list = self.service_coordinator.configs.list_configs()
        if len(config_list) <= 1:
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
    ):
        super().__init__(
            service_coordinator=service_coordinator,
            parent=parent,
            title_icon=FIF.APPLICATION,
        )
        self.delete_button.hide()
        # 选择全部按钮
        self.select_all_button.clicked.connect(self.select_all)
        # 取消选择全部按钮
        self.deselect_all_button.clicked.connect(self.deselect_all)
        # 添加按钮（使用 lambda 确保 idx 参数使用默认值 -2）
        self.add_button.clicked.connect(lambda: self.add_task(-2))
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
        )

    def select_all(self):
        """选择全部"""
        self.task_list.select_all()

    def deselect_all(self):
        """取消选择全部"""
        self.task_list.deselect_all()

    def add_task(self, idx: int = -2):
        """添加任务

        Args:
            idx: 插入位置索引，默认为-2（倒数第二个位置）
        """
        # 打开添加任务对话框
        task_map = self.service_coordinator.tasks.default_option
        interface = self.service_coordinator.tasks.interface
        filtered_task_map = self._filter_task_map(task_map, interface)
        if not filtered_task_map:
            signalBus.info_bar_requested.emit(
                "warning", self.tr("No available tasks to add.")
            )
            return
        dlg = AddTaskDialog(
            task_map=filtered_task_map,
            interface=interface,
            interface_path=self.service_coordinator.interface_api.path,
            parent=self.window(),
        )
        if dlg.exec():
            new_tasks = dlg.get_task_items()
            for i, new_task in enumerate(new_tasks):
                insert_idx = idx + i if idx >= 0 else idx
                self.service_coordinator.modify_task(new_task, insert_idx)

    def _filter_task_map(
        self, task_map: dict[str, dict], interface: dict | None
    ) -> dict[str, dict]:
        """按资源/控制器能力筛选可添加的任务。"""
        if not isinstance(task_map, dict):
            return {}

        interface = interface or {}

        # 获取当前配置中的资源/控制器类型
        current_resource_name = ""
        current_controller_type = ""
        try:
            # 新版本：资源选项位于固定基础任务 `Resource`
            resource_task = self.service_coordinator.tasks.get_task(_RESOURCE_)
            if resource_task and isinstance(resource_task.task_option, dict):
                current_resource_name = resource_task.task_option.get("resource", "")
            # 向后兼容：旧版本可能把 resource 放在 `Pre-Configuration`
            if not current_resource_name:
                pre_config_task = self.service_coordinator.tasks.get_task(
                    PRE_CONFIGURATION
                )
                if pre_config_task and isinstance(pre_config_task.task_option, dict):
                    current_resource_name = pre_config_task.task_option.get(
                        "resource", ""
                    )

            # 控制器类型优先从固定基础任务 `Controller` 读取
            controller_task = self.service_coordinator.tasks.get_task(_CONTROLLER_)
            if controller_task and isinstance(controller_task.task_option, dict):
                current_controller_type = controller_task.task_option.get(
                    "controller_type", ""
                )
            # 向后兼容：旧版本可能把 controller_type 放在 `Pre-Configuration`
            if not current_controller_type:
                pre_config_task = self.service_coordinator.tasks.get_task(
                    PRE_CONFIGURATION
                )
                if pre_config_task and isinstance(pre_config_task.task_option, dict):
                    current_controller_type = pre_config_task.task_option.get(
                        "controller_type", ""
                    )
        except Exception:
            pass

        def _include(task_name: str) -> bool:
            # 根据资源过滤任务
            if current_resource_name or current_controller_type:
                for task_def in interface.get("task", []):
                    if task_def.get("name") != task_name:
                        continue

                    # --- controller 过滤（空=全显示） ---
                    if current_controller_type:
                        controllers = task_def.get("controller", None)
                        if controllers not in (None, "", [], {}):
                            allowed_ctrl: list[str] = []
                            if isinstance(controllers, str):
                                if controllers.strip():
                                    allowed_ctrl = [controllers.strip()]
                            elif isinstance(controllers, list):
                                allowed_ctrl = [
                                    str(x).strip()
                                    for x in controllers
                                    if x is not None and str(x).strip()
                                ]
                            # 非支持格式：默认全显示
                            if allowed_ctrl:
                                if (
                                    str(current_controller_type).strip().lower()
                                    not in {s.lower() for s in allowed_ctrl}
                                ):
                                    return False

                    # --- resource 过滤（空=全显示） ---
                    if current_resource_name:
                        task_resources = task_def.get("resource", [])
                        # 如果任务没有 resource 字段，或者 resource 为空列表，表示所有资源都可用
                        if not task_resources:
                            return True
                        # 如果任务的 resource 列表包含当前资源，则显示
                        if current_resource_name in task_resources:
                            return True
                        return False

            return True

        return {name: opts for name, opts in task_map.items() if _include(name)}

    def remove_selected_task(self):
        cur = self.task_list.currentItem()
        if not cur:
            return
        widget = self.task_list.itemWidget(cur)
        if not widget or not isinstance(widget, TaskListItem):
            return
        task_id = widget.task.item_id if widget.task else None
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

