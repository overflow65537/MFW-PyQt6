import zipfile
import os
import time
import sys
import subprocess


def clear_zip_file():
    try:
        if os.path.exists(zip_file_name):
            os.remove(zip_file_name)
            print(f"Deleted: {zip_file_name}")
    except:
        error_message = f"failed to delete {zip_file_name}"
        with open("ERROR.log", "a") as log_file:
            log_file.write(error_message + "\n")


# 倒计时从4秒开始，逐秒减少到1秒
for i in range(4, 0, -1):
    print(f"update will start in {i} seconds...")
    time.sleep(1)

# 读取版本文件
with open(os.path.join(os.getcwd(), "config", "version.txt"), "r") as version_file:
    version_data = version_file.read().split()

zip_file_name = os.path.join(os.getcwd(), "update.zip")

# 检查ZIP文件是否存在
if os.path.exists(zip_file_name):
    # 解压文件
    try:
        with zipfile.ZipFile(zip_file_name, "r") as zip_ref:
            for file_info in zip_ref.infolist():
                zip_ref.extract(file_info, os.getcwd())
                print(f"Extracted: {file_info.filename}")
    except zipfile.BadZipFile:
        error_message = f"file {zip_file_name} is not a zip file"
        with open("ERROR.log", "a") as log_file:
            log_file.write(error_message + "\n")
        clear_zip_file()

else:
    error_message = f"file {zip_file_name} not found"
    with open("ERROR.log", "a") as log_file:
        log_file.write(error_message + "\n")

# 删除ZIP文件
clear_zip_file()


# 重启程序
if sys.platform.startswith("win32"):
    subprocess.Popen(".\\MFW.exe")
elif sys.platform.startswith("linux"):
    subprocess.Popen("./MFW.bin")
elif sys.platform.startswith("darwin"):
    subprocess.Popen("./MFW")
else:
    sys.exit("Unsupported platform")
print("restart")
