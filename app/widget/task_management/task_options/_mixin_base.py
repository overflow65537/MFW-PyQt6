"""Mixin 基类模块

提供所有 task_options Mixin 的通用类型提示基类。
"""

from typing import TYPE_CHECKING, Any, Protocol, Union

if TYPE_CHECKING:
    from PySide6.QtWidgets import QVBoxLayout, QLayout, QWidget


class OptionWidgetProtocol(Protocol):
    """OptionWidget 协议定义
    
    定义了所有 Mixin 依赖的宿主类（OptionWidget）应该提供的属性和方法。
    使用 Protocol 而不是抽象基类，避免运行时开销和继承复杂度。
    
    设计说明：
    这个协议仅用于类型检查（TYPE_CHECKING），不会在运行时执行。
    所有 task_options 相关的 Mixin 都应该继承 MixinBase，以获得正确的类型提示。
    """
    
    # 布局容器
    controller_specific_options_layout: "QVBoxLayout"
    controller_common_options_layout: "QVBoxLayout"
    option_area_layout: "QVBoxLayout"
    resource_combo_layout: "QVBoxLayout"
    
    # 服务协调器
    service_coordinator: Any
    
    # 任务相关
    task: Any
    current_task: Any
    
    # 图标加载器
    icon_loader: Any
    
    # 控制器相关控件
    device_combo: Any
    controller_type_combo: Any
    controller_configs: dict
    
    # 辅助方法
    def _get_option_value(self, options: dict, key: str, default: Any) -> Any:
        """从选项字典获取值"""
        ...
    
    def _save_current_options(self) -> None:
        """保存当前选项"""
        ...
    
    def _clear_options(self) -> None:
        """清空选项"""
        ...
    
    def _clear_layout(self, layout: Union["QVBoxLayout", "QLayout"]) -> None:
        """清空布局"""
        ...
    
    def _flatten_controller_options(self, options: dict) -> dict:
        """展平控制器选项"""
        ...
    
    def _get_adb_devices(self) -> list:
        """获取 ADB 设备列表"""
        ...
    
    def _get_win32_devices(self) -> list:
        """获取 Win32 窗口列表"""
        ...
    
    def _populate_device_list(self, devices: list) -> None:
        """填充设备列表"""
        ...
    
    def _populate_saved_device(self, saved_options: dict, controller_name: str) -> None:
        """填充保存的设备信息"""
        ...
    
    def findChild(self, type: type, /, name: str = "") -> Any:
        """查找子控件（来自 QObject）"""
        ...
    
    def tr(self, sourceText: str, /, disambiguation: str | None = None, n: int = -1) -> str:
        """QObject 的翻译方法（国际化）"""
        ...
    
    # 动画相关方法（在 AnimationMixin 中）
    def _toggle_description(self, visible: bool) -> None:
        """切换描述显示（带动画）"""
        ...
    
    def _animate_splitter(self, from_option: int, to_option: int, from_desc: int, 
                          to_desc: int, duration: int = 300, on_finished: Any = None) -> None:
        """动画调整 QSplitter 尺寸"""
        ...
    
    def set_description(self, description: str) -> None:
        """设置描述文本"""
        ...
    
    def _add_combox_option(self, *args, **kwargs) -> Any:
        """添加下拉框选项（在 WidgetCreatorsMixin 中）"""
        ...
    
    def _add_multi_input_option(self, *args, **kwargs) -> Any:
        """添加多输入选项（在 WidgetCreatorsMixin 中）"""
        ...
    
    def _on_combox_changed(self, combo_box: Any, text: str) -> None:
        """下拉框值改变回调（在 NestedOptionsMixin 中）"""
        ...
    
    def _update_nested_options(self, combo_box: Any, selected_case: str, recursive: bool = True) -> None:
        """更新嵌套选项（在 NestedOptionsMixin 中）"""
        ...
    
    def Get_Task_List(self, interface: Any, target: str) -> list:
        """获取任务列表（在 TaskOptionsMixin 中）"""
        ...
    
    # 控制器选项相关方法
    def _show_adb_options(self, saved_options: dict) -> None:
        """显示 ADB 控制器选项（在 AdbControllerMixin 中）"""
        ...
    
    def _show_win32_options(self, saved_options: dict) -> None:
        """显示 Win32 控制器选项（在 Win32ControllerMixin 中）"""
        ...
    
    def _show_controller_common_options(self, saved_options: dict) -> None:
        """显示控制器通用选项（在 ControllerCommonMixin 中）"""
        ...


