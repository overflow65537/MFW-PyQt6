from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Mapping

from app.utils.logger import logger


def resolve_project_name(
    interface_data: Mapping[str, Any] | None,
    *,
    cached_name: str | None = None,
    default_name: str = "MFW_CFA",
) -> str:
    """Resolve project name for release note storage."""
    if cached_name:
        return str(cached_name)

    if interface_data:
        name = str(interface_data.get("name", "") or "").strip()
        if name:
            return name

    return default_name


def load_release_notes(project_name: str) -> Dict[str, str]:
    """Load all local release notes for a project, sorted by version desc."""
    release_notes_dir = Path("./release_notes") / project_name
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
    release_notes_dir = Path("./release_notes") / project_name
    release_notes_dir.mkdir(parents=True, exist_ok=True)

    safe_version = version.replace("/", "-").replace("\\", "-").replace(":", "-")
    file_path = release_notes_dir / f"{safe_version}.md"

    try:
        file_path.write_text(content, encoding="utf-8")
    except Exception as exc:
        logger.error("保存更新日志失败: %s", exc)
        return None

    return file_path
