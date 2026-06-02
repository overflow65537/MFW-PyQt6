"""MFW 启动命令行：仅 ``--`` 长选项；首个参数 ``--`` 之后交给 Qt。"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass

# 对外统一的 MFW 开关名（无单字母短选项，避免与 Nuitka / Qt 冲突）
FLAG_CONFIG_ID = "--config-id"
FLAG_DIRECT_RUN = "--direct-run"
FLAG_DEV = "--dev"
FLAG_FORCE_RESTART = "--force-restart"

MFW_FLAGS = (
    FLAG_CONFIG_ID,
    FLAG_DIRECT_RUN,
    FLAG_DEV,
    FLAG_FORCE_RESTART,
)


@dataclass(frozen=True, slots=True)
class StartupOptions:
    """经解析的 MFW 启动选项（不含 Qt 透传参数）。"""

    config_id: str | None = None
    direct_run: bool = False
    enable_dev: bool = False
    force_restart: bool = False


def split_mfw_and_qt_argv(argv: list[str]) -> tuple[list[str], list[str]]:
    """在首个 ``--`` 处拆分：之前为 MFW 参数，之后原样交给 Qt。"""
    if "--" in argv:
        sep = argv.index("--")
        return argv[:sep], argv[sep + 1 :]
    return argv, []


def build_startup_argv(options: StartupOptions) -> list[str]:
    """将 :class:`StartupOptions` 序列化为 MFW 命令行参数（不含 Qt 部分）。"""
    argv: list[str] = []
    if options.config_id:
        argv.append(f"{FLAG_CONFIG_ID}={options.config_id}")
    if options.direct_run:
        argv.append(FLAG_DIRECT_RUN)
    if options.enable_dev:
        argv.append(FLAG_DEV)
    if options.force_restart:
        argv.append(FLAG_FORCE_RESTART)
    return argv


def collect_passthrough_flags(argv: list[str], *flags: str) -> list[str]:
    """从完整 argv 中提取需要透传给他进程的 MFW 开关（按 flags 顺序）。"""
    present = set(flags)
    return [token for token in argv if token in present]


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="MFW",
        description="MFW-ChainFlow Assistant",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "MFW 开关（写在分隔符 ``--`` 之前）:\n"
            f"  {FLAG_CONFIG_ID} ID   启动后切换到指定配置（可用 {FLAG_CONFIG_ID}=ID）\n"
            f"  {FLAG_DIRECT_RUN}      启动后直接运行任务流\n"
            f"  {FLAG_DEV}             显示测试页面\n"
            f"  {FLAG_FORCE_RESTART}   请求同目录下已有实例退出后启动本进程\n"
            "\n"
            "示例:\n"
            f"  %(prog)s {FLAG_CONFIG_ID} default {FLAG_DIRECT_RUN}\n"
            f"  %(prog)s {FLAG_CONFIG_ID}=default {FLAG_DIRECT_RUN} {FLAG_FORCE_RESTART}\n"
            f"  %(prog)s {FLAG_DIRECT_RUN} -- -platform windows:darkmode=1\n"
            "\n"
            "分隔符 ``--`` 之后的参数仅传递给 Qt。"
        ),
    )
    parser.add_argument(
        FLAG_CONFIG_ID,
        dest="config_id",
        metavar="ID",
        help="启动后切换到指定配置 ID",
    )
    parser.add_argument(
        FLAG_DIRECT_RUN,
        action="store_true",
        help="启动后直接运行任务流",
    )
    parser.add_argument(
        FLAG_DEV,
        dest="enable_dev",
        action="store_true",
        help="显示测试页面",
    )
    parser.add_argument(
        FLAG_FORCE_RESTART,
        action="store_true",
        help="请求同安装目录下正在运行的 MFW 停止任务并退出后启动本进程",
    )
    return parser


def parse_startup_cli(argv: list[str] | None = None) -> tuple[StartupOptions, list[str]]:
    """解析 MFW 启动参数，返回 (选项, 传给 Qt 的额外参数列表)。"""
    source = list(argv if argv is not None else sys.argv[1:])
    mfw_argv, qt_extra = split_mfw_and_qt_argv(source)

    parser = _build_parser()
    ns = parser.parse_args(mfw_argv)

    options = StartupOptions(
        config_id=ns.config_id,
        direct_run=bool(ns.direct_run),
        enable_dev=bool(ns.enable_dev),
        force_restart=bool(ns.force_restart),
    )
    return options, qt_extra
