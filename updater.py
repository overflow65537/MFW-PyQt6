import json
import logging
import os
import shutil
import sys
import tempfile
import time
from pathlib import Path


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
                target_root = (
                    current_dir
                    if rel_path == "."
                    else os.path.join(current_dir, rel_path)
                )

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
                    print(
                        f"已恢复: {os.path.join(rel_path, file) if rel_path != '.' else file}"
                    )

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
        backup_dir, moved_files, failed_files = move_specific_files_to_temp_backup(
            update_file_path
        )

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
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {error_message}\n"

    with open("UPDATE_ERROR.log", "a", encoding="utf-8") as log_file:
        log_file.write(log_entry)

    print(f"错误已记录: {error_message}")
    update_logger.error(error_message)


def ensure_update_directories():
    """
    确保 update/new_version 和 update/update_back 存在，并返回路径
    """
    update_root = os.path.join(os.getcwd(), "update")
    new_version_dir = os.path.join(update_root, "new_version")
    update_back_dir = os.path.join(update_root, "update_back")
    os.makedirs(new_version_dir, exist_ok=True)
    os.makedirs(update_back_dir, exist_ok=True)
    return new_version_dir, update_back_dir


def setup_update_logger():
    debug_dir = Path("debug")
    debug_dir.mkdir(exist_ok=True)
    index_file = debug_dir / "run_index.txt"
    try:
        current = int(index_file.read_text().strip() or "0")
    except Exception:
        current = 0
    current = (current % 5) + 1
    index_file.write_text(str(current))
    log_path = debug_dir / f"updater_{current}.log"
    if log_path.exists():
        log_path.unlink()
    logger = logging.getLogger("updater")
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()
    handler = logging.FileHandler(log_path, encoding="utf-8")
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger


update_logger = setup_update_logger()


