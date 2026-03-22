# tools 目录说明

本目录存放开发与发布辅助脚本。**建议在仓库根目录下**执行下列命令（部分脚本会自动切换到根目录；若在别处执行，请确保能解析到 `main.py` 所在的项目根）。

---

## `generate_i18n.py`

从 `app/` 下的 Python 源码提取可翻译字符串，生成/更新 Qt Linguist 的 `.ts` 文件。

**依赖**：已安装 PySide6，且 PATH 或 PySide6 安装目录中可用 **`pylupdate6`**（脚本也会尝试 `pyside6-lupdate`、`lupdate`）。

**用法**：

```bash
python tools/generate_i18n.py
```

可选：第一个参数为 `pylupdate6` 可执行文件的完整路径（或包含该 exe 的目录）。

**输出**：在 `app/i18n/` 下更新 `i18n.zh_CN.ts`、`i18n.zh_TW.ts`、`i18n.ja_JP.ts` 等（与脚本内列表一致）。

---

## `lrelease.py`

将 `app/i18n/*.ts` 编译为运行时使用的 **`.qm`** 文件（与 `.ts` 同名）。

**依赖**：PySide6 自带的 **`lrelease`**（或 `pyside6-lrelease`）。

**用法**：

```bash
python tools/lrelease.py
```

脚本会将工作目录设为项目根，并扫描 `app/i18n` 下所有 `.ts` 逐个编译。

**可选配置**：若存在 `tools/i18n.json`，可指定 `lrelease` 路径，例如：

```json
{ "lrelease": "C:\\path\\to\\lrelease.exe" }
```

---

## `merge_translations.py`

在更新翻译模板后，把**旧 `.ts` 里已有译文**合并进**新抽取的 `.t.ts`**，减少手工重译。

**约定**（每种语言）：

| 角色     | 文件名示例              |
|----------|-------------------------|
| 新模板   | `app/i18n/i18n.zh_CN.t.ts` |
| 旧完整版 | `app/i18n/i18n.zh_CN.ts`   |

合并结果写回 **新模板路径**（即覆盖 `*.t.ts`）。处理的语言列表见脚本内 `languages`（与 `generate_i18n` 输出的语言代码一致）。

**用法**：

```bash
python tools/merge_translations.py
```

---

## `llm_translate_ts.py`

调用 **DeepSeek** 兼容接口，批量翻译 `.ts` 中的 `<source>`，并写回 `<translation>`。

**认证**（非 `--dry-run` 时必选其一）：

1. 环境变量 **`DEEPSEEK_API_KEY`**（默认读取该变量名，可用 `--token-env` 修改），或  
2. 仓库根目录 **`.llm.txt`**（首行非空非 `#` 内容为 API Token）。

**常用命令**：

```bash
# 预览待处理条目（不调用 API、不写文件）
python tools/llm_translate_ts.py --dry-run

# 默认处理 app/i18n 下全部 .ts（filter 默认 both：未完成或空译文）
python tools/llm_translate_ts.py

# 仅处理指定文件
python tools/llm_translate_ts.py --files app/i18n/i18n.ja_JP.ts

# 重译所有非 vanished 条目
python tools/llm_translate_ts.py --filter all
```

并行：默认 **`--workers 4`** 用多线程同时请求 API；若遇限流可改为 **`--workers 1`** 并配合 **`--sleep`**。更多参数见：`python tools/llm_translate_ts.py -h`。

**依赖**：`requests`（见项目 `requirements.txt`）。

---

## `build.py`

使用 **PyInstaller** 打开发行包（含复制部分资源、生成 updater 等）。脚本会切换工作目录到项目根，并清理 `dist/MFW` 后构建。

**用法**（需 **3 个参数**：平台、架构、版本号）：

```bash
python tools/build.py win x86_64 v1.2.3
```

若传入参数个数不符合预期，脚本会使用默认占位：`win`、`x86_64`、`v1.0.0`（以脚本内逻辑为准）。

**依赖**：已安装 PyInstaller 及项目完整运行依赖；具体打包条目以 `build.py` 内配置为准。

---

## 推荐工作流（更新界面文案翻译）

1. 改代码中的 `self.tr(...)` / 可翻译字符串。  
2. `python tools/generate_i18n.py` 更新 `.ts`。  
3. 若采用「新文件为 `.t.ts`」的合并流程：准备好 `i18n.<lang>.t.ts` 后运行 `python tools/merge_translations.py`。  
4. 需要机器辅助翻译时：`python tools/llm_translate_ts.py`（注意勿将 `.llm.txt` 提交进 Git）。  
5. `python tools/lrelease.py` 生成 `.qm`，再运行应用或执行打包验证。
