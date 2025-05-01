import os
import shutil
import subprocess
from setuptools import setup


# 清理之前的构建目录
def clean_build():
    build_dirs = ["dist", "build"]
    for dir in build_dirs:
        if os.path.exists(dir):
            shutil.rmtree(dir)


# 创建应用包
def build_app():
    # 配置py2app选项
    APP = ["main.py"]
    
    DATA_FILES = [  # 添加此定义
        "MFW_resource",
        "config",
    ]
    
    OPTIONS = {
        "argv_emulation": True,
        "plist": {
            "CFBundleName": "MFW",
            "CFBundleDisplayName": "MFW",
            "CFBundleIdentifier": "com.overflow65537.MFWPYQT6",
            "CFBundleVersion": "v0.0.1",
            "NSHumanReadableCopyright": "Copyright © 2025 Overflow65537",
            "LSMinimumSystemVersion": "12.1",
            "PyRuntimeLocations": [
                # 更新为通用架构路径
                "/Library/Frameworks/Python.framework/Versions/Current/lib/python3.12/python3"
            ],
        },
        "arch": ["x86_64", "arm64"],  # 修改为列表格式
        "includes": ["PyQt6", "maa"],
        "resources": DATA_FILES,
        "frameworks": [],
    }

    setup(
        app=APP,
        options={"py2app": OPTIONS},
        setup_requires=["py2app >= 0.29"],  # 指定最小版本
        python_requires=">=3.10",
        script_args=["py2app"],
    )


# 创建dmg安装包
def build_updater():
    """构建更新器"""
    updater_src = "updater.py"
    if os.path.exists(updater_src):
        setup(
            script_args=["py2app"],  # 保留参数
            app=[updater_src],
            options={
                "py2app": {
                    "argv_emulation": False,
                    "plist": {
                        "CFBundleName": "MFWUpdater",
                        "CFBundleIdentifier": "com.overflow65537.MFWUpdater",
                    },
                }
            },
            setup_requires=["py2app"],
        )


def create_dmg():
    """创建包含主程序和所有资源的DMG"""
    dmg_path = os.path.join("dist", "MFW_Complete.dmg")
    temp_dir = os.path.join("dist", "temp_dmg")

    # 创建临时目录结构
    os.makedirs(temp_dir, exist_ok=True)

    # 复制主程序
    shutil.copytree(
        os.path.join("dist", "MFW.app"),
        os.path.join(temp_dir, "MFW.app"),
        dirs_exist_ok=True,
    )

    # 复制更新器
    updater_src = os.path.join("dist", "MFWUpdater.app")
    if os.path.exists(updater_src):
        shutil.copytree(
            updater_src, os.path.join(temp_dir, "MFWUpdater.app"), dirs_exist_ok=True
        )

    # 创建Applications快捷方式
    os.symlink("/Applications", os.path.join(temp_dir, "Applications"))

    # 创建DMG
    if os.path.exists(dmg_path):
        os.remove(dmg_path)

    subprocess.run(
        [
            "hdiutil",
            "create",
            "-volname",
            "MFW",
            "-srcfolder",
            temp_dir,
            "-ov",
            dmg_path,
            "-format",
            "UDZO",
            "-fs",
            "HFS+",
            "-imagekey",
            "zlib-level=9",
        ]
    )

    # 清理临时目录
    shutil.rmtree(temp_dir)


def main():
    clean_build()
    build_app()
    build_updater()
    create_dmg()

if __name__ == "__main__":
    main()
    print("构建完成！完整安装包位于 dist/MFW_Complete.dmg")
