"""嵌套选项处理模块

负责处理选项的嵌套关系，包括动态显示/隐藏子选项。
"""

from typing import TYPE_CHECKING, Callable

from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout
from qfluentwidgets import (
    ComboBox,
    EditableComboBox,
    BodyLabel,
    ToolTipFilter,
    ToolTipPosition,
)

from app.utils.logger import logger

if TYPE_CHECKING:
    from .....core.core import ServiceCoordinator


class NestedOptionHandler:
    """嵌套选项处理器
    
    负责:
    - 根据父选项的值动态显示/隐藏子选项
    - 创建嵌套选项的 UI 布局
    - 清理不再需要的嵌套选项
    """

    def __init__(
        self,
        service_coordinator: "ServiceCoordinator",
        option_area_layout: QVBoxLayout,
        icon_loader,
        get_task_list_func: Callable,
        save_options_func: Callable,
    ):
        self.service_coordinator = service_coordinator
        self.option_area_layout = option_area_layout
        self.icon_loader = icon_loader
        self.get_task_list = get_task_list_func
        self.save_options = save_options_func

    def update_nested_options(
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
        self.remove_nested_options(parent_option_name)

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

        # 获取 interface 配置
        interface = self.service_coordinator.task.interface
        if not interface:
            logger.warning("未找到任务接口配置")
            return

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

        # 导入需要的模块
        from widget_factory import WidgetFactory
        
        # 获取当前任务
        current_task = combo_box.property("current_task")

        # 添加嵌套选项
        for nested_option in nested_options:
            nested_option_config = interface["option"].get(nested_option)
            if not nested_option_config:
                continue

            # 标记为嵌套选项
            nested_obj_name = f"{parent_option_name}__nested__{nested_option}"

            # 获取当前任务的保存值
            current_value = None
            if current_task:
                current_value = current_task.task_option.get(nested_option, None)

            # 根据选项类型添加控件
            option_type = nested_option_config.get("type", "select")

            if "inputs" in nested_option_config and isinstance(
                nested_option_config.get("inputs"), list
            ):
                # 多输入项类型（例如: 自定义关卡）
                if current_task:
                    # 需要从外部传入 WidgetFactory 的 add_multi_input_option 方法
                    factory = WidgetFactory(
                        self.service_coordinator,
                        self.option_area_layout,
                        self.icon_loader,
                        self.save_options,
                    )
                    factory.add_multi_input_option(
                        nested_option,
                        nested_option_config,
                        current_task,
                        parent_option_name=parent_option_name,
                        insert_index=insert_index,
                    )
                    insert_index += 1
            elif option_type == "input":
                # 可编辑下拉框
                name = nested_option_config.get("label", nested_option)
                options = self.get_task_list(interface, nested_option)
                icon_path = nested_option_config.get("icon", "")
                tooltip = nested_option_config.get("description", "")
                option_tooltips = {}
                for case in nested_option_config.get("cases", []):
                    option_tooltips[case["name"]] = case.get("description", "")

                # 创建嵌套选项布局（传递深度+1）
                v_layout = self.create_nested_option_layout(
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
                    current_task=current_task,
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
                            self.update_nested_options(
                                widget,
                                current_value or widget.currentText(),
                                recursive=True,
                            )
                            break
            else:
                # 普通下拉框
                name = nested_option_config.get("label", nested_option)
                options = self.get_task_list(interface, nested_option)
                icon_path = nested_option_config.get("icon", "")
                tooltip = nested_option_config.get("description", "")
                option_tooltips = {}
                for case in nested_option_config.get("cases", []):
                    option_tooltips[case["name"]] = case.get("description", "")

                # 创建嵌套选项布局（传递深度+1）
                v_layout = self.create_nested_option_layout(
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
                    current_task=current_task,
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
                            self.update_nested_options(
                                widget,
                                current_value or widget.currentText(),
                                recursive=True,
                            )
                            break

    def create_nested_option_layout(
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
        current_task=None,
    ) -> QVBoxLayout:
        """创建嵌套选项的布局

        Args:
            depth: 嵌套深度（保留参数以保持接口兼容，但不再用于UI显示）
            current_task: 当前任务对象

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
        combo_box.setMaximumWidth(400)  # 限制最大宽度
        combo_box.addItems(options)

        if current:
            combo_box.setCurrentText(current)

        # 存储配置信息
        combo_box.setProperty("option_config", option_config)
        combo_box.setProperty("parent_option_name", obj_name)
        combo_box.setProperty("is_nested", True)
        combo_box.setProperty("nested_depth", depth)  # 存储嵌套深度
        combo_box.setProperty("current_task", current_task)  # 存储当前任务

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
        def on_changed(text):
            self.update_nested_options(combo_box, text, recursive=False)
            self.save_options()

        combo_box.currentTextChanged.connect(on_changed)

        return v_layout

    def remove_nested_options(self, parent_option_name: str):
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
            self.remove_nested_options(nested_name)

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
