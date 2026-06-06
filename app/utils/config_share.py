"""配置分享编解码：含资源名与版本头，仅包含任务顺序与任务选项。"""

from __future__ import annotations

import base64
import json
import zlib
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import jsonc

from app.core.item import ConfigItem
from app.utils.version_policy import resource_version_from_interface

MAGIC = "MFWCFG1:"
FORMAT_VERSION = 1


class ConfigShareError(ValueError):
    """分享配置编解码失败。"""


class ConfigShareResourceError(ConfigShareError):
    """分享配置与目标资源包不匹配。"""

    def __init__(self, shared_bundle: str, target_bundle: str):
        self.shared_bundle = shared_bundle
        self.target_bundle = target_bundle
        super().__init__("resource mismatch")


@dataclass(frozen=True)
class ConfigSharePayload:
    bundle: str
    resource_version: str
    tasks: list[dict[str, Any]]


def load_bundle_interface(bundle_path: str) -> dict[str, Any] | None:
    """从 bundle 路径加载 interface.json(c)。"""
    path = Path(bundle_path or "./")
    if not path.is_absolute():
        path = Path.cwd() / path

    interface_path = None
    for candidate in (path / "interface.jsonc", path / "interface.json"):
        if candidate.exists():
            interface_path = candidate
            break
    if interface_path is None:
        return None

    try:
        with open(interface_path, "r", encoding="utf-8") as handle:
            data = jsonc.load(handle)
    except Exception:
        return None
    return data if isinstance(data, dict) else None


def resolve_bundle_resource_version(config_service, bundle_name: str) -> str:
    """根据 bundle 名称解析 interface 版本号。"""
    if not bundle_name:
        return ""
    try:
        bundle_raw = config_service.get_bundle(bundle_name)
    except FileNotFoundError:
        return ""
    path = str(bundle_raw.get("path", "./") or "./")
    interface = load_bundle_interface(path)
    return resource_version_from_interface(interface)


def extract_shareable_tasks(config: ConfigItem) -> list[dict[str, Any]]:
    """从配置中提取可分享的任务列表（排除基础任务）。"""
    tasks: list[dict[str, Any]] = []
    for task in config.tasks:
        if task.is_base_task():
            continue
        entry: dict[str, Any] = {
            "name": task.name,
            "is_checked": task.is_checked,
            "task_option": deepcopy(task.task_option),
        }
        if task.task_source != "resource":
            entry["task_source"] = task.task_source
        if task.builtin_key:
            entry["builtin_key"] = task.builtin_key
        tasks.append(entry)
    return tasks


def encode_config_tasks(
    config: ConfigItem,
    *,
    bundle: str,
    resource_version: str,
) -> str:
    """将配置中的任务序列化为可分享的压缩编码字符串。"""
    bundle_name = (bundle or "").strip()
    if not bundle_name:
        raise ConfigShareError("missing bundle")

    tasks = extract_shareable_tasks(config)
    payload = {
        "v": FORMAT_VERSION,
        "bundle": bundle_name,
        "resource_version": str(resource_version or ""),
        "tasks": tasks,
    }
    raw = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    compressed = zlib.compress(raw, level=9)
    encoded = base64.urlsafe_b64encode(compressed).decode("ascii")
    return MAGIC + encoded


def _normalize_tasks(tasks: Any) -> list[dict[str, Any]]:
    if not isinstance(tasks, list):
        raise ConfigShareError("invalid tasks")

    normalized: list[dict[str, Any]] = []
    for entry in tasks:
        if not isinstance(entry, dict):
            continue
        name = entry.get("name")
        if not isinstance(name, str) or not name.strip():
            continue
        task_option = entry.get("task_option", {})
        if not isinstance(task_option, dict):
            task_option = {}
        item: dict[str, Any] = {
            "name": name.strip(),
            "is_checked": bool(entry.get("is_checked", True)),
            "task_option": task_option,
        }
        task_source = entry.get("task_source")
        if isinstance(task_source, str) and task_source.strip():
            item["task_source"] = task_source.strip()
        builtin_key = entry.get("builtin_key")
        if isinstance(builtin_key, str) and builtin_key.strip():
            item["builtin_key"] = builtin_key.strip()
        normalized.append(item)
    return normalized


def decode_share_payload(text: str) -> ConfigSharePayload:
    """解析分享编码字符串。"""
    text = (text or "").strip()
    if not text.startswith(MAGIC):
        raise ConfigShareError("invalid magic prefix")

    try:
        compressed = base64.urlsafe_b64decode(text[len(MAGIC) :].encode("ascii"))
        raw = zlib.decompress(compressed)
        payload = json.loads(raw.decode("utf-8"))
    except Exception as exc:
        raise ConfigShareError("decode failed") from exc

    if not isinstance(payload, dict):
        raise ConfigShareError("invalid payload")
    if payload.get("v") != FORMAT_VERSION:
        raise ConfigShareError("unsupported version")

    bundle = payload.get("bundle")
    if not isinstance(bundle, str) or not bundle.strip():
        raise ConfigShareError("missing bundle header")
    resource_version = payload.get("resource_version", "")
    if resource_version is None:
        resource_version = ""
    if not isinstance(resource_version, str):
        resource_version = str(resource_version)

    tasks = _normalize_tasks(payload.get("tasks"))
    return ConfigSharePayload(
        bundle=bundle.strip(),
        resource_version=resource_version.strip(),
        tasks=tasks,
    )


def validate_share_for_import(
    payload: ConfigSharePayload,
    *,
    target_bundle: str,
    target_resource_version: str,
) -> tuple[str, str] | None:
    """校验分享内容与目标资源包是否匹配。

    跨资源直接拒绝；跨版本返回 (shared_version, target_version) 供 UI 警告，但允许继续。
    """
    shared_bundle = (payload.bundle or "").strip()
    bundle = (target_bundle or "").strip()
    if not shared_bundle or not bundle:
        raise ConfigShareError("missing bundle for validation")
    if shared_bundle != bundle:
        raise ConfigShareResourceError(shared_bundle, bundle)

    shared_version = (payload.resource_version or "").strip()
    target_version = (target_resource_version or "").strip()
    if shared_version != target_version:
        return shared_version, target_version
    return None
