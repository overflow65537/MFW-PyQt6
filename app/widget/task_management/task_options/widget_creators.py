"""控件创建器模块

提供各种选项控件的创建方法。
"""

from qfluentwidgets import (
    ComboBox, EditableComboBox, LineEdit, SwitchButton, BodyLabel,
    ToolTipFilter, ToolTipPosition
)
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout
from app.utils.logger import logger
from ._mixin_base import MixinBase


class WidgetCreatorsMixin(MixinBase):
    """控件创建器 Mixin
    
    继承自 MixinBase，获得通用的类型提示，避免 Pylance 报错。
    运行时 `self` 指向 OptionWidget 实例，可访问其所有属性/方法。
    
    提供各种选项控件的创建方法：
    - 下拉框选项（支持嵌套）
    - 文本输入框
    - 开关按钮
    - 多输入项
    
    依赖的宿主类方法/属性：
    - self.option_area_layout
    - self.icon_loader
    - self._save_current_options
    - self._on_combox_changed (在 NestedOptionsMixin 中)
    """
    
    def _add_combox_option(
        self,
        name,
        obj_name,
        options,
        current=None,
        icon_path="",
        editable=False,
        tooltip="",
        option_tooltips=None,
        option_config=None,
        skip_initial_nested=False,
        block_signals=False,
        return_widget=False,
    ):
        """添加下拉选项
        
        Args:
            name: 显示名称
            obj_name: 对象名称（用于保存）
            options: 选项列表
            current: 当前值
            icon_path: 图标路径
            editable: 是否可编辑
            tooltip: 工具提示
            option_tooltips: 各选项的工具提示字典
            option_config: 选项配置（用于嵌套选项）
            skip_initial_nested: 是否跳过初始嵌套选项加载
            block_signals: 是否阻塞信号
            return_widget: 是否返回创建的控件
            
        Returns:
            ComboBox 或 None（根据 return_widget）
        """
        v_layout = QVBoxLayout()
        
        # 创建水平布局用于放置图标和标签
        h_layout = QHBoxLayout()
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_layout.setSpacing(5)
        
        # 创建图标标签（只在有图标时添加）
        icon = self.icon_loader.load_icon(icon_path, size=16)
        if not icon.isNull():
            from qfluentwidgets import IconWidget
            icon_widget = IconWidget(icon)
            icon_widget.setFixedSize(16, 16)
            h_layout.addWidget(icon_widget)
        
        # 创建文本标签（主标题加粗）
        text_label = BodyLabel(name)
        text_label.setStyleSheet("font-weight: bold;")
        h_layout.addWidget(text_label)
        v_layout.addLayout(h_layout)
        
        # 创建下拉框
        if editable:
            combo_box = EditableComboBox()
        else:
            combo_box = ComboBox()
        
        combo_box.setObjectName(obj_name)
        combo_box.setMaximumWidth(400)
        v_layout.setObjectName(f"{obj_name}_layout")
        
        combo_box.addItems(options)
        
        # 存储选项配置到 combo_box
        if option_config:
            combo_box.setProperty("option_config", option_config)
        
        # 设置标签的工具提示
        if tooltip:
            text_label.setToolTip(tooltip)
            text_label.installEventFilter(
                ToolTipFilter(text_label, 0, ToolTipPosition.TOP)
            )
        
        # 设置下拉框的工具提示
        if option_tooltips and isinstance(option_tooltips, dict):
            current_text = combo_box.currentText()
            if current_text in option_tooltips:
                combo_box.setToolTip(option_tooltips[current_text])
                combo_box.installEventFilter(
                    ToolTipFilter(combo_box, 0, ToolTipPosition.TOP)
                )
            
            # 连接下拉框文本变化信号更新工具提示
            def update_tooltip(text):
                if text in option_tooltips:
                    combo_box.setToolTip(option_tooltips[text])
                else:
                    combo_box.setToolTip(tooltip)
            
            combo_box.currentTextChanged.connect(update_tooltip)
        elif tooltip:
            combo_box.setToolTip(tooltip)
            combo_box.installEventFilter(
                ToolTipFilter(combo_box, 0, ToolTipPosition.TOP)
            )
        
        # 设置当前值
        if current:
            combo_box.setCurrentText(current)
        
        # 连接值变化信号
        combo_box.currentTextChanged.connect(
            lambda text: self._on_combox_changed(combo_box, text)
        )
        
        v_layout.addWidget(combo_box)
        self.option_area_layout.addLayout(v_layout)
        
        if return_widget:
            return combo_box
    
    def _add_multi_input_option(
        self,
        option_name,
        option_config,
        item,
        parent_option_name=None,
        insert_index=None,
    ):
        """添加多输入项选项
        
        用于创建包含多个输入框的选项，如"自定义关卡"。
        
        Args:
            option_name: 选项名称
            option_config: 选项配置
            item: 当前任务项
            parent_option_name: 父级选项名
            insert_index: 插入位置索引
        """
        saved_data = item.task_option.get(option_name, {})
        main_description = option_config.get("description", "")
        main_label = option_config.get("label", option_name)
        icon_path = option_config.get("icon", "")
        
        # 创建主布局
        main_layout = QVBoxLayout()
        if parent_option_name:
            main_layout.setObjectName(f"{parent_option_name}__nested__{option_name}_layout")
        
        # 创建主标题区域
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(5)
        
        # 添加图标（如果存在）
        icon = self.icon_loader.load_icon(icon_path, size=16)
        if not icon.isNull():
            from qfluentwidgets import IconWidget
            icon_widget = IconWidget(icon)
            icon_widget.setFixedSize(16, 16)
            title_layout.addWidget(icon_widget)
        
        # 添加主标题（加粗）
        title_label = BodyLabel(main_label)
        title_label.setStyleSheet("font-weight: bold;")
        title_layout.addWidget(title_label)
        
        main_layout.addLayout(title_layout)
        
        # 设置工具提示
        if main_description:
            title_label.setToolTip(main_description)
            title_label.installEventFilter(
                ToolTipFilter(title_label, 0, ToolTipPosition.TOP)
            )
        
        # 创建各个输入框
        need_save = False
        for input_config in option_config.get("inputs", []):
            input_name = input_config.get("name", "")
            input_label = input_config.get("label", input_name)
            input_type = input_config.get("type", "str")
            default_value = input_config.get("default", "")
            
            # 获取保存的值
            if isinstance(saved_data, dict):
                saved_value = saved_data.get(input_name, default_value)
            else:
                saved_value = default_value
                need_save = True
            
            # 创建输入框
            input_layout = QHBoxLayout()
            input_layout.setContentsMargins(0, 0, 0, 5)
            
            label = BodyLabel(input_label)
            input_layout.addWidget(label)
            
            line_edit = LineEdit()
            line_edit.setObjectName(f"{option_name}${input_name}")
            line_edit.setText(str(saved_value))
            line_edit.setProperty("pipeline_type", input_type)
            line_edit.textChanged.connect(lambda: self._save_current_options())
            
            input_layout.addWidget(line_edit)
            main_layout.addLayout(input_layout)
        
        # 如果修正了数据类型，立即保存
        if need_save:
            if option_name not in item.task_option:
                item.task_option[option_name] = {}
            self.service_coordinator.modify_task(item)
        
        # 添加到选项区域
        if insert_index is not None:
            self.option_area_layout.insertLayout(insert_index, main_layout)
        else:
            self.option_area_layout.addLayout(main_layout)
    
    def _add_lineedit_option(self, name, current, tooltip="", obj_name=""):
        """添加文本输入选项
        
        Args:
            name: 显示名称
            current: 当前值
            tooltip: 工具提示
            obj_name: 对象名称
        """
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
        line_edit.textChanged.connect(lambda: self._save_current_options())
        self.option_area_layout.addLayout(v_layout)
    
    def _add_switch_option(self, name, current, tooltip="", obj_name=""):
        """添加开关选项
        
        Args:
            name: 显示名称
            current: 当前值（布尔）
            tooltip: 工具提示
            obj_name: 对象名称
        """
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
        switch.checkedChanged.connect(lambda: self._save_current_options())
        self.option_area_layout.addLayout(v_layout)
