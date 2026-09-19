"""Build channel-neutral external notification content."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import html
import re


_LOG_LINE_RE = re.compile(r"^\[(?P<time>[^\]]+)\]\[(?P<level>[^\]]+)\](?P<text>.*)$")
_LEVEL_COLORS = {
    "DEBUG": "#6b7280",
    "INFO": "#2563eb",
    "WARNING": "#d97706",
    "WARN": "#d97706",
    "ERROR": "#dc2626",
    "CRITICAL": "#991b1b",
}
_MARKDOWN_SPECIAL_RE = re.compile(r"([\\`*_{}\[\]()#+\-.!|>])")


@dataclass(frozen=True, slots=True)
class NoticePayload:
    """One notification represented in every format used by channel adapters."""

    title: str
    plain_text: str
    html_body: str
    markdown_body: str
    image_bytes: bytes | None = None

    def as_message_dict(self) -> dict[str, str | bytes]:
        message: dict[str, str | bytes] = {
            "title": self.title,
            "text": self.plain_text,
            "html": self.html_body,
            "markdown": self.markdown_body,
        }
        if self.image_bytes:
            message["image_bytes"] = self.image_bytes
        return message


def _timestamp_text(timestamp: datetime | str | None) -> str:
    if timestamp is None:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(timestamp, datetime):
        return timestamp.strftime("%Y-%m-%d %H:%M:%S")
    return str(timestamp)


def _html_shell(title: str, content: str, timestamp: str) -> str:
    return (
        '<div style="font-family:Segoe UI,Arial,sans-serif;line-height:1.6;'
        'color:#1f2937">'
        f'<h2 style="margin:0 0 12px">{html.escape(title)}</h2>'
        f"{content}"
        '<p style="margin:16px 0 0;color:#6b7280;font-size:12px">'
        f"{html.escape(timestamp)}</p>"
        "</div>"
    )


def _html_paragraph(text: str) -> str:
    escaped = html.escape(text).replace("\n", "<br>")
    return f'<p style="margin:0;white-space:normal">{escaped}</p>'


def _escape_markdown(text: str) -> str:
    return _MARKDOWN_SPECIAL_RE.sub(r"\\\1", text)


def build_simple_message(
    title: str,
    message: str,
    *,
    timestamp: datetime | str | None = None,
    image_bytes: bytes | None = None,
) -> NoticePayload:
    """Build a short lifecycle notification."""

    sent_at = _timestamp_text(timestamp)
    text = str(message)
    plain = f"{sent_at}: {text}"
    markdown = f"**{title}**\n\n{text}\n\n> {sent_at}"
    return NoticePayload(
        title=str(title),
        plain_text=plain,
        html_body=_html_shell(str(title), _html_paragraph(text), sent_at),
        markdown_body=markdown,
        image_bytes=image_bytes,
    )


def build_custom_message(
    title: str,
    body: str,
    *,
    timestamp: datetime | str | None = None,
    image_bytes: bytes | None = None,
) -> NoticePayload:
    """Build user-authored content while escaping HTML markup."""

    sent_at = _timestamp_text(timestamp)
    text = str(body)
    return NoticePayload(
        title=str(title),
        plain_text=f"{sent_at}: {text}",
        html_body=_html_shell(str(title), _html_paragraph(text), sent_at),
        markdown_body=(
            f"**{_escape_markdown(str(title))}**\n\n"
            f"{_escape_markdown(text)}\n\n> {sent_at}"
        ),
        image_bytes=image_bytes,
    )


def build_log_summary(
    title: str,
    log_plain_text: str,
    *,
    timestamp: datetime | str | None = None,
    image_bytes: bytes | None = None,
) -> NoticePayload:
    """Build a structured task-flow log summary."""

    sent_at = _timestamp_text(timestamp)
    html_lines: list[str] = []
    markdown_lines: list[str] = []

    for raw_line in str(log_plain_text).splitlines():
        match = _LOG_LINE_RE.match(raw_line)
        if not match:
            escaped = html.escape(raw_line)
            html_lines.append(f"<div>{escaped}</div>")
            markdown_lines.append(raw_line)
            continue

        log_time = match.group("time")
        level = match.group("level")
        text = match.group("text")
        color = _LEVEL_COLORS.get(level.upper(), "#374151")
        html_lines.append(
            '<div style="padding:3px 0">'
            f'<span style="color:#6b7280">[{html.escape(log_time)}]</span> '
            f'<strong style="color:{color}">[{html.escape(level)}]</strong> '
            f"{html.escape(text)}"
            "</div>"
        )
        markdown_lines.append(
            f"`[{_escape_markdown(log_time)}]` "
            f"**[{_escape_markdown(level)}]** {_escape_markdown(text)}"
        )

    content = (
        '<div style="font-family:Consolas,monospace;background:#f3f4f6;'
        'border-radius:6px;padding:12px">'
        + "".join(html_lines)
        + "</div>"
    )
    plain = f"{sent_at}: {log_plain_text}"
    markdown_content = "\n\n".join(markdown_lines)
    markdown = f"**{title}**\n\n{markdown_content}\n\n> {sent_at}"
    return NoticePayload(
        title=str(title),
        plain_text=plain,
        html_body=_html_shell(str(title), content, sent_at),
        markdown_body=markdown,
        image_bytes=image_bytes,
    )


__all__ = [
    "NoticePayload",
    "build_custom_message",
    "build_log_summary",
    "build_simple_message",
]
