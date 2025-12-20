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
import shutil
from pathlib import Path

def find_pyside6_tool(tool_name):
    """查找 PySide6 工具的位置"""
    # 首先尝试在 PATH 中查找
    tool_path = shutil.which(tool_name)
    if tool_path:
        return tool_path
    
    # 尝试查找 PySide6 安装目录
    try:
        import PySide6
        pyside6_path = Path(PySide6.__file__).parent
        # Windows
        if os.name == "nt":
            tool_exe = pyside6_path / f"{tool_name}.exe"
            if tool_exe.exists():
                return str(tool_exe)
        # Linux/Mac
        else:
            tool_path = pyside6_path / tool_name
            if tool_path.exists():
                return str(tool_path)
    except ImportError:
        pass
    
    return None

# 优先使用 lupdate（PySide6 中的实际工具名）
pylupdate6_path = find_pyside6_tool("lupdate")
if not pylupdate6_path:
    # 如果找不到 lupdate，尝试其他可能的名称
    pylupdate6_path = find_pyside6_tool("pyside6-lupdate") or find_pyside6_tool("pylupdate6")
    
# 如果自动搜索都找不到，使用默认名称（可能在 PATH 中）
if not pylupdate6_path:
    pylupdate6_path = "lupdate"
    print("警告: 未在 PySide6 安装目录中找到 lupdate 工具")
    print("  将尝试使用 PATH 中的 lupdate 工具")
    print()

# 支持命令行参数指定路径
if len(sys.argv) > 1:
    if len(sys.argv) > 2:
        print("错误：参数过多。使用方法：python generate_i18n.py [lupdate路径]")
        sys.exit(1)
    pylupdate6_path = sys.argv[1]  # 用户传递的路径
    # 如果是文件夹
    if os.path.isdir(pylupdate6_path):
        if os.name == "nt":  # Windows
            pylupdate6_path = os.path.join(pylupdate6_path, "lupdate.exe")
        else:  # Linux/Mac
            pylupdate6_path = os.path.join(pylupdate6_path, "lupdate")

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
    # 只扫描 app 目录（主要的应用代码）
    app_dir = os.path.join(project_root, "app")
    
    # 排除的目录
    exclude_dirs = [
        "__pycache__",
        "i18n",  # 排除翻译文件目录
    ]
    
    python_files = []
    if os.path.exists(app_dir):
        for root, dirs, files in os.walk(app_dir):
            # 跳过排除的目录
            rel_path = os.path.relpath(root, app_dir)
            if any(exclude_dir in rel_path.split(os.sep) for exclude_dir in exclude_dirs):
                dirs[:] = []  # 跳过当前目录及其子目录
                continue
            
            for file in files:
                if file.endswith(".py"):
                    file_path = os.path.join(root, file)
                    python_files.append(file_path)
    else:
        print(f"警告: 未找到 app 目录: {app_dir}")
        print("  将扫描整个项目目录...")
        # 如果 app 目录不存在，回退到扫描整个项目
        exclude_dirs_full = [
            "dist",
            "build",
            "__pycache__",
            ".git",
            ".venv",
            "venv",
            "env",
            "node_modules",
            "backup",
            "hotfix",
            "runtime",
            "tests",
        ]
        exclude_files = [
            "build_pyinstaller.py",
            "generate_i18n.py",
            "generate_custom_json.py",
            "lrelease.py",
            "find_i18n_tools.py",
            "updater.py",
            "main.py",  # 排除 main.py，因为 lupdate 可能无法处理
        ]
        
        for root, dirs, files in os.walk(project_root):
            rel_path = os.path.relpath(root, project_root)
            if any(exclude_dir in rel_path.split(os.sep) for exclude_dir in exclude_dirs_full):
                dirs[:] = []
                continue
            
            for file in files:
                if file.endswith(".py"):
                    file_path = os.path.join(root, file)
                    if os.path.dirname(file_path) == project_root and file in exclude_files:
                        continue
                    python_files.append(file_path)

    # 构建 lupdate 命令（使用用户指定的路径或默认值）
    command = [pylupdate6_path, "-ts", output_ts_file] + python_files

    print(f"使用工具: {pylupdate6_path}")
    print(f"扫描 {len(python_files)} 个 Python 文件...")
    
    try:
        # 执行 lupdate 命令
        result = subprocess.run(command, check=False, capture_output=True, text=True)
        
        # 检查是否成功生成了文件（即使有警告也可能成功）
        if os.path.exists(output_ts_file):
            print(f"[成功] 生成 {os.path.basename(output_ts_file)} 文件")
            # 如果有警告信息，显示但不作为错误
            if result.stderr and "error" in result.stderr.lower():
                # 过滤掉常见的可忽略错误
                errors = [line for line in result.stderr.split('\n') 
                         if 'error' in line.lower() and 'no recognized extension' not in line.lower()]
                if errors:
                    print(f"  警告: {errors[0]}")
        else:
            print(f"[失败] 未生成 {os.path.basename(output_ts_file)} 文件")
            if result.stderr:
                print(f"  错误信息: {result.stderr[:200]}")  # 只显示前200个字符
    except FileNotFoundError:
        print(f"[失败] 未找到工具: {pylupdate6_path}")
        print("  提示: 请确保已安装 PySide6")
        print("  可以通过以下方式解决:")
        print("  1. 确保 PySide6 已正确安装: pip install PySide6")
        print("  2. 通过命令行参数指定工具路径:")
        print("     python generate_i18n.py <lupdate完整路径>")
    except Exception as e:
        print(f"[失败] 执行 lupdate 命令时出错: {e}")
