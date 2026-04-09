from __future__ import annotations

import platform
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
from app.utils.gpu_cache import gpu_cache

try:
    import psutil
except Exception:
    psutil = None

try:
    import wmi as wmi_module
except Exception:
    wmi_module = None

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
        layout.addWidget(self._build_system_card())
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

        subtitle = QLabel("更现代的控制台界面", card)
        subtitle.setObjectName("V5HeroSubtitle")
        box.addWidget(subtitle)
        box.addStretch(1)

        version = QLabel(f"App {APP_VERSION}  ·  UI {UI_VERSION}", card)
        version.setObjectName("V5HeroVersion")
        box.addWidget(version, 0, Qt.AlignmentFlag.AlignRight)

        return card

    def _build_system_card(self) -> QWidget:
        card = QFrame(self)
        card.setObjectName("V5SystemCard")

        box = QVBoxLayout(card)
        box.setContentsMargins(22, 18, 22, 18)
        box.setSpacing(10)

        header = BodyLabel("系统信息", card)
        header.setObjectName("V5SectionTitle")
        box.addWidget(header)

        info_grid = QGridLayout()
        info_grid.setHorizontalSpacing(36)
        info_grid.setVerticalSpacing(10)

        rows = self._collect_system_info()
        for row_index, (name, value) in enumerate(rows):
            k = QLabel(name, card)
            k.setObjectName("V5InfoKey")
            v = QLabel(value, card)
            v.setObjectName("V5InfoValue")
            v.setWordWrap(True)
            info_grid.addWidget(k, row_index, 0)
            info_grid.addWidget(v, row_index, 1)

        box.addLayout(info_grid)
        return card

    def _build_action_grid(self):
        grid = QGridLayout()
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(14)

        cards = [
            (
                FIF.CHECKBOX,
                "任务流程",
                "配置并执行自动化任务",
                self._open_task,
                self.tr("Start"),
                self._start_task,
            ),
            (
                FIF.PROJECTOR,
                "实时监控",
                "查看识别画面与状态输出",
                self._open_monitor,
                None,
                None,
            ),
            (
                FIF.CALENDAR,
                "计划任务",
                "设置定时运行与强制启动",
                self._open_schedule,
                None,
                None,
            ),
            (
                FIF.SETTING,
                "系统设置",
                "主题、更新与资源管理",
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

    def _collect_system_info(self) -> list[tuple[str, str]]:
        os_version = self._get_os_version_text()
        arch = self._get_arch_text()
        cpu = self._get_cpu_text()
        gpu = self._get_gpu_text()
        memory = self._get_memory_text()

        return [
            ("版本", os_version),
            ("架构", arch),
            ("CPU", cpu),
            ("GPU", gpu),
            ("内存", memory),
        ]

    def _get_os_version_text(self) -> str:
        if platform.system().lower() == "windows":
            try:
                if wmi_module is not None:
                    conn = wmi_module.WMI()
                    os_info = conn.Win32_OperatingSystem()[0]
                    caption = str(getattr(os_info, "Caption", "")).replace(
                        "Microsoft ", ""
                    )
                    build = str(getattr(os_info, "BuildNumber", "")).strip()
                    if caption and build:
                        return f"{caption} Build {build}"
                    if caption:
                        return caption
            except Exception:
                pass
        return platform.platform(aliased=True, terse=True) or "Unknown"

    def _get_arch_text(self) -> str:
        if platform.system().lower() == "windows":
            try:
                if wmi_module is not None:
                    conn = wmi_module.WMI()
                    os_info = conn.Win32_OperatingSystem()[0]
                    arch = str(getattr(os_info, "OSArchitecture", "")).strip()
                    if arch:
                        return arch.replace("-bit", " 位")
            except Exception:
                pass
        return "64 位" if "64" in platform.architecture()[0] else "32 位"

    def _get_cpu_text(self) -> str:
        if platform.system().lower() == "windows":
            try:
                if wmi_module is not None:
                    conn = wmi_module.WMI()
                    processors = conn.Win32_Processor()
                    if processors:
                        cpu_name = str(getattr(processors[0], "Name", "")).strip()
                        if cpu_name:
                            return cpu_name
            except Exception:
                pass
        return platform.processor() or platform.machine() or "Unknown"

    def _get_gpu_text(self) -> str:
        names: list[str] = []
        try:
            cache_info = gpu_cache.get_gpu_info()
            names.extend([str(v).strip() for v in cache_info.values() if str(v).strip()])
        except Exception:
            pass

        if not names and platform.system().lower() == "windows":
            try:
                if wmi_module is not None:
                    conn = wmi_module.WMI()
                    adapters = conn.Win32_VideoController()
                    names.extend(
                        [
                            str(getattr(item, "Name", "")).strip()
                            for item in adapters
                            if str(getattr(item, "Name", "")).strip()
                        ]
                    )
            except Exception:
                pass

        # 去重并保持顺序
        unique_names: list[str] = []
        for name in names:
            if name not in unique_names:
                unique_names.append(name)

        if not unique_names:
            return "Unknown"
        return " / ".join(unique_names)

    def _get_memory_text(self) -> str:

        if psutil is not None:
            try:
                total_gb = psutil.virtual_memory().total / (1024**3)
                return f"{total_gb:.1f} GB"
            except Exception:
                return "Unknown"
        return "Unknown"
