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

main_dist_path = os.path.join(".", "build", "main.dist")
if not os.path.isdir(main_dist_path):
    print(f"[ERROR] Nuitka output not found: {main_dist_path}")
    sys.exit(1)

# 移动 maa 到 dist 目录
shutil.copytree(
    maa_path,
    os.path.join(main_dist_path, "maa"),
    dirs_exist_ok=True,
)
# 移动maa/bin至根目录
src_bin = os.path.join(main_dist_path, "maa", "bin")
dst_root = main_dist_path
if os.path.exists(src_bin):
    for item in os.listdir(src_bin):
        src = os.path.join(src_bin, item)
        dst = os.path.join(dst_root, item)
        if os.path.exists(dst):
            if os.path.isdir(dst):
                shutil.rmtree(dst)
            else:
                os.remove(dst)
        shutil.move(src, dst)
    os.rmdir(src_bin)

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

# 重命名main至MFW
print("[DEBUG] Renaming")
if platform == "win":
    shutil.move(
        os.path.join(main_dist_path, "main.exe"),
        os.path.join(main_dist_path, "MFW.exe"),
    )
elif platform == "linux":
    shutil.move(
        os.path.join(main_dist_path, "main.bin"),
        os.path.join(main_dist_path, "MFW.bin"),
    )
elif platform == "macos":
    shutil.move(
        os.path.join(main_dist_path, "main.bin"),
        os.path.join(main_dist_path, "MFW"),
    )
else:
    shutil.move(
        os.path.join(main_dist_path, "main"),
        os.path.join(main_dist_path, "MFW"),
    )
print("[SUCCESS] Executable renamed")

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

shutil.copytree(
    os.path.join(".", "build", "updater.dist"),
    main_dist_path,
    dirs_exist_ok=True,
)

generate_file_list(
    os.path.join("build", "main.dist"),
    os.path.join("build", "main.dist", "file_list.txt"),
)
