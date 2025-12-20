import json
import logging
import os
import random
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Tuple
from uuid import uuid4

FULL_UPDATE_EXCLUDES = [
    "config",
    "bundle",
    "backup",
    "hotfix",
    "release_notes",
    "debug",
    "update",
    "MFWUpdater1.exe",
    "MFWUpdate1",
]


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


def ensure_mfw_not_running():
    """
    确保MFW不在运行，如果正在运行则等待或退出
    返回True表示可以继续，False表示应该退出
    """
    max_checks = 3
    check_count = 0
    update_logger.info(f"[步骤1] 检查MFW进程状态（最多检查{max_checks}次）...")
    
    while check_count < max_checks:
        if not is_mfw_running():
            update_logger.info(f"[步骤1] MFW进程未运行，可以继续更新")
            return True
        check_count += 1
        update_logger.warning(f"[步骤1] MFW仍在运行（第{check_count}/{max_checks}次检查），5秒后重新检查...")
        print("MFW仍在运行，5秒后重新检查...")
        for sec in range(5, 0, -1):
            print(f"{sec}秒后重新检查...")
            time.sleep(1)

    # 如果MFW仍在运行，记录错误并退出
    if is_mfw_running():
        error_message = f"更新失败：经过{max_checks}次检查后MFW仍在运行，无法继续更新"
        update_logger.error(f"[步骤1] {error_message}")
        log_error(error_message)
        print(error_message)
        sys.exit(error_message)

    return True


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

    # 检查MFW是否在运行
    if not ensure_mfw_not_running():
        return False

    if not update_file_path.lower().endswith(".zip"):
        log_error(f"不支持的文件格式: {update_file_path}")
        return False

    current_dir = os.getcwd()
    extract_dir = Path(tempfile.mkdtemp(prefix="mfw_unpack_"))
    try:
        with zipfile.ZipFile(update_file_path, "r") as archive:
            file_list = archive.namelist()
            print(f"找到 {len(file_list)} 个文件需要解压")
            for file_info in file_list:
                try:
                    archive.extract(file_info, extract_dir)
                    extracted_path = extract_dir / file_info
                    if not extracted_path.exists():
                        raise Exception(f"文件解压后不存在: {file_info}")
                    if sys.platform != "win32" and file_info in {"MFW", "MFWUpdater"}:
                        os.chmod(extracted_path, 0o755)
                    print(f"✓ 已解压: {file_info}")
                except Exception as exc:
                    raise Exception(f"提取 {file_info} 失败: {exc}") from exc
        for root, dirs, files in os.walk(extract_dir):
            rel_root = os.path.relpath(root, extract_dir)
            dest_root = (
                os.path.join(current_dir, rel_root)
                if rel_root not in (".", "")
                else current_dir
            )
            os.makedirs(dest_root, exist_ok=True)
            for d in dirs:
                os.makedirs(os.path.join(dest_root, d), exist_ok=True)
            for file in files:
                src_file = os.path.join(root, file)
                dest_file = os.path.join(dest_root, file)
                os.makedirs(os.path.dirname(dest_file), exist_ok=True)
                shutil.copy2(src_file, dest_file)
                if sys.platform != "win32" and os.path.basename(dest_file) in {
                    "MFW",
                    "MFWUpdater",
                }:
                    os.chmod(dest_file, 0o755)
                print(f"✓ 已复制: {dest_file}")
        return True
    except Exception as exc:
        log_error(f"解压过程出错: {exc}")
        cleanup_update_artifacts(update_file_path)
        start_mfw_process()
        return False
    finally:
        shutil.rmtree(extract_dir, ignore_errors=True)


def log_error(error_message):
    """
    记录错误日志。

    仅使用 update_logger 记录即可，无需手动写文件。
    """
    print(f"错误已记录: {error_message}")
    update_logger.error(error_message)


def start_mfw_process():
    try:
        if sys.platform.startswith("win32"):
            subprocess.Popen(".\\MFW.exe")
        else:
            subprocess.Popen("./MFW")
    except Exception as exc:
        log_error(f"启动MFW程序失败: {exc}")


