import PyInstaller.__main__
import os
import site
import shutil
import sys


def write_version_file(platform, architecture, version):
    version_file_path = os.path.join(
        os.getcwd(), "dist", "MFW", "config", "version.txt"
    )
    with open(version_file_path, "w") as version_file:
        version_file.write(f"{platform} {architecture} {version} v0.0.0.1\n")
        print(f"write version file to {version_file_path}")


if os.path.exists("dist"):
    shutil.rmtree("dist")
# 获取 site-packages 目录列表
site_packages_paths = site.getsitepackages()

# 查找包含 maa/bin 的路径
maa_bin_path = None
for path in site_packages_paths:
    potential_path = os.path.join(path, "maa")
    if os.path.exists(potential_path):
        maa_bin_path = potential_path
        break

if maa_bin_path is None:
    raise FileNotFoundError("not found maa")

# 构建 --add-data 参数
add_data_param = f"{maa_bin_path}{os.pathsep}maa"

# 查找包含 MaaAgentBinary 的路径
maa_bin_path2 = None
for path in site_packages_paths:
    potential_path = os.path.join(path, "MaaAgentBinary")
    if os.path.exists(potential_path):
        maa_bin_path2 = potential_path
        break

if maa_bin_path2 is None:
    raise FileNotFoundError("not found MaaAgentBinary")

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
    command.insert(2, "--icon=MFW_resource/icon/logo.ico")

# 运行 PyInstaller
PyInstaller.__main__.run(command)
# 移动maa/bin至根目录
src_bin = os.path.join(os.getcwd(), "dist", "MFW", "_internal", "maa", "bin")
dst_root = os.path.join(os.getcwd(), "dist", "MFW")
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
# 确保 dist/MFW/MFW_resource 目录存在并复制
resource_src = os.path.join(os.getcwd(), "MFW_resource")
resource_dst = os.path.join(os.getcwd(), "dist", "MFW", "MFW_resource")
os.makedirs(resource_dst, exist_ok=True)
shutil.copytree(resource_src, resource_dst, dirs_exist_ok=True)

# 确保 dist/MFW/dll 目录存在并复制（仅在 Windows 上）
if sys.platform == "win32":
    dll_src = os.path.join(os.getcwd(), "dll")
    dll_dst = os.path.join(os.getcwd(), "dist", "MFW")
    os.makedirs(dll_dst, exist_ok=True)
    shutil.copytree(dll_src, dll_dst, dirs_exist_ok=True)

# 确保 dist/MFW/config/emulator.json 文件存在并复制
emulator_json_src = os.path.join(os.getcwd(), "config", "emulator.json")
emulator_json_dst = os.path.join(os.getcwd(), "dist", "MFW", "config", "emulator.json")
os.makedirs(os.path.dirname(emulator_json_dst), exist_ok=True)
shutil.copy(emulator_json_src, emulator_json_dst)

# 获取参数
print(sys.argv)
print(len(sys.argv))
if len(sys.argv) != 4:
    sys.argv = [sys.argv[0], "unknown", "unknown", "unknown"]

platform = sys.argv[1]
architecture = sys.argv[2]
version = sys.argv[3]

# 写入版本信息
write_version_file(platform, architecture, version)

# 更新器
updater_src = os.path.join(os.getcwd(), "updater.py")
PyInstaller.__main__.run([updater_src, "--name=MFWUpdater", "--clean"])

# 移动updater到dist\MFW目录
shutil.copytree(
    os.path.join(".", "dist", "MFWUpdater"),
    os.path.join(".", "dist", "MFW"),
    dirs_exist_ok=True,
)