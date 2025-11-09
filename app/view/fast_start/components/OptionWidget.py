import json
import re
from pathlib import Path
from typing import List

import markdown
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QSplitter,
)

from qfluentwidgets import (
    SimpleCardWidget,
    ToolTipPosition,
    ToolTipFilter,
    BodyLabel,
    ScrollArea,
    ComboBox,
    EditableComboBox,
    SwitchButton,
    PrimaryPushButton,
    LineEdit,
    SpinBox,
    CheckBox,
)
from app.view.fast_start.animations.option_transition import OptionTransitionAnimator

from app.utils.logger import logger, log_with_ui
from app.common.constants import RESOURCE_TASK_ID, POST_TASK_ID
from app.utils.gui_helper import IconLoader
from app.widget.PathLineEdit import PathLineEdit

from ....core.core import TaskItem, ConfigItem, ServiceCoordinator

# 导入重构后的模块
from .option_modules import (
    OptionDataManager,
    WidgetFactory,
    NestedOptionHandler,
    DeviceManager,
)


class OptionWidget(QWidget):
    """选项面板控件

    负责显示任务的配置选项，支持：
    - 普通任务选项（通过 interface.json 配置）
    - 基础任务选项（控制器、资源、完成后设置）
    - 嵌套选项、多输入项等复杂配置
    """

    # ==================== 初始化 ==================== #

    def __init__(self, service_coordinator: ServiceCoordinator, parent=None):
        super().__init__(parent)
        self.service_coordinator = service_coordinator
        self.task = self.service_coordinator.task
        self.config = self.service_coordinator.config
        self.core_signalBus = self.service_coordinator.signal_bus

        # 创建图标加载器（仅 GUI 使用）
        self.icon_loader = IconLoader(service_coordinator)

        # 初始化 UI
        self._init_ui()
        
        # 初始化重构后的功能模块
        self._init_managers()
        
        # 连接信号
        self.core_signalBus.task_selected.connect(self.show_option)
        self.core_signalBus.config_changed.connect(self._on_config_changed)
        
        # 初始状态
        self._toggle_description(visible=False)
        self.set_title(self.tr("Options"))
        
        # 当前正在编辑的任务
        self.current_task: TaskItem | None = None

    def _init_managers(self):
        """初始化功能模块管理器"""
        # 数据管理器
        self.data_manager = OptionDataManager(self.service_coordinator)
        
        # 控件工厂
        self.widget_factory = WidgetFactory(
            self.service_coordinator,
            self.option_area_layout,
            self.icon_loader,
            self._save_current_options
        )
        
        # 嵌套选项处理器
        self.nested_handler = NestedOptionHandler(
            self.service_coordinator,
            self.option_area_layout,
            self.icon_loader,
            self.Get_Task_List,
            self._save_current_options
        )
        
        # 设备管理器
        self.device_manager = DeviceManager(self.service_coordinator)


    # ==================== UI 初始化 ==================== #

    def _init_ui(self):
        """初始化UI"""
        self.main_layout = QVBoxLayout(self)

        self.title_widget = BodyLabel()
        self.title_widget.setStyleSheet("font-size: 20px;")
        self.title_widget.setAlignment(Qt.AlignmentFlag.AlignLeft)

        # ==================== 选项区域 ==================== #
        # 创建选项卡片
        self.option_area_card = SimpleCardWidget()
        self.option_area_card.setClickEnabled(False)
        self.option_area_card.setBorderRadius(8)

        # 创建滚动区域
        self.option_area_widget = ScrollArea()
        self.option_area_widget.setWidgetResizable(
            True
        )  # 重要:允许内部widget自动调整大小
        # 禁用横向滚动
        self.option_area_widget.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        # 设置透明无边框
        self.option_area_widget.setStyleSheet(
            "background-color: transparent; border: none;"
        )

        # 创建一个容器widget来承载布局
        option_container = QWidget()
        self.option_area_layout = QVBoxLayout(option_container)  # 将布局关联到容器
        self.option_area_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.option_area_layout.setContentsMargins(10, 10, 10, 10)  # 添加内边距

        # 将容器widget设置到滚动区域
        self.option_area_widget.setWidget(option_container)
        # 初始化过渡动画器
        self._option_animator = OptionTransitionAnimator(option_container)

        # 创建一个垂直布局给卡片,然后将滚动区域添加到这个布局中
        card_layout = QVBoxLayout()
        card_layout.addWidget(self.option_area_widget)
        card_layout.setContentsMargins(0, 0, 0, 0)
        self.option_area_card.setLayout(card_layout)
        # ==================== 描述区域 ==================== #
        # 创建描述标题（直接放在主布局中）
        self.description_title = BodyLabel("功能描述")
        self.description_title.setStyleSheet("font-size: 20px;")
        self.description_title.setAlignment(Qt.AlignmentFlag.AlignLeft)

        # 创建描述卡片
        self.description_area_card = SimpleCardWidget()
        self.description_area_card.setClickEnabled(False)
        self.description_area_card.setBorderRadius(8)

        # 正确的布局层次结构
        self.description_area_widget = (
            QWidget()
        )  # 使用普通Widget作为容器，而不是ScrollArea
        self.description_layout = QVBoxLayout(
            self.description_area_widget
        )  # 这个布局只属于widget
        self.description_layout.setContentsMargins(10, 10, 10, 10)  # 设置适当的边距

        # 描述内容区域
        self.description_content = BodyLabel()
        self.description_content.setWordWrap(True)
        self.description_layout.addWidget(self.description_content)

        self.description_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # 创建滚动区域来包裹内容
        self.description_scroll_area = ScrollArea()
        self.description_scroll_area.setWidget(self.description_area_widget)
        self.description_scroll_area.setWidgetResizable(True)
        self.description_scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.description_scroll_area.setStyleSheet(
            "background-color: transparent; border: none;"
        )

        # 将滚动区域添加到卡片
        card_layout = QVBoxLayout(self.description_area_card)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.addWidget(self.description_scroll_area)

        # ==================== 分割器 ==================== #
        # 创建垂直分割器，实现可调整比例功能
        self.splitter = QSplitter(Qt.Orientation.Vertical)
        self.splitter.setStyleSheet(
            """
            QSplitter::handle:vertical {
                background: transparent;   
            }
            """
        )

        # 创建选项区域容器（仅用于分割器）
        self.option_splitter_widget = QWidget()
        self.option_splitter_layout = QVBoxLayout(self.option_splitter_widget)
        self.option_splitter_layout.addWidget(self.option_area_card)
        self.option_splitter_layout.setContentsMargins(0, 0, 0, 0)

        # 创建描述区域容器（仅用于分割器）
        self.description_splitter_widget = QWidget()
        self.description_splitter_layout = QVBoxLayout(self.description_splitter_widget)
        self.description_splitter_layout.addWidget(self.description_title)
        self.description_splitter_layout.addWidget(self.description_area_card)
        # 设置占用比例
        self.description_splitter_layout.setStretch(0, 1)  # 标题占用1单位
        self.description_splitter_layout.setStretch(1, 99)  # 内容占用99单位
        self.description_splitter_layout.setContentsMargins(0, 0, 0, 0)

        # 添加到分割器
        self.splitter.addWidget(self.option_splitter_widget)  # 上方：选项区域
        self.splitter.addWidget(self.description_splitter_widget)  # 下方：描述区域

        # 设置初始比例
        self.splitter.setSizes([90, 10])  # 90% 和 10% 的初始比例

        # 添加到主布局
        self.main_layout.addWidget(self.title_widget)  # 直接添加标题
        self.main_layout.addWidget(self.splitter)  # 添加分割器
        # 添加主布局间距
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(10)

    # ==================== UI 辅助方法 ==================== #

    def _toggle_description(self, visible=None):
        """切换描述区域的显示/隐藏
        visible: True显示，False隐藏，None切换当前状态
        """
        if visible is None:
            # 切换当前状态
            visible = not self.description_splitter_widget.isVisible()

        if visible:
            self.description_splitter_widget.show()
            # 恢复初始比例
            self.splitter.setSizes([90, 10])
        else:
            self.description_splitter_widget.hide()
            # 让选项区域占据全部空间
            self.splitter.setSizes([100, 0])

    def set_description(self, description: str):
        """设置描述内容"""
        self.description_content.setText("")

        html = markdown.markdown(description).replace("\n", "")
        html = re.sub(
            r"<code>(.*?)</code>",
            r"<span style='color: #009faa;'>\1</span>",
            html,
        )
        html = re.sub(
            r'(<a\s+[^>]*href="[^"]+"[^>]*)>', r'\1 style="color: #009faa;">', html
        )
        html = re.sub(r"<li><p>(.*?)</p></li>", r"<p><strong>◆ </strong>\1</p>", html)
        html = re.sub(r"<ul>(.*?)</ul>", r"\1", html)

        self.description_content.setText(html)

    # ==================== 公共方法 ==================== #

    def reset(self):
        """重置选项区域和描述区域"""
        self._clear_options()
        self._toggle_description(visible=False)
        self.current_task = None

    def _on_config_changed(self, config_id: str):
        """配置切换时重置选项面板"""
        self.reset()

    def set_title(self, title: str):
        """设置标题"""
        self.title_widget.setText(title)

    # ==================== 选项数据管理 ==================== #

    # ==================== 选项数据管理 ==================== #

    def _save_current_options(self):
        """收集当前所有选项控件的值并保存到配置 - 委托给数据管理器"""
        if not self.current_task:
            return
        
        # 特殊处理：完成后设置任务
        if self.current_task.item_id == POST_TASK_ID:
            self._save_post_task_options()
            return
        
        is_resource_setting = self.current_task.item_id == RESOURCE_TASK_ID
        self.data_manager.save_options(
            self.current_task,
            self.option_area_layout,
            is_resource_setting
        )
    
    def _save_post_task_options(self):
        """保存完成后设置选项"""
        if not self.current_task:
            return
        
        # 收集所有复选框状态
        options: dict = {
            "no_action": self.checkbox_no_action.isChecked(),
            "close_emulator": self.checkbox_close_emulator.isChecked(),
            "close_software": self.checkbox_close_software.isChecked(),
            "run_other_config": self.checkbox_run_other_config.isChecked(),
        }
        
        # 如果选择了运行其他配置,保存配置信息
        if self.checkbox_run_other_config.isChecked():
            options["other_config_name"] = self.post_task_config_combo.currentText()
            options["other_config_id"] = self.post_task_config_combo.currentData()
        
        # 保存到任务选项
        self.current_task.task_option.update(options)
        
        # 通知任务服务保存
        if self.service_coordinator and hasattr(self.service_coordinator, 'task_service'):
            self.service_coordinator.task_service.update_task(self.current_task)

    def _organize_controller_options(self, options: dict) -> dict:
        """委托给数据管理器"""
        return self.data_manager.organize_controller_options(options)

    def _flatten_controller_options(self, options: dict) -> dict:
        """委托给数据管理器"""
        return self.data_manager.flatten_controller_options(options)

    # ==================== 任务选项显示 - 主入口 ==================== #

    def show_option(self, item_or_id: TaskItem | ConfigItem | str):
        """显示选项。参数可以是 task_id(str) 或 TaskItem/ConfigItem 对象。

        使用过渡动画：淡出 -> 清空 -> 构建新内容 -> 淡入。
        """
        # 获取对象
        item = item_or_id
        if isinstance(item_or_id, str):
            item = self.task.get_task(item_or_id)
        if not item:
            return

        def build():
            # 初始隐藏描述（构建方法内部会决定是否显示）
            self._toggle_description(False)
            self.current_task = None
            if isinstance(item, TaskItem):
                self.current_task = item
                if item.item_id == RESOURCE_TASK_ID:
                    self._show_resource_setting_option(item)
                elif item.item_id == POST_TASK_ID:
                    self._show_post_task_setting_option(item)
                else:
                    self._show_task_option(item)
            else:
                # ConfigItem 等其它类型暂不显示具体内容
                pass

        self._play_option_transition(build)

    # ==================== 普通任务选项显示 ==================== #

    def _show_task_option(self, item: TaskItem):
        """显示任务选项"""

        def _get_task_info(interface: dict, option: str, item: TaskItem):
            name = interface["option"][option].get(
                "label", interface["option"][option].get("name", option)
            )
            # option 本身就是键名，不需要再获取 name 字段
            obj_name = option
            options = self.Get_Task_List(interface, option)
            current = item.task_option.get(option, None)
            icon_path = interface["option"][option].get("icon", "")
            tooltip = interface["option"][option].get("description", "")
            option_tooltips = {}
            for cases in interface["option"][option]["cases"]:
                option_tooltips[cases["name"]] = cases.get("description", "")
            return name, obj_name, options, current, icon_path, tooltip, option_tooltips

        # TaskService stores interface in attribute 'interface'
        interface = getattr(self.task, "interface", None)
        if not interface:
            # fallback load from file
            interface_path = Path.cwd() / "interface.json"
            if not interface_path.exists():
                return
            with open(interface_path, "r", encoding="utf-8") as f:
                interface = json.load(f)
        target_task = None
        for task_template in interface["task"]:
            if task_template["name"] == item.name:
                target_task = task_template
                break
        if target_task is None:
            logger.warning(f"未找到任务模板: {item.name}")
            return

        # 收集描述内容
        descriptions = []

        # 添加任务描述
        task_description = target_task.get("description")
        if task_description:
            descriptions.append(task_description)

        # 添加文档说明
        task_doc = target_task.get("doc")
        if task_doc:
            descriptions.append(task_doc)

        # 根据是否有描述内容决定是否显示描述区域
        if descriptions:
            self._toggle_description(True)
            combined_description = "\n\n---\n\n".join(descriptions)
            self.set_description(combined_description)
        else:
            # 没有任何描述内容时才关闭描述区域
            self._toggle_description(False)

        # 使用智能排序逻辑添加选项
        # 主选项按照 task 的 option 数组顺序，嵌套选项紧随其父选项之后
        self._add_options_with_order(target_task, interface, item)

    def _add_options_with_order(
        self, target_task: dict, interface: dict, item: TaskItem
    ):
        """按照智能顺序添加选项

        主选项按 task.option 顺序添加，嵌套选项紧随其父选项

        Args:
            target_task: 任务模板配置
            interface: 完整的 interface 配置
            item: 当前任务项
        """
        added_options = set()  # 跟踪已添加的选项，避免重复

        def _get_task_info(option: str):
            """获取选项的显示信息和配置"""
            option_config = interface["option"][option]
            display_name = option_config.get("label", option_config.get("name", option))
            obj_name = option
            options = self.Get_Task_List(interface, option)
            current = item.task_option.get(option, None)

            icon_path = option_config.get("icon", "")
            tooltip = option_config.get("description", "")

            # 收集选项提示信息
            option_tooltips = {}
            for case in option_config.get("cases", []):
                option_tooltips[case["name"]] = case.get("description", "")

            return (
                display_name,
                obj_name,
                options,
                current,
                icon_path,
                tooltip,
                option_tooltips,
                option_config,
            )

        def _get_current_case_config(option_name: str):
            """获取选项当前选中的 case 配置

            如果没有选中或找不到，返回第一个 case
            """
            option_config = interface["option"].get(option_name)
            if not option_config:
                return None

            cases = option_config.get("cases", [])
            if not cases:
                return None

            # 尝试获取当前值对应的 case
            current_value = item.task_option.get(option_name, None)
            if current_value:
                for case in cases:
                    if case.get("name") == current_value:
                        return case

            # 默认返回第一个 case
            return cases[0]

        def _add_option_recursive(option_name: str, depth: int = 0):
            """递归添加选项及其嵌套选项

            Args:
                option_name: 选项名称
                depth: 递归深度，防止无限递归
            """
            # 防止重复添加和无限递归
            if option_name in added_options or depth > 10:
                return

            added_options.add(option_name)

            # 获取选项配置
            option_config = interface["option"].get(option_name)
            if not option_config:
                logger.warning(f"未找到选项配置: {option_name}")
                return

            option_type = option_config.get("type", "select")
            created_combo = None

            # 根据选项类型创建对应的控件
            if "inputs" in option_config and isinstance(
                option_config.get("inputs"), list
            ):
                # 多输入项类型（如"自定义关卡"）
                self._add_multi_input_option(option_name, option_config, item)
            elif option_type == "input":
                (
                    display_name,
                    obj_name,
                    options,
                    current,
                    icon_path,
                    tooltip,
                    option_tooltips,
                    opt_cfg,
                ) = _get_task_info(option_name)
                created_combo = self._add_combox_option(
                    display_name,
                    obj_name,
                    options,
                    current,
                    icon_path,
                    editable=True,
                    tooltip=tooltip,
                    option_tooltips=option_tooltips,
                    option_config=opt_cfg,
                    skip_initial_nested=True,
                    block_signals=True,
                    return_widget=True,
                )
            else:
                # 普通下拉框
                (
                    display_name,
                    obj_name,
                    options,
                    current,
                    icon_path,
                    tooltip,
                    option_tooltips,
                    opt_cfg,
                ) = _get_task_info(option_name)
                created_combo = self._add_combox_option(
                    display_name,
                    obj_name,
                    options,
                    current,
                    icon_path,
                    editable=False,
                    tooltip=tooltip,
                    option_tooltips=option_tooltips,
                    option_config=opt_cfg,
                    skip_initial_nested=True,
                    block_signals=True,
                    return_widget=True,
                )

            # 处理嵌套选项
            if (
                created_combo
                and option_type in ["select", "input"]
                and option_config.get("cases")
            ):
                current_case = _get_current_case_config(option_name)
                if current_case and "option" in current_case:
                    current_value = item.task_option.get(option_name, None)
                    if current_value:
                        self._update_nested_options(
                            created_combo, current_value, recursive=True
                        )

        # 按照 task 的 option 数组顺序添加选项
        for option in target_task.get("option", []):
            _add_option_recursive(option)

    def Get_Task_List(self, interface: dict, target: str) -> List[str]:
        """根据选项名称获取所有case的name列表。

        Args:
            path (str): 配置文件路径。
            target (str): 选项名称。

        Returns:
            list: 包含所有case的name列表。
        """
        lists = []
        Task_Config = interface["option"][target]["cases"]
        if not Task_Config:
            return []
        Lens = len(Task_Config) - 1
        for i in range(Lens, -1, -1):
            lists.append(Task_Config[i]["name"])
        lists.reverse()
        return lists

    # ==================== 基础任务选项显示 ==================== #

    def _show_resource_setting_option(self, item: TaskItem):
        """显示资源设置选项页面（合并控制器和资源配置）

        包含：
        - 控制器配置（控制器类型、刷新设备、设备选择）
        - 资源配置（资源选择）
        - 控制器特定选项（ADB/Win32，动态切换）
        - 通用选项（GPU、启动前/后程序等）
        """
        self._clear_options()

        # 保存当前任务项供其他方法使用
        self._current_task_item = item

        # 获取 interface 配置
        interface = self.service_coordinator.task.interface
        if not interface:
            logger.warning("未找到任务接口配置")
            return

        # 获取控制器和资源配置列表
        controllers = interface.get("controller", [])
        resources = interface.get("resource", [])

        if not controllers:
            label = BodyLabel(self.tr("No controller configuration found"))
            self.option_area_layout.addWidget(label)
            return

        # 保存配置供后续使用
        self.controller_configs = {c.get("name"): c for c in controllers}
        self.resource_configs = resources

        # 获取当前保存的选项（展平嵌套的 ADB/Win32 配置）
        saved_options = self._flatten_controller_options(item.task_option)
        current_controller_name = str(saved_options.get("controller_type", ""))

        # 1. 控制器类型选择（水平布局：下拉框 + 按钮）
        controller_h_layout = QHBoxLayout()
        controller_h_layout.setObjectName("controller_type_layout")

        # 控制器类型下拉框
        controller_v_layout = QVBoxLayout()
        controller_label = BodyLabel(self.tr("Controller Type"))
        controller_label.setStyleSheet("font-weight: bold;")
        controller_v_layout.addWidget(controller_label)

        self.controller_type_combo = ComboBox()
        self.controller_type_combo.setObjectName("controller_type")
        self.controller_type_combo.setMaximumWidth(400)

        # 使用 label 作为显示文本，name 作为内部值
        for i, controller in enumerate(controllers):
            name = controller.get("name", "")
            label = controller.get("label", name)
            # 去掉 $ 前缀（如果有）
            if label.startswith("$"):
                label = label[1:]
            self.controller_type_combo.addItem(label)
            self.controller_type_combo.setItemData(i, name)

        # 设置当前选中项
        if current_controller_name:
            for i in range(self.controller_type_combo.count()):
                if self.controller_type_combo.itemData(i) == current_controller_name:
                    self.controller_type_combo.setCurrentIndex(i)
                    break

        controller_v_layout.addWidget(self.controller_type_combo)
        controller_h_layout.addLayout(controller_v_layout, stretch=3)

        # 设备刷新按钮
        button_v_layout = QVBoxLayout()
        button_v_layout.addSpacing(24)

        self.refresh_devices_button = PrimaryPushButton(self.tr("Refresh Devices"))
        self.refresh_devices_button.setObjectName("refresh_devices_button")
        self.refresh_devices_button.clicked.connect(self._on_refresh_devices_clicked)
        button_v_layout.addWidget(self.refresh_devices_button)

        controller_h_layout.addLayout(button_v_layout, stretch=1)
        self.option_area_layout.addLayout(controller_h_layout)

        # 2. 设备选择下拉框
        device_v_layout = QVBoxLayout()
        device_v_layout.setObjectName("device_layout")

        device_label = BodyLabel(self.tr("Select Device"))
        device_label.setStyleSheet("font-weight: bold;")
        device_v_layout.addWidget(device_label)

        self.device_combo = ComboBox()
        self.device_combo.setObjectName("device")
        self.device_combo.setMaximumWidth(400)

        # 从保存的配置中构建设备信息并填充到下拉框
        self._populate_saved_device(saved_options, current_controller_name)

        # 连接设备选择改变信号
        self.device_combo.currentIndexChanged.connect(
            lambda: self._on_device_selected_in_resource_setting(item)
        )

        device_v_layout.addWidget(self.device_combo)
        self.option_area_layout.addLayout(device_v_layout)

        # 3. 资源选择下拉框容器（根据控制器类型过滤）
        self.resource_combo_layout = QVBoxLayout()
        self.resource_combo_layout.setObjectName("resource_combo_layout")
        self.option_area_layout.addLayout(self.resource_combo_layout)

        # 4. 创建容器用于存放动态选项
        self.controller_specific_options_layout = QVBoxLayout()
        self.controller_specific_options_layout.setObjectName("controller_specific_options")
        self.option_area_layout.addLayout(self.controller_specific_options_layout)

        # 5. 通用选项容器
        self.controller_common_options_layout = QVBoxLayout()
        self.controller_common_options_layout.setObjectName("controller_common_options")
        self.option_area_layout.addLayout(self.controller_common_options_layout)

        # 连接控制器类型变化信号
        self.controller_type_combo.currentIndexChanged.connect(
            lambda: self._on_resource_setting_controller_changed(item, clear_device=True)
        )

        # 初始化显示对应的选项
        self._on_resource_setting_controller_changed(item, clear_device=False)

        # 如果有保存的设备信息，手动触发一次自动填充
        if self.device_combo.count() > 0 and self.device_combo.currentIndex() >= 0:
            logger.info(
                f"手动触发设备自动填充，设备数量: {self.device_combo.count()}, 当前索引: {self.device_combo.currentIndex()}"
            )
            self._on_device_selected_in_resource_setting(item)
        else:
            logger.debug(
                f"跳过手动触发自动填充，设备数量: {self.device_combo.count()}, 当前索引: {self.device_combo.currentIndex()}"
            )

    def _on_resource_setting_controller_changed(
        self, item: TaskItem, clear_device: bool = True
    ):
        """资源设置页面中控制器类型改变时的回调

        Args:
            item: 任务项
            clear_device: 是否清空设备下拉框（初始化时为 False，用户切换控制器时为 True）
        """
        # 获取当前选中的控制器配置
        current_name = self.controller_type_combo.currentData()
        if not current_name or current_name not in self.controller_configs:
            return

        controller_config = self.controller_configs[current_name]
        controller_type = controller_config.get("type", "").lower()

        # 更新控制器类型下拉框的 tooltip
        description = controller_config.get("description", "")
        if description:
            self.controller_type_combo.setToolTip(description)
            for child in self.controller_type_combo.children():
                if isinstance(child, ToolTipFilter):
                    self.controller_type_combo.removeEventFilter(child)
                    child.deleteLater()
            self.controller_type_combo.installEventFilter(
                ToolTipFilter(self.controller_type_combo, 0, ToolTipPosition.TOP)
            )
        else:
            self.controller_type_combo.setToolTip("")

        # 清空设备下拉框（仅在用户切换控制器时，初始化时保留从配置加载的设备）
        if clear_device:
            self.device_combo.clear()
            # 清空后，从保存的配置重新加载设备信息
            saved_options = item.task_option
            self._populate_saved_device(saved_options, current_name)

        # 更新资源下拉框（根据控制器过滤）
        self._update_resource_options(item, current_name)

        # 清空并重新创建特定选项
        self._clear_layout(self.controller_specific_options_layout)

        saved_options = item.task_option
        # 将嵌套配置展平，以便从中读取字段值
        flattened_options = self._flatten_controller_options(saved_options)

        # 根据类型显示对应选项
        if controller_type == "adb":
            self._show_adb_options(flattened_options)
        elif controller_type == "win32":
            self._show_win32_options(flattened_options)

        # 显示通用选项
        self._clear_layout(self.controller_common_options_layout)
        self._show_controller_common_options(flattened_options)

        # 【新增】根据控制器类型显示对应的高级选项
        # 默认隐藏，可通过此方法显示
        # self._toggle_advanced_options(controller_type=controller_type, show=True)

        # 如果设备下拉框有内容，触发自动填充
        if self.device_combo.count() > 0 and self.device_combo.currentIndex() >= 0:
            if hasattr(self, "_current_task_item"):
                logger.debug("控制器类型改变，触发设备自动填充")
                self._on_device_selected_in_resource_setting(self._current_task_item)

    def _on_device_selected_in_resource_setting(self, item: TaskItem):
        """资源设置页面中设备选择改变时的回调 - 自动填充相关字段"""
        # 获取当前选中的设备数据（完整的设备信息字典）
        device_data = self.device_combo.currentData()

        logger.info(f"设备选择改变，device_data 类型: {type(device_data)}")
        logger.info(f"设备选择改变，device_data 内容: {device_data}")

        if not device_data or not isinstance(device_data, dict):
            logger.warning("设备数据无效或不是字典类型")
            self._save_current_options()
            return

        # 获取当前控制器类型
        current_name = self.controller_type_combo.currentData()
        if not current_name or current_name not in self.controller_configs:
            logger.warning(f"控制器类型无效: {current_name}")
            self._save_current_options()
            return

        controller_config = self.controller_configs[current_name]
        controller_type = controller_config.get("type", "").lower()
        device_type = device_data.get("type", "")

        logger.info(f"控制器类型: {controller_type}, 设备类型: {device_type}")

        # 根据设备类型自动填充字段
        if device_type == "adb" and controller_type == "adb":
            # ADB 设备信息
            # device_data 结构:
            # {
            #   "type": "adb",
            #   "name": "MuMuPlayer12",
            #   "adb_path": "/path/to/adb",
            #   "address": "127.0.0.1:16384",
            #   "screencap_methods": [...],
            #   "input_methods": [...],
            #   "config": {...}
            # }

            import json

            logger.info("开始自动填充 ADB 字段")

            # 1. ADB 路径（adb 可执行文件的路径）
            # adb_path 可能是 Path 对象，需要转换为字符串
            adb_path = device_data.get("adb_path", "")
            adb_path_str = str(adb_path) if adb_path else ""
            logger.info(f"尝试填充 adb_path: {adb_path_str}")

            # 尝试查找 PathLineEdit 或 LineEdit
            adb_path_widget = self.findChild(PathLineEdit, "adb_path") or self.findChild(LineEdit, "adb_path")
            if adb_path_widget:
                adb_path_widget.setText(adb_path_str)
                logger.info(f"✓ 成功填充 adb_path: {adb_path_str}")
            else:
                logger.error("✗ 未找到 adb_path 控件")

            # 2. ADB 连接地址（完整的设备地址：IP:Port 或设备 ID）
            # 填充到 adb_port 字段（这个字段名有误导性，实际是连接地址）
            device_address = device_data.get("address", "")
            logger.info(f"尝试填充 adb_port (连接地址): {device_address}")

            adb_port_widget = self.findChild(LineEdit, "adb_port")
            if adb_port_widget:
                adb_port_widget.setText(device_address)
                logger.info(f"✓ 成功填充 adb_port (连接地址): {device_address}")
            else:
                logger.error("✗ 未找到 adb_port 控件")

            # 3. 设备名称（用于显示和识别）
            # 注意：adb_device_name 字段在保存时会映射为 adb.device_name
            device_name = device_data.get("name", "")
            if device_name:
                # 创建一个隐藏的控件来存储设备名称
                adb_device_name_widget = self.findChild(LineEdit, "adb_device_name")
                if not adb_device_name_widget:
                    # 如果控件不存在，创建一个隐藏的
                    adb_device_name_widget = LineEdit()
                    adb_device_name_widget.setObjectName("adb_device_name")
                    adb_device_name_widget.setVisible(False)
                    adb_device_name_widget.textChanged.connect(
                        lambda: self._save_current_options()
                    )
                    self.controller_specific_options_layout.addWidget(
                        adb_device_name_widget
                    )
                adb_device_name_widget.setText(device_name)
                logger.info(f"✓ 成功填充 adb_device_name: {device_name}")

            # 4. ADB 截图方法（screencap_methods，整数位掩码）
            screencap_methods = device_data.get("screencap_methods", 0)
            if screencap_methods:
                # 现在是下拉框，需要设置选中项
                adb_screenshot_combo = self.findChild(ComboBox, "adb_screenshot_method")
                if adb_screenshot_combo:
                    # 阻止信号避免触发多次保存
                    adb_screenshot_combo.blockSignals(True)
                    # 查找匹配的选项
                    for i in range(adb_screenshot_combo.count()):
                        if adb_screenshot_combo.itemData(i) == str(screencap_methods):
                            adb_screenshot_combo.setCurrentIndex(i)
                            logger.info(
                                f"✓ 成功填充 adb_screenshot_method: {screencap_methods}"
                            )
                            break
                    else:
                        # 如果没有匹配的选项，存储为原始值
                        adb_screenshot_combo.setProperty(
                            "original_value", str(screencap_methods)
                        )
                        adb_screenshot_combo.setCurrentIndex(0)
                        logger.info(
                            f"⚠ ADB 截图方法 {screencap_methods} 不在选项中，使用默认值"
                        )
                    adb_screenshot_combo.blockSignals(False)
                else:
                    logger.error("✗ 未找到 adb_screenshot_method 控件")

            # 5. ADB 输入方法（input_methods，整数位掩码）
            input_methods = device_data.get("input_methods", 0)
            if input_methods:
                # 现在是下拉框，需要设置选中项
                adb_input_combo = self.findChild(ComboBox, "adb_input_method")
                if adb_input_combo:
                    # 阻止信号避免触发多次保存
                    adb_input_combo.blockSignals(True)
                    # 查找匹配的选项
                    for i in range(adb_input_combo.count()):
                        if adb_input_combo.itemData(i) == str(input_methods):
                            adb_input_combo.setCurrentIndex(i)
                            logger.info(f"✓ 成功填充 adb_input_method: {input_methods}")
                            break
                    else:
                        # 如果没有匹配的选项，存储为原始值
                        adb_input_combo.setProperty(
                            "original_value", str(input_methods)
                        )
                        adb_input_combo.setCurrentIndex(0)
                        logger.info(
                            f"⚠ ADB 输入方法 {input_methods} 不在选项中，使用默认值"
                        )
                    adb_input_combo.blockSignals(False)
                else:
                    logger.error("✗ 未找到 adb_input_method 控件")

            # 6. ADB config（额外配置信息，如 MuMu 模拟器配置）
            config = device_data.get("config", {})
            if config:
                config_widget = self.findChild(LineEdit, "adb_config")
                if config_widget:
                    # 将 config 转换为 JSON 字符串保存
                    config_json = json.dumps(config, ensure_ascii=False)
                    config_widget.setText(config_json)
                    logger.info(f"自动填充 adb_config: {config_json}")

        elif device_type == "win32" and controller_type == "win32":
            # Win32 窗口信息
            # device_data 结构:
            # {
            #   "type": "win32",
            #   "hwnd": 722524,
            #   "class_name": "ApplicationFrameWindow",
            #   "window_name": "Visual Studio"
            # }

            logger.info("开始自动填充 Win32 字段")

            # 1. 窗口句柄（HWND）
            hwnd = device_data.get("hwnd", "")
            if hwnd:
                hwnd_widget = self.findChild(LineEdit, "hwnd")
                if hwnd_widget:
                    hwnd_widget.setText(str(hwnd))
                    logger.info(f"✓ 成功填充 hwnd: {hwnd}")
                else:
                    logger.error("✗ 未找到 hwnd 控件")

            # 2. 窗口名称（用于显示和识别）
            # 注意：win32_device_name 字段在保存时会映射为 win32.device_name
            window_name = device_data.get("window_name", "")
            if window_name:
                # 创建一个隐藏的控件来存储窗口名称
                win32_device_name_widget = self.findChild(LineEdit, "win32_device_name")
                if not win32_device_name_widget:
                    # 如果控件不存在，创建一个隐藏的
                    win32_device_name_widget = LineEdit()
                    win32_device_name_widget.setObjectName("win32_device_name")
                    win32_device_name_widget.setVisible(False)
                    win32_device_name_widget.textChanged.connect(
                        lambda: self._save_current_options()
                    )
                    self.controller_specific_options_layout.addWidget(
                        win32_device_name_widget
                    )
                win32_device_name_widget.setText(window_name)
                logger.info(f"✓ 成功填充 win32_device_name: {window_name}")

        # 保存选项
        self._save_current_options()

    def _update_resource_options(self, item: TaskItem, controller_name: str):
        """更新资源选择下拉框（根据控制器过滤）"""
        # 清空现有的资源下拉框
        self._clear_layout(self.resource_combo_layout)

        # 过滤资源列表
        filtered_resources = []
        for resource in self.resource_configs:
            controller_list = resource.get("controller", [])
            # controller 字段为空或者包含当前控制器名称
            if not controller_list or controller_name in controller_list:
                filtered_resources.append(resource)

        if not filtered_resources:
            return

        # 获取当前保存的资源选项
        saved_options = item.task_option
        current_value = saved_options.get("resource", "")

        # 检查当前选中的资源是否在过滤后的列表中
        filtered_resource_names = [r.get("name", "") for r in filtered_resources]
        if current_value and current_value not in filtered_resource_names:
            # 当前选中的资源不适用于新的控制器，清空选择
            current_value = ""

        # 创建垂直布局
        v_layout = QVBoxLayout()
        v_layout.setObjectName("resource_layout")

        # 标签
        label = BodyLabel(self.tr("Resource"))
        label.setStyleSheet("font-weight: bold;")
        v_layout.addWidget(label)

        # 下拉框
        combo = ComboBox()
        combo.setObjectName("resource")
        combo.setMaximumWidth(400)

        # 添加过滤后的资源
        for i, resource in enumerate(filtered_resources):
            name = resource.get("name", "")
            # 使用 label，如果没有则使用 name
            display_label = resource.get("label", "")
            if not display_label:
                display_label = name
            # 去掉 $ 前缀（如果有）
            if display_label.startswith("$"):
                display_label = display_label[1:]
            combo.addItem(display_label)
            combo.setItemData(i, name)

        # 设置当前选中项（通过 name 匹配）
        if current_value:
            for i in range(combo.count()):
                if combo.itemData(i) == current_value:
                    combo.setCurrentIndex(i)
                    break

        # 连接信号
        combo.currentIndexChanged.connect(lambda: self._save_current_options())

        v_layout.addWidget(combo)
        self.resource_combo_layout.addLayout(v_layout)

    def _show_controller_option(self, item: TaskItem):
        """显示控制器选项页面

        包含：
        - 控制器类型选择下拉框（从 interface.json 读取）
        - 填充设备列表按钮（根据类型调用不同方法）
        - 设备选择下拉框（由按钮填充）
        - 根据控制器类型显示不同的特定选项（ADB/Win32）
        - 通用选项（GPU、启动前/后程序等）
        """
        self._clear_options()

        # 获取 interface 配置
        interface = self.service_coordinator.task.interface
        if not interface:
            logger.warning("未找到任务接口配置")
            return
        # 获取控制器配置列表
        controllers = interface.get("controller", [])
        if not controllers:
            label = BodyLabel(self.tr("No controller configuration found"))
            self.option_area_layout.addWidget(label)
            return

        # 保存控制器配置供后续使用
        self.controller_configs = {c.get("name"): c for c in controllers}

        # 获取当前保存的选项
        saved_options = item.task_option
        current_controller_name = saved_options.get("controller_type", "")

        # 1. 控制器类型选择（水平布局：下拉框 + 按钮）
        controller_h_layout = QHBoxLayout()
        controller_h_layout.setObjectName("controller_type_layout")

        # 控制器类型下拉框
        controller_v_layout = QVBoxLayout()
        controller_label = BodyLabel(self.tr("Controller Type"))
        controller_label.setStyleSheet("font-weight: bold;")
        controller_v_layout.addWidget(controller_label)

        self.controller_type_combo = ComboBox()
        self.controller_type_combo.setObjectName("controller_type")
        self.controller_type_combo.setMaximumWidth(400)  # 限制最大宽度

        # 使用 label 作为显示文本，name 作为内部值
        for i, controller in enumerate(controllers):
            name = controller.get("name", "")
            label = controller.get("label", name)
            # 去掉 $ 前缀（如果有）
            if label.startswith("$"):
                label = label[1:]
            self.controller_type_combo.addItem(label)
            self.controller_type_combo.setItemData(i, name)

        # 设置当前选中项
        if current_controller_name:
            for i in range(self.controller_type_combo.count()):
                if self.controller_type_combo.itemData(i) == current_controller_name:
                    self.controller_type_combo.setCurrentIndex(i)
                    break

        controller_v_layout.addWidget(self.controller_type_combo)
        controller_h_layout.addLayout(controller_v_layout, stretch=3)

        # 设备列表填充按钮
        button_v_layout = QVBoxLayout()
        button_v_layout.addSpacing(24)  # 对齐下拉框

        self.refresh_devices_button = PrimaryPushButton(self.tr("Refresh Devices"))
        self.refresh_devices_button.setObjectName("refresh_devices_button")
        self.refresh_devices_button.clicked.connect(self._on_refresh_devices_clicked)
        button_v_layout.addWidget(self.refresh_devices_button)

        controller_h_layout.addLayout(button_v_layout, stretch=1)
        self.option_area_layout.addLayout(controller_h_layout)

        # 2. 设备选择下拉框（需要通过按钮填充）
        device_v_layout = QVBoxLayout()
        device_v_layout.setObjectName("device_layout")

        device_label = BodyLabel(self.tr("Select Device"))
        device_label.setStyleSheet("font-weight: bold;")
        device_v_layout.addWidget(device_label)

        self.device_combo = ComboBox()
        self.device_combo.setObjectName("device")
        self.device_combo.setMaximumWidth(400)  # 限制最大宽度

        # 保存时使用 userData（address 或 hwnd），而不是显示文本
        self.device_combo.currentIndexChanged.connect(
            lambda: self._save_current_options()
        )

        current_device = saved_options.get("device", "")
        if current_device:
            # 初始化时添加已保存的设备（显示和存储都使用相同值）
            # 确保转换为字符串（可能是 hwnd 整数）
            self.device_combo.addItem(str(current_device))
            self.device_combo.setItemData(0, current_device)
            self.device_combo.setCurrentIndex(0)

        device_v_layout.addWidget(self.device_combo)
        self.option_area_layout.addLayout(device_v_layout)

        # 3. 创建容器用于存放动态选项（ADB 或 Win32 特定选项）
        self.controller_specific_options_layout = QVBoxLayout()
        self.controller_specific_options_layout.setObjectName(
            "controller_specific_options"
        )
        self.option_area_layout.addLayout(self.controller_specific_options_layout)

        # 4. 通用选项容器
        self.controller_common_options_layout = QVBoxLayout()
        self.controller_common_options_layout.setObjectName("controller_common_options")
        self.option_area_layout.addLayout(self.controller_common_options_layout)

        # 连接控制器类型变化信号
        self.controller_type_combo.currentIndexChanged.connect(
            lambda: self._on_controller_type_changed(item)
        )

        # 初始化显示对应的选项
        self._on_controller_type_changed(item)

    def _on_controller_type_changed(self, item: TaskItem):
        """控制器类型改变时的回调"""
        # 获取当前选中的控制器配置
        current_name = self.controller_type_combo.currentData()
        if not current_name or current_name not in self.controller_configs:
            return

        controller_config = self.controller_configs[current_name]
        controller_type = controller_config.get("type", "").lower()

        # 更新控制器类型下拉框的 tooltip 为描述
        description = controller_config.get("description", "")
        if description:
            self.controller_type_combo.setToolTip(description)
            # 移除旧的 ToolTipFilter（如果有）
            for child in self.controller_type_combo.children():
                if isinstance(child, ToolTipFilter):
                    self.controller_type_combo.removeEventFilter(child)
                    child.deleteLater()
            # 安装新的 ToolTipFilter
            self.controller_type_combo.installEventFilter(
                ToolTipFilter(self.controller_type_combo, 0, ToolTipPosition.TOP)
            )
        else:
            # 没有描述时清空 tooltip
            self.controller_type_combo.setToolTip("")

        # 清空设备下拉框
        self.device_combo.clear()

        # 清空并重新创建特定选项
        self._clear_layout(self.controller_specific_options_layout)

        saved_options = item.task_option
        # 将嵌套配置展平，以便从中读取字段值
        flattened_options = self._flatten_controller_options(saved_options)

        # 根据类型显示对应选项
        if controller_type == "adb":
            self._show_adb_options(flattened_options)
        elif controller_type == "win32":
            self._show_win32_options(flattened_options)

        # 显示通用选项
        self._clear_layout(self.controller_common_options_layout)
        self._show_controller_common_options(flattened_options)

    def _show_adb_options(self, saved_options: dict):
        """显示 ADB 特定选项"""
        # 文本输入框选项 - 区分路径和普通输入
        # (obj_name, label_text, default_value, tooltip_text, is_path)
        text_options = [
            ("adb_path", self.tr("ADB Path"), None, self.tr("Path to adb executable"), True),
            (
                "adb_port",
                self.tr("ADB Connection Address"),
                None,
                self.tr("Device connection address (IP:Port or device ID)"),
                False,
            ),
            (
                "emulator_address",
                self.tr("Emulator Launch Path"),
                None,
                self.tr("Path to emulator executable for launching"),
                True,
            ),
            (
                "emulator_launch_args",
                self.tr("Emulator Launch Args"),
                "",
                self.tr("Arguments for launching emulator"),
                False,
            ),
        ]

        for obj_name, label_text, default_value, tooltip_text, is_path in text_options:
            v_layout = QVBoxLayout()
            v_layout.setObjectName(f"{obj_name}_layout")

            label = BodyLabel(label_text)
            
            # 根据是否为路径类型创建不同的输入控件
            if is_path:
                line_edit = PathLineEdit()
            else:
                line_edit = LineEdit()
                
            line_edit.setObjectName(obj_name)
            # 如果 default_value 是 None，则使用空字符串
            actual_default = "" if default_value is None else default_value

            # 阻止信号，避免在初始化时触发保存
            line_edit.blockSignals(True)
            line_edit.setText(str(saved_options.get(obj_name, actual_default)))
            line_edit.blockSignals(False)

            line_edit.setToolTip(tooltip_text)
            label.setToolTip(tooltip_text)

            # 连接信号
            line_edit.textChanged.connect(lambda: self._save_current_options())

            v_layout.addWidget(label)
            v_layout.addWidget(line_edit)

            self.controller_specific_options_layout.addLayout(v_layout)

        # 添加启动超时时间 SpinBox
        timeout_layout = QVBoxLayout()
        timeout_layout.setObjectName("emulator_launch_timeout_layout")
        
        timeout_label = BodyLabel(self.tr("Emulator Launch Timeout (s)"))
        timeout_spinbox = SpinBox()
        timeout_spinbox.setObjectName("emulator_launch_timeout")
        timeout_spinbox.setRange(1, 3600)
        timeout_spinbox.setSuffix(" s")
        
        timeout_spinbox.blockSignals(True)
        timeout_spinbox.setValue(int(saved_options.get("emulator_launch_timeout", 30)))
        timeout_spinbox.blockSignals(False)
        
        timeout_tooltip = self.tr("Time to wait for emulator startup (seconds)")
        timeout_spinbox.setToolTip(timeout_tooltip)
        timeout_label.setToolTip(timeout_tooltip)
        
        timeout_spinbox.valueChanged.connect(lambda: self._save_current_options())
        
        timeout_layout.addWidget(timeout_label)
        timeout_layout.addWidget(timeout_spinbox)
        
        self.controller_specific_options_layout.addLayout(timeout_layout)

        # ADB 截图方法下拉框
        self._add_adb_screenshot_method_option(saved_options)

        # ADB 输入方法下拉框
        self._add_adb_input_method_option(saved_options)

        # 添加隐藏的 ADB config 字段（用于存储设备的额外配置信息）
        config_line_edit = LineEdit()
        config_line_edit.setObjectName("adb_config")
        config_line_edit.setVisible(False)  # 隐藏此字段
        # 从保存的选项中读取 config（JSON 字符串格式）
        import json

        config_value = str(saved_options.get("adb_config", ""))
        if config_value:
            # 阻止信号，避免初始化时触发保存
            config_line_edit.blockSignals(True)
            config_line_edit.setText(config_value)
            config_line_edit.blockSignals(False)
        config_line_edit.textChanged.connect(lambda: self._save_current_options())
        self.controller_specific_options_layout.addWidget(config_line_edit)

    def _add_adb_screenshot_method_option(self, saved_options: dict, visible: bool = False):
        """添加 ADB 截图方法下拉框
        
        Args:
            saved_options: 保存的选项
            visible: 是否默认显示（资源设置中默认隐藏）
        """
        v_layout = QVBoxLayout()
        v_layout.setObjectName("adb_screenshot_method_layout")

        label = BodyLabel(self.tr("ADB Screenshot Method"))
        label.setStyleSheet("font-weight: bold;")

        combo = ComboBox()
        combo.setObjectName("adb_screenshot_method")
        combo.setMaximumWidth(400)

        # 截图方法选项 (位掩码值)
        screenshot_methods = [
            ("EncodeToFileAndPull", "1"),
            ("Encode", "2"),
            ("RawWithGzip", "4"),
            ("RawByNetcat", "8"),
            ("MinicapDirect", "16"),
            ("MinicapStream", "32"),
            ("EmulatorExtras", "64"),
        ]

        for method_name, method_value in screenshot_methods:
            combo.addItem(method_name)
            combo.setItemData(combo.count() - 1, method_value)

        # 获取原始保存的值
        original_value = saved_options.get("adb_screenshot_method", "1")
        current_value = str(original_value)

        # 检查值是否在映射表中
        valid_values = [method_value for _, method_value in screenshot_methods]
        if current_value not in valid_values:
            # 值不在映射表中，存储原始值用于保存，显示时使用第一个选项
            combo.setProperty("original_value", current_value)
            current_value = "1"

        # 设置下拉框选中项
        combo.blockSignals(True)  # 阻止信号，避免初始化时触发保存
        for i in range(combo.count()):
            if combo.itemData(i) == current_value:
                combo.setCurrentIndex(i)
                break
        combo.blockSignals(False)

        # 连接信号：用户改变选择时标记为已修改
        def on_screenshot_changed():
            combo.setProperty("user_changed", True)
            self._save_current_options()

        combo.currentIndexChanged.connect(on_screenshot_changed)

        v_layout.addWidget(label)
        v_layout.addWidget(combo)
        
        # 设置初始可见性
        if not visible:
            label.setVisible(False)
            combo.setVisible(False)
        
        self.controller_specific_options_layout.addLayout(v_layout)

    def _add_adb_input_method_option(self, saved_options: dict, visible: bool = False):
        """添加 ADB 输入方法下拉框
        
        Args:
            saved_options: 保存的选项
            visible: 是否默认显示（资源设置中默认隐藏）
        """
        v_layout = QVBoxLayout()
        v_layout.setObjectName("adb_input_method_layout")

        label = BodyLabel(self.tr("ADB Input Method"))
        label.setStyleSheet("font-weight: bold;")

        combo = ComboBox()
        combo.setObjectName("adb_input_method")
        combo.setMaximumWidth(400)

        # 输入方法选项 (位掩码值)
        input_methods = [
            ("AdbShell", "1"),
            ("MinitouchAndAdbKey", "2"),
            ("Maatouch", "4"),
            ("EmulatorExtras", "8"),
        ]

        for method_name, method_value in input_methods:
            combo.addItem(method_name)
            combo.setItemData(combo.count() - 1, method_value)

        # 获取原始保存的值
        original_value = saved_options.get("adb_input_method", "1")
        current_value = str(original_value)

        # 检查值是否在映射表中
        valid_values = [method_value for _, method_value in input_methods]
        if current_value not in valid_values:
            # 值不在映射表中，存储原始值用于保存，显示时使用第一个选项
            combo.setProperty("original_value", current_value)
            current_value = "1"

        # 设置下拉框选中项
        combo.blockSignals(True)  # 阻止信号，避免初始化时触发保存
        for i in range(combo.count()):
            if combo.itemData(i) == current_value:
                combo.setCurrentIndex(i)
                break
        combo.blockSignals(False)

        # 连接信号：用户改变选择时标记为已修改
        def on_index_changed():
            combo.setProperty("user_changed", True)
            self._save_current_options()

        combo.currentIndexChanged.connect(on_index_changed)

        v_layout.addWidget(label)
        v_layout.addWidget(combo)
        
        # 设置初始可见性
        if not visible:
            label.setVisible(False)
            combo.setVisible(False)
        
        self.controller_specific_options_layout.addLayout(v_layout)

    def _show_win32_options(self, saved_options: dict):
        """显示 Win32 特定选项"""
        # (obj_name, label_text, default_value, tooltip_text, is_path)
        text_options = [
            (
                "hwnd",
                self.tr("Window Handle (HWND)"),
                "",
                self.tr("Window handle identifier"),
                False,
            ),
            (
                "app_path",
                self.tr("Application Path"),
                "",
                self.tr("Path to application executable"),
                True,
            ),
            (
                "app_launch_args",
                self.tr("Application Launch Args"),
                "",
                self.tr("Arguments for launching application"),
                False,
            ),
        ]

        for obj_name, label_text, default_value, tooltip_text, is_path in text_options:
            v_layout = QVBoxLayout()
            v_layout.setObjectName(f"{obj_name}_layout")

            label = BodyLabel(label_text)
            
            # 根据是否为路径类型创建不同的输入控件
            if is_path:
                line_edit = PathLineEdit()
            else:
                line_edit = LineEdit()
                
            line_edit.setObjectName(obj_name)

            # 阻止信号，避免初始化时触发保存
            line_edit.blockSignals(True)
            line_edit.setText(str(saved_options.get(obj_name, default_value)))
            line_edit.blockSignals(False)

            line_edit.setToolTip(tooltip_text)
            label.setToolTip(tooltip_text)

            # 连接信号
            line_edit.textChanged.connect(lambda: self._save_current_options())

            v_layout.addWidget(label)
            v_layout.addWidget(line_edit)

            self.controller_specific_options_layout.addLayout(v_layout)

        # 添加应用启动超时时间 SpinBox
        timeout_layout = QVBoxLayout()
        timeout_layout.setObjectName("app_launch_timeout_layout")
        
        timeout_label = BodyLabel(self.tr("Application Launch Timeout (s)"))
        timeout_spinbox = SpinBox()
        timeout_spinbox.setObjectName("app_launch_timeout")
        timeout_spinbox.setRange(1, 3600)
        timeout_spinbox.setSuffix(" s")
        
        timeout_spinbox.blockSignals(True)
        timeout_spinbox.setValue(int(saved_options.get("app_launch_timeout", 30)))
        timeout_spinbox.blockSignals(False)
        
        timeout_tooltip = self.tr("Time to wait for application startup (seconds)")
        timeout_spinbox.setToolTip(timeout_tooltip)
        timeout_label.setToolTip(timeout_tooltip)
        
        timeout_spinbox.valueChanged.connect(lambda: self._save_current_options())
        
        timeout_layout.addWidget(timeout_label)
        timeout_layout.addWidget(timeout_spinbox)
        
        self.controller_specific_options_layout.addLayout(timeout_layout)

        # Win32 截图方法下拉框
        self._add_win32_screenshot_method_option(saved_options)

        # Win32 输入方法下拉框
        self._add_win32_input_method_option(saved_options)

    def _add_win32_screenshot_method_option(self, saved_options: dict, visible: bool = False):
        """添加 Win32 截图方法下拉框
        
        Args:
            saved_options: 保存的选项
            visible: 是否默认显示（资源设置中默认隐藏）
        """
        v_layout = QVBoxLayout()
        v_layout.setObjectName("win32_screenshot_method_layout")

        label = BodyLabel(self.tr("Win32 Screenshot Method"))
        label.setStyleSheet("font-weight: bold;")

        combo = ComboBox()
        combo.setObjectName("win32_screenshot_method")
        combo.setMaximumWidth(400)

        # Win32 截图方法选项
        screenshot_methods = [
            ("GDI", "1"),
            ("FramePool", "2"),
            ("DXGI_DesktopDup", "4"),
        ]

        for method_name, method_value in screenshot_methods:
            combo.addItem(method_name)
            combo.setItemData(combo.count() - 1, method_value)

        # 设置当前值,默认为 "1" (GDI)
        current_value = str(saved_options.get("win32_screenshot_method", "1"))
        combo.blockSignals(True)  # 阻止信号，避免初始化时触发保存
        for i in range(combo.count()):
            if combo.itemData(i) == current_value:
                combo.setCurrentIndex(i)
                break
        combo.blockSignals(False)

        combo.currentIndexChanged.connect(lambda: self._save_current_options())

        v_layout.addWidget(label)
        v_layout.addWidget(combo)
        
        # 设置初始可见性
        if not visible:
            label.setVisible(False)
            combo.setVisible(False)
        
        self.controller_specific_options_layout.addLayout(v_layout)

    def _add_win32_input_method_option(self, saved_options: dict, visible: bool = False):
        """添加 Win32 输入方法下拉框
        
        Args:
            saved_options: 保存的选项
            visible: 是否默认显示（资源设置中默认隐藏）
        """
        v_layout = QVBoxLayout()
        v_layout.setObjectName("win32_input_method_layout")

        label = BodyLabel(self.tr("Win32 Input Method"))
        label.setStyleSheet("font-weight: bold;")

        combo = ComboBox()
        combo.setObjectName("win32_input_method")
        combo.setMaximumWidth(400)

        # Win32 输入方法选项
        input_methods = [
            ("Seize", "1"),
            ("SendMessage", "2"),
        ]

        for method_name, method_value in input_methods:
            combo.addItem(method_name)
            combo.setItemData(combo.count() - 1, method_value)

        # 设置当前值,默认为 "1" (Seize)
        current_value = str(saved_options.get("win32_input_method", "1"))
        combo.blockSignals(True)  # 阻止信号，避免初始化时触发保存
        for i in range(combo.count()):
            if combo.itemData(i) == current_value:
                combo.setCurrentIndex(i)
                break
        combo.blockSignals(False)

        combo.currentIndexChanged.connect(lambda: self._save_current_options())

        v_layout.addWidget(label)
        v_layout.addWidget(combo)
        
        # 设置初始可见性
        if not visible:
            label.setVisible(False)
            combo.setVisible(False)
        
        self.controller_specific_options_layout.addLayout(v_layout)

    def _show_controller_common_options(self, saved_options: dict):
        """显示控制器通用选项"""
        # GPU 选择下拉框（单独处理）
        self._add_gpu_selection_option(saved_options)

        # 其他文本输入选项 - 区分路径和普通输入
        # (obj_name, label_text, default_value, tooltip_text, is_path)
        text_options = [
            (
                "pre_launch_program",
                self.tr("Pre-Launch Program"),
                "",
                self.tr("Program to run before starting"),
                True,
            ),
            (
                "pre_launch_program_args",
                self.tr("Pre-Launch Program Args"),
                "",
                self.tr("Arguments for pre-launch program"),
                False,
            ),
            (
                "post_launch_program",
                self.tr("Post-Launch Program"),
                "",
                self.tr("Program to run after starting"),
                True,
            ),
            (
                "post_launch_program_args",
                self.tr("Post-Launch Program Args"),
                "",
                self.tr("Arguments for post-launch program"),
                False,
            ),
        ]

        for obj_name, label_text, default_value, tooltip_text, is_path in text_options:
            v_layout = QVBoxLayout()
            v_layout.setObjectName(f"{obj_name}_layout")

            label = BodyLabel(label_text)
            
            # 根据是否为路径类型创建不同的输入控件
            if is_path:
                line_edit = PathLineEdit()
            else:
                line_edit = LineEdit()
                
            line_edit.setObjectName(obj_name)

            # 阻止信号，避免初始化时触发保存
            line_edit.blockSignals(True)
            line_edit.setText(str(saved_options.get(obj_name, default_value)))
            line_edit.blockSignals(False)

            line_edit.setToolTip(tooltip_text)
            label.setToolTip(tooltip_text)

            # 连接信号
            line_edit.textChanged.connect(lambda: self._save_current_options())

            v_layout.addWidget(label)
            v_layout.addWidget(line_edit)

            self.controller_common_options_layout.addLayout(v_layout)

    def _add_gpu_selection_option(self, saved_options: dict, visible: bool = False):
        """添加 GPU 选择下拉框

        Args:
            saved_options: 保存的选项
            visible: 是否默认显示（资源设置中默认隐藏）
        """
        from app.utils.gpu_cache import gpu_cache

        v_layout = QVBoxLayout()
        v_layout.setObjectName("gpu_selection_layout")

        label = BodyLabel(self.tr("GPU Selection"))
        label.setToolTip(self.tr("Select GPU device to use for inference"))

        combo = ComboBox()
        combo.setObjectName("gpu")  # 保存到 "gpu" 字段
        combo.setMaximumWidth(400)

        # 添加特殊选项
        combo.addItem("Auto")
        combo.setItemData(combo.count() - 1, -1)
        combo.addItem("CPU Only")
        combo.setItemData(combo.count() - 1, -2)

        # 添加 GPU 设备
        gpu_info = gpu_cache.get_gpu_info()
        if gpu_info:
            for gpu_id, gpu_name in sorted(gpu_info.items()):
                display_text = f"GPU {gpu_id}: {gpu_name}"
                combo.addItem(display_text)
                combo.setItemData(combo.count() - 1, gpu_id)

        # 设置当前值
        current_gpu = saved_options.get("gpu", -1)
        if current_gpu is not None:
            # 查找对应的索引
            for i in range(combo.count()):
                if combo.itemData(i) == current_gpu:
                    combo.setCurrentIndex(i)
                    break

        # 连接信号
        combo.currentIndexChanged.connect(lambda: self._save_current_options())

        v_layout.addWidget(label)
        v_layout.addWidget(combo)
        
        # 设置初始可见性
        if not visible:
            label.setVisible(False)
            combo.setVisible(False)
        
        self.controller_common_options_layout.addLayout(v_layout)

    def _toggle_advanced_options(self, controller_type: str | None = None, show: bool = True):
        """切换高级选项的显示状态（GPU、截图方法、输入方法）
        
        Args:
            controller_type: 控制器类型 ('adb' 或 'win32')，None 表示隐藏所有
            show: 是否显示
        """
        # GPU 选项（通用，总是根据 show 参数显示/隐藏）
        gpu_layout = self.findChild(QVBoxLayout, "gpu_selection_layout")
        if gpu_layout:
            for i in range(gpu_layout.count()):
                widget = gpu_layout.itemAt(i).widget()
                if widget:
                    widget.setVisible(show)
        
        # ADB 截图和输入方法
        adb_screenshot_layout = self.findChild(QVBoxLayout, "adb_screenshot_method_layout")
        adb_input_layout = self.findChild(QVBoxLayout, "adb_input_method_layout")
        
        show_adb = show and controller_type == "adb"
        if adb_screenshot_layout:
            for i in range(adb_screenshot_layout.count()):
                widget = adb_screenshot_layout.itemAt(i).widget()
                if widget:
                    widget.setVisible(show_adb)
        
        if adb_input_layout:
            for i in range(adb_input_layout.count()):
                widget = adb_input_layout.itemAt(i).widget()
                if widget:
                    widget.setVisible(show_adb)
        
        # Win32 截图和输入方法
        win32_screenshot_layout = self.findChild(QVBoxLayout, "win32_screenshot_method_layout")
        win32_input_layout = self.findChild(QVBoxLayout, "win32_input_method_layout")
        
        show_win32 = show and controller_type == "win32"
        if win32_screenshot_layout:
            for i in range(win32_screenshot_layout.count()):
                widget = win32_screenshot_layout.itemAt(i).widget()
                if widget:
                    widget.setVisible(show_win32)
        
        if win32_input_layout:
            for i in range(win32_input_layout.count()):
                widget = win32_input_layout.itemAt(i).widget()
                if widget:
                    widget.setVisible(show_win32)

    def _populate_saved_device(self, saved_options: dict, controller_name: str):
        """从保存的配置中填充设备信息到下拉框

        Args:
            saved_options: 保存的任务选项
            controller_name: 当前控制器名称
        """
        logger.debug(f"_populate_saved_device 调用: controller_name={controller_name}")
        logger.debug(f"saved_options keys: {list(saved_options.keys())}")

        if not controller_name or controller_name not in self.controller_configs:
            logger.debug("控制器未选择或无效，跳过设备填充")
            return

        controller_config = self.controller_configs[controller_name]
        controller_type = controller_config.get("type", "").lower()

        logger.debug(f"控制器类型: {controller_type}")

        # 将嵌套配置展平，以便读取字段
        flattened_options = self._flatten_controller_options(saved_options)
        logger.debug(f"展平后的选项 keys: {list(flattened_options.keys())}")

        # 从保存的选项中重建设备信息字典
        if controller_type == "adb":
            # 检查是否有 ADB 相关配置（adb_path 或 adb_port）
            adb_path = str(flattened_options.get("adb_path", ""))
            adb_address = str(flattened_options.get("adb_port", ""))
            device_name = str(flattened_options.get("adb_device_name", ""))

            logger.info(f"保存的 adb_path: {adb_path}")
            logger.info(f"保存的 adb_port (address): {adb_address}")
            logger.info(f"保存的 adb_device_name: {device_name}")

            # 如果没有任何 ADB 配置，跳过
            if not adb_path and not adb_address:
                logger.debug("未找到保存的 ADB 配置信息")
                return

            # 构建 ADB 设备信息
            device_data = {
                "type": "adb",
                "name": device_name
                or adb_address
                or "Unknown Device",  # 优先使用保存的名称
                "adb_path": adb_path,
                "address": adb_address,
                "screencap_methods": int(
                    str(flattened_options.get("adb_screenshot_method", "0")) or "0"
                ),
                "input_methods": int(
                    str(flattened_options.get("adb_input_method", "0")) or "0"
                ),
                "config": {},
            }

            logger.debug(
                f"构建的设备数据 - name: {device_data['name']}, address: {device_data['address']}"
            )

            # 尝试解析 adb_config
            import json

            adb_config_str = str(flattened_options.get("adb_config", ""))
            if adb_config_str:
                try:
                    device_data["config"] = json.loads(adb_config_str)
                except json.JSONDecodeError:
                    logger.warning(f"无法解析 adb_config: {adb_config_str}")

            # 添加到下拉框
            display_text = (
                f"{device_data['name']} - {device_data['address']}"
                if device_data["address"]
                else device_data["name"]
            )
            self.device_combo.addItem(display_text)
            self.device_combo.setItemData(0, device_data)
            self.device_combo.setCurrentIndex(0)
            logger.info(f"从保存的配置中加载 ADB 设备: {display_text}")

        elif controller_type == "win32":
            # 从 hwnd 字段读取窗口句柄
            hwnd_str = str(flattened_options.get("hwnd", ""))
            device_name = str(flattened_options.get("win32_device_name", ""))

            if not hwnd_str:
                logger.debug("未找到保存的 Win32 窗口信息")
                return

            # 构建 Win32 窗口信息
            try:
                hwnd_value = int(hwnd_str) if isinstance(hwnd_str, str) else hwnd_str
            except (ValueError, TypeError):
                logger.warning(f"无效的 hwnd 值: {hwnd_str}")
                return

            device_data = {
                "type": "win32",
                "hwnd": hwnd_value,
                "class_name": "",  # 无法从保存的配置中恢复，留空
                "window_name": device_name or str(hwnd_str),  # 优先使用保存的窗口名称
            }

            # 添加到下拉框
            display_text = device_name or str(hwnd_str)  # 显示窗口名称或 hwnd
            self.device_combo.addItem(display_text)
            self.device_combo.setItemData(0, device_data)
            self.device_combo.setCurrentIndex(0)
            logger.info(f"从保存的配置中加载 Win32 窗口: {display_text}")

    def _on_refresh_devices_clicked(self):
        """刷新设备列表按钮点击事件

        根据当前选中的控制器类型调用不同的设备获取方法
        """
        current_name = self.controller_type_combo.currentData()
        if not current_name or current_name not in self.controller_configs:
            logger.warning("未选择控制器类型")
            return

        controller_config = self.controller_configs[current_name]
        controller_type = controller_config.get("type", "").lower()

        # 临时断开信号，避免 clear() 时触发回调
        try:
            self.device_combo.currentIndexChanged.disconnect()
        except TypeError:
            # 信号可能没有连接，忽略错误
            pass
        # 记录当前选中设备数据，以便成功刷新后尝试恢复选择
        previous_index = self.device_combo.currentIndex()
        previous_data = (
            self.device_combo.itemData(previous_index)
            if previous_index >= 0
            else None
        )

        devices = []

        if controller_type == "adb":
            # 调用 ADB 设备获取方法
            devices = self._get_adb_devices()
        elif controller_type == "win32":
            # 调用 Win32 设备获取方法
            devices = self._get_win32_devices()
        else:
            logger.warning(f"未知的控制器类型: {controller_type}")
            devices = []

        # 如果获取失败（为空），保持原有列表与选中项，不清除
        if not devices:
            log_with_ui(
                self.tr("No devices found"),
                "WARNING",
                output=False,
                infobar=True,
                infobar_type="error"
            )
        else:
            # 仅在成功获取设备时清空并重新填充
            self.device_combo.clear()
            self._populate_device_list(devices)

            # 恢复之前的选中项（如果仍然存在）
            if previous_data:
                restored = False
                for i in range(self.device_combo.count()):
                    data = self.device_combo.itemData(i)
                    if not isinstance(data, dict):
                        continue
                    # 匹配逻辑：类型相同 + 关键字段一致
                    if data.get("type") == previous_data.get("type"):
                        if data.get("type") == "adb" and data.get("address") == previous_data.get("address"):
                            self.device_combo.setCurrentIndex(i)
                            restored = True
                            break
                        if data.get("type") == "win32" and data.get("hwnd") == previous_data.get("hwnd"):
                            self.device_combo.setCurrentIndex(i)
                            restored = True
                            break
                # 若未恢复旧选中，保持当前自动选中项（_populate_device_list 内已处理）
                if restored:
                    logger.info("刷新成功，已恢复之前选中的设备")
                else:
                    logger.info("刷新成功，未找到与之前选中设备匹配的项")

        # 填充完设备后重新连接信号
        if hasattr(self, "_current_task_item"):
            self.device_combo.currentIndexChanged.connect(
                lambda: self._on_device_selected_in_resource_setting(
                    self._current_task_item
                )
            )
            # 手动触发一次，填充当前选中设备的信息
            if self.device_combo.count() > 0 and self.device_combo.currentIndex() >= 0:
                self._on_device_selected_in_resource_setting(self._current_task_item)

    def _get_adb_devices(self):
        """委托给设备管理器"""
        return self.device_manager.get_adb_devices()

    def _get_win32_devices(self):
        """委托给设备管理器"""
        return self.device_manager.get_win32_devices()

    def _populate_device_list(self, devices):
        """填充设备下拉框

        使用 interface.json 中的配置进行过滤和匹配：
        - Win32: 使用 class_regex 和 window_regex 过滤窗口
        - ADB: 直接显示所有设备

        Args:
            devices: 设备列表（AdbDevice 或 DesktopWindow 对象）
        """
        if not devices:
            log_with_ui(
                self.tr("No devices found"),
                "WARNING",
                output=False,
                infobar=True,
                infobar_type="error"
            )
            return

        import re
        from maa.toolkit import AdbDevice, DesktopWindow

        # 获取当前选中的控制器配置
        current_name = self.controller_type_combo.currentData()
        controller_config = self.controller_configs.get(current_name, {})

        # 用于自动选中第一个匹配项
        first_match_index = -1
        current_index = 0

        for device in devices:
            should_add = True
            is_match = False

            if isinstance(device, AdbDevice):
                # ADB 设备：显示 "name - address"
                display_text = f"{device.name} - {device.address}"
                # 保存完整的设备对象（转换为字典）
                # 注意：adb_path 是 Path 对象，需要转换为字符串
                user_data = {
                    "type": "adb",
                    "name": device.name,
                    "adb_path": str(device.adb_path),  # Path 对象转字符串
                    "address": device.address,
                    "screencap_methods": device.screencap_methods,
                    "input_methods": device.input_methods,
                    "config": device.config,
                }
                # ADB 设备默认都匹配
                is_match = True

            elif isinstance(device, DesktopWindow):
                # Win32 窗口：使用 class_regex 和 window_regex 过滤
                win32_config = controller_config.get("win32", {})
                class_regex = win32_config.get("class_regex", ".*")
                window_regex = win32_config.get("window_regex", ".*")

                # 检查类名和窗口名是否匹配正则表达式
                class_match = re.search(class_regex, device.class_name or "")
                window_match = re.search(window_regex, device.window_name or "")

                # 只有两个都匹配才添加到列表
                if class_match and window_match:
                    is_match = True
                    logger.debug(
                        f"窗口匹配: {device.window_name} ({device.class_name}) "
                        f"- class_regex: {class_regex}, window_regex: {window_regex}"
                    )
                else:
                    should_add = False
                    logger.debug(
                        f"窗口不匹配: {device.window_name} ({device.class_name}) "
                        f"- class_match: {bool(class_match)}, window_match: {bool(window_match)}"
                    )

                display_text = f"{device.window_name}"
                if device.class_name:
                    display_text += f" ({device.class_name})"
                # 保存完整的窗口对象（转换为字典）
                user_data = {
                    "type": "win32",
                    "hwnd": device.hwnd,
                    "class_name": device.class_name,
                    "window_name": device.window_name,
                }

            else:
                # 兼容旧的字符串格式
                display_text = str(device)
                user_data = None

            # 添加到下拉框
            if should_add:
                self.device_combo.addItem(display_text)
                if user_data is not None:
                    self.device_combo.setItemData(current_index, user_data)

                # 记录第一个匹配的索引（用于自动选中）
                if is_match and first_match_index == -1:
                    first_match_index = current_index

                current_index += 1

        # 如果找到匹配项,自动选中第一个
        if first_match_index >= 0:
            self.device_combo.setCurrentIndex(first_match_index)
            logger.info(f"自动选中第一个匹配的设备（索引: {first_match_index}）")

        added_count = self.device_combo.count()
        logger.info(
            f"已添加 {added_count} 个设备到列表（总共检测到 {len(devices)} 个）"
        )
        
        # 显示成功通知
        if added_count > 0:
            log_with_ui(
                self.tr("Found {count} device(s)").format(count=added_count),
                "INFO",
                output=False,
                infobar=True,
                infobar_type="succeed"
            )

    def _show_post_task_setting_option(self, item: TaskItem):
        """显示完成后设置选项 - 使用多选框实现互斥逻辑"""
        self._clear_options()

        # 获取当前保存的选项
        saved_options = item.task_option
        
        # 主布局
        main_layout = QVBoxLayout()
        main_layout.setObjectName("post_task_main_layout")
        
        # 标题
        title_label = BodyLabel(self.tr("Action After Completion"))
        title_label.setStyleSheet("font-weight: bold;")
        main_layout.addWidget(title_label)
        
        # 选项1: 无动作
        self.checkbox_no_action = CheckBox(self.tr("No Action"))
        self.checkbox_no_action.setObjectName("checkbox_no_action")
        main_layout.addWidget(self.checkbox_no_action)
        
        # 选项2: 关闭模拟器
        self.checkbox_close_emulator = CheckBox(self.tr("Close Emulator"))
        self.checkbox_close_emulator.setObjectName("checkbox_close_emulator")
        main_layout.addWidget(self.checkbox_close_emulator)
        
        # 选项3: 关闭软件
        self.checkbox_close_software = CheckBox(self.tr("Close Software"))
        self.checkbox_close_software.setObjectName("checkbox_close_software")
        main_layout.addWidget(self.checkbox_close_software)
        
        # 选项4: 运行其他配置
        self.checkbox_run_other_config = CheckBox(self.tr("Run Other Configuration"))
        self.checkbox_run_other_config.setObjectName("checkbox_run_other_config")
        main_layout.addWidget(self.checkbox_run_other_config)
        
        # 配置选择下拉框 - 缩进显示
        config_container = QWidget()
        config_layout = QVBoxLayout(config_container)
        config_layout.setContentsMargins(30, 0, 0, 0)  # 左侧缩进
        
        self.post_task_config_combo = ComboBox()
        self.post_task_config_combo.setObjectName("post_task_config_combo")
        self.post_task_config_combo.setMaximumWidth(370)
        self._populate_config_list()  # 填充配置列表
        config_layout.addWidget(self.post_task_config_combo)
        
        main_layout.addWidget(config_container)
        
        # 添加到主选项区域
        self.option_area_layout.addLayout(main_layout)
        
        # 从保存的选项中恢复状态
        self._restore_post_task_options(saved_options)
        
        # 连接信号 - 实现互斥逻辑和启用/禁用控制
        self.checkbox_no_action.stateChanged.connect(
            lambda state: self._on_checkbox_changed('no_action', state)
        )
        self.checkbox_close_emulator.stateChanged.connect(
            lambda state: self._on_checkbox_changed('close_emulator', state)
        )
        self.checkbox_close_software.stateChanged.connect(
            lambda state: self._on_checkbox_changed('close_software', state)
        )
        self.checkbox_run_other_config.stateChanged.connect(
            lambda state: self._on_checkbox_changed('run_other_config', state)
        )
        
        # 连接保存信号
        self.post_task_config_combo.currentTextChanged.connect(lambda: self._save_current_options())
        
        # 初始化启用/禁用状态
        self._update_post_action_states()
        
    def _populate_config_list(self):
        """填充配置列表到下拉框"""
        self.post_task_config_combo.clear()
        
        # 从 service_coordinator 获取所有配置
        if self.service_coordinator and hasattr(self.service_coordinator, 'config_service'):
            configs = self.service_coordinator.config_service.list_configs()
            
            for config in configs:
                if isinstance(config, dict):
                    config_name = config.get("name", "")
                    config_id = config.get("item_id", "")
                    if config_name:
                        self.post_task_config_combo.addItem(config_name, config_id)
    
    def _restore_post_task_options(self, saved_options: dict):
        """从保存的选项中恢复完成后设置"""
        # 直接设置状态,不触发信号(因为信号还未连接)
        no_action = saved_options.get("no_action", False)
        close_emulator = saved_options.get("close_emulator", False)
        close_software = saved_options.get("close_software", False)
        run_other_config = saved_options.get("run_other_config", False)
        
        self.checkbox_no_action.setChecked(no_action)
        self.checkbox_close_emulator.setChecked(close_emulator)
        self.checkbox_close_software.setChecked(close_software)
        self.checkbox_run_other_config.setChecked(run_other_config)
        
        # 恢复配置选择
        if run_other_config:
            config_name = saved_options.get("other_config_name", "")
            if config_name:
                index = self.post_task_config_combo.findText(config_name)
                if index >= 0:
                    self.post_task_config_combo.setCurrentIndex(index)
    
    def _on_checkbox_changed(self, checkbox_name: str, state: int):
        """复选框状态改变时的回调 - 根据具体复选框实现互斥逻辑
        
        Args:
            checkbox_name: 改变状态的复选框名称
            state: 新状态 (Qt.CheckState.Checked = 2, Qt.CheckState.Unchecked = 0)
        """
        from PySide6.QtCore import Qt
        
        # 只在选中时处理互斥逻辑
        if state != Qt.CheckState.Checked.value:
            self._update_post_action_states()
            self._save_current_options()
            return
        
        # 暂时断开所有信号,避免递归触发
        self.checkbox_no_action.stateChanged.disconnect()
        self.checkbox_close_emulator.stateChanged.disconnect()
        self.checkbox_close_software.stateChanged.disconnect()
        self.checkbox_run_other_config.stateChanged.disconnect()
        
        # 互斥逻辑:根据被选中的复选框取消冲突项
        if checkbox_name == 'no_action':
            # "无动作" 选中时,取消其他所有选项
            self.checkbox_close_emulator.setChecked(False)
            self.checkbox_close_software.setChecked(False)
            self.checkbox_run_other_config.setChecked(False)
        
        elif checkbox_name == 'run_other_config':
            # "运行其他配置" 选中时,取消其他所有选项
            self.checkbox_no_action.setChecked(False)
            self.checkbox_close_emulator.setChecked(False)
            self.checkbox_close_software.setChecked(False)
        
        elif checkbox_name in ('close_emulator', 'close_software'):
            # "关闭模拟器" 或 "关闭软件" 选中时,取消 "无动作" 和 "运行其他配置"
            self.checkbox_no_action.setChecked(False)
            self.checkbox_run_other_config.setChecked(False)
            # close_emulator 和 close_software 可以共存,不互斥
        
        # 重新连接信号
        self.checkbox_no_action.stateChanged.connect(
            lambda state: self._on_checkbox_changed('no_action', state)
        )
        self.checkbox_close_emulator.stateChanged.connect(
            lambda state: self._on_checkbox_changed('close_emulator', state)
        )
        self.checkbox_close_software.stateChanged.connect(
            lambda state: self._on_checkbox_changed('close_software', state)
        )
        self.checkbox_run_other_config.stateChanged.connect(
            lambda state: self._on_checkbox_changed('run_other_config', state)
        )
        
        # 更新控件状态
        self._update_post_action_states()
        
        # 保存当前选项
        self._save_current_options()
    
    
    def _update_post_action_states(self):
        """更新完成后操作控件的启用/禁用状态"""
        # 配置下拉框只在选择"运行其他配置"时启用
        is_run_other = self.checkbox_run_other_config.isChecked()
        self.post_task_config_combo.setEnabled(is_run_other)

    # ==================== 选项控件创建 - 复杂控件 ==================== #

    def _add_multi_input_option(
        self,
        option_name: str,
        option_config: dict,
        item: TaskItem,
        parent_option_name: str | None = None,
        insert_index: int | None = None,
    ):
        """添加多输入项选项

        用于创建包含多个输入框的选项，如"自定义关卡"

        Args:
            option_name: 选项名称
            option_config: 选项配置，必须包含 inputs 数组
            item: 当前任务项
            parent_option_name: 父级选项名（作为嵌套选项时使用）
            insert_index: 插入位置索引（作为嵌套选项时使用）
        """
        saved_data = item.task_option.get(option_name, {})
        main_description = option_config.get("description", "")
        main_label = option_config.get("label", option_name)
        icon_path = option_config.get("icon", "")

        # 创建主布局
        main_layout = QVBoxLayout()
        if parent_option_name:
            main_layout.setObjectName(
                f"{parent_option_name}__nested__{option_name}_layout"
            )

        # 创建主标题区域
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(5)

        # 添加图标（如果存在）
        icon = self.icon_loader.load_icon(icon_path, size=16)
        if not icon.isNull():
            icon_label = BodyLabel()
            icon_label.setPixmap(icon.pixmap(16, 16))
            title_layout.addWidget(icon_label)

        # 添加主标题（加粗）
        title_label = BodyLabel(main_label)
        title_label.setStyleSheet("font-weight: bold;")
        title_layout.addWidget(title_label)

        main_layout.addLayout(title_layout)

        # 设置主标题的工具提示
        if main_description:
            title_label.setToolTip(main_description)
            title_label.installEventFilter(
                ToolTipFilter(title_label, 0, ToolTipPosition.TOP)
            )

        # 创建各个输入框
        need_save = False
        for input_config in option_config.get("inputs", []):
            input_name = input_config.get("name")
            input_label = input_config.get("label", input_name)
            input_description = input_config.get("description", "")
            default_value = input_config.get("default", "")
            verify_pattern = input_config.get("verify", "")
            pipeline_type = input_config.get("pipeline_type", "string")

            # 获取当前值并进行类型转换
            current_value = saved_data.get(input_name, default_value)

            if pipeline_type == "int" and isinstance(current_value, str):
                try:
                    current_value = int(current_value) if current_value else 0
                    saved_data[input_name] = current_value
                    need_save = True
                except ValueError:
                    logger.warning(f"无法将 '{current_value}' 转换为整数，保持原值")

            # 创建输入项布局
            input_layout = QVBoxLayout()

            # 子标题（不加粗）
            label_layout = QHBoxLayout()
            label_layout.setContentsMargins(0, 0, 0, 0)
            label_layout.setSpacing(5)

            label = BodyLabel(input_label)
            label_layout.addWidget(label)

            input_layout.addLayout(label_layout)

            # 创建输入框
            line_edit = LineEdit()
            line_edit.setText(str(current_value))
            line_edit.setPlaceholderText(f"默认: {default_value}")
            line_edit.setObjectName(f"{option_name}${input_name}")
            line_edit.setProperty("pipeline_type", pipeline_type)

            # 添加输入验证
            if verify_pattern:

                def create_validator(pattern):
                    def validate():
                        text = line_edit.text()
                        if text and not re.match(pattern, text):
                            line_edit.setStyleSheet("border: 1px solid red;")
                        else:
                            line_edit.setStyleSheet("")

                    return validate

                line_edit.textChanged.connect(create_validator(verify_pattern))

            input_layout.addWidget(line_edit)

            # 设置工具提示
            if input_description:
                label.setToolTip(input_description)
                label.installEventFilter(ToolTipFilter(label, 0, ToolTipPosition.TOP))
                line_edit.setToolTip(input_description)
                line_edit.installEventFilter(
                    ToolTipFilter(line_edit, 0, ToolTipPosition.TOP)
                )

            # 连接保存信号
            line_edit.textChanged.connect(lambda: self._save_current_options())

            main_layout.addLayout(input_layout)

        # 如果修正了数据类型，立即保存
        if need_save:
            item.task_option[option_name] = saved_data
            self.service_coordinator.modify_task(item)
            logger.info(f"已修正选项 '{option_name}' 的数据类型")

        # 添加到选项区域（支持指定插入位置）
        if insert_index is not None:
            self.option_area_layout.insertLayout(insert_index, main_layout)
        else:
            self.option_area_layout.addLayout(main_layout)

    # ==================== 选项控件创建 - 基础控件 ==================== #

    def _add_combox_option(
        self,
        name: str,
        obj_name: str,
        options: list[str],
        current: str | None = None,
        icon_path: str = "",
        editable: bool = False,
        tooltip: str = "",
        option_tooltips: dict[str, str] | None = None,
        option_config: dict | None = None,
        skip_initial_nested: bool = False,
        block_signals: bool = False,
        return_widget: bool = False,
    ):
        """添加下拉选项

        Args:
            option_config: 选项配置字典,包含 cases 信息,用于支持嵌套选项
            skip_initial_nested: 是否跳过初始嵌套选项加载（当使用 _add_options_with_order 时为 True）
            block_signals: 是否阻塞信号（初始化加载时为 True，避免 currentTextChanged 触发重复加载）
            return_widget: 是否返回创建的ComboBox控件（用于初始化时创建嵌套选项）
        """
        v_layout = QVBoxLayout()

        # 创建水平布局用于放置图标和标签
        h_layout = QHBoxLayout()
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_layout.setSpacing(5)

        # 创建图标标签（只在有图标时添加）
        icon = self.icon_loader.load_icon(icon_path, size=16)
        if not icon.isNull():
            icon_label = BodyLabel()
            icon_label.setPixmap(icon.pixmap(16, 16))
            h_layout.addWidget(icon_label)

        # 创建文本标签（主标题加粗）
        text_label = BodyLabel(name)
        text_label.setStyleSheet("font-weight: bold;")

        # 添加到水平布局（不添加 stretch，紧贴左边）
        h_layout.addWidget(text_label)

        # 将水平布局添加到垂直布局
        v_layout.addLayout(h_layout)

        if editable:
            combo_box = EditableComboBox()
        else:
            combo_box = ComboBox()

        combo_box.setObjectName(obj_name)
        combo_box.setMaximumWidth(400)  # 限制最大宽度
        v_layout.setObjectName(f"{obj_name}_layout")

        combo_box.addItems(options)

        # 存储选项配置到 combo_box,用于嵌套选项处理
        if option_config:
            combo_box.setProperty("option_config", option_config)
            combo_box.setProperty("parent_option_name", obj_name)

        # 设置标签的工具提示(第一种工具提示:任务介绍)
        if tooltip:
            text_label.setToolTip(tooltip)
            text_label.installEventFilter(
                ToolTipFilter(text_label, 0, ToolTipPosition.TOP)
            )

        # 设置下拉框的初始工具提示和连接信号(第二种工具提示:选项介绍)
        if option_tooltips and isinstance(option_tooltips, dict):
            # 设置初始工具提示
            if current in option_tooltips:
                combo_box.setToolTip(option_tooltips[current])
            combo_box.installEventFilter(
                ToolTipFilter(combo_box, 0, ToolTipPosition.TOP)
            )

            # 连接currentTextChanged信号,当选项改变时更新工具提示
            combo_box.currentTextChanged.connect(
                lambda text: (
                    combo_box.setToolTip(option_tooltips.get(text, ""))
                    if option_tooltips
                    else None
                )
            )
        elif tooltip:  # 如果没有提供选项级工具提示但有整体工具提示
            combo_box.setToolTip(tooltip)
            combo_box.installEventFilter(
                ToolTipFilter(combo_box, 0, ToolTipPosition.TOP)
            )

        # 连接值变化信号,处理嵌套选项和自动保存
        combo_box.currentTextChanged.connect(
            lambda text: self._on_combox_changed(combo_box, text)
        )

        # 如果需要阻塞信号（初始化时），在设置值前阻塞，设置后恢复
        if block_signals:
            combo_box.blockSignals(True)

        if current:
            combo_box.setCurrentText(current)
        else:
            current = combo_box.currentText()

        if block_signals:
            combo_box.blockSignals(False)

        v_layout.addWidget(combo_box)

        # 初始加载时检查是否有嵌套选项（仅在非智能排序模式下）
        # 如果使用 _add_options_with_order，则跳过此步骤避免重复
        if option_config and not skip_initial_nested:
            self._update_nested_options(combo_box, current or combo_box.currentText())

        self.option_area_layout.addLayout(v_layout)

        # 如果需要返回控件，返回创建的ComboBox
        if return_widget:
            return combo_box

    # ==================== 嵌套选项处理 ==================== #

    def _on_combox_changed(self, combo_box: ComboBox | EditableComboBox, text: str):
        """ComboBox值改变时的回调

        处理嵌套选项更新和配置保存
        """
        self._update_nested_options(combo_box, text, recursive=False)
        self._save_current_options()

    def _update_nested_options(
        self,
        combo_box: ComboBox | EditableComboBox,
        selected_case: str,
        recursive: bool = True,
    ):
        """更新嵌套选项

        根据选中的 case 动态显示或隐藏嵌套选项

        Args:
            combo_box: 父级ComboBox控件
            selected_case: 当前选中的case名称
            recursive: 是否递归加载子嵌套选项
                      初始加载时为True，用户交互时为False
        """
        option_config = combo_box.property("option_config")
        parent_option_name = combo_box.property("parent_option_name")

        if not option_config or not parent_option_name:
            return

        # 获取当前嵌套深度（如果是嵌套选项）
        current_depth = combo_box.property("nested_depth")
        if current_depth is None:
            current_depth = 0  # 顶级选项

        # 移除之前的嵌套选项(如果有)
        self._remove_nested_options(parent_option_name)

        # 查找当前选中的case配置
        cases = option_config.get("cases", [])
        selected_case_config = None
        for case in cases:
            if case.get("name") == selected_case:
                selected_case_config = case
                break

        if not selected_case_config:
            return

        # 获取嵌套选项列表
        nested_options = selected_case_config.get("option", [])
        if not nested_options:
            return

        # 获取 interface 配置
        interface = self.service_coordinator.task.interface
        if not interface:
            logger.warning("未找到任务接口配置")
            return

        # 找到父级ComboBox的布局在option_area_layout中的位置
        parent_layout_name = f"{parent_option_name}_layout"
        insert_index = -1
        for i in range(self.option_area_layout.count()):
            item = self.option_area_layout.itemAt(i)
            if (
                item
                and item.layout()
                and item.layout().objectName() == parent_layout_name
            ):
                insert_index = i + 1
                break

        # 如果没找到父级布局,添加到末尾
        if insert_index == -1:
            insert_index = self.option_area_layout.count()

        # 添加嵌套选项
        for nested_option in nested_options:
            nested_option_config = interface["option"].get(nested_option)
            if not nested_option_config:
                continue

            # 标记为嵌套选项
            nested_obj_name = f"{parent_option_name}__nested__{nested_option}"

            # 获取当前任务的保存值
            current_value = None
            if self.current_task:
                current_value = self.current_task.task_option.get(nested_option, None)

            # 根据选项类型添加控件
            option_type = nested_option_config.get("type", "select")

            if "inputs" in nested_option_config and isinstance(
                nested_option_config.get("inputs"), list
            ):
                # 多输入项类型(例如: 自定义关卡)。作为嵌套选项插入到父项之后，并带有可识别的objectName，便于切换时清理。
                if self.current_task:
                    self._add_multi_input_option(
                        nested_option,
                        nested_option_config,
                        self.current_task,
                        parent_option_name=parent_option_name,
                        insert_index=insert_index,
                    )
                    insert_index += 1
            elif option_type == "input":
                # 可编辑下拉框
                name = nested_option_config.get("label", nested_option)
                options = self.Get_Task_List(interface, nested_option)
                icon_path = nested_option_config.get("icon", "")
                tooltip = nested_option_config.get("description", "")
                option_tooltips = {}
                for case in nested_option_config.get("cases", []):
                    option_tooltips[case["name"]] = case.get("description", "")

                # 创建嵌套选项布局（传递深度+1）
                v_layout = self._create_nested_option_layout(
                    name,
                    nested_obj_name,
                    options,
                    current_value,
                    icon_path,
                    True,
                    tooltip,
                    option_tooltips,
                    nested_option_config,
                    depth=current_depth + 1,  # 子嵌套深度+1
                )
                self.option_area_layout.insertLayout(insert_index, v_layout)
                insert_index += 1

                # 仅在递归模式下加载子嵌套（初始加载时）
                # 用户交互时由信号自动触发，不需要在这里重复调用
                if recursive:
                    for i in range(v_layout.count()):
                        item = v_layout.itemAt(i)
                        widget = item.widget() if item else None
                        if widget and isinstance(widget, (ComboBox, EditableComboBox)):
                            # 初始加载子嵌套（递归=True）
                            self._update_nested_options(
                                widget,
                                current_value or widget.currentText(),
                                recursive=True,
                            )
                            break
            else:
                # 普通下拉框
                name = nested_option_config.get("label", nested_option)
                options = self.Get_Task_List(interface, nested_option)
                icon_path = nested_option_config.get("icon", "")
                tooltip = nested_option_config.get("description", "")
                option_tooltips = {}
                for case in nested_option_config.get("cases", []):
                    option_tooltips[case["name"]] = case.get("description", "")

                # 创建嵌套选项布局（传递深度+1）
                v_layout = self._create_nested_option_layout(
                    name,
                    nested_obj_name,
                    options,
                    current_value,
                    icon_path,
                    False,
                    tooltip,
                    option_tooltips,
                    nested_option_config,
                    depth=current_depth + 1,  # 子嵌套深度+1
                )
                self.option_area_layout.insertLayout(insert_index, v_layout)
                insert_index += 1

                # 仅在递归模式下加载子嵌套（初始加载时）
                # 用户交互时由信号自动触发，不需要在这里重复调用
                if recursive:
                    for i in range(v_layout.count()):
                        item = v_layout.itemAt(i)
                        widget = item.widget() if item else None
                        if widget and isinstance(widget, (ComboBox, EditableComboBox)):
                            # 初始加载子嵌套（递归=True）
                            self._update_nested_options(
                                widget,
                                current_value or widget.currentText(),
                                recursive=True,
                            )
                            break

    def _create_nested_option_layout(
        self,
        name: str,
        obj_name: str,
        options: list,
        current: str | None,
        icon_path: str,
        editable: bool,
        tooltip: str,
        option_tooltips: dict,
        option_config: dict,
        depth: int = 1,
    ) -> QVBoxLayout:
        """创建嵌套选项的布局

        Args:
            depth: 嵌套深度（保留参数以保持接口兼容，但不再用于UI显示）

        Returns:
            创建的垂直布局
        """
        v_layout = QVBoxLayout()
        v_layout.setObjectName(f"{obj_name}_layout")

        # 创建水平布局（不再添加缩进，所有选项左对齐）
        h_layout = QHBoxLayout()
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_layout.setSpacing(5)

        # 创建图标标签（只在有图标时添加）
        icon = self.icon_loader.load_icon(icon_path, size=16)
        if not icon.isNull():
            icon_label = BodyLabel()
            icon_label.setPixmap(icon.pixmap(16, 16))
            h_layout.addWidget(icon_label)

        # 创建文本标签（嵌套选项不加粗）
        text_label = BodyLabel(name)

        # 添加到水平布局（不添加 stretch，紧贴左边）
        h_layout.addWidget(text_label)

        v_layout.addLayout(h_layout)

        # 创建ComboBox
        if editable:
            combo_box = EditableComboBox()
        else:
            combo_box = ComboBox()

        combo_box.setObjectName(obj_name)
        combo_box.setMaximumWidth(400)  # 限制最大宽度
        combo_box.addItems(options)

        if current:
            combo_box.setCurrentText(current)

        # 存储配置信息
        combo_box.setProperty("option_config", option_config)
        combo_box.setProperty("parent_option_name", obj_name)
        combo_box.setProperty("is_nested", True)
        combo_box.setProperty("nested_depth", depth)  # 存储嵌套深度

        v_layout.addWidget(combo_box)

        # 设置工具提示
        if tooltip:
            text_label.setToolTip(tooltip)
            text_label.installEventFilter(
                ToolTipFilter(text_label, 0, ToolTipPosition.TOP)
            )

        if option_tooltips:
            if current and current in option_tooltips:
                combo_box.setToolTip(option_tooltips[current])
            combo_box.installEventFilter(
                ToolTipFilter(combo_box, 0, ToolTipPosition.TOP)
            )
            combo_box.currentTextChanged.connect(
                lambda text: combo_box.setToolTip(option_tooltips.get(text, ""))
            )
        elif tooltip:
            combo_box.setToolTip(tooltip)
            combo_box.installEventFilter(
                ToolTipFilter(combo_box, 0, ToolTipPosition.TOP)
            )

        # 连接信号（支持递归嵌套）
        combo_box.currentTextChanged.connect(
            lambda text: self._on_combox_changed(combo_box, text)
        )

        # 注意：不在这里自动加载子嵌套选项
        # 子嵌套的加载由以下两种情况触发：
        # 1. _update_nested_options 会在创建完所有同级嵌套后，由用户交互触发子嵌套加载
        # 2. _add_options_with_order 的递归逻辑会主动调用来加载初始子嵌套
        # 如果在这里自动加载，会导致重复添加

        return v_layout

    # ==================== 布局清理方法 ==================== #

    def _remove_nested_options(self, parent_option_name: str):
        """递归移除指定父级选项的所有嵌套选项（包括多层嵌套）

        Args:
            parent_option_name: 父级选项的objectName
        """
        # 收集需要移除的布局索引(从后往前,避免索引变化)
        to_remove = []
        nested_items_to_check = []  # 需要递归检查的嵌套项

        for i in range(self.option_area_layout.count()):
            item = self.option_area_layout.itemAt(i)
            if item and item.layout():
                layout_name = item.layout().objectName()
                # 检查是否是该父级的直接嵌套选项
                if layout_name.startswith(f"{parent_option_name}__nested__"):
                    to_remove.append(i)
                    # 提取嵌套选项的名称，用于递归查找它的子嵌套
                    # 格式: parent__nested__option_layout -> parent__nested__option
                    if layout_name.endswith("_layout"):
                        nested_name = layout_name[:-7]  # 移除 "_layout"
                        nested_items_to_check.append(nested_name)

        # 递归移除子嵌套选项
        for nested_name in nested_items_to_check:
            self._remove_nested_options(nested_name)

        # 从后往前移除当前层级的嵌套选项
        for i in reversed(to_remove):
            item = self.option_area_layout.takeAt(i)
            if item and item.layout():
                # 递归删除布局中的所有控件
                self._clear_layout(item.layout())
                item.layout().deleteLater()

    def _clear_layout(self, layout):
        """递归清空布局中的所有控件"""
        if layout is None:
            return
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())

    # ==================== 选项控件创建 - 文本输入控件 ==================== #

    def _add_lineedit_option(
        self, name: str, current: str, tooltip: str = "", obj_name: str = ""
    ):
        """添加文本输入选项"""
        v_layout = QVBoxLayout()
        label = BodyLabel(name)
        line_edit = LineEdit()
        line_edit.setText(current)
        if obj_name:
            line_edit.setObjectName(obj_name)
            v_layout.setObjectName(f"{obj_name}_layout")
        v_layout.addWidget(label)
        v_layout.addWidget(line_edit)
        if tooltip:
            label.setToolTip(tooltip)
            label.installEventFilter(ToolTipFilter(label, 0, ToolTipPosition.TOP))
            line_edit.setToolTip(tooltip)
            line_edit.installEventFilter(
                ToolTipFilter(line_edit, 0, ToolTipPosition.TOP)
            )

        # 连接值变化信号，自动保存选项
        line_edit.textChanged.connect(lambda: self._save_current_options())

        self.option_area_layout.addLayout(v_layout)

    # ==================== 选项控件创建 - 开关控件 ==================== #

    def _add_switch_option(
        self, name: str, current: bool, tooltip: str = "", obj_name: str = ""
    ):
        """添加开关选项"""
        v_layout = QVBoxLayout()
        label = BodyLabel(name)
        switch = SwitchButton()
        switch.setChecked(current)
        if obj_name:
            switch.setObjectName(obj_name)
            v_layout.setObjectName(f"{obj_name}_layout")
        v_layout.addWidget(label)
        v_layout.addWidget(switch)
        if tooltip:
            label.setToolTip(tooltip)
            label.installEventFilter(ToolTipFilter(label, 0, ToolTipPosition.TOP))
            switch.setToolTip(tooltip)
            switch.installEventFilter(ToolTipFilter(switch, 0, ToolTipPosition.TOP))

        # 连接值变化信号，自动保存选项
        switch.checkedChanged.connect(lambda: self._save_current_options())

        self.option_area_layout.addLayout(v_layout)

    def _clear_options(self):
        """同步清除所有选项 (不做动画)。"""
        def recursive_clear_layout(layout):
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget:
                    widget.hide()
                    widget.deleteLater()
                elif item.layout():
                    nested_layout = item.layout()
                    recursive_clear_layout(nested_layout)
                    if nested_layout.parent() is None:
                        del nested_layout
                elif item.spacerItem():
                    layout.removeItem(item)
        recursive_clear_layout(self.option_area_layout)

    def _play_option_transition(self, build_callable):
        """使用过渡动画执行 清空 + 构建。

        Args:
            build_callable: 构建新选项内容的函数。
        """
        if not callable(build_callable):
            return

        def update():
            self._clear_options()
            build_callable()

        self._option_animator.play(update)
