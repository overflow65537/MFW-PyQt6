# TaskFlow、监控、日志与 IPC 重构计划书

> 状态：实施中（阶段 1～4 主体已完成，阶段 5 待稳定后执行）  
> 编写日期：2026-08-13  
> 本次性质：结构重构，不实现多实例运行，不改变现有用户行为

## 0. 实施进度（2026-08-13）

当前工作区已经完成：

- 配置级 `RuntimeContext`、日志/监控状态隔离和活动 Context UI bridge；
- 统一 IPC 协议、换行分帧、payload 限制及新旧协议兼容；
- `LocalIpcClient`、`LocalIpcServer` 和单一 command handler；
- `AppCommandDispatcher`、FIFO command queue、关闭状态和六类命令；
- CLI direct-run 与已有实例复用统一进入应用命令调度层；
- 启动参数兼容矩阵的纯决策层及自动化测试。

实施时确认了一处需要明确的兼容边界：

- 外部 IPC 在 MainWindow 尚未就绪时，`run/switch_config/stop` 返回
  `busy/application_not_ready`，保持旧版复用运行行为；
- `activate/shutdown` 可以进入启动 pending queue；
- 本进程 direct-run 使用 `submit_startup()`，允许在组装阶段进入 pending queue。

阶段 5 的旧字节协议清理仍按原计划延后，待新协议稳定并确认不存在旧外部启动器依赖后再执行。

## 1. 背景

项目后续计划支持多个配置同时运行，并分别连接不同控制器、执行不同任务。为了实现这一目标，不同配置对应的运行状态必须彼此隔离，包括：

- TaskFlow 运行状态；
- MaaFW/控制器运行状态；
- 监控画面与识别区域；
- 运行日志；
- Runner 事件；
- 启停状态与当前任务信息。

当前项目已经建立了按配置持有的 `RuntimeContext`，将 TaskFlow、监控状态和日志存储放入同一运行时对象。下一步需要整理 IPC 和应用启动入口，避免业务命令继续散落在 `single_instance.py` 与 `main.py` 中。

现有 IPC 可以工作，但扩展成本较高。每增加一个命令，目前通常需要同时增加：

1. 字节命令常量；
2. 服务端解析分支；
3. callback 字段；
4. callback setter；
5. 客户端 request 方法；
6. `main.py` 业务处理函数；
7. 对应的 pending/in-progress 状态。

如果继续直接加入“切换配置”“停止任务”“查询状态”等命令，启动文件和 IPC 传输层会持续膨胀，不利于后续多实例扩展。

---

## 2. 本次重构目标

### 2.1 运行时对象目标

确认并稳定以下所有权关系：

```text
config_id
└─ RuntimeContext
   ├─ RunnerEvents
   ├─ TaskFlowRunner
   ├─ MonitorTask
   ├─ RuntimeLogStore
   ├─ RuntimeMonitorState
   └─ CallbackLogProcessor
```

切换当前配置时，UI 应切换到目标配置对应的 `RuntimeContext`，正确显示该配置的：

- 日志历史；
- 最新监控画面；
- ROI/识别区域；
- TaskFlow 状态；
- 当前任务状态。

配置之间的数据不得互相覆盖、清空或串流。

### 2.2 IPC 目标

将 IPC 收敛为统一命令入口，对外提供少量稳定接口：

```python
client.activate()
client.switch_config(config_id)
client.run(config_id=None, force_restart=False)
client.stop(config_id=None)
client.shutdown(reason="user")
client.status()
```

底层统一使用：

```python
client.send_command(request)
server.set_command_handler(handler)
```

IPC 传输层不再直接处理配置、TaskFlow、窗口和关闭流程等业务。

### 2.3 启动入口目标

命令行参数启动和已有实例复用最终进入同一应用命令调度层，避免维护两套运行逻辑：

```text
命令行参数 ─┐
            ├─> AppCommand ─> AppCommandDispatcher
IPC 请求 ───┘
```

