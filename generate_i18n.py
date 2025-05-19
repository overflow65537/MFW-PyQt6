import os
import subprocess
import sys  # 改为导入 sys 模块

# 改为使用 sys.argv 手动获取参数
pylupdate6_path = 'pylupdate6'  # 默认值（环境变量中的路径）
if len(sys.argv) > 1:
    if len(sys.argv) > 2:
        print("错误：参数过多。使用方法：python generate_i18n.py [pylupdate6路径]")
        sys.exit(1)
    pylupdate6_path = sys.argv[1]  # 用户传递的路径
    #如果是文件夹
    if os.path.isdir(pylupdate6_path):
        pylupdate6_path = os.path.join(pylupdate6_path, "pylupdate6.exe")

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
    exclude_dir = os.path.join(project_root, "dist")
    python_files = []
    for root, dirs, files in os.walk(project_root):
        if exclude_dir in root:
            dirs[:] = []  # 跳过当前目录及其子目录
            continue
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))

    # 构建 pylupdate6 命令（使用用户指定的路径或默认值）
    command = [pylupdate6_path, '-ts', output_ts_file] + python_files  # 修改：使用手动获取的路径

    try:
        # 执行 pylupdate6 命令
        subprocess.run(command, check=True)
        print(f"成功生成 {output_ts_file} 文件。")
    except Exception as e:
        print(f"执行 pylupdate6 命令时出错: {e}")