def cleanup_update_artifacts(update_file_path, metadata_path=None):
    target_files = [Path(update_file_path)]
    if metadata_path:
        target_files.append(Path(metadata_path))
    else:
        target_files.append(Path(update_file_path).parent / "update_metadata.json")
    
    update_logger.debug(f"[步骤6] 准备清理 {len(target_files)} 个更新文件...")
    cleaned_count = 0
    for path in target_files:
        try:
            if path.exists():
                path.unlink()
                update_logger.info(f"[步骤6] 已清理更新文件: {path}")
                cleaned_count += 1
            else:
                update_logger.debug(f"[步骤6] 文件不存在，跳过清理: {path}")
        except Exception as exc:
            update_logger.error(f"[步骤6] 清理更新文件失败: {path} -> {exc}")
            log_error(f"清理更新 artifacts 失败: {path} -> {exc}")
    
    update_logger.debug(f"[步骤6] 更新文件清理完成，共清理 {cleaned_count}/{len(target_files)} 个文件")


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


def generate_metadata_samples(target_dir: str | Path | None = None):
    if target_dir is None:
        target_dir = os.path.join(os.getcwd(), "update", "new_version")
    os.makedirs(target_dir, exist_ok=True)
    combos = [
        ("github", "full"),
        ("github", "hotfix"),
        ("mirror", "full"),
        ("mirror", "hotfix"),
    ]
    for source, mode in combos:
        package_name = f"{source}_{mode}_{uuid4().hex[:8]}.zip"
        metadata = {
            "source": source,
            "mode": mode,
            "version": f"v{uuid4().hex[:6]}",
            "package_name": package_name,
            "download_time": datetime.utcnow().isoformat() + "Z",
            "attempts": random.randint(1, 3),
        }
        file_name = f"metadata_{uuid4().hex}.json"
        path = os.path.join(target_dir, file_name)
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            print(f"生成元数据: {path}")
        except Exception as exc:
            log_error(f"写入元数据失败: {exc}")


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


def save_update_metadata(metadata_path: str, metadata: dict) -> None:
    try:
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
    except Exception as exc:
        log_error(f"写入更新元数据失败: {exc}")


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


@dataclass
class SafeDeleteResult:
    success: bool
    backups: List[Tuple[str, str]]
    backup_dir: str | None


def _copy_to_backup(abs_path, backup_root, root):
    if not os.path.exists(abs_path):
        return None
    rel = os.path.relpath(abs_path, root)
    backup_path = os.path.join(backup_root, rel)
    os.makedirs(os.path.dirname(backup_path), exist_ok=True)
    if os.path.isdir(abs_path):
        if os.path.exists(backup_path):
            shutil.rmtree(backup_path)
        shutil.copytree(abs_path, backup_path)
    else:
        shutil.copy2(abs_path, backup_path)
    return abs_path, backup_path


def _restore_from_backup(backups):
    for src, backup in reversed(backups):
        try:
            if not os.path.exists(backup):
                continue
            if os.path.isdir(backup):
                if os.path.exists(src):
                    shutil.rmtree(src)
                shutil.copytree(backup, src, dirs_exist_ok=False)
            else:
                os.makedirs(os.path.dirname(src), exist_ok=True)
                if os.path.exists(src):
                    os.remove(src)
                shutil.copy2(backup, src)
        except Exception as exc:
            log_error(f"恢复 {src} 失败: {exc}")


def _cleanup_root_except(exclude_relatives):
    root = os.getcwd()
    exclude_abs = {
        os.path.abspath(os.path.join(root, rel)) for rel in exclude_relatives if rel
    }
    for entry in os.listdir(root):
        abs_entry = os.path.abspath(os.path.join(root, entry))
        if any(
            abs_entry == ex or abs_entry.startswith(ex + os.sep) for ex in exclude_abs
        ):
            continue
        if os.path.isdir(abs_entry):
            shutil.rmtree(abs_entry, ignore_errors=True)
        else:
            try:
                os.remove(abs_entry)
            except FileNotFoundError:
                pass


