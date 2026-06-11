"""监控预览上的识别 ROI 叠加绘制。"""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QPixmap


def draw_roi_on_pixmap(
    pixmap: QPixmap,
    box: list[int] | tuple[int, int, int, int],
    *,
    label: str = "",
    phase: str = "hit",
) -> QPixmap:
    """在预览图像上绘制识别 ROI 边框。"""
    if pixmap.isNull() or not box or len(box) < 4:
        return pixmap

    x, y, w, h = (int(box[0]), int(box[1]), int(box[2]), int(box[3]))
    if w <= 0 or h <= 0:
        return pixmap

    result = pixmap.copy()
    painter = QPainter(result)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

    stroke = max(2, min(result.width(), result.height()) // 240)
    if phase == "recognizing":
        pen_color = QColor(240, 72, 72, 235)
    else:
        pen_color = QColor(80, 220, 120, 230)
    pen = QPen(pen_color)
    pen.setWidth(stroke)
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.drawRect(x, y, w, h)

    if label:
        font = QFont()
        font.setPointSize(max(8, min(12, result.height() // 60)))
        painter.setFont(font)
        text_bg = QColor(0, 0, 0, 160)
        text_fg = QColor(255, 255, 255, 240)
        metrics = painter.fontMetrics()
        text_width = metrics.horizontalAdvance(label) + 8
        text_height = metrics.height() + 4
        text_y = max(0, y - text_height - 2)
        painter.fillRect(x, text_y, min(text_width, result.width() - x), text_height, text_bg)
        painter.setPen(text_fg)
        painter.drawText(x + 4, text_y + metrics.ascent() + 2, label)

    painter.end()
    return result


def normalize_roi_payload(payload: dict) -> Optional[dict]:
    """校验并规范化 recognition_roi 回调载荷。"""
    if not isinstance(payload, dict):
        return None
    if payload.get("clear"):
        return {"clear": True, "node": payload.get("node", "")}
    box = payload.get("box")
    if not isinstance(box, (list, tuple)) or len(box) < 4:
        return None
    return {
        "clear": False,
        "phase": str(payload.get("phase", "hit")),
        "node": str(payload.get("node", "")),
        "reco_id": payload.get("reco_id"),
        "box": [int(box[0]), int(box[1]), int(box[2]), int(box[3])],
        "algorithm": str(payload.get("algorithm", "")),
    }
