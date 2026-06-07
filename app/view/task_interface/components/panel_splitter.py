from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QResizeEvent
from PySide6.QtWidgets import QSplitter, QWidget
from qfluentwidgets import isDarkTheme, qconfig

from app.common.config import cfg

PANEL_UNIT_WIDTH = 344
MAX_SIDE_PANEL_WIDTH = PANEL_UNIT_WIDTH * 2
MIN_OPTION_PANEL_WIDTH = PANEL_UNIT_WIDTH
PANEL_SPLITTER_GUTTER = 10
PANEL_EDGE_MARGIN = 20
PANEL_SECTION_SPACING = 8
HANDLE_LINE_MARGIN = 60
DEFAULT_PANEL_RATIOS = [1 / 3, 1 / 3, 1 / 3]


def panel_outer_margins() -> tuple[int, int, int, int]:
    """任务页整体外围留白：(左, 上, 右, 下)。"""
    edge = PANEL_EDGE_MARGIN
    return edge, edge, edge, edge


def panel_column_margins(column: str) -> tuple[int, int, int, int]:
    """返回栏内与分割条相邻的留白：(左, 上, 右, 下)。外围 8px 由任务页根布局负责。"""
    gutter = PANEL_SPLITTER_GUTTER
    if column == "task":
        return 0, 0, gutter, 0
    if column == "option":
        return gutter, 0, gutter, 0
    if column == "log":
        return gutter, 0, 0, 0
    raise ValueError(f"unknown panel column: {column}")


def _splitter_line_color() -> str:
    return "rgba(255, 255, 255, 0.25)" if isDarkTheme() else "rgba(0, 0, 0, 0.25)"


def splitter_handle_stylesheet(orientation: Qt.Orientation) -> str:
    line_color = _splitter_line_color()
    if orientation == Qt.Orientation.Horizontal:
        return f"""
            QSplitter::handle:horizontal {{
                width: 6px;
                margin: {HANDLE_LINE_MARGIN}px 0px;
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 transparent,
                    stop:0.45 transparent,
                    stop:0.5 {line_color},
                    stop:0.55 transparent,
                    stop:1 transparent
                );
            }}
            QSplitter::handle:horizontal:hover {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 transparent,
                    stop:0.42 transparent,
                    stop:0.5 rgba(128, 128, 128, 0.55),
                    stop:0.58 transparent,
                    stop:1 transparent
                );
            }}
        """
    return f"""
        QSplitter::handle:vertical {{
            height: 6px;
            margin: 0px {HANDLE_LINE_MARGIN}px;
            background: qlineargradient(
                x1:0, y1:0, x2:0, y2:1,
                stop:0 transparent,
                stop:0.45 transparent,
                stop:0.5 {line_color},
                stop:0.55 transparent,
                stop:1 transparent
            );
        }}
        QSplitter::handle:vertical:hover {{
            background: qlineargradient(
                x1:0, y1:0, x2:0, y2:1,
                stop:0 transparent,
                stop:0.42 transparent,
                stop:0.5 rgba(128, 128, 128, 0.55),
                stop:0.58 transparent,
                stop:1 transparent
            );
        }}
    """


