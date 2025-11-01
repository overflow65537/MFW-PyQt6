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
    ListWidget,
    ToolButton,
    ScrollArea,
    ComboBox,
    EditableComboBox,
    LineEdit,
    SwitchButton,
    PushButton,
    PrimaryPushButton,
    FluentIcon as FIF,
)

from app.utils.logger import logger
from app.utils.gui_helper import IconLoader
from app.utils.i18n_manager import get_interface_i18n


from .ListWidget import TaskDragListWidget, ConfigListWidget
from .AddTaskMessageBox import AddConfigDialog, AddTaskDialog
from ..core.core import TaskItem, ConfigItem, ServiceCoordinator
from .ListItem import TaskListItem, ConfigListItem

# 导入任务选项模块的 Mixin
from .task_management.task_options.utils.config_helper import ConfigHelperMixin
from .task_management.task_options.utils.device_helper import DeviceHelperMixin
from .task_management.task_options.utils.layout_helper import LayoutHelperMixin
from .task_management.task_options.controller.adb import AdbControllerMixin
from .task_management.task_options.controller.win32 import Win32ControllerMixin
from .task_management.task_options.controller.common import ControllerCommonMixin
from .task_management.task_options.resource_setting import ResourceSettingMixin
from .task_management.task_options.task_options import TaskOptionsMixin
from .task_management.task_options.widget_creators import WidgetCreatorsMixin
from .task_management.task_options.nested_options import NestedOptionsMixin
from .task_management.task_options.resource_option import ResourceOptionMixin
from .task_management.task_options.post_task_option import PostTaskOptionMixin
from .task_management.task_options.multi_input_option import MultiInputOptionMixin
from .task_management.task_options.base import OptionWidgetBaseMixin


class BaseListToolBarWidget(QWidget):

    def __init__(self, service_coordinator: ServiceCoordinator, parent=None):
        super().__init__(parent)
        self.service_coordinator = service_coordinator

        # 创建图标加载器（仅 GUI 使用）
        self.icon_loader = IconLoader(service_coordinator)

        self._init_title()
        self._init_selection()

        self.title_layout.setContentsMargins(0, 0, 2, 0)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.addLayout(self.title_layout)
        self.main_layout.addWidget(self.selection_widget)

    def _init_title(self):
        """初始化标题栏"""
        # 标题
        self.selection_title = BodyLabel()
        self.selection_title.setStyleSheet("font-size: 20px;")
        self.selection_title.setAlignment(Qt.AlignmentFlag.AlignLeft)

        # 选择全部按钮
        self.select_all_button = ToolButton(FIF.CHECKBOX)
        self.select_all_button.installEventFilter(
            ToolTipFilter(self.select_all_button, 0, ToolTipPosition.TOP)
        )
        self.select_all_button.setToolTip(self.tr("Select All"))

        # 取消选择全部
        self.deselect_all_button = ToolButton(FIF.CLEAR_SELECTION)
        self.deselect_all_button.installEventFilter(
            ToolTipFilter(self.deselect_all_button, 0, ToolTipPosition.TOP)
        )
        self.deselect_all_button.setToolTip(self.tr("Deselect All"))

        # 添加
        self.add_button = ToolButton(FIF.ADD)
        self.add_button.installEventFilter(
            ToolTipFilter(self.add_button, 0, ToolTipPosition.TOP)
        )
        self.add_button.setToolTip(self.tr("Add"))

        # 删除
        self.delete_button = ToolButton(FIF.DELETE)
        self.delete_button.installEventFilter(
            ToolTipFilter(self.delete_button, 0, ToolTipPosition.TOP)
        )
        self.delete_button.setToolTip(self.tr("Delete"))

        # 布局
        self.title_layout = QHBoxLayout()
        # 设置边距
        self.title_layout.addWidget(self.selection_title)
        self.title_layout.addWidget(self.select_all_button)
        self.title_layout.addWidget(self.deselect_all_button)
        self.title_layout.addWidget(self.delete_button)
        self.title_layout.addWidget(self.add_button)

    def _init_task_list(self):
        """初始化任务列表"""
        self.task_list = ListWidget(parent=self)

    def _init_selection(self):
        """初始化配置选择"""
        self._init_task_list()

        # 配置选择列表布局
        self.selection_widget = SimpleCardWidget()
        self.selection_widget.setClickEnabled(False)
        self.selection_widget.setBorderRadius(8)
        self.selection_layout = QVBoxLayout(self.selection_widget)
        self.selection_layout.addWidget(self.task_list)

    def set_title(self, title: str):
        """设置标题"""
        self.selection_title.setText(title)


class ConfigListToolBarWidget(BaseListToolBarWidget):
    def __init__(self, service_coordinator: ServiceCoordinator, parent=None):
        super().__init__(service_coordinator=service_coordinator, parent=parent)

        self.service_coordinator = service_coordinator

        self.select_all_button.hide()
        self.deselect_all_button.hide()

        self.add_button.clicked.connect(self.add_config)
        self.delete_button.clicked.connect(self.remove_config)

        # 设置配置列表标题
        self.set_title(self.tr("Configurations"))

    def _init_task_list(self):
        """初始化配置列表"""
        self.task_list = ConfigListWidget(
            service_coordinator=self.service_coordinator, parent=self
        )

    def add_config(self):
        """添加配置项。"""
        # 通过对话框创建新配置
        bundles = []
        main_cfg = getattr(self.service_coordinator.config, "_main_config", None)
        if main_cfg:
            bundles = main_cfg.get("bundle", [])

        dlg = AddConfigDialog(resource_bundles=bundles, parent=self.window())
        if dlg.exec():
            cfg = dlg.get_config_item()
            if cfg:
                self.service_coordinator.add_config(cfg)

    def remove_config(self):
        """移除配置项"""
        cur = self.task_list.currentItem()
        if not cur:
            return
        widget = self.task_list.itemWidget(cur)
        if not widget:
            return
        if isinstance(widget, ConfigListItem):
            cfg_id = widget.item.item_id
        else:
            cfg_id = None
        if not cfg_id:
            return
        # 调用服务删除即可,视图通过信号刷新
        self.service_coordinator.delete_config(cfg_id)


