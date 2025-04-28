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

# 在已有的 --add-data 参数后添加新的数据收集

command = [
    "main.py",
    "--name=MFW",
    f"--add-data={add_data_param}", 
    f"--add-data={add_data_param2}",
    "--clean",
]

# 平台特定参数应该集中处理
darwin_args = []
win_args = []

if sys.platform == "darwin":
    if architecture == "x64":
        darwin_args.append("--target-arch=x86_64")
    # macOS 专用参数

    pyqt6_path = None
    for path in site_packages_paths:
        qt_path = os.path.join(path, 'PyQt6', 'Qt6')
        if os.path.exists(qt_path):
            pyqt6_path = qt_path
            break
    
    if pyqt6_path:
        # 添加Qt核心资源
        darwin_args.extend([
            f'--add-data={os.path.join(pyqt6_path, "plugins/platforms/*")}:PyQt6/Qt6/plugins/platforms',
            f'--add-data={os.path.join(pyqt6_path, "resources/*")}:PyQt6/Qt6/resources'
        ])
    
    # macOS 专用参数
    command += darwin_args

if sys.platform == "win32":
    win_args.extend([
        "--noconsole",
        "--icon=MFW_resource/icon/logo.ico"
    ])
    command += win_args

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
    
    # 修复 macOS 动态库依赖
    if sys.platform == "darwin":
        from subprocess import run
        lib_dir = dst_root 
        
        libs_to_fix = [
            "libMaaToolkit.dylib",
            "libMaaFramework.dylib",
            "libMaaUtils.dylib",
            "libopencv_world4.4.8.0.dylib",
            "PyQt6/Qt6/lib/libQt6Core.abi3.dylib"
        ]
        # 创建qt.conf配置文件
        qt_conf_dir = os.path.join(lib_dir, "PyQt6", "Qt6", "libexec")
        os.makedirs(qt_conf_dir, exist_ok=True)
        with open(os.path.join(qt_conf_dir, "qt.conf"), "w") as f:
            f.write("[Paths]\nPlugins = ../../plugins\n")
        
        for lib in libs_to_fix:
            lib_path = os.path.join(lib_dir, lib)
            if os.path.exists(lib_path):
                # 添加 RPATH 设置
                run(["install_name_tool", "-add_rpath", "@executable_path", lib_path], check=True)
                # 修复系统库路径（针对 libc++.1.dylib）
                run(["install_name_tool", "-change", "@rpath/libc++.1.dylib", 
                    "/usr/lib/libc++.1.dylib", lib_path], check=True)
        # 添加Qt框架符号链接
        qt_lib_path = os.path.join(lib_dir, "PyQt6", "Qt6", "lib")
        if os.path.exists(qt_lib_path):
            libcpp_path = os.path.join(qt_lib_path, "libc++.1.dylib")
            if not os.path.exists(libcpp_path):
                os.symlink("/usr/lib/libc++.1.dylib", libcpp_path)
                print("Created libc++ symlink for Qt")
                
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



# 写入版本信息
write_version_file(platform, architecture, version)

# 更新器
updater_src = os.path.join(os.getcwd(), "updater.py")
PyInstaller.__main__.run([updater_src, "--name=MFWUpdater", "--onefile", "--clean"])

# 移动updater到dist\MFW目录
if sys.platform == "win32":
    updater_file = os.path.join("dist", "MFWUpdater.exe")
elif sys.platform.startswith("linux"):
    updater_file = os.path.join("dist", "MFWUpdater")
elif sys.platform == "darwin":
    updater_file = os.path.join("dist", "MFWUpdater")
else:
    exit("Unsupported platform")

mfw_dir = os.path.join("dist", "MFW")

# 移动文件到 MFW 目录
if os.path.exists(updater_file):
    dst_path = os.path.join(mfw_dir, os.path.basename(updater_file))
    shutil.move(updater_file, dst_path)
    print(f"Moved {updater_file} to {dst_path}")
else:
    print(f"File {updater_file} not found.")
if sys.platform == "darwin":
    # 自动查找 darkdetect 安装路径
    darkdetect_path = None
    for path in site.getsitepackages():
        potential_path = os.path.join(path, "darkdetect")
        if os.path.exists(potential_path):
            darkdetect_path = potential_path
            break
    
    if darkdetect_path:
        # 复制整个 darkdetect 目录
        darkdetect_dst = os.path.join(os.getcwd(), "dist", "MFW", "_internal", "darkdetect")
        shutil.copytree(darkdetect_path, darkdetect_dst, dirs_exist_ok=True)
        # 修复可执行文件权限
        detect_bin = os.path.join(darkdetect_dst, "detect")
        if os.path.exists(detect_bin):
            os.chmod(detect_bin, 0o755)