"""本地更新包暂存：与在线全量包共用 update/new_version 路径。"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import jsonc
import shutil

from app.utils.logger import logger


def path_is_zip_backed_archive(path: Path | str) -> bool:
    """
    判断路径是否为可直接用 zipfile 打开的归档：
    - .zip 视为是；
    - .exe 则尝试打开（ZIP 尾结构的自解压包）。
    """
    import zipfile

    p = Path(path)
    name_lower = p.name.lower()
    if name_lower.endswith(".zip"):
        return True
    if name_lower.endswith(".exe"):
        try:
            with zipfile.ZipFile(p, "r", metadata_encoding="utf-8") as zf:
                zf.namelist()
            return True
        except (zipfile.BadZipFile, OSError):
            return False
    return False


def path_is_update_archive_readable(path: Path | str) -> bool:
    """本地/更新器可识别的更新包：zip、tar.gz/tgz、.7z、ZIP 型 exe、7z SFX exe。"""
    from app.utils.archive_seven import path_readable_by_py7zr

    p = Path(path)
    nl = p.name.lower()
    if nl.endswith(".zip"):
        return True
    if nl.endswith((".tar.gz", ".tgz")):
        return True
    if nl.endswith(".7z"):
        return path_readable_by_py7zr(p)
    if nl.endswith(".exe"):
        if path_is_zip_backed_archive(p):
            return True
        return path_readable_by_py7zr(p)
    return False


def local_update_package_dir() -> Path:
    """全量更新包落盘目录（与在线下载一致）。"""
    return Path.cwd() / "update" / "new_version"


def local_update_package_name_for_source(source: Path) -> str:
    """与在线全量包对齐：zip 统一为 update.zip；其它格式保留原名以便识别。"""
    name_lower = source.name.lower()
    if name_lower.endswith(".zip") or path_is_zip_backed_archive(source):
        return "update.zip"
    return source.name


def write_local_update_metadata(
    download_dir: Path,
    *,
    source: str,
    mode: str,
    version: str | None,
    attempts: int,
    package_name: str,
) -> Path:
    """写入 update/new_version/update_metadata.json。"""
    data = {
        "source": source,
        "mode": mode,
        "version": str(version) if version else "",
        "package_name": package_name,
        "download_time": datetime.utcnow().isoformat() + "Z",
        "attempts": attempts,
    }
    metadata_path = download_dir / "update_metadata.json"
    with open(metadata_path, "w", encoding="utf-8") as f:
        jsonc.dump(data, f, indent=2, ensure_ascii=False)
    return metadata_path


def stage_local_update_package(
    source_path: Path | str,
    *,
    version: str | None = None,
) -> Path:
    """将本地更新压缩包复制到全量包目录并写入元数据，供外部更新器安装。

    目标路径与在线全量下载一致：``update/new_version/``（zip 固定为 ``update.zip``）。
    """
    source = Path(source_path)
    if not source.is_file():
        raise FileNotFoundError(f"update package not found: {source}")
    if not path_is_update_archive_readable(source):
        raise ValueError(f"unsupported update archive: {source.name}")

    target_dir = local_update_package_dir()
    target_dir.mkdir(parents=True, exist_ok=True)

    package_name = local_update_package_name_for_source(source)
    target_path = target_dir / package_name

    for existing in target_dir.iterdir():
        if not existing.is_file():
            continue
        if existing.resolve() == source.resolve():
            continue
        try:
            existing.unlink()
            logger.info("已清理旧更新文件: %s", existing)
        except Exception as exc:
            logger.warning("清理旧更新文件失败: %s -> %s", existing, exc)

    if source.resolve() != target_path.resolve():
        shutil.copy2(source, target_path)
        logger.info("已暂存本地更新包: %s -> %s", source, target_path)
        try:
            if (
                source.parent.resolve() == target_dir.resolve()
                and source.exists()
                and source.resolve() != target_path.resolve()
            ):
                source.unlink()
                logger.info("已移除目标目录内的源文件副本: %s", source)
        except Exception as exc:
            logger.warning("移除目标目录内源文件失败: %s -> %s", source, exc)
    else:
        logger.info("本地更新包已在目标位置: %s", target_path)

    metadata_path = write_local_update_metadata(
        target_dir,
        source="local",
        mode="full",
        version=version or "",
        attempts=0,
        package_name=package_name,
    )
    logger.info("已写入本地更新元数据: %s", metadata_path)
    return target_path