def safe_delete_all_except(exclude_relatives):
    root = os.getcwd()
    exclude_abs = {
        os.path.abspath(os.path.join(root, rel)) for rel in exclude_relatives if rel
    }
    delete_candidates = []
    for entry in os.listdir(root):
        abs_entry = os.path.abspath(os.path.join(root, entry))
        if any(
            abs_entry == ex or abs_entry.startswith(ex + os.sep) for ex in exclude_abs
        ):
            continue
        delete_candidates.append(abs_entry)

    backup_dir = tempfile.mkdtemp(prefix="mfw_delete_backup_")
    backups: List[Tuple[str, str]] = []
    try:
        for abs_entry in delete_candidates:
            if not os.path.exists(abs_entry):
                continue
            backup_entry = _copy_to_backup(abs_entry, backup_dir, root)
            if backup_entry:
                backups.append(backup_entry)
        for abs_entry in delete_candidates:
            if not os.path.exists(abs_entry):
                continue
            if os.path.isdir(abs_entry):
                shutil.rmtree(abs_entry)
            else:
                os.remove(abs_entry)
        return SafeDeleteResult(True, backups, backup_dir)
    except Exception as exc:
        log_error(f"安全删除失败: {exc}")
        _restore_from_backup(backups)
        shutil.rmtree(backup_dir, ignore_errors=True)
        return SafeDeleteResult(False, [], None)


def _extract_zip_to_temp(zip_path: Path):
    import zipfile

    temp_dir = Path(tempfile.mkdtemp(prefix="mfw_full_extract_"))
    try:
        with zipfile.ZipFile(zip_path, "r", metadata_encoding="utf-8") as archive:
            archive.extractall(temp_dir)
        return temp_dir
    except Exception as exc:
        log_error(f"解压更新包到临时目录失败: {exc}")
        shutil.rmtree(temp_dir, ignore_errors=True)
        return None


def _copy_temp_to_root(temp_dir: Path):
    current_dir = os.getcwd()
    for root_dir, dirs, files in os.walk(temp_dir):
        rel_root = os.path.relpath(root_dir, temp_dir)
        dest_root = (
            os.path.join(current_dir, rel_root)
            if rel_root not in (".", "")
            else current_dir
        )
        os.makedirs(dest_root, exist_ok=True)
        for d in dirs:
            os.makedirs(os.path.join(dest_root, d), exist_ok=True)
        for file in files:
            src_file = os.path.join(root_dir, file)
            dest_file = os.path.join(dest_root, file)
            os.makedirs(os.path.dirname(dest_file), exist_ok=True)
            shutil.copy2(src_file, dest_file)
            if sys.platform != "win32" and os.path.basename(dest_file) in {
                "MFW",
                "MFWUpdater",
            }:
                os.chmod(dest_file, 0o755)


def _increment_attempts(metadata: dict, metadata_path: str):
    metadata["attempts"] = metadata.get("attempts", 0) + 1
    try:
        save_update_metadata(metadata_path, metadata)
    except Exception as exc:
        log_error(f"更新尝试次数记录失败: {exc}")


def _handle_full_update_failure(
    package_path: str,
    metadata_path: str,
    metadata: dict,
    backups: List[Tuple[str, str]] | None = None,
):
    if backups:
        _cleanup_root_except(FULL_UPDATE_EXCLUDES)
        _restore_from_backup(backups)
    _increment_attempts(metadata, metadata_path)
    start_mfw_process()


def perform_full_update(package_path: str, metadata_path: str, metadata: dict) -> bool:
    # 检查MFW是否在运行
    if not ensure_mfw_not_running():
        return False

    metadata = metadata or {}
    temp_dir = _extract_zip_to_temp(Path(package_path))
    if not temp_dir:
        _handle_full_update_failure(package_path, metadata_path, metadata)
        return False

    delete_result = safe_delete_all_except(FULL_UPDATE_EXCLUDES)
    if not delete_result.success:
        shutil.rmtree(temp_dir, ignore_errors=True)
        _handle_full_update_failure(package_path, metadata_path, metadata)
        return False

    try:
        _copy_temp_to_root(temp_dir)
    except Exception as exc:
        log_error(f"覆盖目录失败: {exc}")
        _handle_full_update_failure(
            package_path, metadata_path, metadata, delete_result.backups
        )
        if delete_result.backup_dir:
            shutil.rmtree(delete_result.backup_dir, ignore_errors=True)
        return False
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

    if delete_result.backup_dir:
        shutil.rmtree(delete_result.backup_dir, ignore_errors=True)
    return True


