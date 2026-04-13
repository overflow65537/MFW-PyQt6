from __future__ import annotations

from pathlib import Path
import re
from typing import Callable

from PySide6.QtCore import QEvent, QObject, Qt, Signal
from PySide6.QtGui import QColor, QImage, QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsBlurEffect,
    QGridLayout,
    QHBoxLayout,
    QLabel,
 
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
    SimpleCardWidget,
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
    "__version__",
    "v0.0.1"
  
)


class _ActionCard(SimpleCardWidget):
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
        self.setClickEnabled(False)
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

    def mousePressEvent(self, e) -> None:  # noqa: N802
        if e.button() == Qt.MouseButton.LeftButton:
            if self._action_button is not None:
                child = self.childAt(e.position().toPoint())
                if child is self._action_button or (
                    child is not None and self._action_button.isAncestorOf(child)
                ):
                    super().mousePressEvent(e)
                    return
            self.clicked.emit()
            e.accept()
            return
        super().mousePressEvent(e)


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
        self._hero_cover_stage: QFrame | None = None
        self._hero_cover_backdrop: QLabel | None = None
        self._hero_cover_label: QLabel | None = None
        self._hero_cover_pixmap: QPixmap | None = None
        self._hero_title_label: BodyLabel | None = None
        self._hero_cover_needs_refresh = True

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

        box = QHBoxLayout(card)
        box.setContentsMargins(28, 26, 28, 24)
        box.setSpacing(18)

        text_col = QVBoxLayout()
        text_col.setContentsMargins(0, 0, 0, 0)
        text_col.setSpacing(6)

        title = BodyLabel(self._get_hero_title(), card)
        title.setObjectName("V5HeroTitle")
        text_col.addWidget(title)
        self._hero_title_label = title

        subtitle = BodyLabel(self._get_hero_subtitle(), card)
        subtitle.setObjectName("V5HeroSubtitle")
        subtitle.setWordWrap(True)
        text_col.addWidget(subtitle)
        text_col.addStretch(1)

        version = BodyLabel(
            self.tr("FrameWork Version")+f" {self._get_hero_maafw_version()}  ·  UI {UI_VERSION}",
            card,
        )
        version.setObjectName("V5HeroVersion")
        text_col.addWidget(version)
        box.addLayout(text_col, 7)

        cover_stage = QFrame(card)
        cover_stage.setObjectName("V5HeroImageStage")
        cover_stage.setFixedSize(300, 150)
        cover_stage.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        cover_stage.installEventFilter(self)
        self._hero_cover_stage = cover_stage

        backdrop = QLabel(cover_stage)
        backdrop.setObjectName("V5HeroImageBackdrop")
        backdrop.setAlignment(Qt.AlignmentFlag.AlignCenter)
        backdrop.hide()
        blur = QGraphicsBlurEffect(backdrop)
        blur.setBlurRadius(28)
        backdrop.setGraphicsEffect(blur)
        self._hero_cover_backdrop = backdrop

        cover = QLabel(cover_stage)
        cover.setObjectName("V5HeroImage")
        cover.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cover.hide()
        self._hero_cover_label = cover

        box.addStretch(1)
        box.addWidget(cover_stage, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self._apply_hero_cover(cfg.get(cfg.home_cover_image_path) or "")

        return card

    def _build_release_note_card(self) -> QWidget:
        card = SimpleCardWidget(self)
        card.setObjectName("V5SystemCard")
        card.setClickEnabled(False)

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
        if (
            self._hero_cover_label is None
            or self._hero_cover_backdrop is None
            or self._hero_cover_stage is None
            or self._hero_card is None
        ):
            return

        resolved_path = self._resolve_hero_cover_path(image_path)
        if not resolved_path:
            self._clear_hero_cover()
            return

        image_file = Path(resolved_path)
        if not image_file.is_file():
            self._clear_hero_cover()
            return

        pixmap = QPixmap(str(image_file))
        if pixmap.isNull():
            self._clear_hero_cover()
            return

        self._hero_cover_pixmap = pixmap
        self._hero_cover_stage.show()
        self._apply_hero_palette(pixmap.toImage())
        self._update_hero_cover_layout()

    def _clear_hero_cover(self) -> None:
        self._hero_cover_pixmap = None
        if self._hero_cover_label is not None:
            self._hero_cover_label.clear()
            self._hero_cover_label.hide()
        if self._hero_cover_backdrop is not None:
            self._hero_cover_backdrop.clear()
            self._hero_cover_backdrop.hide()
        if self._hero_cover_stage is not None:
            self._hero_cover_stage.hide()
        self._apply_hero_palette(None)

    def _resolve_hero_cover_path(self, requested_path: str) -> str:
        path = str(requested_path or "").strip()
        if path and Path(path).is_file():
            return path

        interface_path = getattr(self.service_coordinator, "interface_path", None)
        if interface_path:
            interface_dir = Path(interface_path).expanduser().resolve().parent
            for candidate_name in (
                "dashboard.jpg",
                "dashboard.jpeg",
                "dashboard.png",
                "dashboard.webp",
            ):
                candidate = interface_dir / candidate_name
                if candidate.is_file():
                    return str(candidate)
        return ""

    def _apply_hero_palette(self, image: QImage | None) -> None:
        if self._hero_card is None or self._hero_cover_stage is None:
            return

        if image is None or image.isNull():
            start = QColor("#293e66")
            middle = QColor("#5965a5")
            end = QColor("#2a2f5f")
        else:
            start, middle, end = self._extract_cover_palette(image)

        border = self._mix_colors(middle, QColor("#ffffff"), 0.18)
        stage_fill = self._mix_colors(end, QColor("#ffffff"), 0.12)
        stage_border = self._mix_colors(end, QColor("#ffffff"), 0.30)
        image_fill = self._mix_colors(start, QColor("#101318"), 0.58)

        self._hero_card.setStyleSheet(
            "\n".join(
                [
                    "QFrame#V5HeroCard {",
                    "    border-radius: 16px;",
                    f"    border: 1px solid {self._color_to_rgba(border, 0.88)};",
                    "    background: qlineargradient(",
                    "        x1: 0, y1: 0, x2: 1, y2: 1,",
                    f"        stop: 0 {self._color_to_rgba(start)} ,",
                    f"        stop: 0.58 {self._color_to_rgba(middle)} ,",
                    f"        stop: 1 {self._color_to_rgba(end)}",
                    "    );",
                    "}",
                    "QFrame#V5HeroImageStage {",
                    "    border-radius: 18px;",
                    f"    border: 1px solid {self._color_to_rgba(stage_border, 0.72)};",
                    f"    background-color: {self._color_to_rgba(stage_fill, 0.24)};",
                    "}",
                    "QLabel#V5HeroImageBackdrop {",
                    "    border-radius: 16px;",
                    "    background: transparent;",
                    "}",
                    "QLabel#V5HeroImage {",
                    "    border-radius: 14px;",
                    f"    border: 1px solid {self._color_to_rgba(QColor('#ffffff'), 0.18)};",
                    f"    background-color: {self._color_to_rgba(image_fill, 0.34)};",
                    "}",
                ]
            )
        )

    def _update_hero_cover_layout(self) -> None:
        if (
            self._hero_cover_stage is None
            or self._hero_cover_backdrop is None
            or self._hero_cover_label is None
            or self._hero_cover_pixmap is None
        ):
            return

        stage_rect = self._hero_cover_stage.contentsRect().adjusted(10, 10, -10, -10)
        if stage_rect.width() <= 0 or stage_rect.height() <= 0:
            return

        backdrop_rect = stage_rect.adjusted(4, 4, -4, -4)
        image_rect = stage_rect.adjusted(18, 14, -18, -14)
        if image_rect.width() <= 0 or image_rect.height() <= 0:
            return

        backdrop = self._hero_cover_pixmap.scaled(
            backdrop_rect.size(),
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation,
        )
        self._hero_cover_backdrop.setGeometry(backdrop_rect)
        self._hero_cover_backdrop.setPixmap(backdrop)
        self._hero_cover_backdrop.lower()
        self._hero_cover_backdrop.show()

        image = self._hero_cover_pixmap.scaled(
            image_rect.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        pos_x = image_rect.x() + max(0, (image_rect.width() - image.width()) // 2)
        pos_y = image_rect.y() + max(0, (image_rect.height() - image.height()) // 2)
        self._hero_cover_label.setGeometry(pos_x, pos_y, image.width(), image.height())
        self._hero_cover_label.setPixmap(image)
        self._hero_cover_label.raise_()
        self._hero_cover_label.show()

    def _extract_cover_palette(self, image: QImage) -> tuple[QColor, QColor, QColor]:
        sample = image.convertToFormat(QImage.Format.Format_RGB32).scaled(
            36,
            36,
            Qt.AspectRatioMode.IgnoreAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        start = self._tune_color(
            self._average_image_color(sample, 0.0, 0.55, 0.0, 1.0),
            saturation_factor=0.92,
            lightness_shift=-52,
        )
        middle = self._tune_color(
            self._average_image_color(sample, 0.15, 0.85, 0.0, 1.0),
            saturation_factor=1.08,
            lightness_shift=-18,
        )
        end = self._tune_color(
            self._average_image_color(sample, 0.55, 1.0, 0.0, 1.0),
            saturation_factor=1.2,
            lightness_shift=4,
        )
        return start, middle, end

    def _average_image_color(
        self,
        image: QImage,
        x_start: float,
        x_end: float,
        y_start: float,
        y_end: float,
    ) -> QColor:
        width = image.width()
        height = image.height()
        if width <= 0 or height <= 0:
            return QColor("#445b89")

        start_x = max(0, min(width - 1, int(width * x_start)))
        end_x = max(start_x + 1, min(width, int(width * x_end)))
        start_y = max(0, min(height - 1, int(height * y_start)))
        end_y = max(start_y + 1, min(height, int(height * y_end)))

        red = 0
        green = 0
        blue = 0
        count = 0
        for pos_y in range(start_y, end_y):
            for pos_x in range(start_x, end_x):
                color = image.pixelColor(pos_x, pos_y)
                red += color.red()
                green += color.green()
                blue += color.blue()
                count += 1

        if count == 0:
            return QColor("#445b89")
        return QColor(red // count, green // count, blue // count)

    def _tune_color(
        self,
        color: QColor,
        *,
        saturation_factor: float,
        lightness_shift: int,
    ) -> QColor:
        hue = color.hslHue()
        saturation = color.hslSaturation()
        lightness = color.lightness()
        alpha = color.alpha()
        if hue < 0:
            hue = 210
        saturation = max(36, min(255, int(saturation * saturation_factor)))
        lightness = max(24, min(210, lightness + lightness_shift))
        return QColor.fromHsl(hue, saturation, lightness, alpha)

    def _mix_colors(self, first: QColor, second: QColor, ratio: float) -> QColor:
        ratio = max(0.0, min(1.0, ratio))
        inv_ratio = 1.0 - ratio
        return QColor(
            int(first.red() * inv_ratio + second.red() * ratio),
            int(first.green() * inv_ratio + second.green() * ratio),
            int(first.blue() * inv_ratio + second.blue() * ratio),
        )

    def _color_to_rgba(self, color: QColor, alpha: float = 1.0) -> str:
        bounded_alpha = max(0.0, min(1.0, alpha))
        alpha_value = int(round(bounded_alpha * 255))
        return f"rgba({color.red()}, {color.green()}, {color.blue()}, {alpha_value})"

    def _on_home_cover_image_changed(self, path: str) -> None:
        self._apply_hero_cover(path)
        self._hero_cover_needs_refresh = False

    def showEvent(self, event) -> None:  # noqa: N802
        super().showEvent(event)
        if self._hero_cover_needs_refresh or self._hero_cover_pixmap is None:
            self._hero_cover_needs_refresh = False
            self._apply_hero_cover(cfg.get(cfg.home_cover_image_path) or "")

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if (
            watched in (self._hero_card, self._hero_cover_stage)
            and event.type() == QEvent.Type.Resize
            and self._hero_cover_label is not None
        ):
            if self._hero_cover_pixmap is None:
                self._apply_hero_cover(cfg.get(cfg.home_cover_image_path) or "")
            else:
                self._update_hero_cover_layout()
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
