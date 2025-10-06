import os
import sys
import shutil


def is_mfw_running():
    import psutil

    try:
        if sys.platform.startswith("win32"):
            for proc in psutil.process_iter(["name"]):
                if proc.info["name"] == "MFW.exe":
                    return True
        elif sys.platform.startswith("darwin") or sys.platform.startswith("linux"):
            for proc in psutil.process_iter(["name"]):
                if proc.info["name"] == "MFW":
                    return True
        return False
    except psutil.Error:
        return False


def move_specific_files_to_temp_backup(update_file_path):
    """
    只将更新包中会覆盖的文件移动到临时备份目录

    Args:
        update_file_path: 更新包路径

    Returns:
        tuple: (临时目录路径, 移动成功的文件列表, 移动失败的文件列表)
    """
    current_dir = os.getcwd()
    import tempfile
    import zipfile

    temp_backup_dir = tempfile.mkdtemp(prefix="mfw_backup_")
    moved_files = []
    failed_files = []

    print(f"创建临时备份目录: {temp_backup_dir}")

    try:
        # 获取更新包中的文件列表
        with zipfile.ZipFile(update_file_path, "r") as zip_ref:
            update_files = zip_ref.namelist()

        # 只备份更新包中会覆盖的文件
        for file_info in update_files:
            file_path = os.path.join(current_dir, file_info)
            
            # 检查文件是否存在
            if os.path.exists(file_path):
                backup_path = os.path.join(temp_backup_dir, file_info)
                
                # 确保备份目录结构存在
                backup_dir = os.path.dirname(backup_path)
                if backup_dir and not os.path.exists(backup_dir):
                    os.makedirs(backup_dir)
                
                try:
                    # 移动文件到临时备份目录
                    shutil.move(file_path, backup_path)
                    moved_files.append(file_info)
                    print(f"已备份: {file_info}")
                except Exception as e:
                    failed_files.append((file_info, str(e)))
                    print(f"备份失败: {file_info} - {e}")

        return temp_backup_dir, moved_files, failed_files

    except Exception as e:
        print(f"备份过程出错: {e}")
        return temp_backup_dir, moved_files, failed_files


def restore_files_from_backup(backup_dir):
    """
    从备份目录恢复文件到当前目录

    Args:
        backup_dir: 备份目录路径
    """
    current_dir = os.getcwd()

    try:
        if os.path.exists(backup_dir):
            # 恢复备份文件
            for root, dirs, files in os.walk(backup_dir):
                # 计算相对路径
                rel_path = os.path.relpath(root, backup_dir)
                target_root = current_dir if rel_path == "." else os.path.join(current_dir, rel_path)
                
                # 确保目标目录存在
                if not os.path.exists(target_root):
                    os.makedirs(target_root)
                
                # 恢复文件
                for file in files:
                    backup_path = os.path.join(root, file)
                    target_path = os.path.join(target_root, file)
                    
                    # 如果目标文件已存在，先删除
                    if os.path.exists(target_path):
                        if os.path.isdir(target_path):
                            shutil.rmtree(target_path)
                        else:
                            os.remove(target_path)

                    # 移动文件回原位置
                    shutil.move(backup_path, target_path)
                    print(f"已恢复: {os.path.join(rel_path, file) if rel_path != '.' else file}")

            # 删除备份目录
            shutil.rmtree(backup_dir)
            print("备份目录已清理")

    except Exception as e:
        print(f"恢复文件时出错: {e}")


def extract_zip_file_with_validation(update_file_path):
    """
    解压指定的压缩文件，使用循环逐个文件解压并验证

    Args:
        update_file_path: 要解压的压缩文件的路径

    Returns:
        bool: 解压是否成功
    """
    import zipfile

    current_dir = os.getcwd()

    try:
        print(f"开始解压文件: {update_file_path}")
        print(f"解压目标目录: {current_dir}")

        # 创建备份并移动当前文件（只备份更新包中会覆盖的文件）
        backup_dir, moved_files, failed_files = move_specific_files_to_temp_backup(update_file_path)

        # 如果有文件备份失败，记录日志并恢复
        if failed_files:
            error_msg = f"备份文件失败，无法继续更新。失败的文件: {failed_files}"
            log_error(error_msg)

            # 恢复已备份的文件
            restore_files_from_backup(backup_dir)
            return False

        try:
            # 尝试解压zip文件
            if update_file_path.endswith(".zip"):
                with zipfile.ZipFile(update_file_path, "r") as zip_ref:
                    file_list = zip_ref.namelist()
                    print(f"找到 {len(file_list)} 个文件需要解压")

                    # 逐个文件解压
                    for file_info in file_list:
                        try:
                            # 解压单个文件
                            zip_ref.extract(file_info, current_dir)
                            extracted_path = os.path.join(current_dir, file_info)
                            # 如果解压的文件名是MFW或者MFWUpdater,添加可执行权限
                            if sys.platform != "win32" and (
                                file_info == "MFW" or file_info == "MFWUpdater"
                            ):
                                os.chmod(extracted_path, 0o755)

                            # 验证文件是否成功解压
                            if os.path.exists(extracted_path):
                                print(f"✓ 已解压: {file_info}")
                            else:
                                raise Exception(f"文件解压后不存在: {file_info}")

                        except Exception as e:
                            error_msg = f"解压文件失败: {file_info} - {e}"
                            log_error(error_msg)

                            # 恢复备份文件
                            restore_files_from_backup(backup_dir)
                            return False

            else:
                error_msg = f"不支持的文件格式: {update_file_path}"
                log_error(error_msg)
                restore_files_from_backup(backup_dir)
                return False

            # 解压成功，清理备份目录
            if os.path.exists(backup_dir):
                shutil.rmtree(backup_dir)
                print("解压完成，备份目录已清理")

            return True

        except Exception as e:
            error_msg = f"解压过程出错: {e}"
            log_error(error_msg)

            # 恢复备份文件
            restore_files_from_backup(backup_dir)
            return False

    except Exception as e:
        error_msg = f"解压准备过程出错: {e}"
        log_error(error_msg)
        return False


