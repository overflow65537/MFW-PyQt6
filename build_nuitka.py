import os
import site
import shutil
import sys


def write_version_file(platform, architecture, version):
    version_file_path = os.path.join(".", "build", "main.dist", "dist", "config", "version.txt")
    with open(version_file_path, "w") as version_file:
        version_file.write(f"{platform} {architecture} {version} v0.0.0.1\n")
        print(f"[INFO] Version file generated at: {version_file_path}")


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

# 移动 maa 到 dist 目录
shutil.copytree(
    maa_bin_path,
    os.path.join(".", "build", "main.dist", "maa"),
    dirs_exist_ok=True,
)
# 移动maa/bin至根目录
src_bin = os.path.join(".", "build", "main.dist", "maa", "bin")
dst_root = os.path.join(".", "build", "main.dist")
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
    os.path.join(".", "build", "main.dist", "MaaAgentBinary"),
    dirs_exist_ok=True,
)
print(f"[INFO] Copied MaaAgentBinary to distribution directory")

# 复制 emulator.json 
os.makedirs(os.path.join(".", "build", "main.dist", "config"), exist_ok=True)
shutil.copy(
    os.path.join(".", "config", "emulator.json"),
    os.path.join(".", "build", "main.dist", "config", "emulator.json"),
)
print("[INFO] Configuration file emulator.json copied")

# 参数错误提示修改
if len(sys.argv) != 4:
    error_message = "Argument error. Required format: platform architecture version"
    with open("ERROR.log", "a") as log_file:
        log_file.write(error_message + "\n")
    print(f"[ERROR] {error_message}")
    sys.exit(1)


platform = sys.argv[1]
architecture = sys.argv[2]
version = sys.argv[3]
# 重命名main至MFW
# 获取 main.dist 目录路径
dist_path = os.path.join(".", "build", "main.dist")

print(f"[DEBUG] Renaming")
if platform == "win":
    shutil.move(
        os.path.join(dist_path, "main.exe"),
        os.path.join(dist_path, "MFW.exe"),
    )
elif platform ==  "linux":
    shutil.move(
        os.path.join(dist_path, "main.bin"),
        os.path.join(dist_path, "MFW.bin"),
    )
if platform == "macos":
    # macOS 的可执行文件位于.app包内
    src_binary = os.path.join(dist_path, "main.app", "Contents", "MacOS", "main")
    dest_binary = os.path.join(dist_path, "MFW.app", "Contents", "MacOS", "MFW")
    
    # 确保目标目录存在
    os.makedirs(os.path.dirname(dest_binary), exist_ok=True)
else:
    src_binary = os.path.join(dist_path, "main")
    dest_binary = os.path.join(dist_path, "MFW")

try:
    shutil.move(src_binary, dest_binary)
except FileNotFoundError as e:
    print(f"Warning: File not found during move: {e}")
except Exception as e:
    print(f"Error moving file: {e}")
    raise
print(f"[SUCCESS] Executable renamed")
# 创建dist子目录
dist_path = os.path.join(dist_path, 'dist')
os.makedirs(dist_path, exist_ok=True)

# 移动依赖文件到dist目录
for folder in ['maa', 'MaaAgentBinary', 'MFW_resource', 'dll', 'config', 'updater.dist']:
    src = os.path.join(dist_path, folder)
    if os.path.exists(src):
        shutil.move(src, os.path.join(dist_path, folder))

# 复制资源文件
shutil.copytree(
    os.path.join(".", "MFW_resource"),
    os.path.join(dist_path, "MFW_resource"),
    dirs_exist_ok=True,
)
#复制dll文件
shutil.copytree(
    os.path.join(".", "dll"),
    os.path.join(dist_path, "dll"),
    dirs_exist_ok=True,
)
# 写入版本信息
write_version_file(platform, architecture, version)

# 移动配置文件到dist目录
config_src = os.path.join(dist_path, 'config')
if os.path.exists(config_src):
    shutil.move(config_src, os.path.join(dist_path, 'config'))
# 复制updater.bin到dist目录
shutil.copytree(
    os.path.join(".","build", "updater.dist"),
    os.path.join(dist_path),
    dirs_exist_ok=True,
)