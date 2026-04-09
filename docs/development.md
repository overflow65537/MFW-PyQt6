# 开发文档

本文面向项目贡献者，提供本地开发、调试、测试与发布的最小闭环流程。

## 1. 环境要求

- 操作系统：Windows / Linux / macOS
- Python：推荐 3.11+（项目内测试环境为 3.11）
- GUI 依赖：PySide6、PySide6-Fluent-Widgets
- 框架依赖：MaaFw `v5.9.2`（见 `requirements.txt`）

> 说明：若你开发自定义动作/识别器并单独运行，建议遵循 README 中“自定义动作/识别器使用 Python 3.12”的约定。

## 2. 本地启动

在仓库根目录执行。

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\activate
python -m pip install -U pip
python -m pip install -r requirements.txt
python main.py
```

### Linux / macOS (bash/zsh)

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -r requirements.txt
python main.py
```

常用启动参数：

- `-c <config_id>`：启动后切换到指定配置
- `-d`：启动后直接运行任务流
- `-dev`：显示测试页面（开发调试开关）

示例：

```powershell
python main.py -c default -d -dev
```

## 3. 目录结构（开发重点）

```text
app/
  common/          # 全局常量、配置、版本与信号总线
  core/            # 任务运行核心、服务层、流程编排
  view/            # 各页面与组件（PySide6 UI）
  utils/           # 日志、加密、热键、更新等工具模块
  i18n/            # Qt 翻译源文件(.ts)与编译产物(.qm)
docs/              # 项目文档
tests/             # 单元测试
tools/             # 开发/发布辅助脚本
main.py            # 应用入口
```

## 4. 测试与校验

当前仓库使用 `unittest`，在根目录执行：

```powershell
python -m unittest discover -s tests -v
```

现有测试覆盖重点：

- `tests/test_import_path_case_guard.py`
  - 校验 `app/` 下模块路径命名大小写一致性
  - 校验 `app.*` 导入路径在磁盘上可精确解析
- `tests/test_embedded_agent_runtime.py`
  - 校验 embedded agent 转 custom 的构建与加载流程

若出现 `ModuleNotFoundError: jsonc`，通常是当前解释器不是已安装依赖的环境。先确认当前解释器路径，再补装依赖：

```powershell
python -c "import sys; print(sys.executable)"
```

随后执行：

```powershell
python -m pip install -r requirements.txt
```

## 5. 国际化流程

仓库内 i18n 流程由 `tools/` 脚本维护，推荐顺序：

1. 修改源码可翻译字符串（如 `self.tr(...)`）
2. 运行 `python tools/generate_i18n.py` 更新 `.ts`
3. 需要合并旧译文时运行 `python tools/merge_translations.py`
4. 运行 `python tools/lrelease.py` 生成 `.qm`
5. 启动应用验证翻译效果

可选：使用 `python tools/llm_translate_ts.py` 批量机器翻译（需配置 API token）。

## 6. 打包与发布

本地打包脚本：

```powershell
python tools/build.py win x86_64 v1.2.3
```

参数依次为：平台、架构、版本号。详细说明见 `tools/README.md`。

自动构建可参考 `deploy/install.yml` 与 `.github/workflows`。

## 7. 开发约定

- 尽量保持 `app/` 下模块/目录名使用小写 snake_case（仓库有测试守护）
- 变更 UI 文案后同步更新 i18n 资源
- 新增功能优先补充最小可运行测试
- 提交前至少执行一次本地启动和核心测试
