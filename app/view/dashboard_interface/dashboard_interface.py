from __future__ import annotations

from pathlib import Path
import re
from typing import Callable

from PySide6.QtCore import QEvent, QObject, Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
 
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    BodyLabel,
    CaptionLabel,
    FluentIcon as FIF,
    ScrollArea,
    IconWidget,
    PrimaryPushButton,
)

from app.common.config import cfg
from app.common.signal_bus import signalBus
from app.common import __version__ as version_meta
        
from app.core.core import ServiceCoordinator
from app.utils.markdown_helper import render_markdown
from app.utils.release_notes import load_release_notes, resolve_project_name

from maa.library import Library

MAAFW_VERSION = Library.version()
UI_VERSION = getattr(
    version_meta,
    "__ui_version__",
    getattr(version_meta, "__version__", "Unknown"),
)


class _ActionCard(QFrame):
    clicked = Signal()

    def __init__(
        self,
        *,
        icon,
        title: str,
        description: str,
        on_click: Callable[[], None] | None = None,
        action_text: str | None = None,
        on_action_click: Callable[[], None] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("V5ActionCard")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setFixedHeight(110)
        self._action_button: PrimaryPushButton | None = None

        root = QHBoxLayout(self)
        root.setContentsMargins(18, 14, 18, 14)
        root.setSpacing(12)

        icon_widget = IconWidget(icon, self)
        icon_widget.setFixedSize(26, 26)
        root.addWidget(icon_widget, 0, Qt.AlignmentFlag.AlignTop)

        text_col = QVBoxLayout()
        text_col.setContentsMargins(0, 0, 0, 0)
        text_col.setSpacing(4)

        title_label = BodyLabel(title, self)
        title_label.setObjectName("V5ActionTitle")
        text_col.addWidget(title_label)

        desc_label = CaptionLabel(description, self)
        desc_label.setObjectName("V5ActionDesc")
        desc_label.setWordWrap(True)
        text_col.addWidget(desc_label)
        root.addLayout(text_col, 1)

        if action_text:
            self._action_button = PrimaryPushButton(action_text, self)
            self._action_button.setFixedHeight(34)
            if on_action_click is not None:
                self._action_button.clicked.connect(on_action_click)
            root.addWidget(self._action_button, 0, Qt.AlignmentFlag.AlignVCenter)

        arrow = BodyLabel("›", self)
        arrow.setObjectName("V5ActionArrow")
        root.addWidget(arrow, 0, Qt.AlignmentFlag.AlignVCenter)

        if on_click is not None:
            self.clicked.connect(on_click)

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            if self._action_button is not None:
                child = self.childAt(event.position().toPoint())
                if child is self._action_button or (
                    child is not None and self._action_button.isAncestorOf(child)
                ):
                    super().mousePressEvent(event)
                    return
            self.clicked.emit()
            event.accept()
            return
        super().mousePressEvent(event)


class DashboardInterface(QWidget):
    def __init__(
        self,
        service_coordinator: ServiceCoordinator,
        *,
        open_task: Callable[[], None] | None = None,
        start_task: Callable[[], None] | None = None,
        open_monitor: Callable[[], None] | None = None,
        open_schedule: Callable[[], None] | None = None,
        open_setting: Callable[[], None] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent=parent)
        self.setObjectName("DashboardInterface")
        self.service_coordinator = service_coordinator

        self._open_task = open_task
        self._start_task = start_task
        self._open_monitor = open_monitor
        self._open_schedule = open_schedule
        self._open_setting = open_setting
        self._hero_card: QFrame | None = None
        self._hero_cover_label: BodyLabel | None = None
        self._hero_title_label: BodyLabel | None = None

        self._init_ui()
        signalBus.home_cover_image_changed.connect(self._on_home_cover_image_changed)

    def _init_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        scroll = ScrollArea(self)
        scroll.setObjectName("V5DashboardScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        root.addWidget(scroll)

        content = QWidget(self)
        content.setObjectName("V5DashboardContent")
        scroll.setWidget(content)

        layout = QVBoxLayout(content)
        layout.setContentsMargins(24, 20, 24, 24)
        layout.setSpacing(16)

        layout.addWidget(self._build_hero_card())
        layout.addWidget(self._build_release_note_card())
        layout.addLayout(self._build_action_grid())
        layout.addStretch(1)

    def _build_hero_card(self) -> QWidget:
        card = QFrame(self)
        card.setObjectName("V5HeroCard")
        card.setFixedHeight(210)
        card.installEventFilter(self)
        self._hero_card = card

        cover = BodyLabel(card)
        cover.setObjectName("V5HeroCover")
        cover.setScaledContents(True)
        cover.hide()
        self._hero_cover_label = cover

        box = QVBoxLayout(card)
        box.setContentsMargins(28, 26, 28, 24)
        box.setSpacing(6)

        title = BodyLabel(self._get_hero_title(), card)
        title.setObjectName("V5HeroTitle")
        box.addWidget(title)
        self._hero_title_label = title

        subtitle = BodyLabel(self._get_hero_subtitle(), card)
        subtitle.setObjectName("V5HeroSubtitle")
        subtitle.setWordWrap(True)
        box.addWidget(subtitle)
        box.addStretch(1)

        version = BodyLabel(
            self.tr("FrameWork Version")+f" {self._get_hero_maafw_version()}  ·  UI {UI_VERSION}",
            card,
        )
        version.setObjectName("V5HeroVersion")
        box.addWidget(version, 0, Qt.AlignmentFlag.AlignRight)
        self._apply_hero_cover(cfg.get(cfg.home_cover_image_path) or "")

        return card

    def _build_release_note_card(self) -> QWidget:
        card = QFrame(self)
        card.setObjectName("V5SystemCard")

        box = QVBoxLayout(card)
        box.setContentsMargins(22, 18, 22, 18)
        box.setSpacing(10)

        header = BodyLabel(self.tr("Update Log"), card)
        header.setObjectName("V5SectionTitle")
        box.addWidget(header)

        note = self._get_latest_release_note()
        if note is None:
            empty_label = BodyLabel(
                self.tr(
                    "No update log found locally.\n\n"
                    "Please check for updates first, or visit the GitHub releases page."
                ),
                card,
            )
            empty_label.setObjectName("V5InfoValue")
            empty_label.setWordWrap(True)
            box.addWidget(empty_label)
            return card

        version, content = note

        version_label = BodyLabel(version, card)
        version_label.setObjectName("V5InfoValue")
        box.addWidget(version_label)

        content_label = BodyLabel(card)
        content_label.setObjectName("V5InfoKey")
        content_label.setWordWrap(True)
        content_label.setTextFormat(Qt.TextFormat.RichText)
        content_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextBrowserInteraction
        )
        content_label.setOpenExternalLinks(True)
        content_label.setText(render_markdown(content))
        box.addWidget(content_label)

        hint = BodyLabel(
            self.tr("View full changelog in Settings > Open update log."),
            card,
        )
        hint.setObjectName("V5InfoKey")
        hint.setWordWrap(True)
        box.addWidget(hint)
        return card

    def _build_action_grid(self):
        grid = QGridLayout()
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(14)

        cards = [
            (
                FIF.CHECKBOX,
                self.tr("Task"),
                self.tr("Configure and execute automation tasks"),
                self._open_task,
                self.tr("Start"),
                self._start_task,
            ),
            (
                FIF.PROJECTOR,
                self.tr("Monitor"),
                self.tr("View real-time frames and runtime status"),
                self._open_monitor,
                None,
                None,
            ),
            (
                FIF.CALENDAR,
                self.tr("Schedule"),
                self.tr("Configure scheduled runs and force start"),
                self._open_schedule,
                None,
                None,
            ),
            (
                FIF.SETTING,
                self.tr("Setting"),
                self.tr("Theme, update, and resource management"),
                self._open_setting,
                None,
                None,
            ),
        ]

        for i, (icon, title, desc, callback, action_text, action_callback) in enumerate(
            cards
        ):
            card = _ActionCard(
                icon=icon,
                title=title,
                description=desc,
                on_click=callback,
                action_text=action_text,
                on_action_click=action_callback,
            )
            grid.addWidget(card, i // 2, i % 2)

        return grid

    def _get_interface_metadata(self) -> dict:
        interface_data = getattr(self.service_coordinator.task, "interface", None)
        return interface_data or {}

    def _get_hero_title(self) -> str:
        metadata = self._get_interface_metadata()
        for key in ("custom_title", "title", "name"):
            value = str(metadata.get(key, "") or "").strip()
            if value:
                return value
        concise_description = self._extract_concise_title_from_description(
            metadata.get("description", "")
        )
        if concise_description:
            return concise_description
        return f"MFW {UI_VERSION}"

    def _get_hero_subtitle(self) -> str:
        metadata = self._get_interface_metadata()
        raw_description = str(metadata.get("description", "") or "").strip()
        if not raw_description:
            return self.tr("A More Modern Console Interface")

        lines = [line.strip() for line in raw_description.splitlines() if line.strip()]
        if not lines:
            return self.tr("A More Modern Console Interface")

        subtitle = " ".join(lines)
        subtitle = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", subtitle)  # Markdown links
        subtitle = re.sub(r"[*_`~]+", "", subtitle).strip()
        return subtitle or self.tr("A More Modern Console Interface")

    def _get_hero_maafw_version(self) -> str:
        metadata = self._get_interface_metadata()
        current_version = str(metadata.get("version", "") or "").strip()
        return current_version or MAAFW_VERSION

    def _extract_concise_title_from_description(self, raw_description: object) -> str:
        text = str(raw_description or "").strip()
        if not text:
            return ""

        lines = [line.strip() for line in text.splitlines() if line.strip()]
        if not lines:
            return ""

        candidate = lines[0]
        candidate = re.sub(r"^#+\s*", "", candidate)  # Markdown heading
        candidate = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", candidate)  # Markdown links
        candidate = re.sub(r"[*_`~]+", "", candidate).strip()
        candidate = re.split(r"[。.!?；;，,\(\)\[\]【】|/\\]", candidate)[0].strip()

        if not candidate:
            return ""

        # 标题保持简洁，超长时截断
        if len(candidate) > 16:
            return candidate[:15].rstrip() + "…"
        return candidate

    def _apply_hero_cover(self, image_path: str) -> None:
        if self._hero_cover_label is None or self._hero_card is None:
            return

        path = str(image_path or "").strip()
        if not path:
            self._hero_cover_label.clear()
            self._hero_cover_label.hide()
            return

        image_file = Path(path)
        if not image_file.is_file():
            self._hero_cover_label.clear()
            self._hero_cover_label.hide()
            return

        pixmap = QPixmap(str(image_file))
        if pixmap.isNull():
            self._hero_cover_label.clear()
            self._hero_cover_label.hide()
            return

        target_size = self._hero_card.size()
        scaled = pixmap.scaled(
            target_size,
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation,
        )
        self._hero_cover_label.setGeometry(self._hero_card.rect())
        self._hero_cover_label.setPixmap(scaled)
        self._hero_cover_label.lower()
        self._hero_cover_label.show()

    def _on_home_cover_image_changed(self, path: str) -> None:
        self._apply_hero_cover(path)

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if (
            watched is self._hero_card
            and event.type() == QEvent.Type.Resize
            and self._hero_cover_label is not None
        ):
            self._apply_hero_cover(cfg.get(cfg.home_cover_image_path) or "")
        return super().eventFilter(watched, event)

    def _get_latest_release_note(self) -> tuple[str, str] | None:
        project_name = resolve_project_name(self._get_interface_metadata())
        notes = load_release_notes(project_name)
        return next(iter(notes.items()), None)

    def _summarize_markdown(self, text: str, max_len: int = 180) -> str:
        lines = []
        for raw in str(text or "").splitlines():
            line = raw.strip()
            if not line:
                continue
            if line.startswith("#"):
                line = line.lstrip("#").strip()
            if line.startswith("- "):
                line = line[2:].strip()
            lines.append(line)

        summary = " ".join(lines).strip()
        if not summary:
            return self.tr("No summary available")
        if len(summary) > max_len:
            return summary[: max_len - 1].rstrip() + "…"
        return summary
