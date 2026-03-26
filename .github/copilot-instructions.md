# MFW-PyQt6 代码规范 — Copilot / AI Agent 指令

> 本文件用于规范 AI 代码生成工具在此项目中的行为，确保生成的代码符合项目的架构约定。

## 项目概述

MFW-ChainFlow Assistant 是一个基于 **PySide6 (Qt6)** 的桌面应用，作为 MaaFramework 的通用 UI Client。
项目遵循 **MVC (Model-View-Controller/Service)** 分层架构，追求 **低耦合、高内聚**。

## 分层架构

```
app/
├── common/          # 共享基础设施: 信号总线、全局配置、常量
├── core/            # 业务核心 (Model + Controller/Service)
│   ├── Item.py      # 数据模型 (TaskItem, ConfigItem, CoreSignalBus ...)
│   ├── core.py      # ServiceCoordinator — 服务编排入口
│   ├── service/     # 各业务 Service (Config, Task, Option, Schedule, InterfaceManager, i18n)
│   ├── runner/      # 运行时 (TaskFlowRunner, MaaFW, MonitorTask)
│   └── utils/       # 核心工具 (pipeline_helper, holiday)
├── view/            # 视图层 (各 Interface / Window)
├── widget/          # 可复用 UI 组件
├── utils/           # 应用级工具 (logger, crypto, notice, update ...)
├── i18n/            # Qt Linguist 翻译文件
└── assets/          # 图标、图片等静态资源
```

---

## 核心规则

### 1. 信号总线分层 — 禁止跨层直接耦合

项目存在 **两个信号总线**，分属不同层级：

| 信号总线 | 定义位置 | 作用域 | 允许的发射者 | 允许的监听者 |
|----------|----------|--------|--------------|--------------|
| `CoreSignalBus` | `app/core/Item.py` | Core↔Service 内部通信 | Service / Runner | Service / ServiceCoordinator |
| `FromeServiceCoordinator` | `app/core/Item.py` | Core→View 单向通知 | ServiceCoordinator / Runner | View 层 |
| `signalBus` (全局) | `app/common/signal_bus.py` | View↔View / View↔App | View 层 / App 级组件 | View 层 / App 级组件 |

**规则：**
- **`app/core/runner/` 和 `app/core/service/` 中的代码禁止直接 import `signalBus`（全局信号总线）。**
  - 现有代码中存在此类违规（`task_flow.py`、`maafw.py`、`log_processor.py` 直接 import `signalBus`），这是已知技术债务，不得新增。
  - 新增的 Core 层通信必须通过 `CoreSignalBus` 或 `FromeServiceCoordinator`。
- View 层通过 `FromeServiceCoordinator` 信号或 `signalBus` 全局信号响应 Core 层事件，**不要在 View 中直接调用 Service 的内部方法改变业务状态**。
- 如需在 Core 层发送日志，使用 `signalBus.log_output.emit()` 是当前的过渡方案；新代码优先通过 Runner 自身 Signal（如 `MaaFW.agent_info`、`MaaFW.custom_info`）向上层传递，由 `ServiceCoordinator` 或适配层转发给 `signalBus`。

### 2. MVC 职责划分

#### Model（数据模型 — `app/core/Item.py`）
- 纯数据类，使用 `@dataclass`。
- 不导入 View、Widget 或 `signalBus`。
- 仅包含数据字段、序列化/反序列化方法、ID 生成。

#### Service / Controller（`app/core/service/` + `app/core/core.py`）
- 负责业务逻辑、状态管理、配置持久化。
- 通过 `CoreSignalBus` 通知状态变化。
- 不直接操作 UI 组件或 import View/Widget 模块。
- `ServiceCoordinator`（`core.py`）负责组装各 Service 并暴露给 View 层。

#### Runner（`app/core/runner/`）
- 负责异步任务执行（MaaFW 控制、任务流编排）。
- 可发射自身定义的 `Signal`（如 `MaaFW.custom_info`, `MaaFW.agent_info`）。
- **新代码不应新增 `from app.common.signal_bus import signalBus`**。
- 已有 `signalBus` 引用作为技术债保留，但新增功能应通过 Runner Signal → ServiceCoordinator → signalBus 链路传递。

#### View（`app/view/`）
- 负责 UI 展示与用户交互。
- 通过 `ServiceCoordinator` 的方法执行业务操作。
- 监听 `FromeServiceCoordinator` / `signalBus` 获取状态更新。
- **不应直接修改 `TaskItem.is_checked` 等 Model 属性**，应通过 Service 方法。
- **不应包含业务逻辑**（如 pipeline override 计算、资源路径拼接）。

#### Widget（`app/widget/`）
- 可复用的纯 UI 组件。
- 不导入 Service、ServiceCoordinator 或 Core 模块。
- 通过自身 Signal/Slot 与父 View 通信。

### 3. 数据流方向

```
用户操作 → View → ServiceCoordinator.method() → Service → CoreSignalBus
                                                              ↓
View ← signalBus / FromeServiceCoordinator ← ServiceCoordinator ← CoreSignalBus

Runner(MaaFW/TaskFlow) → Runner Signal → ServiceCoordinator → signalBus → View
```

