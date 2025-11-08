"""控件工厂模块

负责创建各种类型的选项控件。
"""

import re
from typing import TYPE_CHECKING, Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QVBoxLayout,
    QHBoxLayout,
)
from qfluentwidgets import (
    ComboBox,
    EditableComboBox,
    BodyLabel,
    SwitchButton,
    ToolTipFilter,
    ToolTipPosition,
    LineEdit,
)

from app.utils.logger import logger

if TYPE_CHECKING:
    from .....core.core import TaskItem, ServiceCoordinator


class WidgetFactory:
    """控件工厂
    
    负责创建各种类型的选项控件:
    - 下拉框（普通/可编辑）
    - 文本输入框
    - 开关按钮
    - 多输入项控件
    """

    def __init__(
        self,
        service_coordinator: "ServiceCoordinator",
        option_area_layout: QVBoxLayout,
        icon_loader,
        save_options_func: Callable,
    ):
        self.service_coordinator = service_coordinator
        self.option_area_layout = option_area_layout
        self.icon_loader = icon_loader
        self.save_options = save_options_func

    def add_combox_option(
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
        on_changed_callback: Callable | None = None,
        current_task: "TaskItem | None" = None,
    ):
        """添加下拉选项

        Args:
            option_config: 选项配置字典,包含 cases 信息,用于支持嵌套选项
            skip_initial_nested: 是否跳过初始嵌套选项加载（当使用 _add_options_with_order 时为 True）
            block_signals: 是否阻塞信号（初始化加载时为 True，避免 currentTextChanged 触发重复加载）
            return_widget: 是否返回创建的ComboBox控件（用于初始化时创建嵌套选项）
            on_changed_callback: 值改变时的回调函数
            current_task: 当前任务对象
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
        combo_box.setMaximumWidth(400)  # 限制最大宽度
        v_layout.setObjectName(f"{obj_name}_layout")

        combo_box.addItems(options)

        # 存储选项配置到 combo_box,用于嵌套选项处理
        if option_config:
            combo_box.setProperty("option_config", option_config)
            combo_box.setProperty("parent_option_name", obj_name)
        
        # 存储当前任务
        if current_task:
            combo_box.setProperty("current_task", current_task)

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

        # 连接值变化信号
        if on_changed_callback:
            combo_box.currentTextChanged.connect(
                lambda text: on_changed_callback(combo_box, text)
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
        if option_config and not skip_initial_nested and on_changed_callback:
            # 这里需要调用嵌套选项处理器
            pass  # 由外部调用者处理

        self.option_area_layout.addLayout(v_layout)

        # 如果需要返回控件，返回创建的ComboBox
        if return_widget:
            return combo_box

    def add_lineedit_option(
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
        line_edit.textChanged.connect(lambda: self.save_options())

        self.option_area_layout.addLayout(v_layout)

    def add_switch_option(
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
        switch.checkedChanged.connect(lambda: self.save_options())

        self.option_area_layout.addLayout(v_layout)

    def add_multi_input_option(
        self,
        option_name: str,
        option_config: dict,
        item: "TaskItem",
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
            current_value = saved_data.get(input_name, default_value)

            if pipeline_type == "int" and isinstance(current_value, str):
                try:
                    current_value = int(current_value) if current_value else 0
                    saved_data[input_name] = current_value
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

                def create_validator(pattern, edit_widget):
                    def validate():
                        text = edit_widget.text()
                        if text and not re.match(pattern, text):
                            edit_widget.setStyleSheet("border: 1px solid red;")
                        else:
                            edit_widget.setStyleSheet("")

                    return validate

                line_edit.textChanged.connect(create_validator(verify_pattern, line_edit))

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
            line_edit.textChanged.connect(lambda: self.save_options())

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
