#   This file is part of MFW-ChainFlow Assistant.

#   MFW-ChainFlow Assistant is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published
#   by the Free Software Foundation, either version 3 of the License,
#   or (at your option) any later version.

#   MFW-ChainFlow Assistant is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty
#   of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See
#   the GNU General Public License for more details.

#   You should have received a copy of the GNU General Public License
#   along with MFW-ChainFlow Assistant. If not, see <https://www.gnu.org/licenses/>.

#   Contact: err.overflow@gmail.com
#   Copyright (C) 2024-2025  MFW-ChainFlow Assistant. All rights reserved.

"""
MFW-ChainFlow Assistant
MFW-ChainFlow Assistant 打包脚本
作者:overflow65537
"""
import PyInstaller.__main__
import os
import site
import shutil
import sys

# 删除dist
if os.path.exists(os.path.join(os.getcwd(), "dist", "MFW")):
    shutil.rmtree(os.path.join(os.getcwd(), "dist", "MFW"))

# 获取参数
# === 构建参数处理 ===
print("[INFO] Received command line arguments:", sys.argv)
if len(sys.argv) != 4:  # 参数校验：平台/架构/版本号
    sys.argv = [sys.argv[0], "win", "x86_64", "v1.0.0"]

platform = sys.argv[1]
architecture = sys.argv[2]
version = sys.argv[3]

# 写入版本号
with open(os.path.join(os.getcwd(), "app", "common", "__version__.py"), "w") as f:
    f.write(f'__version__ = "{version}"')


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
    strenum = locate_package("strenum")
except FileNotFoundError as e:
    print(f"[FATAL] Dependency missing: {str(e)}")
    sys.exit(1)

# === PyInstaller 配置生成 ===
base_command = [
    "main.py",
    "--name=MFW",
    "--onedir",
    "--clean",
    "--noconfirm",
    f"--add-binary={maa_path}{os.pathsep}maa",
    f"--add-binary={agent_path}{os.pathsep}MaaAgentBinary",
    f"--add-binary={darkdetect_path}{os.pathsep}darkdetect",
    f"--add-binary={strenum}{os.pathsep}strenum",
]

# === 平台特定配置 准备阶段 ===
print(f"[DEBUG] Platform: {sys.platform}")

if sys.platform == "darwin":

    if architecture == "x86_64":  # intel CPU
        base_command += [
            "--target-arch=x86_64",
        ]
        print("[DEBUG] Target arch: x86_64")
    elif architecture == "aarch64":  # M1/M2 CPU
        base_command += [
            "--target-arch=arm64",
        ]
        print("[DEBUG] Target arch: aarch64")
    base_command += [
        "--osx-bundle-identifier=com.overflow65537.MFW",
        
        "--windowed",
        # 图标
        "--icon=MFW_resource/icon/logo.icns",
        "--distpath",
        os.path.join("dist", "MFW"),
    ]

elif sys.platform == "win32":
    base_command += [
        "--icon=MFW_resource/icon/logo.ico",
        "--distpath",
        os.path.join("dist"),
    ]
    if "ci" not in version:
        base_command += [
            "--noconsole",  # 禁用控制台窗口
        ]

elif sys.platform == "linux":
    base_command += ["--distpath", os.path.join("dist")]
# === 开始构建 ===
print("[INFO] Starting MFW build")
print(f"\n\n[DEBUG] base_command: {base_command}\n\n")
PyInstaller.__main__.run(base_command)

