from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QResizeEvent
from PySide6.QtWidgets import QSplitter, QWidget

from app.common.config import cfg

PANEL_UNIT_WIDTH = 344
MAX_SIDE_PANEL_WIDTH = PANEL_UNIT_WIDTH * 2
MIN_OPTION_PANEL_WIDTH = PANEL_UNIT_WIDTH


class TaskInterfacePanelSplitter(QSplitter):
    """任务页三栏水平分割器。

    以 344px 为一格，任务/日志最多占 2 格并向选项区单侧扩展，选项区至少 1 格且可向左右扩展。
    """

    def __init__(self, parent: QWidget | None = None):
        super().__init__(Qt.Orientation.Horizontal, parent)
        self.setChildrenCollapsible(True)
        self.setHandleWidth(6)
        self.setStyleSheet(
            """
            QSplitter::handle:horizontal {
                background: transparent;
            }
            """
        )
        self._pending_ratios: list[float] | None = None
        self._layout_restored = False
        self._save_timer = QTimer(self)
        self._save_timer.setSingleShot(True)
        self._save_timer.timeout.connect(self._save_layout_to_config)
        self.splitterMoved.connect(self._on_splitter_moved)

    def _on_splitter_moved(self, _pos: int, _index: int) -> None:
        self._clamp_panel_sizes()
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

        total = sum(self.sizes())
        if total <= 0:
            self._pending_ratios = ratios
            return False

        self._apply_ratio_sizes(ratios, total)
        self._layout_restored = True
        return True

    def _apply_ratio_sizes(self, ratios: list[float], total: int) -> None:
        ratio_sum = sum(ratios)
        sizes = [int(total * ratio / ratio_sum) for ratio in ratios]
        sizes[1] += total - sum(sizes)

        self.blockSignals(True)
        self.setSizes(sizes)
        self._clamp_panel_sizes()
        self.blockSignals(False)

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
        if self._pending_ratios is None or self._layout_restored:
            return
        total = sum(self.sizes())
        if total <= 0:
            return
        self._apply_ratio_sizes(self._pending_ratios, total)
        self._pending_ratios = None
        self._layout_restored = True
