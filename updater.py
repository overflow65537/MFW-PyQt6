import zipfile
import os
import time
import sys
import subprocess


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
    with zipfile.ZipFile(zip_file_name, "r") as zip_ref:
        zip_ref.extractall(os.getcwd())

else:
    error_message = f"file {zip_file_name} not found"
    with open("ERROR.log", "a") as log_file:
        log_file.write(error_message + "\n")

# 清除ZIP文件
if os.path.exists(zip_file_name):
    os.remove(zip_file_name)

# 重启程序
if sys.platform == "win32":
    os.system(".\\MFW.exe")
elif sys.platform == "linux":
    os.system("./MFW.bin")
elif sys.platform == "darwin":
    os.system("./MFW")
