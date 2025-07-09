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
import os
import time
import sys
import subprocess
import psutil 


def clear_zip_file():
    try:
        if os.path.exists(zip_file_name):
            os.remove(zip_file_name)
            print(f"Deleted: {zip_file_name}")
    except:
        error_message = f"failed to delete {zip_file_name}"
        with open("ERROR.log", "a") as log_file:
            log_file.write(error_message + "\n")


def is_mfw_running():
    try:
        if sys.platform.startswith("win32"):
            for proc in psutil.process_iter(['name']):
                if proc.info['name'] == 'MFW.exe':
                    return True
        elif sys.platform.startswith("darwin") or sys.platform.startswith("linux"):
            for proc in psutil.process_iter(['name']):
                if proc.info['name'] == 'MFW':
                    return True
        return False
    except psutil.Error:
        return False


def close_mfw_with_retry():
    max_retries = 3
    retry_count = 0
    while retry_count < max_retries:
        if not is_mfw_running():  # 检查 MFW 是否在运行
            break

        try:
            if sys.platform.startswith("win32"):
                # 以管理员权限执行 taskkill 命令
                subprocess.run(["powershell", "-Command", "Start-Process", "taskkill", "-ArgumentList", "'/F', '/IM', 'MFW.exe'", "-Verb", "RunAs", "-Wait"], check=True)
            elif sys.platform.startswith("darwin") or sys.platform.startswith("linux"):
                # 以管理员权限执行 pkill 命令
                subprocess.run(["sudo", "pkill", "MFW"], check=True)
            break  # 关闭成功，跳出循环
        except subprocess.CalledProcessError as e:
            error_message = f"Failed to close MFW: {e}"
            with open("ERROR.log", "a") as log_file:
                log_file.write(error_message + "\n")
            retry_count += 1
            if retry_count < max_retries:
                print("Failed to get permission, waiting 5 seconds before retrying...")
                time.sleep(5)
    if retry_count == max_retries and is_mfw_running():  # 达到最大重试次数且 MFW 仍在运行
        sys.exit("Failed to close MFW after multiple attempts")


for i in range(4, 0, -1):
    print(f"update in {i} seconds")
    time.sleep(1)

# 检查MFW-ChainFlow Assistant是否在运行,在运行的话尝试关闭
close_mfw_with_retry()

zip_file_name = os.path.join(os.getcwd(), "update.zip")

# 检查ZIP文件是否存在
if os.path.exists(zip_file_name):
    # 解压文件
    try:
        with zipfile.ZipFile(zip_file_name, "r") as zip_ref:
            for file_info in zip_ref.infolist():
                try:
                    zip_ref.extract(file_info, os.getcwd())
                    print(f"Extracted: {file_info.filename}")
                except PermissionError as e:
                    error_message = (
                        f"Permission denied while extracting {file_info.filename}: {e}"
                    )
                    with open("ERROR.log", "a") as log_file:
                        log_file.write(error_message + "\n")
    except zipfile.BadZipFile:
        error_message = f"file {zip_file_name} is not a zip file"
        if sys.platform.startswith("win32"):
            print(error_message)
            os.system("pause")
        elif sys.platform.startswith("darwin") or sys.platform.startswith("linux"):
            print(error_message)
            input("Press Enter to continue...")
        sys.exit(error_message)

# 删除ZIP文件
clear_zip_file()
if os.path.exists("changes.json"):
    import json

    with open("changes.json", "r") as f:
        changes: dict = json.load(f)
    delete_list = changes.get("deleted", [])
    for i in delete_list:
        try:
            os.remove(i)
            print(f"Deleted: {i}")
        except:
            error_message = f"failed to delete {i}"
            with open("ERROR.log", "a") as log_file:
                log_file.write(error_message + "\n")

# 重启程序
if sys.platform.startswith("win32"):
    subprocess.Popen(".\\MFW.exe")
elif sys.platform.startswith("darwin") or sys.platform.startswith("linux"):
    subprocess.Popen("./MFW")
else:
    sys.exit("Unsupported platform")
print("restart")