**禁止方向：**
- View → 直接修改 Model 属性（跳过 Service）
- Runner → 直接 emit signalBus（新代码禁止，旧代码暂容忍）
- Widget → 直接 import Service
- Service → 直接 import View / Widget

### 4. 命名与编码约定

| 分类 | 约定 |
|------|------|
| 文件名 / 模块名 | 一律使用小写蛇形，例如 `config_service.py`、`task_interface_logic.py`、`list_widget.py` |
| 类名 | 一律使用大驼峰，例如 `TaskFlowRunner`、`ConfigService` |
| 公有方法/函数 | 一律使用小写蛇形，例如 `run_tasks_flow`、`build_agent_env_vars` |
| 私有/内部 | 单前导下划线，例如 `_init_agent`、`_build_agent_env_vars` |
| 防止子类冲突 | 双前导下划线，例如 `__private_var` |
| 魔法方法 | 双前导双后缀，例如 `__init__` |
| 信号名 | 默认使用小写蛇形，例如 `task_status_changed`、`config_changed` |
| 变量/属性 | 一律使用小写蛇形，例如 `task_service`、`current_config_id` |
| 常量 | 全大写下划线 `POST_ACTION`, `_CONTROLLER_`, `_RESOURCE_` |
| 翻译 | View/Runner 中使用 `self.tr("...")` 进行 Qt 翻译标记 |
| i18n 键 | interface.json 字符串以 `$` 开头表示需要翻译 |

**统一规则：**
- 除类名外，公开命名默认遵循 Python 标准风格：**模块、函数、方法、变量、属性、信号均使用小写蛇形**。
- 类名、异常名使用 `PascalCase`。
- 常量使用 `UPPER_SNAKE_CASE`。
- 私有/内部成员使用单前导下划线；仅在确有 name mangling 需要时使用双前导下划线。
- 若进行重构或重命名，优先统一以下对象：文件名、模块名、公有方法、信号名、公有变量/属性、公开数据字段。
- 对外兼容层可以暂时保留旧命名别名，但新增代码不得继续扩散非标准命名。

### 5. 异步与线程

- 异步操作使用 `asyncio` + `@asyncify` 装饰器（将同步阻塞操作包装为异步）。
- UI 线程不做阻塞调用；MaaFW SDK 调用都在 `@asyncify` 中执行。
- `QTimer` 用于延迟 UI 操作（如 `QTimer.singleShot`）。
- Agent 子进程使用 `subprocess.Popen`，通过独立线程读取输出。

### 6. 配置管理

- **全局 UI 配置**：`app/common/config.py` 的 `cfg` 对象（基于 qfluentwidgets `QConfig`）。
- **多配置系统**：`config/multi_config.json` → `config/configs/` 目录下的 JSON 文件。
- **Interface 配置**：`interface.json`（PI 协议 v2），由 `InterfaceManager` 单例管理。
- Service 层通过 `ConfigService` 读写配置，不直接操作文件。

### 7. Interface 协议 (PI v2.5.0)

- 项目作为 MaaFramework 的 **Client**，需实现 ProjectInterface 协议。
- `PI_*` 环境变量在 agent 子进程启动时注入（`task_flow.py._build_agent_env_vars`）。
- interface.json 中以 `$` 开头的字符串通过 `I18nService` 翻译。
- 翻译后的 interface 数据通过 `task_service.interface` 访问（已完成 i18n 解析）。
- option 覆盖优先级：`global_option < resource.option < controller.option < task.option`。

---

## 已知技术债务（不要扩大，逐步治理）

以下是项目中的已知架构问题。新增代码**必须避免**引入相同模式：

1. **`signalBus` 在 Core 层的使用**
   - `task_flow.py`、`maafw.py`、`log_processor.py` 直接 import 全局 `signalBus` 发射 UI 信号。
   - 新功能应通过 Runner 自身的 `Signal` → `ServiceCoordinator` 中继。

2. **View 直接修改 Model 属性**
   - 部分 View 直接操作 `task.is_checked` 等属性。
   - 新代码应通过 `ServiceCoordinator` / `OptionService` 的方法。

3. **ServiceCoordinator 职责过多**
   - `core.py` 中的 `ServiceCoordinator` 承担了过多职责。
   - 新增功能尽量放入对应 Service，不要继续向 `ServiceCoordinator` 添加方法。

4. **MainWindow 是超大类**
   - 如需添加全新功能模块，应提取为独立的 Manager 类并在 MainWindow 中组合。

---

## 代码生成检查清单

在生成或修改代码前，请确认：

- [ ] Core 层（`app/core/`）新代码是否 **没有** import `signalBus`？
- [ ] View 层是否通过 Service 方法修改业务状态，而非直接操作 Model？
- [ ] Widget 是否不依赖任何 Service/Core 模块？
- [ ] 新增信号是否放在了正确的信号总线上？
- [ ] 异步阻塞操作是否使用了 `@asyncify`？
- [ ] 用户可见文本是否使用了 `self.tr("...")`？
- [ ] 新增的 interface.json 字段是否遵循 PI v2 协议？
- [ ] 文件/类/方法命名是否符合上述约定？
