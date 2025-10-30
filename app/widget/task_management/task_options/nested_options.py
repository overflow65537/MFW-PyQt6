"""嵌套选项处理模块

提供嵌套选项的动态加载和管理。
"""

from qfluentwidgets import ComboBox, EditableComboBox, BodyLabel
from PySide6.QtWidgets import QVBoxLayout
from app.utils.logger import logger
from ._mixin_base import MixinBase


class NestedOptionsMixin(MixinBase):
    """嵌套选项处理 Mixin
    
    继承自 MixinBase，获得通用的类型提示，避免 Pylance 报错。
    运行时 `self` 指向 OptionWidget 实例，可访问其所有属性/方法。
    
    提供嵌套选项的动态处理功能：
    - 下拉框值改变时触发嵌套选项更新
    - 递归创建嵌套选项布局
    - 移除旧的嵌套选项
    
    依赖的宿主类方法/属性：
    - self.option_area_layout
    - self._save_current_options
    - self._add_combox_option (在 WidgetCreatorsMixin 中)
    - self._add_multi_input_option (在 WidgetCreatorsMixin 中)
    - self.Get_Task_List (在 TaskOptionsMixin 中)
    - self.current_task
    """
    
    def _on_combox_changed(self, combo_box, text):
        """下拉框值改变时的回调
        
        Args:
            combo_box: ComboBox 控件
            text: 新选中的文本
        """
        # 先移除旧的嵌套选项
        parent_option_name = combo_box.objectName()
        self._remove_nested_options(parent_option_name)
        
        # 更新嵌套选项
        self._update_nested_options(combo_box, text, recursive=True)
        
        # 保存配置
        self._save_current_options()
    
    def _update_nested_options(self, combo_box, selected_case, recursive=True):
        """更新嵌套选项
        
        根据父选项的当前选中值，动态加载对应的嵌套选项。
        
        Args:
            combo_box: 父级 ComboBox 控件
            selected_case: 选中的 case 名称
            recursive: 是否递归处理嵌套的嵌套选项
        """
        option_config = combo_box.property("option_config")
        if not option_config:
            return
        
        parent_option_name = combo_box.objectName()
        
        # 查找选中的 case 配置
        selected_case_config = None
        for case in option_config.get("cases", []):
            if case.get("name") == selected_case:
                selected_case_config = case
                break
        
        if not selected_case_config:
            return
        
        # 获取嵌套选项列表
        nested_options = selected_case_config.get("option", [])
        if not nested_options:
            return
        
        # 获取父选项布局的索引
        parent_layout_name = f"{parent_option_name}_layout"
        parent_index = -1
        for i in range(self.option_area_layout.count()):
            item = self.option_area_layout.itemAt(i)
            if item and item.layout() and item.layout().objectName() == parent_layout_name:
                parent_index = i
                break
        
        if parent_index == -1:
            logger.warning(f"未找到父选项布局: {parent_layout_name}")
            return
        
        # 获取 interface 配置
        interface = getattr(self.task, "interface", None)
        if not interface:
            return
        
        # 在父选项后面插入嵌套选项
        insert_index = parent_index + 1
        
        for nested_option_name in nested_options:
            nested_option_config = interface["option"].get(nested_option_name)
            if not nested_option_config:
                logger.warning(f"嵌套选项配置不存在: {nested_option_name}")
                continue
            
            # 判断嵌套选项类型
            option_type = nested_option_config.get("type", "select")
            
            if option_type == "multi_input":
                # 多输入项类型
                self._add_multi_input_option(
                    nested_option_name,
                    nested_option_config,
                    self.current_task,
                    parent_option_name=parent_option_name,
                    insert_index=insert_index,
                )
            else:
                # 下拉框类型
                current_value = self.current_task.task_option.get(nested_option_name, None)
                
                self._create_nested_option_layout(
                    name=nested_option_config.get("label", nested_option_name),
                    obj_name=nested_option_name,
                    options=self.Get_Task_List(interface, nested_option_name),
                    current=current_value,
                    icon_path=nested_option_config.get("icon", ""),
                    editable=False,
                    tooltip=nested_option_config.get("description", ""),
                    option_tooltips={
                        case["name"]: case.get("description", "")
                        for case in nested_option_config.get("cases", [])
                    },
                    option_config=nested_option_config,
                    depth=1,
                    insert_index=insert_index,
                )
            
            insert_index += 1
    
    def _create_nested_option_layout(
        self,
        name,
        obj_name,
        options,
        current,
        icon_path,
        editable,
        tooltip,
        option_tooltips,
        option_config,
        depth=1,
        insert_index: int | None = None,
    ):
        """创建嵌套选项布局
        
        与普通选项类似，但使用特殊的命名约定标记为嵌套选项。
        
        Args:
            depth: 嵌套深度（用于缩进）
            insert_index: 插入位置索引（作为嵌套选项时使用）
            
        Returns:
            创建的垂直布局
        """
        # 嵌套选项使用特殊的 objectName 格式
        # 例如: parent__nested__child
        nested_obj_name = f"{obj_name}__nested__{obj_name}"
        
        # 创建布局（带缩进）
        v_layout = QVBoxLayout()
        v_layout.setObjectName(f"{nested_obj_name}_layout")
        v_layout.setContentsMargins(depth * 20, 0, 0, 0)  # 左侧缩进
        
        # 创建标签
        label = BodyLabel(name)
        label.setStyleSheet("font-weight: bold;")
        v_layout.addWidget(label)
        
        # 创建下拉框
        if editable:
            combo = EditableComboBox()
        else:
            combo = ComboBox()
        
        combo.setObjectName(nested_obj_name)
        combo.setMaximumWidth(400)
        combo.addItems(options)
        
        # 存储配置
        if option_config:
            combo.setProperty("option_config", option_config)
        
        # 设置当前值
        if current:
            combo.setCurrentText(current)
        
        # 连接信号
        combo.currentTextChanged.connect(
            lambda text: self._on_combox_changed(combo, text)
        )
        
        v_layout.addWidget(combo)
        
        # 添加到选项区域（支持指定插入位置）
        if insert_index is not None:
            self.option_area_layout.insertLayout(insert_index, v_layout)
        else:
            self.option_area_layout.addLayout(v_layout)
        
        return v_layout

    
    def _remove_nested_options(self, parent_option_name):
        """移除指定父选项的所有嵌套选项
        
        Args:
            parent_option_name: 父选项名称
        """
        # 遍历布局，找到所有以 parent__nested__ 开头的布局并移除
        nested_prefix = f"{parent_option_name}__nested__"
        
        i = 0
        while i < self.option_area_layout.count():
            item = self.option_area_layout.itemAt(i)
            if item and item.layout():
                layout_name = item.layout().objectName()
                if layout_name.startswith(nested_prefix):
                    # 移除此布局
                    self.option_area_layout.takeAt(i)
                    self._clear_layout(item.layout())
                    continue
            i += 1