def safe_delete_paths(relative_paths):
    root = os.getcwd()
    backup_dir = tempfile.mkdtemp(prefix="mfw_delete_backup_")
    backups = []
    try:
        for rel_path in relative_paths:
            abs_path = os.path.abspath(os.path.join(root, rel_path))
            if not abs_path.startswith(root) or not os.path.exists(abs_path):
                continue
            backup_entry = _copy_to_backup(abs_path, backup_dir, root)
            if backup_entry:
                backups.append(backup_entry)
            if os.path.isdir(abs_path):
                shutil.rmtree(abs_path)
            else:
                os.remove(abs_path)
        shutil.rmtree(backup_dir, ignore_errors=True)
        return True
    except Exception as exc:
        log_error(f"删除失败: {exc}")
        _restore_from_backup(backups)
        shutil.rmtree(backup_dir, ignore_errors=True)
        return False


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

    delete_candidates = []
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
        delete_candidates.append(abs_entry)

    backup_dir = tempfile.mkdtemp(prefix="mfw_delete_backup_")
    backups = []
    try:
        for abs_entry in delete_candidates:
            if not os.path.exists(abs_entry):
                continue
            backup_entry = _copy_to_backup(abs_entry, backup_dir, root)
            if backup_entry:
                backups.append(backup_entry)
        for abs_entry in delete_candidates:
            if not os.path.exists(abs_entry):
                continue
            if os.path.isdir(abs_entry):
                shutil.rmtree(abs_entry)
            else:
                os.remove(abs_entry)
        shutil.rmtree(backup_dir, ignore_errors=True)
        return True
    except Exception as exc:
        log_error(f"安全删除失败: {exc}")
        _restore_from_backup(backups)
        shutil.rmtree(backup_dir, ignore_errors=True)
        return False


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
                if sys.platform != "win32" and relative_path in {"MFW", "MFWUpdater"}:
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
                deleted = data.get("deleted", [])
                modified = data.get("modified", [])
                entries: list[str] = []
                if isinstance(deleted, list):
                    entries.extend(deleted)
                if isinstance(modified, list):
                    entries.extend(modified)
                return entries
    except Exception as exc:
        log_error(f"读取 change.json 失败: {exc}")
        return None


def _get_bundle_path_from_metadata(metadata: dict) -> str | None:
    """
    从 metadata 中获取 bundle 路径。
    尝试从常见位置查找 bundle 路径。
    """
    update_logger.debug("[步骤4] 开始从 metadata 和 interface 配置中获取 bundle 路径...")
    # 尝试从 interface.json 中获取
    repo_root = os.getcwd()
    interface_paths = [
        os.path.join(repo_root, "interface.json"),
        os.path.join(repo_root, "interface.jsonc"),
    ]
    for interface_path in interface_paths:
        if os.path.exists(interface_path):
            update_logger.debug(f"[步骤4] 找到 interface 文件: {interface_path}")
            try:
                with open(interface_path, "r", encoding="utf-8") as f:
                    interface_data = json.load(f)
                    # 假设 bundle 路径在当前目录或 bundle 目录下
                    bundle_name = interface_data.get("name", "")
                    if bundle_name:
                        update_logger.debug(f"[步骤4] 从 interface 配置中获取到 bundle 名称: {bundle_name}")
                        bundle_paths = [
                            os.path.join(repo_root, "bundle", bundle_name),
                            os.path.join(repo_root, bundle_name),
                        ]
                        for bp in bundle_paths:
                            if os.path.exists(bp):
                                update_logger.debug(f"[步骤4] 找到 bundle 路径: {bp}")
                                return bp
                        update_logger.warning(f"[步骤4] bundle 名称存在但路径不存在: {bundle_paths}")
                    else:
                        update_logger.warning(f"[步骤4] interface 配置中未找到 bundle 名称 (name 字段)")
            except Exception as exc:
                update_logger.warning(f"[步骤4] 读取 interface 文件失败: {interface_path} -> {exc}")
                pass
    update_logger.warning("[步骤4] 未找到有效的 interface 配置文件或 bundle 路径")
    return None


