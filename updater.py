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

FULL_UPDATE_EXCLUDES = ["config", "debug", "update", "MFWUpdater1.exe", "MFWUpdate1"]


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
    while check_count < max_checks:
        if not is_mfw_running():
            return True
        print("MFW仍在运行，5秒后重新检查...")
        for sec in range(5, 0, -1):
            print(f"{sec}秒后重新检查...")
            time.sleep(1)
        check_count += 1

    # 如果MFW仍在运行，记录错误并退出
    if is_mfw_running():
        error_message = "更新失败：多次检查后MFW仍在运行"
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
    for path in target_files:
        try:
            if path.exists():
                path.unlink()
                update_logger.info("已清理更新 artifacts: %s", path)
        except Exception as exc:
            log_error(f"清理更新 artifacts 失败: {path} -> {exc}")


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
            abs_entry == ex or abs_entry.startswith(ex + os.sep)
            for ex in exclude_abs
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
            abs_entry == ex or abs_entry.startswith(ex + os.sep)
            for ex in exclude_abs
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


def apply_github_hotfix(package_path, keep_list):
    # 检查MFW是否在运行
    if not ensure_mfw_not_running():
        return False
    
    repo_root = os.getcwd()
    model_backup = backup_model_dir()
    skip_paths = {
        os.path.abspath(__file__),
        os.path.abspath(os.path.join(repo_root, "update")),
        os.path.abspath(os.path.join(repo_root, "file_list.txt")),
        os.path.abspath(package_path),
        os.path.abspath(os.path.join(repo_root, "update_back")),
    }
    success = False
    if safe_delete_except(
        keep_list,
        skip_paths,
        extra_keep=["config", "update", "debug", "file_list.txt"],
    ):
        success = extract_interface_folder(package_path)
    else:
        log_error("执行 GitHub 热更新的安全删除阶段失败")
    restore_model_dir(model_backup)
    return success


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
    package_path = (
        os.path.join(new_version_dir, package_name)
        if package_name
        else None
    )
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
        update_logger.warning(
            "更新尝试次数已大于3次，清理更新包与元数据"
        )
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
                success = perform_full_update(
                    package_path, metadata_path, metadata
                )
            else:
                success = apply_github_hotfix(package_path, file_list)
        elif source == "mirror":
            if mode == "full":
                success = perform_full_update(
                    package_path, metadata_path, metadata
                )
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
