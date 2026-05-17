"""Pre-release version markers that block unattended (auto) updates."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

_AUTO_UPDATE_BLOCK_KEYWORDS = ("ci", "alpha")
_WELCOME_ANNOUNCEMENT_SUPPRESS_KEYWORDS = ("ci",)


def version_disallows_auto_update(version: str | None) -> bool:
    """Return True when version contains ci/alpha (case-insensitive substring)."""
    text = (version or "").lower()
    return any(keyword in text for keyword in _AUTO_UPDATE_BLOCK_KEYWORDS)


def version_suppresses_welcome_announcement(version: str | None) -> bool:
    """Return True when welcome announcement should not auto-popup (CI builds)."""
    text = (version or "").lower()
    return any(keyword in text for keyword in _WELCOME_ANNOUNCEMENT_SUPPRESS_KEYWORDS)


def resolve_resource_version(
    *,
    interface: Mapping[str, Any] | None = None,
    resource_version: str | None = None,
) -> str:
    version = resource_version or resource_version_from_interface(interface)
    if not version:
        version = read_resource_version_from_cwd()
    return version


def read_resource_version_from_cwd() -> str:
    """Read interface.json(c) version from the current working directory."""
    for name in ("interface.jsonc", "interface.json"):
        path = Path(name)
        if not path.is_file():
            continue
        try:
            raw = path.read_text(encoding="utf-8")
        except OSError:
            continue
        try:
            import jsonc

            data = jsonc.loads(raw)
        except Exception:
            try:
                data = json.loads(raw)
            except Exception:
                continue
        if isinstance(data, dict):
            return str(data.get("version", "") or "")
    return ""


def resource_version_from_interface(interface: Mapping[str, Any] | None) -> str:
    if not interface:
        return ""
    return str(interface.get("version", "") or "")


def is_auto_update_permitted(
    *,
    config_enabled: bool,
    interface: Mapping[str, Any] | None = None,
    resource_version: str | None = None,
) -> bool:
    """Config may enable auto-update, but ci/alpha resource builds require manual updates."""
    if not config_enabled:
        return False
    version = resolve_resource_version(
        interface=interface, resource_version=resource_version
    )
    return not version_disallows_auto_update(version)


def is_welcome_announcement_auto_show_permitted(
    *,
    interface: Mapping[str, Any] | None = None,
    resource_version: str | None = None,
) -> bool:
    version = resolve_resource_version(
        interface=interface, resource_version=resource_version
    )
    return not version_suppresses_welcome_announcement(version)
