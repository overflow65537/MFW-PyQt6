"""热更新解压辅助：除 interface 目录外，同步提取与 interface 同级的 agent 目录。"""

from __future__ import annotations

import shutil
import tarfile
import zipfile
from pathlib import Path, PurePosixPath

from app.utils.logger import logger

INTERFACE_NAMES = frozenset({"interface.json", "interface.jsonc"})
AGENT_DIR_NAME = "agent"


def normalize_archive_parts(parts: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(part for part in parts if part and part != ".")


def determine_interface_dir(
    member_names: list[str],
    interface_names: set[str] | None = None,
) -> tuple[str, ...] | None:
    names = interface_names or set(INTERFACE_NAMES)
    names_lower = {n.lower() for n in names}
    for member in member_names:
        member_path = PurePosixPath(member.replace("\\", "/"))
        if member_path.name.lower() in names_lower:
            return normalize_archive_parts(member_path.parent.parts)
    return None


def agent_dir_parts(interface_dir_parts: tuple[str, ...] | None) -> tuple[str, ...]:
    """agent 位于 interface.json 所在目录的上一级，与 interface 目录同级。"""
    if not interface_dir_parts:
        return (AGENT_DIR_NAME,)
    return interface_dir_parts[:-1] + (AGENT_DIR_NAME,)


def _member_under_dir(
    member_parts: tuple[str, ...], dir_parts: tuple[str, ...]
) -> tuple[str, ...] | None:
    if member_parts[: len(dir_parts)] != dir_parts:
        return None
    return member_parts[len(dir_parts) :]


def _prepare_agent_dest(dest_root: Path) -> Path:
    agent_dest = dest_root / AGENT_DIR_NAME
    if agent_dest.exists():
        shutil.rmtree(agent_dest)
    agent_dest.mkdir(parents=True, exist_ok=True)
    return agent_dest


def _write_agent_member(
    agent_dest: Path, relative_parts: tuple[str, ...], data: bytes
) -> None:
    if not relative_parts:
        return
    target_path = agent_dest.joinpath(*relative_parts)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_bytes(data)


def extract_agent_folder_from_zip(archive_path: Path | str, dest_root: Path | str) -> bool:
    archive = Path(archive_path)
    dest = Path(dest_root)
    try:
        with zipfile.ZipFile(archive, "r", metadata_encoding="utf-8") as zf:
            members = zf.namelist()
            interface_dir = determine_interface_dir(members)
            agent_parts = agent_dir_parts(interface_dir)
            agent_members = []
            for member in members:
                member_path = PurePosixPath(member.replace("\\", "/"))
                member_parts = normalize_archive_parts(member_path.parts)
                relative = _member_under_dir(member_parts, agent_parts)
                if relative is None:
                    continue
                agent_members.append((member, relative))

            if not agent_members:
                logger.debug(
                    "[热更新] 更新包中未找到 agent 目录 (%s)",
                    "/".join(agent_parts),
                )
                return True

            agent_dest = _prepare_agent_dest(dest)
            for member, relative_parts in agent_members:
                if member.endswith("/"):
                    agent_dest.joinpath(*relative_parts).mkdir(
                        parents=True, exist_ok=True
                    )
                    continue
                with zf.open(member) as source:
                    _write_agent_member(agent_dest, relative_parts, source.read())

            logger.info(
                "[热更新] 已提取 agent 目录到 %s（共 %d 项）",
                agent_dest,
                len(agent_members),
            )
            return True
    except Exception:
        logger.exception("[热更新] 从 zip 提取 agent 失败: %s", archive)
        return False


def extract_agent_folder_from_tar(archive_path: Path | str, dest_root: Path | str) -> bool:
    archive = Path(archive_path)
    dest = Path(dest_root)
    try:
        with tarfile.open(archive, "r:*") as tf:
            members = tf.getmembers()
            member_names = [m.name for m in members]
            interface_dir = determine_interface_dir(member_names)
            agent_parts = agent_dir_parts(interface_dir)
            agent_members: list[tuple[tarfile.TarInfo, tuple[str, ...]]] = []
            for member in members:
                member_path = PurePosixPath(member.name.replace("\\", "/"))
                member_parts = normalize_archive_parts(member_path.parts)
                relative = _member_under_dir(member_parts, agent_parts)
                if relative is None:
                    continue
                agent_members.append((member, relative))

            if not agent_members:
                logger.debug(
                    "[热更新] 更新包中未找到 agent 目录 (%s)",
                    "/".join(agent_parts),
                )
                return True

            agent_dest = _prepare_agent_dest(dest)
            for member, relative_parts in agent_members:
                if member.isdir():
                    agent_dest.joinpath(*relative_parts).mkdir(
                        parents=True, exist_ok=True
                    )
                    continue
                extracted = tf.extractfile(member)
                if extracted is None:
                    continue
                _write_agent_member(
                    agent_dest, relative_parts, extracted.read()
                )

            logger.info(
                "[热更新] 已提取 agent 目录到 %s（共 %d 项）",
                agent_dest,
                len(agent_members),
            )
            return True
    except Exception:
        logger.exception("[热更新] 从 tar 提取 agent 失败: %s", archive)
        return False


def extract_agent_folder_from_archive(
    archive_path: Path | str, dest_root: Path | str
) -> bool:
    """将压缩包内与 interface 同级的 agent/ 解压到 dest_root/agent/。"""
    name = Path(archive_path).name.lower()
    if name.endswith(".zip"):
        return extract_agent_folder_from_zip(archive_path, dest_root)
    if name.endswith((".tar.gz", ".tgz")):
        return extract_agent_folder_from_tar(archive_path, dest_root)
    if name.endswith(".exe"):
        try:
            with zipfile.ZipFile(archive_path, "r", metadata_encoding="utf-8"):
                return extract_agent_folder_from_zip(archive_path, dest_root)
        except (zipfile.BadZipFile, OSError):
            return False
    logger.warning("[热更新] 不支持的压缩格式，跳过 agent 提取: %s", archive_path)
    return False
