from typing import Dict, Any
from PySide6.QtWidgets import QVBoxLayout
from qfluentwidgets import (
    BodyLabel,
    ComboBox,
    ToolTipFilter,
)

from app.utils.logger import logger
from app.core.core import ServiceCoordinator


class ResourceSettingMixin:
    """
    资源设置生成的Mixin组件 - 仅包含资源下拉框相关逻辑
    """

    service_coordinator: ServiceCoordinator
    parent_layout: QVBoxLayout

    resource_setting_widgets: Dict[str, Any]
    CHILD = [300, 300]

    def _toggle_description(self, visible: bool) -> None: ...
    def tr(
        self, sourceText: str, /, disambiguation: str | None = ..., n: int = ...
    ) -> str: ...

    def __init__(self):
        """初始化资源设置Mixin"""
        self.current_resource = None
        # 构建资源映射表
        self._rebuild_resource_mapping()

    def _rebuild_resource_mapping(self):
        """重新构建资源映射表（用于多配置模式下interface更新时）"""
        # 获取最新的interface
        interface = self.service_coordinator.interface

        # 获取控制器类型映射（应该由 ControllerSettingMixin 提供）
        if not hasattr(self, "controller_type_mapping"):
            # 如果没有控制器映射，创建一个临时的
            self.controller_type_mapping = {
                ctrl.get("label", ctrl.get("name", "")): {
                    "name": ctrl.get("name", ""),
                    "type": ctrl.get("type", ""),
                    "icon": ctrl.get("icon", ""),
                    "description": ctrl.get("description", ""),
                }
                for ctrl in interface.get("controller", [])
            }

        # 构建资源映射表
        self.resource_mapping = {
            ctrl.get("label", ctrl.get("name", "")): []
            for ctrl in interface.get("controller", [])
        }
        # 遍历每个资源，确定它支持哪些控制器
        for resource in interface.get("resource", []):
            supported_controllers = resource.get("controller")
            if not supported_controllers:
                # 未指定支持的控制器则默认对所有控制器生效
                for key in self.resource_mapping:
                    self.resource_mapping[key].append(resource)
                continue

            for controller in interface.get("controller", []):
                if controller.get("name", "") in supported_controllers:
                    label = controller.get("label", controller.get("name", ""))
                    self.resource_mapping[label].append(resource)

    def create_resource_settings(self):
        """创建固定的资源设置UI"""
        logger.info("Creating resource settings UI...")
        # 在多配置模式下，重新构建资源映射表以确保使用最新的interface
        self._rebuild_resource_mapping()

        # 创建资源选择下拉框
        self._create_resource_option()
        
        # 填充资源选项
        self._fill_resource_option()

    def _create_resource_option(self):
        """创建资源选择下拉框"""
        resource_label = BodyLabel(self.tr("Resource"))
        self.parent_layout.addWidget(resource_label)

        resource_combox = ComboBox()
        self.parent_layout.addWidget(resource_combox)
        self.resource_setting_widgets["resource_combo"] = resource_combox
        resource_combox.currentTextChanged.connect(self._on_resource_combox_changed)

    def _on_resource_combox_changed(self, new_resource):
        """资源变化时的处理函数"""
        if hasattr(self, "_syncing") and getattr(self, "_syncing", False):
            return
        # 更新当前资源信息变量
        self.current_resource = new_resource

        # 确保 current_controller_label 存在
        if not hasattr(self, "current_controller_label") or not hasattr(self, "current_config"):
            return

        current_controller_label = getattr(self, "current_controller_label")
        current_config = getattr(self, "current_config")

        if current_controller_label not in self.resource_mapping:
            return

        for resource in self.resource_mapping[current_controller_label]:
            if resource.get("label", resource.get("name", "")) == self.current_resource:
                current_config["resource"] = resource["name"]
                res_combo: ComboBox = self.resource_setting_widgets["resource_combo"]
                if description := resource.get("description"):
                    res_combo.installEventFilter(ToolTipFilter(res_combo))
                    res_combo.setToolTip(description)
                # 仅提交 resource 字段，任务列表据此判断是否需要重载
                if hasattr(self, "_auto_save_options"):
                    getattr(self, "_auto_save_options")({"resource": resource["name"]})
                # 资源变化时，通知任务列表更新（仅携带 resource 字段）
                self._notify_task_list_update()
                break

    def _notify_task_list_update(self):
        """通知任务列表更新（资源变化时调用）"""
        try:
            # 通过信号总线通知任务列表更新
            if hasattr(self, "service_coordinator") and hasattr(self, "current_config"):
                current_config = getattr(self, "current_config")
                # 发出 option_updated 信号，任务列表可以监听此信号来更新
                # 仅携带 resource 字段，避免其他字段变化导致任务列表重载
                self.service_coordinator.signal_bus.option_updated.emit(
                    {"resource": current_config.get("resource")}
                )
        except Exception:
            pass

    def _fill_resource_option(self):
        """填充资源选项"""
        if "resource_combo" not in self.resource_setting_widgets:
            return
        
        resource_combo: ComboBox = self.resource_setting_widgets["resource_combo"]
        resource_combo.clear()

        # 确保 current_controller_label 和 current_config 存在
        if not hasattr(self, "current_controller_label") or not hasattr(self, "current_config"):
            return

        current_controller_label = getattr(self, "current_controller_label")
        current_config = getattr(self, "current_config")

        if current_controller_label not in self.resource_mapping:
            return

        # 使用当前控制器信息变量
        curren_config = self.resource_mapping[current_controller_label]
        for resource in curren_config:
            icon = resource.get("icon", "")
            resource_label = resource.get("label", resource.get("name", ""))
            resource_combo.addItem(resource_label, icon)

        # 根据 current_config 中的 resource 选择对应项
        target = current_config.get("resource", "")
        target_label = None
        for resource in curren_config:
            name = resource.get("name", "")
            label = resource.get("label", name)
            if target and target in (name, label):
                target_label = label
                break
        resource_combo.blockSignals(True)
        if target_label:
            idx = resource_combo.findText(target_label)
            if idx >= 0:
                resource_combo.setCurrentIndex(idx)
        resource_combo.blockSignals(False)