def _read_config_file(config_path: str) -> dict:
    """
    读取指定路径的JSON/JSONC配置文件。
    基于 app/utils/update.py 中的实现。
    """
    if not os.path.exists(config_path):
        return {}
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            # 尝试使用 jsonc，如果不可用则使用 json
            try:
                import jsonc

                return jsonc.load(f)
            except ImportError:
                return json.load(f)
    except Exception as exc:
        update_logger.error(f"读取配置文件失败 {config_path}: {exc}")
        return {}


def _extract_zip_to_hotfix_dir(zip_path: str, extract_to: str) -> str | None:
    """
    解压 zip 文件到指定目录，自动查找 interface.json 并返回解压后的根目录。
    基于 app/utils/update.py 中的 extract_zip 实现。

    Args:
        zip_path: zip 文件路径
        extract_to: 解压目标目录

    Returns:
        str | None: 解压后的根目录路径，如果失败返回 None
    """
    import zipfile

    update_logger.info(f"[步骤3] 开始解压更新包: {zip_path} -> {extract_to}")
    extract_to_path = Path(extract_to)
    extract_to_path.mkdir(parents=True, exist_ok=True)
    update_logger.debug(f"[步骤3] 创建/确认解压目标目录: {extract_to_path}")

    interface_names = {"interface.json", "interface.jsonc"}

    try:
        with zipfile.ZipFile(zip_path, "r", metadata_encoding="utf-8") as archive:
            members = archive.namelist()
            total_files = len(members)
            update_logger.info(f"[步骤3] 打开更新包成功，包含 {total_files} 个文件/目录")

            # 查找 interface.json 或 interface.jsonc
            update_logger.debug("[步骤3] 查找 interface.json/interface.jsonc 文件...")
            interface_dir_parts = None
            for member in members:
                member_path = Path(member.replace("\\", "/"))
                if member_path.name.lower() in interface_names:
                    # 获取 interface 文件所在的目录
                    interface_dir_parts = member_path.parent.parts
                    update_logger.info(f"[步骤3] 找到 interface 文件: {member}，所在目录: {'/'.join(interface_dir_parts)}")
                    break
            
            if not interface_dir_parts:
                update_logger.warning("[步骤3] 未在更新包中找到 interface.json/interface.jsonc 文件，将解压所有文件")

            # 解压文件
            update_logger.info("[步骤3] 开始解压文件...")
            extracted_count = 0
            for member in members:
                member_path = Path(member.replace("\\", "/"))
                member_parts = tuple(p for p in member_path.parts if p and p != ".")

                # 如果找到了 interface 目录，只解压该目录下的文件
                if interface_dir_parts:
                    if member_parts[: len(interface_dir_parts)] != interface_dir_parts:
                        continue
                    # 移除 interface 目录前缀
                    relative_parts = member_parts[len(interface_dir_parts) :]
                else:
                    relative_parts = member_parts

                if not relative_parts:
                    continue

                target_path = extract_to_path.joinpath(*relative_parts)
                if member.endswith("/"):
                    target_path.mkdir(parents=True, exist_ok=True)
                else:
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    with archive.open(member) as source, open(
                        target_path, "wb"
                    ) as target:
                        shutil.copyfileobj(source, target)
                    extracted_count += 1
                    if extracted_count % 100 == 0:
                        update_logger.debug(f"[步骤3] 已解压 {extracted_count} 个文件...")

            update_logger.info(f"[步骤3] 文件解压完成，共解压 {extracted_count} 个文件")

            # 返回解压后的根目录
            if interface_dir_parts:
                return str(extract_to_path)
            return str(extract_to_path)
    except Exception as exc:
        update_logger.exception(f"[步骤3] 解压文件失败 {zip_path} -> {extract_to}: {exc}")
        return None


