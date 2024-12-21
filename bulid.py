import os
import subprocess
import site
import shutil

# 获取 site-packages 路径
site_packages_paths = site.getsitepackages()

# 获取 Scripts 路径
site_user_base = site_packages_paths[0]
scripts_path = os.path.join(site_user_base, "Scripts")
print(f"Scripts 路径: {scripts_path}")

# 查找包含 nuitka 的路径
nuitka_path = os.path.join(scripts_path, "nuitka.cmd")

# 检查 nuitka 是否存在
if not os.path.exists(nuitka_path):
    print(f"未找到 Nuitka 可执行文件在路径: {nuitka_path}")
    raise FileNotFoundError("Nuitka 可执行文件未找到。")


# 定义打包命令
nuitka_command = [
    nuitka_path,
    "--standalone",
    "--plugin-enable=pyqt6",
    "--include-data-dir=config=config",
    "--include-data-dir=i18n=i18n",
    "--include-data-dir=icon=icon",
    "main.py",
]
subprocess.run(nuitka_command, check=True)

# 查找包含 maa/bin 的路径
maa_bin_path = None
for path in site_packages_paths:
    potential_path = os.path.join(path, "maa", "bin")
    if os.path.exists(potential_path):
        maa_bin_path = potential_path
        break

if maa_bin_path is None:
    raise FileNotFoundError("未找到包含 maa/bin 的路径")

# 查找包含 MaaAgentBinary 的路径
maa_bin_path2 = None
for path in site_packages_paths:
    potential_path = os.path.join(path, "MaaAgentBinary")
    if os.path.exists(potential_path):
        maa_bin_path2 = potential_path
        break

if maa_bin_path2 is None:
    raise FileNotFoundError("未找到包含 MaaAgentBinary 的路径")

# 移动 maa/bin 到 dist 目录
shutil.copytree(
    maa_bin_path,
    os.path.join(os.getcwd(), "dist", "main.dist", "maa", "bin"),
    dirs_exist_ok=True,
)

# 移动 MaaAgentBinary 到 dist 目录
shutil.copytree(
    maa_bin_path2,
    os.path.join(os.getcwd(), "dist", "main.dist", "MaaAgentBinary"),
    dirs_exist_ok=True,
)
