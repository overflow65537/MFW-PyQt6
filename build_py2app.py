#!/usr/bin/env python3
import os
import sys
import subprocess
import argparse
import shutil


def build_app(arch, version):
    """
    使用py2app构建应用
    """
    print(f"Building MFW-ChainFlow Assistant for MacOS-{arch} version {version}")

    # 设置版本信息
    with open("VERSION", "w") as f:
        f.write(version)

    try:
        # 清理之前的构建
        if os.path.exists("dist"):
            shutil.rmtree("dist")
        if os.path.exists("build"):
            shutil.rmtree("build")

        # 执行py2app构建
        result = subprocess.run(
            [sys.executable, "setup.py", "py2app"], capture_output=True, text=True
        )
        if result.returncode != 0:
            print(f"Build failed: {result.stderr}")
            return False

        print("Build completed successfully!")

        return True

    except Exception as e:
        print(f"Build error: {e}")
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Build MFW-ChainFlow Assistant with py2app"
    )
    parser.add_argument("arch", help="Target architecture")
    parser.add_argument("version", help="Application version")

    args = parser.parse_args()

    success = build_app( args.arch, args.version)
    sys.exit(0 if success else 1)
