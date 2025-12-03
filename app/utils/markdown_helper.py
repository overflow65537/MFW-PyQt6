"""
提供统一的 Markdown 渲染与文件读取。
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Union

import markdown

_IMG_PATTERN = re.compile(
    r'<img\s+([^>]*?)src=["\']([^"\']+)["\']([^>]*)>',
    re.IGNORECASE,
)


def _wrap_image(match: re.Match[str]) -> str:
    before_src = match.group(1)
    src = match.group(2)
    after_src = match.group(3)
    img_tag = f'<img {before_src}src="{src}"{after_src} style="cursor: pointer;">'
    return f'<a href="image:{src}" style="text-decoration: none;">{img_tag}</a>'


def render_markdown(content: str | None) -> str:
    """
    将 Markdown/HTML 内容渲染成 HTML，并为 <img> 自动添加点击链接。
    """
    if not content:
        return ""

    processed = content.replace("\r\n", "\n")
    stripped = processed.strip()

    if stripped.startswith("<") and stripped.endswith(">"):
        html = processed.replace("\n", "<br>") if "\n" in processed else processed
    else:
        html = markdown.markdown(processed, extensions=["extra", "sane_lists"])

    return _IMG_PATTERN.sub(_wrap_image, html)


def load_markdown_file(path: Union[str, Path]) -> str:
    """
    读取 Markdown 文件并返回原始文本。
    """
    file_path = Path(path)
    return file_path.read_text(encoding="utf-8")
