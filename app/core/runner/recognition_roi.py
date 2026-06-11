"""识别结果 ROI 提取（Runner 层，供 MaaContextSink 使用）。"""

from __future__ import annotations

from typing import Any


def _normalize_box(box: Any, *, allow_non_positive_size: bool = False) -> tuple[int, int, int, int] | None:
    """将 Maa Rect 或 [x, y, w, h] 序列转为 (x, y, w, h)。"""
    if box is None:
        return None

    if hasattr(box, "x") and hasattr(box, "y") and hasattr(box, "w") and hasattr(box, "h"):
        w, h = int(box.w), int(box.h)
        if not allow_non_positive_size and (w <= 0 or h <= 0):
            return None
        return (int(box.x), int(box.y), w, h)

    try:
        if len(box) >= 4:
            w, h = int(box[2]), int(box[3])
            if not allow_non_positive_size and (w <= 0 or h <= 0):
                return None
            return (int(box[0]), int(box[1]), w, h)
    except TypeError:
        pass
    return None


def _apply_roi_offset(
    box: tuple[int, int, int, int], offset: Any
) -> tuple[int, int, int, int]:
    normalized_offset = _normalize_box(offset, allow_non_positive_size=True)
    if normalized_offset is None:
        return box
    return (
        box[0] + normalized_offset[0],
        box[1] + normalized_offset[1],
        box[2] + normalized_offset[2],
        box[3] + normalized_offset[3],
    )


def _extract_roi_from_param(param: Any) -> tuple[int, int, int, int] | None:
    if param is None:
        return None

    roi_raw = getattr(param, "roi", None)
    if roi_raw is None and isinstance(param, dict):
        roi_raw = param.get("roi")
        roi_offset = param.get("roi_offset")
    else:
        roi_offset = getattr(param, "roi_offset", None)

    if isinstance(roi_raw, (str, bool)):
        return None

    box = _normalize_box(roi_raw)
    if box is None:
        return None

    return _apply_roi_offset(box, roi_offset)


def extract_node_recognition_roi(context: Any, node_name: str) -> tuple[int, int, int, int] | None:
    """从 get_node_data / get_node_object 提取节点配置的识别 ROI。"""
    if not node_name:
        return None

    try:
        node_obj = context.get_node_object(node_name)
    except Exception:
        node_obj = None

    if node_obj is not None:
        recognition = getattr(node_obj, "recognition", None)
        param = getattr(recognition, "param", None) if recognition else None
        box = _extract_roi_from_param(param)
        if box is not None:
            return box

    try:
        node_data = context.get_node_data(node_name)
    except Exception:
        node_data = None

    if not isinstance(node_data, dict):
        return None

    recognition = node_data.get("recognition")
    if not isinstance(recognition, dict):
        return None

    param = recognition.get("param")
    if not isinstance(param, dict):
        return None

    return _extract_roi_from_param(param)


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
