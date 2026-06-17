"""在 GUI 进程中调用子进程时避免弹出控制台窗口。"""

from __future__ import annotations

import subprocess
import sys

_CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)


def hidden_subprocess_kwargs() -> dict:
    """返回适用于 subprocess.run / Popen 的隐藏控制台参数。"""
    if sys.platform != "win32":
        return {}
    return {"creationflags": _CREATE_NO_WINDOW}
