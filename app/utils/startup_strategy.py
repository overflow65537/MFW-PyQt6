"""Pure startup decisions for handling an already-running application."""

from enum import StrEnum


class ExistingInstanceAction(StrEnum):
    START = "start"
    REUSE = "reuse"
    RESTART = "restart"
    ACTIVATE = "activate"


class ReuseExistingCommand(StrEnum):
    ACTIVATE = "activate"
    SWITCH_CONFIG = "switch_config"
    RUN = "run"


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


def decide_reuse_existing_command(
    *,
    direct_run: bool,
    config_id: str | None,
) -> ReuseExistingCommand:
    """Choose the IPC command used to reuse an already-running instance.

    Reusing an instance is a process-selection policy, not an instruction to
    start tasks. Task execution remains exclusively controlled by
    ``--direct-run``.
    """
    if direct_run:
        return ReuseExistingCommand.RUN
    if config_id:
        return ReuseExistingCommand.SWITCH_CONFIG
    return ReuseExistingCommand.ACTIVATE
