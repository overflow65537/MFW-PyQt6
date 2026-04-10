from __future__ import annotations

from typing import Callable

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)
from qfluentwidgets import (
    BodyLabel,
    CaptionLabel,
    FluentIcon as FIF,
    IconWidget,
    PrimaryPushButton,
)

from app.common import __version__ as version_meta
from app.core.core import ServiceCoordinator
from app.utils.release_notes import load_release_notes, resolve_project_name

APP_VERSION = getattr(version_meta, "__version__", "Unknown")
UI_VERSION = getattr(version_meta, "__ui_version__", APP_VERSION)


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

        arrow = QLabel("›", self)
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
        self._recent_notes_limit = 3

        self._init_ui()

    def _init_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea(self)
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

        box = QVBoxLayout(card)
        box.setContentsMargins(28, 26, 28, 24)
        box.setSpacing(6)

        title = QLabel(f"MFW {UI_VERSION}", card)
        title.setObjectName("V5HeroTitle")
        box.addWidget(title)

        subtitle = QLabel(self.tr("A More Modern Console Interface"), card)
        subtitle.setObjectName("V5HeroSubtitle")
        box.addWidget(subtitle)
        box.addStretch(1)

        version = QLabel(f"App {APP_VERSION}  ·  UI {UI_VERSION}", card)
        version.setObjectName("V5HeroVersion")
        box.addWidget(version, 0, Qt.AlignmentFlag.AlignRight)

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

        notes = self._get_recent_release_notes(self._recent_notes_limit)
        if not notes:
            empty_label = QLabel(
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

        for version, preview in notes:
            row = QWidget(card)
            row_box = QVBoxLayout(row)
            row_box.setContentsMargins(0, 0, 0, 0)
            row_box.setSpacing(2)

            version_label = QLabel(version, row)
            version_label.setObjectName("V5InfoValue")
            row_box.addWidget(version_label)

            preview_label = QLabel(preview, row)
            preview_label.setObjectName("V5InfoKey")
            preview_label.setWordWrap(True)
            row_box.addWidget(preview_label)

            box.addWidget(row)

        hint = QLabel(
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

    def _get_recent_release_notes(self, limit: int) -> list[tuple[str, str]]:
        project_name = resolve_project_name(self._get_interface_metadata())
        notes = load_release_notes(project_name)
        items = list(notes.items())[: max(0, int(limit))]
        return [(version, self._summarize_markdown(content)) for version, content in items]

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