class TaskListToolBarWidget(BaseListToolBarWidget):

    def __init__(self, service_coordinator: ServiceCoordinator, parent=None):
        super().__init__(service_coordinator=service_coordinator, parent=parent)
        self.core_signalBus = self.service_coordinator.signal_bus
        # 选择全部按钮
        self.select_all_button.clicked.connect(self.select_all)
        # 取消选择全部按钮
        self.deselect_all_button.clicked.connect(self.deselect_all)
        # 添加按钮
        self.add_button.clicked.connect(self.add_task)
        # 删除按钮
        self.delete_button.clicked.connect(self.remove_selected_task)

        # 设置任务列表标题
        self.set_title(self.tr("Tasks"))

        # 初始填充任务列表
        # 不在工具栏直接刷新列表：视图会订阅 ServiceCoordinator 的信号自行更新

    def _init_task_list(self):
        """初始化任务列表"""
        self.task_list = TaskDragListWidget(
            service_coordinator=self.service_coordinator, parent=self
        )

    def select_all(self):
        """选择全部"""
        self.task_list.select_all()

    def deselect_all(self):
        """取消选择全部"""
        self.task_list.deselect_all()

    def add_task(self):
        """添加任务"""
        # 打开添加任务对话框
        task_map = getattr(self.service_coordinator.task, "default_option", {})
        interface = getattr(self.service_coordinator.task, "interface", {})
        dlg = AddTaskDialog(
            task_map=task_map, interface=interface, parent=self.window()
        )
        if dlg.exec():
            new_task = dlg.get_task_item()
            if new_task:
                # 持久化到服务层
                self.service_coordinator.modify_task(new_task)

    def remove_selected_task(self):
        cur = self.task_list.currentItem()
        if not cur:
            return
        widget = self.task_list.itemWidget(cur)
        if not widget or not isinstance(widget, TaskListItem):
            return
        task_id = getattr(widget.task, "item_id", None)
        if not task_id:
            return
        # 删除通过服务层执行，视图会通过fs系列信号刷新
        self.service_coordinator.delete_task(task_id)


