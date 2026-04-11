from __future__ import annotations

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

    return dict(sorted(notes.items(), key=lambda x: x[0], reverse=True))


def save_release_note(project_name: str, version: str, content: str) -> Path | None:
    """Save a release note file and return its path when successful."""
    safe_project_name = _safe_path_segment(project_name)
    release_notes_dir = Path("./release_notes") / safe_project_name
    release_notes_dir.mkdir(parents=True, exist_ok=True)

    safe_version = version.replace("/", "-").replace("\\", "-").replace(":", "-")
    file_path = release_notes_dir / f"{safe_version}.md"

    try:
        file_path.write_text(content, encoding="utf-8")
    except Exception as exc:
        logger.error("保存更新日志失败: %s", exc)
        return None

    return file_path