### 2.4 未来兼容目标

本次仍然只允许一个应用进程、一个活动运行任务，但数据结构和 IPC 协议应允许未来扩展为：

```text
一个应用进程
├─ RuntimeContext(config-a) -> controller-a
├─ RuntimeContext(config-b) -> controller-b
└─ RuntimeContext(config-c) -> controller-c
```

本次不得提前实现并发运行多个配置。

---

## 3. 非目标

本次明确不包含：

- 不实现多个配置同时运行；
- 不实现多个控制器同时连接；
- 不修改 TaskFlow 的业务执行规则；
- 不修改任务配置文件格式；
- 不增加跨机器 IPC；
- 不引入 HTTP/WebSocket 服务；
- 不重写更新器；
- 不取消单应用进程限制；
- 不改变现有 `force_restart` 与 `reuse_existing` 的用户可见行为；
- 不让 View 直接依赖 Runner 或 Service 内部实现。

---

## 4. 核心设计原则

### 4.1 配置数据与运行时状态分离

持久化配置对象只保存配置数据，不直接持有 socket、窗口或应用生命周期对象。

`RuntimeContext` 负责某个配置的非持久化运行时状态。它由 `ServiceCoordinator` 创建、缓存和管理。

### 4.2 IPC 与业务分离

`single_instance.py` 只负责：

- 单实例锁；
- server name；
- 本地 socket 的启动与关闭；
- 请求和响应的传输；
- 旧实例检测与必要的进程恢复能力。

它不负责：

- 判断配置是否存在；
- 启停 TaskFlow；
- 切换 UI 配置；
- 操作 MainWindow；
- 决定 `force_restart` 与 `reuse_existing` 的组合策略。

### 4.3 所有状态变更命令串行执行

以下命令会修改共享应用状态，必须串行：

- `switch_config`；
- `run`；
- `stop`；
- `shutdown`。

第一阶段使用单一 FIFO 命令队列，避免多个 `asyncio.ensure_future()` 之间产生竞态。

### 4.4 “请求已接收”不等于“任务已完成”

IPC 是控制面，不等待整个 TaskFlow 结束。

- `ok`：同步操作已经完成；
- `accepted`：异步命令已校验并进入队列；
- `busy`：当前状态不允许接受；
- `invalid`：请求格式或参数无效；
- `not_found`：目标配置不存在；
- `error`：内部执行错误。

### 4.5 本次保持行为兼容

本次是结构重构，不趁机修改启动参数的既有行为。参数语义是否收窄，应在 IPC 重构稳定后作为独立变更处理。

---

## 5. 目标架构

```text
┌─────────────────────────────────────────┐
│                 调用入口                 │
│  CLI / 系统计划任务 / 第二次启动 / 更新器 │
└───────────────────┬─────────────────────┘
                    │
                    ▼
          AppCommand / AppCommandResponse
                    │
        ┌───────────┴───────────┐
        │                       │
        ▼                       ▼
  Local IPC Client        本进程直接提交
        │                       │
        ▼                       │
  QLocalSocket/Server           │
        │                       │
        └───────────┬───────────┘
                    ▼
          AppCommandDispatcher
          ├─ 启动阶段 pending queue
          ├─ 运行阶段 command queue
          ├─ MainWindow 控制
          └─ ServiceCoordinator 调用
                    │
                    ▼
          ServiceCoordinator
          ├─ ConfigService
          ├─ active config
          └─ RuntimeContext registry
                    │
          ┌─────────┴─────────┐
          ▼                   ▼
 RuntimeContext A       RuntimeContext B
 ├─ TaskFlow            ├─ TaskFlow
 ├─ Monitor             ├─ Monitor
 └─ Logs                └─ Logs
```

---

## 6. RuntimeContext 设计

### 6.1 所有权

`ServiceCoordinator` 继续维护：

```python
_runtime_contexts: dict[str, RuntimeContext]
_active_runtime_context: RuntimeContext
```

