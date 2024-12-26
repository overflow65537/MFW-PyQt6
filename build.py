import PyInstaller.__main__
import os
import site
import shutil
import sys

# 获取 site-packages 目录列表
site_packages_paths = site.getsitepackages()

# 查找包含 maa/bin 的路径
maa_bin_path = None
for path in site_packages_paths:
    potential_path = os.path.join(path, "maa", "bin")
    if os.path.exists(potential_path):
        maa_bin_path = potential_path
        break

if maa_bin_path is None:
    raise FileNotFoundError("未找到包含 maa/bin 的路径")

# 构建 --add-data 参数
add_data_param = f"{maa_bin_path}{os.pathsep}maa/bin"

# 查找包含 MaaAgentBinary 的路径
maa_bin_path2 = None
for path in site_packages_paths:
    potential_path = os.path.join(path, "MaaAgentBinary")
    if os.path.exists(potential_path):
        maa_bin_path2 = potential_path
        break

if maa_bin_path2 is None:
    raise FileNotFoundError("未找到包含 MaaAgentBinary 的路径")

# 构建 --add-data 参数
add_data_param2 = f"{maa_bin_path2}{os.pathsep}MaaAgentBinary"

command = [
    "main.py",
    "--name=MFW",
    f"--add-data={add_data_param}",
    f"--add-data={add_data_param2}",
    "--clean",
]
if sys.platform == "win32":
    command.insert(2, "--noconsole")
    command.insert(2, "--icon=resource/icon/logo.ico")
# 运行 PyInstaller
PyInstaller.__main__.run(command)
print(
    f"{os.path.join(os.getcwd(), "resource")} to {os.path.join(os.getcwd(), "dist", "MFW", "resource")}"
)
shutil.copytree(
    os.path.join(os.getcwd(), "resource"),
    os.path.join(os.getcwd(), "dist", "MFW", "resource"),
    dirs_exist_ok=True,
)
if sys.platform == "win32":
    print(
        f"{os.path.join(os.getcwd(), "dll")} to {os.path.join(os.getcwd(), "dist", "MFW")}"
    )
    shutil.copytree(
        os.path.join(os.getcwd(), "dll"),
        os.path.join(os.getcwd(), "dist", "MFW"),
        dirs_exist_ok=True,
    )
print(
    f"{os.path.join(os.getcwd(), "config", "emulator.json")} to {os.path.join(os.getcwd(), "dist", "MFW", "config", "emulator.json")}"
)
os.makedirs(os.path.join(os.getcwd(), "dist", "MFW", "config"), exist_ok=True)
shutil.copy(
    os.path.join(os.getcwd(), "config", "emulator.json"),
    os.path.join(os.getcwd(), "dist", "MFW", "config", "emulator.json"),
)
