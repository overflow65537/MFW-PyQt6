"""PI v2.9.2 失败诊断附件：采样与本地诊断文件收集。"""

from __future__ import annotations

import random
from pathlib import Path
from typing import Any, Iterable

MAX_ATTACHMENT_BYTES = 2 * 1024 * 1024
MAX_DISK_IMAGES = 4
LOG_TAIL_BYTES = 32 * 1024
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}


def parse_unit_interval(value: Any, default: float = 1.0) -> float:
    """将配置值规范到 [0, 1]。"""
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        parsed = default
    return max(0.0, min(1.0, parsed))


def should_sample_attachments(
    sample_rate: float, *, rng: random.Random | None = None
) -> bool:
    """按独立采样率决定是否上传附件。"""
    rate = parse_unit_interval(sample_rate, default=0.0)
    if rate <= 0.0:
        return False
    if rate >= 1.0:
        return True
    picker = rng.random if rng is not None else random.random
    return picker() < rate


def _newest_files(directory: Path, suffixes: Iterable[str], limit: int) -> list[Path]:
    if not directory.is_dir():
        return []
    wanted = {suffix.lower() for suffix in suffixes}
    files = [
        path
        for path in directory.iterdir()
        if path.is_file() and path.suffix.lower() in wanted
    ]
    files.sort(key=lambda path: path.stat().st_mtime, reverse=True)
    return files[:limit]


def _read_capped(path: Path, max_bytes: int = MAX_ATTACHMENT_BYTES) -> bytes | None:
    try:
        size = path.stat().st_size
        if size <= 0 or size > max_bytes:
            return None
        return path.read_bytes()
    except OSError:
        return None


def collect_failure_diagnostic_files(
    debug_root: Path | None = None,
) -> list[dict[str, Any]]:
    """收集已落盘的失败诊断文件，不读取配置明文。"""
    root = Path(debug_root) if debug_root is not None else Path("debug")
    attachments: list[dict[str, Any]] = []

    image_dirs = (root / "on_error", root / "vision")
    remaining = MAX_DISK_IMAGES
    for image_dir in image_dirs:
        if remaining <= 0:
            break
        for path in _newest_files(image_dir, IMAGE_SUFFIXES, remaining):
            data = _read_capped(path)
            if not data:
                continue
            suffix = path.suffix.lower().lstrip(".") or "png"
            attachments.append(
                {
                    "filename": f"{image_dir.name}_{path.name}",
                    "content_type": f"image/{'jpeg' if suffix in {'jpg', 'jpeg'} else suffix}",
                    "bytes": data,
                }
            )
            remaining -= 1

    log_path = root / "maafw.log"
    if log_path.is_file():
        try:
            with log_path.open("rb") as handle:
                handle.seek(0, 2)
                size = handle.tell()
                handle.seek(max(0, size - LOG_TAIL_BYTES))
                tail = handle.read()
            if tail:
                attachments.append(
                    {
                        "filename": "maafw.log.tail.txt",
                        "content_type": "text/plain",
                        "bytes": tail,
                    }
                )
        except OSError:
            pass

    return attachments
