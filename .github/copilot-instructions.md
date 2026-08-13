# MFW-PyQt6 代码规范 — Copilot / AI Agent 指令

> 本文件用于规范 AI 代码生成工具在此项目中的行为，确保生成的代码符合项目的架构约定。

## 项目概述

MFW-ChainFlow Assistant 是一个基于 **PySide6 (Qt6)** 的桌面应用，作为 MaaFramework 的通用 UI Client。
项目遵循 **MVC (Model-View-Controller/Service)** 分层架构，追求 **低耦合、高内聚**。

## 分层架构

```text
app/
├── assets/          # 图标、图片等静态资源
├── builtin_tasks/   # Client 内置任务定义
├── common/          # 共享基础设施：全局 UI 信号、配置、常量
├── core/            # 业务核心（Model + Facade + Service + Runner）
│   ├── item.py      # dataclass Model 与 QObject 事件对象
│   ├── core.py      # ServiceCoordinator — 组装、跨域编排与事件桥接
│   ├── facade/      # View 稳定领域 API（Config/Task/Option/Schedule/Runtime/Interface）
│   ├── service/     # 业务服务、持久化、Interface 与系统计划任务
│   ├── runner/      # 运行时（TaskFlowRunner、MaaFW、MonitorTask）
│   ├── speedrun/    # 速通调度与条件计算
│   └── utils/       # Core 工具（pipeline、热键、资源校验等）
├── i18n/            # Qt Linguist 翻译文件
├── utils/           # 应用级工具（logger、notice、update 等）
├── view/            # 页面、窗口及页面专用组件
└── widget/          # 跨页面复用的纯 UI 组件
```

---

## 核心规则

### 1. 事件通道分层 — 禁止跨层直接耦合

项目存在 **四类事件通道**，分属不同层级：

| 事件通道 | 定义位置 | 作用域 | 允许的发射者 | 允许的监听者 |
| ---------- | ---------- | -------- | -------------- | -------------- |
| `CoreSignalBus` | `app/core/item.py` | Service→Coordinator 的 Core 内部状态事件 | Service / Core 组件 | ServiceCoordinator / Core 适配器 |
| `ViewSignalBus` | `app/core/item.py` | Coordinator→View 单向域通知 | ServiceCoordinator 及其桥接器 | View 层 |
| `RunnerEvents` / Runner Signal | `app/core/item.py` / Runner 类 | Runner→Core 的运行时上报 | Runner / Core 运行时组件 | ServiceCoordinator、TelemetryService / Core 适配器 |
| `signalBus` (全局) | `app/common/signal_bus.py` | View↔View / Core→View 运行时通知 | ServiceCoordinator 适配层 / View 层 / App 级组件 | View 层 / App 级组件 |

**规则：**

- **`app/core/runner/` 中的代码禁止直接持有、import 或 emit `signalBus`（全局信号总线）或 `ViewSignalBus`。**
  - `Runner` UI 事件统一通过 `RunnerEvents` / Runner 自身 `Signal` 上报给 `ServiceCoordinator`，再由其转发到 `signalBus`；遥测事件通过 `RunnerEvents.telemetry` 交给 `TelemetryService`。
- **`app/core/service/` 中的代码禁止直接 import `signalBus`（全局信号总线）。**
  - `signalBus` 的 Core→View 桥接集中在 `ServiceCoordinator` 的适配器中，不得向 Service / Runner 扩散。
  - 新增的 Core 内部通信使用 `CoreSignalBus` 或 `RunnerEvents`；只有 `ServiceCoordinator` 及其桥接器可发射 `ViewSignalBus`。
- `ServiceCoordinator._core_signals` 是 Core 私有总线；View 禁止访问、监听或发射 `CoreSignalBus`。
- View 层通过 `ServiceCoordinator.view_signals` 或 `signalBus` 响应事件，**不得直接调用 Service 内部方法改变业务状态**。
- Runner 日志、回调和运行状态等通知应通过 `RunnerEvents` / Runner 自身 `Signal` 向上层传递，由 `ServiceCoordinator` 或适配层转发给 `signalBus`。
- Core 业务命令必须通过 Facade / `ServiceCoordinator` 方法调用，不得伪装成信号；纯 UI 或 App 级解耦请求可以使用全局 `signalBus`。

