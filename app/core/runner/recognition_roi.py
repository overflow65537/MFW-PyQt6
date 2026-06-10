"""识别结果 ROI 提取（Runner 层，供 MaaContextSink 使用）。"""

from __future__ import annotations

from typing import Any


def _normalize_box(box: Any) -> tuple[int, int, int, int] | None:
    """将 Maa Rect 或 [x, y, w, h] 序列转为 (x, y, w, h)。"""
    if box is None:
        return None

    if hasattr(box, "x") and hasattr(box, "y") and hasattr(box, "w") and hasattr(box, "h"):
        w, h = int(box.w), int(box.h)
        if w <= 0 or h <= 0:
            return None
        return (int(box.x), int(box.y), w, h)

    try:
        if len(box) >= 4:
            w, h = int(box[2]), int(box[3])
            if w <= 0 or h <= 0:
                return None
            return (int(box[0]), int(box[1]), w, h)
    except TypeError:
        pass
    return None


def extract_recognition_box(reco_detail: Any) -> tuple[int, int, int, int] | None:
    """从 Maa RecognitionDetail 提取 best 命中框 (x, y, w, h)。"""
    if reco_detail is None:
        return None

    box = _normalize_box(getattr(reco_detail, "box", None))
    if box is not None:
        return box

    best = getattr(reco_detail, "best_result", None)
    if best is None:
        return None

    return _normalize_box(getattr(best, "box", None))
