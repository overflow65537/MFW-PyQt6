#   This file is part of MFW-ChainFlow Assistant.
#
#   MFW-ChainFlow Assistant is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published
#   by the Free Software Foundation, either version 3 of the License,
#   or (at your option) any later version.
#
#   MFW-ChainFlow Assistant is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty
#   of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See
#   the GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with MFW-ChainFlow Assistant. If not, see <https://www.gnu.org/licenses/>.
#
#   Contact: err.overflow@gmail.com
#   Copyright (C) 2024-2025  MFW-ChainFlow Assistant. All rights reserved.

"""
MFW-ChainFlow Assistant Nuitka 构建后处理脚本
作者: overflow65537
"""

import os
import plistlib
import shutil
import site
import sys
from pathlib import Path

# === 确保从项目根目录运行 ===
script_dir = Path(__file__).parent.absolute()
project_root = script_dir.parent

if not (project_root / "main.py").exists():
    if (Path.cwd() / "main.py").exists():
        project_root = Path.cwd()
    else:
        print("[ERROR] can't find project root (can't find main.py)")
        print(f"  current working directory: {os.getcwd()}")
        print(f"  script directory: {script_dir}")
        sys.exit(1)

os.chdir(project_root)
print(f"[INFO] working directory has been set to: {os.getcwd()}")


def locate_package(package_name):
    """在 site-packages 中定位指定包的安装路径"""
    for path in site.getsitepackages():
        candidate = os.path.join(path, package_name)
        if os.path.exists(candidate):
            return candidate
    raise FileNotFoundError(f"Can't find {package_name} package")


def generate_file_list(input_dir, output_file=None):
    """
    生成文件夹内所有文件的列表

    Args:
        input_dir (str): 输入文件夹路径
        output_file (str, optional): 输出文件路径，如果不提供则使用默认名称
    """
    input_path = Path(input_dir)

    if not input_path.exists():
        print(f"Error: '{input_dir}' not found")
        return False

    if not input_path.is_dir():
        print(f"Error: '{input_dir}' is not a directory")
        return False

    if output_file is None:
        output_file = f"{input_path.name}_file_list.txt"

    try:
        with open(output_file, "w", encoding="utf-8") as f:
            for root, dirs, files in os.walk(input_path):
                rel_root = os.path.relpath(root, input_path.parent)

                for file in files:
                    if rel_root == input_path.name:
                        file_path = f"./{file}"
                    else:
                        rel_dir = os.path.relpath(root, input_path)
                        if rel_dir == ".":
                            file_path = f"./{file}"
                        else:
                            file_path = f"./{rel_dir}/{file}"

                    f.write(file_path + "\n")
            f.write("./file_list.txt" + "\n")

        print(f"File list generated: {output_file}")
        print(
            f"Processed {sum([len(files) for _, _, files in os.walk(input_path)])} files"
        )
        return True

    except Exception as e:
        print(f"Error generating file list: {e}")
        return False


# === 构建参数处理 ===
print("[INFO] Received command line arguments:", sys.argv)
if len(sys.argv) != 4:
    sys.argv = [sys.argv[0], "win", "x86_64", "v1.0.0"]

platform = sys.argv[1]
architecture = sys.argv[2]
version = sys.argv[3]

with open(os.path.join(os.getcwd(), "app", "common", "__version__.py"), "w") as f:
    f.write(f'__version__ = "{version}"')

try:
    maa_path = locate_package("maa")
    agent_path = locate_package("MaaAgentBinary")
    darkdetect_path = locate_package("darkdetect")
    strenum_path = locate_package("strenum")
except FileNotFoundError as e:
    print(f"[FATAL] Dependency missing: {str(e)}")
    sys.exit(1)

build_dir = os.path.join(".", "build")
main_dist_dir = os.path.join(build_dir, "main.dist")
main_app_bundle = os.path.join(build_dir, "main.app")
macos_payload = os.path.join(main_app_bundle, "Contents", "MacOS")

if platform == "macos" and os.path.isdir(main_app_bundle) and os.path.isdir(macos_payload):
    main_dist_path = macos_payload
    bundle_root = main_app_bundle
elif os.path.isdir(main_dist_dir):
    main_dist_path = main_dist_dir
    bundle_root = main_dist_dir
else:
    print(
        f"[ERROR] Nuitka output not found. Expected {main_dist_dir} or {main_app_bundle}"
    )
    sys.exit(1)

print(f"[INFO] Bundle payload directory: {main_dist_path}")


