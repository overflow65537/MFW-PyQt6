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

# 表格相关的正则表达式
_TABLE_PATTERN = re.compile(
    r'<table(\s[^>]*)?>',
    re.IGNORECASE,
)
_TABLE_CELL_PATTERN = re.compile(
    r'<(td|th)(\s[^>]*)?>',
    re.IGNORECASE,
)

# 列表相关的正则表达式
_UL_PATTERN = re.compile(r'<ul(\s[^>]*)?>', re.IGNORECASE)
_OL_PATTERN = re.compile(r'<ol(\s[^>]*)?>', re.IGNORECASE)
_LI_PATTERN = re.compile(r'<li(\s[^>]*)?>', re.IGNORECASE)


def _wrap_image(match: re.Match[str]) -> str:
    before_src = match.group(1)
    src = match.group(2)
    after_src = match.group(3)
    img_tag = f'<img {before_src}src="{src}"{after_src} style="cursor: pointer;">'
    return f'<a href="image:{src}" style="text-decoration: none;">{img_tag}</a>'


def _add_table_styles(html: str) -> str:
    """为表格添加内联样式，确保在Qt RichText中正确显示"""
    # Qt RichText可能不完全支持<thead>和<tbody>，所以需要简化表格结构
    # 移除<thead>和<tbody>标签，但保留其内容
    html = re.sub(r'</?thead>', '', html, flags=re.IGNORECASE)
    html = re.sub(r'</?tbody>', '', html, flags=re.IGNORECASE)
    
    # 为table标签添加样式（如果没有style属性）
    def add_table_style(match: re.Match[str]) -> str:
        attrs = match.group(1) or ""
        if 'style=' in attrs.lower():
            # 如果已有style，追加样式
            html_str = match.group(0)
            return re.sub(
                r'style="([^"]*)"',
                r'style="\1; border-collapse: collapse; border: 1px solid #ccc; margin: 4px 0;"',
                html_str,
                flags=re.IGNORECASE
            )
        else:
            return f'<table{attrs} style="border-collapse: collapse; border: 1px solid #ccc; margin: 4px 0;">'
    
    html = _TABLE_PATTERN.sub(add_table_style, html)
    
    # 为td和th标签添加样式
    def add_cell_style(match: re.Match[str]) -> str:
        tag = match.group(1)  # td or th
        attrs = match.group(2) or ""
        base_style = "border: 1px solid #ccc; padding: 4px 8px; text-align: left;"
        
        if tag.lower() == 'th':
            base_style += " font-weight: bold; background-color: #f0f0f0;"
        
        if 'style=' in attrs.lower():
            # 如果已有style，追加样式
            return re.sub(
                r'style="([^"]*)"',
                lambda m: f'style="{m.group(1)}; {base_style}"',
                match.group(0),
                flags=re.IGNORECASE
            )
        else:
            return f'<{tag}{attrs} style="{base_style}">'
    
    html = _TABLE_CELL_PATTERN.sub(add_cell_style, html)
    
    return html


def _add_list_styles(html: str) -> str:
    """为列表添加内联样式，确保在Qt RichText中正确显示"""
    # Qt RichText对列表支持有限，使用更兼容的方式
    # 使用简单的连字符作为无序列表的项目符号（更兼容）
    
    # 处理无序列表：将<ul>和<li>转换为带样式的<p>或<div>
    # 匹配整个<ul>...</ul>块
    def convert_ul(match: re.Match[str]) -> str:
        ul_content = match.group(0)
        # 提取所有<li>内容
        li_items = re.findall(r'<li[^>]*>(.*?)</li>', ul_content, re.IGNORECASE | re.DOTALL)
        # 生成带项目符号的div（使用简单的-符号，确保兼容性）
        result_parts = []
        for item in li_items:
            # 使用更简单的样式，确保Qt RichText能正确渲染
            result_parts.append(
                '<div style="margin: 4px 0; padding-left: 20px;">- ' + item + '</div>'
            )
        return ''.join(result_parts)
    
    # 匹配<ul>...</ul>
    ul_pattern = re.compile(r'<ul[^>]*>.*?</ul>', re.IGNORECASE | re.DOTALL)
    html = ul_pattern.sub(convert_ul, html)
    
    # 处理有序列表：将<ol>和<li>转换为带编号的<div>
    def convert_ol(match: re.Match[str]) -> str:
        ol_content = match.group(0)
        # 提取所有<li>内容
        li_items = re.findall(r'<li[^>]*>(.*?)</li>', ol_content, re.IGNORECASE | re.DOTALL)
        # 生成带编号的div
        result_parts = []
        for i, item in enumerate(li_items, 1):
            result_parts.append(
                f'<div style="margin: 4px 0; padding-left: 20px;">{i}. {item}</div>'
            )
        return ''.join(result_parts)
    
    # 匹配<ol>...</ol>
    ol_pattern = re.compile(r'<ol[^>]*>.*?</ol>', re.IGNORECASE | re.DOTALL)
    html = ol_pattern.sub(convert_ol, html)
    
    return html


def render_markdown(content: str | None) -> str:
    """
    将 Markdown/HTML 内容渲染成 HTML，并为 <img> 自动添加点击链接，为表格添加样式。
    """
    if not content:
        return ""

    processed = content.replace("\r\n", "\n")
    stripped = processed.strip()

    if stripped.startswith("<") and stripped.endswith(">"):
        html = processed.replace("\n", "<br>") if "\n" in processed else processed
    else:
        # 使用 extra 扩展，它包含了表格支持（tables是extra的子扩展）
        html = markdown.markdown(
            processed, 
            extensions=["extra", "sane_lists"]
        )

    # 为表格添加样式
    html = _add_table_styles(html)
    # 为列表添加样式
    html = _add_list_styles(html)
    # 为图片添加点击链接
    html = _IMG_PATTERN.sub(_wrap_image, html)
    
    return html


def load_markdown_file(path: Union[str, Path]) -> str:
    """
    读取 Markdown 文件并返回原始文本。
    """
    file_path = Path(path)
    return file_path.read_text(encoding="utf-8")
