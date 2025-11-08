"""OptionWidget 重构模块

这个包包含了从原始 OptionWidget.py (3000+ 行) 中拆分出来的功能模块。

模块说明:
- option_data_manager: 选项数据的保存、组织和转换
- widget_factory: 创建各种类型的选项控件
- nested_option_handler: 处理选项的嵌套关系
- device_manager: 设备列表的获取、过滤和管理

使用示例请参考 OptionWidget_Refactored_Example.py
"""

from .option_data_manager import OptionDataManager
from .widget_factory import WidgetFactory
from .nested_option_handler import NestedOptionHandler
from .device_manager import DeviceManager

__all__ = [
    "OptionDataManager",
    "WidgetFactory",
    "NestedOptionHandler",
    "DeviceManager",
]
