"""
选项项组件
单个选项的独立组件，支持 combobox 和 lineedit 类型，以及子选项
"""
# type: ignore[attr-defined]
from typing import Dict, Any, Optional, List, Tuple
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from PySide6.QtCore import Qt, Signal
from qfluentwidgets import ComboBox, LineEdit, BodyLabel, ToolTipFilter, SwitchButton
import re
from app.utils.logger import logger


class OptionItemWidget(QWidget):
    """
    选项项组件
    一个独立的选项组件，包含标题和对应的控件（combobox 或 lineedit）
    支持子选项，可以递归获取选项配置
    """
    
    # 信号：选项值改变时发出
    option_changed = Signal(str, object)  # key, value
    
    def __init__(self, key: str, config: Dict[str, Any], parent: Optional[QWidget] = None):
        """
        初始化选项项组件
        
        :param key: 选项的键名
        :param config: 选项配置字典，包含 label, type, description, options/inputs 等
        :param parent: 父组件
        """
        super().__init__(parent)
        self.key = key
        self.config = config
        self.config_type = config.get("type", "combobox")
        self.child_options: Dict[str, 'OptionItemWidget'] = {}  # 子选项组件字典
        self._child_value_map: Dict[str, List[str]] = {}
        self._child_name_map: Dict[Tuple[str, str], str] = {}
        self.current_value: Any = None  # 当前选中的值
        inputs_value = self.config.get("inputs")
        self._single_input_mode = (
            self.config_type == "lineedit"
            and isinstance(inputs_value, list)
            and len(inputs_value) == 1
            and self.config.get("single_input", False)
        )
        
        self._init_ui()
        self._init_config()
    
    def _init_ui(self):
        """初始化UI"""
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(5, 5, 5, 5)
        self.main_layout.setSpacing(5)
        
        # 先创建子选项容器（用于存放子选项）
        # 必须在创建控件之前创建，因为 _create_combobox 中可能会调用 add_child_option
        self.children_container = QWidget()
        self.children_layout = QVBoxLayout(self.children_container)
        self.children_layout.setContentsMargins(0, 0, 0, 0)
        
        # 根据类型创建对应的控件
        # switch 类型的布局不同，需要特殊处理
        if self.config_type == "switch":
            self._create_switch()
        else:
            # 其他类型：标题在上，组件在下
            # 创建标签
            label_text = self.config.get("label", self.key)
            if not self._single_input_mode:
                self.label = BodyLabel(label_text)
                self.main_layout.addWidget(self.label)
                
                # 添加 tooltip
                if "description" in self.config:
                    filter = ToolTipFilter(self.label)
                    self.label.installEventFilter(filter)
                    self.label.setToolTip(self.config["description"])
            
            # 创建对应的控件
            if self.config_type == "combobox":
                self._create_combobox()
            elif self.config_type == "lineedit":
                self._create_lineedit()
            else:
                logger.warning(f"不支持的选项类型: {self.config_type}")
        
        # 将子选项容器添加到主布局
        self.main_layout.addWidget(self.children_container)
        
        # 初始状态隐藏子选项容器（将在 _init_config 中根据是否有子选项来设置可见性）
        self.children_container.setVisible(False)
    
    def _create_combobox(self):
        """创建下拉框"""
        self.control_widget = ComboBox()
        
        # 保存选项映射关系 (label -> name 和 name -> label)
        self._option_map = {}  # label -> name
        self._reverse_option_map = {}  # name -> label
        
        # 添加选项
        options = self.config.get("options", [])
        for option in options:
            if isinstance(option, dict):
                label = option.get("label", "")
                name = option.get("name", label)
            else:
                label = str(option)
                name = label
            
            self.control_widget.addItem(label)
            self._option_map[label] = name
            self._reverse_option_map[name] = label
        
        self.main_layout.addWidget(self.control_widget)
        
        self._preload_child_options()
        
        # 连接信号（在预创建子选项后）
        self.control_widget.currentTextChanged.connect(self._on_combobox_changed)
    
    def _create_switch(self):
        """创建开关按钮（标题和开关在同一行）"""
        # 创建水平布局容器，用于放置标题和开关
        switch_container = QWidget()
        switch_layout = QHBoxLayout(switch_container)
        switch_layout.setContentsMargins(0, 10, 0, 10)
        switch_layout.setSpacing(10)
        
        # 创建标签（标题）
        label_text = self.config.get("label", self.key)
        self.label = BodyLabel(label_text)
        switch_layout.addWidget(self.label)
        
        # 添加 tooltip 到标签
        if "description" in self.config:
            filter = ToolTipFilter(self.label)
            self.label.installEventFilter(filter)
            self.label.setToolTip(self.config["description"])
        
        # 添加弹性空间，让开关靠右对齐
        switch_layout.addStretch()
        
        # 创建开关按钮
        self.control_widget = SwitchButton(parent=self)
        
        # 保存选项映射关系
        self._option_map = {"是": "Yes", "否": "No"}
        self._reverse_option_map = {"Yes": "是", "No": "否"}
        
        # switch 类型固定为 Yes 和 No 两个选项
        # 设置开关按钮的文本标签
        self.control_widget.setOnText("是")
        self.control_widget.setOffText("否")
        
        # 添加 tooltip 到开关按钮
        if "description" in self.config:
            filter = ToolTipFilter(self.control_widget)
            self.control_widget.installEventFilter(filter)
            self.control_widget.setToolTip(self.config["description"])
        
        # 将开关按钮添加到水平布局
        switch_layout.addWidget(self.control_widget)
        
        # 将整个容器添加到主布局
        self.main_layout.addWidget(switch_container)
        
        self._preload_child_options()
        
        # 连接信号（在预创建子选项后）
        self.control_widget.checkedChanged.connect(self._on_switch_changed)
    
    def _create_lineedit(self):
        """创建输入框"""
        inputs = self.config.get("inputs", [])

        # 单输入模式：只渲染一个输入框，避免重复的标题/描述
        if self._single_input_mode and inputs:
            input_item = inputs[0]
            input_name = input_item.get("name", self.key)
            self.control_widget = {}
            line_edit = LineEdit()

            label_text = input_item.get("label") or self.config.get("label", self.key)
            if label_text:
                single_label = BodyLabel(label_text)
                self.main_layout.addWidget(single_label)

            # 设置默认值
            if "default" in input_item:
                line_edit.setText(str(input_item["default"]))

            # 设置占位提示（优先使用 input label）
            placeholder = input_item.get("label") or self.config.get("label", "")
            if placeholder:
                line_edit.setPlaceholderText(placeholder)

            # 添加验证规则
            if "verify" in input_item:
                verify_pattern = input_item["verify"]
                try:
                    def create_validator(pattern):
                        def validate(text: str):
                            if text and not re.match(pattern, text):
                                line_edit.setError(True)  # type: ignore[attr-defined]
                            else:
                                line_edit.setError(False)  # type: ignore[attr-defined]
                        return validate

                    line_edit.textChanged.connect(create_validator(verify_pattern))
                except Exception as e:
                    logger.error(f"设置输入验证规则失败: {verify_pattern}, 错误: {e}")

            # 添加 tooltip
            description = input_item.get("description") or self.config.get("description")
            if description:
                filter = ToolTipFilter(line_edit)
                line_edit.installEventFilter(filter)
                line_edit.setToolTip(description)

            line_edit.textChanged.connect(
                lambda text, name=input_name: self._on_lineedit_changed(name, text)
            )

            self.control_widget[input_name] = line_edit
            self.main_layout.addWidget(line_edit)
        elif "inputs" in self.config:
            self.control_widget = {}  # 字典存储多个输入框
            inputs = self.config.get("inputs", [])
            
            for input_item in inputs:
                input_name = input_item.get("name", "")
                input_label_text = input_item.get("label", input_name)
                
                # 创建输入项容器
                input_container = QVBoxLayout()
                input_container.setContentsMargins(10, 5, 10, 5)
                
                # 创建标签
                input_label = BodyLabel(input_label_text)
                input_container.addWidget(input_label)
                
                # 创建输入框
                line_edit = LineEdit()
                
                # 设置默认值
                if "default" in input_item:
                    line_edit.setText(str(input_item["default"]))
                
                # 添加验证规则
                if "verify" in input_item:
                    verify_pattern = input_item["verify"]
                    try:
                        def create_validator(pattern):
                            def validate(text: str):
                                if text and not re.match(pattern, text):
                                    line_edit.setError(True)  # type: ignore[attr-defined]
                                else:
                                    line_edit.setError(False)  # type: ignore[attr-defined]
                            return validate

                        line_edit.textChanged.connect(create_validator(verify_pattern))
                    except Exception as e:
                        logger.error(f"设置输入验证规则失败: {verify_pattern}, 错误: {e}")
                
                # 添加 tooltip
                if "description" in input_item:
                    filter = ToolTipFilter(line_edit)
                    line_edit.installEventFilter(filter)
                    line_edit.setToolTip(input_item["description"])
                
                input_container.addWidget(line_edit)
                self.main_layout.addLayout(input_container)
                
                # 连接信号
                line_edit.textChanged.connect(
                    lambda text, name=input_name: self._on_lineedit_changed(name, text)
                )
                
                self.control_widget[input_name] = line_edit
        else:
            # 单个输入框
            self.control_widget = LineEdit()
            
            # 设置默认值
            if "default" in self.config:
                self.control_widget.setText(str(self.config["default"]))
            
            # 添加验证规则
            if "verify" in self.config:
                verify_pattern = self.config["verify"]
                try:
                    def create_validator(pattern):
                        def validate(text: str):
                            if text and not re.match(pattern, text):
                                self.control_widget.setError(True)  # type: ignore[attr-defined]
                            else:
                                self.control_widget.setError(False)  # type: ignore[attr-defined]
                        return validate
                    
                    self.control_widget.textChanged.connect(create_validator(verify_pattern))
                except Exception as e:
                    logger.error(f"设置输入验证规则失败: {verify_pattern}, 错误: {e}")
            
            # 添加 tooltip
            if "description" in self.config:
                filter = ToolTipFilter(self.control_widget)
                self.control_widget.installEventFilter(filter)
                self.control_widget.setToolTip(self.config["description"])
            
            # 连接信号
            self.control_widget.textChanged.connect(
                lambda text: self._on_lineedit_changed(None, text)
            )
            
            self.main_layout.addWidget(self.control_widget)
    
    def _init_config(self):
        """初始化配置值"""
        if self.config_type == "combobox":
            current_label = self.control_widget.currentText()
            self.current_value = self._option_map.get(current_label, current_label)
            # 触发初始子选项显示
            self._update_children_visibility(self.current_value)
        elif self.config_type == "switch":
            # switch 类型：checked -> "Yes", unchecked -> "No"
            is_checked = self.control_widget.isChecked()
            self.current_value = "Yes" if is_checked else "No"
            # 触发初始子选项显示
            self._update_children_visibility(self.current_value)
        elif self.config_type == "lineedit":
            if isinstance(self.control_widget, dict):
                # 多输入框类型
                self.current_value = {
                    name: widget.text() for name, widget in self.control_widget.items()
                }
            else:
                # 单个输入框
                self.current_value = self.control_widget.text()
    
    def _on_combobox_changed(self, label: str):
        """下拉框值改变处理"""
        # 获取实际值（name）
        actual_value = self._option_map.get(label, label)
        self.current_value = actual_value
        
        # 处理子选项显示/隐藏
        self._update_children_visibility(actual_value)
        
        # 发出信号
        self.option_changed.emit(self.key, self.current_value)
    
    def _on_switch_changed(self, checked: bool):
        """开关按钮值改变处理"""
        # switch 类型：checked -> "Yes", unchecked -> "No"
        actual_value = "Yes" if checked else "No"
        self.current_value = actual_value
        
        # 处理子选项显示/隐藏
        self._update_children_visibility(actual_value)
        
        # 发出信号
        self.option_changed.emit(self.key, self.current_value)
    
    def _on_lineedit_changed(self, input_name: Optional[str], text: str):
        """输入框值改变处理"""
        if isinstance(self.control_widget, dict):
            # 多输入框类型
            if input_name:
                self.current_value[input_name] = text
        else:
            # 单个输入框
            self.current_value = text
        
        # 发出信号
        self.option_changed.emit(self.key, self.current_value)
    
    def _update_children_visibility(self, selected_value: Any):
        """更新子选项的可见性"""
        children = self.config.get("children", {})
        selected_value_str = str(selected_value) if selected_value is not None else ""
        normalized_selected = selected_value_str.strip()

        logger.debug(
            f"更新子选项可见性: key={self.key}, selected_value={selected_value}, "
            f"selected_value_str={selected_value_str}, children_keys={list(children.keys())}"
        )

        for child_widget in self.child_options.values():
            child_widget.setVisible(False)

        matched_key = self._match_child_key(
            children, selected_value, selected_value_str, normalized_selected
        )

        if matched_key:
            logger.debug(f"找到匹配的子选项: matched_key={matched_key}")
            if matched_key not in self._child_value_map:
                self.add_child_option(matched_key, children.get(matched_key))

            visible_any = False
            for child_key in self._child_value_map.get(matched_key, []):
                child_widget = self.child_options.get(child_key)
                if child_widget:
                    child_widget.setVisible(True)
                    visible_any = True

            self.children_container.setVisible(visible_any)
            if visible_any:
                logger.debug("设置子选项容器可见")
        else:
            logger.debug("没有找到匹配的子选项，隐藏容器")
            self.children_container.setVisible(False)

    def _match_child_key(
        self,
        children: Dict[str, Any],
        selected_value: Any,
        selected_value_str: str,
        normalized_selected: str,
    ) -> Optional[str]:
        """匹配哪个子选项集合应该被显示"""
        if selected_value_str in children:
            logger.debug(f"精确匹配1: selected_value_str={selected_value_str}")
            return selected_value_str
        if selected_value in children:
            logger.debug(f"精确匹配2: selected_value={selected_value}")
            return selected_value
        if normalized_selected in children:
            logger.debug(f"精确匹配3: normalized_selected={normalized_selected}")
            return normalized_selected

        logger.debug(f"开始遍历匹配，标准化值={normalized_selected}")
        for key in children.keys():
            key_str = str(key)
            key_stripped = key_str.strip()
            logger.debug(
                f"比较键: key={repr(key)}, key_str={repr(key_str)}, key_stripped={repr(key_stripped)}"
            )
            if key_str == selected_value_str:
                logger.debug(f"匹配成功（原始值）: {key}")
                return key
            if key_stripped == normalized_selected:
                logger.debug(f"匹配成功（标准化值）: {key}")
                return key
            if str(key) == str(selected_value):
                logger.debug(f"匹配成功（字符串转换）: {key}")
                return key

        return None
    
    def _preload_child_options(self):
        for option_value, child_config in self.config.get("children", {}).items():
            self.add_child_option(option_value, child_config)

    def add_child_option(self, option_value: str, child_config: Any):
        """
        添加子选项组件
        
        :param option_value: 选项值（当下拉框选中此值时显示）
        :param child_config: 子选项配置，支持 dict 或 list
        """
        self._create_child_widgets_for_config(option_value, child_config)

    def _create_child_widgets_for_config(self, option_value: str, child_config: Any):
        if not child_config:
            return

        if isinstance(child_config, dict) and child_config.get("_type") == "multi":
            configs = child_config.get("items", [])
        elif isinstance(child_config, list):
            configs = child_config
        else:
            configs = [child_config]

        for index, config in enumerate(configs):
            self._create_single_child_widget(option_value, config, index)

    def _create_single_child_widget(self, option_value: str, child_config: Dict[str, Any], index: int):
        if not isinstance(child_config, dict):
            return

        child_copy = dict(child_config)
        child_name = child_copy.get("name") or child_copy.get("label") or f"{option_value}_{index}"
        child_copy["name"] = child_name

        if (option_value, child_name) in self._child_name_map:
            return

        child_key = f"{self.key}_child_{option_value}_{child_name}_{index}"
        child_widget = OptionItemWidget(child_key, child_copy, self)
        child_widget.setVisible(False)
        self.child_options[child_key] = child_widget
        self._child_value_map.setdefault(option_value, []).append(child_key)
        self._child_name_map[(option_value, child_name)] = child_key
        self.children_layout.addWidget(child_widget)

    def get_child_widgets_for_value(self, option_value: str) -> List['OptionItemWidget']:
        child_keys = self._child_value_map.get(option_value, [])
        return [self.child_options[key] for key in child_keys if key in self.child_options]

    def find_child_widget(self, option_value: str, child_config: Dict[str, Any]) -> Optional['OptionItemWidget']:
        child_name = child_config.get("name")
        if child_name:
            child_key = self._child_name_map.get((option_value, child_name))
            if child_key:
                return self.child_options.get(child_key)

        child_widgets = self.get_child_widgets_for_value(option_value)
        return child_widgets[0] if child_widgets else None
    
    def set_value(self, value: Any):
        """
        设置选项的值
        
        :param value: 要设置的值
        """
        if self.config_type == "combobox":
            # 如果传入的是字典，说明可能是配置对象，尝试提取 value
            if isinstance(value, dict):
                # 如果是字典但没有 value 字段，可能是输入框的值，不应该用在这里
                if "value" in value:
                    value = value["value"]
                else:
                    # 如果字典不是配置格式，可能是输入框的值，不应该用于 combobox
                    logger.warning(f"尝试为 combobox 设置字典值，将忽略: {value}")
                    return
            
            # 确保值是字符串或可哈希的类型
            if not isinstance(value, (str, int, float)) and value is not None:
                logger.warning(f"combobox 值类型不正确: {type(value)}, 值: {value}")
                return
            
            # 尝试从反向映射获取 label
            label = self._reverse_option_map.get(str(value), str(value))
            index = self.control_widget.findText(label)
            if index >= 0:
                self.control_widget.blockSignals(True)
                try:
                    self.control_widget.setCurrentIndex(index)
                    self.current_value = str(value)
                    self._update_children_visibility(str(value))
                finally:
                    self.control_widget.blockSignals(False)
        elif self.config_type == "switch":
            # 如果传入的是字典，说明可能是配置对象，尝试提取 value
            if isinstance(value, dict):
                if "value" in value:
                    value = value["value"]
                else:
                    logger.warning(f"尝试为 switch 设置字典值，将忽略: {value}")
                    return
            
            # 标准化值：处理各种可能的 Yes/No 变体
            value_str = str(value).strip()
            value_upper = value_str.upper()
            
            # 判断应该设置为 checked 还是 unchecked
            if value_upper in ["YES", "Y", "TRUE", "1", "ON", "是"]:
                target_checked = True
                target_value = "Yes"
            elif value_upper in ["NO", "N", "FALSE", "0", "OFF", "否"]:
                target_checked = False
                target_value = "No"
            else:
                logger.warning(f"switch 值类型不正确: {value}")
                return
            
            self.control_widget.blockSignals(True)
            try:
                self.control_widget.setChecked(target_checked)
                self.current_value = target_value
                self._update_children_visibility(target_value)
            finally:
                self.control_widget.blockSignals(False)
        elif self.config_type == "lineedit":
            if isinstance(self.control_widget, dict):
                # 多输入框类型
                if isinstance(value, dict):
                    for input_name, input_value in value.items():
                        if input_name in self.control_widget:
                            widget = self.control_widget[input_name]
                            widget.blockSignals(True)
                            try:
                                widget.setText(str(input_value))
                                self.current_value[input_name] = str(input_value)
                            finally:
                                widget.blockSignals(False)
            else:
                # 单个输入框
                self.control_widget.blockSignals(True)
                try:
                    self.control_widget.setText(str(value))
                    self.current_value = str(value)
                finally:
                    self.control_widget.blockSignals(False)
    
    def get_option(self) -> Dict[str, Any]:
        """
        获取当前选项的配置（递归获取子选项）
        
        :return: 选项配置字典，格式如 {"value": ..., "name": ..., "hidden": ..., "children": {...}}
        """
        result: Dict[str, Any] = {
            "value": self.current_value
        }
        
        # 递归获取子选项的配置
        children_config = {}
        
        # 对于 combobox 和 switch 类型，需要获取所有已创建的子选项配置
        if self.config_type in ["combobox", "switch"]:
            for option_value, child_widget in self.child_options.items():
                if child_widget:
                    # 获取子选项的配置
                    child_option = child_widget.get_option()
                    
                    # 获取子选项的 name（从结构字典中获取）
                    child_structure = self.config.get("children", {}).get(option_value, {})
                    child_name = child_structure.get("name", "")
                    
                    # 检查子选项是否被隐藏（当前选中值不等于此子选项的键值时，该子选项被隐藏）
                    is_hidden = not child_widget.isVisible()
                    
                    # 对于 lineedit 类型的子选项，如果只有 value，直接使用值
                    if child_widget.config_type == "lineedit" and "children" not in child_option:
                        # lineedit 类型保持简单值，但如果被隐藏需要转换为字典格式
                        if is_hidden:
                            children_config[option_value] = {
                                "value": child_option.get("value", ""),
                                "hidden": True
                            }
                        else:
                            children_config[option_value] = child_option.get("value", "")
                    else:
                        # 将子选项的 name 添加到配置中（用于从接口文件中获取具体选项）
                        if child_name:
                            child_option["name"] = child_name
                        # 添加隐藏属性（用于 runner 跳过已隐藏的配置）
                        if is_hidden:
                            child_option["hidden"] = True
                        children_config[option_value] = child_option
        
        # 如果有子选项配置，添加到结果中
        if children_config:
            result["children"] = children_config
        
        return result
    
    def get_simple_option(self) -> Any:
        """
        获取简单的选项值（不包含 children 结构）
        对于有子选项的情况，返回的值会包含子选项的值
        
        :return: 选项值
        """
        if self.config_type in ["combobox", "switch"]:
            # 如果有子选项，需要组装子选项的值
            children = self.config.get("children", {})
            if children and self.current_value in children:
                child_widget = self.child_options.get(self.current_value)
                if child_widget and child_widget.isVisible():
                    child_value = child_widget.get_simple_option()
                    return {
                        "value": self.current_value,
                        "children": {self.current_value: child_value}
                    }
            return self.current_value
        else:
            return self.current_value

