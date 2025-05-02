import os
import shutil
import subprocess
from setuptools import setup


# 清理之前的构建目录
def clean_build():
    build_dirs = ["dist", "build", "MFW.app", "MFWUpdater.app"]
    for dir in build_dirs:
        if os.path.exists(dir):
            shutil.rmtree(dir, ignore_errors=True)  # 添加容错处理


# 创建应用包
def build_app():
    OPTIONS = {
        "argv_emulation": True,
        "arch": "universal2",
        "plist": {
            "CFBundleName": "MFW",
            "CFBundleDisplayName": "MFW",
            "CFBundleIdentifier": "com.overflow65537.MFWPYQT6",
            "CFBundleVersion": "v0.0.1",
            "NSHumanReadableCopyright": "Copyright © 2025 Overflow65537",
            "LSMinimumSystemVersion": "12.1",
            "PyRuntimeLocations": [
                "@executable_path/../Frameworks/Python.framework/Versions/3.12/Python",
                "@executable_path/../Frameworks/Python.framework/Versions/Current/Python",
            ],
            "LSArchitecturePriority": ["arm64", "x86_64"],
        },
        "frameworks": ["/Library/Frameworks/Python.framework"],
        "includes": [
            "PyQt6",
            "maa",
            "python3.12",  # 显式包含 Python 解释器
            "site",  # 包含 Python 站点模块
        ],
        "packages": ["os", "sys", "encodings", "sqlite3"],  # 基础编码模块  # 数据库支持
        "resources": [
            "MFW_resource",
            "config",
            "/Library/Frameworks/Python.framework/Versions/3.12/lib/python3.12",  # 添加系统级库路径
        ],
        "excludes": ["tkinter"],
        "semi_standalone": True,
        "use_pythonpath": True,
        "no_strip": False,
        "optimize": 0,
        "use_2to3": False,
    }

    APP = [
        {
            "script": "main.py",
            "plist": {
                "PyRuntimeLocations": [
                    "@executable_path/../Frameworks/libpython3.12.dylib",  # 嵌入式Python路径
                    "/usr/local/bin/python3",  # Homebrew安装路径
                    "/Library/Frameworks/Python.framework/Versions/3.12/Python",  # 官方Python安装路径
                ],
                "CFBundleSupportedPlatforms": ["MacOSX"],
                "LSRequiresNativeExecution": True,
            },
        }
    ]

    setup(
        app=APP,
        options={"py2app": OPTIONS},
        setup_requires=["py2app>=0.28.6"],
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
    os.makedirs(temp_dir, exist_ok=True)

    # 定义路径变量
    src_app = os.path.join("dist", "MFW.app")
    updater_src = os.path.join("dist", "MFWUpdater.app")

    # 修改后的复制逻辑
    ignore_patterns = shutil.ignore_patterns("*.pyc", "__pycache__", "config-3.12-*")

    # 复制主程序
    if os.path.exists(src_app):
        shutil.copytree(
            src_app,
            os.path.join(temp_dir, "MFW.app"),
            dirs_exist_ok=True,
            ignore=ignore_patterns,
        )

    # 复制更新器
    if os.path.exists(updater_src):
        shutil.copytree(
            updater_src,
            os.path.join(temp_dir, "MFWUpdater.app"),
            dirs_exist_ok=True,
            ignore=ignore_patterns,
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