核心入口：

```python
def get_runtime_context(config_id: str | None = None) -> RuntimeContext

def select_config(config_id: str) -> bool

async def run_configuration(
    config_id: str,
    *,
    clear_logs: bool = False,
) -> bool
```

### 6.2 切换配置

切换配置只改变：

- 当前活动配置；
- UI 绑定的 RuntimeContext；
- 当前配置对应的任务/选项显示。

切换配置不得：

- 清空其他配置日志；
- 清空其他配置监控状态；
- 把其他配置事件重新绑定到当前配置；
- 销毁仍可能需要保留状态的 RuntimeContext。

### 6.3 UI 桥接

Runner 层继续通过 `RunnerEvents` 发出领域事件，不依赖全局 `signalBus`。

`ServiceCoordinator` 负责把活动 RuntimeContext 的事件桥接给 View。切换 RuntimeContext 时应：

1. 断开旧 Context 的 UI bridge；
2. 连接新 Context 的 UI bridge；
3. 主动回放新 Context 已保存的日志/监控状态；
4. 避免旧 Context 后续事件更新当前 UI。

### 6.4 本阶段运行限制

尽管 `_runtime_contexts` 中可以存在多个 RuntimeContext，本阶段只允许一个 TaskFlow 运行。该限制放在应用命令/协调层，不通过共享 Runner 对象隐式实现。

---

## 7. IPC 协议设计

### 7.1 请求模型

建议新增：

```python
class IpcCommand(StrEnum):
    ACTIVATE = "activate"
    SWITCH_CONFIG = "switch_config"
    RUN = "run"
    STOP = "stop"
    SHUTDOWN = "shutdown"
    STATUS = "status"
```

请求：

```json
{
  "version": 1,
  "request_id": "uuid",
  "command": "run",
  "params": {
    "config_id": "config-a",
    "force_restart": false
  }
}
```

响应：

```json
{
  "version": 1,
  "request_id": "uuid",
  "status": "accepted",
  "code": "ok",
  "message": "",
  "data": {}
}
```

### 7.2 响应状态

```python
class IpcStatus(StrEnum):
    OK = "ok"
    ACCEPTED = "accepted"
    BUSY = "busy"
    INVALID = "invalid"
    NOT_FOUND = "not_found"
    ERROR = "error"
```

### 7.3 分帧

不再假设一次 `readyRead` 就包含完整请求。

第一阶段采用“一条连接一个请求，以换行结束”的分帧方式：

```text
<json>\n
```

同时增加：

```python
MAX_IPC_PAYLOAD = 64 * 1024
```

超过限制直接返回 `invalid/payload_too_large` 并断开连接。

### 7.4 未知命令

未知命令必须返回 `invalid/unknown_command`，不得像当前协议一样退化为窗口激活。

### 7.5 版本

第一版使用：

```json
{"version": 1}
```

协议版本不支持时返回：

```json
{
  "status": "invalid",
  "code": "unsupported_version"
}
```

---

## 8. 应用命令语义

### 8.1 `activate`

用途：显示并前置已有窗口。

行为：

- 隐藏时显示；
- 最小化时恢复；
- 调用 `raise_()` 与 `activateWindow()`；
- Windows 下保留必要的前台窗口兼容处理。

响应：同步完成后返回 `ok`。

### 8.2 `switch_config`

参数：

```json
{"config_id": "config-a"}
```

行为：

- 校验配置存在；
- 调用 `ServiceCoordinator.select_config()`；
- 切换 UI 到对应日志和监控状态；
- 不运行任务。

响应：校验通过并入队后返回 `accepted`；同步校验失败返回 `not_found` 或
`invalid`。执行结果通过日志和后续 `status()` 观察。

### 8.3 `run`

参数：

```json
{
  "config_id": "config-a",
  "force_restart": false
}
```

规则：

