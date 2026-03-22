"""
基于 Qt .ts 文件的运行时翻译器。

用途：
- 开发环境未生成 .qm 文件时，仍可根据 .ts 翻译 UI 文案。
- 优先用于兜底，不替代正式 .qm 加载流程。
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Tuple
from defusedxml import ElementTree as ET

from PySide6.QtCore import QTranslator


class TsTranslator(QTranslator):
    """从 .ts 文件加载翻译映射并参与 Qt 翻译链。"""

    def __init__(self) -> None:
        super().__init__()
        self._context_map: Dict[Tuple[str, str], str] = {}
        self._global_map: Dict[str, str] = {}

    def load_ts(self, ts_path: str | Path) -> bool:
        """加载 .ts 文件。"""
        path = Path(ts_path)
        if not path.exists():
            return False

        try:
            root = ET.parse(path).getroot()
        except ET.ParseError:
            return False

        self._context_map.clear()
        self._global_map.clear()

        for context in root.findall("context"):
            name_node = context.find("name")
            context_name = (name_node.text or "") if name_node is not None else ""

            for message in context.findall("message"):
                source_node = message.find("source")
                translation_node = message.find("translation")
                if source_node is None or translation_node is None:
                    continue

                source_text = source_node.text or ""
                translated_text = translation_node.text or ""
                if not source_text or not translated_text:
                    continue

                self._context_map[(context_name, source_text)] = translated_text
                self._global_map.setdefault(source_text, translated_text)

        return bool(self._context_map or self._global_map)

    def translate(self, context, sourceText, disambiguation=None, n=-1):
        """按 Qt 调用约定返回翻译文本；未命中时返回 None。"""
        if not sourceText:
            return None

        translated = self._context_map.get((context or "", sourceText))
        if translated:
            return translated

        translated = self._global_map.get(sourceText)
        if translated:
            return translated

        return None