### 2. MVC 职责划分

#### Model（`app/core/item.py` 中的 dataclass）

- 当前 Model 是 `TaskItem`、`ConfigItem` 等 dataclass；不要把同文件中的 Qt 事件对象视为 Model。
- 以数据承载为主，优先使用 `@dataclass`。
- 不导入 View、Widget 或 `signalBus`。
- 可包含与自身数据直接相关的序列化、反序列化、兼容迁移、字段规范化和 ID 生成。
- 不包含跨对象业务编排、持久化、UI 状态或 Service 调用。

#### Core 事件对象（`app/core/item.py` 中的 QObject）

- `CoreSignalBus`、`ViewSignalBus`、`RunnerEvents` 继承 `QObject`，是分层事件通道，不是业务数据模型。
- `CoreSignalBus` 只承载 Core 内部状态变化事件，不承载命令型请求。
- `RunnerEvents` 只承载 Runner 运行时事件上报，不直接暴露给 View。
- `ViewSignalBus` 通过 `ServiceCoordinator.view_signals` 暴露，只承载 Coordinator 转发或产生的单向域通知。
- Core 业务命令通过 Facade 或 `ServiceCoordinator` 方法调用，不应伪装成信号。

#### Service（`app/core/service/`）

- 负责业务逻辑、状态管理、配置持久化。
- 通过 `CoreSignalBus` 通知状态变化。
- 不直接操作 UI 组件或 import View/Widget 模块。

#### Facade / ServiceCoordinator（`app/core/facade/` + `app/core/core.py`）

- Facade 是 View 访问单一业务域的稳定公开 API，负责隐藏 Service 内部实现，并对可变返回值提供必要的快照隔离。
- View 优先使用 `ServiceCoordinator.configs`、`tasks`、`options`、`schedules`、`runtime`、`interface_api`。
- 单领域命令遵循 **View → Facade → Service**；`ServiceCoordinator` 负责组装 Service / Facade、跨领域用例与应用生命周期编排、事件桥接，并通过 `view_signals` 暴露 View 域通知。
- 新增单一领域能力时，先实现到对应 Service，再通过对应 Facade 暴露；仅跨领域用例或应用生命周期操作才新增 Coordinator 方法。
- `config_service`、`task_service`、`schedule_service`、`task_runner` 等直接属性仅用于尚未迁移的阶段边界，不是新 View 代码的公开入口。

#### Runner（`app/core/runner/`）

- 负责异步任务执行（MaaFW 控制、任务流编排）。
- 可发射自身定义的 `Signal`（如 `MaaFW.custom_info`, `MaaFW.agent_info`）。
- **不应直接持有、import 或 emit 全局 `signalBus` 或 `ViewSignalBus`**。
- Runner 的 UI 通知统一通过 `RunnerEvents` / Runner Signal → `ServiceCoordinator` → `signalBus`；`RunnerEvents.telemetry` 由 `TelemetryService` 订阅处理。

#### View（`app/view/`）

- 负责 UI 展示与用户交互。
- 单领域读写优先通过 `ServiceCoordinator` 暴露的 Facade，跨领域操作通过 `ServiceCoordinator` 方法。
- 监听 `ServiceCoordinator.view_signals` / `signalBus` 获取状态更新。
- **不得访问、监听或发射 `CoreSignalBus`，也不得使用已废弃的 `signal_bus` / `signals` 别名。**
- **不应直接修改 `TaskItem.is_checked` 等 Model 属性**，应通过 Facade / `ServiceCoordinator` 命令。
- 不直接访问 `task_service`、`config_service`、`option_service` 等 Service 内部实现；现存阶段边界除外且不得扩散。
- **不应包含业务逻辑**（如 pipeline override 计算、资源路径拼接）。

#### 通用 Widget（`app/widget/`）

- 可复用的纯 UI 组件。
- 不导入 Service、ServiceCoordinator 或 Core 模块。
- 通过自身 Signal/Slot 与父 View 通信。
- `app/view/**/components/`、`app/view/**/widget/` 中的页面专用组件属于 View 层，可使用 Facade / `ServiceCoordinator` 公开 API，但仍不得访问 Service 内部实现或承载业务逻辑。