- `config_id` 存在：原子地选择并运行该配置；
- `config_id` 为空：运行当前活动配置；
- 不能要求客户端先 `switch_config` 再 `run`，否则两条请求之间可能发生竞态；
- 本阶段仍然只允许一个 TaskFlow 运行。

`force_restart` 在该命令中的使用仅用于 `reuse_existing + direct_run + force_restart` 的停止后重跑行为，不新增 `force_start`、`replace_running_task` 等第二套公开参数。

### 8.4 `stop`

参数：

```json
{"config_id": null}
```

本阶段：

- 不指定 ID：停止当前运行任务；
- 指定 ID：校验对应 RuntimeContext；当前仍只允许停止唯一运行任务；
- 已经停止时仍可接受，执行保持幂等。

响应：校验通过并入队后返回 `accepted`。

未来多实例时可自然扩展为停止指定配置，不修改协议。

### 8.5 `shutdown`

参数：

```json
{"reason": "restart"}
```

行为：

1. 标记应用正在关闭；
2. 拒绝后续 `run/switch_config`；
3. 停止当前任务；
4. 关闭遥测及其他应用资源；
5. 允许窗口关闭；
6. 退出进程。

响应：请求入队后返回 `accepted`。

`reason` 是内部上下文，不是新的用户启动参数。可选值包括：

- `user`；
- `restart`；
- `update`；
- `external`。

### 8.6 `status`

建议返回：

```json
{
  "ready": true,
  "active_config_id": "config-a",
  "running": true,
  "running_config_ids": ["config-a"],
  "shutting_down": false
}
```

本阶段 `running_config_ids` 最多只有一个元素，但使用数组可避免未来协议破坏性升级。

---

## 9. `force_restart` 与 `reuse_existing` 规则

### 9.1 启动语义矩阵

`reuse_existing` 只决定是否优先复用已有进程，不再隐含“运行任务”。是否运行任务始终由 `direct_run` 决定。

| 已有实例 | `reuse_existing` | `direct_run` | `force_restart` | 行为 |
|---|---:|---:|---:|---|
| 否 | 任意 | 否 | 任意 | 当前进程正常启动，不运行任务 |
| 否 | 任意 | 是 | 任意 | 当前进程正常启动并运行任务 |
| 是 | 否 | 任意 | 否 | 普通重复启动流程，优先激活旧实例 |
| 是 | 否 | 否 | 是 | 旧实例停止任务并退出；新进程启动后不运行任务 |
| 是 | 否 | 是 | 是 | 旧实例停止任务并退出；新进程启动后运行任务 |
| 是 | 是 | 否 | 任意 | 有 `config_id` 时仅切换已有实例的配置；否则仅激活窗口；不运行任务 |
| 是 | 是 | 是 | 否 | 复用旧实例运行目标配置；旧实例忙时返回 `busy` |
| 是 | 是 | 是 | 是 | 复用优先；旧实例停止当前任务后运行目标配置，不关闭进程 |

### 9.2 决策位置

组合决策只放在新进程的启动策略层：

```python
if existing_instance:
    if options.reuse_existing:
        if options.direct_run:
            send_run(
                config_id=options.config_id,
                force_restart=options.force_restart,
            )
        elif options.config_id:
            send_switch_config(config_id=options.config_id)
        else:
            send_activate()
    elif options.force_restart:
        send_shutdown(reason="restart")
        wait_for_instance_available()
        continue_startup()
    else:
        send_activate()
```

关键规则：

```text
reuse_existing 决定复用哪个进程；direct_run 决定是否运行任务。
```

因此 `reuse_existing + force_restart` 仍不会关闭已有实例；但只有再显式指定 `direct_run` 时，`force_restart` 才会表示“停止当前任务后重新运行”。

### 9.3 能力保留

保留“关闭旧进程，由新进程接管”的能力，原因包括：

- 原生控制器或 MaaFW 状态异常恢复；
- 启动参数、Qt 参数或环境变量发生变化；
- 更新程序需要释放文件和原生资源；
- 外部计划任务要求全新进程状态；
- 旧进程长时间运行后需要彻底重置。

