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
MFW-ChainFlow Assistant i18n生成器
作者:overflow65537
"""

import os
import subprocess
import sys
import json  # 新增：导入 json 模块

# 改为使用 sys.argv 手动获取参数
pylupdate6_path = "pylupdate6"  # 默认值（环境变量中的路径）
if len(sys.argv) > 1:
    if len(sys.argv) > 2:
        print("错误：参数过多。使用方法：python generate_i18n.py [pylupdate6路径]")
        sys.exit(1)
    pylupdate6_path = sys.argv[1]  # 用户传递的路径
    # 如果是文件夹
    if os.path.isdir(pylupdate6_path):
        pylupdate6_path = os.path.join(pylupdate6_path, "pylupdate6.exe")

# 项目根目录
project_root = os.getcwd()

# 输出的 .ts 文件路径
output_ts_files = [
    os.path.join(project_root, "app", "i18n", "i18n.zh_CN.ts"),
    os.path.join(project_root, "app", "i18n", "i18n.zh_HK.ts"),
]

# 创建 translations 目录（如果不存在）
for output_ts_file in output_ts_files:
    translations_dir = os.path.dirname(output_ts_file)
    if not os.path.exists(translations_dir):
        os.makedirs(translations_dir)

    # 查找项目内所有的 Python 文件
    exclude_dir = os.path.join(project_root, "dist")
    python_files = []
    for root, dirs, files in os.walk(project_root):
        if exclude_dir in root:
            dirs[:] = []  # 跳过当前目录及其子目录
            continue
        for file in files:
            if file.endswith(".py"):
                python_files.append(os.path.join(root, file))

    # 构建 pylupdate6 命令（使用用户指定的路径或默认值）
    command = [pylupdate6_path, "-ts", output_ts_file] + python_files

    try:
        # 执行 pylupdate6 命令
        subprocess.run(command, check=True)
        print(f"成功生成 {output_ts_file} 文件。")
    except Exception as e:
        print(f"首次执行 pylupdate6 命令时出错: {e}")
        print("尝试从 i18n.json 文件中读取 pylupdate6 路径...")
        # 定义 i18n.json 文件路径
        i18n_json_path = os.path.join(project_root, "i18n.json")
        if os.path.exists(i18n_json_path):
            try:
                with open(i18n_json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if "pylupdate6" in data:
                        pylupdate6_path = data["pylupdate6"]
                        # 如果是文件夹
                        if os.path.isdir(pylupdate6_path):
                            pylupdate6_path = os.path.join(
                                pylupdate6_path, "pylupdate6.exe"
                            )
                        # 重新构建命令
                        command = [
                            pylupdate6_path,
                            "-ts",
                            output_ts_file,
                        ] + python_files
                        try:
                            # 再次执行 pylupdate6 命令
                            subprocess.run(command, check=True)
                            print(
                                f"使用 i18n.json 中的路径成功生成 {output_ts_file} 文件。"
                            )
                        except Exception as e:
                            print(
                                f"使用 i18n.json 中的路径执行 pylupdate6 命令时仍然出错: {e}"
                            )
                    else:
                        print("i18n.json 文件中未找到 'pylupdate6' 字段。")
            except Exception as e:
                print(f"读取 i18n.json 文件出错: {e}")
        else:
            print("i18n.json 文件不存在。")
