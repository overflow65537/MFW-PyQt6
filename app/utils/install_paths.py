"""安装锚点与可执行文件路径解析（与 main.py 逻辑保持一致）。"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path


def resolve_install_anchor() -> Path:
    """定位 MFW 安装锚点（发行根目录旁的 exe 或 main.py）。"""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve()

    compiled = globals().get("__compiled__")
    if compiled is not None:
        argv0 = getattr(compiled, "onefile_argv0", None) or sys.argv[0]
        return Path(argv0).resolve()

    if sys.argv and sys.argv[0]:
        candidate = Path(sys.argv[0]).resolve()
        if candidate.exists():
            return candidate

    root = Path(__file__).resolve().parents[2]
    return (root / "main.py").resolve()


def resolve_schedule_instance_id() -> str:
    """为当前安装实例生成稳定的短标识，用于隔离系统计划任务命名空间。"""
    anchor = str(resolve_install_anchor().resolve())
    return hashlib.sha256(anchor.encode("utf-8")).hexdigest()[:8]


def resolve_schedule_task_folder() -> str:
    """Windows 任务计划程序文件夹名（按安装路径隔离，避免多实例互相覆盖）。"""
    return f"MFW-ChainFlow Assistant-{resolve_schedule_instance_id()}"


def resolve_schedule_launch_command(config_id: str, *, force_start: bool) -> tuple[str, str]:
    """构建计划任务启动命令，返回 (executable, arguments)。"""
    from mfw_cli import FLAG_CONFIG_ID, FLAG_DIRECT_RUN, FLAG_FORCE_RESTART

    cli_args: list[str] = [f"{FLAG_CONFIG_ID}={config_id}", FLAG_DIRECT_RUN]
    if force_start:
        cli_args.append(FLAG_FORCE_RESTART)

    anchor = resolve_install_anchor()
    if getattr(sys, "frozen", False) or anchor.suffix.lower() in {".exe", ".bin"}:
        return str(anchor), " ".join(cli_args)

    main_py = anchor if anchor.suffix.lower() == ".py" else anchor.parent / "main.py"
    if not main_py.is_file():
        root = Path(__file__).resolve().parents[2]
        main_py = root / "main.py"
    return str(Path(sys.executable).resolve()), f'"{main_py}" {" ".join(cli_args)}'