### 3. 数据流方向

```text
单领域命令：用户操作 → View → Facade → Service
跨领域命令：用户操作 → View → ServiceCoordinator → 多个 Service / Facade

Service 状态：Service → CoreSignalBus → ServiceCoordinator/Core UI Bridge
                                               ↓
View ← ServiceCoordinator.view_signals（ViewSignalBus）

Runner(MaaFW/TaskFlow) → RunnerEvents/Runner Signal → ServiceCoordinator → signalBus → View
Runner 遥测 → RunnerEvents.telemetry → TelemetryService
ScheduleService.schedules_changed → ServiceCoordinator/Core UI Bridge → ViewSignalBus → View
```

**禁止方向：**

- View → 直接修改 Model 属性（跳过 Service）
- View → 直接监听或 emit CoreSignalBus（禁止）
- View → 新增代码直接调用 Service 内部 API（绕过 Facade / Coordinator）
- Runner → 直接持有或 emit `signalBus` / `ViewSignalBus`（禁止）
- `app/widget/` → 直接 import Service / Core
- Service → 直接 import View / Widget

### 4. 命名与编码约定

| 分类 | 约定 |
| ------ | ------ |
| 文件名 / 模块名 | 一律使用小写蛇形，例如 `config_service.py`、`task_interface_logic.py`、`list_widget.py` |
| 类名 | 一律使用大驼峰，例如 `TaskFlowRunner`、`ConfigService` |
| 公有方法/函数 | 一律使用小写蛇形，例如 `run_tasks_flow`、`build_agent_env_vars` |
| 私有/内部 | 单前导下划线，例如 `_init_agent`、`_build_agent_env_vars` |
| 防止子类冲突 | 双前导下划线，例如 `__private_var` |
| 魔法方法 | 双前导双后缀，例如 `__init__` |
| 信号名 | 默认使用小写蛇形，例如 `task_status_changed`、`config_changed` |
| 变量/属性 | 一律使用小写蛇形，例如 `task_service`、`current_config_id` |
| 常量 | 全大写下划线，例如 `POST_ACTION`、`DEFAULT_TIMEOUT` |
| 翻译 | View/Runner 中使用 `self.tr("...")` 进行 Qt 翻译标记 |
| i18n 键 | interface.json 字符串以 `$` 开头表示需要翻译 |

**统一规则：**

- 除类名外，公开命名默认遵循 Python 标准风格：**模块、函数、方法、变量、属性、信号均使用小写蛇形**。
- 类名、异常名使用 `PascalCase`。
- 常量使用 `UPPER_SNAKE_CASE`。
- `_CONTROLLER_`、`_RESOURCE_` 等既有协议哨兵是兼容性例外；新增普通常量不得仿照其首尾下划线命名。
- 私有/内部成员使用单前导下划线；仅在确有 name mangling 需要时使用双前导下划线。
- 若进行重构或重命名，优先统一以下对象：文件名、模块名、公有方法、信号名、公有变量/属性、公开数据字段。
- 对外兼容层可以暂时保留旧命名别名，但新增代码不得继续扩散非标准命名。

### 5. 异步与线程

- Qt 主循环由 `qasync.QEventLoop` 与 `asyncio` 集成；原生异步 API 直接 `async` / `await`，不得为了形式统一额外套用 `@asyncify`。
- `@asyncify` 或 `asyncio.to_thread()` 仅用于确认可安全跨线程的同步阻塞 I/O、同步 MaaFW SDK 调用或短时等待；不得在线程池中直接操作具有 Qt 线程亲和性的 `QObject` / Widget。
- 可异步控制的子进程使用 `asyncio.create_subprocess_exec()` 并异步读取/等待；仅在既有同步库或平台 API 无异步接口时，才用后台线程封装 `subprocess.Popen` / `wait`。
- 长生命周期、需要 Qt Signal/Slot 或专属事件循环的后台工作使用 `QThread`（或 worker-object + `QThread`），并通过 queued connection 回到 UI 线程；不要把 `QThread` 当作一次性延迟工具。
- CPU 密集任务使用进程方案；文件、网络、子进程等待、MaaFW SDK 等阻塞操作不得占用 UI 线程。
- `QTimer` 用于延迟 UI 操作（如 `QTimer.singleShot`）。