def apply_github_hotfix(package_path, metadata=None):
    """
    应用 GitHub 热更新。
    基于 app/utils/update.py:1339-1412 的逻辑实现。
    更新器只负责读取元数据并应用更新，不进行下载或远程检查。
    主程序已经下载了更新包并判断过可以热更新，更新器只需要应用即可。

    Args:
        package_path: 更新包路径（从元数据中获取）
        metadata: 更新元数据，包含 source、mode、version 等信息

    Returns:
        bool: 更新是否成功
    """
    update_logger.info("=" * 50)
    update_logger.info("[GitHub热更新] 开始执行热更新流程")
    update_logger.info(f"[GitHub热更新] 更新包路径: {package_path}")
    
    # 检查MFW是否在运行
    update_logger.info("[步骤1] 检查MFW进程状态...")
    if not ensure_mfw_not_running():
        update_logger.error("[步骤1] MFW进程检查失败，无法继续更新")
        return False
    update_logger.info("[步骤1] MFW进程检查通过，可以继续更新")

    # 验证元数据
    update_logger.info("[步骤2] 验证更新元数据...")
    if not metadata:
        update_logger.warning("[步骤2] 缺少更新元数据，无法执行热更新")
        return False
    
    version = metadata.get("version", "")
    package_name = metadata.get("package_name", "unknown")
    update_logger.info(f"[步骤2] 元数据验证通过 - 版本: {version}, 包名: {package_name}")

    update_logger.info(
        f"[步骤3] 准备解压更新包: 版本={version}, 包名={package_name}"
    )

    # 步骤3: 解压更新包到 hotfix 目录
    hotfix_dir = os.path.join(os.getcwd(), "hotfix")
    update_logger.info(f"[步骤3] 准备解压到 hotfix 目录: {hotfix_dir}")
    hotfix_root = _extract_zip_to_hotfix_dir(package_path, hotfix_dir)
    if not hotfix_root:
        update_logger.error("[步骤3] 解压更新包失败")
        return False
    update_logger.info(f"[步骤3] 更新包解压完成，根目录: {hotfix_root}")

    # 步骤4: 获取 bundle 路径
    update_logger.info("[步骤4] 获取 Bundle 路径...")
    bundle_path = _get_bundle_path_from_metadata(metadata)
    if not bundle_path:
        update_logger.warning("[步骤4] Bundle 配置不存在，跳过热更新")
        return False
    bundle_path_obj = Path(bundle_path)
    update_logger.info(f"[步骤4] Bundle 路径获取成功: {bundle_path_obj}")

    # 步骤5: 使用安全覆盖模式进行热更新
    update_logger.info("[步骤5] 使用安全覆盖模式进行热更新")
    project_path = bundle_path_obj
    if not os.path.exists(hotfix_root):
        update_logger.error("[步骤5] hotfix 目录不存在，无法覆盖")
        return False
    update_logger.info(f"[步骤5] 验证 hotfix 目录存在: {hotfix_root}")

    # 备份并删除资源文件中的 pipeline 目录，以供后续无损覆盖
    resource_backup_dir = Path.cwd() / "backup" / "resource"
    update_logger.info(f"[步骤5] 创建资源备份目录: {resource_backup_dir}")
    resource_backup_dir.mkdir(parents=True, exist_ok=True)

    # 读取 interface.json 获取 resource 列表
    update_logger.info("[步骤5] 读取 interface 配置文件...")
    interface_paths = [
        bundle_path_obj / "interface.jsonc",
        bundle_path_obj / "interface.json",
    ]
    interface_data = {}
    for path in interface_paths:
        if path.exists():
            update_logger.info(f"[步骤5] 找到 interface 文件: {path}")
            interface_data = _read_config_file(str(path))
            if interface_data:
                update_logger.info(f"[步骤5] 成功读取 interface 配置")
                break
    if not interface_data:
        update_logger.warning("[步骤5] 未找到有效的 interface 配置文件")

    resource_list = interface_data.get("resource", [])
    resource_count = len(resource_list)
    update_logger.info(f"[步骤5] 获取到 {resource_count} 个资源配置项")
    known_resources: list[str] = []
    resource_backups: list[tuple[Path, Path]] = []

    try:
        update_logger.info("[步骤5] 开始备份资源目录和清理 pipeline 目录...")
        backup_count = 0
        for resource in resource_list:
            for resource_path_str in resource.get("path", []):
                resource_path = Path(resource_path_str.replace("{PROJECT_DIR}", "."))
                if resource_path.is_dir() and (
                    resource_path_str not in known_resources
                ):
                    backup_target = resource_backup_dir / resource_path.name
                    try:
                        # 先备份资源
                        update_logger.info(f"[步骤5] 备份资源目录: {resource_path} -> {backup_target}")
                        if backup_target.is_dir():
                            shutil.rmtree(backup_target)
                        shutil.copytree(str(resource_path), str(backup_target))
                        update_logger.info(f"[步骤5] 资源目录备份完成: {resource_path}")

                        resource_backups.append((resource_path, backup_target))
                        known_resources.append(resource_path_str)
                        backup_count += 1

                        # 再删除旧的 pipeline 目录，避免影响后续覆盖
                        pipeline_path = resource_path / "pipeline"
                        if pipeline_path.exists():
                            update_logger.info(f"[步骤5] 删除旧 pipeline 目录: {pipeline_path}")
                            shutil.rmtree(str(pipeline_path))
                            update_logger.info(f"[步骤5] pipeline 目录删除完成: {pipeline_path}")
                    except Exception as backup_err:
                        update_logger.exception(
                            f"[步骤5] 备份或清理资源目录时出错: {resource_path} -> {backup_err}"
                        )
                        raise
        update_logger.info(f"[步骤5] 资源备份和清理完成，共处理 {backup_count} 个资源目录")

        update_logger.info(f"[步骤5] 开始覆盖项目目录: {hotfix_root} -> {project_path}")
        # 允许目标目录已存在（Python 3.8+ 支持 dirs_exist_ok）
        # 这样在 bundle 目录本身已存在时不会因 WinError 183 直接失败
        shutil.copytree(hotfix_root, project_path, dirs_exist_ok=True)
        update_logger.info(f"[步骤5] 项目目录覆盖完成: {project_path}")

        # 更新 interface.jsonc 中的版本号
        update_logger.info(f"[步骤5] 开始更新 interface 配置文件中的版本号为: {version}")
        version_updated = False
        for path in interface_paths:
            if path.exists():
                interface = _read_config_file(str(path))
                if interface:
                    old_version = interface.get("version", "unknown")
                    interface["version"] = version
                    try:
                        import jsonc

                        with open(path, "w", encoding="utf-8") as f:
                            jsonc.dump(interface, f, indent=4, ensure_ascii=False)
                    except ImportError:
                        with open(path, "w", encoding="utf-8") as f:
                            json.dump(interface, f, indent=4, ensure_ascii=False)
                    update_logger.info(f"[步骤5] 版本号更新成功: {path.name} ({old_version} -> {version})")
                    version_updated = True
                    break
        if not version_updated:
            update_logger.warning("[步骤5] 未能更新 interface 配置文件中的版本号")
        else:
            update_logger.info("[步骤5] interface 配置同步完毕")

        # 步骤5: 完成
        update_logger.info("[步骤5] 热更新文件操作成功完成!")
        update_logger.info("=" * 50)

        # 步骤6: 清理更新数据
        update_logger.info("[步骤6] 开始清理更新数据...")
        download_dir = Path(package_path).parent
        metadata_file = str(download_dir / "update_metadata.json")
        update_logger.info(f"[步骤6] 准备清理: 更新包={package_path}, 元数据={metadata_file}")
        cleanup_update_artifacts(package_path, metadata_file)
        update_logger.info("[步骤6] 更新数据清理完成")
        update_logger.info("=" * 50)
        update_logger.info("[GitHub热更新] 热更新流程全部完成!")
        update_logger.info("=" * 50)

        return True

    except Exception as e:
        # 资源目录异常回滚
        update_logger.error(f"[步骤5] 热更新过程中出现错误: {e}")
        if resource_backups:
            update_logger.warning(f"[步骤5] 更新失败，正在恢复 {len(resource_backups)} 个资源备份目录...")
            restore_count = 0
            for original_path, backup_path in reversed(resource_backups):
                try:
                    if not backup_path.exists():
                        update_logger.warning(f"[步骤5] 备份路径不存在，跳过恢复: {backup_path}")
                        continue
                    update_logger.info(f"[步骤5] 恢复资源目录: {backup_path} -> {original_path}")
                    # 清理已被部分覆盖/删除的原目录
                    if original_path.exists():
                        if original_path.is_file():
                            original_path.unlink()
                        else:
                            shutil.rmtree(original_path)
                    # 使用备份进行还原
                    if backup_path.is_dir():
                        shutil.copytree(backup_path, original_path)
                    else:
                        original_path.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(backup_path, original_path)
                    update_logger.info(f"[步骤5] 资源目录恢复成功: {original_path}")
                    restore_count += 1
                except Exception as restore_err:
                    update_logger.exception(
                        f"[步骤5] 恢复资源目录失败: {original_path} -> {restore_err}"
                    )
            update_logger.info(f"[步骤5] 资源备份恢复完成，成功恢复 {restore_count}/{len(resource_backups)} 个目录")
        else:
            update_logger.warning("[步骤5] 没有需要恢复的资源备份")
        update_logger.exception("[GitHub热更新] 热更新失败，详细信息:")
        update_logger.error("=" * 50)
        return False
    finally:
        # 清理资源备份目录
        if resource_backup_dir.exists():
            try:
                update_logger.info(f"[步骤5] 清理资源备份目录: {resource_backup_dir}")
                shutil.rmtree(resource_backup_dir)
                update_logger.info("[步骤5] 资源备份目录清理完成")
            except Exception as cleanup_err:
                update_logger.warning(f"[步骤5] 清理资源备份目录失败: {cleanup_err}")