# === 平台特定配置 完成阶段 ===
if sys.platform == "darwin":
    for file in os.listdir(os.path.join(os.getcwd(), "dist", "MFW")):
        print(file)

    shutil.copytree(
        os.path.join(os.getcwd(), "MFW_resource"),
        os.path.join(
            os.getcwd(),
            "dist",
            "MFW",
            "MFW.app",
            "Contents",
            "MacOS",
            "MFW_resource",
        ),
        dirs_exist_ok=True,
    )
    shutil.rmtree(os.path.join(os.getcwd(), "dist", "MFW", "MFW"))
    # 遍历MFW.app/Contents/Resources文件夹下的所有文件
    for file in os.listdir(
        os.path.join(os.getcwd(), "dist", "MFW", "MFW.app", "Contents", "Resources")
    ):
        # 删除除了logo.icns以外的所有文件和文件夹
        if file != "logo.icns":
            # 这里有可能是文件夹，需要递归删除
            try:
                os.remove(
                    os.path.join(
                        os.getcwd(),
                        "dist",
                        "MFW",
                        "MFW.app",
                        "Contents",
                        "Resources",
                        file,
                    )
                )
            except PermissionError:
                shutil.rmtree(
                    os.path.join(
                        os.getcwd(),
                        "dist",
                        "MFW",
                        "MFW.app",
                        "Contents",
                        "Resources",
                        file,
                    )
                )

    # === 代码签名集成 ===
    print("[INFO] Starting code signing process...")
    
    # 检查是否在CI环境中（证书已在CI阶段导入到钥匙串）
    if os.environ.get('CERTIFICATE_BASE64'):
        print("[INFO] Detected CI environment - certificate already imported to keychain")
        
        # 执行签名（证书已在CI阶段导入到钥匙串）
        app_path = os.path.join(os.getcwd(), "dist", "MFW", "MFW.app")
        
        if not os.path.exists(app_path):
            print("[WARNING] Application not found, skipping code signing")
        else:
            print(f"[INFO] Application path: {app_path}")
            
            # 分步签名避免文件类型问题
            print("[INFO] Signing libraries and executables...")
            
            # 签名动态库
            for root, dirs, files in os.walk(app_path):
                for file in files:
                    if file.endswith('.dylib') or file.endswith('.so'):
                        file_path = os.path.join(root, file)
                        print(f"[DEBUG] Signing: {file_path}")
                        subprocess.run([
                            'codesign', '--force', '--sign', 
                            'overflow65537 Developer Certificate', 
                            file_path
                        ], check=False)
            
            # 签名可执行文件
            executable_path = os.path.join(app_path, "Contents", "MacOS", "MFW")
            if os.path.exists(executable_path):
                print(f"[DEBUG] Signing executable: {executable_path}")
                subprocess.run([
                    'codesign', '--force', '--sign', 
                    'overflow65537 Developer Certificate', 
                    executable_path
                ], check=False)
            
            # 签名更新器
            updater_path = os.path.join(app_path, "Contents", "MacOS", "MFWUpdater")
            if os.path.exists(updater_path):
                print(f"[DEBUG] Signing updater: {updater_path}")
                subprocess.run([
                    'codesign', '--force', '--sign', 
                    'overflow65537 Developer Certificate', 
                    updater_path
                ], check=False)
            
            # 签名整个应用（使用--deep选项）
            print("[INFO] Signing entire application with deep signing...")
            result = subprocess.run([
                'codesign', '--force', '--deep', '--sign', 
                'overflow65537 Developer Certificate',
                '--options', 'runtime',
                app_path
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print("[SUCCESS] Application signed successfully!")
            else:
                print(f"[WARNING] Deep signing failed: {result.stderr}")
                # 尝试不使用--deep选项
                print("[INFO] Trying without --deep option...")
                subprocess.run([
                    'codesign', '--force', '--sign', 
                    'overflow65537 Developer Certificate',
                    '--options', 'runtime',
                    app_path
                ], check=False)
            
            # 验证签名
            print("[INFO] Verifying signature...")
            verify_result = subprocess.run([
                'codesign', '-dv', '--verbose=4', app_path
            ], capture_output=True, text=True)
            
            if verify_result.returncode == 0:
                print("[SUCCESS] Signature verification passed!")
                print(verify_result.stdout)
            else:
                print(f"[WARNING] Signature verification failed: {verify_result.stderr}")
    
    else:
        print("[INFO] No certificate environment detected, skipping code signing")

else:
    shutil.copytree(
        os.path.join(os.getcwd(), "MFW_resource"),
        os.path.join(os.getcwd(), "dist", "MFW", "MFW_resource"),
        dirs_exist_ok=True,
    )

# 复制README和许可证并在开头加上MFW_前缀
for file in ["README.md", "README-en.md", "LICENSE"]:
    shutil.copy(
        os.path.join(os.getcwd(), file),
        os.path.join(os.getcwd(), "dist", "MFW", f"MFW_{file}"),
    )


# === 构建updater ===
updater_command = [
    "updater.py",
    "--name=MFWUpdater",
    "--onefile",
    "--clean",
    "--noconfirm",  # 禁用确认提示
    "--distpath",
    os.path.join("dist", "MFWupdater"),
]
PyInstaller.__main__.run(updater_command)

# 转移更新器
if sys.platform == "win32":
    shutil.copy(
        os.path.join(os.getcwd(), "dist", "MFWupdater", "MFWUpdater.exe"),
        os.path.join(os.getcwd(), "dist", "MFW", "MFWUpdater.exe"),
    )
    shutil.rmtree(os.path.join(os.getcwd(), "dist", "MFWupdater"))
elif sys.platform == "linux":
    shutil.copy(
        os.path.join(os.getcwd(), "dist", "MFWupdater", "MFWUpdater"),
        os.path.join(os.getcwd(), "dist", "MFW", "MFWUpdater"),
    )
    shutil.rmtree(os.path.join(os.getcwd(), "dist", "MFWupdater"))
elif sys.platform == "darwin":

    shutil.copy(
        os.path.join(os.getcwd(), "dist", "MFWupdater", "MFWUpdater"),
        os.path.join(
            os.getcwd(), "dist", "MFW", "MFW.app", "Contents", "MacOS", "MFWUpdater"
        ),
    )
    shutil.rmtree(os.path.join(os.getcwd(), "dist", "MFWupdater"))
