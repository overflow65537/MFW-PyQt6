# Option Modules - OptionWidget 重构模块

## 📁 文件夹说明

这个文件夹包含了从原始 `OptionWidget.py` (3000+ 行) 中拆分出来的功能模块。

## 📦 模块列表

### 核心模块

1. **option_data_manager.py** (~330 行)
   - 选项数据的保存、组织和转换
   - MAA 标准格式与 UI 扁平格式之间的转换

2. **widget_factory.py** (~380 行)
   - 控件工厂，创建各种类型的选项控件
   - 支持下拉框、文本框、开关、多输入项等

3. **nested_option_handler.py** (~300 行)
   - 处理选项的嵌套关系
   - 支持多层嵌套和递归加载/卸载

4. **device_manager.py** (~240 行)
   - 管理 ADB 和 Win32 设备
   - 设备列表的获取、过滤和配置恢复

### 示例和文档

- **OptionWidget_Refactored_Example.py** - 使用示例
- **REFACTORING.md** - 重构说明
- **REFACTOR_SUMMARY.md** - 详细总结

## 🚀 快速使用

```python
from .option_modules import (
    OptionDataManager,
    WidgetFactory,
    NestedOptionHandler,
    DeviceManager,
)

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

## 📊 重构效果

- ✅ 代码从 3000+ 行拆分为 4 个核心模块
- ✅ 每个模块职责单一，易于维护
- ✅ 模块之间低耦合，可独立测试
- ✅ 提高了代码的可重用性和可读性

## 📝 详细文档

请查看以下文档了解更多信息：

- **REFACTORING.md** - 重构策略和步骤
- **REFACTOR_SUMMARY.md** - 详细的重构总结和使用指南
- **OptionWidget_Refactored_Example.py** - 完整的使用示例代码

## 🔧 维护指南

### 添加新功能

1. 确定功能属于哪个模块
2. 在对应模块中添加方法
3. 更新 `__init__.py` 的导出（如果需要）
4. 更新文档说明

### 修改现有功能

1. 找到对应的模块文件
2. 修改相关方法
3. 运行测试确保兼容性
4. 更新文档（如果接口有变化）

## ⚠️ 注意事项

- 这些模块是从原始文件中提取的，需要与主 OptionWidget 配合使用
- 修改模块时注意保持向后兼容性
- 建议在完全迁移前保留原始 OptionWidget.py 作为备份

## 📅 创建日期

2025年11月7日

## 👤 维护者

overflow65537
