from __future__ import annotations

import os
import sys


def is_admin() -> bool:
    if sys.platform == "win32":
        try:
            import ctypes

            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception:
            return False
    return os.geteuid() == 0