### 6. 配置管理

- **全局 UI 配置**：`app/common/config.py` 的 `cfg` 对象（基于 qfluentwidgets `QConfig`）。
- **多配置系统**：`config/multi_config.json` → `config/configs/` 目录下的 JSON 文件。
- **Interface 配置**：`interface.json`（PI v2 大版本；当前 Client 能力对齐 v2.9.1），由 `InterfaceManager` 单例管理。
- 多配置域通过 `ConfigService` / Repository 读写，不在 View 或其他 Service 中散落直接文件操作；具有独立存储职责的专用 Repository / Manager 除外。

### 7. Interface 协议（PI v2；当前能力 v2.9.1）

- 项目作为 MaaFramework 的 **Client**，需实现 ProjectInterface 协议。
- `interface_version: 2` 表示 JSON 结构主版本；当前实现能力对齐 PI 语义版本 **v2.9.1**，两者不要混淆。
- `PI_*` 环境变量在 agent 子进程启动时注入（`task_flow.py._build_agent_env_vars`）。
- interface.json 中以 `$` 开头的字符串通过 `I18nService` 翻译。
- View 通过 `ServiceCoordinator.interface_api.data` 获取 interface 数据；Core 内部由 `InterfaceManager` / 对应 Service 使用。
- `InterfaceManager` 将主文件及 import 中的 `global_option` 合并去重后转换为 runtime `setting` 分区；运行期不再单独消费 `global_option`。
- Setting UI 的当前值经 `OptionFacade` / `ConfigFacade` 写入当前配置的 `Resource.task_option.setting_options`；历史根层 `global_options`、Resource 内嵌 `global_options`、旧 Setting 任务及扁平值仅用于迁移。
- pipeline override 按低到高依次合并：`setting_options`（PI 输入来源为 `global_option` / `setting`）→ `resource.option` → `controller.option` → `task.option`，后者覆盖前者；不满足 controller/resource 条件的 option 先过滤。
- 遥测生命周期事件使用 `RunnerEvents.telemetry → TelemetryService`；节点回调也由 `TelemetryService` 按 PI v2.9.1 `focus.trace` 规则处理。
- 调度变更使用 `ScheduleService.schedules_changed → ServiceCoordinator/Core UI Bridge → ViewSignalBus.schedules_changed → View`。

---

## 已知技术债务（不要扩大，逐步治理）

以下是项目中的已知架构问题。新增代码**必须避免**引入相同模式：

- **ServiceCoordinator 职责过多**
  `core.py` 中的 `ServiceCoordinator` 承担了过多职责。
  新增单领域功能放入对应 Service，并经对应 Facade 暴露；只有跨领域编排或应用生命周期操作才进入 `ServiceCoordinator`。

- **MainWindow 是超大类**
  如需添加全新功能模块，应提取为独立的 Manager 类并在 MainWindow 中组合。

---

## 代码生成检查清单

在生成或修改代码前，请确认：

- [ ] Runner 层（`app/core/runner/`）代码是否 **没有** 直接持有/import/emit `signalBus` 或 `ViewSignalBus`？
- [ ] Service 层（`app/core/service/`）新代码是否 **没有** import `signalBus`？
- [ ] View 层是否通过 Facade / `ServiceCoordinator` 命令修改业务状态，而非直接操作 Model 或 Service？
- [ ] View 层是否只监听 `view_signals` / `signalBus`，且没有访问或发射 `CoreSignalBus`？
- [ ] View 层是否避免直接访问 `task_service`、`config_service`、`option_service` 内部实现？
- [ ] `app/widget/` 通用组件是否不依赖任何 Service/Core 模块？
- [ ] 新增事件是否放在了正确的事件通道，且 Core 业务命令没有伪装成信号？
- [ ] 同步阻塞操作是否在确认线程安全后使用 `@asyncify` 或其他合适的后台执行方案？
- [ ] 用户可见文本是否使用了 `self.tr("...")`？
- [ ] 新增的 interface.json 字段是否遵循 PI v2（当前能力 v2.9.1）协议？
- [ ] 文件/类/方法命名是否符合上述约定？
