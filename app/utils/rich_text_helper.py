"""
富文本标签的链接交互与 Qt HTML 兼容处理。
"""

from __future__ import annotations

import re
from collections.abc import Callable
from typing import TYPE_CHECKING

from PySide6.QtCore import QEvent, QObject, Qt, QUrl, QPoint
from PySide6.QtGui import QDesktopServices, QTextDocument
from app.utils.logger import logger

if TYPE_CHECKING:
    from PySide6.QtWidgets import QLabel

_FONT_OPEN_PATTERN = re.compile(
    r"<font\s+color=(['\"])([^'\"]+)\1\s*>",
    re.IGNORECASE,
)
_FONT_CLOSE_PATTERN = re.compile(r"</font>", re.IGNORECASE)
# href 被误包成 Markdown 时的修复：href="[https://...](https://...)"
_CORRUPTED_HREF_IN_ATTR = re.compile(
    r'href=(["\'])\[(https?://[^\]]+)\]\(\2\)\1',
    re.IGNORECASE,
)
# anchorAt 返回带前导 [ 的损坏 URL
_CORRUPTED_LEADING_BRACKET_URL = re.compile(
    r"^\[(https?://[^\]]+)(?:\]\([^)]*\))?$"
)


def normalize_html_for_qt(html: str) -> str:
    """将 Qt RichText 支持较差的 <font> 转为 <span style=\"color:...\">。"""
    if not html:
        return html

    # 修复 linkify 误处理导致的 href="[url](url)"
    html = _CORRUPTED_HREF_IN_ATTR.sub(r"href=\1\2\1", html)

    if "<font" not in html.lower():
        return html

    def _replace_open(match: re.Match[str]) -> str:
        return f'<span style="color:{match.group(2)}">'

    html = _FONT_OPEN_PATTERN.sub(_replace_open, html)
    return _FONT_CLOSE_PATTERN.sub("</span>", html)


def sanitize_link_url(url: str) -> str:
    """清理 anchorAt / 损坏 HTML 返回的 URL。"""
    if not url:
        return ""
    cleaned = url.strip()
    match = _CORRUPTED_LEADING_BRACKET_URL.match(cleaned)
    if match:
        return match.group(1)
    if cleaned.startswith("[") and cleaned[1:].startswith("http"):
        bracket_end = cleaned.find("]")
        if bracket_end > 1:
            return cleaned[1:bracket_end]
    return cleaned


def open_external_link(url: str) -> bool:
    """在系统浏览器中打开 http(s)/file 链接，成功返回 True。"""
    url = sanitize_link_url(url)
    if not url:
        return False
    qurl = QUrl(url)
    if qurl.scheme() in ("http", "https", "file") and qurl.isValid():
        opened = QDesktopServices.openUrl(qurl)
        if opened:
            logger.info("已打开链接: %s", url)
        else:
            logger.warning("打开链接失败: %s", url)
        return opened
    logger.debug("忽略非外部链接: %s", url)
    return False


def _anchor_at_label(label: "QLabel", pos: QPoint) -> str:
    """用 QTextDocument 检测点击位置处的超链接（QLabel.linkActivated 在部分样式下不触发）。"""
    text = label.text()
    if not text:
        return ""
    doc = QTextDocument()
    doc.setHtml(text)
    width = label.width() if label.width() > 0 else 400
    doc.setTextWidth(width)
    layout = doc.documentLayout()
    if layout is None:
        return ""
    anchor = layout.anchorAt(pos)
    return sanitize_link_url(anchor) if anchor else ""


class _RichTextLinkFilter(QObject):
    """拦截鼠标事件，手动打开富文本中的超链接。"""

    def __init__(
        self,
        label: "QLabel",
        *,
        on_image_link: Callable[[str], None] | None = None,
    ) -> None:
        super().__init__(label)
        self._label = label
        self._on_image_link = on_image_link

    def _handle_link(self, url: str) -> bool:
        if not url:
            return False
        if url.startswith("image:"):
            if self._on_image_link is not None:
                logger.debug("点击图片链接: %s", url)
                self._on_image_link(url)
            return True
        return open_external_link(url)

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        if obj is not self._label:
            return super().eventFilter(obj, event)

        if event.type() == QEvent.Type.MouseButtonRelease:
            mouse = event
            if mouse.button() == Qt.MouseButton.LeftButton:
                pos = (
                    mouse.position().toPoint()
                    if hasattr(mouse, "position")
                    else mouse.pos()
                )
                url = _anchor_at_label(self._label, pos)
                if url and self._handle_link(url):
                    return True

        if event.type() == QEvent.Type.MouseMove:
            mouse = event
            pos = (
                mouse.position().toPoint()
                if hasattr(mouse, "position")
                else mouse.pos()
            )
            over_link = bool(_anchor_at_label(self._label, pos))
            self._label.setCursor(
                Qt.CursorShape.PointingHandCursor
                if over_link
                else Qt.CursorShape.ArrowCursor
            )

        return super().eventFilter(obj, event)


def configure_rich_text_label(
    label: "QLabel",
    *,
    on_image_link: Callable[[str], None] | None = None,
) -> None:
    """配置 QLabel/BodyLabel 以支持富文本中的可点击超链接。"""
    label.setTextFormat(Qt.TextFormat.RichText)
    label.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
    label.setOpenExternalLinks(False)

    existing = getattr(label, "_rich_text_link_filter", None)
    if isinstance(existing, _RichTextLinkFilter):
        label.removeEventFilter(existing)
        existing.deleteLater()

    link_filter = _RichTextLinkFilter(label, on_image_link=on_image_link)
    label._rich_text_link_filter = link_filter  # type: ignore[attr-defined]
    label.installEventFilter(link_filter)


def apply_rich_text_html(
    label: "QLabel",
    html: str,
    *,
    on_image_link: Callable[[str], None] | None = None,
) -> None:
    """配置标签并设置经 Qt 兼容处理后的 HTML。"""
    configure_rich_text_label(label, on_image_link=on_image_link)
    label.setText(normalize_html_for_qt(html))
