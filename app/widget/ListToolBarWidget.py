import json
import re
from pathlib import Path

import markdown
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QSplitter,
)


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

from app.utils.logger import logger
from app.utils.gui_helper import IconLoader


from .ListWidget import TaskDragListWidget, ConfigListWidget
from .AddTaskMessageBox import AddConfigDialog, AddTaskDialog
from ..core.core import TaskItem, ConfigItem, ServiceCoordinator
from .ListItem import TaskListItem, ConfigListItem


class BaseListToolBarWidget(QWidget):

    def __init__(self, service_coordinator: ServiceCoordinator, parent=None):
        super().__init__(parent)
        self.service_coordinator = service_coordinator
        
        # 创建图标加载器（仅 GUI 使用）
        self.icon_loader = IconLoader(service_coordinator)

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
        # 调用服务删除即可,视图通过信号刷新
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

        # 设置任务列表标题
        self.set_title(self.tr("Tasks"))

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
        interface = getattr(self.service_coordinator.task, "interface", {})
        dlg = AddTaskDialog(
            task_map=task_map, interface=interface, parent=self.window()
        )
        if dlg.exec():
            new_task = dlg.get_task_item()
            if new_task:
                # 持久化到服务层
                self.service_coordinator.modify_task(new_task)

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
        
        # 创建图标加载器（仅 GUI 使用）
        self.icon_loader = IconLoader(service_coordinator)
        
        # 使用 task_selected 信号（由 ServiceCoordinator 触发）
        self.core_signalBus.task_selected.connect(self.show_option)
        # 监听配置切换以重置选项面板
        self.core_signalBus.config_changed.connect(self._on_config_changed)
        self._init_ui()
        self._toggle_description(visible=False)

        # 设置选项面板标题
        self.set_title(self.tr("Options"))

        # 当前正在编辑的任务
        self.current_task: TaskItem | None = None

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

        # 创建滚动区域
        self.option_area_widget = ScrollArea()
        self.option_area_widget.setWidgetResizable(
            True
        )  # 重要:允许内部widget自动调整大小
        # 设置透明无边框
        self.option_area_widget.setStyleSheet(
            "background-color: transparent; border: none;"
        )

        # 创建一个容器widget来承载布局
        option_container = QWidget()
        self.option_area_layout = QVBoxLayout(option_container)  # 将布局关联到容器
        self.option_area_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.option_area_layout.setContentsMargins(10, 10, 10, 10)  # 添加内边距

        # 将容器widget设置到滚动区域
        self.option_area_widget.setWidget(option_container)

        # 创建一个垂直布局给卡片,然后将滚动区域添加到这个布局中
        card_layout = QVBoxLayout()
        card_layout.addWidget(self.option_area_widget)
        card_layout.setContentsMargins(0, 0, 0, 0)
        self.option_area_card.setLayout(card_layout)
        # ==================== 描述区域 ==================== #
        # 创建描述标题（直接放在主布局中）
        self.description_title = BodyLabel("功能描述")
        self.description_title.setStyleSheet("font-size: 20px;")
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
        self.splitter.setStyleSheet(
            """
            QSplitter::handle:vertical {
                background: transparent;   
            }
            """
        )

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
        self._clear_options()
        self._toggle_description(visible=False)
        self.current_task = None

    def _on_config_changed(self, config_id: str):
        """配置切换时重置选项面板"""
        self.reset()

    def _save_current_options(self):
        """收集当前所有选项控件的值并保存到配置"""
        if not self.current_task:
            return

        # 递归查找所有控件的辅助函数
        def find_widgets_recursive(layout, widgets_list):
            """递归查找布局中的所有控件"""
            for i in range(layout.count()):
                item = layout.itemAt(i)
                if not item:
                    continue

                widget = item.widget()
                if widget:
                    widgets_list.append(widget)
                elif item.layout():
                    # 递归查找子布局
                    find_widgets_recursive(item.layout(), widgets_list)

        # 收集所有控件
        all_widgets = []
        find_widgets_recursive(self.option_area_layout, all_widgets)

        # 遍历所有控件，收集有 objectName 的选项控件
        updated_options = {}
        for widget in all_widgets:
            # 获取控件的 objectName
            obj_name = widget.objectName()
            if not obj_name:
                continue

            # 检查是否是多输入项格式(option$input_name)
            if "$" in obj_name:
                option_name, input_name = obj_name.split("$", 1)

                # 确保 option 存在
                if option_name not in updated_options:
                    updated_options[option_name] = {}

                # 获取值
                if isinstance(widget, LineEdit):
                    value = widget.text()

                    # 获取 pipeline_type 属性,根据类型转换值
                    pipeline_type = widget.property("pipeline_type")
                    if pipeline_type == "int":
                        # 尝试转换为整数,失败则保持字符串
                        try:
                            value = int(value) if value else 0
                        except ValueError:
                            logger.warning(
                                f"无法将 '{value}' 转换为整数,保持字符串格式"
                            )

                    updated_options[option_name][input_name] = {
                        "value": value,
                        "type": "input",
                    }
            # 检查是否是嵌套选项格式(parent__nested__option_name)
            elif "__nested__" in obj_name:
                # 嵌套选项:作战关卡A__nested__是否进行信源回收
                # 提取真正的选项名(最后一部分)
                real_option_name = obj_name.split("__nested__")[-1]

                # 根据控件类型获取值
                if isinstance(widget, (ComboBox, EditableComboBox)):
                    value = widget.currentText()
                    option_type = (
                        "input" if isinstance(widget, EditableComboBox) else "select"
                    )
                    updated_options[real_option_name] = {
                        "value": value,
                        "type": option_type,
                    }
                elif isinstance(widget, LineEdit):
                    updated_options[real_option_name] = {
                        "value": widget.text(),
                        "type": "input",
                    }
            else:
                # 单个选项:普通格式
                # 根据控件类型获取值
                if isinstance(widget, (ComboBox, EditableComboBox)):
                    value = widget.currentText()
                    # 获取选项类型
                    option_type = (
                        "input" if isinstance(widget, EditableComboBox) else "select"
                    )

                    updated_options[obj_name] = {"value": value, "type": option_type}
                elif isinstance(widget, LineEdit):
                    updated_options[obj_name] = {
                        "value": widget.text(),
                        "type": "input",
                    }
                elif isinstance(widget, SwitchButton):
                    updated_options[obj_name] = {
                        "value": widget.isChecked(),
                        "type": "switch",
                    }

        # 更新任务的 task_option
        if updated_options:
            self.current_task.task_option.update(updated_options)
            # 通过服务层保存
            self.service_coordinator.modify_task(self.current_task)

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
            # 保存当前任务引用
            self.current_task = item
            # 只展示任务选项
            self._show_task_option(item)

    def _show_task_option(self, item: TaskItem):
        """显示任务选项"""

        def _get_task_info(interface: dict, option: str, item: TaskItem):
            name = interface["option"][option].get(
                "label", interface["option"][option].get("name", option)
            )
            # option 本身就是键名，不需要再获取 name 字段
            obj_name = option
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
            logger.warning(f"未找到任务模板: {item.name}")
            return

        # 收集描述内容
        descriptions = []

        # 添加任务描述
        task_description = target_task.get("description")
        if task_description:
            descriptions.append(task_description)

        # 添加文档说明
        task_doc = target_task.get("doc")
        if task_doc:
            descriptions.append(task_doc)

        # 根据是否有描述内容决定是否显示描述区域
        if descriptions:
            self._toggle_description(True)
            combined_description = "\n\n---\n\n".join(descriptions)
            self.set_description(combined_description)
        else:
            # 没有任何描述内容时才关闭描述区域
            self._toggle_description(False)

        # 使用智能排序逻辑添加选项
        # 主选项按照 task 的 option 数组顺序，嵌套选项紧随其父选项之后
        self._add_options_with_order(target_task, interface, item)

    def _add_options_with_order(
        self, target_task: dict, interface: dict, item: TaskItem
    ):
        """按照智能顺序添加选项

        主选项按 task.option 顺序添加，嵌套选项紧随其父选项

        Args:
            target_task: 任务模板配置
            interface: 完整的 interface 配置
            item: 当前任务项
        """
        added_options = set()  # 跟踪已添加的选项，避免重复

        def _get_task_info(option: str):
            """获取选项的显示信息和配置"""
            option_config = interface["option"][option]
            display_name = option_config.get("label", option_config.get("name", option))
            obj_name = option
            options = self.Get_Task_List(interface, option)
            current = item.task_option.get(option, {}).get("value")
            icon_path = option_config.get("icon", "")
            tooltip = option_config.get("description", "")

            # 收集选项提示信息
            option_tooltips = {}
            for case in option_config.get("cases", []):
                option_tooltips[case["name"]] = case.get("description", "")

            return (
                display_name,
                obj_name,
                options,
                current,
                icon_path,
                tooltip,
                option_tooltips,
                option_config,
            )

        def _get_current_case_config(option_name: str):
            """获取选项当前选中的 case 配置

            如果没有选中或找不到，返回第一个 case
            """
            option_config = interface["option"].get(option_name)
            if not option_config:
                return None

            cases = option_config.get("cases", [])
            if not cases:
                return None

            # 尝试获取当前值对应的 case
            current_value = item.task_option.get(option_name, {}).get("value")
            if current_value:
                for case in cases:
                    if case.get("name") == current_value:
                        return case

            # 默认返回第一个 case
            return cases[0]

        def _add_option_recursive(option_name: str, depth: int = 0):
            """递归添加选项及其嵌套选项

            Args:
                option_name: 选项名称
                depth: 递归深度，防止无限递归
            """
            # 防止重复添加和无限递归
            if option_name in added_options or depth > 10:
                return

            added_options.add(option_name)

            # 获取选项配置
            option_config = interface["option"].get(option_name)
            if not option_config:
                logger.warning(f"未找到选项配置: {option_name}")
                return

            option_type = option_config.get("type", "select")
            created_combo = None

            # 根据选项类型创建对应的控件
            if "inputs" in option_config and isinstance(
                option_config.get("inputs"), list
            ):
                # 多输入项类型（如"自定义关卡"）
                self._add_multi_input_option(option_name, option_config, item)
            elif option_type == "input":
                # 可编辑下拉框
                (
                    display_name,
                    obj_name,
                    options,
                    current,
                    icon_path,
                    tooltip,
                    option_tooltips,
                    opt_cfg,
                ) = _get_task_info(option_name)
                created_combo = self._add_combox_option(
                    display_name,
                    obj_name,
                    options,
                    current,
                    icon_path,
                    editable=True,
                    tooltip=tooltip,
                    option_tooltips=option_tooltips,
                    option_config=opt_cfg,
                    skip_initial_nested=True,
                    block_signals=True,
                    return_widget=True,
                )
            else:
                # 普通下拉框
                (
                    display_name,
                    obj_name,
                    options,
                    current,
                    icon_path,
                    tooltip,
                    option_tooltips,
                    opt_cfg,
                ) = _get_task_info(option_name)
                created_combo = self._add_combox_option(
                    display_name,
                    obj_name,
                    options,
                    current,
                    icon_path,
                    editable=False,
                    tooltip=tooltip,
                    option_tooltips=option_tooltips,
                    option_config=opt_cfg,
                    skip_initial_nested=True,
                    block_signals=True,
                    return_widget=True,
                )

            # 处理嵌套选项
            if (
                created_combo
                and option_type in ["select", "input"]
                and option_config.get("cases")
            ):
                current_case = _get_current_case_config(option_name)
                if current_case and "option" in current_case:
                    current_value = item.task_option.get(option_name, {}).get("value")
                    if current_value:
                        self._update_nested_options(
                            created_combo, current_value, recursive=True
                        )

        # 按照 task 的 option 数组顺序添加选项
        for option in target_task.get("option", []):
            _add_option_recursive(option)

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

    def _add_multi_input_option(
        self,
        option_name: str,
        option_config: dict,
        item: TaskItem,
        parent_option_name: str | None = None,
        insert_index: int | None = None,
    ):
        """添加多输入项选项

        用于创建包含多个输入框的选项，如"自定义关卡"

        Args:
            option_name: 选项名称
            option_config: 选项配置，必须包含 inputs 数组
            item: 当前任务项
            parent_option_name: 父级选项名（作为嵌套选项时使用）
            insert_index: 插入位置索引（作为嵌套选项时使用）
        """
        saved_data = item.task_option.get(option_name, {})
        main_description = option_config.get("description", "")
        main_label = option_config.get("label", option_name)
        icon_path = option_config.get("icon", "")

        # 创建主布局
        main_layout = QVBoxLayout()
        if parent_option_name:
            main_layout.setObjectName(
                f"{parent_option_name}__nested__{option_name}_layout"
            )

        # 创建主标题区域
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(5)

        # 添加图标（如果存在）
        icon = self.icon_loader.load_icon(icon_path, size=16)
        if not icon.isNull():
            icon_label = BodyLabel()
            icon_label.setPixmap(icon.pixmap(16, 16))
            title_layout.addWidget(icon_label)

        # 添加主标题（加粗）
        title_label = BodyLabel(main_label)
        title_label.setStyleSheet("font-weight: bold;")
        title_layout.addWidget(title_label)

        main_layout.addLayout(title_layout)

        # 设置主标题的工具提示
        if main_description:
            title_label.setToolTip(main_description)
            title_label.installEventFilter(
                ToolTipFilter(title_label, 0, ToolTipPosition.TOP)
            )

        # 创建各个输入框
        need_save = False
        for input_config in option_config.get("inputs", []):
            input_name = input_config.get("name")
            input_label = input_config.get("label", input_name)
            input_description = input_config.get("description", "")
            default_value = input_config.get("default", "")
            verify_pattern = input_config.get("verify", "")
            pipeline_type = input_config.get("pipeline_type", "string")

            # 获取当前值并进行类型转换
            current_value = saved_data.get(input_name, {}).get("value", default_value)
            if pipeline_type == "int" and isinstance(current_value, str):
                try:
                    current_value = int(current_value) if current_value else 0
                    if input_name in saved_data:
                        saved_data[input_name]["value"] = current_value
                        need_save = True
                except ValueError:
                    logger.warning(f"无法将 '{current_value}' 转换为整数，保持原值")

            # 创建输入项布局
            input_layout = QVBoxLayout()

            # 子标题（不加粗）
            label_layout = QHBoxLayout()
            label_layout.setContentsMargins(0, 0, 0, 0)
            label_layout.setSpacing(5)

            label = BodyLabel(input_label)
            label_layout.addWidget(label)

            input_layout.addLayout(label_layout)

            # 创建输入框
            line_edit = LineEdit()
            line_edit.setText(str(current_value))
            line_edit.setPlaceholderText(f"默认: {default_value}")
            line_edit.setObjectName(f"{option_name}${input_name}")
            line_edit.setProperty("pipeline_type", pipeline_type)

            # 添加输入验证
            if verify_pattern:

                def create_validator(pattern):
                    def validate():
                        text = line_edit.text()
                        if text and not re.match(pattern, text):
                            line_edit.setStyleSheet("border: 1px solid red;")
                        else:
                            line_edit.setStyleSheet("")

                    return validate

                line_edit.textChanged.connect(create_validator(verify_pattern))

            input_layout.addWidget(line_edit)

            # 设置工具提示
            if input_description:
                label.setToolTip(input_description)
                label.installEventFilter(ToolTipFilter(label, 0, ToolTipPosition.TOP))
                line_edit.setToolTip(input_description)
                line_edit.installEventFilter(
                    ToolTipFilter(line_edit, 0, ToolTipPosition.TOP)
                )

            # 连接保存信号
            line_edit.textChanged.connect(lambda: self._save_current_options())

            main_layout.addLayout(input_layout)

        # 如果修正了数据类型，立即保存
        if need_save:
            item.task_option[option_name] = saved_data
            self.service_coordinator.modify_task(item)
            logger.info(f"已修正选项 '{option_name}' 的数据类型")

        # 添加到选项区域（支持指定插入位置）
        if insert_index is not None:
            self.option_area_layout.insertLayout(insert_index, main_layout)
        else:
            self.option_area_layout.addLayout(main_layout)

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
        option_config: dict | None = None,
        skip_initial_nested: bool = False,
        block_signals: bool = False,
        return_widget: bool = False,
    ):
        """添加下拉选项

        Args:
            option_config: 选项配置字典,包含 cases 信息,用于支持嵌套选项
            skip_initial_nested: 是否跳过初始嵌套选项加载（当使用 _add_options_with_order 时为 True）
            block_signals: 是否阻塞信号（初始化加载时为 True，避免 currentTextChanged 触发重复加载）
            return_widget: 是否返回创建的ComboBox控件（用于初始化时创建嵌套选项）
        """
        v_layout = QVBoxLayout()

        # 创建水平布局用于放置图标和标签
        h_layout = QHBoxLayout()
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_layout.setSpacing(5)

        # 创建图标标签（只在有图标时添加）
        icon = self.icon_loader.load_icon(icon_path, size=16)
        if not icon.isNull():
            icon_label = BodyLabel()
            icon_label.setPixmap(icon.pixmap(16, 16))
            h_layout.addWidget(icon_label)

        # 创建文本标签（主标题加粗）
        text_label = BodyLabel(name)
        text_label.setStyleSheet("font-weight: bold;")

        # 添加到水平布局（不添加 stretch，紧贴左边）
        h_layout.addWidget(text_label)

        # 将水平布局添加到垂直布局
        v_layout.addLayout(h_layout)

        if editable:
            combo_box = EditableComboBox()
        else:
            combo_box = ComboBox()

        combo_box.setObjectName(obj_name)
        v_layout.setObjectName(f"{obj_name}_layout")

        combo_box.addItems(options)

        # 存储选项配置到 combo_box,用于嵌套选项处理
        if option_config:
            combo_box.setProperty("option_config", option_config)
            combo_box.setProperty("parent_option_name", obj_name)

        # 设置标签的工具提示(第一种工具提示:任务介绍)
        if tooltip:
            text_label.setToolTip(tooltip)
            text_label.installEventFilter(
                ToolTipFilter(text_label, 0, ToolTipPosition.TOP)
            )

        # 设置下拉框的初始工具提示和连接信号(第二种工具提示:选项介绍)
        if option_tooltips and isinstance(option_tooltips, dict):
            # 设置初始工具提示
            if current in option_tooltips:
                combo_box.setToolTip(option_tooltips[current])
            combo_box.installEventFilter(
                ToolTipFilter(combo_box, 0, ToolTipPosition.TOP)
            )

            # 连接currentTextChanged信号,当选项改变时更新工具提示
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

        # 连接值变化信号,处理嵌套选项和自动保存
        combo_box.currentTextChanged.connect(
            lambda text: self._on_combox_changed(combo_box, text)
        )

        # 如果需要阻塞信号（初始化时），在设置值前阻塞，设置后恢复
        if block_signals:
            combo_box.blockSignals(True)

        if current:
            combo_box.setCurrentText(current)
        else:
            current = combo_box.currentText()

        if block_signals:
            combo_box.blockSignals(False)

        v_layout.addWidget(combo_box)

        # 初始加载时检查是否有嵌套选项（仅在非智能排序模式下）
        # 如果使用 _add_options_with_order，则跳过此步骤避免重复
        if option_config and not skip_initial_nested:
            self._update_nested_options(combo_box, current or combo_box.currentText())

        self.option_area_layout.addLayout(v_layout)

        # 如果需要返回控件，返回创建的ComboBox
        if return_widget:
            return combo_box

    def _on_combox_changed(self, combo_box: ComboBox | EditableComboBox, text: str):
        """ComboBox值改变时的回调

        处理嵌套选项更新和配置保存
        """
        self._update_nested_options(combo_box, text, recursive=False)
        self._save_current_options()

    def _update_nested_options(
        self,
        combo_box: ComboBox | EditableComboBox,
        selected_case: str,
        recursive: bool = True,
    ):
        """更新嵌套选项

        根据选中的 case 动态显示或隐藏嵌套选项

        Args:
            combo_box: 父级ComboBox控件
            selected_case: 当前选中的case名称
            recursive: 是否递归加载子嵌套选项
                      初始加载时为True，用户交互时为False
        """
        option_config = combo_box.property("option_config")
        parent_option_name = combo_box.property("parent_option_name")

        if not option_config or not parent_option_name:
            return

        # 获取当前嵌套深度（如果是嵌套选项）
        current_depth = combo_box.property("nested_depth")
        if current_depth is None:
            current_depth = 0  # 顶级选项

        # 移除之前的嵌套选项(如果有)
        self._remove_nested_options(parent_option_name)

        # 查找当前选中的case配置
        cases = option_config.get("cases", [])
        selected_case_config = None
        for case in cases:
            if case.get("name") == selected_case:
                selected_case_config = case
                break

        if not selected_case_config:
            return

        # 获取嵌套选项列表
        nested_options = selected_case_config.get("option", [])
        if not nested_options:
            return

        # 加载interface配置
        interface = getattr(self.task, "interface", None)
        if not interface:
            interface_path = Path.cwd() / "interface.json"
            if not interface_path.exists():
                return
            with open(interface_path, "r", encoding="utf-8") as f:
                interface = json.load(f)

        # 找到父级ComboBox的布局在option_area_layout中的位置
        parent_layout_name = f"{parent_option_name}_layout"
        insert_index = -1
        for i in range(self.option_area_layout.count()):
            item = self.option_area_layout.itemAt(i)
            if (
                item
                and item.layout()
                and item.layout().objectName() == parent_layout_name
            ):
                insert_index = i + 1
                break

        # 如果没找到父级布局,添加到末尾
        if insert_index == -1:
            insert_index = self.option_area_layout.count()

        # 添加嵌套选项
        for nested_option in nested_options:
            nested_option_config = interface["option"].get(nested_option)
            if not nested_option_config:
                continue

            # 标记为嵌套选项
            nested_obj_name = f"{parent_option_name}__nested__{nested_option}"

            # 获取当前任务的保存值
            current_value = None
            if self.current_task:
                current_value = self.current_task.task_option.get(
                    nested_option, {}
                ).get("value")

            # 根据选项类型添加控件
            option_type = nested_option_config.get("type", "select")

            if "inputs" in nested_option_config and isinstance(
                nested_option_config.get("inputs"), list
            ):
                # 多输入项类型(例如: 自定义关卡)。作为嵌套选项插入到父项之后，并带有可识别的objectName，便于切换时清理。
                if self.current_task:
                    self._add_multi_input_option(
                        nested_option,
                        nested_option_config,
                        self.current_task,
                        parent_option_name=parent_option_name,
                        insert_index=insert_index,
                    )
                    insert_index += 1
            elif option_type == "input":
                # 可编辑下拉框
                name = nested_option_config.get("label", nested_option)
                options = self.Get_Task_List(interface, nested_option)
                icon_path = nested_option_config.get("icon", "")
                tooltip = nested_option_config.get("description", "")
                option_tooltips = {}
                for case in nested_option_config.get("cases", []):
                    option_tooltips[case["name"]] = case.get("description", "")

                # 创建嵌套选项布局（传递深度+1）
                v_layout = self._create_nested_option_layout(
                    name,
                    nested_obj_name,
                    options,
                    current_value,
                    icon_path,
                    True,
                    tooltip,
                    option_tooltips,
                    nested_option_config,
                    depth=current_depth + 1,  # 子嵌套深度+1
                )
                self.option_area_layout.insertLayout(insert_index, v_layout)
                insert_index += 1

                # 仅在递归模式下加载子嵌套（初始加载时）
                # 用户交互时由信号自动触发，不需要在这里重复调用
                if recursive:
                    for i in range(v_layout.count()):
                        item = v_layout.itemAt(i)
                        widget = item.widget() if item else None
                        if widget and isinstance(widget, (ComboBox, EditableComboBox)):
                            # 初始加载子嵌套（递归=True）
                            self._update_nested_options(
                                widget,
                                current_value or widget.currentText(),
                                recursive=True,
                            )
                            break
            else:
                # 普通下拉框
                name = nested_option_config.get("label", nested_option)
                options = self.Get_Task_List(interface, nested_option)
                icon_path = nested_option_config.get("icon", "")
                tooltip = nested_option_config.get("description", "")
                option_tooltips = {}
                for case in nested_option_config.get("cases", []):
                    option_tooltips[case["name"]] = case.get("description", "")

                # 创建嵌套选项布局（传递深度+1）
                v_layout = self._create_nested_option_layout(
                    name,
                    nested_obj_name,
                    options,
                    current_value,
                    icon_path,
                    False,
                    tooltip,
                    option_tooltips,
                    nested_option_config,
                    depth=current_depth + 1,  # 子嵌套深度+1
                )
                self.option_area_layout.insertLayout(insert_index, v_layout)
                insert_index += 1

                # 仅在递归模式下加载子嵌套（初始加载时）
                # 用户交互时由信号自动触发，不需要在这里重复调用
                if recursive:
                    for i in range(v_layout.count()):
                        item = v_layout.itemAt(i)
                        widget = item.widget() if item else None
                        if widget and isinstance(widget, (ComboBox, EditableComboBox)):
                            # 初始加载子嵌套（递归=True）
                            self._update_nested_options(
                                widget,
                                current_value or widget.currentText(),
                                recursive=True,
                            )
                            break

    def _create_nested_option_layout(
        self,
        name: str,
        obj_name: str,
        options: list,
        current: str | None,
        icon_path: str,
        editable: bool,
        tooltip: str,
        option_tooltips: dict,
        option_config: dict,
        depth: int = 1,
    ) -> QVBoxLayout:
        """创建嵌套选项的布局

        Args:
            depth: 嵌套深度（保留参数以保持接口兼容，但不再用于UI显示）

        Returns:
            创建的垂直布局
        """
        v_layout = QVBoxLayout()
        v_layout.setObjectName(f"{obj_name}_layout")

        # 创建水平布局（不再添加缩进，所有选项左对齐）
        h_layout = QHBoxLayout()
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_layout.setSpacing(5)

        # 创建图标标签（只在有图标时添加）
        icon = self.icon_loader.load_icon(icon_path, size=16)
        if not icon.isNull():
            icon_label = BodyLabel()
            icon_label.setPixmap(icon.pixmap(16, 16))
            h_layout.addWidget(icon_label)

        # 创建文本标签（嵌套选项不加粗）
        text_label = BodyLabel(name)

        # 添加到水平布局（不添加 stretch，紧贴左边）
        h_layout.addWidget(text_label)

        v_layout.addLayout(h_layout)

        # 创建ComboBox
        if editable:
            combo_box = EditableComboBox()
        else:
            combo_box = ComboBox()

        combo_box.setObjectName(obj_name)
        combo_box.addItems(options)

        if current:
            combo_box.setCurrentText(current)

        # 存储配置信息
        combo_box.setProperty("option_config", option_config)
        combo_box.setProperty("parent_option_name", obj_name)
        combo_box.setProperty("is_nested", True)
        combo_box.setProperty("nested_depth", depth)  # 存储嵌套深度

        v_layout.addWidget(combo_box)

        # 设置工具提示
        if tooltip:
            text_label.setToolTip(tooltip)
            text_label.installEventFilter(
                ToolTipFilter(text_label, 0, ToolTipPosition.TOP)
            )

        if option_tooltips:
            if current and current in option_tooltips:
                combo_box.setToolTip(option_tooltips[current])
            combo_box.installEventFilter(
                ToolTipFilter(combo_box, 0, ToolTipPosition.TOP)
            )
            combo_box.currentTextChanged.connect(
                lambda text: combo_box.setToolTip(option_tooltips.get(text, ""))
            )
        elif tooltip:
            combo_box.setToolTip(tooltip)
            combo_box.installEventFilter(
                ToolTipFilter(combo_box, 0, ToolTipPosition.TOP)
            )

        # 连接信号（支持递归嵌套）
        combo_box.currentTextChanged.connect(
            lambda text: self._on_combox_changed(combo_box, text)
        )

        # 注意：不在这里自动加载子嵌套选项
        # 子嵌套的加载由以下两种情况触发：
        # 1. _update_nested_options 会在创建完所有同级嵌套后，由用户交互触发子嵌套加载
        # 2. _add_options_with_order 的递归逻辑会主动调用来加载初始子嵌套
        # 如果在这里自动加载，会导致重复添加

        return v_layout

    def _remove_nested_options(self, parent_option_name: str):
        """递归移除指定父级选项的所有嵌套选项（包括多层嵌套）

        Args:
            parent_option_name: 父级选项的objectName
        """
        # 收集需要移除的布局索引(从后往前,避免索引变化)
        to_remove = []
        nested_items_to_check = []  # 需要递归检查的嵌套项

        for i in range(self.option_area_layout.count()):
            item = self.option_area_layout.itemAt(i)
            if item and item.layout():
                layout_name = item.layout().objectName()
                # 检查是否是该父级的直接嵌套选项
                if layout_name.startswith(f"{parent_option_name}__nested__"):
                    to_remove.append(i)
                    # 提取嵌套选项的名称，用于递归查找它的子嵌套
                    # 格式: parent__nested__option_layout -> parent__nested__option
                    if layout_name.endswith("_layout"):
                        nested_name = layout_name[:-7]  # 移除 "_layout"
                        nested_items_to_check.append(nested_name)

        # 递归移除子嵌套选项
        for nested_name in nested_items_to_check:
            self._remove_nested_options(nested_name)

        # 从后往前移除当前层级的嵌套选项
        for i in reversed(to_remove):
            item = self.option_area_layout.takeAt(i)
            if item and item.layout():
                # 递归删除布局中的所有控件
                self._clear_layout(item.layout())
                item.layout().deleteLater()

    def _clear_layout(self, layout):
        """递归清空布局中的所有控件"""
        if layout is None:
            return
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())

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

        # 连接值变化信号，自动保存选项
        line_edit.textChanged.connect(lambda: self._save_current_options())

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

        # 连接值变化信号，自动保存选项
        switch.checkedChanged.connect(lambda: self._save_current_options())

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
