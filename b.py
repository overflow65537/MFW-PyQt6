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

# 查找包含 maa/bin 的路径
maa_bin_path = None
for path in site_packages_paths:
    potential_path = os.path.join(path, "maa")
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
    os.path.join(os.getcwd(), "main.dist", "maa"),
    dirs_exist_ok=True,
)
# 移动maa/bin至根目录
src_bin = os.path.join(os.getcwd(), "main.dist", "maa", "bin")
dst_root = os.path.join(os.getcwd(), "main.dist")
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
    # 删除空文件夹
    os.rmdir(src_bin)

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
# 重命名main至MFW
src_file = os.path.join(os.getcwd(), "main.dist", "main.bin")
dst_ext = {
    'win': 'MFW.exe',
    'macos': 'MFW.app',
    'linux': 'MFW.bin'
}.get(platform, 'MFW.bin')

shutil.move(
    src_file,
    os.path.join(os.getcwd(), "main.dist", dst_ext)
)
# 写入版本信息
write_version_file(platform, architecture, version)
# 复制updater.bin
"""shutil.copy(
    os.path.join(os.getcwd(), "updater.dist", "updater.bin"),
    os.path.join(os.getcwd(), "main.dist", "updater.bin"),
)"""