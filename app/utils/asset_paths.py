"""应用内嵌静态资源路径（Qt resource + 开发态文件回退）。"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PySide6.QtGui import QIcon, QPixmap

APP_LOGO_QT_RESOURCE = ":/icons/logo.png"
DEFAULT_APP_LOGO_FILE = "app/assets/icons/logo.png"


def _dev_logo_file() -> Path:
    return Path(__file__).resolve().parents[2] / "app" / "assets" / "icons" / "logo.png"


def is_default_app_logo_path(path: str | None) -> bool:
    if not path:
        return True
    normalized = str(path).replace("\\", "/").lstrip("./")
    return normalized == DEFAULT_APP_LOGO_FILE or path == APP_LOGO_QT_RESOURCE


def load_app_logo_pixmap() -> QPixmap | None:
    from PySide6.QtGui import QPixmap

    pixmap = QPixmap(APP_LOGO_QT_RESOURCE)
    if pixmap.isNull():
        file_path = _dev_logo_file()
        if file_path.is_file():
            pixmap = QPixmap(str(file_path))
    if pixmap.isNull():
        return None
    return pixmap


def app_logo_icon() -> QIcon:
    from PySide6.QtGui import QIcon

    icon = QIcon(APP_LOGO_QT_RESOURCE)
    if icon.isNull():
        file_path = _dev_logo_file()
        if file_path.is_file():
            icon = QIcon(str(file_path))
    return icon


def resolve_window_icon(path: str | None = None) -> QIcon:
    """解析窗口/托盘图标：自定义路径优先，否则默认 logo。"""
    from PySide6.QtGui import QIcon

    candidate = str(path or "").strip()
    if candidate and not is_default_app_logo_path(candidate):
        if candidate.startswith(":"):
            icon = QIcon(candidate)
            if not icon.isNull():
                return icon
        file_path = Path(candidate)
        if not file_path.is_absolute():
            file_path = Path.cwd() / file_path
        if file_path.is_file():
            return QIcon(str(file_path))
    return app_logo_icon()
