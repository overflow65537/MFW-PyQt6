import asyncio
from pathlib import Path
from typing import Any

import shiboken6

from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QSizePolicy,
    QVBoxLayout,
    QFrame,
)

from PySide6.QtCore import Signal, Qt, QTimer
from PySide6.QtGui import QPalette, QGuiApplication, QPixmap, QColor

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
    MessageBoxBase,
    LineEdit,
    SubtitleLabel,
    MessageBox,
    IndeterminateProgressRing,
    ProgressRing,
    IconWidget,
)
from app.common.fluent_tooltip import apply_fluent_tooltip
from app.view.task_interface.components.marquee_label import OptionLabel
from app.core.item import TaskItem, ConfigItem
from app.common.constants import _RESOURCE_, _CONTROLLER_, POST_ACTION
from app.core.core import ServiceCoordinator
from app.core.utils.option_branches_compat import get_option_branches


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
        # 确保 BaseListItem 的高度不超过 item 高度（44px）
        self.setFixedHeight(44)

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
        # 调整高度，确保总高度不超过 item 高度（44px）
        label.setFixedHeight(40)  # BaseListItem 没有 option_label，所以可以更高
        label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        return label

    def _get_display_name(self):
        """获取显示名称（优先使用 label，否则使用 name）

        仅在 TaskListItem 中重写，用于从 interface 获取 label
        """
        return self.item.name

    def _create_setting_button(self):
        # 基类默认创建设置按钮，TaskListItem 会重写为删除按钮
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

    def _create_icon_label(
        self, icon_path: str, base_path: Path | None = None
    ) -> BodyLabel:
        """创建图标标签（通用方法，供子类复用）

        Args:
            icon_path: 图标路径（可能是相对路径或绝对路径）
            base_path: 如果 icon_path 是相对路径，相对于此路径。如果为 None，则相对于项目根目录

        Returns:
            BodyLabel 对象，已加载图标
        """
        icon_label = BodyLabel(self)
        icon_label.setFixedSize(24, 24)
        icon_label.setScaledContents(True)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 加载图标
        self._load_icon_to_label(icon_label, icon_path, base_path)

        return icon_label

    def _load_icon_to_label(
        self, icon_label: BodyLabel, icon_path: str, base_path: Path | None = None
    ):
        """将图标加载到标签中（通用方法，供子类复用）

        Args:
            icon_label: 要加载图标的标签
            icon_path: 图标路径（可能是相对路径或绝对路径）
            base_path: 如果 icon_path 是相对路径，相对于此路径。如果为 None，则相对于项目根目录
        """
        icon_file = Path(icon_path)

        # 处理相对路径
        if not icon_file.is_absolute():
            if base_path:
                icon_file = base_path / icon_path.lstrip("./")
            else:
                # 如果是相对路径，假设相对于项目根目录
                project_root = Path.cwd()
                icon_file = project_root / icon_path.lstrip("./")

        # 加载图标
        if icon_file.exists():
            pixmap = QPixmap(str(icon_file))
            if not pixmap.isNull():
                icon_label.setPixmap(
                    pixmap.scaled(
                        24,
                        24,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                )


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

        # 连接选项标签的resize事件，以便在大小改变时重新检查滚动
        if hasattr(self, "option_label"):
            self.option_label.installEventFilter(self)

    def _apply_interface_constraints(self):
        """根据 interface 中的 task 列表决定是否允许此任务勾选/显示为禁用状态。"""
        interface_task_defs = self.interface.get("task")
        self._interface_allowed = True
        if isinstance(interface_task_defs, list) and not self.task.is_base_task():
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

    def _apply_theme_colors(self, *_):
        """应用主题颜色到名称标签，同时保持选项标签的灰色小字体样式"""
        super()._apply_theme_colors()
        # 选项标签保持灰色小字体样式，不受主题变化影响
        if hasattr(self, "option_label"):
            self.option_label.setStyleSheet("color: gray; font-size: 11px;")
            # 确保字体大小有效
            self._ensure_font_valid(self.option_label)

    @property
    def interface_allows(self) -> bool:
        return self._interface_allowed

    def update_interface(self, interface: dict | None):
        """在接口数据变更时重新评估任务是否被允许显示，并更新图标。"""
        self.interface = interface or {}
        self._apply_interface_constraints()
        # 更新图标
        self._update_icon()

    def _init_ui(self):
        # 创建水平布局
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)
        # 确保 TaskListItem 的高度不超过 item 高度（44px）
        self.setFixedHeight(44)

        # 复选框 - 任务项特有的UI元素
        self.checkbox = CheckBox()
        self.checkbox.setFixedSize(34, 34)
        self.checkbox.setChecked(self.task.is_checked)
        self.checkbox.setTristate(False)
        layout.addWidget(self.checkbox)

        # 添加图标（如果有）
        icon_path = self._get_task_icon_path()
        if icon_path:
            self.icon_label = self._create_icon_label(icon_path)
            layout.addWidget(self.icon_label)
        else:
            self.icon_label = None

        # 创建垂直布局容器（名称和选项）
        name_option_container = QWidget()
        name_option_layout = QVBoxLayout(name_option_container)
        name_option_layout.setContentsMargins(0, 0, 0, 0)
        name_option_layout.setSpacing(2)

        # 添加标签
        self.name_label = self._create_name_label()
        name_option_layout.addWidget(self.name_label)

        # 添加选项显示标签
        self.option_label = self._create_option_label()
        name_option_layout.addWidget(self.option_label)
        # 在添加到布局后更新显示
        self._update_option_display()

        layout.addWidget(name_option_container, stretch=1)

        # 添加状态标志（在删除按钮之前）
        self.status_widget = self._create_status_widget()
        layout.addWidget(self.status_widget)
        
        # 添加删除按钮（基础任务不能删除，会禁用）
        self.setting_button = self._create_setting_button()
        self.setting_button.clicked.connect(self._on_delete_button_clicked)
        # 基础任务禁用删除按钮
        if self.task.is_base_task():
            self.setting_button.setDisabled(True)
        layout.addWidget(self.setting_button)

        # 连接选项标签的resize事件，以便在大小改变时重新检查滚动
        if hasattr(self, "option_label"):
            self.option_label.installEventFilter(self)

    def eventFilter(self, obj, event):
        """事件过滤器，用于监听选项标签的大小变化"""
        if obj == self.option_label and event.type() == event.Type.Resize:
            # 当选项标签大小改变时，重新计算是否需要滚动（不重置滚动位置）
            label = self.option_label
            QTimer.singleShot(
                50,
                lambda: label.refresh_scroll(reset_offset=False)
                if shiboken6.isValid(label)
                else None,
            )
        return super().eventFilter(obj, event)

    def _get_task_icon_path(self) -> str | None:
        """从 interface.task 中获取当前任务的图标路径

        Returns:
            图标路径字符串，如果不存在则返回 None
        """
        if not self.interface:
            return None

        interface_task_defs = self.interface.get("task", [])

        # 查找与当前任务同名的数据块
        for task_def in interface_task_defs:
            if task_def.get("name") == self.task.name:
                icon_path = task_def.get("icon")
                if icon_path and isinstance(icon_path, str):
                    return icon_path
        return None

    def _create_icon_label(
        self, icon_path: str, base_path: Path | None = None
    ) -> BodyLabel:
        """创建图标标签（调用基类方法）

        Args:
            icon_path: 图标路径（可能是相对路径或绝对路径）
            base_path: 如果 icon_path 是相对路径，相对于此路径。如果为 None，则相对于项目根目录

        Returns:
            BodyLabel 对象，已加载图标
        """
        # 使用基类方法，相对路径相对于项目根目录
        return super()._create_icon_label(icon_path, base_path=base_path)

    def _load_icon_to_label(
        self, icon_label: BodyLabel, icon_path: str, base_path: Path | None = None
    ):
        """将图标加载到标签中（调用基类方法）

        Args:
            icon_label: 要加载图标的标签
            icon_path: 图标路径（可能是相对路径或绝对路径）
            base_path: 如果 icon_path 是相对路径，相对于此路径。如果为 None，则相对于项目根目录
        """
        # 使用基类方法，相对路径相对于项目根目录
        super()._load_icon_to_label(icon_label, icon_path, base_path=base_path)

    def _update_icon(self):
        """更新图标显示"""
        icon_path = self._get_task_icon_path()
        layout = self.layout()

        if layout is None or not isinstance(layout, QHBoxLayout):
            return

        if icon_path:
            # 如果有图标路径
            if self.icon_label is None:
                # 如果还没有图标标签，创建并插入到 checkbox 和 name_label 之间
                self.icon_label = self._create_icon_label(icon_path)
                # 找到 checkbox 和 name_label 的位置
                checkbox_index = layout.indexOf(self.checkbox)
                layout.insertWidget(checkbox_index + 1, self.icon_label)
            else:
                # 如果已有图标标签，更新图标
                self._load_icon_to_label(self.icon_label, icon_path)
        else:
            # 如果没有图标路径，移除图标标签
            if self.icon_label is not None:
                layout.removeWidget(self.icon_label)
                self.icon_label.deleteLater()
                self.icon_label = None

    def _get_display_name(self):
        """获取显示名称（从 interface 获取 label，否则使用 name）

        注意：保留 $ 前缀，它用于国际化标记
        """
        from app.utils.logger import logger

        # 修改为
        if self.task.item_id == _RESOURCE_:
            return self.tr("Resource")
        elif self.task.item_id == _CONTROLLER_:
            return self.tr("Controller")
        elif self.task.item_id == POST_ACTION:
            return self.tr("Post-Action")
        elif self.interface:
            for task in self.interface.get("task", []):
                if task["name"] == self.task.name:
                    display_label = task.get("label", task.get("name", self.task.name))
                    logger.info(f"任务显示: {self.task.name} -> {display_label}")
                    return str(display_label)
        # 如果没有找到对应的 label，返回 name
        logger.warning(
            f"任务未找到 label，使用 name: {self.task.name} (interface={bool(self.interface)})"
        )
        return self.task.name

    def _create_name_label(self):
        """创建名称标签（使用 label 而不是 name）"""
        label = ClickableLabel(self._get_display_name())
        # 调整高度，确保总高度不超过 item 高度（44px）
        # item 高度 44px = name_label + spacing(2px) + option_label
        label.setFixedHeight(30)  # 从 34 调整为 30
        label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        return label

    def _ensure_font_valid(self, label: QWidget):
        """确保标签的字体大小有效，防止出现负数"""
        font = label.font()
        if font.pointSize() <= 0:
            font.setPointSize(11)
            label.setFont(font)
        # 如果使用像素大小，也确保有效
        if font.pixelSize() <= 0 and font.pointSize() <= 0:
            font.setPointSize(11)
            label.setFont(font)

    def _create_option_label(self):
        """创建选项显示标签（支持自动滚动，事件传递给父组件）"""
        label = OptionLabel("")
        # 调整高度，确保总高度不超过 item 高度（44px）
        # item 高度 44px = name_label(30px) + spacing(2px) + option_label(12px)
        label.setFixedHeight(12)  # 从 20 调整为 12
        label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        label.setWordWrap(False)  # 不换行
        # 设置样式，使文本更小更淡
        label.setStyleSheet("color: gray; font-size: 11px;")
        # 确保字体大小有效，防止出现负数
        self._ensure_font_valid(label)
        # 禁用文本选择，让所有事件（点击、拖动等）直接作用于父组件 ListItem
        label.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)

        # 跑马灯：慢速 + 两端停顿 1s + 往返滚动
        label.setMarqueeConfig(speed_px_per_sec=25.0, interval_ms=30, pause_ms=1000)

        self._option_full_text = ""
        apply_fluent_tooltip(label)

        return label

    def _resolve_option_display_label(
        self, option_def: dict | None, raw_value: Any
    ) -> str:
        """从 interface 选项定义中解析 case 的显示 label。"""
        if raw_value is None:
            return ""
        raw_str = str(raw_value)
        if not isinstance(option_def, dict):
            return raw_str

        for field in ("cases", "options"):
            entries = option_def.get(field, [])
            if not isinstance(entries, list):
                continue
            for entry in entries:
                if isinstance(entry, dict):
                    name = str(entry.get("name", ""))
                    label = str(entry.get("label", name))
                    if name == raw_str or label == raw_str:
                        return label
                elif str(entry) == raw_str:
                    return raw_str
        return raw_str

    def _build_child_interface_options(
        self, child_option_structure: Any
    ) -> dict | None:
        """从表单 children 结构构建子选项 interface 映射。"""
        if isinstance(child_option_structure, list) and child_option_structure:
            child_interface_options = {}
            for child_opt in child_option_structure:
                if isinstance(child_opt, dict) and "name" in child_opt:
                    child_interface_options[child_opt["name"]] = child_opt
            return child_interface_options or None
        return None

    def _collect_active_branch_payload(
        self, branches: dict, selected_cases: list[Any]
    ) -> dict:
        """合并 checkbox 已选中分支下的可见子选项。"""
        active_branches: dict = {}
        for selected_case in selected_cases:
            branch_group = branches.get(str(selected_case))
            if not isinstance(branch_group, dict):
                continue
            for child_key, child_value in branch_group.items():
                if isinstance(child_value, dict) and child_value.get("hidden"):
                    continue
                active_branches[child_key] = child_value
        return active_branches

    def _extract_option_values(
        self,
        task_option: dict,
        result: list | None = None,
        interface_options: dict | None = None,
    ) -> list:
        """递归提取任务选项中的当前选择的可见值

        Args:
            task_option: 任务选项字典
            result: 结果列表（递归使用）
            interface_options: interface 中的选项定义，用于获取选项的 label

        Returns:
            提取的值列表（只包含当前选择的选项值）
        """
        if result is None:
            result = []

        if not isinstance(task_option, dict):
            return result

        # 如果没有传入 interface_options，尝试从 self.interface 获取
        if interface_options is None and hasattr(self, "interface"):
            interface_options = self.interface.get("option", {})

        for key, value in task_option.items():
            # 跳过特殊键（如 _speedrun_config）
            if key.startswith("_"):
                continue

            # 如果 value 是字典
            if isinstance(value, dict):
                # 检查是否有 hidden 标志（在 value 同级）
                if value.get("hidden", False):
                    continue

                # 只提取当前选择的选项值（必须有 value 字段）
                option_value = value.get("value")
                if option_value is not None:
                    option_def = (
                        interface_options.get(key)
                        if interface_options and key in interface_options
                        else None
                    )

                    if isinstance(option_value, list):
                        labels = [
                            self._resolve_option_display_label(option_def, item)
                            for item in option_value
                        ]
                        labels = [
                            label.strip() for label in labels if label and label.strip()
                        ]
                        if labels:
                            result.append("、".join(labels))
                    elif isinstance(option_value, dict):
                        for sub_value in option_value.values():
                            if sub_value and str(sub_value).strip():
                                result.append(str(sub_value).strip())
                    else:
                        display_value = self._resolve_option_display_label(
                            option_def, option_value
                        )
                        if display_value and display_value.strip():
                            result.append(display_value.strip())

                # 递归处理 branches（兼容历史 children）
                branches = get_option_branches(value)
                if branches and option_value is not None:
                    child_interface_options = None
                    if (
                        interface_options
                        and key in interface_options
                        and not isinstance(option_value, list)
                    ):
                        option_def = interface_options[key]
                        children_def = option_def.get("children", {})
                        if (
                            isinstance(children_def, dict)
                            and option_value in children_def
                        ):
                            child_interface_options = self._build_child_interface_options(
                                children_def[option_value]
                            )

                    if isinstance(option_value, list):
                        active_branches = self._collect_active_branch_payload(
                            branches, option_value
                        )
                        if active_branches:
                            self._extract_option_values(
                                active_branches, result, interface_options
                            )
                    else:
                        self._extract_option_values(
                            branches, result, child_interface_options
                        )
            else:
                # 直接是值的情况（简单格式）- 这种情况表示当前选择的选项
                if value and str(value).strip():
                    result.append(str(value).strip())

        return result

    def _update_option_display(self):
        """更新选项显示"""
        # 尝试从 service_coordinator 获取最新的 task 对象，确保使用最新的 task_option
        if self.service_coordinator:
            try:
                latest_task = self.service_coordinator.task.get_task(self.task.item_id)
                if latest_task:
                    self.task = latest_task
            except Exception:
                # 如果获取失败，继续使用当前的 task 对象
                pass

        # 如果是基础任务，不显示选项
        if self.task.is_base_task():
            self._option_full_text = ""
            self.option_label.setText("")
            self.option_label.setToolTip("")
            return

        # 提取选项值（只显示当前选择的选项）
        interface_options = None
        if self.interface:
            interface_options = self.interface.get("option", {})
        option_values = self._extract_option_values(
            self.task.task_option, interface_options=interface_options
        )

        # 组合显示文本
        if option_values:
            display_text = " · ".join(option_values)
            self._option_full_text = display_text
            self.option_label.setToolTip(display_text)  # 设置工具提示以便查看完整内容
            # 交给 OptionLabel 自己判断是否需要滚动
            self.option_label.setText(display_text)
        else:
            self._option_full_text = ""
            self.option_label.setText("")
            self.option_label.setToolTip("")

    def on_checkbox_changed(self, state):
        # 复选框状态变更处理
        is_checked = state == 2
        self.task.is_checked = is_checked
        # 发射信号通知父组件更新
        self.checkbox_changed.emit(self.task)

    def contextMenuEvent(self, event):
        """右键菜单：单独运行任务、插入任务"""
        if not self.service_coordinator:
            return super().contextMenuEvent(event)

        menu = RoundMenu(parent=self)
        run_action = Action(FIF.PLAY, self.tr("Run this task"))
        run_action.triggered.connect(self._run_single_task)
        if self.task.is_base_task():
            run_action.setEnabled(False)
        menu.addAction(run_action)

        if not self.task.is_base_task():
            run_from_action = Action(
                FIF.RIGHT_ARROW, self.tr("Run from here")
            )
            run_from_action.triggered.connect(self._run_from_task)
            menu.addAction(run_from_action)

        # 插入任务选项（post action 和 controller 不显示）

        if self.task.item_id not in [POST_ACTION, _CONTROLLER_]:
            insert_action = Action(FIF.ADD, self.tr("Insert task"))
            insert_action.triggered.connect(self._insert_task)
            menu.addAction(insert_action)

        menu.popup(event.globalPos())
        event.accept()

    def _run_single_task(self):
        if not self.service_coordinator:
            return
        asyncio.create_task(self.service_coordinator.run_tasks_flow(self.task.item_id))

    def _run_from_task(self):
        if not self.service_coordinator or self.task.is_base_task():
            return
        asyncio.create_task(
            self.service_coordinator.run_tasks_flow(
                start_task_id=self.task.item_id
            )
        )

    def _insert_task(self):
        """插入任务：在当前任务下方插入新任务"""
        if not self.service_coordinator:
            return

        # 保存当前任务的 item_id，用于在对话框关闭后重新查找索引
        current_task_id = self.task.item_id

        # 打开添加任务对话框
        from app.view.task_interface.components.add_task_message_box import AddTaskDialog
        from app.common.signal_bus import signalBus

        task_map = getattr(self.service_coordinator.task, "default_option", {})
        interface = getattr(self.service_coordinator.task, "interface", {})

        # 过滤任务映射（根据当前工具栏的过滤模式，这里使用全部任务）
        filtered_task_map = task_map  # 可以根据需要添加过滤逻辑

        if not filtered_task_map:
            signalBus.info_bar_requested.emit(
                "warning", self.tr("No available tasks to add.")
            )
            return

        dlg = AddTaskDialog(
            task_map=filtered_task_map,
            interface=interface,
            interface_path=self.service_coordinator.interface_path,
            parent=self.window(),
        )
        if dlg.exec():
            new_task = dlg.get_task_item()
            if new_task:
                # 在对话框关闭后重新获取任务列表和索引（因为列表可能在对话框打开期间发生了变化）
                all_tasks = self.service_coordinator.task.get_tasks()
                current_idx = -1
                for i, task in enumerate(all_tasks):
                    if task.item_id == current_task_id:
                        current_idx = i
                        break

                # 计算插入位置：当前任务的下方（idx + 1）
                # 如果找不到当前任务，使用默认位置（-2，倒数第二个）
                if current_idx == -1:
                    insert_idx = -2
                    from app.utils.logger import logger

                    logger.warning(f"未找到任务 {current_task_id}，使用默认插入位置 -2")
                else:
                    insert_idx = current_idx + 1
                    from app.utils.logger import logger

                    logger.info(
                        f"找到任务 {current_task_id} 在索引 {current_idx}，将在索引 {insert_idx} 插入新任务 '{new_task.name}'"
                    )

                # 插入到指定位置
                self.service_coordinator.modify_task(new_task, insert_idx)

    def _create_status_widget(self):
        """创建状态标志组件"""
        widget = QWidget(self)
        widget.setFixedSize(24, 24)
        widget.hide()  # 默认隐藏
        # 创建布局用于放置状态图标或进度条
        status_layout = QHBoxLayout(widget)
        status_layout.setContentsMargins(0, 0, 0, 0)
        status_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._status_icon = None
        self._status_progress = None
        self._current_status = ""
        self._status_layout = status_layout
        return widget
    
    def update_status(self, status: str):
        """更新任务状态显示
        
        Args:
            status: 状态字符串，可选值:
                "running", "completed", "failed", "restart_success",
                "waiting", "skipped", ""(清除状态)
        """
        # 基础任务不显示状态标志
        if self.task.is_base_task():
            self.status_widget.hide()
            return
        
        self._current_status = status
        
        # 清除之前的状态组件
        if self._status_icon:
            self._status_layout.removeWidget(self._status_icon)
            self._status_icon.deleteLater()
            self._status_icon = None
        if self._status_progress:
            self._status_layout.removeWidget(self._status_progress)
            # 只对 IndeterminateProgressRing 调用 stop() 方法
            if isinstance(self._status_progress, IndeterminateProgressRing):
                self._status_progress.stop()
            self._status_progress.deleteLater()
            self._status_progress = None
        
        # 根据状态显示不同的图标
        if status == "running":
            # 显示加载动画
            self._status_progress = IndeterminateProgressRing(self.status_widget)
            self._status_progress.setFixedSize(20, 20)
            # 设置进度环宽度为更细
            self._status_progress.setStrokeWidth(2)
            self._status_layout.addWidget(self._status_progress)
            self._status_progress.start()
            self.status_widget.show()
        elif status == "completed":
            # 显示完成图标
            self._status_icon = IconWidget(FIF.ACCEPT, self.status_widget)
            self._status_icon.setFixedSize(20, 20)
            self._status_layout.addWidget(self._status_icon)
            self.status_widget.show()
        elif status == "failed":
            # 显示错误图标
            self._status_icon = IconWidget(FIF.CLOSE, self.status_widget)
            self._status_icon.setFixedSize(20, 20)
            self._status_layout.addWidget(self._status_icon)
            self.status_widget.show()
        elif status == "restart_success":
            # 显示信息图标（重启后成功）
            self._status_icon = IconWidget(FIF.ROTATE, self.status_widget)
            self._status_icon.setFixedSize(20, 20)
            self._status_layout.addWidget(self._status_icon)
            self.status_widget.show()
        elif status == "skipped":
            # 因 speedrun 被跳过：使用与完成相同的图标
            self._status_icon = IconWidget(FIF.ACCEPT, self.status_widget)
            self._status_icon.setFixedSize(20, 20)
            self._status_layout.addWidget(self._status_icon)
            self.status_widget.show()
        elif status == "waiting":
            # 显示等待图标：使用进度环显示 100% 进度，颜色为灰色
            self._status_progress = ProgressRing(self.status_widget)
            self._status_progress.setFixedSize(20, 20)
            # 设置进度环宽度为更细
            self._status_progress.setStrokeWidth(2)
            # 设置进度为 100%
            self._status_progress.setValue(100)
            # 设置颜色为灰色（使用相同的灰色作为前景和背景色）
            gray_color = QColor(128, 128, 128)  # 灰色
            self._status_progress.setCustomBarColor(gray_color, gray_color)
            self._status_layout.addWidget(self._status_progress)
            self.status_widget.show()
        else:
            # 清除状态，隐藏组件
            self.status_widget.hide()
    
    def _create_setting_button(self):
        """重写基类方法，创建删除按钮"""
        button = TransparentToolButton(FIF.DELETE)
        button.setFixedSize(34, 34)
        apply_fluent_tooltip(button, self.tr("Delete task"))
        return button

    def _on_delete_button_clicked(self):
        """处理删除按钮点击事件"""
        if not self.service_coordinator:
            return

        # 基础任务不能删除
        if self.task.is_base_task():
            return

        # 获取任务显示名称
        task_name = self._get_display_name()

        # 弹出确认对话框
        w = MessageBox(
            self.tr("Delete Task"),
            self.tr("Are you sure you want to delete task '{}'?").format(task_name),
            self.window(),
        )

        if w.exec():
            # 用户确认删除
            try:
                success = self.service_coordinator.delete_task(self.task.item_id)
                if not success:
                    from app.utils.logger import logger

                    logger.error(f"删除任务失败: {self.task.item_id}")
            except Exception as e:
                from app.utils.logger import logger

                logger.error(f"删除任务时发生错误: {e}")