### 9.4 后续可选语义清理

在本次重构稳定后，可另开变更评估是否将 `force_restart` 收窄为纯进程级参数。该变更涉及用户行为和计划任务兼容，不纳入本次重构。

---

## 10. AppCommandDispatcher

建议新增：

```text
app/core/service/app_command_dispatcher.py
```

职责：

- 持有 MainWindow/ServiceCoordinator 的可用状态；
- 校验命令业务参数；
- 管理启动阶段 pending queue；
- 管理运行阶段 FIFO command queue；
- 调用 `ServiceCoordinator`；
- 执行窗口激活和应用关闭；
- 生成统一响应；
- 记录命令生命周期日志。

建议接口：

```python
class AppCommandDispatcher:
    def submit(self, request: IpcRequest) -> IpcResponse:
        ...

    def attach_window(self, window: MainWindow) -> None:
        ...

    async def start(self) -> None:
        ...

    async def close(self) -> None:
        ...
```

### 10.1 启动阶段 pending queue

替换 `main.py` 当前多个字典：

```python
pending_force_shutdown
pending_activation
pending_reuse_request
reuse_request_in_progress
```

统一为：

```python
_pending_commands: deque[IpcRequest]
```

外部请求仅暂存启动期 `activate/shutdown`；本进程启动命令可通过
`submit_startup()` 暂存。外部 `run/switch_config/stop` 在应用未就绪时返回
`busy/application_not_ready`，避免改变既有复用启动语义。

窗口和 Coordinator 就绪后：

```python
dispatcher.attach_window(window)
dispatcher.drain_pending_commands()
```

### 10.2 运行阶段 command queue

```python
_command_queue: asyncio.Queue[IpcRequest]
```

由一个 worker 串行消费。

`shutdown` 被接受后：

- 设置 `_shutting_down=True`；
- 不再接受新的状态变更命令；
- 队列中尚未执行的普通运行命令可按明确规则拒绝或丢弃并记录日志。

### 10.3 错误隔离

某条命令执行失败不得终止 worker。每条命令独立捕获异常并记录：

- `request_id`；
- `command`；
- `config_id`；
- 错误堆栈。

---

## 11. 推荐文件结构

```text
app/
├─ ipc/
│  ├─ __init__.py
│  ├─ protocol.py
│  ├─ local_client.py
│  └─ local_server.py
├─ core/
│  ├─ runner/
│  │  └─ runtime_context.py
│  └─ service/
│     └─ app_command_dispatcher.py
└─ utils/
   └─ single_instance.py
```

### 11.1 `protocol.py`

负责：

- command/status 枚举；
- request/response 数据模型；
- JSON 编解码；
- schema/version 校验；
- payload 大小限制。

### 11.2 `local_client.py`

负责：

- 连接 `QLocalServer`；
- 发送一条请求；
- 等待并解析响应；
- 暴露便利接口。

### 11.3 `local_server.py`

负责：

- 启动/关闭 `QLocalServer`；
- socket 缓冲和分帧；
- 调用单一 command handler；
- 写回响应。

### 11.4 `single_instance.py`

保留：

- `_SingleInstanceLock`；
- server name 计算；
- 进程匹配与旧实例恢复；
- 对 `LocalIpcClient/LocalIpcServer` 的组合管理；
- 旧接口兼容包装。

---

## 12. 渐进迁移步骤

### 阶段 0：固定现有行为

目的：在重构前用测试锁定现有语义。

工作：

- 增加启动策略组合测试；
- 增加复用运行 busy/force 行为测试；
- 增加旧实例 shutdown 后新实例等待锁释放测试；
- 固定无效 config ID 的返回行为；
- 固定 `reuse_existing` 优先级。

完成标准：现有行为全部由自动化测试描述。

### 阶段 1：建立协议模型

工作：

