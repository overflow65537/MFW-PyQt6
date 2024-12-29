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
        signalBus.download_self_finished.connect(self.close)
        signalBus.download_self_stopped.connect(self.cancelDownload)
        self.cancelButton.clicked.connect(self.cancelDownload)

    def setProgress(self, downloaded, total):
        if total == 0:
            self.progressBar.setValue(0)
            self.progressLabel.setText("0 / 0 " + self.tr("bytes"))
        else:
            self.progressBar.show()
            self.inProgressBar.hide()
            progress_value = int((downloaded / total) * 100)
            self.progressBar.setValue(progress_value)
            self.progressLabel.setText(f"{downloaded} / {total}" + self.tr("bytes"))

    def cancelDownload(self):
        signalBus.bundle_download_stopped.emit(True)
        self.close()
