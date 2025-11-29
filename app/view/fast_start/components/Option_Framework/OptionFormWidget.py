"""
选项表单组件
从 form_structure 生成选项表单，包含多个选项项组件
"""
from typing import Dict, Any, Optional, List
from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtCore import Qt
from app.utils.logger import logger
from .OptionItemWidget import OptionItemWidget


class OptionFormWidget(QWidget):
    """
    选项表单组件
    根据 form_structure 动态生成选项表单
    """
    
    def __init__(self, parent: Optional[QWidget] = None):
        """
        初始化选项表单组件
        
        :param parent: 父组件
        """
        super().__init__(parent)
        self.option_items: Dict[str, OptionItemWidget] = {}  # 选项项组件字典
        self.form_structure: Dict[str, Any] = {}  # 表单结构
        
        self._init_ui()
    
    def _init_ui(self):
        """初始化UI"""
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
    
    def build_from_structure(self, form_structure: Dict[str, Any], config: Optional[Dict[str, Any]] = None):
        """
        根据表单结构生成选项表单
        
        :param form_structure: 表单结构字典
        :param config: 可选的初始配置字典
        """
        self.form_structure = form_structure
        
        # 清空现有的选项项
        self._clear_options()
        
        # 遍历表单结构，创建选项项
        for key, item_config in form_structure.items():
            # 跳过非选项字段（如 description）
            if key == "description" or not isinstance(item_config, dict):
                continue
            
            # 检查是否有 type 字段
            if "type" not in item_config:
                continue
            
            # 创建选项项组件
            option_item = OptionItemWidget(key, item_config, self)
            
            # 预创建子选项（如果存在）
            if "children" in item_config:
                for option_value, child_config in item_config["children"].items():
                    option_item.add_child_option(option_value, child_config)
            
            # 保存选项项引用
            self.option_items[key] = option_item
            
            # 添加到布局
            self.main_layout.addWidget(option_item)
        
        # 如果有初始配置，应用它
        if config:
            self.apply_config(config)
    
    def _clear_options(self):
        """清空所有选项项"""
        # 移除所有选项项组件
        while self.main_layout.count() > 0:
            item = self.main_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        
        self.option_items.clear()
    
    def apply_config(self, config: Dict[str, Any]):
        """
        应用配置到表单
        
        :param config: 配置字典
        """
        # 第一步：先隐藏所有子选项容器
        for option_item in self.option_items.values():
            if option_item.config_type in ["combobox", "switch"]:
                for child_widget in option_item.child_options.values():
                    child_widget.setVisible(False)
                option_item.children_container.setVisible(False)
        
        # 第二步：应用配置并设置值
        for key, value in config.items():
            if key in self.option_items:
                option_item = self.option_items[key]
                
                if isinstance(value, dict):
                    # 如果有 value 字段，提取出来
                    if "value" in value:
                        # 先保存 children 配置，等设置完值后再应用
                        children_config = value.get("children", {})
                        
                        # 设置选项值（这会触发 _update_children_visibility，只显示对应的子选项）
                        option_item.set_value(value["value"])
                        
                        # 如果有 children 配置，在设置完值后应用当前选中值的子选项
                        if children_config:
                            # 获取当前选中值（set_value 后已更新）
                            current_value = option_item.current_value
                            if current_value and current_value in children_config:
                                # 只应用当前选中值的子选项配置
                                child_config = children_config[current_value]
                                if child_config:
                                    self._apply_single_child_config(option_item, current_value, child_config)
                    else:
                        # 直接使用字典作为值
                        option_item.set_value(value)
                else:
                    # 直接使用值
                    option_item.set_value(value)
        
        # 第三步：最后确保所有选项项的子选项可见性正确（只显示当前选中值对应的子选项）
        for option_item in self.option_items.values():
            if option_item.config_type in ["combobox", "switch"]:
                # 再次调用 _update_children_visibility 确保只显示当前选中值对应的子选项
                option_item._update_children_visibility(option_item.current_value)
    
    def _apply_single_child_config(self, option_item: OptionItemWidget, option_value: str, child_config: Any):
        """
        应用单个子选项的配置
        
        :param option_item: 选项项组件
        :param option_value: 子选项的值（当前选中值）
        :param child_config: 子选项配置
        """
        # 确保子选项已创建（应该已经通过 set_value -> _update_children_visibility 创建了）
        if option_value in option_item.config.get("children", {}):
            if option_value not in option_item.child_options:
                child_structure = option_item.config["children"][option_value]
                option_item.add_child_option(option_value, child_structure)
        
        # 获取子选项组件
        child_widget = option_item.child_options.get(option_value)
        if child_widget:
            # 注意：不需要设置可见性，因为 set_value 已经通过 _update_children_visibility 处理了
            
            # 递归应用子选项的配置
            # 根据子选项的类型决定如何处理配置
            if isinstance(child_config, dict):
                # 如果是配置格式（包含 value 字段）
                if "value" in child_config:
                    # 先保存 children 配置
                    children_config = child_config.get("children", {})
                    
                    # 设置子选项的值（这会触发子选项的 _update_children_visibility）
                    child_widget.set_value(child_config["value"])
                    
                    # 如果有子选项的子选项，递归应用
                    if children_config:
                        current_child_value = child_widget.current_value
                        if current_child_value and current_child_value in children_config:
                            self._apply_single_child_config(
                                child_widget, 
                                current_child_value, 
                                children_config[current_child_value]
                            )
                else:
                    # 如果字典不包含 value 字段，可能是输入框的值（inputs 类型）
                    # 需要根据子选项的类型来判断
                    if child_widget.config_type == "lineedit":
                        # lineedit 类型（特别是 inputs 类型）可以接收字典
                        child_widget.set_value(child_config)
                    else:
                        # 其他类型（如 combobox）不应该接收字典
                        logger.warning(f"子选项类型 {child_widget.config_type} 不应该接收字典值: {child_config}")
            else:
                # 非字典值直接传递
                child_widget.set_value(child_config)
    
    def _apply_children_config(self, option_item: OptionItemWidget, children_config: Dict[str, Any]):
        """
        递归应用子选项配置（已废弃，请使用 _apply_single_child_config）
        
        :param option_item: 选项项组件
        :param children_config: 子选项配置字典
        """
        # 这个方法保留用于向后兼容，但实际逻辑应该通过 set_value 触发 _update_children_visibility
        # 然后在需要时调用 _apply_single_child_config
        pass
    
    def get_options(self) -> Dict[str, Any]:
        """
        获取当前所有选项的配置（递归获取子选项）
        
        :return: 选项配置字典
        """
        result = {}
        
        for key, option_item in self.option_items.items():
            result[key] = option_item.get_option()
        
        return result
    
    def get_simple_options(self) -> Dict[str, Any]:
        """
        获取简单的选项值（不包含嵌套的 children 结构）
        
        :return: 选项值字典
        """
        result = {}
        
        for key, option_item in self.option_items.items():
            result[key] = option_item.get_simple_option()
        
        return result

