from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, Mapping

from app.utils.logger import logger


def _safe_path_segment(value: str, fallback: str = "MFW_CFA") -> str:
    """Return a single safe path segment (no traversal / separators)."""
    text = str(value or "").strip().replace("\\", "/")
    for ch in ('<', '>', ':', '"', "|", "?", "*"):
        text = text.replace(ch, "_")

    parts = [p for p in text.split("/") if p and p not in (".", "..")]
    if not parts:
        return fallback

    sanitized = "_".join(parts).strip(" .")
    return sanitized or fallback


def _safe_version_file_stem(version: str, fallback: str = "latest") -> str:
    """Return a filesystem-safe release note stem while preserving version readability."""
    text = str(version or "").strip()
    if not text:
        return fallback

    for ch in ('<', '>', ':', '"', "|", "?", "*", '/', '\\'):
        text = text.replace(ch, "-")

    text = text.strip(" .")
    return text or fallback


def _version_part_key(part: str) -> tuple[int, int | str]:
    if part.isdigit():
        return (1, int(part))
    return (0, part.lower())


def _release_note_sort_key(version: str) -> tuple[tuple[int, ...], tuple[int, tuple[tuple[int, int | str], ...]], str]:
    """Build a descending-friendly sort key for semantic-ish version strings."""
    raw = str(version or "").strip()
    normalized = raw.lstrip("vV")
    match = re.match(r"^(\d+(?:\.\d+)*)?(?:[-_.]?(.+))?$", normalized)
    if not match:
        return ((), (-1, ()), raw.lower())

    core_text = match.group(1) or ""
    suffix_text = (match.group(2) or "").strip()
    core = tuple(int(part) for part in core_text.split(".") if part.isdigit())

    if not suffix_text:
        suffix_rank = 3
        suffix_parts: tuple[tuple[int, int | str], ...] = ()
    else:
        first_token = re.split(r"[._-]", suffix_text, maxsplit=1)[0].lower()
        if first_token.startswith("rc"):
            suffix_rank = 2
        elif first_token.startswith("beta"):
            suffix_rank = 1
        elif first_token.startswith("alpha"):
            suffix_rank = 0
        else:
            suffix_rank = -1
        suffix_parts = tuple(
            _version_part_key(part) for part in re.split(r"[._-]", suffix_text) if part
        )

    return (core, (suffix_rank, suffix_parts), raw.lower())


def resolve_project_name(
    interface_data: Mapping[str, Any] | None,
    *,
    cached_name: str | None = None,
    default_name: str = "MFW_CFA",
) -> str:
    """Resolve project name for release note storage."""
    if cached_name:
        return _safe_path_segment(cached_name, default_name)

    if interface_data:
        name = str(interface_data.get("name", "") or "").strip()
        if name:
            return _safe_path_segment(name, default_name)

    return _safe_path_segment(default_name, "MFW_CFA")


def load_release_notes(project_name: str) -> Dict[str, str]:
    """Load all local release notes for a project, sorted by version desc."""
    safe_project_name = _safe_path_segment(project_name)
    release_notes_dir = Path("./release_notes") / safe_project_name
    notes: Dict[str, str] = {}

    if not release_notes_dir.exists():
        return notes

    try:
        for path in release_notes_dir.glob("*.md"):
            notes[path.stem] = path.read_text(encoding="utf-8")
    except Exception as exc:
        logger.error("加载更新日志失败: %s", exc)
        return {}

    return dict(
        sorted(notes.items(), key=lambda item: _release_note_sort_key(item[0]), reverse=True)
    )


def save_release_note(project_name: str, version: str, content: str) -> Path | None:
    """Save a release note file and return its path when successful."""
    safe_project_name = _safe_path_segment(project_name)
    release_notes_dir = Path("./release_notes") / safe_project_name
    release_notes_dir.mkdir(parents=True, exist_ok=True)

    safe_version = _safe_version_file_stem(version)
    file_path = release_notes_dir / f"{safe_version}.md"

    try:
        file_path.write_text(content, encoding="utf-8")
    except Exception as exc:
        logger.error("保存更新日志失败: %s", exc)
        return None

    return file_path
