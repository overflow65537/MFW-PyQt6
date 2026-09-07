"""热更新后按 interface.resource.path 计算 MaaResourceGetHash 并回填 resource.hash。"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.utils.logger import logger


def resolve_resource_path(bundle_base: Path, raw_path: object) -> Path | None:
    """解析 resource.path 条目为绝对路径（与 task_flow.load_resources 一致）。"""
    if not isinstance(raw_path, str):
        return None
    stripped = raw_path.strip()
    if not stripped:
        return None
    normalized = stripped.replace("{PROJECT_DIR}", "").strip().lstrip("\\/")
    if not normalized:
        return None
    base = bundle_base.resolve()
    return (base / normalized).resolve()


def _read_resource_hash(resource: Any) -> str:
    actual_hash = getattr(resource, "hash", "")
    if callable(actual_hash):
        actual_hash = actual_hash()
    return str(actual_hash or "").strip()


def compute_resource_hash_for_paths(
    bundle_base: Path | str,
    path_items: list[object],
) -> str | None:
    """加载 path 数组并返回 MaaResourceGetHash；失败返回 None。"""
    base = Path(bundle_base)
    if not base.is_absolute():
        base = (Path.cwd() / base).resolve()
    else:
        base = base.resolve()

    resolved_paths: list[Path] = []
    for item in path_items:
        resolved = resolve_resource_path(base, item)
        if resolved is None:
            continue
        if not resolved.exists():
            logger.warning(
                "[热更新] 资源路径不存在，跳过 hash 计算: %s",
                resolved,
            )
            return None
        resolved_paths.append(resolved)

    if not resolved_paths:
        return None

    try:
        from maa.resource import Resource
    except ImportError as exc:
        logger.warning("[热更新] 无法导入 maa.resource，跳过 hash 回填: %s", exc)
        return None

    resource = Resource()
    resource.use_cpu()
    for resolved in resolved_paths:
        request = resource.post_bundle(resolved)
        result = request.wait()
        if not result.succeeded:
            logger.warning(
                "[热更新] 资源加载失败，跳过 hash 计算: %s",
                resolved,
            )
            return None

    hash_value = _read_resource_hash(resource)
    if not hash_value:
        logger.warning("[热更新] MaaResourceGetHash 返回空值")
        return None
    return hash_value


def apply_resource_hashes_to_interface(
    interface: dict[str, Any],
    bundle_path: Path | str,
) -> int:
    """按 resource.path 计算 hash 并覆盖写入 interface.resource[].hash。

    Returns:
        成功写入 hash 的资源条目数量。
    """
    resources = interface.get("resource")
    if not isinstance(resources, list):
        return 0

    updated = 0
    for entry in resources:
        if not isinstance(entry, dict):
            continue
        paths = entry.get("path")
        if not isinstance(paths, list) or not paths:
            continue
        resource_name = str(entry.get("name", "") or "").strip() or "<unnamed>"
        hash_value = compute_resource_hash_for_paths(bundle_path, paths)
        if hash_value is None:
            logger.warning(
                "[热更新] 未能计算 resource.hash: name=%s",
                resource_name,
            )
            continue
        old_hash = str(entry.get("hash", "") or "").strip()
        entry["hash"] = hash_value
        updated += 1
        if old_hash != hash_value:
            logger.info(
                "[热更新] resource.hash 已更新: name=%s, %s -> %s",
                resource_name,
                old_hash or "<empty>",
                hash_value,
            )
    return updated
