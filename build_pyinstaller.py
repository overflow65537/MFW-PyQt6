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
        version_file.write(f"{platform} {architecture} {version}\n")
        print(f"write version file to {version_file_path}")


# 获取参数
print(sys.argv)
print(len(sys.argv))
if len(sys.argv) != 4:
    sys.argv = [sys.argv[0], "unknown", "unknown", "unknown"]

platform = sys.argv[1]
architecture = sys.argv[2]
version = sys.argv[3]

if os.path.exists("dist"):
    shutil.rmtree("dist")
# 获取 site-packages 目录列表
site_packages_paths = site.getsitepackages()

# 查找包含 maa/bin 的路径
maa_path = None
for path in site_packages_paths:
    potential_path = os.path.join(path, "maa")
    if os.path.exists(potential_path):
        maa_path = potential_path
        break

if maa_path is None:
    raise FileNotFoundError("not found maa")

# 查找包含 MaaAgentBinary 的路径
MaaAgentBinary_path = None
for path in site_packages_paths:
    potential_path = os.path.join(path, "MaaAgentBinary")
    if os.path.exists(potential_path):
        MaaAgentBinary_path = potential_path
        break

if MaaAgentBinary_path is None:
    raise FileNotFoundError("not found MaaAgentBinary")

# 查找 darkdetect 路径
darkdetect_path = None
for path in site_packages_paths:
    potential_path = os.path.join(path, "darkdetect")
    if os.path.exists(potential_path):
        darkdetect_path = potential_path
        break

if darkdetect_path is None:
    raise FileNotFoundError("darkdetect binaries not found")


# PyInstaller 命令参数
command = [
    "main.py",
    "--name=MFW",
    f"--add-data={maa_path}{os.pathsep}MaaAgentBinary",
    f"--add-data={MaaAgentBinary_path}{os.pathsep}MaaAgentBinary",
    f"--add-data={darkdetect_path}{os.pathsep}darkdetect",  
    "--clean",
    "--collect-data=darkdetect", 
    "--collect-data=maa", 
    "--collect-data=MaaAgentBinary",
    "--hidden-import=darkdetect", 
    "--hidden-import=maa",
    "--hidden-import=MaaAgentBinary",
]
maa_bin = []
src_bin = os.path.join(os.getcwd(), maa_path, "bin")
for file in os.listdir(src_bin):
    if file.endswith(".dylib") or file.endswith(".so") or file.endswith(".dll"):
        maa_bin.append(file)
        command += [f"--add-binary={os.path.join(src_bin, file)}:."]

# 添加 macOS 通用二进制支持
if sys.platform == "darwin":
    if architecture == "x86_64":
        command += ["--target-arch=x86_64"]
    command += [
        "--osx-bundle-identifier=com.overflow65537.MFW",
    ]

elif sys.platform == "win32":
    command += [
        "--noconsole",
        "--icon=MFW_resource/icon/logo.ico",
        f"--add-binary={os.path.join(os.getcwd(), 'DLL', 'msvcp140.dll')}:.",
        f"--add-binary={os.path.join(os.getcwd(), 'DLL','vcruntime140.dll')}:.",
    ]

# 运行 PyInstaller
print(f"Running PyInstaller with command: {command}\n")
PyInstaller.__main__.run(command)

#删除dist/MFW/_internal/maa/bin目录,内部有文件
if os.path.exists(os.path.join(os.getcwd(), "dist", "MFW", "_internal", "maa", "bin")):
    shutil.rmtree(os.path.join(os.getcwd(), "dist", "MFW", "_internal", "maa", "bin"))
dst_root = os.path.join(os.getcwd(), "dist", "MFW")

# 移动os.path.join(os.getcwd(),"dist", "MFW", "_internal", "maa", "bin")内的文件到根目录
for file in maa_bin:
    src = os.path.join(os.getcwd(), "dist", "MFW", "_internal", file)
    dst = os.path.join(dst_root, file)
    if os.path.exists(src):
        shutil.move(src, dst)
        print(f"Moved {src} to {dst}")


# 确保 dist/MFW/MFW_resource 目录存在并复制
resource_src = os.path.join(os.getcwd(), "MFW_resource")
resource_dst = os.path.join(os.getcwd(), "dist", "MFW", "MFW_resource")
os.makedirs(resource_dst, exist_ok=True)
shutil.copytree(resource_src, resource_dst, dirs_exist_ok=True)


# 确保 dist/MFW/config/emulator.json 文件存在并复制
emulator_json_src = os.path.join(os.getcwd(), "config", "emulator.json")
emulator_json_dst = os.path.join(os.getcwd(), "dist", "MFW", "config", "emulator.json")
os.makedirs(os.path.dirname(emulator_json_dst), exist_ok=True)
shutil.copy(emulator_json_src, emulator_json_dst)


# 写入版本信息
write_version_file(platform, architecture, version)

# 更新器
updater_src = os.path.join(os.getcwd(), "updater.py")
PyInstaller.__main__.run([updater_src, "--name=MFWUpdater", "--onefile", "--clean"])

# 移动updater到dist\MFW目录
if sys.platform == "win32":
    updater_file = os.path.join("dist", "MFWUpdater.exe")
elif sys.platform == "linux" or sys.platform == "darwin":
    updater_file = os.path.join("dist", "MFWUpdater")

mfw_path = os.path.join("dist", "MFW")

# 移动文件到 MFW 目录
if os.path.exists(updater_file):
    dst_path = os.path.join(mfw_path, os.path.basename(updater_file))
    shutil.move(updater_file, dst_path)
    print(f"Moved {updater_file} to {dst_path}")
else:
    print(f"File {updater_file} not found.")
