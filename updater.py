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


def extract_zip_file(update_file_path):
    """
    解压指定的压缩文件，自动判断是zip还是tar.gz格式。

    :param update_file_path: 要解压的压缩文件的路径
    """
    try:
        # 确定解压目标目录
        target_dir = os.getcwd()

        print(f"解压目标目录: {target_dir}")

        try:
            with zipfile.ZipFile(update_file_path, "r") as zip_ref:
                for file_info in zip_ref.infolist():
                    zip_ref.extract(file_info, target_dir)
                    print(f"已解压: {file_info.filename}")
        except zipfile.BadZipfile:
            try:
                with tarfile.open(update_file_path, "r") as tar_ref:
                    for file_info in tar_ref.getmembers():
                        tar_ref.extract(file_info, target_dir)
                        print(f"已解压: {file_info.name}")
            except tarfile.TarError as e:
                error_message = f"无法识别的文件格式或文件已损坏: {update_file_path}"
                input(error_message)
                sys.exit(error_message)
    except Exception as e:
        error_message = f"解压 {update_file_path} 失败: {e}"
        input(error_message)
        sys.exit(error_message)


def handle_extract_error(filename, error):
    """
    处理解压过程中的错误

    :param filename: 解压失败的文件名
    :param error: 错误信息
    """
    error_message = f"解压 {filename} 失败: {error}"
    with open("ERROR.log", "a") as log_file:
        log_file.write(error_message + "\n")
        if len(sys.argv) > 1 and sys.argv[1] != "-update":
            input(f"{error_message}\n按回车键继续...")
    sys.exit(1)


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
    elif sys.platform.startswith("darwin"):
        subprocess.Popen("open .\\MFW.app")
    elif sys.platform.startswith("linux"):
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
