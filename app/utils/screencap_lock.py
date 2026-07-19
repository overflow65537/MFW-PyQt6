"""进程内截图互斥：序列化对 Maa controller / 模拟器 extras 的截图访问。

Monitor 与任务流可能各自持有 Controller，但 MuMu extras 等原生库是进程共享的；
并发 post_screencap / 读 cached_image 会导致 access violation。
"""

from __future__ import annotations

import threading
from contextlib import contextmanager
from typing import Iterator

_SCREENCAP_LOCK = threading.RLock()


@contextmanager
def screencap_guard() -> Iterator[None]:
    """持有截图互斥锁，直到 with 块结束。"""
    _SCREENCAP_LOCK.acquire()
    try:
        yield
    finally:
        _SCREENCAP_LOCK.release()
