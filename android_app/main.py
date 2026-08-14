# This file is part of MFW-ChainFlow Assistant.
#
# Android Phase-0 entry point. It intentionally does not import the desktop
# application entry point or MainWindow.

from __future__ import annotations

import platform
import sys
import traceback
from datetime import datetime

from PySide6 import __version__ as pyside_version
from PySide6.QtCore import QLibraryInfo, qVersion
from PySide6.QtWidgets import (
    QApplication,
    QLabel,
    QMainWindow,
    QPushButton,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
)


def is_android() -> bool:
    """Return whether this interpreter exposes Python-for-Android APIs."""
    return hasattr(sys, "getandroidapilevel") or sys.platform == "android"


def platform_summary() -> list[str]:
    """Collect information that is safe to query before MaaFw is integrated."""
    android_api = getattr(sys, "getandroidapilevel", lambda: "n/a")()
    return [
        f"Android runtime: {is_android()}",
        f"Android API level: {android_api}",
        f"sys.platform: {sys.platform}",
        f"platform.machine: {platform.machine() or 'unknown'}",
        f"Python: {platform.python_version()}",
        f"PySide6: {pyside_version}",
        f"Qt runtime: {qVersion()}",
        f"Qt prefix: {QLibraryInfo.path(QLibraryInfo.LibraryPath.PrefixPath)}",
    ]


def run_smoke_test() -> tuple[bool, list[str]]:
    """Run dependency-free checks suitable for the first Android APK."""
    results: list[str] = []
    try:
        now = datetime.now().astimezone()
        results.append(f"[PASS] Python execution: {now.isoformat(timespec='seconds')}")
        results.append(f"[PASS] Qt application: {QApplication.instance() is not None}")
        results.append(f"[PASS] Platform detection: android={is_android()}")
        results.append(f"[PASS] Qt version query: {qVersion()}")
        results.append("[SKIP] MaaFw native runtime: not integrated in Phase 0")
        return True, results
    except Exception:
        results.append("[FAIL] Unexpected exception:")
        results.extend(traceback.format_exc().splitlines())
        return False, results


class AndroidPocWindow(QMainWindow):
    """Minimal touch-friendly Qt Widgets window for deployment validation."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("MFW Android PoC")
        self.resize(720, 960)

        title = QLabel("MFW Android Deployment PoC")
        title.setStyleSheet("font-size: 22px; font-weight: 600;")

        self.info = QPlainTextEdit()
        self.info.setReadOnly(True)
        self.info.setPlainText("\n".join(platform_summary()))

        self.status = QLabel(
            "Phase 0 only: the desktop MainWindow and MaaFw native runtime are not loaded."
        )
        self.status.setWordWrap(True)

        smoke_button = QPushButton("Run basic smoke test")
        smoke_button.setMinimumHeight(56)
        smoke_button.clicked.connect(self._run_smoke_test)

        layout = QVBoxLayout()
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        layout.addWidget(title)
        layout.addWidget(self.status)
        layout.addWidget(self.info, 1)
        layout.addWidget(smoke_button)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def _run_smoke_test(self) -> None:
        ok, lines = run_smoke_test()
        self.info.appendPlainText("\n--- Smoke test ---")
        self.info.appendPlainText("\n".join(lines))
        self.status.setText("Smoke test passed." if ok else "Smoke test failed; inspect output.")


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("MFW Android PoC")
    app.setOrganizationName("MFW-ChainFlow")

    window = AndroidPocWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
