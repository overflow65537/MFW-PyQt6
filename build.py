import os
import subprocess
import site
import shutil
import sys


site_packages_paths = site.getsitepackages()
subprocess.run(["nuitka", "--version"], check=True)
if sys.platform == "win32":
    # 获取 Scripts 路径
    site_user_base = site_packages_paths[0]
    scripts_path = os.path.join(site_user_base, "Scripts")
    print(f"Scripts path: {scripts_path}")

    # 查找包含 nuitka 的路径
    nuitka_path = os.path.join(scripts_path, "nuitka.cmd")
    subprocess.run([nuitka_path, "--version"], check=True)
else:
    subprocess.run(["nuitka", "--version"], check=True)

    result = subprocess.run(
        ["which", "nuitka"], check=True, capture_output=True, text=True
    )
    nuitka_path = result.stdout.strip()

# 定义打包命令
nuitka_command = [
    str(nuitka_path),
    "--standalone",
    "--plugin-enable=pyqt6",
    "--include-data-dir=config=config",
    "--include-data-dir=i18n=i18n",
    "--include-data-dir=icon=icon",
    "main.py",
]
# macos 下需要额外参数
if sys.platform == "darwin":
    nuitka_command.insert(1, "--macos-create-app-bundle")
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