def _rename_nuitka_entry_preserve_suffix(
    dist_root: str,
    build_dir: str,
    old_stem: str,
    new_stem: str,
) -> str | None:
    """Pick Nuitka output old_stem(.exe|.bin|''); rename to new_stem + same suffix. Search dist then build."""
    for root in (dist_root, build_dir):
        for name in (f"{old_stem}.exe", f"{old_stem}.bin", old_stem):
            src = os.path.join(root, name)
            if not os.path.isfile(src):
                continue
            suffix = Path(name).suffix
            dst_name = new_stem + suffix
            dst = os.path.join(dist_root, dst_name)
            if os.path.normcase(os.path.abspath(src)) != os.path.normcase(
                os.path.abspath(dst)
            ):
                if os.path.isfile(dst):
                    os.remove(dst)
                shutil.move(src, dst)
            return dst_name
    return None


def _patch_macos_cf_bundle_executable(app_bundle_root: str, executable_name: str) -> None:
    """Keep .app launchable after renaming the Mach-O in Contents/MacOS."""
    plist_path = os.path.join(app_bundle_root, "Contents", "Info.plist")
    if not os.path.isfile(plist_path):
        print(f"[WARN] Info.plist missing, skip CFBundleExecutable patch: {plist_path}")
        return
    with open(plist_path, "rb") as fp:
        data = plistlib.load(fp)
    data["CFBundleExecutable"] = executable_name
    with open(plist_path, "wb") as fp:
        plistlib.dump(data, fp)
    print(f"[INFO] CFBundleExecutable set to {executable_name}")


# 复制完整 maa 包到发行目录（不将 maa/bin 提升到根目录）
shutil.copytree(
    maa_path,
    os.path.join(main_dist_path, "maa"),
    dirs_exist_ok=True,
)

# 移动 MaaAgentBinary 到 dist 目录
shutil.copytree(
    agent_path,
    os.path.join(main_dist_path, "MaaAgentBinary"),
    dirs_exist_ok=True,
)
print("[INFO] Copied MaaAgentBinary to distribution directory")

shutil.copytree(
    darkdetect_path,
    os.path.join(main_dist_path, "darkdetect"),
    dirs_exist_ok=True,
)
shutil.copytree(
    strenum_path,
    os.path.join(main_dist_path, "strenum"),
    dirs_exist_ok=True,
)

# main -> MFW（仅改主文件名，保留 Nuitka 产出尾缀 .exe / .bin / 无后缀）
print("[DEBUG] Renaming main -> MFW (preserve suffix)")
_main_out = _rename_nuitka_entry_preserve_suffix(
    main_dist_path, build_dir, "main", "MFW"
)
if _main_out is None:
    print(
        f"[ERROR] Nuitka main entry not found under {main_dist_path} or {build_dir} "
        "(expected main.exe / main.bin / main)"
    )
    sys.exit(1)
if platform == "macos":
    _patch_macos_cf_bundle_executable(bundle_root, _main_out)
print(f"[SUCCESS] Main executable: {_main_out}")

# 复制README和许可证
shutil.copy(
    os.path.join(os.getcwd(), "README.md"),
    os.path.join(main_dist_path, "MFW_README.md"),
)
shutil.copy(
    os.path.join(os.getcwd(), "README-en.md"),
    os.path.join(main_dist_path, "MFW_README-en.md"),
)
shutil.copy(
    os.path.join(os.getcwd(), "LICENSE"),
    os.path.join(main_dist_path, "MFW_LICENSE"),
)

os.makedirs(os.path.join(main_dist_path, "app", "i18n"), exist_ok=True)
for qm_file in [
    "i18n.zh_CN.qm",
    "i18n.zh_TW.qm",
    "i18n.ja_JP.qm",
]:
    src = os.path.join(os.getcwd(), "app", "i18n", qm_file)
    if os.path.isfile(src):
        shutil.copy(
            src,
            os.path.join(main_dist_path, "app", "i18n", qm_file),
        )

_updater_dist = os.path.join(build_dir, "updater.dist")
if os.path.isdir(_updater_dist):
    shutil.copytree(_updater_dist, main_dist_path, dirs_exist_ok=True)
else:
    print(
        f"[WARN] {_updater_dist} not found; skip updater.dist merge "
        "(onefile may place updater only under build/)"
    )

print("[DEBUG] Renaming updater -> MFWUpdater (preserve suffix)")
_updater_out = _rename_nuitka_entry_preserve_suffix(
    main_dist_path, build_dir, "updater", "MFWUpdater"
)
if _updater_out is None:
    print(
        f"[ERROR] Nuitka updater entry not found under {main_dist_path} or {build_dir} "
        "(expected updater.exe / updater.bin / updater)"
    )
    sys.exit(1)
print(f"[SUCCESS] Updater executable: {_updater_out}")

_file_list_path = os.path.join(bundle_root, "file_list.txt")
generate_file_list(bundle_root, _file_list_path)
