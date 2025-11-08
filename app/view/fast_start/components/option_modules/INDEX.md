# Option Modules 文件索引

## 📂 文件结构

```
option_modules/
├── __init__.py                          # 包初始化文件，导出主要类
├── README.md                            # 文件夹说明和使用指南
├── option_data_manager.py               # 数据管理模块 (~330行)
├── widget_factory.py                    # 控件工厂模块 (~380行)
├── nested_option_handler.py             # 嵌套选项处理模块 (~300行)
├── device_manager.py                    # 设备管理模块 (~240行)
├── OptionWidget_Refactored_Example.py   # 使用示例 (~350行)
├── REFACTORING.md                       # 重构说明文档
├── REFACTOR_SUMMARY.md                  # 详细总结文档
└── INDEX.md                             # 本文件
```

## 🎯 快速导航

### 我想了解...

- **如何使用这些模块？** → 查看 `OptionWidget_Refactored_Example.py`
- **重构的原因和策略？** → 查看 `REFACTORING.md`
- **详细的功能说明？** → 查看 `REFACTOR_SUMMARY.md`
- **如何开始集成？** → 查看 `README.md`

### 我想修改...

- **数据保存逻辑** → 编辑 `option_data_manager.py`
- **控件创建方式** → 编辑 `widget_factory.py`
- **嵌套选项行为** → 编辑 `nested_option_handler.py`
- **设备管理功能** → 编辑 `device_manager.py`

## 📋 核心类说明

| 类名 | 文件 | 主要职责 |
|------|------|----------|
| `OptionDataManager` | option_data_manager.py | 数据的保存、组织、转换 |
| `WidgetFactory` | widget_factory.py | 创建各种选项控件 |
| `NestedOptionHandler` | nested_option_handler.py | 处理嵌套选项关系 |
| `DeviceManager` | device_manager.py | 管理设备列表 |

## 🔗 模块依赖关系

```
OptionWidget (主类)
    ├── OptionDataManager      # 独立使用
    ├── WidgetFactory          # 独立使用
    ├── NestedOptionHandler    # 依赖 WidgetFactory
    └── DeviceManager          # 独立使用
```

## 📊 代码统计

- **原文件**: OptionWidget.py (~3000行)
- **重构后**:
  - option_data_manager.py: ~330行
  - widget_factory.py: ~380行
  - nested_option_handler.py: ~300行
  - device_manager.py: ~240行
  - 示例主文件: ~350行
  - **总计**: ~1600行 + 文档

**代码精简**: ~45% (通过模块化消除重复)

## ⚡ 快速开始

```python
# 1. 导入模块
from .option_modules import (
    OptionDataManager,
    WidgetFactory,
    NestedOptionHandler,
    DeviceManager,
)

# 2. 初始化
self.data_manager = OptionDataManager(service_coordinator)
self.widget_factory = WidgetFactory(...)
self.nested_handler = NestedOptionHandler(...)
self.device_manager = DeviceManager(service_coordinator)

# 3. 使用
self.widget_factory.add_combox_option(...)
self.data_manager.save_options(...)
```

详细示例请查看 `OptionWidget_Refactored_Example.py`

## 📝 更新日志

- **2025-11-07**: 初始创建，从 OptionWidget.py 拆分出 4 个核心模块
