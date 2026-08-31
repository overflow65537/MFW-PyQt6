常用启动参数（MFW 开关写在分隔符 `--` 之前；之后仅传给 Qt）：

- `--config-id <ID>`（或 `--config-id=<ID>`）：启动后切换到指定配置
- `--direct-run`：启动后直接运行任务流
- `--dev`：显示测试页面（开发调试开关）
- `--force-restart`：强制重启同目录下已有实例

示例：

```powershell
python main.py --config-id default --direct-run --dev
python main.py --config-id=default --direct-run -- -platform windows:darkmode=1
MFW.exe --direct-run --force-restart --config-id c_08b08298fcf340d8a028ee63503125e2
```

查看完整说明：`python main.py --help`

## 打包

Windows、Linux 与 macOS 均由 `.github/workflows/install.yml` 中的 Nuitka job 构建主程序。更新器在独立仓库 [overflow65537/MFW-Updater](https://github.com/overflow65537/MFW-Updater) 以 Nuitka `standalone` 编译发布；主仓库 CI 通过 `tools/packaging/fetch_mfw_updater.py` 下载最新 Release 后组装。Linux 主程序使用 `onefile`；macOS 主程序使用 `app-dist`。macOS 还需 `imageio`（见 `requirements-nuitka.txt`）以将 PNG 图标转为 `.icns`：

```bash
python -m pip install -r requirements-nuitka.txt
python -m nuitka --mode=onefile --enable-plugin=pyside6 \
  --linux-icon=app/assets/icons/logo.png --output-filename=MFW main.py
python -m nuitka --mode=app-dist --enable-plugin=pyside6 \
  --macos-app-mode=gui --macos-app-icon=app/assets/icons/logo.png main.py
```

更新器源码与打包见独立仓库 [overflow65537/MFW-Updater](https://github.com/overflow65537/MFW-Updater)（本地路径 `D:\WorkSpace\MFW-Updater`）。

Linux CI 会把 onefile 的 `MFW`、自 MFW-Updater Release 下载的 `MFWUpdater/` 与外置 `maafw/` 组装为发行根。macOS 则为 `MFW.app`、`MFWUpdater/`、`maafw/` 同级。`interface.json(c)`、`resource/`、`bundle/` 和 `config/` 必须保留在主程序外部；调试更新流程时也应从该发行根启动程序。