- 新建 `app/ipc/protocol.py`；
- 实现 request/response JSON 编解码；
- 增加版本、未知命令、缺失字段和 payload 限制测试；
- 暂不接入实际启动流程。

完成标准：纯协议测试通过，不影响现有 IPC。

### 阶段 2：统一传输层

工作：

- 新建 `LocalIpcServer` 与 `LocalIpcClient`；
- 服务端只保留一个 `set_command_handler()`；
- 使用换行分帧；
- 每个连接只处理一个请求；
- 返回统一 JSON 响应。

兼容：

- 暂时识别旧 `activate`、`shutdown`、`run-config:` 请求；
- 将旧请求转换成新的 `IpcRequest`；
- 旧客户端公共方法内部改为调用新 client。

完成标准：新旧请求均可控制当前实例。

### 阶段 3：引入 AppCommandDispatcher

工作：

- 新建 dispatcher；
- 实现六个命令；
- 引入 pending queue 和 command queue；
- 把窗口激活、运行配置、停止任务、优雅关闭逻辑从 `main.py` 移入 dispatcher；
- 删除 `main.py` 中多个 pending 字典和 in-progress 标记。

完成标准：`main.py` 只负责组装应用对象、注册 dispatcher 和启动事件循环。

### 阶段 4：统一 CLI 与 IPC 路径

工作：

- 将启动参数解析结果转换为应用命令或启动决策；
- 新实例启动后的 direct-run 通过 dispatcher 执行；
- 已有实例复用时根据 `direct_run/config_id` 选择 run、switch_config 或 activate；
- 保留 `reuse_existing` 优先于进程重启的规则，并由 `direct_run` 独立控制任务执行。

完成标准：同一运行请求在新实例和复用实例中具有一致的 config 校验、日志和返回语义。

### 阶段 5：清理旧 API

稳定一段时间后：

- 删除多个 callback setter；
- 删除旧命令解析分支；
- 删除旧 bytes 响应常量依赖；
- 更新 README、CLI 帮助和开发文档；
- 如需兼容旧外部启动器，可延后此阶段。

完成标准：IPC 只有统一 request/response 模型和单一 handler。

---

## 13. 测试计划

### 13.1 RuntimeContext 隔离

- 不同配置拥有不同 RunnerEvents；
- 不同配置拥有不同 TaskFlowRunner；
- 日志写入不跨配置；
- 清空日志不影响其他配置；
- 监控帧不跨配置；
- ROI 更新/清理不跨配置；
- 切换配置后 UI 回放目标 Context 状态；
- 旧 Context 事件不再更新当前 UI；
- 删除配置时正确释放对应 Context。

### 13.2 IPC 协议

- request/response 往返编码；
- Unicode config ID；
- 未知 command；
- 不支持的 version；
- 缺失 params；
- 无效 JSON；
- 半包与分包；
- 超大 payload；
- response request_id 对应。

### 13.3 命令处理

- activate；
- switch_config 成功与不存在；
- run 当前配置；
- run 指定配置；
- run 的原子切换；
- busy 时拒绝普通复用；
- `reuse_existing + direct_run + force_restart` 时先停止后运行；
- stop 幂等；
- shutdown 先停止任务再退出；
- shutdown 后拒绝新运行请求；
- status 返回当前配置与运行状态。

### 13.4 启动阶段

- 窗口创建前收到 activate；
- 窗口创建前收到外部 run 时返回 busy；
- 本进程 startup run 可进入 pending queue；
- 窗口创建前收到 shutdown；
- pending 命令按顺序执行；
- shutdown 优先/终止后续命令的规则；
- dispatcher attach 后只消费一次 pending 命令。

### 13.5 CLI 组合

覆盖第 9.1 节完整矩阵，特别是：

```text
reuse_existing=True + direct_run=True + force_restart=True
```

必须验证：

- 不关闭已有进程；
- 停止当前任务；
- 运行目标配置；
- 新进程正常退出。

---

## 14. 日志与可观测性

每个 IPC 请求建议记录：

