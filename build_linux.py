import os
import subprocess
import site
import shutil
import sys


def write_version_file(platform, architecture, version):
    version_file_path = os.path.join(os.getcwd(), "main.dist", "config", "version.txt")
    with open(version_file_path, "w") as version_file:
        version_file.write(f"{platform} {architecture} {version} v0.0.0.1\n")
        print(f"write version to {version_file_path}")


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

# 确保 config 目录存在并复制 emulator.json 文件
os.makedirs(os.path.join(os.getcwd(), "main.dist", "config"), exist_ok=True)
shutil.copy(
    os.path.join(os.getcwd(), "config", "emulator.json"),
    os.path.join(os.getcwd(), "main.dist", "config", "emulator.json"),
)
# 重命名main至MFW
shutil.move(
    os.path.join(os.getcwd(), "main.dist", "main.bin"),
    os.path.join(os.getcwd(), "main.dist", "MFW.bin"),
)

# 获取参数
if len(sys.argv) != 4:
    error_message = "args error, should be: platform architecture version"
    with open("ERROR.log", "a") as log_file:
        log_file.write(error_message + "\n")
    print(error_message)
    sys.exit(1)

platform = sys.argv[1]
architecture = sys.argv[2]
version = sys.argv[3]

# 写入版本信息
write_version_file(platform, architecture, version)

# 更新器
# 定义打包命令
nuitka_command_updater = [
    str(nuitka_path),
    "--standalone",
    "--onefile",
    "updater.py",
]

# 执行打包命令
subprocess.run(nuitka_command_updater, check=True)

shutil.copy(
    os.path.join(os.getcwd(), "updater.dist", "updater.bin"),
    os.path.join(os.getcwd(), "main.dist", "updater.bin"),
)
