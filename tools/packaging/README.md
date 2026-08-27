# CI / Nuitka 打包脚本

由 `.github/workflows/install.yml` 的 Nuitka job 在组装阶段调用；本地调试发行布局时也可手动运行。

| 脚本 | 作用 |
|------|------|
| `build_nuitka.py` | 为 `build/mfw-release` 生成 `file_list.txt` |
| `move_maa_bin_to_maafw.py` | 将 Nuitka 产物内 `maa/bin` 迁到发行根 `maafw/` |
| `copy_maagentbinary_to_dist.py` | macOS：拷贝 `MaaAgentBinary`（ADB 代理）进 `.app` |
| `bundle_macos_openssl.py` | macOS：打入 OpenSSL dylib 并修正 `cryptography` 路径 |
| `fix_maafw_macos_dylib_paths.py` | macOS：外置 `maafw/` 的 dylib `@executable_path` → `@loader_path` |

macOS `app-dist` 需额外安装 `requirements-nuitka.txt`（`imageio`，PNG → `.icns`）。

```bash
python tools/packaging/build_nuitka.py --file-list
python tools/packaging/move_maa_bin_to_maafw.py build/main.dist
python tools/packaging/move_maa_bin_to_maafw.py \
  build/mfw-release/MFW.app/Contents/MacOS build/mfw-release
```

macOS 发行根布局：`MFW.app`、`MFWUpdater` 与 `maafw/` 同级。