```text
IPC received request_id=... command=run config_id=...
IPC accepted request_id=...
IPC completed request_id=...
IPC rejected request_id=... status=busy code=task_running
IPC failed request_id=...
```

应用日志与运行日志需要区分：

- IPC/启动/进程生命周期日志：写入应用全局 debug 日志；
- TaskFlow 日志：写入目标 `RuntimeContext.logs`；
- 不把 IPC 自身日志混入某个配置的运行日志。

---

## 15. 风险与处理

### 15.1 Qt socket 半包

风险：`readyRead` 不保证完整 JSON。  
处理：缓冲到换行分隔符，增加 payload 上限。

### 15.2 异步命令响应误解

风险：客户端把 `accepted` 当作 TaskFlow 已运行成功。  
处理：文档明确 accepted 只代表入队；需要运行状态时调用 `status()`。

### 15.3 启动阶段命令丢失

风险：MainWindow 尚未创建。  
处理：dispatcher 统一 pending queue，不再分散保存状态。

### 15.4 重构导致计划任务行为变化

风险：`force_start/reuse_existing` 已被计划任务配置使用。  
处理：计划任务始终显式携带 `direct_run`，因此复用运行行为不变；同时为“仅复用、不运行”增加单独测试。

### 15.5 多个状态变更请求竞态

风险：同时 run/stop/switch。  
处理：单一 FIFO worker 串行执行。

### 15.6 View/Core 边界破坏

风险：为了操作窗口状态让 Service/Runner 反向依赖 View。  
处理：窗口生命周期只由 dispatcher 持有；Runner 不导入 View，View 不直接导入 Runner/Service。

---

## 16. 验收标准

### 16.1 结构验收

- `RuntimeContext` 持有配置级 TaskFlow、监控和日志；
- IPC server 只有一个 command handler；
- `main.py` 不再维护多个 IPC callback 和 pending 字典；
- IPC 传输层不导入 `MainWindow`、`ServiceCoordinator` 或 Runner；
- Runner 不依赖全局 `signalBus`；
- View 继续通过 Facade/Coordinator 访问 Core。

### 16.2 行为验收

- 切换配置能显示对应日志和监控；
- 不同配置日志/监控互不影响；
- IPC 可激活、切换、运行、停止、关闭和查询状态；
- 运行指定配置是单条原子命令；
- `reuse_existing` 不隐式启动任务，任务执行只由 `direct_run` 触发；
- 强制重启时旧实例优雅停止后，新实例才能取得锁并启动；
- 复用优先时旧实例不会被关闭。

### 16.3 质量验收

使用项目 PySide6 环境执行：

```powershell
D:\AnaConda\envs\MFW\python.exe -m unittest discover -s tests
git diff --check
```

要求：

- 全部测试通过；
- 无 whitespace 错误；
- 无新增跨层依赖违规；
- 无遗留未消费异步任务警告；
- 新协议与兼容协议均有测试覆盖。

---

## 17. 推荐实施顺序总结

```text
固定现有行为测试
    ↓
新增 IPC 协议模型
    ↓
新增统一 Client/Server
    ↓
兼容旧 IPC 请求
    ↓
新增 AppCommandDispatcher
    ↓
迁移 main.py 业务处理
    ↓
统一 CLI 与 IPC 运行入口
    ↓
补齐隔离、并发和启动阶段测试
    ↓
稳定后删除旧 API
```

本次重构完成后，项目仍然是单应用进程、单任务运行模式，但将具备清晰的三层边界：

```text
RuntimeContext：配置级运行状态隔离
ServiceCoordinator：配置与 RuntimeContext 管理
AppCommandDispatcher：应用控制命令调度
IPC：纯命令传输
```

未来实现多实例运行时，主要修改 `ServiceCoordinator/AppCommandDispatcher` 如何按 `config_id` 定位、启动和停止 RuntimeContext；IPC 协议、日志/监控隔离结构以及外部调用接口无需推翻重做。
