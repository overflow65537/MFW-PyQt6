"""Pure startup decisions for handling an already-running application."""

from enum import StrEnum


class ExistingInstanceAction(StrEnum):
    START = "start"
    REUSE = "reuse"
    RESTART = "restart"
    ACTIVATE = "activate"


def decide_existing_instance_action(
    *,
    existing_instance: bool,
    reuse_existing: bool,
    force_restart: bool,
) -> ExistingInstanceAction:
    """Resolve CLI flags without performing process or IPC side effects."""
    if not existing_instance:
        return ExistingInstanceAction.START
    if reuse_existing:
        return ExistingInstanceAction.REUSE
    if force_restart:
        return ExistingInstanceAction.RESTART
    return ExistingInstanceAction.ACTIVATE
