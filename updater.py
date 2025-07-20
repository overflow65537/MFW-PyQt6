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
MFW-ChainFlow Assistant 更新器
作者:overflow65537
"""

import zipfile
import tarfile
import os
import time
import sys
import subprocess
import psutil


def is_mfw_running():
    try:
        if sys.platform.startswith("win32"):
            for proc in psutil.process_iter(["name"]):
                if proc.info["name"] == "MFW.exe":
                    return True
        elif sys.platform.startswith("darwin") or sys.platform.startswith("linux"):
            for proc in psutil.process_iter(["name"]):
                if proc.info["name"] == "MFW":
                    return True
        return False
    except psutil.Error:
        return False


def extract_zip_file(update1_zip_name):
    """
    解压指定的 ZIP 文件。

    :param update1_zip_name: 要解压的 ZIP 文件的路径
    """
    try:
        with zipfile.ZipFile(update1_zip_name, "r") as zip_ref:
            for file_info in zip_ref.infolist():
                # 排除列表
                exclude_list = [
                    "msvcp140.dll",
                    "vcruntime140.dll",
                    "onnxruntime_maa.dll",
                    "onnxruntime_maa.so",
                    "onnxruntime_maa.dylib",
                    "fastdeploy_ppocr_maa.dll",
                    "fastdeploy_ppocr_maa.so",
                    "fastdeploy_ppocr_maa.dylib",
                ]
                if file_info.filename in exclude_list:
                    continue
                try:
                    zip_ref.extract(file_info, os.getcwd())
                    print(f"Extracted: {file_info.filename}")
                except PermissionError as e:
                    # 等待 3 秒
                    time.sleep(3)
                    # 再次尝试解压
                    try:
                        zip_ref.extract(file_info, os.getcwd())
                        print(f"Extracted: {file_info.filename}")
                    except Exception as e:
                        error_message = f"try extract {file_info.filename} failed: {e}"
                        with open("ERROR.log", "a") as log_file:
                            log_file.write(error_message + "\n")
                            if sys.argv[1] != "-update":
                                input(f"{error_message}\nPress Enter to continue...")
                        sys.exit(1)
    except zipfile.BadZipfile as e:
        tar_file_path = update1_zip_name.replace(".zip", ".tar.gz")
        os.rename(update1_zip_name, tar_file_path)
        # 按照上面的逻辑
        with tarfile.open(tar_file_path, "r") as tar_ref:
            for file_info in tar_ref.getmembers():
                # 排除列表
                exclude_list = [
                    "msvcp140.dll",
                    "vcruntime140.dll",
                    "onnxruntime_maa.dll",
                    "onnxruntime_maa.so",
                    "onnxruntime_maa.dylib",
                    "fastdeploy_ppocr_maa.dll",
                    "fastdeploy_ppocr_maa.so",
                    "fastdeploy_ppocr_maa.dylib",
                ]
                if file_info.name in exclude_list:
                    continue
                try:
                    tar_ref.extract(file_info, os.getcwd())
                    print(f"Extracted: {file_info.name}")
                except PermissionError as e:
                    # 等待 3 秒
                    time.sleep(3)
                    # 再次尝试解压
                    try:
                        tar_ref.extract(file_info, os.getcwd())
                        print(f"Extracted: {file_info.name}")
                    except Exception as e:
                        error_message = f"try extract {file_info.name} failed: {e}"
                        with open("ERROR.log", "a") as log_file:
                            log_file.write(error_message + "\n")
                            if sys.argv[1] != "-update":
                                input(f"{error_message}\nPress Enter to continue...")
                        sys.exit(1)
    except Exception as e:
        error_message = f"extract {update1_zip_name} failed: {e},enter to continue"
        input(error_message)
        sys.exit(error_message)


def standard_update():
    # 最多检查 3 次，每次间隔 5 秒
    max_checks = 3
    check_count = 0
    while check_count < max_checks:
        if not is_mfw_running():
            break
        print("MFW is still running, checking again in 5 seconds...")
        for sec in range(5, 0, -1):
            print(f"Checking again in {sec} seconds...")
            time.sleep(1)
        check_count += 1

    # 如果 3 次检查后 MFW 仍在运行，写入错误日志并结束
    if is_mfw_running():
        error_message = "Failed to update: MFW is still running after multiple checks"
        with open("ERROR.log", "a") as log_file:
            log_file.write(error_message + "\n")
        sys.exit(error_message)

    zip_file_name = os.path.join(os.getcwd(), "update.zip")
    update1_zip_name = os.path.join(os.getcwd(), "update1.zip")

    # 检查 update1.zip 文件是否存在
    if os.path.exists(zip_file_name):
        extract_zip_file(zip_file_name)

    # 删除 update1.zip 文件
    if os.path.exists(update1_zip_name):
        os.remove(update1_zip_name)
        print(f"Deleted: {update1_zip_name}")

    # 重命名 update.zip 为 update1.zip
    if os.path.exists(zip_file_name):
        os.rename(zip_file_name, update1_zip_name)
    elif os.path.exists(os.path.join(os.getcwd(), "update.tar.gz")):
        os.rename(os.path.join(os.getcwd(), "update.tar.gz"), update1_zip_name)

    # 重启程序
    if sys.platform.startswith("win32"):
        subprocess.Popen(".\\MFW.exe")
    elif sys.platform.startswith("darwin") or sys.platform.startswith("linux"):
        subprocess.Popen("./MFW")
    else:
        sys.exit("Unsupported platform")
    print("restart")


def recovery_mode():
    input("Press Enter to start recovery update...")
    update1_zip_name = os.path.join(os.getcwd(), "update1.zip")

    # 检查 update1.zip 文件是否存在
    if os.path.exists(update1_zip_name):
        extract_zip_file(update1_zip_name)
    if os.path.exists(os.path.join(os.getcwd(), "update.tar.gz")):
        os.rename(os.path.join(os.getcwd(), "update.tar.gz"), "update1.zip")

    # 重启程序
    if sys.platform.startswith("win32"):
        subprocess.Popen(".\\MFW.exe")
    elif sys.platform.startswith("darwin") or sys.platform.startswith("linux"):
        subprocess.Popen("./MFW")
    else:
        sys.exit("Unsupported platform")
    print("restart")


if __name__ == "__main__":
    # 删除错误日志
    if os.path.exists("ERROR.log"):
        os.remove("ERROR.log")
    if len(sys.argv) > 1 and sys.argv[1] == "-update":
        standard_update()
    else:
        mode = input("1. 更新模式 / Standard update\n2. 恢复模式 / Recovery update\n")
        if mode == "1":
            standard_update()
        elif mode == "2":
            recovery_mode()
        else:
            print("无效输入 / Invalid input")
            input("按回车键继续... / Press Enter to continue...")
