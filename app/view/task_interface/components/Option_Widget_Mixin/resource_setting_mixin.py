from copy import deepcopy
from typing import Dict, Any, Callable, Protocol, Optional
from qfluentwidgets import (
    BodyLabel,
    ComboBox,
    ToolTipFilter,
)
from PySide6.QtWidgets import QVBoxLayout

from app.utils.logger import logger
from app.core.core import ServiceCoordinator
from app.view.task_interface.components.option_framework.option_form_widget import OptionFormWidget


class ResourceSettingMixin:
    """
    资源设置 Mixin - 提供资源下拉框相关功能
    使用方法：在 OptionWidget 中使用多重继承添加此 mixin
    """

    option_page_layout: QVBoxLayout
    service_coordinator: ServiceCoordinator
    current_config: Dict[str, Any]
    tr: Callable[..., str]  # Qt翻译方法
    set_description: Callable[..., None]  # 设置描述方法（可选）
    _toggle_description: Callable[..., None]  # 切换描述显示（可选）

    def _init_resource_settings(self):
        """初始化资源设置相关属性"""
        if not hasattr(self, "resource_setting_widgets"):
            self.resource_setting_widgets: Dict[str, Any] = {}
        self._resource_syncing = False
        self.current_resource: str | None = None
        if not hasattr(self, "current_controller_label"):
            self.current_controller_label: str | None = None
        # 资源选项表单组件
        if not hasattr(self, "resource_option_form_widget"):
            self.resource_option_form_widget: Optional[OptionFormWidget] = None
        # 全局选项（interface.global_option）
        if not hasattr(self, "global_option_label"):
            self.global_option_label = None
        if not hasattr(self, "global_option_form_widget"):
            self.global_option_form_widget: Optional[OptionFormWidget] = None
        # 构建资源映射表
        self._rebuild_resource_mapping()

    def _rebuild_resource_mapping(self):
        """重新构建资源映射表（用于多配置模式下interface更新时）"""
        if not hasattr(self, "controller_type_mapping") or not self.controller_type_mapping:
            self.controller_type_mapping = self.service_coordinator.task_query.get_controller_ui_context(
                self.current_config
            )["controller_type_mapping"]

        self.resource_mapping = self.service_coordinator.task_query.build_resource_mapping(
            self.controller_type_mapping
        )

    def create_resource_settings(self) -> None:
        """创建固定的资源设置UI"""
        # 在多配置模式下，重新构建资源映射表以确保使用最新的interface
        self._rebuild_resource_mapping()

        # 创建资源选择下拉框
        self._create_resource_option()

        # 填充资源选项
        self._fill_resource_option()
        
        # 根据当前资源渲染资源选项（如果有）
        self._update_resource_options()
        # 渲染全局选项（如果有 interface.global_option）
        self._update_global_options()

    def _create_resource_option(self):
        """创建资源选择下拉框"""
        resource_label = BodyLabel(self.tr("Resource"))
        self.option_page_layout.addWidget(resource_label)

        resource_combox = ComboBox()
        self.option_page_layout.addWidget(resource_combox)
        # 存储 label 和 combo，确保可以被正确控制显示/隐藏
        self.resource_setting_widgets["resource_combo_label"] = resource_label
        self.resource_setting_widgets["resource_combo"] = resource_combox
        resource_combox.currentTextChanged.connect(self._on_resource_combox_changed)

    def _on_resource_combox_changed(self, new_resource):
        """资源变化时的处理函数（只有用户主动更改时才触发）"""
        if self._resource_syncing:
            return
        
        # 如果新资源与当前资源相同，不处理（避免重复触发）
        if self.current_resource == new_resource:
            return
        
        # 更新当前资源信息变量
        self.current_resource = new_resource

        # 确保 current_controller_label 存在
        if not hasattr(self, "current_controller_label") or not self.current_controller_label:
            return

        current_controller_label = self.current_controller_label

        if current_controller_label not in self.resource_mapping:
            return

        for resource in self.service_coordinator.task_query.get_resources_for_controller(
            current_controller_label,
            self.controller_type_mapping,
        ):
            if resource.get("label", resource.get("name", "")) == self.current_resource:
                # 检查资源是否真的改变了
                old_resource = self.current_config.get("resource", "")
                new_resource_name = resource["name"]
                
                if old_resource == new_resource_name:
                    # 资源没有实际改变，不触发更新
                    return
                
                self.current_config["resource"] = new_resource_name
                res_combo: ComboBox = self.resource_setting_widgets["resource_combo"]
                if description := resource.get("description"):
                    res_combo.installEventFilter(ToolTipFilter(res_combo))
                    res_combo.setToolTip(description)
                    # 设置资源描述到公告页面
                    if hasattr(self, "set_description"):
                        self.set_description(description, has_options=True)
                else:
                    # 如果没有描述，清空公告页面
                    if hasattr(self, "set_description"):
                        self.set_description("", has_options=True)
                # 保存资源选项到Resource任务
                self._auto_save_resource_option(new_resource_name)
                # 获取当前资源的选项名称列表
                resource_option_names = resource.get("option", [])
                # 更新资源选项的 hidden 状态（根据新资源）
                self._update_resource_options_hidden_state(resource_option_names)
                # 更新资源选项（如果有）
                self._update_resource_options()
                # 资源变化时，通知任务列表更新（仅携带 resource 字段）
                self._notify_task_list_update()
                break

    def _auto_save_resource_option(self, resource_name: str, skip_sync_check: bool = False):
        """自动保存资源选项到Resource任务
        
        Args:
            resource_name: 资源名称
            skip_sync_check: 是否跳过 _syncing 检查（用于控制器类型切换时的自动保存）
        """
        if not skip_sync_check and self._resource_syncing:
            return
        try:
            # 更新当前配置
            self.current_config["resource"] = resource_name
            if not self.service_coordinator.set_resource_name(resource_name):
                logger.warning("未找到 Resource 任务，无法保存资源选项")
            
            # 同时通过OptionService保存（用于触发信号）
            self.service_coordinator.update_selected_options({"resource": resource_name})
        except Exception as e:
            logger.error(f"自动保存资源选项失败: {e}")

    def _notify_task_list_update(self):
        """通知任务列表更新（资源变化时调用）"""
        try:
            if hasattr(self, "service_coordinator"):
                self.service_coordinator.notify_option_updated(
                    {"resource": self.current_config.get("resource")}
                )
        except Exception:
            pass

    def _fill_resource_option(self):
        """填充资源选项"""
        if "resource_combo" not in self.resource_setting_widgets:
            return

        resource_combo: ComboBox = self.resource_setting_widgets["resource_combo"]
        
        # 在填充时完全阻止信号，避免触发任务更新
        resource_combo.blockSignals(True)
        
        resource_combo.clear()

        # 确保 current_controller_label 存在
        if not hasattr(self, "current_controller_label") or not self.current_controller_label:
            logger.warning(f"current_controller_label 不存在或为空，无法填充资源选项")
            resource_combo.blockSignals(False)
            return

        current_controller_label = self.current_controller_label
        
        # 确保资源映射表已构建
        if not hasattr(self, "resource_mapping") or not self.resource_mapping:
            self._rebuild_resource_mapping()

        if current_controller_label not in self.resource_mapping:
            logger.warning(
                f"控制器标签 {current_controller_label} 不在资源映射表中。"
                f"可用的控制器标签: {list(self.resource_mapping.keys())}"
            )
            resource_combo.blockSignals(False)
            return

        # 使用当前控制器信息变量
        curren_config = self.resource_mapping[current_controller_label]
        
        for resource in curren_config:
            icon = resource.get("icon", "")
            resource_label = resource.get("label", resource.get("name", ""))
            resource_combo.addItem(resource_label, icon)

        # 根据 current_config 中的 resource 选择对应项
        target = self.current_config.get("resource", "")
        target_label = None
        for resource in curren_config:
            name = resource.get("name", "")
            label = resource.get("label", name)
            # 使用精确匹配，而不是 in 操作符，避免部分匹配问题
            if target and (target == name or target == label):
                target_label = label
                break
        
        if target_label:
            idx = resource_combo.findText(target_label)
            if idx >= 0:
                resource_combo.setCurrentIndex(idx)
                # 更新 current_resource，避免下次误判为变化
                self.current_resource = target_label
                # 确保 current_config 中的 resource 是最新的（使用 name，不是 label）
                # 同时获取资源的 description 并设置到公告页面
                for resource in curren_config:
                    if resource.get("label", resource.get("name", "")) == target_label:
                        self.current_config["resource"] = resource.get("name", "")
                        # 设置资源描述到公告页面
                        if hasattr(self, "set_description"):
                            description = resource.get("description", "")
                            self.set_description(description, has_options=True)
                            # 如果有描述，显示描述区域
                            if description and hasattr(self, "_toggle_description"):
                                self._toggle_description(True)
                        break
            else:
                logger.warning(f"未找到资源标签 {target_label} 在下拉框中")
        else:
            # 如果当前保存的资源不在新控制器的资源列表中，自动选择第一个资源并保存
            if target and curren_config:
                first_resource = curren_config[0]
                first_resource_name = first_resource.get("name", "")
                first_resource_label = first_resource.get("label", first_resource_name)
                
                # 设置下拉框为第一个资源
                idx = resource_combo.findText(first_resource_label)
                if idx >= 0:
                    resource_combo.setCurrentIndex(idx)
                    self.current_resource = first_resource_label
                    
                    # 更新配置并保存（跳过 _syncing 检查，因为这是控制器类型切换时的自动更新）
                    self.current_config["resource"] = first_resource_name
                    self._auto_save_resource_option(first_resource_name, skip_sync_check=True)
                    
                    # 设置资源描述到公告页面
                    if hasattr(self, "set_description"):
                        description = first_resource.get("description", "")
                        self.set_description(description, has_options=True)
                        # 如果有描述，显示描述区域
                        if description and hasattr(self, "_toggle_description"):
                            self._toggle_description(True)
                else:
                    logger.warning(f"未找到资源标签 {first_resource_label} 在下拉框中")
        
        # 恢复信号
        resource_combo.blockSignals(False)
        
        # 填充完成后，根据当前资源更新资源选项（如果有）
        if target_label or (target and curren_config):
            self._update_resource_options()
    
    def _get_current_resource_dict(self) -> Optional[Dict[str, Any]]:
        """获取当前资源的配置字典"""
        if not hasattr(self, "current_controller_label") or not self.current_controller_label:
            return None
        
        current_controller_label = self.current_controller_label
        
        current_resource_name = self.current_config.get("resource", "")
        return self.service_coordinator.task_query.get_current_resource_entry(
            current_controller_label,
            current_resource_name,
            getattr(self, "controller_type_mapping", None),
        )
    
    def _get_current_controller_name(self) -> str:
        """获取当前选中的控制器 name（用于按 controller 字段过滤选项）"""
        try:
            return self.service_coordinator.task_query.get_current_controller_type()
        except Exception:
            pass
        return ""

    def _build_resource_option_form_structure(self, resource: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """构建资源选项的表单结构
        
        Args:
            resource: 资源配置字典
            
        Returns:
            表单结构字典，如果没有选项则返回 None
        """
        # 获取资源的 option 字段
        resource_option_names = resource.get("option", [])
        if not resource_option_names:
            return None
        
        interface = self.service_coordinator.interface
        all_options = interface.get("option", {})
        
        if not all_options:
            return None
        
        form_structure = {}
        current_controller = self._get_current_controller_name()
        
        # 遍历资源需要的每个选项
        for option_name in resource_option_names:
            if option_name in all_options:
                option_def = all_options[option_name]
                # 按 controller 字段过滤：仅当当前控制器匹配时才显示
                if not self.service_coordinator.task_query.is_option_visible_for_controller(
                    option_def, current_controller
                ):
                    continue
                # 使用 process_option_def 方法递归处理选项定义
                field_config = self.service_coordinator.task_query.process_option_def(
                    option_def, all_options, option_name
                )
                form_structure[option_name] = field_config
        
        return form_structure if form_structure else None

    def _build_global_option_form_structure(self) -> Optional[Dict[str, Any]]:
        """从 interface.global_option 构建全局选项的表单结构。与 task/resource/controller 同级，无则返回 None。"""
        interface = self.service_coordinator.interface
        global_option_def = interface.get("global_option")
        if not global_option_def:
            return None
        all_options = interface.get("option", {})
        if not all_options:
            return None
        current_controller = self._get_current_controller_name()
        form_structure = {}
        if isinstance(global_option_def, list):
            for option_name in global_option_def:
                if option_name in all_options:
                    option_def = all_options[option_name]
                    # 按 controller 字段过滤
                    if not self.service_coordinator.task_query.is_option_visible_for_controller(
                        option_def, current_controller
                    ):
                        continue
                    field_config = self.service_coordinator.task_query.process_option_def(
                        option_def, all_options, option_name
                    )
                    form_structure[option_name] = field_config
        elif isinstance(global_option_def, dict):
            for option_name, option_def in global_option_def.items():
                if option_name == "description":
                    continue
                # 按 controller 字段过滤
                if isinstance(option_def, dict) and not self.service_coordinator.task_query.is_option_visible_for_controller(
                    option_def, current_controller
                ):
                    continue
                field_config = self.service_coordinator.task_query.process_option_def(
                    option_def, all_options, option_name
                )
                form_structure[option_name] = field_config
        return form_structure if form_structure else None

    def _update_global_options(self):
        """根据 interface.global_option 更新全局选项区域：有则显示「全局选项」标题与表单，无则不显示。"""
        form_structure = self._build_global_option_form_structure()
        if not form_structure:
            self._clear_global_options()
            return
        option_config = self.service_coordinator.config_query.get_current_global_options()
        if self.global_option_label is None:
            self.global_option_label = BodyLabel(self.tr("Global Option"))
            self.option_page_layout.addWidget(self.global_option_label)
        if self.global_option_form_widget is None:
            self.global_option_form_widget = OptionFormWidget()
            self.option_page_layout.addWidget(self.global_option_form_widget)
        self.global_option_form_widget.build_from_structure(form_structure, option_config)
        self._connect_global_option_signals()

    def _clear_global_options(self):
        """移除全局选项标题与表单。"""
        if self.global_option_label is not None:
            label = self.global_option_label
            self.global_option_label = None
            if label.parent():
                self.option_page_layout.removeWidget(label)
            label.deleteLater()
        if self.global_option_form_widget is not None:
            widget = self.global_option_form_widget
            self.global_option_form_widget = None
            if hasattr(widget, "option_items"):
                for option_item in widget.option_items.values():
                    try:
                        option_item.option_changed.disconnect()
                    except Exception:
                        pass
            widget._clear_options()
            if widget.parent():
                self.option_page_layout.removeWidget(widget)
            widget.deleteLater()

    def _connect_global_option_signals(self):
        """连接全局选项变化信号。"""
        if self.global_option_form_widget is None:
            return
        for option_item in self.global_option_form_widget.option_items.values():
            option_item.option_changed.connect(self._on_global_option_changed)
            self._connect_global_option_child_signals(option_item)

    def _connect_global_option_child_signals(self, option_item):
        """递归连接全局选项子项信号。"""
        for child_widget in option_item.child_options.values():
            child_widget.option_changed.connect(self._on_global_option_changed)
            self._connect_global_option_child_signals(child_widget)

    def _on_global_option_changed(self, key: str, value: Any):
        """全局选项变化时写入当前配置根层的 global_options。"""
        if self.global_option_form_widget is None:
            return
        all_options = self.global_option_form_widget.get_options()
        if self.service_coordinator.config_query.update_current_global_options(dict(all_options)):
            self.service_coordinator.notify_option_updated(all_options)

    def _update_resource_options_hidden_state(self, current_resource_option_names: list):
        """更新资源选项的 hidden 状态（当资源切换时调用）
        
        Args:
            current_resource_option_names: 当前资源的选项名称列表
        """
        try:
            self.service_coordinator.task_query.update_resource_options_hidden_state(
                current_resource_option_names
            )
        except Exception as e:
            logger.error(f"更新资源选项 hidden 状态失败: {e}")
    
    def _update_resource_options(self):
        """根据当前资源更新资源选项的显示"""
        # 获取当前资源
        current_resource = self._get_current_resource_dict()
        if not current_resource:
            # 如果没有当前资源，清除选项显示
            self._clear_resource_options()
            return
        
        # 构建表单结构
        form_structure = self._build_resource_option_form_structure(current_resource)
        if not form_structure:
            # 如果资源没有选项，清除选项显示
            self._clear_resource_options()
            return
        
        option_config = self.service_coordinator.task_query.get_resource_option_config(
            form_structure
        )
        
        # 创建或更新选项表单组件
        if self.resource_option_form_widget is None:
            self.resource_option_form_widget = OptionFormWidget()
            self.option_page_layout.addWidget(self.resource_option_form_widget)
        
        # 构建表单
        self.resource_option_form_widget.build_from_structure(form_structure, option_config)
        
        # 连接选项变化信号（需要在 build_from_structure 之后，因为会重新创建选项项）
        self._connect_resource_option_signals()
    
    def _clear_resource_options(self):
        """清除资源选项的显示"""
        if self.resource_option_form_widget is not None:
            widget_to_remove = self.resource_option_form_widget
            self.resource_option_form_widget = None  # 先设置为 None，避免重复调用
            
            # 断开所有信号连接
            if hasattr(widget_to_remove, "option_items"):
                for option_item in widget_to_remove.option_items.values():
                    try:
                        option_item.option_changed.disconnect()
                    except:
                        pass
            
            # 清空选项表单组件的内容
            widget_to_remove._clear_options()
            
            # 从布局中移除
            if widget_to_remove.parent():
                self.option_page_layout.removeWidget(widget_to_remove)
            
            # 删除组件
            widget_to_remove.deleteLater()
    
    def _connect_resource_option_signals(self):
        """连接资源选项的变化信号"""
        if self.resource_option_form_widget is None:
            return
        
        # 遍历所有选项项，连接它们的信号
        for option_item in self.resource_option_form_widget.option_items.values():
            # 连接选项变化信号
            option_item.option_changed.connect(self._on_resource_option_changed)
            # 递归连接子选项的信号
            self._connect_resource_child_option_signals(option_item)
    
    def _connect_resource_child_option_signals(self, option_item):
        """递归连接资源选项的子选项信号
        
        Args:
            option_item: 选项项组件
        """
        for child_widget in option_item.child_options.values():
            child_widget.option_changed.connect(self._on_resource_option_changed)
            # 递归连接子选项的子选项
            self._connect_resource_child_option_signals(child_widget)
    
    def _on_resource_option_changed(self, key: str, value: Any):
        """资源选项变化时的回调函数，用于保存到 Resource 任务的 task_option
        
        Args:
            key: 选项键名
            value: 选项值
        """
        try:
            # 获取当前所有资源选项配置
            if self.resource_option_form_widget is None:
                return
            
            all_options = self.resource_option_form_widget.get_options()
            
            # 获取当前资源的选项列表（用于验证哪些选项应该被保留）
            current_resource = self._get_current_resource_dict()
            if not current_resource:
                return
            
            resource_option_names = current_resource.get("option", [])
            if not resource_option_names:
                return
            
            # 只保存当前资源的选项（过滤掉不属于当前资源的选项）
            resource_options = {
                k: v for k, v in all_options.items() 
                if k in resource_option_names
            }
            
            if not self.service_coordinator.save_resource_options(
                resource_option_names, resource_options
            ):
                logger.warning("资源选项保存失败")
                return

            # 如果当前选中的是 Resource 任务，同时更新 OptionService 的 current_options
            from app.common.constants import _RESOURCE_

            if self.service_coordinator.task_query.get_current_option_task_id() == _RESOURCE_:
                current_options = self.service_coordinator.task_query.get_current_options()
                current_options.update(resource_options)
                self.service_coordinator.notify_option_updated(resource_options)
        except Exception as e:
            logger.error(f"保存资源选项失败: {e}")