# 重命名配置对话框
class RenameConfigDialog(MessageBoxBase):
    """重命名配置对话框"""

    def __init__(self, current_name: str, parent=None):
        super().__init__(parent)

        # 设置对话框标题
        self.titleLabel = SubtitleLabel(self.tr("Rename config"), self)
        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addSpacing(10)

        # 创建输入框布局
        name_layout = QVBoxLayout()
        name_label = BodyLabel(self.tr("Enter new config name:"), self)
        self.name_edit = LineEdit(self)
        self.name_edit.setText(current_name)
        self.name_edit.setPlaceholderText(self.tr("Enter the name of the config"))
        self.name_edit.setClearButtonEnabled(True)
        self.name_edit.selectAll()  # 选中所有文本以便快速输入

        name_layout.addWidget(name_label)
        name_layout.addWidget(self.name_edit)

        # 添加到视图布局
        self.viewLayout.addLayout(name_layout)

        # 设置对话框大小
        self.widget.setMinimumWidth(400)
        self.widget.setMinimumHeight(180)

        # 设置按钮文本
        self.yesButton.setText(self.tr("Confirm"))
        self.cancelButton.setText(self.tr("Cancel"))

        # 连接确认按钮信号
        self.yesButton.clicked.connect(self.on_confirm)

        # 设置焦点到输入框
        self.name_edit.setFocus()

    def on_confirm(self):
        """确认重命名"""
        new_name = self.name_edit.text().strip()
        if not new_name:
            # 如果名称为空，不接受
            return

        self.accept()

    def get_new_name(self) -> str:
        """获取新名称"""
        return self.name_edit.text().strip()


