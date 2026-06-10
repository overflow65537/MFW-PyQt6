"""识别 ROI 最新结果缓存：task_flow 盲写，监控出图时读取。"""

from __future__ import annotations

import threading
from copy import deepcopy
from typing import Optional

from app.view.monitor.roi_overlay import normalize_roi_payload


class RecognitionRoiStore:
    """线程安全的「最新 ROI」槽，只保留最后一次写入。"""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._latest: Optional[dict] = None

    def update(self, payload: dict) -> None:
        normalized = normalize_roi_payload(payload)
        if normalized is None:
            return
        with self._lock:
            if normalized.get("clear"):
                self._latest = None
            else:
                self._latest = normalized

    def peek(self) -> Optional[dict]:
        with self._lock:
            if self._latest is None:
                return None
            return deepcopy(self._latest)

    def clear(self) -> None:
        with self._lock:
            self._latest = None
