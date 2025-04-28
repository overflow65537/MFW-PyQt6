import os
import subprocess

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
        # 调用 lrelease 命令进行转换
        subprocess.run(["lrelease", ts_file_path], check=True)
        print(f"成功将 {ts_file} 转换为 {qm_file}")
    except subprocess.CalledProcessError as e:
        print(f"转换 {ts_file} 时出错: {e}")