def apply_mirror_hotfix(package_path):
    # 检查MFW是否在运行
    if not ensure_mfw_not_running():
        return False

    deletes = load_change_entries(package_path)
    if deletes is None:
        return False
    if not safe_delete_paths(deletes):
        log_error("执行镜像热更新的安全删除阶段失败")
        return False
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
    if not ensure_mfw_not_running():
        return

    new_version_dir, update_back_dir = ensure_update_directories()
    metadata_path = os.path.join(new_version_dir, "update_metadata.json")
    metadata = load_update_metadata(new_version_dir)
    if metadata:
        metadata["attempts"] = metadata.get("attempts", 0) + 1
        save_update_metadata(metadata_path, metadata)
    file_list_path = os.path.join(os.getcwd(), "file_list.txt")
    file_list = read_file_list(file_list_path)
    update_logger.info(
        "读取更新信息：metadata=%s, file_list=%s",
        metadata,
        file_list,
    )

    package_name = metadata.get("package_name") if metadata else None
    package_path = os.path.join(new_version_dir, package_name) if package_name else None
    if not package_path or not os.path.isfile(package_path):
        package_path = find_latest_zip_file(new_version_dir)

    if not package_path:
        print("未找到更新文件，清理元数据并启动MFW")
        # 删除元数据文件
        if os.path.exists(metadata_path):
            try:
                os.remove(metadata_path)
                update_logger.info("已删除元数据文件: %s", metadata_path)
            except Exception as exc:
                log_error(f"删除元数据文件失败: {exc}")
        # 启动MFW程序
        start_mfw_process()
        # 自身退出
        sys.exit(0)

    if metadata and metadata.get("attempts", 0) > 3:
        update_logger.warning("更新尝试次数已大于3次，清理更新包与元数据")
        if package_path and os.path.exists(package_path):
            os.remove(package_path)
        if os.path.exists(metadata_path):
            os.remove(metadata_path)
        sys.exit("更新尝试次数超过限制，已清理旧更新包")

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
                success = perform_full_update(package_path, metadata_path, metadata)
            else:
                success = apply_github_hotfix(package_path, metadata)
        elif source == "mirror":
            if mode == "full":
                success = perform_full_update(package_path, metadata_path, metadata)
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

    update_logger.info("恢复模式开始")
    # 检查MFW是否在运行
    if not ensure_mfw_not_running():
        return

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
        if len(sys.argv) > 1:
            if sys.argv[1] == "-update":
                standard_update()
            elif sys.argv[1] == "-generate-metadata":
                target = sys.argv[2] if len(sys.argv) > 2 else None
                generate_metadata_samples(target)
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

        input("按回车键退出... / Press Enter to exit...")
        sys.exit(1)
