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
MFW-ChainFlow Assistant i18n 翻译脚本
作者:overflow65537
"""


import os
import subprocess
import sys  # 新增：导入 sys 模块

# 新增：通过 sys.argv 获取 lrelease 路径（默认使用系统中的 lrelease）
lrelease_path = "lrelease.exe"  # 默认值
if len(sys.argv) > 1:
    if len(sys.argv) > 2:
        print("错误：参数过多。使用方法：python lrelease.py [lrelease路径]")
        sys.exit(1)
    lrelease_path = sys.argv[1]  # 用户指定的路径
    # 如果是文件夹
    if os.path.isdir(lrelease_path):
        lrelease_path = os.path.join(lrelease_path, "lrelease.exe")

# 获取当前脚本所在的目录
current_dir = os.path.dirname(os.path.abspath(__file__))

# 定义要转换的 .ts 文件列表
ts_files = ["i18n.zh_CN.ts", "i18n.zh_HK.ts"]

# 遍历每个 .ts 文件
for ts_file in ts_files:
    # 构建完整的 .ts 文件路径
    ts_file_path = os.path.join(current_dir, ts_file)
    qm_file = os.path.splitext(ts_file)[0] + ".qm"

    try:
        # 调用用户指定或默认的 lrelease 路径进行转换
        print(f"路径:{lrelease_path}")
        subprocess.run([lrelease_path, ts_file_path], check=True)
        print(f"成功将 {ts_file} 转换为 {qm_file}")
    except subprocess.CalledProcessError as e:
        print(f"转换 {ts_file} 时出错: {e}")