class MixinBase:
    """所有 task_options Mixin 的通用基类
    
    设计说明：
    这是一个 Mixin 基类，不直接实例化，而是通过多重继承与 OptionWidget 组合使用。
    当 Mixin 的方法在 OptionWidget 实例上调用时，`self` 实际指向 OptionWidget 实例，
    因此可以访问 OptionWidget 提供的属性和方法（包括从 QWidget 继承的 `tr` 方法）。
    
    类型提示：
    在 TYPE_CHECKING 块中声明了 OptionWidgetProtocol 中定义的所有属性/方法，
    这样 Pylance 就能识别这些成员，不会报告"未定义"错误。
    """
    
    if TYPE_CHECKING:
        # 告诉类型检查器：这些属性/方法由宿主类（OptionWidget）提供
        # 实际运行时，self 是 OptionWidget 实例，这些成员确实存在
        
        # 布局容器
        controller_specific_options_layout: "QVBoxLayout"
        controller_common_options_layout: "QVBoxLayout"
        option_area_layout: "QVBoxLayout"
        resource_combo_layout: "QVBoxLayout"
        
        # 服务协调器
        service_coordinator: Any
        
        # 任务相关
        task: Any
        current_task: Any
        
        # 图标加载器
        icon_loader: Any
        
        # 控制器相关控件
        device_combo: Any
        controller_type_combo: Any
        controller_configs: dict
        
        def _get_option_value(self, options: dict, key: str, default: Any) -> Any:
            """从选项字典获取值（由宿主类提供）"""
            ...
        
        def _save_current_options(self) -> None:
            """保存当前选项（由宿主类提供）"""
            ...
        
        def _clear_options(self) -> None:
            """清空选项（由宿主类提供）"""
            ...
        
        def _clear_layout(self, layout: Union["QVBoxLayout", "QLayout"]) -> None:
            """清空布局（由宿主类提供）"""
            ...
        
        def _flatten_controller_options(self, options: dict) -> dict:
            """展平控制器选项（由宿主类提供）"""
            ...
        
        def _get_adb_devices(self) -> list:
            """获取 ADB 设备列表（由宿主类提供）"""
            ...
        
        def _get_win32_devices(self) -> list:
            """获取 Win32 窗口列表（由宿主类提供）"""
            ...
        
        def _populate_device_list(self, devices: list) -> None:
            """填充设备列表（由宿主类提供）"""
            ...
        
        def _populate_saved_device(self, saved_options: dict, controller_name: str) -> None:
            """填充保存的设备信息（由宿主类提供）"""
            ...
        
        def findChild(self, type: type, /, name: str = "") -> Any:
            """查找子控件（由宿主类 QObject 提供）"""
            ...
        
        def tr(self, sourceText: str, /, disambiguation: str | None = None, n: int = -1) -> str:
            """QObject 的翻译方法（由宿主类 QObject 提供）"""
            ...
        
        # 动画相关方法（在 AnimationMixin 中提供）
        def _toggle_description(self, visible: bool) -> None:
            """切换描述显示（带动画）（在 AnimationMixin 中提供）"""
            ...
        
        def _animate_splitter(self, from_option: int, to_option: int, from_desc: int, 
                              to_desc: int, duration: int = 300, on_finished: Any = None) -> None:
            """动画调整 QSplitter 尺寸（在 AnimationMixin 中提供）"""
            ...
        
        def set_description(self, description: str) -> None:
            """设置描述文本（由宿主类提供）"""
            ...
        
        def _add_combox_option(self, *args, **kwargs) -> Any:
            """添加下拉框选项（在 WidgetCreatorsMixin 中提供）"""
            ...
        
        def _add_multi_input_option(self, *args, **kwargs) -> Any:
            """添加多输入选项（在 WidgetCreatorsMixin 中提供）"""
            ...
        
        def _on_combox_changed(self, combo_box: Any, text: str) -> None:
            """下拉框值改变回调（在 NestedOptionsMixin 中提供）"""
            ...
        
        def _update_nested_options(self, combo_box: Any, selected_case: str, recursive: bool = True) -> None:
            """更新嵌套选项（在 NestedOptionsMixin 中提供）"""
            ...
        
        def Get_Task_List(self, interface: Any, target: str) -> list:
            """获取任务列表（在 TaskOptionsMixin 中提供）"""
            ...
        
        # 控制器选项相关方法
        def _show_adb_options(self, saved_options: dict) -> None:
            """显示 ADB 控制器选项（在 AdbControllerMixin 中提供）"""
            ...
        
        def _show_win32_options(self, saved_options: dict) -> None:
            """显示 Win32 控制器选项（在 Win32ControllerMixin 中提供）"""
            ...
        
        def _show_controller_common_options(self, saved_options: dict) -> None:
            """显示控制器通用选项（在 ControllerCommonMixin 中提供）"""
            ...
