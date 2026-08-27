"""安装锚点、发行根与可执行文件路径解析。"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

APP_BUNDLE_NAME = "MFW.app"
APP_EXECUTABLE_RELATIVE_PATH = Path("Contents") / "MacOS" / "MFW"
UPDATER_NAME = "MFWUpdater.exe" if sys.platform.startswith("win32") else "MFWUpdater"


def is_packed() -> bool:
    """是否为打包运行时（PyInstaller ``sys.frozen`` 或 Nuitka ``__compiled__``）。"""
    return (
        getattr(sys, "frozen", False)
        or globals().get("__compiled__") is not None
    )


def resolve_install_anchor() -> Path:
    """定位 MFW 安装锚点（主程序 Mach-O/exe 或源码 ``main.py``）。"""
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


def normalize_install_anchor(anchor: Path | str) -> Path:
    """把 ``.app`` 路径和主程序路径统一为 bundle 内的 Mach-O 路径。"""
    resolved = Path(anchor).resolve()
    if resolved.suffix.lower() == ".app":
        return (resolved / APP_EXECUTABLE_RELATIVE_PATH).resolve()
    return resolved


def is_app_bundle_layout(anchor: Path | str | None = None) -> bool:
    """主程序是否位于标准 ``*.app/Contents/MacOS`` 目录中。"""
    resolved = normalize_install_anchor(anchor or resolve_install_anchor())
    executable_dir = resolved.parent
    contents_dir = executable_dir.parent
    app_dir = contents_dir.parent
    return (
        executable_dir.name == "MacOS"
        and contents_dir.name == "Contents"
        and app_dir.suffix.lower() == ".app"
    )


def resolve_install_root(
    anchor: Path | str | None = None, *, meipass: Path | str | None = None
) -> Path:
    """定位外置发行根，即 ``MFW.app``、资源和用户数据的共同父目录。"""
    resolved_anchor = normalize_install_anchor(anchor or resolve_install_anchor())
    if is_app_bundle_layout(resolved_anchor):
        return resolved_anchor.parents[3]

    internal_value = meipass
    if internal_value is None:
        internal_value = getattr(sys, "_MEIPASS", None)
    if internal_value:
        internal = Path(internal_value).resolve()
        if internal.name == "_internal":
            return internal.parent

    root = resolved_anchor.parent
    if root.name == "_internal":
        return root.parent
    return root


def resolve_main_executable(
    install_root: Path | str | None = None,
    *,
    anchor: Path | str | None = None,
) -> Path:
    """解析可用于锁、计划任务与重启的主程序入口。"""
    resolved_anchor = normalize_install_anchor(anchor or resolve_install_anchor())
    if is_app_bundle_layout(resolved_anchor):
        return resolved_anchor

    root = Path(install_root or resolve_install_root(resolved_anchor)).resolve()
    app_executable = root / APP_BUNDLE_NAME / APP_EXECUTABLE_RELATIVE_PATH
    if app_executable.is_file():
        return app_executable.resolve()

    if is_packed() or resolved_anchor.suffix.lower() in {".exe", ".bin"}:
        return resolved_anchor
    return resolved_anchor


def resolve_updater_paths(
    install_root: Path | str | None = None,
) -> tuple[Path, Path]:
    """返回发行根中的正式更新器与运行副本路径。"""
    root = Path(install_root or resolve_install_root()).resolve()
    updater = root / UPDATER_NAME
    updater_copy = updater.with_name(f"{updater.stem}1{updater.suffix}")
    return updater, updater_copy


def resolve_schedule_instance_id() -> str:
    """为当前安装实例生成稳定的短标识，用于隔离系统计划任务命名空间。"""
    anchor = str(normalize_install_anchor(resolve_install_anchor()))
    return hashlib.sha256(anchor.encode("utf-8")).hexdigest()[:8]


def resolve_schedule_task_folder() -> str:
    """Windows 任务计划程序文件夹名（按安装路径隔离，避免多实例互相覆盖）。"""
    return f"MFW-ChainFlow Assistant-{resolve_schedule_instance_id()}"


def resolve_schedule_launch_command(
    config_id: str, *, force_start: bool, reuse_existing: bool = False
) -> tuple[str, str]:
    """构建计划任务启动命令，返回 (executable, arguments)。"""
    from mfw_cli import (
        FLAG_CONFIG_ID,
        FLAG_DIRECT_RUN,
        FLAG_FORCE_RESTART,
        FLAG_REUSE_EXISTING,
    )

    cli_args: list[str] = [f"{FLAG_CONFIG_ID}={config_id}", FLAG_DIRECT_RUN]
    if force_start:
        cli_args.append(FLAG_FORCE_RESTART)
    if reuse_existing:
        cli_args.append(FLAG_REUSE_EXISTING)

    anchor = resolve_main_executable()
    if (
        is_app_bundle_layout(anchor)
        or is_packed()
        or anchor.suffix.lower() in {".exe", ".bin"}
    ):
        return str(anchor), " ".join(cli_args)

    main_py = anchor if anchor.suffix.lower() == ".py" else anchor.parent / "main.py"
    if not main_py.is_file():
        root = Path(__file__).resolve().parents[2]
        main_py = root / "main.py"
    return str(Path(sys.executable).resolve()), f'"{main_py}" {" ".join(cli_args)}'
