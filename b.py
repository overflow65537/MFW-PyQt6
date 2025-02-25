import os
import site
import shutil
import sys


def write_version_file(platform, architecture, version):
    version_file_path = os.path.join(".", "bulid", "main.dist", "config", "version.txt")
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

# 移动 maa/bin 到 dist 目录
shutil.copytree(
    maa_bin_path,
    os.path.join(".", "bulid", "main.dist", "maa"),
    dirs_exist_ok=True,
)
# 移动maa/bin至根目录
src_bin = os.path.join(".", "bulid", "main.dist", "maa", "bin")
dst_root = os.path.join(".", "bulid", "main.dist")
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
    os.path.join(".", "bulid", "main.dist", "MaaAgentBinary"),
    dirs_exist_ok=True,
)
print(f"[INFO] Copied MaaAgentBinary to distribution directory")

# 复制 emulator.json 
shutil.copy(
    os.path.join(".", "config", "emulator.json"),
    os.path.join(".", "bulid", "main.dist", "config", "emulator.json"),
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
main_dist_path = os.path.join(".", "bulid", "main.dist")

# 动态识别原始文件名（支持 .exe/.bin/无扩展名）
src_files = [
    f
    for f in os.listdir(main_dist_path)
    if f.startswith("main") and os.path.isfile(os.path.join(main_dist_path, f))
]

if not src_files:
    print(f"Error: No main executable found in {main_dist_path}")
    sys.exit(1)

src_file = os.path.join(main_dist_path, src_files[0])  # 取第一个匹配项

dst_ext = {"win": "MFW.exe", "macos": "MFW.app", "linux": "MFW.bin"}.get(
    platform
)

shutil.move(src_file, os.path.join(main_dist_path, dst_ext))  # 使用动态获取的源文件路径
# 重命名文件时添加日志
print(f"[DEBUG] Renaming {src_files[0]} to {dst_ext}")
shutil.move(src_file, os.path.join(main_dist_path, dst_ext))
print(f"[SUCCESS] Executable renamed to {dst_ext}")

# 写入版本信息
write_version_file(platform, architecture, version)
# 复制updater.bin
"""shutil.copy(
    os.path.join(".","bulid", "updater.dist", "updater.bin"),
    os.path.join(".","bulid", "main.dist", "updater.bin"),
)"""