class OptionWidget(
    QWidget,
    ConfigHelperMixin,
    DeviceHelperMixin,
    LayoutHelperMixin,
    AdbControllerMixin,
    Win32ControllerMixin,
    ControllerCommonMixin,
    ResourceSettingMixin,
    TaskOptionsMixin,
    WidgetCreatorsMixin,
    NestedOptionsMixin,
    ResourceOptionMixin,
    PostTaskOptionMixin,
    MultiInputOptionMixin,
    OptionWidgetBaseMixin,
):
    """选项面板控件

    负责显示任务的配置选项，支持：
    - 普通任务选项（通过 interface.json 配置）
    - 基础任务选项（控制器、资源、完成后设置）
    - 嵌套选项、多输入项等复杂配置

    通过多重继承组合各个功能模块：
    - ConfigHelperMixin: 配置保存和处理
    - DeviceHelperMixin: 设备获取和填充
    - LayoutHelperMixin: 布局清理工具
    - AdbControllerMixin: ADB 控制器选项
    - Win32ControllerMixin: Win32 控制器选项
    - ControllerCommonMixin: 控制器通用选项
    - ResourceSettingMixin: 资源设置页面
    - TaskOptionsMixin: 任务选项显示
    - WidgetCreatorsMixin: 控件创建器
    - NestedOptionsMixin: 嵌套选项处理
    - ResourceOptionMixin: 资源槽位选项
    - PostTaskOptionMixin: 完成后设置选项
    - MultiInputOptionMixin: 多输入项选项
    - OptionWidgetBaseMixin: UI初始化和主入口
    """

    # ==================== 初始化 ==================== #

    def __init__(self, service_coordinator: ServiceCoordinator, parent=None):
        super().__init__(parent)
        self.service_coordinator: ServiceCoordinator = service_coordinator
        self.task = self.service_coordinator.task
        self.config = self.service_coordinator.config
        self.core_signalBus = self.service_coordinator.signal_bus

        # 创建图标加载器（仅 GUI 使用）
        self.icon_loader = IconLoader(service_coordinator)

        # 使用 task_selected 信号（由 ServiceCoordinator 触发）
        self.core_signalBus.task_selected.connect(self.show_option)
        # 监听配置切换以重置选项面板
        self.core_signalBus.config_changed.connect(self._on_config_changed)
        self._init_ui()

        # 设置选项面板标题
        self.set_title(self.tr("Options"))

        # 当前正在编辑的任务
        self.current_task: TaskItem | None = None

    # ==================== UI 初始化 (已迁移至 base.py) ==================== #
    # _init_ui() 方法已迁移至 OptionWidgetBaseMixin

    # ==================== UI 辅助方法 (已迁移至 base.py) ==================== #
    # _toggle_description() 方法已迁移至 OptionWidgetBaseMixin
    # set_description() 方法已迁移至 OptionWidgetBaseMixin

    # ==================== 公共方法 (已迁移至 base.py) ==================== #
    # reset() 方法已迁移至 OptionWidgetBaseMixin
    # _on_config_changed() 方法已迁移至 OptionWidgetBaseMixin
    # set_title() 方法已迁移至 OptionWidgetBaseMixin

    # ==================== 选项数据管理 ==================== #

    def _save_current_options(self):
        """收集当前所有选项控件的值并保存到配置"""
        if not self.current_task:
            return

        # 递归查找所有控件的辅助函数
        def find_widgets_recursive(layout, widgets_list):
            """递归查找布局中的所有控件"""
            for i in range(layout.count()):
                item = layout.itemAt(i)
                if not item:
                    continue

                widget = item.widget()
                if widget:
                    widgets_list.append(widget)
                elif item.layout():
                    # 递归查找子布局
                    find_widgets_recursive(item.layout(), widgets_list)

        # 收集所有控件
        all_widgets = []
        find_widgets_recursive(self.option_area_layout, all_widgets)

        # 遍历所有控件，收集有 objectName 的选项控件
        updated_options = {}
        for widget in all_widgets:
            # 获取控件的 objectName
            obj_name = widget.objectName()
            if not obj_name:
                continue

            # 检查是否是多输入项格式(option$input_name)
            if "$" in obj_name:
                option_name, input_name = obj_name.split("$", 1)

                # 确保 option 存在
                if option_name not in updated_options:
                    updated_options[option_name] = {}

                # 获取值
                if isinstance(widget, LineEdit):
                    value = widget.text()

                    # 获取 pipeline_type 属性,根据类型转换值
                    pipeline_type = widget.property("pipeline_type")
                    if pipeline_type == "int":
                        # 尝试转换为整数,失败则保持字符串
                        try:
                            value = int(value) if value else 0
                        except ValueError:
                            logger.warning(
                                f"无法将 '{value}' 转换为整数,保持字符串格式"
                            )

                    updated_options[option_name][input_name] = value
            # 检查是否是嵌套选项格式(parent__nested__option_name)
            elif "__nested__" in obj_name:
                # 嵌套选项:作战关卡A__nested__是否进行信源回收
                # 提取真正的选项名(最后一部分)
                real_option_name = obj_name.split("__nested__")[-1]

                # 根据控件类型获取值
                if isinstance(widget, (ComboBox, EditableComboBox)):
                    value = widget.currentText()
                    updated_options[real_option_name] = value
                elif isinstance(widget, LineEdit):
                    updated_options[real_option_name] = widget.text()
            else:
                # 单个选项:普通格式
                # 根据控件类型获取值
                if isinstance(widget, (ComboBox, EditableComboBox)):
                    # 对于设备选择下拉框，不保存（它只用于触发自动填充）
                    if obj_name == "device":
                        # 设备选择框的值会通过自动填充逻辑保存到对应的字段
                        # (ADB: adb_path, adb_port, adb_device_name; Win32: hwnd, win32_device_name)
                        continue
                    # 对于资源选择和控制器类型下拉框，使用 userData
                    elif obj_name in ("controller_type", "resource"):
                        value = widget.currentData()
                        # 如果没有 userData（旧数据或手动输入），使用文本
                        if value is None:
                            value = widget.currentText()
                    # 对于输入/截图方法下拉框，使用 userData 并保存为整数
                    elif obj_name in (
                        "adb_screenshot_method",
                        "adb_input_method",
                        "win32_screenshot_method",
                        "win32_input_method",
                    ):
                        # 检查是否有存储的原始值（用于不在映射表中的值）
                        original_value = widget.property("original_value")
                        if original_value is not None:
                            # 如果用户改变了选择，清除原始值，使用新选择的值
                            # 否则保持原始值
                            if widget.property("user_changed"):
                                value = widget.currentData()
                            else:
                                value = original_value
                        else:
                            value = widget.currentData()

                        # 如果有 userData，转换为整数
                        if value is not None:
                            try:
                                value = int(value)
                            except (ValueError, TypeError):
                                # 转换失败，使用文本
                                value = widget.currentText()
                        else:
                            # 没有 userData，使用文本
                            value = widget.currentText()
                    else:
                        value = widget.currentText()

                    updated_options[obj_name] = value
                elif isinstance(widget, LineEdit):
                    updated_options[obj_name] = widget.text()
                elif isinstance(widget, SwitchButton):
                    updated_options[obj_name] = widget.isChecked()

        # 更新任务的 task_option
        if updated_options:
            # 对于资源设置任务，需要重新组织 ADB 和 Win32 的选项
            if self.current_task.item_id.startswith("r_"):
                organized_options = self._organize_controller_options(updated_options)
                # 深度合并 adb 和 win32 组，避免覆盖未修改的字段
                for key, value in organized_options.items():
                    if key in ("adb", "win32") and isinstance(value, dict):
                        # 如果是 adb 或 win32 组，需要深度合并
                        if key not in self.current_task.task_option:
                            self.current_task.task_option[key] = {}
                        self.current_task.task_option[key].update(value)
                    else:
                        # 其他字段直接更新
                        self.current_task.task_option[key] = value
            else:
                self.current_task.task_option.update(updated_options)
            # 通过服务层保存
            self.service_coordinator.modify_task(self.current_task)

    def _organize_controller_options(self, options: dict) -> dict:
        """将控制器选项组织为 MAA 标准格式

        将扁平的选项字典组织为:
        {
            "adb": {
                "adb_path": "...",
                "address": "...",
                "input_method": 0,
                "screen_method": 0,
                "config": {...}
            },
            "win32": {
                "hwnd": 0,
                "input_method": 0,
                "screen_method": 0
            },
            "controller": {...},
            "resource": "...",
            ...
        }
        """
        # ADB 相关字段映射（包括模拟器相关字段）
        adb_fields = {
            "adb_path": "adb_path",
            "adb_port": "address",  # adb_port 实际存储的是完整地址
            "adb_screenshot_method": "screen_method",
            "adb_input_method": "input_method",
            "adb_config": "config",
            # 模拟器相关字段
            "emulator_address": "emulator_address",
            "emulator_launch_args": "emulator_launch_args",
            "emulator_launch_timeout": "emulator_launch_timeout",
            # 设备名称（用于显示）
            "adb_device_name": "device_name",
        }

        # Win32 相关字段映射（包括应用相关字段）
        win32_fields = {
            "hwnd": "hwnd",
            "win32_screenshot_method": "screen_method",
            "win32_input_method": "input_method",
            # 应用相关字段
            "app_path": "app_path",
            "app_launch_args": "app_launch_args",
            "app_launch_timeout": "app_launch_timeout",
            # 设备相关字段
            "win32_device_name": "device_name",
        }

        # 通用字段（不属于 adb 或 win32）
        common_fields = [
            "controller_type",
            "resource",
        ]

        result = {}
        adb_group = {}
        win32_group = {}

        for key, option_data in options.items():
            # 兼容新旧格式：如果是字典且有 value 字段，提取 value；否则直接使用
            if isinstance(option_data, dict) and "value" in option_data:
                value = option_data["value"]
            else:
                value = option_data

            # 检查是否是 ADB 字段
            if key in adb_fields:
                target_key = adb_fields[key]
                # 特殊处理 config 字段（JSON 字符串转对象）
                if target_key == "config" and isinstance(value, str):
                    try:
                        import json

                        adb_group[target_key] = json.loads(value) if value else {}
                    except:
                        adb_group[target_key] = {}
                else:
                    adb_group[target_key] = value
            # 检查是否是 Win32 字段
            elif key in win32_fields:
                target_key = win32_fields[key]
                win32_group[target_key] = value
            # 通用字段保持原样（直接保存值，不包装）
            elif key in common_fields:
                result[key] = value

        # 将分组后的选项添加到结果中（不包装 value/type）
        if adb_group:
            result["adb"] = adb_group
        if win32_group:
            result["win32"] = win32_group

        return result

    def _get_option_value(self, options: dict, key: str, default=None):
        """获取选项值的辅助方法

        兼容两种格式:
        1. 新格式: {"key": value}
        2. 旧格式: {"key": {"value": value, "type": "..."}}
        """
        value = options.get(key, default)
        # 如果是字典且包含 value 字段，提取 value（向后兼容）
        if isinstance(value, dict) and "value" in value:
            return value["value"]
        return value if value is not None else default

    def _flatten_controller_options(self, options: dict) -> dict:
        """将嵌套的控制器选项展平为扁平格式

        将 MAA 标准格式:
        {
            "adb": {
                "adb_path": "...",
                "address": "...",
                "input_method": 0,
                "screen_method": 0,
                "config": {...}
            },
            "win32": {
                "hwnd": 0,
                "input_method": 0,
                "screen_method": 0
            },
            ...
        }

        展平为内部使用的格式:
        {
            "adb_path": "...",
            "adb_port": "...",
            "adb_input_method": 0,
            "adb_screenshot_method": 0,
            "adb_config": "{...}",
            ...
        }
        """
        result = {}

        # 处理 ADB 配置
        if "adb" in options:
            adb_data = options["adb"]
            if isinstance(adb_data, dict):
                # 映射 ADB 基本字段
                if "adb_path" in adb_data:
                    result["adb_path"] = adb_data["adb_path"]
                if "address" in adb_data:
                    result["adb_port"] = adb_data["address"]
                if "input_method" in adb_data:
                    result["adb_input_method"] = adb_data["input_method"]
                if "screen_method" in adb_data:
                    result["adb_screenshot_method"] = adb_data["screen_method"]
                if "config" in adb_data:
                    # 将 config 对象转为 JSON 字符串
                    import json

                    config_str = (
                        json.dumps(adb_data["config"]) if adb_data["config"] else ""
                    )
                    result["adb_config"] = config_str
                # 映射模拟器相关字段
                if "emulator_address" in adb_data:
                    result["emulator_address"] = adb_data["emulator_address"]
                if "emulator_launch_args" in adb_data:
                    result["emulator_launch_args"] = adb_data["emulator_launch_args"]
                if "emulator_launch_timeout" in adb_data:
                    result["emulator_launch_timeout"] = adb_data[
                        "emulator_launch_timeout"
                    ]
                # 映射设备名称字段
                if "device_name" in adb_data:
                    result["adb_device_name"] = adb_data["device_name"]

        # 处理 Win32 配置
        if "win32" in options:
            win32_data = options["win32"]
            if isinstance(win32_data, dict):
                # 映射 Win32 基本字段
                if "hwnd" in win32_data:
                    result["hwnd"] = win32_data["hwnd"]
                if "input_method" in win32_data:
                    result["win32_input_method"] = win32_data["input_method"]
                if "screen_method" in win32_data:
                    result["win32_screenshot_method"] = win32_data["screen_method"]
                # 映射应用相关字段
                if "app_path" in win32_data:
                    result["app_path"] = win32_data["app_path"]
                if "app_launch_args" in win32_data:
                    result["app_launch_args"] = win32_data["app_launch_args"]
                if "app_launch_timeout" in win32_data:
                    result["app_launch_timeout"] = win32_data["app_launch_timeout"]
                # 映射设备相关字段
                if "device_name" in win32_data:
                    result["win32_device_name"] = win32_data["device_name"]

        # 复制其他通用字段
        for key, value in options.items():
            if key not in ("adb", "win32"):
                result[key] = value

        return result

        # ==================== 任务选项显示 - 主入口 (已迁移至 base.py 和 task_options.py) ==================== #
        # show_option() 方法已迁移至 OptionWidgetBaseMixin
        # _show_task_option() 方法已迁移至 TaskOptionsMixin
        # _add_options_with_order() 方法已迁移至 TaskOptionsMixin

        # ==================== 任务选项工具方法 (已迁移至 task_options.py) ==================== #
        # Get_Task_List() 方法已迁移至 TaskOptionsMixin

        # ==================== 基础任务选项显示 (已迁移) ==================== #
        # _show_resource_option() 方法已迁移至 ResourceOptionMixin
        # _show_resource_setting_option() 方法已迁移至 ResourceSettingMixin

        # ==================== 资源设置回调方法 (已迁移至 resource_setting.py) ==================== #

        if not interface:
            interface_path = Path.cwd() / "interface.json"
            if not interface_path.exists():
                logger.warning("未找到 interface.json 文件")
                return
            with open(interface_path, "r", encoding="utf-8") as f:
                interface = json.load(f)

        # 获取资源列表
        resources = interface.get("resource", [])
        resource_options = [r.get("name", "") for r in resources if r.get("name")]

        # 如果没有资源配置，显示提示
        if not resource_options:
            label = BodyLabel(self.tr("No resource configuration found"))
            self.option_area_layout.addWidget(label)
            return

        # 获取当前保存的资源选项
        saved_options = item.task_option

        # 创建6个资源下拉框
        resource_fields = [
            ("resource_1", self.tr("Resource Slot 1")),
            ("resource_2", self.tr("Resource Slot 2")),
            ("resource_3", self.tr("Resource Slot 3")),
            ("resource_4", self.tr("Resource Slot 4")),
            ("resource_5", self.tr("Resource Slot 5")),
            ("resource_6", self.tr("Resource Slot 6")),
        ]

        for field_name, field_label in resource_fields:
            current_value = saved_options.get(field_name, "")

            # 创建垂直布局
            v_layout = QVBoxLayout()
            v_layout.setObjectName(f"{field_name}_layout")

            # 标签
            label = BodyLabel(field_label)
            label.setStyleSheet("font-weight: bold;")
            v_layout.addWidget(label)

            # 下拉框
            combo = ComboBox()
            combo.setObjectName(field_name)
            combo.addItems([""] + resource_options)  # 添加空选项
            if current_value:
                combo.setCurrentText(current_value)

            # 连接信号
            combo.currentTextChanged.connect(lambda: self._save_current_options())

            v_layout.addWidget(combo)
            self.option_area_layout.addLayout(v_layout)

    def _show_resource_setting_option(self, item: TaskItem):
        """显示资源设置选项页面（合并控制器和资源配置）

        包含：
        - 控制器类型选择下拉框
        - 刷新设备按钮
        - 资源选择下拉框（根据控制器类型过滤）
        - 设备选择下拉框
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
        current_controller_name = str(
            self._get_option_value(saved_options, "controller_type", "")
        )

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

        # 设备刷新按钮
        button_v_layout = QVBoxLayout()
        button_v_layout.addSpacing(24)  # 对齐下拉框

        self.refresh_devices_button = PrimaryPushButton(self.tr("Refresh Devices"))
        self.refresh_devices_button.setObjectName("refresh_devices_button")
        self.refresh_devices_button.clicked.connect(self._on_refresh_devices_clicked)
        button_v_layout.addWidget(self.refresh_devices_button)

        controller_h_layout.addLayout(button_v_layout, stretch=1)
        self.option_area_layout.addLayout(controller_h_layout)

        # 2. 资源选择下拉框（根据控制器类型过滤）
        self.resource_combo_layout = QVBoxLayout()
        self.resource_combo_layout.setObjectName("resource_combo_layout")
        self.option_area_layout.addLayout(self.resource_combo_layout)

        # 3. 设备选择下拉框
        device_v_layout = QVBoxLayout()
        device_v_layout.setObjectName("device_layout")

        device_label = BodyLabel(self.tr("Select Device"))
        device_label.setStyleSheet("font-weight: bold;")
        device_v_layout.addWidget(device_label)

        self.device_combo = ComboBox()
        self.device_combo.setObjectName("device")
        self.device_combo.setMaximumWidth(400)  # 限制最大宽度

        # 从保存的配置中构建设备信息并填充到下拉框（在连接信号之前）
        self._populate_saved_device(saved_options, current_controller_name)

        # 连接设备选择改变信号 - 自动填充字段和保存
        # 注意：必须在 _populate_saved_device 之后连接，避免初始化时触发不必要的回调
        self.device_combo.currentIndexChanged.connect(
            lambda: self._on_device_selected_in_resource_setting(item)
        )

        device_v_layout.addWidget(self.device_combo)
        self.option_area_layout.addLayout(device_v_layout)

        # 4. 创建容器用于存放动态选项（ADB 或 Win32 特定选项）
        self.controller_specific_options_layout = QVBoxLayout()
        self.controller_specific_options_layout.setObjectName(
            "controller_specific_options"
        )
        self.option_area_layout.addLayout(self.controller_specific_options_layout)

        # 5. 通用选项容器
        self.controller_common_options_layout = QVBoxLayout()
        self.controller_common_options_layout.setObjectName("controller_common_options")
        self.option_area_layout.addLayout(self.controller_common_options_layout)

        # 连接控制器类型变化信号
        self.controller_type_combo.currentIndexChanged.connect(
            lambda: self._on_resource_setting_controller_changed(
                item, clear_device=True
            )
        )

        # 初始化显示对应的选项（这会创建 ADB/Win32 输入框）
        # 初始化时不清空设备下拉框，因为已经从配置中加载了
        self._on_resource_setting_controller_changed(item, clear_device=False)

        # 如果有保存的设备信息，手动触发一次自动填充
        # 此时输入框已经创建，可以正确填充
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

        # 如果设备下拉框有内容，触发自动填充
        # 这样切换控制器类型时，如果有已选设备，会自动填充字段
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

            adb_path_widget = self.findChild(LineEdit, "adb_path")
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
        current_value = self._get_option_value(saved_options, "resource", "")

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
        combo.setMaximumWidth(400)  # 限制最大宽度

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
        current_controller_name = self._get_option_value(
            saved_options, "controller_type", ""
        )

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

        current_device = self._get_option_value(saved_options, "device", "")
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
        # 文本输入框选项
        text_options = [
            ("adb_path", self.tr("ADB Path"), None, self.tr("Path to adb executable")),
            (
                "adb_port",
                self.tr("ADB Connection Address"),
                None,
                self.tr("Device connection address (IP:Port or device ID)"),
            ),
            (
                "emulator_address",
                self.tr("Emulator Launch Path"),
                None,
                self.tr("Path to emulator executable for launching"),
            ),
            (
                "emulator_launch_args",
                self.tr("Emulator Launch Args"),
                "",
                self.tr("Arguments for launching emulator"),
            ),
            (
                "emulator_launch_timeout",
                self.tr("Emulator Launch Timeout (ms)"),
                "60000",
                self.tr("Time to wait for emulator startup"),
            ),
        ]

        for obj_name, label_text, default_value, tooltip_text in text_options:
            v_layout = QVBoxLayout()
            v_layout.setObjectName(f"{obj_name}_layout")

            label = BodyLabel(label_text)
            line_edit = LineEdit()
            line_edit.setObjectName(obj_name)
            # 如果 default_value 是 None，则使用空字符串
            actual_default = "" if default_value is None else default_value

            # 阻止信号，避免在初始化时触发保存
            line_edit.blockSignals(True)
            line_edit.setText(
                str(self._get_option_value(saved_options, obj_name, actual_default))
            )
            line_edit.blockSignals(False)

            line_edit.setToolTip(tooltip_text)
            label.setToolTip(tooltip_text)

            # 连接信号
            line_edit.textChanged.connect(lambda: self._save_current_options())

            v_layout.addWidget(label)
            v_layout.addWidget(line_edit)

            self.controller_specific_options_layout.addLayout(v_layout)

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

        config_value = str(self._get_option_value(saved_options, "adb_config", ""))
        if config_value:
            # 阻止信号，避免初始化时触发保存
            config_line_edit.blockSignals(True)
            config_line_edit.setText(config_value)
            config_line_edit.blockSignals(False)
        config_line_edit.textChanged.connect(lambda: self._save_current_options())
        self.controller_specific_options_layout.addWidget(config_line_edit)

    def _add_adb_screenshot_method_option(self, saved_options: dict):
        """添加 ADB 截图方法下拉框"""
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
        original_value = self._get_option_value(
            saved_options, "adb_screenshot_method", "1"
        )
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
        self.controller_specific_options_layout.addLayout(v_layout)

    def _add_adb_input_method_option(self, saved_options: dict):
        """添加 ADB 输入方法下拉框"""
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
        original_value = self._get_option_value(saved_options, "adb_input_method", "1")
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
        self.controller_specific_options_layout.addLayout(v_layout)

    def _show_win32_options(self, saved_options: dict):
        """显示 Win32 特定选项"""
        text_options = [
            (
                "hwnd",
                self.tr("Window Handle (HWND)"),
                "",
                self.tr("Window handle identifier"),
            ),
            (
                "app_path",
                self.tr("Application Path"),
                "",
                self.tr("Path to application executable"),
            ),
            (
                "app_launch_args",
                self.tr("Application Launch Args"),
                "",
                self.tr("Arguments for launching application"),
            ),
            (
                "app_launch_timeout",
                self.tr("Application Launch Timeout (ms)"),
                "10000",
                self.tr("Time to wait for application startup"),
            ),
        ]

        for obj_name, label_text, default_value, tooltip_text in text_options:
            v_layout = QVBoxLayout()
            v_layout.setObjectName(f"{obj_name}_layout")

            label = BodyLabel(label_text)
            line_edit = LineEdit()
            line_edit.setObjectName(obj_name)

            # 阻止信号，避免初始化时触发保存
            line_edit.blockSignals(True)
            line_edit.setText(
                str(self._get_option_value(saved_options, obj_name, default_value))
            )
            line_edit.blockSignals(False)

            line_edit.setToolTip(tooltip_text)
            label.setToolTip(tooltip_text)

            # 连接信号
            line_edit.textChanged.connect(lambda: self._save_current_options())

            v_layout.addWidget(label)
            v_layout.addWidget(line_edit)

            self.controller_specific_options_layout.addLayout(v_layout)

        # Win32 截图方法下拉框
        self._add_win32_screenshot_method_option(saved_options)

        # Win32 输入方法下拉框
        self._add_win32_input_method_option(saved_options)

    def _add_win32_screenshot_method_option(self, saved_options: dict):
        """添加 Win32 截图方法下拉框"""
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
        current_value = str(
            self._get_option_value(saved_options, "win32_screenshot_method", "1")
        )
        combo.blockSignals(True)  # 阻止信号，避免初始化时触发保存
        for i in range(combo.count()):
            if combo.itemData(i) == current_value:
                combo.setCurrentIndex(i)
                break
        combo.blockSignals(False)

        combo.currentIndexChanged.connect(lambda: self._save_current_options())

        v_layout.addWidget(label)
        v_layout.addWidget(combo)
        self.controller_specific_options_layout.addLayout(v_layout)

    def _add_win32_input_method_option(self, saved_options: dict):
        """添加 Win32 输入方法下拉框"""
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
        current_value = str(
            self._get_option_value(saved_options, "win32_input_method", "1")
        )
        combo.blockSignals(True)  # 阻止信号，避免初始化时触发保存
        for i in range(combo.count()):
            if combo.itemData(i) == current_value:
                combo.setCurrentIndex(i)
                break
        combo.blockSignals(False)

        combo.currentIndexChanged.connect(lambda: self._save_current_options())

        v_layout.addWidget(label)
        v_layout.addWidget(combo)
        self.controller_specific_options_layout.addLayout(v_layout)

    def _show_controller_common_options(self, saved_options: dict):
        """显示控制器通用选项"""
        options = [
            (
                "gpu_selection",
                self.tr("GPU Selection"),
                "",
                self.tr("GPU device to use"),
            ),
            (
                "pre_launch_program",
                self.tr("Pre-Launch Program"),
                "",
                self.tr("Program to run before starting"),
            ),
            (
                "pre_launch_program_args",
                self.tr("Pre-Launch Program Args"),
                "",
                self.tr("Arguments for pre-launch program"),
            ),
            (
                "post_launch_program",
                self.tr("Post-Launch Program"),
                "",
                self.tr("Program to run after starting"),
            ),
            (
                "post_launch_program_args",
                self.tr("Post-Launch Program Args"),
                "",
                self.tr("Arguments for post-launch program"),
            ),
        ]

        for obj_name, label_text, default_value, tooltip_text in options:
            v_layout = QVBoxLayout()
            v_layout.setObjectName(f"{obj_name}_layout")

            label = BodyLabel(label_text)
            line_edit = LineEdit()
            line_edit.setObjectName(obj_name)

            # 阻止信号，避免初始化时触发保存
            line_edit.blockSignals(True)
            line_edit.setText(
                str(self._get_option_value(saved_options, obj_name, default_value))
            )
            line_edit.blockSignals(False)

            line_edit.setToolTip(tooltip_text)
            label.setToolTip(tooltip_text)

            # 连接信号
            line_edit.textChanged.connect(lambda: self._save_current_options())

            v_layout.addWidget(label)
            v_layout.addWidget(line_edit)

            self.controller_common_options_layout.addLayout(v_layout)

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
            adb_path = str(self._get_option_value(flattened_options, "adb_path", ""))
            adb_address = str(self._get_option_value(flattened_options, "adb_port", ""))
            # 优先使用新的独立字段，如果没有则回退到旧的共享字段（兼容旧配置）
            adb_device_name_new = str(
                self._get_option_value(flattened_options, "adb_device_name", "")
            )
            device_name_old = str(
                self._get_option_value(flattened_options, "device_name", "")
            )
            device_name = adb_device_name_new or device_name_old

            logger.info(f"保存的 adb_path: {adb_path}")
            logger.info(f"保存的 adb_port (address): {adb_address}")
            logger.info(f"保存的 adb_device_name (新字段): {adb_device_name_new}")
            logger.info(f"保存的 device_name (旧字段): {device_name_old}")
            logger.info(f"最终使用的 device_name: {device_name}")

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
                    str(
                        self._get_option_value(
                            flattened_options, "adb_screenshot_method", "0"
                        )
                    )
                    or "0"
                ),
                "input_methods": int(
                    str(
                        self._get_option_value(
                            flattened_options, "adb_input_method", "0"
                        )
                    )
                    or "0"
                ),
                "config": {},
            }

            logger.debug(
                f"构建的设备数据 - name: {device_data['name']}, address: {device_data['address']}"
            )

            # 尝试解析 adb_config
            import json

            adb_config_str = str(
                self._get_option_value(flattened_options, "adb_config", "")
            )
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
            hwnd_str = str(self._get_option_value(flattened_options, "hwnd", ""))
            # 优先使用新的独立字段，如果没有则回退到旧的共享字段（兼容旧配置）
            device_name = str(
                self._get_option_value(flattened_options, "win32_device_name", "")
            ) or str(self._get_option_value(flattened_options, "device_name", ""))

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

        # 清空当前设备列表
        self.device_combo.clear()

        if controller_type == "adb":
            # 调用 ADB 设备获取方法
            devices = self._get_adb_devices()
            self._populate_device_list(devices)
        elif controller_type == "win32":
            # 调用 Win32 设备获取方法
            devices = self._get_win32_devices()
            self._populate_device_list(devices)
        else:
            logger.warning(f"未知的控制器类型: {controller_type}")

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
        """获取 ADB 设备列表

        通过 maa.toolkit 调用实际的 ADB 设备检测逻辑

        Returns:
            AdbDevice 对象列表
        """
        try:
            from maa.toolkit import Toolkit

            logger.info("获取 ADB 设备列表")
            adb_devices = Toolkit.find_adb_devices()
            logger.info(f"找到 {len(adb_devices)} 个 ADB 设备")
            return adb_devices
        except Exception as e:
            logger.error(f"获取 ADB 设备失败: {e}")
            return []

    def _get_win32_devices(self):
        """获取 Win32 窗口列表

        通过 maa.toolkit 调用实际的 Win32 窗口检测逻辑

        Returns:
            DesktopWindow 对象列表
        """
        try:
            from maa.toolkit import Toolkit

            logger.info("获取 Win32 窗口列表")
            windows = Toolkit.find_desktop_windows()
            logger.info(f"找到 {len(windows)} 个窗口")
            return windows
        except Exception as e:
            logger.error(f"获取 Win32 窗口失败: {e}")
            return []

    def _populate_device_list(self, devices):
        """填充设备下拉框

        使用 interface.json 中的配置进行过滤和匹配：
        - Win32: 使用 class_regex 和 window_regex 过滤窗口
        - ADB: 直接显示所有设备

        Args:
            devices: 设备列表（AdbDevice 或 DesktopWindow 对象）
        """
        if not devices:
            self.device_combo.addItem(self.tr("No devices found"))
            logger.warning("未找到设备")
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

        # 如果找到匹配项，自动选中第一个
        if first_match_index >= 0:
            self.device_combo.setCurrentIndex(first_match_index)
            logger.info(f"自动选中第一个匹配的设备（索引: {first_match_index}）")

        added_count = self.device_combo.count()
        logger.info(
            f"已添加 {added_count} 个设备到列表（总共检测到 {len(devices)} 个）"
        )

    def _show_post_task_setting_option(self, item: TaskItem):
        """显示完成后设置选项 - 2个下拉框"""
        self._clear_options()

        # 获取当前保存的选项
        saved_options = item.task_option

        # 第一个下拉框：完成后操作
        post_action_layout = QVBoxLayout()
        post_action_layout.setObjectName("post_action_layout")

        post_action_label = BodyLabel(self.tr("Action After Completion"))
        post_action_label.setStyleSheet("font-weight: bold;")
        post_action_layout.addWidget(post_action_label)

        post_action_combo = ComboBox()
        post_action_combo.setObjectName("post_action")
        post_action_combo.setMaximumWidth(400)  # 限制最大宽度
        post_action_options = [
            self.tr("None"),
            self.tr("Exit Program"),
            self.tr("Shutdown Computer"),
            self.tr("Hibernate Computer"),
            self.tr("Sleep Computer"),
        ]
        post_action_combo.addItems(post_action_options)

        current_action = saved_options.get("post_action", "")
        if current_action:
            post_action_combo.setCurrentText(current_action)

        post_action_combo.currentTextChanged.connect(
            lambda: self._save_current_options()
        )

        post_action_layout.addWidget(post_action_combo)
        self.option_area_layout.addLayout(post_action_layout)

        # 第二个下拉框：通知方式
        notification_layout = QVBoxLayout()
        notification_layout.setObjectName("notification_layout")

        notification_label = BodyLabel(self.tr("Notification Method"))
        notification_label.setStyleSheet("font-weight: bold;")
        notification_layout.addWidget(notification_label)

        notification_combo = ComboBox()
        notification_combo.setObjectName("notification")
        notification_combo.setMaximumWidth(400)  # 限制最大宽度
        notification_options = [
            self.tr("None"),
            self.tr("System Notification"),
            self.tr("Sound Alert"),
            self.tr("Email Notification"),
            self.tr("Webhook"),
        ]
        notification_combo.addItems(notification_options)

        current_notification = saved_options.get("notification", "")
        if current_notification:
            notification_combo.setCurrentText(current_notification)

        notification_combo.currentTextChanged.connect(
            lambda: self._save_current_options()
        )

        notification_layout.addWidget(notification_combo)
        self.option_area_layout.addLayout(notification_layout)

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
        # multi_input 选项的值应该是字典，如果不是则重置为空字典
        if not isinstance(saved_data, dict):
            saved_data = {}
            logger.warning(f"选项 '{option_name}' 的值不是字典，已重置为空字典")

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

            # 获取当前值
            current_value = saved_data.get(input_name, default_value)

            # 如果需要转换为整数
            if pipeline_type == "int" and isinstance(current_value, str):
                try:
                    current_value = int(current_value) if current_value else 0
                    if input_name in saved_data:
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
                    insert_index=insert_index,
                )
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
                    insert_index=insert_index,
                )
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
        insert_index: int | None = None,
    ) -> QVBoxLayout:
        """创建嵌套选项的布局

        Args:
            depth: 嵌套深度（保留参数以保持接口兼容，但不再用于UI显示）
            insert_index: 插入位置索引（作为嵌套选项时使用）

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

        # 添加到选项区域（支持指定插入位置）
        if insert_index is not None:
            self.option_area_layout.insertLayout(insert_index, v_layout)
        # else: 不在这里添加，由调用者决定如何添加

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
        """清除所有选项"""

        def recursive_clear_layout(layout):
            """递归清理布局中的所有项目"""
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
