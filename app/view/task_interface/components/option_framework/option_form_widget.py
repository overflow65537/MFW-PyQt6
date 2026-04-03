"""
选项表单组件
从 form_structure 生成选项表单，包含多个选项项组件
"""
import warnings
from typing import Dict, Any, Optional, TYPE_CHECKING
from PySide6.QtWidgets import QWidget, QVBoxLayout
from app.core.utils.option_branches_compat import get_option_branches
from app.utils.logger import logger
from app.view.task_interface.components.option_framework.items import (
    OptionItemBase,
    OptionItemRegistry,
)

if TYPE_CHECKING:
    from app.view.task_interface.components.option_framework.items import OptionItemBase


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
        self.option_items: Dict[str, "OptionItemBase"] = {}  # 选项项组件字典
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

            # 使用注册器创建选项项组件
            option_item = OptionItemRegistry.create(key, option_config, self)
            
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
            if option_item is None:
                continue
            signal = getattr(option_item, "option_changed", None)
            if signal is None:
                continue
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", RuntimeWarning)
                    signal.disconnect()
            except Exception:
                pass  # 如果没有连接或接收端已失效，忽略
        
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
            if option_item.config_type in ["combobox", "switch", "checkbox"]:
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
                        children_config = get_option_branches(value)
                        
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
            elif option_item.config_type == "checkbox":
                # checkbox 类型使用自己的子选项更新逻辑
                if option_item.current_value is not None:
                    option_item._update_children_for_checkbox(skip_animation=True)
    
    def _apply_single_child_config(
        self,
        option_item: "OptionItemBase",
        option_value: str,
        child_config: Any,
        target_widget: Optional["OptionItemBase"] = None,
    ):
        """
        应用单个子选项的配置
        
        :param option_item: 选项项组件
        :param option_value: 子选项的值（当前选中值）
        :param child_config: 子选项配置
        :param target_widget: 已定位的子选项控件（优先使用，避免重复查找导致定位错误）
        """
        if option_value in option_item.config.get("children", {}):
            child_structure = option_item.config["children"][option_value]
            option_item.add_child_option(option_value, child_structure)

        if isinstance(child_config, list):
            for config_item in child_config:
                self._apply_single_child_config(option_item, option_value, config_item)
            return

        child_widget = target_widget or option_item.find_child_widget(option_value, child_config)
        if child_widget:
            # 注意：不需要设置可见性，因为 set_value 已经通过 _update_children_visibility 处理了
            
            # 递归应用子选项的配置
            # 根据子选项的类型决定如何处理配置
            if isinstance(child_config, dict):
                # 如果是配置格式（包含 value 字段）
                if "value" in child_config:
                    # 先保存 children 配置
                    children_config = get_option_branches(child_config)
                    
                    # 设置子选项的值（这会触发子选项的 _update_children_visibility）
                    child_widget.set_value(child_config["value"])
                    
                    # 如果有子选项的子选项，递归应用（使用 _apply_children_config 以支持 hidden 字段）
                    if children_config:
                        self._apply_children_config(child_widget, children_config)
                else:
                    # 如果字典不包含 value 字段，可能是输入框的值（inputs 类型）
                    # 需要根据子选项的类型来判断
                    if child_widget.config_type in ["input", "inputs"]:
                        # input/inputs 类型可以接收字典
                        child_widget.set_value(child_config)
                    else:
                        # 其他类型（如 combobox）不应该接收字典
                        logger.warning(f"子选项类型 {child_widget.config_type} 不应该接收字典值: {child_config}")
            else:
                # 非字典值直接传递
                child_widget.set_value(child_config)

    def _get_active_child_option_values(self, option_item: "OptionItemBase") -> set[str]:
        """获取当前处于激活状态的子选项分支。"""
        if option_item.config_type == "checkbox":
            current_value = getattr(option_item, "current_value", []) or []
            return {str(value) for value in current_value}

        child_definitions = option_item.config.get("children", {})
        if not child_definitions or getattr(option_item, "current_value", None) is None:
            return set()

        current_value = option_item.current_value
        selected_str = str(current_value)
        matched_key = option_item._match_child_key(
            child_definitions,
            current_value,
            selected_str,
            selected_str.strip(),
        )
        return {str(matched_key)} if matched_key is not None else set()

    def _resolve_child_target(
        self,
        option_item: "OptionItemBase",
        config_key: str,
        search_option_values: set[str],
    ) -> tuple[Optional[str], Optional["OptionItemBase"]]:
        """根据配置 key 定位子选项，优先命中当前激活分支。"""
        child_definitions = option_item.config.get("children", {})

        if config_key in child_definitions:
            return str(config_key), None

        direct_widget = option_item.child_options.get(config_key)
        if direct_widget:
            option_value = option_item.get_option_value_for_child_key(config_key)
            return (str(option_value) if option_value is not None else None), direct_widget

        for option_value in search_option_values:
            child_key = option_item._child_name_map.get((option_value, config_key))
            if child_key:
                return option_value, option_item.child_options.get(child_key)

        result = option_item.find_child_by_name(config_key)
        if result:
            option_value, child_widget = result
            return str(option_value), child_widget

        return None, None

    def _is_grouped_children_branch(
        self,
        option_item: "OptionItemBase",
        config_key: str,
        child_cfg: Any,
    ) -> bool:
        """判断是否为新的按父分支分组的 children 结构。"""
        if config_key not in option_item.config.get("children", {}):
            return False
        if not isinstance(child_cfg, dict):
            return False
        reserved_keys = {"value", "hidden", "children", "name"}
        if any(key in child_cfg for key in reserved_keys):
            return False

        # 只有当分支内的每个键都能映射到该分支下的子控件时，才视为分组结构
        for nested_key in child_cfg.keys():
            child_key = option_item._child_name_map.get((config_key, nested_key))
            if child_key is None:
                return False
        return True

    def _apply_child_entry(
        self,
        option_item: "OptionItemBase",
        config_key: str,
        child_cfg: Any,
        active_option_values: set[str],
        search_option_values: Optional[set[str]] = None,
    ) -> None:
        """应用单个子选项配置。"""
        option_value, child_widget = self._resolve_child_target(
            option_item,
            config_key,
            search_option_values or active_option_values,
        )

        # 跳过非当前激活分支上的 hidden 子选项；若 hidden 标记陈旧但当前分支已激活，则仍尝试应用
        if isinstance(child_cfg, dict) and child_cfg.get("hidden", False):
            if not option_value or str(option_value) not in active_option_values:
                logger.debug(f"跳过隐藏的子选项: option_key={option_item.key}, config_key={config_key}")
                return

        if option_value and child_cfg:
            # 如果 child_cfg 是字典且包含 hidden 字段（但 hidden=False），移除 hidden 字段后应用
            if isinstance(child_cfg, dict) and "hidden" in child_cfg:
                actual_cfg = {k: v for k, v in child_cfg.items() if k != "hidden"}
                if len(actual_cfg) == 1 and "value" in actual_cfg:
                    actual_cfg = actual_cfg["value"]
                self._apply_single_child_config(option_item, option_value, actual_cfg, child_widget)
            else:
                self._apply_single_child_config(option_item, option_value, child_cfg, child_widget)
        else:
            logger.debug(
                f"跳过无效的子选项配置: option_key={option_item.key}, config_key={config_key}"
            )
    
    def _apply_children_config(self, option_item: "OptionItemBase", children_config: Dict[str, Any]):
        """
        应用子选项配置，兼容多种配置格式：
        1. config_key 是 option_value（如 "自行输入角色名"）
        2. config_key 是 child_name（如 "输入A级角色名"）
        会跳过标记为 hidden 的子选项。
        """
        if not children_config:
            return

        active_option_values = self._get_active_child_option_values(option_item)

        for config_key, child_cfg in children_config.items():
            if self._is_grouped_children_branch(option_item, config_key, child_cfg):
                branch_value = str(config_key)
                for nested_key, nested_cfg in child_cfg.items():
                    self._apply_child_entry(
                        option_item,
                        nested_key,
                        nested_cfg,
                        active_option_values,
                        {branch_value},
                    )
                continue

            self._apply_child_entry(
                option_item,
                config_key,
                child_cfg,
                active_option_values,
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

