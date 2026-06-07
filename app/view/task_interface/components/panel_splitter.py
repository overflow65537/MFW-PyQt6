from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QResizeEvent
from PySide6.QtWidgets import QSplitter, QWidget
from qfluentwidgets import isDarkTheme, qconfig

from app.common.config import cfg

PANEL_UNIT_WIDTH = 344
MAX_SIDE_PANEL_WIDTH = PANEL_UNIT_WIDTH * 2
MIN_OPTION_PANEL_WIDTH = PANEL_UNIT_WIDTH
LOG_PANEL_MIN_WIDTH = 320
PANEL_SPLITTER_GUTTER = 10
PANEL_EDGE_MARGIN = 20
PANEL_SECTION_SPACING = 8
START_BAR_TOP_MARGIN = 5
HANDLE_LINE_MARGIN = 60
MAIN_SPLITTER_HANDLE_WIDTH = 8
MAIN_SPLITTER_LINE_WIDTH = 2
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


def _splitter_line_color(*, prominent: bool = False) -> str:
    if isDarkTheme():
        return (
            "rgba(255, 255, 255, 0.42)"
            if prominent
            else "rgba(255, 255, 255, 0.25)"
        )
    return (
        "rgba(0, 0, 0, 0.35)" if prominent else "rgba(0, 0, 0, 0.25)"
    )


def _splitter_hover_line_color(*, prominent: bool = False) -> str:
    alpha = 0.72 if prominent else 0.55
    return f"rgba(128, 128, 128, {alpha})"


def _centered_line_gradient(
    line_color: str,
    *,
    horizontal: bool,
    hit_size: int,
    line_width: int,
) -> str:
    start = (hit_size - line_width) / 2 / hit_size
    end = (hit_size + line_width) / 2 / hit_size
    if horizontal:
        return (
            f"qlineargradient(x1:0, y1:0, x2:1, y2:0, "
            f"stop:0 transparent, "
            f"stop:{start:.4f} transparent, "
            f"stop:{start:.4f} {line_color}, "
            f"stop:{end:.4f} {line_color}, "
            f"stop:{end:.4f} transparent, "
            f"stop:1 transparent)"
        )
    return (
        f"qlineargradient(x1:0, y1:0, x2:0, y2:1, "
        f"stop:0 transparent, "
        f"stop:{start:.4f} transparent, "
        f"stop:{start:.4f} {line_color}, "
        f"stop:{end:.4f} {line_color}, "
        f"stop:{end:.4f} transparent, "
        f"stop:1 transparent)"
    )


def splitter_handle_stylesheet(
    orientation: Qt.Orientation,
    *,
    prominent: bool = False,
) -> str:
    hit_size = MAIN_SPLITTER_HANDLE_WIDTH if prominent else 6
    line_width = MAIN_SPLITTER_LINE_WIDTH if prominent else 1
    line_color = _splitter_line_color(prominent=prominent)
    hover_color = _splitter_hover_line_color(prominent=prominent)
    line_gradient = _centered_line_gradient(
        line_color,
        horizontal=orientation == Qt.Orientation.Horizontal,
        hit_size=hit_size,
        line_width=line_width,
    )
    hover_gradient = _centered_line_gradient(
        hover_color,
        horizontal=orientation == Qt.Orientation.Horizontal,
        hit_size=hit_size,
        line_width=line_width,
    )
    if orientation == Qt.Orientation.Horizontal:
        return f"""
            QSplitter::handle:horizontal {{
                width: {hit_size}px;
                margin: {HANDLE_LINE_MARGIN}px 0px;
                background: {line_gradient};
            }}
            QSplitter::handle:horizontal:hover {{
                background: {hover_gradient};
            }}
        """
    return f"""
        QSplitter::handle:vertical {{
            height: {hit_size}px;
            margin: 0px {HANDLE_LINE_MARGIN}px;
            background: {line_gradient};
        }}
        QSplitter::handle:vertical:hover {{
            background: {hover_gradient};
        }}
    """


