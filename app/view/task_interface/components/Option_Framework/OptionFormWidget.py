"""
选项表单组件
从 form_structure 生成选项表单，包含多个选项项组件
"""
from typing import Dict, Any, Optional
from PySide6.QtWidgets import QWidget, QVBoxLayout
from app.utils.logger import logger
from app.view.task_interface.components.Option_Framework.OptionItemWidget import OptionItemWidget


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

            # 处理缺失的 type 字段（向后兼容）
            option_config = dict(item_config)
            if "type" not in option_config:
                option_config["type"] = "combobox"
                logger.debug(f"选项 {key} 缺失 type，默认作为 combobox 处理")

            # 创建选项项组件
            option_item = OptionItemWidget(key, option_config, self)
            
            # 预创建子选项（如果存在）
            if "children" in option_config:
                for option_value, child_config in option_config["children"].items():
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
        # 先断开所有信号连接，防止在清理过程中触发不必要的信号
        for option_item in list(self.option_items.values()):
            try:
                option_item.option_changed.disconnect()
            except:
                pass  # 如果没有连接，忽略错误
        
        # 收集所有需要删除的控件
        widgets_to_delete = []
        layouts_to_delete = []
        
        # 移除所有选项项组件
        while self.main_layout.count() > 0:
            item = self.main_layout.takeAt(0)
            
            # 处理不同类型的布局项
            if item.widget():
                widget = item.widget()
                if widget:
                    widget.hide()
                    widget.setParent(None)
                widgets_to_delete.append(widget)
            elif item.layout():
                layout = item.layout()
                # 递归清理子布局中的控件
                while layout.count() > 0:
                    child_item = layout.takeAt(0)
                    if child_item.widget():
                        child_widget = child_item.widget()
                        if child_widget:
                            child_widget.hide()
                            child_widget.setParent(None)
                        widgets_to_delete.append(child_widget)
                    elif child_item.layout():
                        # 嵌套的子布局也要清理
                        child_layout = child_item.layout()
                        while child_layout.count() > 0:
                            nested_item = child_layout.takeAt(0)
                            if nested_item.widget():
                                nested_widget = nested_item.widget()
                                if nested_widget:
                                    nested_widget.hide()
                                    nested_widget.setParent(None)
                                widgets_to_delete.append(nested_widget)
                        layouts_to_delete.append(child_layout)
                layouts_to_delete.append(layout)
            # spacer 会被 takeAt 自动清理，不需要手动处理
        
        # 清空选项项字典
        self.option_items.clear()
        
        # 删除所有布局
        for layout in layouts_to_delete:
            layout.deleteLater()
        
        # 删除所有控件
        for widget in widgets_to_delete:
            widget.deleteLater()
        
        # 确保布局完全清空（处理可能遗漏的项）
        remaining_count = 0
        max_iterations = 100  # 防止无限循环
        iteration = 0
        while self.main_layout.count() > 0 and iteration < max_iterations:
            item = self.main_layout.takeAt(0)
            # 删除剩余的项
            if item:
                if item.widget():
                    widget = item.widget()
                    if widget:
                        widget.hide()
                        widget.setParent(None)
                        widget.deleteLater()
                elif item.layout():
                    layout = item.layout()
                    layout.deleteLater()
            iteration += 1
            remaining_count = self.main_layout.count()
        
        # 如果还有剩余项，记录警告
        if remaining_count > 0:
            logger.warning(f"布局未完全清空，剩余 {remaining_count} 项")
        
        # 重置布局属性，确保下次添加时状态正确
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # 强制更新布局和几何结构，确保界面刷新
        self.updateGeometry()
        self.update()
    
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
                option_item.children_wrapper.setVisible(False)
        
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
                            self._apply_children_config(option_item, children_config)
                    else:
                        # 直接使用字典作为值
                        option_item.set_value(value)
                else:
                    # 直接使用值
                    option_item.set_value(value)
        
        # 第三步：最后确保所有选项项的子选项可见性正确（只显示当前选中值对应的子选项）
        # 注意：由于 set_value 已经调用了 _update_children_visibility，这里只需要处理那些没有通过 set_value 设置的选项
        # 实际上，如果所有选项都通过 set_value 设置，这一步可能是多余的，但保留作为保险
        for option_item in self.option_items.values():
            if option_item.config_type in ["combobox", "switch"]:
                # 只在选项值已设置但子选项可见性可能不正确时才更新（跳过动画）
                # 由于 set_value 已经处理了可见性，这里主要是为了处理边缘情况
                if option_item.current_value is not None:
                    option_item._update_children_visibility(option_item.current_value, skip_animation=True)
    
    def _apply_single_child_config(self, option_item: OptionItemWidget, option_value: str, child_config: Any):
        """
        应用单个子选项的配置
        
        :param option_item: 选项项组件
        :param option_value: 子选项的值（当前选中值）
        :param child_config: 子选项配置
        """
        if option_value in option_item.config.get("children", {}):
            child_structure = option_item.config["children"][option_value]
            option_item.add_child_option(option_value, child_structure)

        if isinstance(child_config, list):
            for config_item in child_config:
                self._apply_single_child_config(option_item, option_value, config_item)
            return

        child_widget = option_item.find_child_widget(option_value, child_config)
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
                    
                    # 如果有子选项的子选项，递归应用（使用 _apply_children_config 以支持 hidden 字段）
                    if children_config:
                        self._apply_children_config(child_widget, children_config)
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
        应用子选项配置，兼容 children 中以 option_value 或 child_key 为键的情况。
        会跳过标记为 hidden 的子选项。
        """
        if not children_config:
            return

        child_definitions = option_item.config.get("children", {})

        for config_key, child_cfg in children_config.items():
            # 跳过标记为 hidden 的子选项（hidden=True）
            if isinstance(child_cfg, dict) and child_cfg.get("hidden", False):
                logger.debug(f"跳过隐藏的子选项: option_key={option_item.key}, config_key={config_key}")
                continue
            
            option_value = config_key if config_key in child_definitions else None

            if not option_value:
                option_value = option_item.get_option_value_for_child_key(config_key)

            if option_value and child_cfg:
                # 如果 child_cfg 是字典且包含 hidden 字段（但 hidden=False），移除 hidden 字段后应用
                if isinstance(child_cfg, dict) and "hidden" in child_cfg:
                    # 移除 hidden 字段，保留其他配置
                    actual_cfg = {k: v for k, v in child_cfg.items() if k != "hidden"}
                    # 如果移除 hidden 后只剩下 value 字段，直接使用 value
                    if len(actual_cfg) == 1 and "value" in actual_cfg:
                        actual_cfg = actual_cfg["value"]
                    self._apply_single_child_config(option_item, option_value, actual_cfg)
                else:
                    self._apply_single_child_config(option_item, option_value, child_cfg)
            else:
                logger.debug(
                    f"跳过无效的子选项配置: option_key={option_item.key}, config_key={config_key}"
                )
    
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

