from typing import Dict, Any
from PySide6.QtWidgets import QWidget, QVBoxLayout
from qfluentwidgets import (
    BodyLabel,
    ComboBox,
    ToolTipFilter,
)

from app.utils.logger import logger
from app.core.core import ServiceCoordinator


class ResourceSettingWidget(QWidget):
    """
    资源设置组件 - 仅包含资源下拉框相关逻辑
    """
    
    # 这些方法由 OptionWidget 动态设置
    _toggle_description: Any = None
    _clear_options: Any = None
    tr: Any = None

    def __init__(
        self,
        service_coordinator: ServiceCoordinator,
        parent_layout: QVBoxLayout,
        parent=None,
    ):
        super().__init__(parent)
        self.service_coordinator = service_coordinator
        self.parent_layout = parent_layout
        self.current_config: Dict[str, Any] = {}
        self._syncing = False
        self.resource_setting_widgets: Dict[str, Any] = {}
        self.current_resource: str | None = None
        self.current_controller_label: str | None = None
        # 构建资源映射表
        self._rebuild_resource_mapping()

    def _rebuild_resource_mapping(self):
        """重新构建资源映射表（用于多配置模式下interface更新时）"""
        logger.debug("[_rebuild_resource_mapping] 开始重新构建资源映射表")
        # 获取最新的interface
        interface = self.service_coordinator.interface

        # 获取控制器类型映射（应该由 ControllerSettingWidget 提供）
        if not hasattr(self, "controller_type_mapping") or not self.controller_type_mapping:
            # 如果没有控制器映射，创建一个临时的
            logger.debug("[_rebuild_resource_mapping] 控制器映射不存在或为空，创建临时映射")
            self.controller_type_mapping = {
                ctrl.get("label", ctrl.get("name", "")): {
                    "name": ctrl.get("name", ""),
                    "type": ctrl.get("type", ""),
                    "icon": ctrl.get("icon", ""),
                    "description": ctrl.get("description", ""),
                }
                for ctrl in interface.get("controller", [])
            }
        else:
            logger.debug(f"[_rebuild_resource_mapping] 使用现有的控制器映射，包含 {len(self.controller_type_mapping)} 个控制器")

        # 构建资源映射表
        # 使用 label（如果存在）或 name 作为键，确保与 controller_type_mapping 的键一致
        self.resource_mapping = {}
        # 使用 controller_type_mapping 的键来构建资源映射表，确保键的一致性
        for label in self.controller_type_mapping.keys():
            self.resource_mapping[label] = []
        logger.debug(f"[_rebuild_resource_mapping] 初始化资源映射表，包含 {len(self.resource_mapping)} 个控制器键: {list(self.resource_mapping.keys())}")
        
        # 遍历每个资源，确定它支持哪些控制器
        for resource in interface.get("resource", []):
            supported_controllers = resource.get("controller")
            if not supported_controllers:
                # 未指定支持的控制器则默认对所有控制器生效
                for key in self.resource_mapping:
                    self.resource_mapping[key].append(resource)
                logger.debug(
                    f"资源 {resource.get('name', '')} 未指定控制器，添加到所有控制器"
                )
                continue

            # 资源中的 controller 字段存储的是控制器的 name（不是 type）
            # 例如：["安卓端", "桌面端"]
            for controller in interface.get("controller", []):
                controller_name = controller.get("name", "")
                # 检查控制器的 name 是否在资源支持的控制器列表中
                if controller_name in supported_controllers:
                    label = controller.get("label", controller.get("name", ""))
                    if label in self.resource_mapping:
                        self.resource_mapping[label].append(resource)
                        logger.debug(
                            f"资源 {resource.get('name', '')} 添加到控制器 {label} (name: {controller_name})"
                        )
                    else:
                        logger.warning(
                            f"控制器标签 {label} 不在资源映射表中，无法添加资源 {resource.get('name', '')}"
                        )

    def create_settings(self) -> None:
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
        """资源变化时的处理函数（只有用户主动更改时才触发）"""
        if self._syncing:
            return
        
        # 如果新资源与当前资源相同，不处理（避免重复触发）
        if self.current_resource == new_resource:
            return
        
        # 更新当前资源信息变量
        self.current_resource = new_resource

        # 确保 current_controller_label 存在
        if not hasattr(self, "current_controller_label"):
            return

        current_controller_label = getattr(self, "current_controller_label")

        if current_controller_label not in self.resource_mapping:
            return

        for resource in self.resource_mapping[current_controller_label]:
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
                # 保存资源选项到Resource任务
                self._auto_save_resource_option(new_resource_name)
                # 资源变化时，通知任务列表更新（仅携带 resource 字段）
                self._notify_task_list_update()
                break

    def _auto_save_resource_option(self, resource_name: str, skip_sync_check: bool = False):
        """自动保存资源选项到Resource任务
        
        Args:
            resource_name: 资源名称
            skip_sync_check: 是否跳过 _syncing 检查（用于控制器类型切换时的自动保存）
        """
        if not skip_sync_check and self._syncing:
            return
        try:
            from app.common.constants import _RESOURCE_
            option_service = self.service_coordinator.option_service
            # 更新当前配置
            self.current_config["resource"] = resource_name
            # 保存到Resource任务
            resource_task = option_service.task_service.get_task(_RESOURCE_)
            if resource_task:
                resource_task.task_option["resource"] = resource_name
                if not option_service.task_service.update_task(resource_task):
                    logger.warning("资源选项保存失败")
                else:
                    logger.debug(f"资源选项已保存: {resource_name}")
            else:
                logger.warning("未找到 Resource 任务，无法保存资源选项")
            
            # 同时通过OptionService保存（用于触发信号）
            option_service.update_options({"resource": resource_name})
        except Exception as e:
            logger.error(f"自动保存资源选项失败: {e}")

    def _notify_task_list_update(self):
        """通知任务列表更新（资源变化时调用）"""
        try:
            # 通过信号总线通知任务列表更新
            if hasattr(self, "service_coordinator"):
                # 发出 option_updated 信号，任务列表可以监听此信号来更新
                # 仅携带 resource 字段，避免其他字段变化导致任务列表重载
                self.service_coordinator.signal_bus.option_updated.emit(
                    {"resource": self.current_config.get("resource")}
                )
        except Exception:
            pass

    def _fill_resource_option(self):
        """填充资源选项"""
        logger.debug(f"[_fill_resource_option] 开始填充资源选项")
        if "resource_combo" not in self.resource_setting_widgets:
            logger.debug("[_fill_resource_option] 资源下拉框尚未创建，无法填充资源选项")
            return

        resource_combo: ComboBox = self.resource_setting_widgets["resource_combo"]
        
        # 在填充时完全阻止信号，避免触发任务更新
        resource_combo.blockSignals(True)
        
        resource_combo.clear()
        logger.debug(f"[_fill_resource_option] 已清空资源下拉框")

        # 确保 current_controller_label 存在
        if not hasattr(self, "current_controller_label") or not self.current_controller_label:
            logger.warning(f"[_fill_resource_option] current_controller_label 不存在或为空，无法填充资源选项")
            logger.debug(f"[_fill_resource_option] hasattr check: {hasattr(self, 'current_controller_label')}")
            if hasattr(self, "current_controller_label"):
                logger.debug(f"[_fill_resource_option] current_controller_label value: {getattr(self, 'current_controller_label', None)}")
            resource_combo.blockSignals(False)
            return

        current_controller_label = getattr(self, "current_controller_label")
        logger.debug(f"[_fill_resource_option] 当前控制器标签: {current_controller_label}")
        
        # 确保资源映射表已构建
        if not hasattr(self, "resource_mapping") or not self.resource_mapping:
            logger.debug("[_fill_resource_option] 资源映射表未构建，重新构建...")
            self._rebuild_resource_mapping()

        logger.debug(f"[_fill_resource_option] 资源映射表包含的控制器: {list(self.resource_mapping.keys())}")
        if current_controller_label not in self.resource_mapping:
            logger.warning(
                f"[_fill_resource_option] 控制器标签 {current_controller_label} 不在资源映射表中。"
                f"可用的控制器标签: {list(self.resource_mapping.keys())}"
            )
            resource_combo.blockSignals(False)
            return

        # 使用当前控制器信息变量
        curren_config = self.resource_mapping[current_controller_label]
        logger.debug(
            f"[_fill_resource_option] 为控制器 {current_controller_label} 填充资源选项，共 {len(curren_config)} 个资源"
        )
        
        # 记录所有资源的名称，用于调试
        resource_names = [r.get("name", "") for r in curren_config]
        logger.debug(f"[_fill_resource_option] 资源列表: {resource_names}")
        
        for resource in curren_config:
            icon = resource.get("icon", "")
            resource_label = resource.get("label", resource.get("name", ""))
            resource_combo.addItem(resource_label, icon)
            logger.debug(f"[_fill_resource_option] 添加资源选项: {resource_label} (name: {resource.get('name', '')})")

        # 根据 current_config 中的 resource 选择对应项
        target = self.current_config.get("resource", "")
        logger.debug(f"[_fill_resource_option] 配置中的目标资源: {target}")
        target_label = None
        for resource in curren_config:
            name = resource.get("name", "")
            label = resource.get("label", name)
            if target and target in (name, label):
                target_label = label
                logger.debug(f"[_fill_resource_option] 找到匹配的资源: {target_label} (name: {name})")
                break
        
        if target_label:
            idx = resource_combo.findText(target_label)
            if idx >= 0:
                resource_combo.setCurrentIndex(idx)
                # 更新 current_resource，避免下次误判为变化
                self.current_resource = target_label
                # 确保 current_config 中的 resource 是最新的（使用 name，不是 label）
                for resource in curren_config:
                    if resource.get("label", resource.get("name", "")) == target_label:
                        self.current_config["resource"] = resource.get("name", "")
                        logger.debug(f"[_fill_resource_option] 更新 current_config['resource'] 为: {self.current_config['resource']}")
                        break
                logger.debug(f"[_fill_resource_option] 设置资源下拉框当前项为: {target_label} (索引: {idx})")
            else:
                logger.warning(f"[_fill_resource_option] 未找到资源标签 {target_label} 在下拉框中")
        else:
            # 如果当前保存的资源不在新控制器的资源列表中，自动选择第一个资源并保存
            if target and curren_config:
                first_resource = curren_config[0]
                first_resource_name = first_resource.get("name", "")
                first_resource_label = first_resource.get("label", first_resource_name)
                logger.debug(f"[_fill_resource_option] 当前资源 {target} 不在控制器 {current_controller_label} 的资源列表中，自动选择第一个资源: {first_resource_label} (name: {first_resource_name})")
                
                # 设置下拉框为第一个资源
                idx = resource_combo.findText(first_resource_label)
                if idx >= 0:
                    resource_combo.setCurrentIndex(idx)
                    self.current_resource = first_resource_label
                    
                    # 更新配置并保存（跳过 _syncing 检查，因为这是控制器类型切换时的自动更新）
                    self.current_config["resource"] = first_resource_name
                    self._auto_save_resource_option(first_resource_name, skip_sync_check=True)
                    logger.debug(f"[_fill_resource_option] 已自动保存资源: {first_resource_name}")
                else:
                    logger.warning(f"[_fill_resource_option] 未找到资源标签 {first_resource_label} 在下拉框中")
            else:
                logger.debug(f"[_fill_resource_option] 配置中没有资源或资源列表为空")
        
        # 恢复信号
        resource_combo.blockSignals(False)
        logger.debug(f"[_fill_resource_option] 资源下拉框填充完成，当前显示 {resource_combo.count()} 个选项")

