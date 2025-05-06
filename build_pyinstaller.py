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
# === 构建参数处理 ===
print("[INFO] Received command line arguments:", sys.argv)
if len(sys.argv) != 4:  # 参数校验：平台/架构/版本号
    sys.argv = [sys.argv[0], "unknown", "unknown", "unknown"]
platform = sys.argv[1]
architecture = sys.argv[2]
version = sys.argv[3]


# === 依赖包路径发现 ===
def locate_package(package_name):
    """在 site-packages 中定位指定包的安装路径"""
    for path in site.getsitepackages():
        candidate = os.path.join(path, package_name)
        if os.path.exists(candidate):
            return candidate
    raise FileNotFoundError(f"Can't find {package_name} package")


try:
    # 核心依赖包定位
    maa_path = locate_package("maa")  # MAA 框架核心库
    agent_path = locate_package("MaaAgentBinary")  # 设备连接组件
    darkdetect_path = locate_package("darkdetect")  # 系统主题检测库
except FileNotFoundError as e:
    print(f"[FATAL] Dependency missing: {str(e)}")
    sys.exit(1)

# === PyInstaller 配置生成 ===
base_command = [
    "main.py",
    "--name=MFW",
    "--clean",
    "--noconfirm",  # 禁用确认提示
    # 资源包含规则（格式：源路径{分隔符}目标目录）
    f"--add-data={maa_path}{os.pathsep}maa",
    f"--add-data={agent_path}{os.pathsep}MaaAgentBinary",
    f"--add-data={darkdetect_path}{os.pathsep}darkdetect",
    f"--add-data={os.path.join(os.getcwd(), 'MFW_resource')}{os.pathsep}TEM_files{os.sep}MFW_resource",
    f"--add-data={os.path.join(os.getcwd(), 'config','emulator.json')}{os.pathsep}TEM_files{os.sep}config",
    # 自动收集包数据
    "--collect-data=darkdetect",
    "--collect-data=maa",
    "--collect-data=MaaAgentBinary",
    # 隐式依赖声明
    "--hidden-import=darkdetect",
    "--hidden-import=maa",
    "--hidden-import=MaaAgentBinary",
]

# === 平台特定配置 ===
print(f"[DEBUG] Platform: {sys.platform}")

if sys.platform == "darwin":
    if architecture == "x86_64":  # intel CPU
        base_command += [
            "--target-arch=x86_64",
        ]
    base_command += [
        "--osx-bundle-identifier=com.overflow65537.MFW",
        "--windowed",
    ]

elif sys.platform == "win32":
    base_command += [
        "--icon=MFW_resource/icon/logo.ico",
        # Windows 运行时依赖
        f"--add-binary={os.path.join('DLL', 'msvcp140.dll')}{os.pathsep}.",
        f"--add-binary={os.path.join('DLL', 'vcruntime140.dll')}{os.pathsep}.",
        "--noconsole",  # 禁用控制台窗口
    ]

# === 二进制文件处理 ===
# 收集 MAA 的本地库文件
bin_dir = os.path.join(maa_path, "bin")
bin_files = []
for f in os.listdir(bin_dir):
    print(f"[DEBUG] Found binary file: {f}")
    print(f"[DEBUG] Adding binary file: {os.path.join(bin_dir, f)}")
    bin_files.append(f)
    base_command += [f"--add-binary={os.path.join(bin_dir, f)}{os.pathsep}."]


# === 开始构建 ===
print("[INFO] Starting MFW build")
print(f"\n\n[DEBUG] base_command: {base_command}\n\n")
PyInstaller.__main__.run(base_command)

# === 构建后处理 ===

# 复制TEM_files的内容到 dist/MFW 目录
shutil.copytree(
    os.path.join(os.getcwd(), "dist", "MFW", "_internal", "TEM_files"),
    os.path.join(os.getcwd(), "dist", "MFW"),
    dirs_exist_ok=True,
)
# 删除临时目录
shutil.rmtree(os.path.join(os.getcwd(), "dist", "MFW", "_internal", "TEM_files"))

for i in bin_files:
    # 复制二进制文件到 dist/MFW 目录
    shutil.copy(
        os.path.join(os.getcwd(), "dist", "MFW", "_internal", i),
        os.path.join(os.getcwd(), "dist", "MFW"),
    )
    # 删除临时文件
    os.remove(os.path.join(os.getcwd(), "dist", "MFW", "_internal", i))


# 写入版本信息
write_version_file(platform, architecture, version)

# === 构建updater ===
PyInstaller.__main__.run(
    [
        "updater.py",
        "--name=MFWUpdater",
        "--onefile",
        "--clean",
        "--noconfirm",  # 禁用确认提示
        "--distpath",
        os.path.join("dist", "MFW"),
    ]
)
