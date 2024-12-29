import zipfile
import os
import time


def unzip_file(zip_path, extract_to):
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(extract_to)
        print(f"文件已成功解压到 {extract_to}")


for i in range(4):
    print(f"update will start in {i+1} seconds...")
    time.sleep(1)

# 假设你的ZIP文件位于同一目录下，或者你可以提供完整的路径
with open(os.path.join(os.getcwd(), "config", "version.txt"), "r") as version_file:
    version_data = version_file.read().split()

zip_file_name = f"MFW-PyQt6-{version_data[0]}-{version_data[1]}-{version_data[2]}.zip"

# 检查ZIP文件是否存在
if os.path.exists(zip_file_name):
    # 解压文件
    unzip_file(zip_file_name, os.getcwd())
else:
    error_message = f"文件 {zip_file_name} 不存在"
    with open("ERROR.log", "a") as log_file:
        log_file.write(error_message + "\n")