# 配置列表项组件
class ConfigListItem(BaseListItem):
    def __init__(
        self,
        config: ConfigItem,
        service_coordinator: ServiceCoordinator | None = None,
        parent=None,
    ):
        self.service_coordinator = service_coordinator
        self._locked: bool = False
        super().__init__(config, parent)

    def set_locked(self, locked: bool):
        self._locked = bool(locked)
        # 锁定时避免给出“可操作”的指针提示
        if self._locked:
            self.setCursor(Qt.CursorShape.ArrowCursor)
        else:
            self.unsetCursor()

    def set_running(self, running: bool):
        """显示/隐藏该配置的运行指示点（多实例模式下各配置独立运行）。"""
        indicator = getattr(self, "running_indicator", None)
        if indicator is None:
            return
        indicator.setVisible(bool(running))

    def _init_ui(self):
        # 创建水平布局
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)

        # 添加图标（如果有）
        icon_path = self._get_bundle_icon_path()
        if icon_path:
            self.icon_label = self._create_icon_label(icon_path)
            layout.addWidget(self.icon_label)
        else:
            self.icon_label = None

        # 添加标签
        self.name_label = self._create_name_label()
        layout.addWidget(self.name_label)

        # 运行指示点（默认隐藏，多实例模式下表示该配置正在运行）
        layout.addStretch(1)
        from qfluentwidgets import CaptionLabel as _CaptionLabel

        self.running_indicator = _CaptionLabel("●", self)
        self.running_indicator.setStyleSheet("color: #50c878;")
        self.running_indicator.setToolTip(self.tr("Running"))
        self.running_indicator.setVisible(False)
        layout.addWidget(self.running_indicator, 0, Qt.AlignmentFlag.AlignVCenter)

        # 创建设置按钮但不添加到布局（隐藏）
        self.setting_button = self._create_setting_button()
        self.setting_button.clicked.connect(self._select_in_parent_list)
        self.setting_button.hide()  # 隐藏设置按钮

    def _get_bundle_icon_path(self) -> str | None:
        """从配置的 bundle 中获取图标路径

        Returns:
            图标路径字符串，如果不存在则返回 None
        """
        if not self.service_coordinator:
            return None

        bundle_name = getattr(self.item, "bundle", None)
        if not bundle_name or not isinstance(bundle_name, str):
            return None

        try:
            # 获取 bundle 信息
            bundle_info = self.service_coordinator.config.get_bundle(bundle_name)
            if not bundle_info:
                return None

            bundle_path_str = bundle_info.get("path", "")
            if not bundle_path_str:
                return None

            # 解析 bundle 路径
            bundle_path = Path(bundle_path_str)
            if not bundle_path.is_absolute():
                bundle_path = Path.cwd() / bundle_path

            # 查找 interface.json 或 interface.jsonc
            interface_path = bundle_path / "interface.jsonc"
            if not interface_path.exists():
                interface_path = bundle_path / "interface.json"

            if not interface_path.exists():
                return None

            # 使用 preview_interface 获取 interface 数据（不改变当前激活的 interface）
            from app.core.service.interface_manager import get_interface_manager

            interface_manager = get_interface_manager()
            current_language = interface_manager.get_language()
            interface_data = interface_manager.preview_interface(
                interface_path, language=current_language
            )

            if not interface_data:
                return None

            # 获取图标路径
            icon_relative = interface_data.get("icon", "")
            if not icon_relative:
                return None

            # 图标路径相对于 bundle 路径
            icon_path = bundle_path / icon_relative
            if icon_path.exists():
                return str(icon_path)

            return None
        except Exception as e:
            from app.utils.logger import logger

            logger.warning(f"获取 bundle '{bundle_name}' 图标失败: {e}")
            return None

    def _create_icon_label(
        self, icon_path: str, base_path: Path | None = None
    ) -> BodyLabel:
        """创建图标标签（调用基类方法）

        Args:
            icon_path: 图标路径（绝对路径）
            base_path: 如果 icon_path 是相对路径，相对于此路径。如果为 None，则相对于项目根目录

        Returns:
            BodyLabel 对象，已加载图标
        """
        # 使用基类方法，传入 bundle_path 作为 base_path（如果路径是相对的话）
        # 但这里 icon_path 已经是绝对路径，所以 base_path 传 None 即可
        return super()._create_icon_label(icon_path, base_path=base_path)

    def _load_icon_to_label(
        self, icon_label: BodyLabel, icon_path: str, base_path: Path | None = None
    ):
        """将图标加载到标签中（调用基类方法）

        Args:
            icon_label: 要加载图标的标签
            icon_path: 图标路径（绝对路径）
            base_path: 如果 icon_path 是相对路径，相对于此路径。如果为 None，则相对于项目根目录
        """
        # 使用基类方法，icon_path 已经是绝对路径
        super()._load_icon_to_label(icon_label, icon_path, base_path=base_path)

    def contextMenuEvent(self, event):
        """右键菜单：复制配置 ID、更改配置名"""
        menu = RoundMenu(parent=self)

        # 添加更改配置名选项
        rename_action = Action(FIF.EDIT, self.tr("Rename config"))
        rename_action.triggered.connect(self._rename_config)
        menu.addAction(rename_action)

        # 添加复制配置 ID 选项
        copy_action = Action(FIF.COPY, self.tr("Copy config ID"))
        copy_action.triggered.connect(self._copy_config_id)
        menu.addAction(copy_action)

        # 分享配置（仅任务顺序与选项）
        share_action = Action(FIF.SHARE, self.tr("Share config"))
        share_action.triggered.connect(self._share_config)
        menu.addAction(share_action)

        menu.popup(event.globalPos())
        event.accept()

    def _rename_config(self):
        """更改配置名称"""
        if not self.service_coordinator:
            return

        # 确保 item 是 ConfigItem 类型
        if not isinstance(self.item, ConfigItem):
            return

        # 获取当前配置名称
        current_name = self.item.name
        if not current_name:
            current_name = ""

        # 创建输入对话框，使用顶层窗口作为父组件
        dialog = RenameConfigDialog(current_name, self.window())
        if dialog.exec():
            new_name = dialog.get_new_name()
            if new_name and new_name.strip() and new_name != current_name:
                new_name = new_name.strip()

                # 更新配置项的 name
                self.item.name = new_name

                # 保存配置
                try:
                    success = self.service_coordinator.config.save_config(
                        self.item.item_id, self.item
                    )
                    if success:
                        # 更新显示的标签文本
                        self.name_label.setText(new_name)

                        # 发送配置已保存的信号，触发刷新
                        self.service_coordinator.signal_bus.config_saved.emit(True)
                    else:
                        from app.utils.logger import logger

                        logger.error(f"保存配置失败: {self.item.item_id}")
                except Exception as e:
                    from app.utils.logger import logger

                    logger.error(f"保存配置时发生错误: {e}")

    def _copy_config_id(self):
        config_id = getattr(self.item, "item_id", "") or ""
        if not config_id:
            return
        QGuiApplication.clipboard().setText(str(config_id))

    def _share_config(self):
        """将配置中的任务顺序与选项编码到剪贴板。"""
        if not self.service_coordinator:
            return
        if not isinstance(self.item, ConfigItem):
            return

        from app.common.signal_bus import signalBus
        from app.utils.config_share import (
            ConfigShareError,
            encode_config_tasks,
            resolve_bundle_resource_version,
        )

        config_id = self.item.item_id
        config = self.service_coordinator.config.get_config(config_id)
        if not config:
            signalBus.info_bar_requested.emit(
                "error", self.tr("Failed to load config for sharing.")
            )
            return

        bundle_name = (config.bundle or "").strip()
        if not bundle_name:
            signalBus.info_bar_requested.emit(
                "error", self.tr("Config has no resource bundle, cannot share.")
            )
            return

        resource_version = resolve_bundle_resource_version(
            self.service_coordinator.config, bundle_name
        )

        try:
            code = encode_config_tasks(
                config,
                bundle=bundle_name,
                resource_version=resource_version,
            )
        except ConfigShareError:
            signalBus.info_bar_requested.emit(
                "error", self.tr("Failed to encode config for sharing.")
            )
            return
        except Exception:
            signalBus.info_bar_requested.emit(
                "error", self.tr("Failed to encode config for sharing.")
            )
            return

        QGuiApplication.clipboard().setText(code)
        signalBus.info_bar_requested.emit(
            "success", self.tr("Config copied to clipboard.")
        )