def log_error(error_message):
    """
    记录错误日志

    Args:
        error_message: 错误信息
    """
    import time

    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {error_message}\n"

    with open("UPDATE_ERROR.log", "a", encoding="utf-8") as log_file:
        log_file.write(log_entry)

    print(f"错误已记录: {error_message}")


def standard_update():
    """
    标准更新模式
    """
    import subprocess
    import time

    # 检查MFW是否在运行
    max_checks = 3
    check_count = 0
    while check_count < max_checks:
        if not is_mfw_running():
            break
        print("MFW仍在运行，5秒后重新检查...")
        for sec in range(5, 0, -1):
            print(f"{sec}秒后重新检查...")
            time.sleep(1)
        check_count += 1

    # 如果MFW仍在运行，记录错误并退出
    if is_mfw_running():
        error_message = "更新失败：多次检查后MFW仍在运行"
        log_error(error_message)
        sys.exit(error_message)

    zip_file_name = os.path.join(os.getcwd(), "update.zip")
    update1_zip_name = os.path.join(os.getcwd(), "update1.zip")

    # 检查并解压更新文件
    update_file = None
    if os.path.exists(zip_file_name):
        update_file = zip_file_name

    if update_file:
        # 使用新的解压方法
        if extract_zip_file_with_validation(update_file):
            print("更新文件解压成功")

            # 重命名更新文件为备份文件
            if os.path.exists(update_file):
                os.rename(update_file, update1_zip_name)
                print(f"更新文件已重命名为: {update1_zip_name}")
        else:
            error_message = "更新文件解压失败，更新已中止"
            log_error(error_message)
            sys.exit(error_message)
    else:
        print("未找到更新文件")

    # 重启程序
    print("重启MFW程序...")
    if sys.platform.startswith("win32"):
        subprocess.Popen(".\\MFW.exe")
    elif sys.platform.startswith("darwin"):
        subprocess.Popen("./MFW")
    elif sys.platform.startswith("linux"):
        subprocess.Popen("./MFW")
    else:
        sys.exit("不支持的操作系统")


def recovery_mode():
    """
    恢复模式
    """
    import subprocess

    input("按回车键开始恢复更新...")

    update1_zip_name = os.path.join(os.getcwd(), "update1.zip")

    # 检查并解压备份的更新文件
    update_file = None
    if os.path.exists(update1_zip_name):
        update_file = update1_zip_name

    if update_file:
        if extract_zip_file_with_validation(update_file):
            print("恢复更新成功")
        else:
            error_message = "恢复更新失败"
            log_error(error_message)
            sys.exit(error_message)
    else:
        print("未找到恢复更新文件")

    # 重启程序
    if sys.platform.startswith("win32"):
        subprocess.Popen(".\\MFW.exe")
    elif sys.platform.startswith("darwin") or sys.platform.startswith("linux"):
        subprocess.Popen("./MFW")
    else:
        sys.exit("不支持的操作系统")
    print("程序已重启")


if __name__ == "__main__":
    # 清理错误日志
    if os.path.exists("UPDATE_ERROR.log"):
        os.remove("UPDATE_ERROR.log")

    if len(sys.argv) > 1 and sys.argv[1] == "-update":
        standard_update()
    else:
        mode = input("1. 更新模式 / Standard update\n2. 恢复模式 / Recovery update\n")
        if mode == "1":
            standard_update()
        elif mode == "2":
            recovery_mode()
        else:
            print("无效输入 / Invalid input")
            input("按回车键继续... / Press Enter to continue...")