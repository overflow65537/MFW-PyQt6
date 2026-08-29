"""首次运行资源包时的安全确认对话框。"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget
from qfluentwidgets import (
    BodyLabel,
    CaptionLabel,
    MessageBoxBase,
    StrongBodyLabel,
    SubtitleLabel,
)

from app.utils.markdown_helper import render_markdown
from app.utils.rich_text_helper import apply_rich_text_html


class ResourceRunConfirmDialog(MessageBoxBase):
    """展示资源名称、联系方式和 GitHub，供用户确认后才允许运行。"""

    def __init__(
        self,
        parent: QWidget | None,
        *,
        resource_name: str,
        contact: str,
        github: str,
        github_owner: str = "",
        github_repo: str = "",
    ) -> None:
        super().__init__(parent)
        self.widget.setMinimumWidth(460)
        self.widget.setMinimumHeight(280)

        title = SubtitleLabel(self.tr("Confirm the resource you are about to run"), self)
        warning = BodyLabel(
            self.tr(
                "Please verify this is the resource pack you intend to use. "
                "This helps prevent MFW from running a malicious pack."
            ),
            self,
        )
        warning.setWordWrap(True)

        self.viewLayout.addWidget(title)
        self.viewLayout.addSpacing(6)
        self.viewLayout.addWidget(warning)
        self.viewLayout.addSpacing(12)
        self.viewLayout.addLayout(
            self._info_row(self.tr("Resource"), resource_name or self.tr("(unknown)"))
        )
        self.viewLayout.addLayout(self._contact_row(contact))
        self.viewLayout.addLayout(
            self._github_row(github, github_owner, github_repo)
        )

        self.yesButton.setText(self.tr("Confirm"))
        self.cancelButton.setText(self.tr("Cancel"))

    def _info_row(self, label: str, value: str) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(12)
        caption = CaptionLabel(label, self)
        caption.setFixedWidth(88)
        content = StrongBodyLabel(value, self)
        content.setWordWrap(True)
        content.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        row.addWidget(caption, 0, Qt.AlignmentFlag.AlignTop)
        row.addWidget(content, 1)
        return row

    def _contact_row(self, contact: str) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(12)
        caption = CaptionLabel(self.tr("Contact"), self)
        caption.setFixedWidth(88)
        content = BodyLabel(self)
        content.setWordWrap(True)
        content.setOpenExternalLinks(True)
        text = (contact or "").strip()
        if text:
            apply_rich_text_html(content, render_markdown(text))
        else:
            content.setText(self.tr("Not provided"))
        row.addWidget(caption, 0, Qt.AlignmentFlag.AlignTop)
        row.addWidget(content, 1)
        return row

    def _github_row(
        self,
        github: str,
        github_owner: str,
        github_repo: str,
    ) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(12)
        caption = CaptionLabel(self.tr("GitHub"), self)
        caption.setFixedWidth(88)
        url = (github or "").strip()
        owner = (github_owner or "").strip()
        repo = (github_repo or "").strip()
        if owner and repo:
            value = QWidget(self)
            value_layout = QVBoxLayout(value)
            value_layout.setContentsMargins(0, 0, 0, 0)
            value_layout.setSpacing(2)
            title = StrongBodyLabel(f"{owner} / {repo}", value)
            title.setWordWrap(True)
            title.setTextInteractionFlags(
                Qt.TextInteractionFlag.TextSelectableByMouse
            )
            value_layout.addWidget(title)
            if url:
                value_layout.addWidget(self._github_url_label(url, value))
            row.addWidget(caption, 0, Qt.AlignmentFlag.AlignTop)
            row.addWidget(value, 1)
        elif url:
            row.addWidget(caption, 0, Qt.AlignmentFlag.AlignTop)
            row.addWidget(self._github_url_label(url, self), 1)
        else:
            content = BodyLabel(self.tr("Not provided"), self)
            row.addWidget(caption, 0, Qt.AlignmentFlag.AlignTop)
            row.addWidget(content, 1)
        return row

    def _github_url_label(self, url: str, parent: QWidget) -> BodyLabel:
        content = BodyLabel(parent)
        content.setWordWrap(True)
        content.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
            | Qt.TextInteractionFlag.LinksAccessibleByMouse
        )
        if url.lower().startswith(("http://", "https://")):
            content.setOpenExternalLinks(True)
            content.setTextFormat(Qt.TextFormat.RichText)
            escaped = (
                url.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            )
            content.setText(f'<a href="{escaped}">{escaped}</a>')
        else:
            content.setText(url)
        return content
