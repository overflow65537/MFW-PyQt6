from __future__ import annotations

import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QVBoxLayout, QWidget
from qfluentwidgets import BodyLabel, ScrollArea

from app.view.task_interface.components.option_widget import (
    setup_description_content_layout,
)

_LONG_HTML = """
<p><b>战斗模式</b></p>
<div style="margin: 4px 0; padding-left: 20px;">- 关卡需要解密或跑图且角色仍在战斗时，使用自动检测模式。</div>
<div style="margin: 4px 0; padding-left: 20px;">- 关卡无剧情或解密，进入地图即可战斗但角色未开打时，使用持续战斗模式。</div>
<h3>速通模式</h3>
<div style="margin: 4px 0; padding-left: 20px;">- 开启：自动选择下一章并尝试开启速通模式后进入战斗或剧情。</div>
<div style="margin: 4px 0; padding-left: 20px;">- 关闭：不会选择下一章。</div>
<h3>跳过剧情</h3>
<div style="margin: 4px 0; padding-left: 20px;">- 开启后自动点击跳过，并处理确认弹窗。这段文字故意写长一点以便换行。</div>
<div style="margin: 4px 0; padding-left: 20px;">- 关闭后保留剧情，需要手动操作。这段文字也故意写长一点。</div>
<p>补充说明。补充说明。补充说明。补充说明。补充说明。补充说明。</p>
"""


class TestDescriptionContentHeight(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def _mount(self, width: int, height: int) -> tuple[QWidget, BodyLabel, ScrollArea]:
        label = BodyLabel()
        label.setWordWrap(True)
        label.setTextFormat(Qt.TextFormat.RichText)
        label.setText(_LONG_HTML)

        inner = QWidget()
        layout = QVBoxLayout(inner)
        layout.setContentsMargins(10, 10, 10, 10)
        setup_description_content_layout(layout, label)
        self.assertFalse(layout.alignment() & Qt.AlignmentFlag.AlignTop)

        scroll = ScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setWidget(inner)

        host = QWidget()
        host_layout = QVBoxLayout(host)
        host_layout.setContentsMargins(0, 0, 0, 0)
        host_layout.addWidget(scroll)
        host.resize(width, height)
        host.show()
        self.app.processEvents()
        return host, label, scroll

    def test_long_rich_text_keeps_wrapped_height_and_can_scroll(self):
        host, label, scroll = self._mount(420, 220)
        self.addCleanup(host.close)

        needed = label.heightForWidth(label.width())
        self.assertGreater(needed, scroll.viewport().height())
        self.assertGreaterEqual(label.height(), needed)

        margins = label.parentWidget().layout().contentsMargins()
        reach = scroll.verticalScrollBar().maximum() + scroll.viewport().height()
        self.assertGreaterEqual(
            reach, label.height() + margins.top() + margins.bottom()
        )

        host.resize(260, 220)
        self.app.processEvents()
        needed = label.heightForWidth(label.width())
        self.assertGreaterEqual(label.height(), needed)
        reach = scroll.verticalScrollBar().maximum() + scroll.viewport().height()
        self.assertGreaterEqual(
            reach, label.height() + margins.top() + margins.bottom()
        )


if __name__ == "__main__":
    unittest.main()
