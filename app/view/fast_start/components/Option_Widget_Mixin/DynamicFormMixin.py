import json
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from PySide6.QtCore import Qt
from qfluentwidgets import ComboBox, LineEdit, BodyLabel


class DynamicFormMixin:
    """
    动态表单生成器的Mixin组件
    提供动态生成表单和管理配置的功能
    可以集成到OptionWidget等UI组件中
    """

    def __init__(self):
        """初始化动态表单Mixin"""
        # 确保这些属性被初始化
        if not hasattr(self, "widgets"):
            self.widgets = {}
        if not hasattr(self, "child_layouts"):
            self.child_layouts = {}
        if not hasattr(self, "current_config"):
            self.current_config = {}
        if not hasattr(self, "config_structure"):
            self.config_structure = {}
        if not hasattr(self, "parent_layout"):
            self.parent_layout = None
        # 添加子配置缓存，用于保存不同主选项对应的子配置
        if not hasattr(self, "child_config_cache"):
            self.child_config_cache = {}
        # 子选项配置缓存，按主选项键和主选项值组织
        if not hasattr(self, "option_subconfig_cache"):
            self.option_subconfig_cache = {}
        # 存储所有子选项容器的字典，格式：{main_key: {option_value: {layout: QVBoxLayout, widgets: {}, config: {}}}}}
        if not hasattr(self, "all_child_containers"):
            self.all_child_containers = {}

    def update_form(self, form_structure, config=None):
        """
        更新表单结构和配置
        :param form_structure: 新的表单结构定义
        :param config: 可选的配置对象，用于设置表单的当前选择
        """
        # 保存新的表单结构
        self.config_structure = form_structure

        # 清空当前配置
        self.current_config = {}
        self.widgets = {}
        self.child_layouts = {}

        # 清空父布局
        if self.parent_layout:
            self._clear_layout(self.parent_layout)
        else:
            raise ValueError("parent_layout 未设置")

        # 生成新表单
        for key, config_item in form_structure.items():
            if config_item["type"] == "combobox":
                self._create_combobox(
                    key, config_item, self.parent_layout, self.current_config
                )
            elif config_item["type"] == "lineedit":
                self._create_lineedit(
                    key, config_item, self.parent_layout, self.current_config
                )

        # 如果提供了配置，则应用它
        if config:
            self._apply_config(config, self.config_structure, self.current_config)

    def get_config(self):
        """
        获取当前表单的配置
        :return: 当前选择的配置字典
        """
        return self.current_config

    def _create_combobox(self, key, config, parent_layout, parent_config):
        """创建下拉框"""
        # 创建控件容器布局
        container_layout = QVBoxLayout()
        container_layout.setContentsMargins(5, 5, 5, 5)
        container_layout.setSpacing(5)
        parent_layout.addLayout(container_layout)

        # 创建下拉框 - 使用垂直布局
        label_text = config["label"]
        if label_text.startswith("$"):
            pass
        label = BodyLabel(label_text)
        # 移除固定宽度，让标签自然显示
        container_layout.addWidget(label)

        combo = ComboBox()
        combo.addItems(config["options"])
        container_layout.addWidget(combo)

        # 创建子控件容器布局
        child_layout = QVBoxLayout()
        container_layout.addLayout(child_layout)

        # 保存引用
        self.widgets[key] = combo
        self.child_layouts[key] = child_layout

        # 初始化配置
        parent_config[key] = {"value": combo.currentText(), "children": {}}
        
        # 初始化所有子选项容器字典
        self.all_child_containers[key] = {}
        
        # 预先生成所有子选项并设置为不可见
        if "children" in config:
            for option_value, child_config in config["children"].items():
                # 创建子选项容器
                option_container = QWidget()
                option_container_layout = QVBoxLayout(option_container)
                option_container_layout.setContentsMargins(0, 0, 0, 0)
                option_container_layout.setSpacing(0)
                child_layout.addWidget(option_container)
                
                # 默认设置为不可见
                option_container.setVisible(False)
                
                # 保存子选项容器的引用和相关信息
                self.all_child_containers[key][option_value] = {
                    'container': option_container,
                    'layout': option_container_layout,
                    'widgets': {},
                    'config': {}
                }
        
        # 连接信号，默认save_config=True
        combo.currentTextChanged.connect(
            lambda value, current_key=key, current_config=config, current_parent_config=parent_config[
                key
            ]: self._on_combobox_changed(
                current_key, value, current_config, current_parent_config, child_layout, save_config=True
            )
        )

        # 触发初始加载，但设置save_config=False避免保存默认值
        self._on_combobox_changed(
            key, combo.currentText(), config, parent_config[key], child_layout, save_config=False
        )

    def _create_lineedit(self, key, config, parent_layout, parent_config):
        """创建输入框"""
        # 创建控件容器布局
        container_layout = QVBoxLayout()
        container_layout.setContentsMargins(5, 5, 5, 5)
        container_layout.setSpacing(5)
        parent_layout.addLayout(container_layout)

        # 处理标签，移除可能的$符号
        label_text = config["label"]
        if label_text.startswith("$"):
            pass
        label = BodyLabel(label_text)
        # 移除固定宽度，让标签自然显示
        container_layout.addWidget(label)

        # 检查是否有inputs数组（input类型的选项）
        if "inputs" in config:
            # 对于input类型，为每个input项创建独立的输入框
            parent_config[key] = {}

            for input_item in config["inputs"]:
                # 创建子容器
                input_container = QVBoxLayout()
                input_container.setContentsMargins(10, 5, 10, 5)
                container_layout.addLayout(input_container)

                # 处理input项的标签
                input_label_text = input_item.get("label", input_item.get("name", ""))
                if input_label_text.startswith("$"):
                    pass
                input_label = BodyLabel(input_label_text)
                input_container.addWidget(input_label)

                # 创建输入框
                input_line_edit = LineEdit()
                if "default" in input_item:
                    input_line_edit.setText(str(input_item["default"]))
                input_container.addWidget(input_line_edit)

                # 保存引用，使用input的name作为键
                input_name = input_item.get("name", "input")
                if key not in self.widgets:
                    self.widgets[key] = {}
                self.widgets[key][input_name] = input_line_edit

                # 初始化配置
                parent_config[key][input_name] = input_line_edit.text()

                # 连接信号
                input_line_edit.textChanged.connect(
                    lambda text, k=key, input_name=input_name, p_conf=parent_config: self._on_input_item_changed(
                        k, input_name, text, p_conf
                    )
                )
        else:
            # 普通的单行输入框
            line_edit = LineEdit()
            if "default" in config:
                line_edit.setText(config["default"])

            container_layout.addWidget(line_edit)

            # 保存引用
            self.widgets[key] = line_edit

            # 初始化配置
            parent_config[key] = line_edit.text()

            # 连接信号（用户交互时保存配置）
            line_edit.textChanged.connect(
                lambda text, k=key, p_conf=parent_config: self._on_lineedit_changed(
                    k, text, p_conf, save_config=True
                )
            )

    def _on_input_item_changed(self, key, input_name, text, parent_config):
        """处理input类型中单个输入项的变化"""
        if key in parent_config and isinstance(parent_config[key], dict):
            parent_config[key][input_name] = text
            # 自动保存选项
            self._auto_save_options()

    def _on_combobox_changed(self, key, value, config, parent_config, child_layout, save_config=True):
        """下拉框值改变处理
        
        :param save_config: 是否保存配置，默认为True。初始化时可以设置为False避免保存默认值
        """
        # 保存当前子配置到缓存（如果有）
        current_value = parent_config.get('value')
        if current_value and key in self.all_child_containers and current_value in self.all_child_containers[key]:
            # 获取当前子容器的配置
            current_container = self.all_child_containers[key][current_value]
            if current_container['config']:
                # 为当前主选项值创建缓存键
                cache_key = f"{key}_{current_value}"
                # 深拷贝子配置以保存完整状态
                import copy
                self.option_subconfig_cache[cache_key] = copy.deepcopy(current_container['config'])

        # 更新配置
        parent_config["value"] = value
        
        # 隐藏所有子选项容器
        if key in self.all_child_containers:
            for option_value, container_info in self.all_child_containers[key].items():
                container_info['container'].setVisible(False)

        # 处理当前选择的子选项
        if "children" in config and value in config["children"] and key in self.all_child_containers and value in self.all_child_containers[key]:
            child_config = config["children"][value]
            current_container = self.all_child_containers[key][value]
            
            # 如果子容器中还没有创建控件，则创建它们
            if current_container['layout'].count() == 0:
                # 检查child_config是否是一个包含多个配置项的字典
                if isinstance(child_config, dict):
                    # 方式1：如果child_config有type键，处理为单个控件
                    if "type" in child_config:
                        if child_config["type"] == "combobox":
                            self._create_combobox(
                                f"{key}_child", child_config, current_container['layout'], current_container['config']
                            )
                        elif child_config["type"] == "lineedit":
                            self._create_lineedit(
                                f"{key}_child", child_config, current_container['layout'], current_container['config']
                            )
                    # 方式2：如果child_config不包含type键，但包含多个配置项，处理为多个控件
                    elif len(child_config) > 0:
                        # 为每个子配置项创建控件
                        for sub_key, sub_config in child_config.items():
                            if sub_config.get("type") == "combobox":
                                self._create_combobox(
                                    sub_key, sub_config, current_container['layout'], current_container['config']
                                )
                            elif sub_config.get("type") == "lineedit":
                                self._create_lineedit(
                                    sub_key, sub_config, current_container['layout'], current_container['config']
                                )
            
            # 尝试从缓存中恢复之前的子配置
            cache_key = f"{key}_{value}"
            if cache_key in self.option_subconfig_cache:
                # 临时禁用自动保存，避免恢复配置时触发保存
                old_disable_auto_save = getattr(self, '_disable_auto_save', False)
                self._disable_auto_save = True
                try:
                    # 应用缓存的子配置
                    self._apply_subconfigs(child_config, current_container['config'], self.option_subconfig_cache[cache_key])
                finally:
                    # 恢复自动保存状态
                    self._disable_auto_save = old_disable_auto_save
            
            # 设置当前子容器为可见
            current_container['container'].setVisible(True)
            
            # 更新parent_config中的children引用，指向当前容器的配置
            parent_config["children"] = current_container['config']

        # 自动保存选项，只有当save_config为True且未禁用自动保存时才保存
        if save_config and (not hasattr(self, "_disable_auto_save") or not self._disable_auto_save):
            self._auto_save_options()

    def _on_lineedit_changed(self, key, text, parent_config, save_config=True):
        """输入框值改变处理
        
        :param save_config: 是否保存配置，默认为True。初始化时可以设置为False避免保存默认值
        """
        parent_config[key] = text
        # 自动保存选项，只有当save_config为True且未禁用自动保存时才保存
        if save_config and (not hasattr(self, "_disable_auto_save") or not self._disable_auto_save):
            self._auto_save_options()

    def _clear_layout(self, layout):
        """清空布局中的所有控件"""
        while layout.count() > 0:
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
            else:
                child_layout = item.layout()
                if child_layout:
                    self._clear_layout(child_layout)

    def _apply_subconfigs(self, child_structure, target_config, cached_config):
        """应用缓存的子配置到目标配置
        
        :param child_structure: 子控件结构定义
        :param target_config: 目标配置字典
        :param cached_config: 缓存的配置字典
        """
        # 首先合并缓存配置到目标配置
        # 如果子结构是单个控件
        if isinstance(child_structure, dict):
            if "type" in child_structure:
                # 单个控件情况
                # 直接复制缓存配置到目标配置
                for sub_key, sub_value in cached_config.items():
                    target_config[sub_key] = sub_value
            else:
                # 多个控件情况
                for sub_key, sub_config in child_structure.items():
                    if sub_key in cached_config:
                        target_config[sub_key] = cached_config[sub_key]
        
        # 应用配置到UI控件
        # 遍历目标配置中的所有键
        for sub_key, sub_value in target_config.items():
            # 检查子键是否在widgets字典中
            if sub_key in self.widgets:
                sub_widget = self.widgets[sub_key]
                # 处理嵌套的widgets字典（如inputs类型）
                if isinstance(sub_widget, dict):
                    for input_name, input_widget in sub_widget.items():
                        if isinstance(sub_value, dict) and input_name in sub_value:
                            input_widget.blockSignals(True)
                            input_widget.setText(str(sub_value[input_name]))
                            input_widget.blockSignals(False)
                # 处理普通控件
                else:
                    if hasattr(sub_widget, 'setText'):
                        sub_widget.blockSignals(True)
                        sub_widget.setText(str(sub_value))
                        sub_widget.blockSignals(False)
                    elif hasattr(sub_widget, 'setCurrentText'):
                        sub_widget.blockSignals(True)
                        index = sub_widget.findText(str(sub_value))
                        if index >= 0:
                            sub_widget.setCurrentIndex(index)
                        sub_widget.blockSignals(False)

    def _auto_save_options(self):
        """自动保存当前选项"""
        # 检查是否禁用了自动保存
        if hasattr(self, "_disable_auto_save") and self._disable_auto_save:
            return
            
        # 检查是否有service_coordinator和option_service
        if hasattr(self, "service_coordinator") and hasattr(self.service_coordinator, "option_service"):  # type: ignore
            try:
                # 获取当前所有配置
                all_config = self.get_config()
                # 调用OptionService的update_options方法保存选项
                self.service_coordinator.option_service.update_options(all_config)  # type: ignore
            except Exception as e:
                # 如果保存失败，记录错误但不影响用户操作
                from app.utils.logger import logger

                logger.error(f"自动保存选项失败: {e}")

    def _apply_config(self, config, form_structure, current_config):
        """
        应用配置到表单
        :param config: 要应用的配置字典
        :param form_structure: 表单结构定义
        :param current_config: 当前配置字典
        """
        # 创建一个标志来临时禁用自动保存
        self._disable_auto_save = True
        
        try:
            for key, value in config.items():
                if key in form_structure:
                    field_config = form_structure[key]

                    if field_config["type"] == "combobox":
                        # 处理下拉框配置
                        if isinstance(value, dict):
                            combo_value = value.get("value", "")
                            # 查找并设置下拉框的值
                            if key in self.widgets:
                                combo = self.widgets[key]
                                # 临时断开信号连接
                                combo.blockSignals(True)
                                index = combo.findText(combo_value)
                                if index >= 0:
                                    combo.setCurrentIndex(index)
                                # 重新连接信号
                                combo.blockSignals(False)
                                
                                # 手动更新当前配置
                                if key not in current_config:
                                    current_config[key] = {}
                                current_config[key]["value"] = combo_value
                                
                                # 递归应用子配置
                                if "children" in value:
                                    # 优先使用children属性
                                    if (
                                        "children" in field_config
                                        and combo_value in field_config["children"]
                                    ):
                                        # 确保子选项容器存在
                                        if key in self.all_child_containers and combo_value in self.all_child_containers[key]:
                                            # 获取对应的子选项容器
                                            child_container = self.all_child_containers[key][combo_value]
                                            
                                            # 确保子容器中的控件已创建
                                            if child_container['layout'].count() == 0:
                                                child_config = field_config["children"][combo_value]
                                                # 创建子控件
                                                if isinstance(child_config, dict):
                                                    if "type" in child_config:
                                                        # 单个控件情况
                                                        if child_config["type"] == "combobox":
                                                            self._create_combobox(
                                                                f"{key}_child", child_config, child_container['layout'], child_container['config']
                                                            )
                                                        elif child_config["type"] == "lineedit":
                                                            self._create_lineedit(
                                                                f"{key}_child", child_config, child_container['layout'], child_container['config']
                                                            )
                                                    else:
                                                        # 多个控件情况
                                                        for sub_key, sub_config in child_config.items():
                                                            if sub_config.get("type") == "combobox":
                                                                self._create_combobox(
                                                                    sub_key, sub_config, child_container['layout'], child_container['config']
                                                                )
                                                            elif sub_config.get("type") == "lineedit":
                                                                self._create_lineedit(
                                                                    sub_key, sub_config, child_container['layout'], child_container['config']
                                                                )
                                            
                                            # 应用子配置到子容器
                                            child_config = field_config["children"][combo_value]
                                            # 使用_apply_subconfigs方法应用子配置
                                            self._apply_subconfigs(child_config, child_container['config'], value["children"])
                                            
                                            # 更新parent_config中的children引用，指向子容器的配置
                                            current_config[key]["children"] = child_container['config']
                                            
                                            # 设置当前子容器为可见
                                            child_container['container'].setVisible(True)
                                            
                                            # 隐藏其他所有子选项容器
                                            for option_value, container_info in self.all_child_containers[key].items():
                                                if option_value != combo_value:
                                                    container_info['container'].setVisible(False)

                    elif field_config["type"] == "lineedit":
                        # 处理输入框配置
                        if key in self.widgets:
                            # 检查是否是input类型（有inputs数组）
                            if "inputs" in field_config and isinstance(value, dict):
                                # 处理input类型的多个输入项
                                if isinstance(self.widgets[key], dict):
                                    # 确保current_config[key]是一个字典
                                    if key not in current_config:
                                        current_config[key] = {}
                                    
                                    for input_name, input_value in value.items():
                                        if input_name in self.widgets[key]:
                                            # 临时断开信号连接
                                            self.widgets[key][input_name].blockSignals(True)
                                            self.widgets[key][input_name].setText(str(input_value))
                                            # 重新连接信号
                                            self.widgets[key][input_name].blockSignals(False)
                                            # 手动更新current_config
                                            current_config[key][input_name] = input_value
                            else:
                                # 普通的单行输入框
                                # 临时断开信号连接
                                self.widgets[key].blockSignals(True)
                                self.widgets[key].setText(str(value))
                                # 重新连接信号
                                self.widgets[key].blockSignals(False)
                                # 手动更新current_config
                                current_config[key] = value
        finally:
            # 恢复自动保存
            self._disable_auto_save = False
