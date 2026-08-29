# CI / Nuitka 打包脚本

由 `.github/workflows/install.yml` 的 Nuitka job 在组装阶段调用；本地调试发行布局时也可手动运行。

| 脚本 | 作用 |
|------|------|
| `build_nuitka.py` | 为 `build/mfw-release` 生成 `file_list.txt` |
| `move_maa_bin_to_maafw.py` | 将 Nuitka 产物内 `maa/bin` 迁到发行根 `maafw/` |
| `copy_maagentbinary_to_dist.py` | macOS：拷贝 `MaaAgentBinary`（ADB 代理）进 `.app` |
| `patch_macos_info_plist.py` | macOS：声明 `CFBundleLocalizations`（Qt 其它本地化行为；语言检测走 `AppleLanguages`） |
| `bundle_macos_openssl.py` | macOS：打入 OpenSSL dylib 并修正 `cryptography` 路径 |
| `fix_maafw_macos_dylib_paths.py` | macOS：外置 `maafw/` 的 dylib `@executable_path` → `@loader_path` |

Nuitka 须收录 `app.builtin_tasks`（`BuiltinTaskLoader` 运行时 `importlib` 加载；见 `main.py` 的 `nuitka-project` 与 CI `include-package`）。

内嵌 Qt 资源经 `tools/lrelease.py` + `tools/rcc_resources.py` 生成 `app/resources/app_rc.py`，包含 UI 翻译（`:/i18n/*.qm`）与默认 logo（`:/icons/logo.png`），由 Nuitka 打进 MFW 主程序。`logo.ico` / `logo.icns` 仅用于 Nuitka 可执行文件图标，不打入运行时资源。

macOS `app-dist` 需额外安装 `requirements-nuitka.txt`（`imageio`，PNG → `.icns`）。

```bash
python tools/packaging/build_nuitka.py --file-list
python tools/packaging/move_maa_bin_to_maafw.py build/main.dist
python tools/packaging/move_maa_bin_to_maafw.py build/main.dist build/mfw-release
python tools/packaging/move_maa_bin_to_maafw.py \
  build/mfw-release/MFW.app/Contents/MacOS build/mfw-release
```

Linux `onefile` 发行根：`MFW`、`MFWUpdater` 与 `maafw/` 同级（`maa/bin` 从 Nuitka 留下的 `main.dist` 迁出）。macOS 发行根：`MFW.app`、`MFWUpdater` 与 `maafw/` 同级。