class TaskInterfacePanelSplitter(QSplitter):
    """任务页三栏水平分割器。

    以 344px 为一格，任务/日志最多占 2 格并向选项区单侧扩展，选项区至少 1 格且可向左右扩展。
    """

    def __init__(self, parent: QWidget | None = None):
        super().__init__(Qt.Orientation.Horizontal, parent)
        self.setChildrenCollapsible(True)
        self.setHandleWidth(6)
        self._apply_handle_style()
        qconfig.themeChanged.connect(self._apply_handle_style)
        self._layout_ratios = list(DEFAULT_PANEL_RATIOS)
        self._applying_layout = False
        self._pending_ratios: list[float] | None = None
        self._layout_restored = False
        self._save_timer = QTimer(self)
        self._save_timer.setSingleShot(True)
        self._save_timer.timeout.connect(self._save_layout_to_config)
        self.splitterMoved.connect(self._on_splitter_moved)

    def _apply_handle_style(self) -> None:
        self.setStyleSheet(splitter_handle_stylesheet(Qt.Orientation.Horizontal))

    def _on_splitter_moved(self, _pos: int, _index: int) -> None:
        self._clamp_panel_sizes()
        self._sync_layout_ratios_from_sizes()
        self._schedule_save_layout()

    def _schedule_save_layout(self) -> None:
        self._save_timer.start(300)

    def save_layout_to_config(self) -> None:
        self._save_timer.stop()
        self._save_layout_to_config()

    def _save_layout_to_config(self) -> None:
        sizes = self.sizes()
        total = sum(sizes)
        if total <= 0:
            return
        ratios = [size / total for size in sizes]
        cfg.set(
            cfg.task_interface_panel_layout,
            f"{ratios[0]:.6f},{ratios[1]:.6f},{ratios[2]:.6f}",
        )

    def apply_default_layout(self) -> None:
        self._layout_ratios = list(DEFAULT_PANEL_RATIOS)
        total = sum(self.sizes())
        if total <= 0:
            self._pending_ratios = list(self._layout_ratios)
            self._layout_restored = False
            return
        self._apply_ratio_sizes(self._layout_ratios, total)
        self._layout_restored = True

    def restore_layout_from_config(self) -> bool:
        value = cfg.get(cfg.task_interface_panel_layout)
        if not value:
            return False
        try:
            ratios = [float(part.strip()) for part in value.split(",")]
        except ValueError:
            return False
        if len(ratios) != 3 or sum(ratios) <= 0:
            return False

        ratio_sum = sum(ratios)
        self._layout_ratios = [ratio / ratio_sum for ratio in ratios]

        total = sum(self.sizes())
        if total <= 0:
            self._pending_ratios = list(self._layout_ratios)
            return False

        self._apply_ratio_sizes(self._layout_ratios, total)
        self._layout_restored = True
        return True

    def _sync_layout_ratios_from_sizes(self) -> None:
        sizes = self.sizes()
        total = sum(sizes)
        if total <= 0:
            return
        self._layout_ratios = [size / total for size in sizes]

    def _apply_ratio_sizes(self, ratios: list[float], total: int) -> None:
        ratio_sum = sum(ratios)
        if ratio_sum <= 0 or total <= 0:
            return

        sizes = [int(total * ratio / ratio_sum) for ratio in ratios]
        sizes[1] += total - sum(sizes)

        self._applying_layout = True
        self.blockSignals(True)
        try:
            self.setSizes(sizes)
            self._clamp_panel_sizes()
            self._sync_layout_ratios_from_sizes()
        finally:
            self.blockSignals(False)
            self._applying_layout = False

    def _clamp_panel_sizes(self) -> None:
        sizes = list(self.sizes())
        total = sum(sizes)
        if total <= 0:
            return

        task = max(0, sizes[0])
        log = max(0, sizes[2])

        task = min(task, MAX_SIDE_PANEL_WIDTH)
        log = min(log, MAX_SIDE_PANEL_WIDTH)

        option = total - task - log
        if option < MIN_OPTION_PANEL_WIDTH:
            deficit = MIN_OPTION_PANEL_WIDTH - option
            log_reduce = min(deficit, log)
            log -= log_reduce
            deficit -= log_reduce
            if deficit > 0:
                task -= min(deficit, task)
            option = total - task - log

        task = min(max(0, task), MAX_SIDE_PANEL_WIDTH)
        log = min(max(0, log), MAX_SIDE_PANEL_WIDTH)
        option = total - task - log

        new_sizes = [task, option, log]
        if new_sizes != sizes:
            self.blockSignals(True)
            self.setSizes(new_sizes)
            self.blockSignals(False)

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        if self._applying_layout:
            return

        if self._pending_ratios is not None and not self._layout_restored:
            total = sum(self.sizes())
            if total <= 0:
                return
            self._layout_ratios = list(self._pending_ratios)
            self._apply_ratio_sizes(self._layout_ratios, total)
            self._pending_ratios = None
            self._layout_restored = True
            return

        total = sum(self.sizes())
        if total <= 0:
            return
        self._apply_ratio_sizes(self._layout_ratios, total)
