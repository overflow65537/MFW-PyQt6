import os
import subprocess
import site
import shutil
import sys


site_packages_paths = site.getsitepackages()

subprocess.run(["nuitka", "--version"], check=True)

result = subprocess.run(["which", "nuitka"], check=True, capture_output=True, text=True)
nuitka_path = result.stdout.strip()

# 定义打包命令
nuitka_command = [
    str(nuitka_path),
    "--standalone",
    "--plugin-enable=pyqt6",
    "--include-data-dir=resource=resource",
    "main.py",
]

# 执行打包命令
subprocess.run(nuitka_command, check=True)

# 查找包含 maa/bin 的路径
maa_bin_path = None
for path in site_packages_paths:
    potential_path = os.path.join(path, "maa", "bin")
    if os.path.exists(potential_path):
        maa_bin_path = potential_path
        break

if maa_bin_path is None:
    exit(1)

# 查找包含 MaaAgentBinary 的路径
maa_bin_path2 = None
for path in site_packages_paths:
    potential_path = os.path.join(path, "MaaAgentBinary")
    if os.path.exists(potential_path):
        maa_bin_path2 = potential_path
        break

if maa_bin_path2 is None:
    exit(1)

# 移动 maa/bin 到 dist 目录
shutil.copytree(
    maa_bin_path,
    os.path.join(os.getcwd(), "main.dist", "maa", "bin"),
    dirs_exist_ok=True,
)

# 移动 MaaAgentBinary 到 dist 目录
shutil.copytree(
    maa_bin_path2,
    os.path.join(os.getcwd(), "main.dist", "MaaAgentBinary"),
    dirs_exist_ok=True,
)
os.makedirs(os.path.join(os.getcwd(), "main.dist", "config"), exist_ok=True)
shutil.copy(
    os.path.join(os.getcwd(), "config", "emulator.json"),
    os.path.join(os.getcwd(), "main.dist", "config", "emulator.json"),
)
