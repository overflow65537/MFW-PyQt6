"""
qframelesswindow Windows 平台补丁。

部分环境（虚拟显示驱动、DWM 未就绪、Qt 6.10+ 窗口标志组合）在 MainWindow 构造阶段
调用 updateFrameless 时会触发原生 abort，导致启动纯闪退。
"""

from __future__ import annotations

import sys
from typing import Any, Callable

_PATCH_INSTALLED = False


def _resolve_logger():
    try:
        from app.utils.logger import logger

        return logger
    except Exception:
        import logging

        return logging.getLogger(__name__)


def _valid_hwnd(widget: Any) -> int | None:
    try:
        hwnd = int(widget.winId())
    except Exception:
        return None
    return hwnd if hwnd else None


def _defer_window_effects(widget: Any, callback: Callable[[], None]) -> None:
    from PySide6.QtCore import QTimer

    QTimer.singleShot(0, callback)


def _run_window_effect(label: str, callback: Callable[[], None]) -> None:
    logger = _resolve_logger()
    try:
        callback()
    except Exception as exc:
        logger.warning("无边框窗口效果 %s 失败，已跳过: %s", label, exc)


def _patch_update_frameless_base(original: Callable[..., None]) -> Callable[..., None]:
    from PySide6.QtCore import Qt

    try:
        from qframelesswindow.windows import AcrylicWindow
    except ImportError:
        AcrylicWindow = ()  # type: ignore

    def patched_update_frameless(self: Any) -> None:
        logger = _resolve_logger()
        try:
            stay_on_top = (
                Qt.WindowStaysOnTopHint
                if self.windowFlags() & Qt.WindowStaysOnTopHint
                else 0
            )
            self.setWindowFlags(
                self.windowFlags() | Qt.FramelessWindowHint | stay_on_top
            )
        except Exception as exc:
            logger.warning("设置无边框窗口标志失败，已跳过: %s", exc)
            return

        if isinstance(self, AcrylicWindow):
            return

        def apply_effects() -> None:
            hwnd = _valid_hwnd(self)
            if hwnd is None:
                logger.debug("无边框窗口 hwnd 未就绪，跳过 DWM 效果")
                return
            _run_window_effect(
                "addWindowAnimation",
                lambda: self.windowEffect.addWindowAnimation(hwnd),
            )
            _run_window_effect(
                "addShadowEffect",
                lambda: self.windowEffect.addShadowEffect(hwnd),
            )

        if _valid_hwnd(self) is None:
            _defer_window_effects(self, apply_effects)
            return
        apply_effects()

    patched_update_frameless.__name__ = getattr(
        original, "__name__", "updateFrameless"
    )
    patched_update_frameless.__doc__ = original.__doc__
    return patched_update_frameless


def _patch_update_frameless_acrylic(original: Callable[..., None]) -> Callable[..., None]:
    from PySide6.QtCore import Qt

    try:
        from qframelesswindow.utils import win32_utils as win_utils
    except ImportError:
        win_utils = None  # type: ignore

    def patched_update_frameless(self: Any) -> None:
        logger = _resolve_logger()
        try:
            stay_on_top = (
                Qt.WindowStaysOnTopHint
                if self.windowFlags() & Qt.WindowStaysOnTopHint
                else 0
            )
            # Qt 6.10+ 的 Window|NoTitleBarBackgroundHint 在部分虚拟显示/DWM
            # 环境下会触发原生 abort；统一回退到 FramelessWindowHint 组合。
            self.setWindowFlags(Qt.FramelessWindowHint | stay_on_top)
        except Exception as exc:
            logger.warning("设置 Acrylic 无边框窗口标志失败，已跳过: %s", exc)
            return

        def apply_effects() -> None:
            hwnd = _valid_hwnd(self)
            if hwnd is None:
                logger.debug("Acrylic 窗口 hwnd 未就绪，跳过 DWM 效果")
                return
            _run_window_effect(
                "enableBlurBehindWindow",
                lambda: self.windowEffect.enableBlurBehindWindow(hwnd),
            )
            _run_window_effect(
                "addWindowAnimation",
                lambda: self.windowEffect.addWindowAnimation(hwnd),
            )
            _run_window_effect(
                "setAcrylicEffect",
                lambda: self.windowEffect.setAcrylicEffect(hwnd),
            )
            if win_utils and win_utils.isGreaterEqualWin11():
                _run_window_effect(
                    "addShadowEffect",
                    lambda: self.windowEffect.addShadowEffect(hwnd),
                )

        if _valid_hwnd(self) is None:
            _defer_window_effects(self, apply_effects)
            return
        apply_effects()

    patched_update_frameless.__name__ = getattr(
        original, "__name__", "updateFrameless"
    )
    patched_update_frameless.__doc__ = original.__doc__
    return patched_update_frameless


def install_qframeless_window_patch() -> None:
    """安装 qframelesswindow 启动安全补丁（仅 Windows，幂等）。"""
    global _PATCH_INSTALLED
    if _PATCH_INSTALLED or sys.platform != "win32":
        return

    try:
        from qframelesswindow.windows import AcrylicWindow, WindowsFramelessWindowBase
    except ImportError:
        return

    WindowsFramelessWindowBase.updateFrameless = _patch_update_frameless_base(
        WindowsFramelessWindowBase.updateFrameless
    )
    AcrylicWindow.updateFrameless = _patch_update_frameless_acrylic(
        AcrylicWindow.updateFrameless
    )
    _PATCH_INSTALLED = True
    _resolve_logger().debug("qframelesswindow 启动安全补丁已应用")
