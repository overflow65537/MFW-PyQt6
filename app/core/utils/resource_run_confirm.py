"""首次运行资源包前的身份确认（防止误跑恶意资源）。"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping

from app.utils.logger import logger

MAX_ACKNOWLEDGED_RESOURCE_RUNS = 200


def build_resource_run_identity(interface: Mapping[str, Any] | None) -> dict[str, str]:
    """从 interface 提取需要向用户展示、并用于记住确认的身份信息。"""
    data = interface if isinstance(interface, Mapping) else {}
    name = str(data.get("label") or "").strip()
    if name.startswith("$"):
        name = ""
    if not name:
        name = str(data.get("title") or "").strip()
    if name.startswith("$"):
        name = ""
    if not name:
        name = str(data.get("name") or "").strip()
    github = str(data.get("github") or data.get("url") or "").strip()
    contact = str(data.get("contact") or "").strip()
    return {
        "name": name,
        "github": github,
        "contact": contact,
    }


def resource_run_fingerprint(identity: Mapping[str, str] | None) -> str:
    """根据名称 / GitHub / 联系方式生成稳定指纹。任一字段变化都会重新确认。"""
    data = identity if isinstance(identity, Mapping) else {}
    payload = json.dumps(
        {
            "name": str(data.get("name") or "").strip(),
            "github": str(data.get("github") or "").strip(),
            "contact": str(data.get("contact") or "").strip(),
        },
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def is_resource_run_acknowledged(identity: Mapping[str, str] | None) -> bool:
    fingerprint = resource_run_fingerprint(identity)
    return fingerprint in _load_acknowledged_fingerprints()


def acknowledge_resource_run(identity: Mapping[str, str] | None) -> None:
    fingerprint = resource_run_fingerprint(identity)
    fingerprints = _load_acknowledged_fingerprints()
    if fingerprint in fingerprints:
        if fingerprints[-1] != fingerprint:
            fingerprints = [item for item in fingerprints if item != fingerprint]
            fingerprints.append(fingerprint)
            _save_acknowledged_fingerprints(fingerprints)
        return
    fingerprints.append(fingerprint)
    if len(fingerprints) > MAX_ACKNOWLEDGED_RESOURCE_RUNS:
        fingerprints = fingerprints[-MAX_ACKNOWLEDGED_RESOURCE_RUNS:]
    _save_acknowledged_fingerprints(fingerprints)


def _load_acknowledged_fingerprints() -> list[str]:
    raw = _read_config_value()
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        logger.warning("已确认资源列表损坏，将重新记录")
        return []
    if not isinstance(parsed, list):
        return []
    return [str(item) for item in parsed if isinstance(item, str) and item]


def _save_acknowledged_fingerprints(fingerprints: list[str]) -> None:
    _write_config_value(json.dumps(fingerprints, ensure_ascii=False))


def _read_config_value() -> str:
    try:
        from app.common.config import cfg

        return str(cfg.get(cfg.acknowledged_resource_runs) or "")
    except Exception as exc:
        logger.debug("读取已确认资源列表失败: %s", exc)
        return ""


def _write_config_value(value: str) -> None:
    try:
        from app.common.config import cfg

        cfg.set(cfg.acknowledged_resource_runs, value)
    except Exception as exc:
        logger.warning("保存已确认资源列表失败: %s", exc)
