# OptionWidget 重构说明

## 文件结构

原来的 `OptionWidget.py` (3000+ 行) 已被拆分为以下模块:

### 核心模块

1. **option_data_manager.py** - 选项数据管理
   - `OptionDataManager` 类
   - 负责保存、组织和转换选项数据
   - 主要方法:
     - `save_options()` - 保存选项到任务配置
     - `organize_controller_options()` - 组织为 MAA 标准格式
     - `flatten_controller_options()` - 展平嵌套结构

2. **widget_factory.py** - 控件工厂
   - `WidgetFactory` 类
   - 创建各种类型的选项控件
   - 主要方法:
     - `add_combox_option()` - 创建下拉框
     - `add_lineedit_option()` - 创建文本输入框
     - `add_switch_option()` - 创建开关按钮
     - `add_multi_input_option()` - 创建多输入项控件

3. **nested_option_handler.py** - 嵌套选项处理
   - `NestedOptionHandler` 类
   - 处理选项的嵌套关系
   - 主要方法:
     - `update_nested_options()` - 更新嵌套选项显示
     - `create_nested_option_layout()` - 创建嵌套选项布局
     - `remove_nested_options()` - 移除嵌套选项

4. **device_manager.py** - 设备管理
   - `DeviceManager` 类
   - 管理设备列表的获取和填充
   - 主要方法:
     - `get_adb_devices()` - 获取 ADB 设备
     - `get_win32_devices()` - 获取 Win32 窗口
     - `populate_device_list()` - 填充设备列表
     - `populate_saved_device()` - 从配置恢复设备信息

### 待创建模块

5. **task_option_handler.py** (待创建) - 任务选项处理
   - 处理普通任务选项的显示
   - 处理基础任务选项(资源设置、完成后操作)

## 重构优势

1. **代码组织**: 每个模块职责单一,易于维护
2. **可测试性**: 模块化后更容易编写单元测试
3. **可重用性**: 各模块可独立使用
4. **可读性**: 文件大小合理,逻辑清晰

## 使用示例

```python
from .option_data_manager import OptionDataManager
from .widget_factory import WidgetFactory
from .nested_option_handler import NestedOptionHandler
from .device_manager import DeviceManager

class OptionWidget(QWidget):
    def __init__(self, service_coordinator, parent=None):
        super().__init__(parent)
        
        # 初始化各个管理器
        self.data_manager = OptionDataManager(service_coordinator)
        self.widget_factory = WidgetFactory(
            service_coordinator,
            self.option_area_layout,
            self.icon_loader,
            self._save_current_options
        )
        self.nested_handler = NestedOptionHandler(
            service_coordinator,
            self.option_area_layout,
            self.icon_loader,
            self.Get_Task_List,
            self._save_current_options
        )
        self.device_manager = DeviceManager(service_coordinator)
```

## 迁移步骤

1. ✅ 创建 `option_data_manager.py`
2. ✅ 创建 `widget_factory.py`
3. ✅ 创建 `nested_option_handler.py`
4. ✅ 创建 `device_manager.py`
5. ⏳ 创建 `task_option_handler.py`
6. ⏳ 重构 `OptionWidget.py` 主文件