def load_update_metadata(update_dir):
    metadata_path = os.path.join(update_dir, "update_metadata.json")
    if not os.path.exists(metadata_path):
        return {}
    try:
        with open(metadata_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as exc:
        log_error(f"读取更新元数据失败: {exc}")
        return {}


def read_file_list(file_list_path):
    entries = []
    if not os.path.exists(file_list_path):
        return entries
    try:
        with open(file_list_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                entries.append(line)
    except Exception as exc:
        log_error(f"读取 file_list.txt 失败: {exc}")
    return entries


def safe_delete_paths(relative_paths):
    root = os.getcwd()
    for rel_path in relative_paths:
        abs_path = os.path.abspath(os.path.join(root, rel_path))
        if not abs_path.startswith(root):
            continue
        try:
            if os.path.isdir(abs_path):
                shutil.rmtree(abs_path)
            elif os.path.exists(abs_path):
                os.remove(abs_path)
        except Exception as exc:
            log_error(f"删除 {abs_path} 失败: {exc}")


def safe_delete_except(keep_relative_paths, skip_paths=None, extra_keep=None):
    root = os.getcwd()
    keep_abs = set()
    for rel_path in keep_relative_paths:
        abs_path = os.path.abspath(os.path.join(root, rel_path))
        keep_abs.add(abs_path)
        dirname = os.path.abspath(os.path.dirname(abs_path))
        if dirname and dirname != root:
            keep_abs.add(dirname)
    for rel_path in extra_keep or []:
        abs_path = os.path.abspath(os.path.join(root, rel_path))
        keep_abs.add(abs_path)
        if os.path.isdir(abs_path):
            keep_abs.add(os.path.abspath(abs_path))
    skip_abs = {os.path.abspath(path) for path in (skip_paths or [])}
    for entry in os.listdir(root):
        abs_entry = os.path.abspath(os.path.join(root, entry))
        if abs_entry in skip_abs:
            continue
        if any(
            abs_entry == keep_path or abs_entry.startswith(keep_path + os.sep)
            for keep_path in keep_abs
            if keep_path
        ):
            continue
        try:
            if os.path.isdir(abs_entry):
                shutil.rmtree(abs_entry)
            else:
                os.remove(abs_entry)
        except Exception as exc:
            log_error(f"安全删除 {abs_entry} 失败: {exc}")


def backup_model_dir():
    repo_root = os.getcwd()
    model_path = os.path.join(repo_root, "model")
    if not os.path.isdir(model_path):
        return None
    backup_root = tempfile.mkdtemp(prefix="mfw_model_backup_")
    backup_model = os.path.join(backup_root, "model")
    try:
        shutil.copytree(model_path, backup_model)
        return backup_root
    except Exception as exc:
        log_error(f"备份 model 目录失败: {exc}")
        shutil.rmtree(backup_root, ignore_errors=True)
        return None


def restore_model_dir(backup_root):
    if not backup_root or not os.path.isdir(backup_root):
        return
    backup_model = os.path.join(backup_root, "model")
    if not os.path.isdir(backup_model):
        shutil.rmtree(backup_root, ignore_errors=True)
        return
    target = os.path.join(os.getcwd(), "model")
    if os.path.exists(target):
        shutil.rmtree(target)
    try:
        shutil.copytree(backup_model, target)
    except Exception as exc:
        log_error(f"恢复 model 目录失败: {exc}")
    finally:
        shutil.rmtree(backup_root, ignore_errors=True)


def extract_interface_folder(zip_path):
    import zipfile

    repo_root = os.getcwd()
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            interface_member = next(
                (
                    name
                    for name in zf.namelist()
                    if os.path.basename(name).lower()
                    in {"interface.json", "interface.jsonc"}
                ),
                None,
            )
            if not interface_member:
                log_error("未在更新包中找到 interface.json/ interface.jsonc")
                return False

            interface_dir = os.path.dirname(interface_member)
            prefix = f"{interface_dir.rstrip('/')}/" if interface_dir else ""

            for member in zf.namelist():
                if prefix and not member.startswith(prefix):
                    continue
                relative_path = member[len(prefix) :] if prefix else member
                if not relative_path:
                    continue
                target_path = os.path.join(repo_root, relative_path)
                if member.endswith("/"):
                    os.makedirs(target_path, exist_ok=True)
                    continue
                os.makedirs(os.path.dirname(target_path), exist_ok=True)
                with zf.open(member) as source, open(target_path, "wb") as target:
                    shutil.copyfileobj(source, target)
                if (
                    sys.platform != "win32"
                    and relative_path in {"MFW", "MFWUpdater"}
                ):
                    os.chmod(target_path, 0o755)
        return True
    except Exception as exc:
        log_error(f"解压 interface 文件夹失败: {exc}")
        return False


def load_change_entries(zip_path):
    import zipfile

    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            candidate = next(
                (
                    name
                    for name in zf.namelist()
                    if os.path.basename(name).lower() in {"change.json", "changes.json"}
                ),
                None,
            )
            if not candidate:
                log_error("更新包中未包含 change.json/changes.json")
                return None
            with zf.open(candidate) as change_file:
                data = json.load(change_file)
                return data.get("deleted", [])
    except Exception as exc:
        log_error(f"读取 change.json 失败: {exc}")
        return None


def apply_github_hotfix(package_path, keep_list):
    repo_root = os.getcwd()
    model_backup = backup_model_dir()
    skip_paths = {
        os.path.abspath(__file__),
        os.path.abspath(os.path.join(repo_root, "update")),
        os.path.abspath(os.path.join(repo_root, "file_list.txt")),
        os.path.abspath(os.path.join(repo_root, "UPDATE_ERROR.log")),
        os.path.abspath(package_path),
        os.path.abspath(os.path.join(repo_root, "update_back")),
    }
    safe_delete_except(
        keep_list,
        skip_paths,
        extra_keep=["config", "update", "debug"],
    )
    success = extract_interface_folder(package_path)
    restore_model_dir(model_backup)
    return success


def apply_mirror_hotfix(package_path):
    deletes = load_change_entries(package_path)
    if deletes is None:
        return False
    safe_delete_paths(deletes)
    return extract_zip_file_with_validation(package_path)



def find_latest_zip_file(directory):
    """
    查找目录中最新的 zip 包
    """
    try:
        candidates = [
            os.path.join(directory, file_name)
            for file_name in os.listdir(directory)
            if os.path.isfile(os.path.join(directory, file_name))
            and file_name.lower().endswith(".zip")
        ]
        if not candidates:
            return None
        return max(candidates, key=os.path.getmtime)
    except FileNotFoundError:
        return None
    except Exception as e:
        log_error(f"查找更新包时出错: {e}")
        return None


def move_update_archive_to_backup(src_path, backup_dir, metadata_path=None):
    """
    将更新包移动到备份目录，避免名称冲突
    """
    base_name = os.path.basename(src_path)
    dest_path = os.path.join(backup_dir, base_name)
    if os.path.exists(dest_path):
        name, ext = os.path.splitext(base_name)
        dest_path = os.path.join(
            backup_dir,
            f"{name}_{time.strftime('%Y%m%d%H%M%S')}{ext}",
        )
    try:
        shutil.move(src_path, dest_path)
        print(f"更新包已移入备份目录: {dest_path}")
        if metadata_path and os.path.exists(metadata_path):
            metadata_dest = os.path.join(backup_dir, f"{base_name}.metadata.json")
            shutil.move(metadata_path, metadata_dest)
            print(f"更新元数据已随包移动: {metadata_dest}")
    except Exception as e:
        log_error(f"移动更新包到备份目录失败: {e}")


def standard_update():
    """
    标准更新模式
    """
    import subprocess

    update_logger.info("标准更新模式开始")
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

    new_version_dir, update_back_dir = ensure_update_directories()
    metadata = load_update_metadata(new_version_dir)
    file_list_path = os.path.join(os.getcwd(), "file_list.txt")
    file_list = read_file_list(file_list_path)
    update_logger.info(
        "读取更新信息：metadata=%s, file_list=%s",
        metadata,
        file_list,
    )

    package_name = metadata.get("package_name") if metadata else None
    package_path = (
        os.path.join(new_version_dir, package_name)
        if package_name
        else None
    )
    if not package_path or not os.path.isfile(package_path):
        package_path = find_latest_zip_file(new_version_dir)

    if not package_path:
        print("未找到更新文件")
        sys.exit("未找到更新文件")

    source = metadata.get("source", "unknown") if metadata else "unknown"
    mode = metadata.get("mode", "full") if metadata else "full"
    version = metadata.get("version", "")
    print(
        f"检测到更新包: {os.path.basename(package_path)} "
        f"来源: {source} 模式: {mode} 版本: {version}"
    )

    success = False
    if metadata:
        if source == "github":
            if mode == "full":
                safe_delete_paths(file_list)
                success = extract_zip_file_with_validation(package_path)
            else:
                success = apply_github_hotfix(package_path, file_list)
        elif source == "mirror":
            if mode == "full":
                safe_delete_paths(file_list)
                success = extract_zip_file_with_validation(package_path)
            else:
                success = apply_mirror_hotfix(package_path)
        else:
            success = extract_zip_file_with_validation(package_path)
    else:
        success = extract_zip_file_with_validation(package_path)

    if success:
        print("更新文件处理完成")
        metadata_path = os.path.join(new_version_dir, "update_metadata.json")
        move_update_archive_to_backup(
            package_path, update_back_dir, metadata_path=metadata_path
        )
    else:
        error_message = "更新文件处理失败"
        log_error(error_message)
        sys.exit(error_message)

    # 重启程序
    print("重启MFW程序...")
    try:
        if sys.platform.startswith("win32"):
            subprocess.Popen(".\\MFW.exe")
        elif sys.platform.startswith("darwin"):
            subprocess.Popen("./MFW")
        elif sys.platform.startswith("linux"):
            subprocess.Popen("./MFW")
        else:
            error_message = "不支持的操作系统"
            log_error(error_message)
            sys.exit(error_message)
    except Exception as e:
        error_message = f"启动MFW程序失败: {e}"
        log_error(error_message)
        print(error_message)
        sys.exit(error_message)


def recovery_mode():
    """
    恢复模式
    """
    import subprocess

    input("按回车键开始恢复更新...")

    _, update_back_dir = ensure_update_directories()
    update_file = find_latest_zip_file(update_back_dir)

    update_logger.info("恢复模式开始, update_file=%s", update_file)

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
    try:
        if sys.platform.startswith("win32"):
            subprocess.Popen(".\\MFW.exe")
        elif sys.platform.startswith("darwin") or sys.platform.startswith("linux"):
            subprocess.Popen("./MFW")
        else:
            error_message = "不支持的操作系统"
            log_error(error_message)
            sys.exit(error_message)
        print("程序已重启")
    except Exception as e:
        error_message = f"启动MFW程序失败: {e}"
        log_error(error_message)
        print(error_message)
        sys.exit(error_message)


if __name__ == "__main__":
    # 不再启动时删除旧日志，而是追加写入（便于排查历史错误）
    # 在日志中记录本次更新开始
    import time

    log_entry = (
        f"\n{'='*60}\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] 更新程序启动\n{'='*60}\n"
    )
    update_logger.info("更新程序启动, argv=%s", sys.argv)
    try:
        with open("UPDATE_ERROR.log", "a", encoding="utf-8") as log_file:
            log_file.write(log_entry)
    except Exception:
        pass  # 如果无法写入日志文件，继续执行

    try:
        if len(sys.argv) > 1 and sys.argv[1] == "-update":
            standard_update()
        else:
            mode = input(
                "1. 更新模式 / Standard update\n2. 恢复模式 / Recovery update\n"
            )
            if mode == "1":
                standard_update()
            elif mode == "2":
                recovery_mode()
            else:
                print("无效输入 / Invalid input")
                input("按回车键继续... / Press Enter to continue...")
    except Exception as e:
        # 捕获所有未处理的异常并记录
        error_message = f"更新程序发生未捕获的异常: {type(e).__name__}: {e}"
        log_error(error_message)
        print(f"\n{error_message}")
        print("\n更新失败，请查看 UPDATE_ERROR.log 了解详情")
        input("按回车键退出... / Press Enter to exit...")
        sys.exit(1)
