"""
热更新解压辅助（主程序与 MFWUpdater 共用）。

仅依赖标准库，便于 Nuitka/PyInstaller 分别打成独立 onefile，无需引用 app 包。
"""

from __future__ import annotations

import json
import logging
import shutil
import tarfile
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any

logger = logging.getLogger(__name__)

INTERFACE_NAMES = frozenset({"interface.json", "interface.jsonc"})
AGENT_DIR_NAME = "agent"
CFA_SETTING_FILENAME = "CFA_setting.json"
LEGACY_UPDATE_FLAG_FILENAME = "update_flag.txt"


def default_cfa_setting() -> dict[str, Any]:
    return {"update_flag": "1", "embedded": False}


def read_cfa_setting(bundle_path: Path | str) -> dict[str, Any] | None:
    """读取 bundle 下的 CFA_setting.json；不存在时回退到旧版 update_flag.txt。"""
    base = Path(bundle_path)
    setting_path = base / CFA_SETTING_FILENAME
    if setting_path.is_file():
        try:
            with open(setting_path, "r", encoding="utf-8") as file:
                data = json.load(file)
            if isinstance(data, dict) and "update_flag" in data:
                return data
            logger.warning(
                "[热更新] %s 格式无效，缺少 update_flag 字段: %s",
                CFA_SETTING_FILENAME,
                setting_path,
            )
        except Exception as exc:
            logger.error("[热更新] 读取 %s 失败: %s", setting_path, exc)

    legacy_path = base / LEGACY_UPDATE_FLAG_FILENAME
    if legacy_path.is_file():
        try:
            flag = legacy_path.read_text(encoding="utf-8").strip()
            if flag:
                return {"update_flag": flag}
        except Exception as exc:
            logger.error("[热更新] 读取旧版 %s 失败: %s", legacy_path, exc)
    return None


def cfa_setting_update_flag(setting: dict[str, Any] | None) -> str | None:
    if not setting:
        return None
    flag = setting.get("update_flag")
    if flag is None:
        return None
    return str(flag).strip()


def cfa_setting_embedded(setting: dict[str, Any] | None) -> bool | None:
    if not setting or "embedded" not in setting:
        return None
    return bool(setting["embedded"])


def apply_cfa_embedded_to_interface(
    interface: dict[str, Any],
    bundle_path: Path | str,
) -> bool:
    """按 CFA_setting.json 的 embedded 字段更新 interface.agent.embedded。

    Returns:
        True 表示 interface 中的 embedded 值已变更。
    """
    embedded = cfa_setting_embedded(read_cfa_setting(bundle_path))
    if embedded is None:
        return False

    agent = interface.get("agent")
    if not isinstance(agent, dict):
        agent = {}
        interface["agent"] = agent
    if agent.get("embedded") == embedded:
        return False

    agent["embedded"] = embedded
    return True


def _read_interface_config(config_path: Path) -> dict[str, Any]:
    if not config_path.is_file():
        return {}
    try:
        with open(config_path, "r", encoding="utf-8") as file:
            try:
                import jsonc

                return jsonc.load(file)
            except ImportError:
                return json.load(file)
    except Exception as exc:
        logger.error("[热更新] 读取 interface 配置失败 %s: %s", config_path, exc)
        return {}


def _write_interface_config(config_path: Path, data: dict[str, Any]) -> None:
    with open(config_path, "w", encoding="utf-8") as file:
        try:
            import jsonc

            jsonc.dump(data, file, indent=4, ensure_ascii=False)
        except ImportError:
            json.dump(data, file, indent=4, ensure_ascii=False)


def sync_interface_after_hotfix(
    interface_paths: list[Path],
    version: str,
    bundle_path: Path | str,
) -> bool:
    """热更新后同步 interface 版本号，并按 CFA_setting.json 写入 agent.embedded。"""
    setting = read_cfa_setting(bundle_path)
    embedded = cfa_setting_embedded(setting)

    for path in interface_paths:
        if not path.is_file():
            continue
        interface = _read_interface_config(path)
        if not interface:
            continue
        old_version = interface.get("version", "unknown")
        interface["version"] = version
        apply_cfa_embedded_to_interface(interface, bundle_path)
        _write_interface_config(path, interface)
        embedded_note = (
            f", agent.embedded={embedded}" if embedded is not None else ""
        )
        logger.info(
            "[热更新] interface 已同步: %s (version %s -> %s%s)",
            path.name,
            old_version,
            version,
            embedded_note,
        )
        return True
    logger.warning("[热更新] 未能更新 interface 配置")
    return False


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
