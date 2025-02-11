import os
import subprocess

# 项目根目录
project_root = os.getcwd()

# 输出的 .ts 文件路径
output_ts_files = [
    os.path.join(project_root, 'MFW_resource', 'i18n', 'i18n.zh_CN.ts'),
    os.path.join(project_root, 'MFW_resource', 'i18n', 'i18n.zh_HK.ts'),
]

# 创建 translations 目录（如果不存在）
for output_ts_file in output_ts_files:
    translations_dir = os.path.dirname(output_ts_file)
    if not os.path.exists(translations_dir):
        os.makedirs(translations_dir)

    # 查找项目内所有的 Python 文件
    python_files = []
    for root, dirs, files in os.walk(project_root):
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))

    # 构建 pylupdate6 命令
    command = ['pylupdate6', '-ts', output_ts_file] + python_files

    try:
        # 执行 pylupdate6 命令
        subprocess.run(command, check=True)
        print(f"成功生成 {output_ts_file} 文件。")
    except subprocess.CalledProcessError as e:
        print(f"执行 pylupdate6 命令时出错: {e}")
    except FileNotFoundError:
        print("未找到 pylupdate6 命令，请确保 PyQt6 或 PySide6 已安装。")