class TaskInterfacePanelSplitter(QSplitter):
    """任务页三栏水平分割器。

    任务/日志宽度由用户拖动决定，窗口变宽时仅选项区扩展；
    任务/日志最多占 2/3 宽度，选项区至少 1/3，拖动时可连续调整。
    """

    panel_geometry_changed = Signal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(Qt.Orientation.Horizontal, parent)
        self.setChildrenCollapsible(True)
        self.setHandleWidth(MAIN_SPLITTER_HANDLE_WIDTH)
        self._apply_handle_style()
        qconfig.themeChanged.connect(self._apply_handle_style)
        self._layout_ratios = list(DEFAULT_PANEL_RATIOS)
        self._fixed_task_width: int | None = None
        self._fixed_log_width: int | None = None
        self._applying_layout = False
        self._pending_ratios: list[float] | None = None
        self._layout_restored = False
        self._save_timer = QTimer(self)
        self._save_timer.setSingleShot(True)
        self._save_timer.timeout.connect(self._save_layout_to_config)
        self.splitterMoved.connect(self._on_splitter_moved)

    def _apply_handle_style(self) -> None:
        self.setStyleSheet(
            splitter_handle_stylesheet(
                Qt.Orientation.Horizontal,
                prominent=True,
            )
        )

    def _on_splitter_moved(self, _pos: int, _index: int) -> None:
        self._clamp_panel_sizes()
        self._sync_layout_ratios_from_sizes()
        self._schedule_save_layout()
        self.panel_geometry_changed.emit()

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
        self.panel_geometry_changed.emit()

    def reset_saved_layout(self) -> None:
        """清除已保存布局并恢复默认三等分。"""
        cfg.set(cfg.task_interface_panel_layout, "")
        self._pending_ratios = None
        self._fixed_task_width = None
        self._fixed_log_width = None
        self._layout_restored = False
        self.apply_default_layout()

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

    def _is_equal_ratios(self, ratios: list[float]) -> bool:
        if len(ratios) != 3:
            return False
        return (
            abs(ratios[0] - ratios[1]) < 1e-6
            and abs(ratios[1] - ratios[2]) < 1e-6
        )

    def _equal_panel_sizes(self, total: int) -> list[int]:
        base = total // 3
        remainder = total % 3
        return [base + (1 if index < remainder else 0) for index in range(3)]

    def _apply_ratio_sizes(self, ratios: list[float], total: int) -> None:
        ratio_sum = sum(ratios)
        if ratio_sum <= 0 or total <= 0:
            return

        if self._is_equal_ratios(ratios):
            sizes = self._equal_panel_sizes(total)
        else:
            sizes = [int(total * ratio / ratio_sum) for ratio in ratios]
            sizes[1] += total - sum(sizes)

        self._applying_layout = True
        self.blockSignals(True)
        try:
            self.setSizes(sizes)
            self._clamp_panel_sizes()
            self._sync_layout_ratios_from_sizes()
            self._sync_fixed_side_widths_from_sizes()
        finally:
            self.blockSignals(False)
            self._applying_layout = False

    def _sync_fixed_side_widths_from_sizes(self) -> None:
        sizes = self.sizes()
        if len(sizes) < 3:
            return
        self._fixed_task_width = sizes[0]
        self._fixed_log_width = sizes[2]

    def _resolve_panel_sizes(
        self,
        total: int,
        *,
        task: int,
        log: int,
    ) -> list[int]:
        min_option = max(1, total // 3)
        max_task = max(0, total * 2 // 3)
        max_log = max(0, total * 2 // 3)

        task = min(max(0, task), max_task)
        raw_log = max(0, log)
        if raw_log == 0:
            log = 0
        else:
            log = min(max(LOG_PANEL_MIN_WIDTH, raw_log), max_log)

        option = total - task - log
        if option < min_option:
            deficit = min_option - option
            log_floor = LOG_PANEL_MIN_WIDTH if log > 0 else 0
            log_reduce = min(deficit, max(0, log - log_floor))
            log -= log_reduce
            deficit -= log_reduce
            if deficit > 0:
                task -= min(deficit, task)
            option = total - task - log

        return [task, option, log]

    def _set_panel_sizes(self, new_sizes: list[int]) -> None:
        sizes = self.sizes()
        if new_sizes == sizes:
            return
        self.blockSignals(True)
        try:
            self.setSizes(new_sizes)
        finally:
            self.blockSignals(False)

    def _clamp_panel_sizes(self) -> None:
        sizes = list(self.sizes())
        total = sum(sizes)
        if total <= 0:
            return

        new_sizes = self._resolve_panel_sizes(
            total,
            task=sizes[0],
            log=sizes[2],
        )
        self._set_panel_sizes(new_sizes)
        self._sync_fixed_side_widths_from_sizes()

    def _apply_side_fixed_layout(self, total: int) -> None:
        if self._fixed_task_width is None or self._fixed_log_width is None:
            sizes = self.sizes()
            if sum(sizes) > 0:
                self._fixed_task_width = sizes[0]
                self._fixed_log_width = sizes[2]
            else:
                self._fixed_task_width = total // 3
                self._fixed_log_width = total // 3

        new_sizes = self._resolve_panel_sizes(
            total,
            task=self._fixed_task_width,
            log=self._fixed_log_width,
        )
        self._fixed_task_width = new_sizes[0]
        self._fixed_log_width = new_sizes[2]
        self._applying_layout = True
        try:
            self._set_panel_sizes(new_sizes)
            self._sync_layout_ratios_from_sizes()
        finally:
            self._applying_layout = False

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
            self.panel_geometry_changed.emit()
            return

        total = sum(self.sizes())
        if total <= 0:
            return
        self._apply_side_fixed_layout(total)
        self.panel_geometry_changed.emit()
