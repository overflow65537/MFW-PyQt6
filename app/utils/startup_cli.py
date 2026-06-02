"""MFW 进程启动命令行解析（仅识别固定 MFW 开关，其余交给 Qt）。"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass

# 需要跟一个值的 MFW 选项
_VALUE_OPTIONS = frozenset({"-c", "--config", "--config-id"})
# 布尔 MFW 选项
_BOOL_OPTIONS = frozenset(
    {
        "-d",
        "--direct-run",
        "-dev",
        "--dev",
        "-f",
        "--force-restart",
    }
)
_KNOWN_OPTIONS = _VALUE_OPTIONS | _BOOL_OPTIONS | frozenset({"-h", "--help"})


@dataclass(frozen=True, slots=True)
class StartupOptions:
    """经解析的 MFW 启动选项（不含 Qt 透传参数）。"""

    config_id: str | None = None
    direct_run: bool = False
    enable_dev: bool = False
    force_restart: bool = False


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="MFW",
        description="MFW-ChainFlow Assistant",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "示例:\n"
            "  %(prog)s -c default -d\n"
            "  %(prog)s -c=default -f -platform windows:darkmode=1\n"
            "\n"
            "仅识别上述 MFW 开关；未列出的参数（如 Qt 的 -platform）会原样传给 Qt。"
        ),
    )
    parser.add_argument(
        "-c",
        "--config-id",
        "--config",
        dest="config_id",
        metavar="ID",
        help="启动后切换到指定配置 ID（可用 -c=ID）",
    )
    parser.add_argument(
        "-d",
        "--direct-run",
        action="store_true",
        help="启动后直接运行任务流",
    )
    parser.add_argument(
        "-dev",
        "--dev",
        dest="enable_dev",
        action="store_true",
        help="显示测试页面",
    )
    parser.add_argument(
        "-f",
        "--force-restart",
        action="store_true",
        help="请求同安装目录下正在运行的 MFW 停止任务并退出后启动本进程",
    )
    return parser


def _option_key(token: str) -> str | None:
    """若 token 为 ``-c=foo`` 形式，返回选项名 ``-c``。"""
    if "=" in token:
        return token.split("=", 1)[0]
    return token if token in _KNOWN_OPTIONS else None


def _parse_mfw_tokens(argv: list[str]) -> StartupOptions:
    config_id: str | None = None
    direct_run = False
    enable_dev = False
    force_restart = False

    i = 0
    while i < len(argv):
        token = argv[i]

        if "=" in token:
            key, _, value = token.partition("=")
            if key in _VALUE_OPTIONS:
                config_id = value
                i += 1
                continue
            # 非 MFW 的 --foo=bar（如 Qt）不在此处理
        elif token in _VALUE_OPTIONS:
            if i + 1 >= len(argv):
                print(f"error: 选项 {token} 需要指定配置 ID", file=sys.stderr)
                sys.exit(2)
            nxt = argv[i + 1]
            if _option_key(nxt) is not None or nxt in _BOOL_OPTIONS:
                print(
                    f"error: 选项 {token} 需要配置 ID，但下一个参数是 {nxt!r}",
                    file=sys.stderr,
                )
                print(
                    "提示: 请写成「-c <配置ID> -d」或「-c=<配置ID> -d」",
                    file=sys.stderr,
                )
                sys.exit(2)
            config_id = nxt
            i += 2
            continue
        elif token in ("-d", "--direct-run"):
            direct_run = True
            i += 1
            continue
        elif token in ("-dev", "--dev"):
            enable_dev = True
            i += 1
            continue
        elif token in ("-f", "--force-restart"):
            force_restart = True
            i += 1
            continue

        i += 1

    return StartupOptions(
        config_id=config_id,
        direct_run=direct_run,
        enable_dev=enable_dev,
        force_restart=force_restart,
    )


def parse_startup_cli(argv: list[str] | None = None) -> tuple[StartupOptions, list[str]]:
    """解析 MFW 启动参数，返回 (选项, 传给 Qt 的额外参数列表)。

    只识别固定的 MFW 开关（``-c`` ``-d`` ``-dev`` ``-f`` 及对应长选项）；
    其余参数按原顺序交给 Qt，无需使用 ``--`` 分隔。
    """
    source = list(argv if argv is not None else sys.argv[1:])

    if "-h" in source or "--help" in source:
        _build_parser().print_help()
        raise SystemExit(0)

    mfw_tokens: list[str] = []
    qt_extra: list[str] = []

    i = 0
    while i < len(source):
        token = source[i]
        key = _option_key(token)

        if key is not None:
            mfw_tokens.append(token)
            if key in _VALUE_OPTIONS and "=" not in token:
                if i + 1 < len(source) and _option_key(source[i + 1]) is None:
                    mfw_tokens.append(source[i + 1])
                    i += 2
                    continue
            i += 1
            continue

        qt_extra.append(token)
        i += 1

    options = _parse_mfw_tokens(mfw_tokens)
    return options, qt_extra
