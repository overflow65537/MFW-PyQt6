from qfluentwidgets import (
    MessageBoxBase,
    IndeterminateProgressBar,
    SubtitleLabel,
    ProgressBar,
    BodyLabel,
)
from PyQt6.QtWidgets import QVBoxLayout
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from ..common.signal_bus import signalBus

# from ..utils.logger import logger


class ShowDownload(MessageBoxBase):
    def __init__(self, parent=None):
        super().__init__(parent)
        transparent_color = QColor(255, 255, 255, 0)
        self.setMaskColor(transparent_color)
        self.titleLabel = SubtitleLabel(self.tr("Downloading..."), self)

        self.widget.setMinimumWidth(350)
        self.widget.setMinimumHeight(100)
        self.progressBar_layout = QVBoxLayout()
        self.progressBar = ProgressBar(self)
        self.inProgressBar = IndeterminateProgressBar(self)
        self.progressBar.setRange(0, 100)
        self.progressBar.setValue(0)
        self.progressBar.hide()
        self.progressBar_layout.addWidget(self.progressBar)
        self.progressBar_layout.addWidget(self.inProgressBar)
        self.progressBar_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cancelButton.setText(self.tr("Cancel"))
        # 进度数字标签
        self.progressLabel = BodyLabel("0 / 0 " + self.tr("bytes"), self)
        self.progressLabel.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addLayout(self.progressBar_layout)
        self.viewLayout.addWidget(self.progressLabel)
        self.yesButton.hide()

        signalBus.bundle_download_progress.connect(self.setProgress)
        signalBus.bundle_download_finished.connect(self.close)
        signalBus.download_self_progress.connect(self.setProgress)
        self.cancelButton.clicked.connect(self.cancelDownload)
        signalBus.download_self_finished.connect(self.cancelDownload)

    def setProgress(self, downloaded, total):
        if total == 0:
            self.progressBar.setValue(0)
            self.progressLabel.setText("0 B")
        else:
            self.progressBar.show()
            self.inProgressBar.hide()
            progress_value = int((downloaded / total) * 100)
            self.progressBar.setValue(progress_value)

            total_str = self.format_size(total)
            downloaded_str = self.format_size(downloaded)
            self.progressLabel.setText(f"{downloaded_str} / {total_str}")

    def format_size(self, size):

        units = ["B", "KB", "MB", "GB", "TB"]
        unit_index = 0
        while size >= 1024 and unit_index < len(units) - 1:
            size /= 1024
            unit_index += 1
        return f"{size:.2f} {units[unit_index]}"

    def cancelDownload(self, name):
        signalBus.bundle_download_stopped.emit(True)
        signalBus.download_self_stopped.emit(True)
        self.close()
