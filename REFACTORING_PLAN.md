# 组件重构为 Mixin 架构计划

## 当前架构问题

### 1. 组件独立创建带来的问题
- `ControllerSettingWidget`、`ResourceSettingWidget`、`PostActionSettingWidget` 都是独立的 QWidget 实例
- 需要通过 `parent_layout` 参数将控件添加到布局中
- 切换选项时需要清理和重新创建控件，导致信号连接丢失

### 2. 状态共享复杂
- 需要通过 `setattr` 动态设置方法（`_clear_options`、`_set_description` 等）
- 需要通过 `current_config` 字典共享状态
- 需要通过回调函数在组件之间通信

### 3. 生命周期管理复杂
- 每次调用 `create_settings()` 时，组件会重新创建控件
- `_clear_options()` 会清理布局中的控件，导致组件内部状态不一致
- 信号连接在组件清理时断开，需要手动重新连接

## Mixin 架构优势

### 1. 统一的生命周期
- 所有方法直接成为 `OptionWidget` 的一部分
- 不需要创建独立的组件实例
- 组件状态在整个 `OptionWidget` 生命周期内保持稳定

### 2. 简单的状态共享
- 直接访问 `self.current_config`、`self.service_coordinator` 等属性
- 不需要通过 `setattr` 和回调函数
- 方法调用更直接

### 3. 稳定的信号连接
- 信号连接不会因为组件销毁而丢失
- 不需要在清理时断开信号，在创建时重新连接
- 避免 RuntimeWarning 和崩溃问题

### 4. 更清晰的代码结构
- 所有相关方法都在同一个类中
- 更容易理解和维护
- 减少组件间的依赖关系

## 重构步骤

### 步骤 1: 重构 ResourceSettingWidget 为 ResourceSettingMixin
- 移除 `__init__` 方法（不需要独立的组件实例）
- 移除 `parent_layout` 参数，直接使用 `self.option_page_layout`
- 将 `resource_setting_widgets` 改为 `self.resource_setting_widgets`
- 移除通过 `setattr` 设置的方法调用

### 步骤 2: 重构 PostActionSettingWidget 为 PostActionSettingMixin
- 移除 `__init__` 方法
- 移除 `parent_layout` 参数
- 将 `post_action_widgets` 改为 `self.post_action_widgets`
- 移除通过 `setattr` 设置的方法调用

### 步骤 3: 重构 ControllerSettingWidget 为 ControllerSettingMixin（可选）
- 虽然名称是 ControllerSettingWidget，但可以重构为真正的 mixin
- 与 ResourceSettingMixin 和 PostActionSettingMixin 保持一致

### 步骤 4: 更新 OptionWidget
- 移除组件实例创建
- 使用多重继承添加 mixin 功能
- 更新方法调用，移除 `self.resource_setting_widget.xxx` 改为 `self.xxx`
- 简化 `_clear_options()` 方法，只清理控件，不清理组件

## 重构后的代码结构

```python
class OptionWidget(
    QWidget,
    ResourceSettingMixin,
    PostActionSettingMixin,
    ControllerSettingMixin,
):
    def __init__(self, ...):
        # 初始化 QWidget
        super().__init__(parent)
        # 初始化 mixin（不需要创建组件实例）
        self._init_resource_settings()
        self._init_post_action_settings()
        self._init_controller_settings()
    
    def _clear_options(self):
        # 只清理控件，不清理组件
        # 组件状态保持稳定
        ...
```

