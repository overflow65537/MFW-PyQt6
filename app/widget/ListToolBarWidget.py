from json import tool
import re
import markdown

from PySide6.QtCore import Qt
import json
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QAbstractItemView,
    QSplitter,
    QPushButton,
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

from app.common import icon


from .ListWidget import TaskDragListWidget, ConfigListWidget
from .AddTaskMessageBox import AddConfigDialog, AddTaskDialog
from ..core.core import CoreSignalBus, TaskItem, ConfigItem, ServiceCoordinator
from .ListItem import TaskListItem, ConfigListItem


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
            bundles = main_cfg.get("bundle", [])

        dlg = AddConfigDialog(resource_bundles=bundles, parent=self.window())
        if dlg.exec():
            cfg = dlg.get_config_item()
            if cfg:
                self.service_coordinator.add_config(cfg)

    def remove_config(self):
        """移除配置项"""
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
        # 调用服务删除即可，视图通过信号刷新
        self.service_coordinator.delete_config(cfg_id)


class TaskListToolBarWidget(BaseListToolBarWidget):

    def __init__(self, service_coordinator: ServiceCoordinator, parent=None):
        super().__init__(service_coordinator=service_coordinator, parent=parent)
        self.core_signalBus = self.service_coordinator.signal_bus
        # 选择全部按钮
        self.select_all_button.clicked.connect(self.select_all)
        # 取消选择全部按钮
        self.deselect_all_button.clicked.connect(self.deselect_all)
        # 添加按钮
        self.add_button.clicked.connect(self.add_task)
        # 删除按钮
        self.delete_button.clicked.connect(self.remove_selected_task)

        # 监听服务总线任务选中事件以更新标题/选项
        self.core_signalBus.task_selected.connect(self._change_title)

        # 初始填充任务列表
        # 不在工具栏直接刷新列表：视图会订阅 ServiceCoordinator 的信号自行更新

    def _init_task_list(self):
        """初始化任务列表"""
        self.task_list = TaskDragListWidget(
            service_coordinator=self.service_coordinator, parent=self
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
        dlg = AddTaskDialog(task_map=task_map, parent=self.window())
        if dlg.exec():
            new_task = dlg.get_task_item()
            if new_task:
                # 持久化到服务层
                self.service_coordinator.modify_task(new_task)

    def _change_title(self, task_id: str):
        """改变标题为被选中的任务名（通过 task_id 查找）"""
        task = self.service_coordinator.task.get_task(task_id)
        if task:
            self.set_title(task.name)

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
        # 删除通过服务层执行，视图会通过fs系列信号刷新
        self.service_coordinator.delete_task(task_id)


class OptionWidget(QWidget):
    def __init__(self, service_coordinator: ServiceCoordinator, parent=None):
        super().__init__(parent)
        self.service_coordinator = service_coordinator
        self.task = self.service_coordinator.task
        self.config = self.service_coordinator.config
        self.core_signalBus = self.service_coordinator.signal_bus
        # 使用 task_selected 信号（由 ServiceCoordinator 触发）
        self.core_signalBus.task_selected.connect(self.show_option)
        self._init_ui()
        self._toggle_description(visible=False)

    def _init_ui(self):
        """初始化UI"""
        self.main_layout = QVBoxLayout(self)

        self.title_widget = BodyLabel()
        self.title_widget.setStyleSheet("font-size: 20px;")
        self.title_widget.setAlignment(Qt.AlignmentFlag.AlignLeft)

        # ==================== 选项区域 ==================== #
        # 创建选项卡片
        self.option_area_card = SimpleCardWidget()
        self.option_area_card.setClickEnabled(False)
        self.option_area_card.setBorderRadius(8)

        self.option_area_widget = ScrollArea()
        # 设置透明无边框
        self.option_area_widget.setStyleSheet(
            "background-color: transparent; border: none;"
        )
        self.option_area_layout = QVBoxLayout()  # 先创建布局
        self.option_area_widget.setLayout(self.option_area_layout)
        self.option_area_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # 创建一个垂直布局给卡片，然后将滚动区域添加到这个布局中
        card_layout = QVBoxLayout()
        card_layout.addWidget(self.option_area_widget)
        card_layout.setContentsMargins(0, 0, 0, 0)
        self.option_area_card.setLayout(card_layout)
        # ==================== 描述区域 ==================== #
        # 创建描述标题（直接放在主布局中）
        self.description_title = BodyLabel("功能描述")
        self.description_title.setStyleSheet("font-size: 16px; font-weight: bold;")
        self.description_title.setAlignment(Qt.AlignmentFlag.AlignLeft)

        # 创建描述卡片
        self.description_area_card = SimpleCardWidget()
        self.description_area_card.setClickEnabled(False)
        self.description_area_card.setBorderRadius(8)

        # 正确的布局层次结构
        self.description_area_widget = (
            QWidget()
        )  # 使用普通Widget作为容器，而不是ScrollArea
        self.description_layout = QVBoxLayout(
            self.description_area_widget
        )  # 这个布局只属于widget
        self.description_layout.setContentsMargins(10, 10, 10, 10)  # 设置适当的边距

        # 描述内容区域
        self.description_content = BodyLabel()
        self.description_content.setWordWrap(True)
        self.description_layout.addWidget(self.description_content)

        self.description_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # 创建滚动区域来包裹内容
        self.description_scroll_area = ScrollArea()
        self.description_scroll_area.setWidget(self.description_area_widget)
        self.description_scroll_area.setWidgetResizable(True)
        self.description_scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.description_scroll_area.setStyleSheet(
            "background-color: transparent; border: none;"
        )

        # 将滚动区域添加到卡片
        card_layout = QVBoxLayout(self.description_area_card)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.addWidget(self.description_scroll_area)

        # ==================== 分割器 ==================== #
        # 创建垂直分割器，实现可调整比例功能
        self.splitter = QSplitter(Qt.Orientation.Vertical)

        # 创建选项区域容器（仅用于分割器）
        self.option_splitter_widget = QWidget()
        self.option_splitter_layout = QVBoxLayout(self.option_splitter_widget)
        self.option_splitter_layout.addWidget(self.option_area_card)
        self.option_splitter_layout.setContentsMargins(0, 0, 0, 0)

        # 创建描述区域容器（仅用于分割器）
        self.description_splitter_widget = QWidget()
        self.description_splitter_layout = QVBoxLayout(self.description_splitter_widget)
        self.description_splitter_layout.addWidget(self.description_title)
        self.description_splitter_layout.addWidget(self.description_area_card)
        # 设置占用比例
        self.description_splitter_layout.setStretch(0, 1)  # 标题占用1单位
        self.description_splitter_layout.setStretch(1, 99)  # 内容占用99单位
        self.description_splitter_layout.setContentsMargins(0, 0, 0, 0)

        # 添加到分割器
        self.splitter.addWidget(self.option_splitter_widget)  # 上方：选项区域
        self.splitter.addWidget(self.description_splitter_widget)  # 下方：描述区域

        # 设置初始比例
        self.splitter.setSizes([90, 10])  # 90% 和 10% 的初始比例

        # 添加到主布局
        self.main_layout.addWidget(self.title_widget)  # 直接添加标题
        self.main_layout.addWidget(self.splitter)  # 添加分割器
        # 添加主布局间距
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(10)

    def _toggle_description(self, visible=None):
        """切换描述区域的显示/隐藏
        visible: True显示，False隐藏，None切换当前状态
        """
        if visible is None:
            # 切换当前状态
            visible = not self.description_splitter_widget.isVisible()

        if visible:
            self.description_splitter_widget.show()
            # 恢复初始比例
            self.splitter.setSizes([90, 10])
        else:
            self.description_splitter_widget.hide()
            # 让选项区域占据全部空间
            self.splitter.setSizes([100, 0])

    def set_description(self, description: str):
        """设置描述内容"""
        self.description_content.setText("")

        html = markdown.markdown(description).replace("\n", "")
        html = re.sub(
            r"<code>(.*?)</code>",
            r"<span style='color: #009faa;'>\1</span>",
            html,
        )
        html = re.sub(
            r'(<a\s+[^>]*href="[^"]+"[^>]*)>', r'\1 style="color: #009faa;">', html
        )
        html = re.sub(r"<li><p>(.*?)</p></li>", r"<p><strong>◆ </strong>\1</p>", html)
        html = re.sub(r"<ul>(.*?)</ul>", r"\1", html)

        self.description_content.setText(html)

    def reset(self):
        """重置选项区域和描述区域"""
        self.set_title(self.tr("Options"))
        self._clear_options()

        self._toggle_description(visible=False)

    def set_title(self, title: str):
        """设置标题"""
        self.title_widget.setText(title)

    def show_option(self, item_or_id: TaskItem | ConfigItem | str):
        """显示选项。参数可以是 task_id(str) 或 TaskItem/ConfigItem 对象。"""
        self.reset()
        # 如果传入的是 id，获取对象
        item = item_or_id
        if isinstance(item_or_id, str):
            item = self.task.get_task(item_or_id)
        if not item:
            return
        if isinstance(item, TaskItem):
            self.set_title(item.name)
            # 只展示任务选项
            self._show_task_option(item)

    def _show_task_option(self, item: TaskItem):
        """显示任务选项"""

        def _get_task_info(interface: dict, option: str, item: TaskItem):
            name = interface["option"][option].get(
                "label", interface["option"][option].get("name", option)
            )
            obj_name = interface["option"][option].get("name")
            options = self.Get_Task_List(interface, option)
            current = item.task_option.get(option, {}).get("value")
            icon_path = interface["option"][option].get("icon", "")
            tooltip = interface["option"][option].get("description", "")
            option_tooltips = {}
            for cases in interface["option"][option]["cases"]:
                option_tooltips[cases["name"]] = cases.get("description", "")
            return name, obj_name, options, current, icon_path, tooltip, option_tooltips

        # TaskService stores interface in attribute 'interface'
        interface = getattr(self.task, "interface", None)
        if not interface:
            # fallback load from file
            interface_path = Path.cwd() / "interface.json"
            if not interface_path.exists():
                return
            with open(interface_path, "r", encoding="utf-8") as f:
                interface = json.load(f)
        target_task = None
        for task_template in interface["task"]:
            if task_template["name"] == item.name:
                target_task = task_template
                break
        if target_task is None:
            print(f"未找到任务模板: {item.name}")
            return
        task_description = target_task.get("description")
        if task_description:
            self._toggle_description(True)
            self.set_description(task_description)
        for option in target_task["option"]:
            name, obj_name, options, current, icon_path, tooltip, option_tooltips = (
                _get_task_info(interface, option, item)
            )
            if interface["option"][option].get("type", "select") == "input":
                self._add_combox_option(
                    name,
                    obj_name,
                    options,
                    current,
                    icon_path,
                    True,
                    tooltip,
                    option_tooltips,
                )
            else:
                self._add_combox_option(
                    name,
                    obj_name,
                    options,
                    current,
                    icon_path,
                    False,
                    tooltip,
                    option_tooltips,
                )

    from typing import List

    def Get_Task_List(self, interface: dict, target: str) -> List[str]:
        """根据选项名称获取所有case的name列表。

        Args:
            path (str): 配置文件路径。
            target (str): 选项名称。

        Returns:
            list: 包含所有case的name列表。
        """
        lists = []
        Task_Config = interface["option"][target]["cases"]
        if not Task_Config:
            return []
        Lens = len(Task_Config) - 1
        for i in range(Lens, -1, -1):
            lists.append(Task_Config[i]["name"])
        lists.reverse()
        return lists

    def _show_resource_option(self, item: TaskItem):
        """显示资源选项"""
        self._clear_options()

    def _show_controller_option(self, item: TaskItem):
        self._clear_options()

    def _add_combox_option(
        self,
        name: str,
        obj_name: str,
        options: list[str],
        current: str | None = None,
        icon_path: str = "",
        editable: bool = False,
        tooltip: str = "",
        option_tooltips: dict[str, str] | None = None,
    ):
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
        combo_box.setObjectName(obj_name)
        v_layout.setObjectName(f"{obj_name}_layout")
        combo_box.addItems(options)
        if current:
            combo_box.setCurrentText(current)
        else:
            current = combo_box.currentText()
        v_layout.addWidget(combo_box)

        # 设置标签的工具提示（第一种工具提示：任务介绍）
        if tooltip:
            text_label.setToolTip(tooltip)
            text_label.installEventFilter(
                ToolTipFilter(text_label, 0, ToolTipPosition.TOP)
            )

        # 设置下拉框的初始工具提示和连接信号（第二种工具提示：选项介绍）
        if option_tooltips and isinstance(option_tooltips, dict):
            # 设置初始工具提示
            if current in option_tooltips:
                combo_box.setToolTip(option_tooltips[current])
            combo_box.installEventFilter(
                ToolTipFilter(combo_box, 0, ToolTipPosition.TOP)
            )

            # 连接currentTextChanged信号，当选项改变时更新工具提示
            combo_box.currentTextChanged.connect(
                lambda text: (
                    combo_box.setToolTip(option_tooltips.get(text, ""))
                    if option_tooltips
                    else None
                )
            )
        elif tooltip:  # 如果没有提供选项级工具提示但有整体工具提示
            combo_box.setToolTip(tooltip)
            combo_box.installEventFilter(
                ToolTipFilter(combo_box, 0, ToolTipPosition.TOP)
            )

        self.option_area_layout.addLayout(v_layout)

    def _add_lineedit_option(
        self, name: str, current: str, tooltip: str = "", obj_name: str = ""
    ):
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

    def _add_switch_option(
        self, name: str, current: bool, tooltip: str = "", obj_name: str = ""
    ):
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
            switch.installEventFilter(ToolTipFilter(switch, 0, ToolTipPosition.TOP))
        self.option_area_layout.addLayout(v_layout)

    def _clear_options(self):
        """清除所有选项"""

        def recursive_clear_layout(layout):
            """递归清理布局中的所有项目"""
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget:
                    widget.hide()
                    widget.deleteLater()
                elif item.layout():
                    nested_layout = item.layout()
                    recursive_clear_layout(nested_layout)
                    if nested_layout.parent() is None:
                        del nested_layout
                elif item.spacerItem():
                    layout.removeItem(item)

        recursive_clear_layout(self.option_area_layout)
