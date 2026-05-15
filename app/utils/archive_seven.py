#   This file is part of MFW-ChainFlow Assistant.
#
#   SPDX-License-Identifier: GPL-3.0-or-later

"""7z / 7-Zip SFX 归档检测与解压（依赖 py7zr）。"""

from __future__ import annotations

from pathlib import Path, PurePosixPath
from typing import Callable

from app.utils.logger import logger


def import_py7zr():
    try:
        import py7zr

        return py7zr
    except ImportError:
        return None


def path_readable_by_py7zr(path: Path | str) -> bool:
    """路径是否为 py7zr 可打开的 7z 归档（含 7-Zip 自解压 exe）。"""
    py7zr = import_py7zr()
    if py7zr is None:
        return False
    try:
        with py7zr.SevenZipFile(Path(path), mode="r") as archive:
            archive.getnames()
        return True
    except Exception:
        return False


def extract_all_7z_to_directory(archive_path: Path | str, dest: Path) -> bool:
    """将 7z / 7z SFX 全部解压到 dest。"""
    py7zr = import_py7zr()
    if py7zr is None:
        return False
    dest.mkdir(parents=True, exist_ok=True)
    try:
        with py7zr.SevenZipFile(Path(archive_path), mode="r") as archive:
            archive.extractall(path=str(dest))
        return True
    except Exception as exc:
        logger.debug("extract_all_7z_to_directory 失败: %s", exc)
        return False


def extract_7z_filtered_tree(
    archive_path: Path,
    extract_to_path: Path,
    *,
    interface_names: set[str],
    normalize_parts: Callable[[tuple[str, ...]], tuple[str, ...]],
) -> Path | None:
    """
    按与 zip 热更新一致的方式解压：仅保留包含 interface 的目录树；
    解压后 final_root 为 interface 所在目录（与 BaseUpdate._perform_archive_extraction 一致）。
    """
    py7zr = import_py7zr()
    if py7zr is None:
        return None
    extract_to_path.mkdir(parents=True, exist_ok=True)
    interface_names_lower = {n.lower() for n in interface_names}
    try:
        with py7zr.SevenZipFile(archive_path, mode="r") as sz:
            raw_names = sz.getnames()
            names_norm = [n.replace("\\", "/") for n in raw_names]

            interface_dir_parts: tuple[str, ...] | None = None
            for mn in names_norm:
                mp = PurePosixPath(mn)
                if mp.name.lower() in interface_names_lower:
                    interface_dir_parts = normalize_parts(mp.parent.parts)
                    break

            targets: list[str] = []
            for raw, mn in zip(raw_names, names_norm):
                if mn.endswith("/"):
                    continue
                mp = PurePosixPath(mn)
                member_parts = normalize_parts(mp.parts)
                if interface_dir_parts:
                    if member_parts[: len(interface_dir_parts)] != interface_dir_parts:
                        continue
                targets.append(raw)

            if interface_dir_parts and not targets:
                return None

            if targets:
                sz.extract(path=str(extract_to_path), targets=targets)
            else:
                sz.extract(path=str(extract_to_path))

            if interface_dir_parts:
                return extract_to_path.joinpath(*interface_dir_parts)
            return extract_to_path
    except Exception:
        logger.exception("extract_7z_filtered_tree 失败: %s", archive_path)
        return None


def extract_7z_hotfix_flat(
    archive_path: Path | str,
    extract_to_path: Path,
    *,
    interface_names: set[str],
) -> bool:
    """
    与 updater._extract_zip_to_hotfix_dir 一致：去掉 interface 目录前缀，将子树铺到 extract_to_path。
    """
    py7zr = import_py7zr()
    if py7zr is None:
        return False
    extract_to_path.mkdir(parents=True, exist_ok=True)
    interface_names_lower = {n.lower() for n in interface_names}
    archive_path = Path(archive_path)
    try:
        with py7zr.SevenZipFile(archive_path, mode="r") as archive:
            raw_names = archive.getnames()
            members = [n.replace("\\", "/") for n in raw_names]

            interface_dir_parts: tuple[str, ...] | None = None
            for member in members:
                member_path = Path(member)
                if member_path.name.lower() in interface_names_lower:
                    interface_dir_parts = tuple(
                        p for p in member_path.parent.parts if p and p != "."
                    )
                    break

            for raw, member in zip(raw_names, members):
                member_path = Path(member)
                member_parts = tuple(p for p in member_path.parts if p and p != ".")
                if interface_dir_parts:
                    if member_parts[: len(interface_dir_parts)] != interface_dir_parts:
                        continue
                    relative_parts = member_parts[len(interface_dir_parts) :]
                else:
                    relative_parts = member_parts
                if not relative_parts:
                    continue
                if member.endswith("/"):
                    extract_to_path.joinpath(*relative_parts).mkdir(
                        parents=True, exist_ok=True
                    )
                    continue
                data = archive.read([raw])
                bio = data.get(raw)
                if bio is None:
                    for k, v in data.items():
                        if k.replace("\\", "/") == member:
                            bio = v
                            break
                if bio is None:
                    continue
                target_path = extract_to_path.joinpath(*relative_parts)
                target_path.parent.mkdir(parents=True, exist_ok=True)
                with open(target_path, "wb") as out_f:
                    bio.seek(0)
                    out_f.write(bio.read())
        return True
    except Exception:
        logger.exception("extract_7z_hotfix_flat 失败: %s", archive_path)
        return False
