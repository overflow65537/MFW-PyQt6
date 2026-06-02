"""MFW 启动命令行解析（实现见根目录 ``mfw_cli``）。"""

from mfw_cli import (
    FLAG_CONFIG_ID,
    FLAG_DEV,
    FLAG_DIRECT_RUN,
    FLAG_FORCE_RESTART,
    MFW_FLAGS,
    StartupOptions,
    build_startup_argv,
    collect_passthrough_flags,
    parse_startup_cli,
    split_mfw_and_qt_argv,
)

__all__ = [
    "FLAG_CONFIG_ID",
    "FLAG_DEV",
    "FLAG_DIRECT_RUN",
    "FLAG_FORCE_RESTART",
    "MFW_FLAGS",
    "StartupOptions",
    "build_startup_argv",
    "collect_passthrough_flags",
    "parse_startup_cli",
    "split_mfw_and_qt_argv",
]
