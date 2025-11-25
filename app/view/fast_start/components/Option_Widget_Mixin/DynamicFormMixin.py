import copy
from .LineEditGenerator import LineEditGenerator
from .ComboBoxGenerator import ComboBoxGenerator
from .PathLineEditGenerator import PathLineEditGenerator
from .GPUComboBoxGenerator import GPUComboBoxGenerator
from .SearchDeviceGenerator import SearchDeviceGenerator

from app.utils.logger import logger

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
        
        # 处理任务层级的description
        try:
            if hasattr(self, 'set_description'):
                if 'description' in form_structure:
                    self.set_description(form_structure['description']) # type: ignore
                    if hasattr(self, '_toggle_description'):
                        self._toggle_description(visible=True) # type: ignore
                else:
                    # 如果form_structure中没有description字段，隐藏描述区域
                    self.set_description('') # type: ignore
        except Exception:
            # 如果设置description失败，忽略此错误
            pass

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
            # 跳过任务层级的description字段
            if key == "description":
                continue
                
            if config_item["type"] == "combobox":
                self._create_combobox(
                    key, config_item, self.parent_layout, self.current_config
                )
            elif config_item["type"] == "lineedit":
                self._create_lineedit(
                    key, config_item, self.parent_layout, self.current_config
                )
            elif config_item["type"] == "pathlineedit":
                self._create_pathlineedit(
                    key, config_item, self.parent_layout, self.current_config
                )
            elif config_item["type"] == "gpu_combobox":
                self._create_gpu_combobox(
                    key, config_item, self.parent_layout, self.current_config
                )
            elif config_item["type"] == "search_device":
                self._create_search_device(
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
        combo_generator = ComboBoxGenerator(self)
        combo_generator.create_combobox(key, config, parent_layout, parent_config)
    def _create_lineedit(self, key, config, parent_layout, parent_config):
        """创建输入框"""
        line_edit_generator = LineEditGenerator(self)
        line_edit_generator.create_lineedit(key, config, parent_layout, parent_config)
        
    def _create_pathlineedit(self, key, config, parent_layout, parent_config):
        """创建带按钮的路径输入框"""
        path_line_edit_generator = PathLineEditGenerator(self)
        path_line_edit_generator.create_pathlineedit(key, config, parent_layout, parent_config)

    def _create_gpu_combobox(self, key, config, parent_layout, parent_config):
        """创建GPU下拉框"""
        gpu_combo_generator = GPUComboBoxGenerator(self)
        gpu_combo_generator.create_gpu_combobox(key, config, parent_layout, parent_config)

    def _create_search_device(self, key, config, parent_layout, parent_config):
        """创建搜索设备组件"""
        search_device_generator = SearchDeviceGenerator(self)
        search_device_generator.create_search_device(key, config, parent_layout, parent_config)


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
        # 确保cached_config是一个字典
        if not isinstance(cached_config, dict):
            return
            
        # 深度合并缓存配置到目标配置，保留未在缓存中但存在于目标配置中的键
        # import copy is now at the top of the file
        
        # 如果子结构是单个控件
        if isinstance(child_structure, dict):
            if "type" in child_structure:
                # 单个控件情况
                # 深度合并缓存配置到目标配置
                for sub_key, sub_value in cached_config.items():
                    # 确保在更新时深度复制，避免引用问题
                    target_config[sub_key] = copy.deepcopy(sub_value)
            else:
                # 多个控件情况
                for sub_key, sub_config in child_structure.items():
                    if sub_key in cached_config:
                        # 如果缓存配置是字典，进行深度合并
                        if isinstance(cached_config[sub_key], dict) and isinstance(target_config.get(sub_key), dict):
                            # 合并两个字典，保留目标配置中不在缓存中的键
                            for k, v in cached_config[sub_key].items():
                                target_config[sub_key][k] = copy.deepcopy(v)
                        else:
                            # 否则直接复制
                            target_config[sub_key] = copy.deepcopy(cached_config[sub_key])
        
        # 应用配置到UI控件
        # 遍历目标配置中的所有键
        for sub_key, sub_value in target_config.items():
            # 检查子键是否在widgets字典中
            if sub_key in self.widgets:
                sub_widget = self.widgets[sub_key]
                try:
                    # 处理嵌套的widgets字典（如inputs类型）
                    if isinstance(sub_widget, dict):
                        for input_name, input_widget in sub_widget.items():
                            if isinstance(sub_value, dict) and input_name in sub_value:
                                # 临时阻断信号
                                input_widget.blockSignals(True)
                                try:
                                    input_widget.setText(str(sub_value[input_name]))
                                finally:
                                    # 确保恢复信号
                                    input_widget.blockSignals(False)
                    # 处理普通控件
                    else:
                        # 临时阻断信号
                        sub_widget.blockSignals(True)
                        try:
                            if hasattr(sub_widget, 'setText'):
                                sub_widget.setText(str(sub_value))
                            elif hasattr(sub_widget, 'setCurrentText'):
                                index = sub_widget.findText(str(sub_value))
                                if index >= 0:
                                    sub_widget.setCurrentIndex(index)
                            # 处理其他可能的控件类型
                            elif hasattr(sub_widget, 'setChecked') and isinstance(sub_value, bool):
                                sub_widget.setChecked(sub_value)
                        finally:
                            # 确保恢复信号
                            sub_widget.blockSignals(False)
                except Exception as e:
                    # 记录错误但不影响其他控件的更新
                    logger.error(f"应用子配置到控件失败 (key: {sub_key}, value: {sub_value}): {e}")

    def _set_child_container_visibility(self, key, visible_option_value):
        """设置子选项容器的可见性"""
        if key in self.all_child_containers:
            for option_value, container_info in self.all_child_containers[key].items():
                container_info['container'].setVisible(option_value == visible_option_value)
    
    def _build_all_children_config(self, key, current_value, current_config):
        """构建包含所有子选项配置的字典"""
        all_children_config = {current_value: current_config}
        
        if key in self.all_child_containers:
            for option_value, container_info in self.all_child_containers[key].items():
                if option_value != current_value:  # 已经添加了当前选项，跳过
                    cache_key = f"{key}_{option_value}"
                    if cache_key in self.option_subconfig_cache:
                        # 从缓存中获取配置
                        all_children_config[option_value] = copy.deepcopy(self.option_subconfig_cache[cache_key])
                    elif container_info['config']:  # 如果缓存中没有但容器中有配置
                        all_children_config[option_value] = copy.deepcopy(container_info['config'])
        
        return all_children_config
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
                logger.error(f"自动保存选项失败: {e}")

    def _apply_config(self, config, form_structure, current_config):
        """
        应用配置到表单
        :param config: 要应用的配置字典
        :param form_structure: 表单结构定义
        :param current_config: 当前配置字典
        """
        # 保存旧的_disable_auto_save值，确保正确恢复
        old_disable_auto_save = getattr(self, '_disable_auto_save', False)
        self._disable_auto_save = True
        
        try:
            for key, value in config.items():
                if key in form_structure:
                    field_config = form_structure[key]

                    if field_config["type"] == "combobox":
                        # 处理下拉框配置
                        if isinstance(value, dict):
                            # 配置文件中的value是实际的name值，而不是label
                            saved_name = value.get("value", "")
                            combo_value = ""
                            
                            # 查找对应的label值
                            for option in field_config["options"]:
                                if option["name"] == saved_name:
                                    combo_value = option["label"]
                                    break
                            
                            # 如果没有找到label，直接使用name
                            if not combo_value:
                                combo_value = saved_name
                                
                            # 查找并设置下拉框的值
                            if key in self.widgets:
                                combo = self.widgets[key]
                                # 临时断开信号连接，防止触发_on_combobox_changed
                                combo.blockSignals(True)
                                try:
                                    index = combo.findText(combo_value)
                                    if index >= 0:
                                        combo.setCurrentIndex(index)
                                        
                                        # 手动更新当前配置，确保保留原始值
                                        if key not in current_config:
                                            current_config[key] = {}
                                        # 保存实际的name值，而不是label
                                        current_config[key]["value"] = saved_name
                                        
                                        # 递归应用子配置
                                        if "children" in value:
                                            # 优先使用children属性
                                            # 查找实际的name值，而不是label
                                            actual_name = None
                                            for option in field_config["options"]:
                                                if option["label"] == combo_value:
                                                    actual_name = option["name"]
                                                    break
                                            
                                            if (
                                                "children" in field_config
                                                and actual_name in field_config["children"]
                                            ):
                                                # 确保子选项容器存在
                                                if key in self.all_child_containers and actual_name in self.all_child_containers[key]:
                                                    # 获取对应的子选项容器
                                                    child_container = self.all_child_containers[key][actual_name]
                                                    
                                                    # 确保子容器中的控件已创建
                                                    if child_container['layout'].count() == 0:
                                                        child_config = field_config["children"][actual_name]
                                                        # 创建子控件
                                                        if isinstance(child_config, dict):
                                                            if "type" in child_config:
                                                                # 单个控件情况
                                                                if child_config["type"] == "combobox":
                                                                    # 查找当前子选项的实际键名，而不是硬编码为f"{key}_child"
                                                                    # 直接使用child_config的name或label字段
                                                                    child_key = child_config.get("name", child_config.get("label", f"{key}_child"))
                                                                    # 移除可能的$前缀
                                                                    if child_key.startswith("$"):
                                                                        child_key = child_key[1:]
                                                                    self._create_combobox(
                                                                        child_key, child_config, child_container['layout'], child_container['config']
                                                                    )
                                                                elif child_config["type"] == "lineedit":
                                                                    # 查找当前子选项的实际键名，而不是硬编码为f"{key}_child"
                                                                    # 直接使用child_config的name或label字段
                                                                    child_key = child_config.get("name", child_config.get("label", f"{key}_child"))
                                                                    # 移除可能的$前缀
                                                                    if child_key.startswith("$"):
                                                                        child_key = child_key[1:]
                                                                    self._create_lineedit(
                                                                        child_key, child_config, child_container['layout'], child_container['config']
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
                                                    
                                                    # 设置当前子容器为可见并隐藏其他容器
                                                    self._set_child_container_visibility(key, actual_name)
            
                                                    # 检查是否有缓存的子配置
                                                    cache_key = f"{key}_{actual_name}"
                                                    if cache_key in self.option_subconfig_cache:
                                                        # 优先使用缓存的子配置
                                                        self._apply_subconfigs(field_config["children"][actual_name], child_container['config'], self.option_subconfig_cache[cache_key])
                                                    else:
                                                        # 应用子配置到子容器
                                                        # value["children"] 可能包含所有子选项配置，因此我们需要获取当前选项的配置
                                                        # 应用子配置到子容器
                                                        # value["children"] 可能包含所有子选项配置，因此我们需要获取当前选项的配置
                                                        child_value_config = value["children"].get(actual_name, value["children"])
                                                     
                                                        # 根据child_config的类型选择不同的处理方式
                                                        if "type" in field_config["children"][actual_name]:
                                                            # 单个控件情况，将整个配置传递进去
                                                            self._apply_subconfigs(field_config["children"][actual_name], child_container['config'], child_value_config)
                                                        else:
                                                            # 多个控件情况，可能有不同的结构
                                                            self._apply_subconfigs(field_config["children"][actual_name], child_container['config'], child_value_config)
                                                         
                                                        # 处理子选项配置
                                                        all_children_config = self._build_all_children_config(key, actual_name, child_container['config'])
                                                         
                                                        # 更新current_config中的children，包含所有子选项配置
                                                        current_config[key]["children"] = all_children_config
                                                         
                                                        # 设置当前子容器为可见并隐藏其他容器
                                                        self._set_child_container_visibility(key, actual_name)
                                finally:
                                    # 确保在任何情况下都恢复信号
                                    combo.blockSignals(False)

                    elif field_config["type"] in ("lineedit", "pathlineedit"):
                        # 处理输入框配置，包括带按钮的路径输入框
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
                                            widget = self.widgets[key][input_name]
                                            widget.blockSignals(True)
                                            try:
                                                widget.setText(str(input_value))
                                                # 手动更新current_config，确保保留原始值
                                                current_config[key][input_name] = input_value
                                            finally:
                                                # 确保在任何情况下都恢复信号
                                                widget.blockSignals(False)
                            else:
                                # 普通的单行输入框
                                widget = self.widgets[key]
                                # 临时断开信号连接
                                widget.blockSignals(True)
                                try:
                                    widget.setText(str(value))
                                    # 手动更新current_config，确保保留原始值
                                    current_config[key] = value
                                finally:
                                    # 确保在任何情况下都恢复信号
                                    widget.blockSignals(False)
        finally:
            # 恢复自动保存状态
            self._disable_auto_save = old_disable_auto_save
