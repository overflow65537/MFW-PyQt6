#   This file is part of MFW-ChainFlow Assistant.

#   MFW-ChainFlow Assistant is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published
#   by the Free Software Foundation, either version 3 of the License,
#   or (at your option) any later version.

#   MFW-ChainFlow Assistant is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty
#   of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See
#   the GNU General Public License for more details.

#   You should have received a copy of the GNU General Public License
#   along with MFW-ChainFlow Assistant. If not, see <https://www.gnu.org/licenses/>.

#   Contact: err.overflow@gmail.com
#   Copyright (C) 2024-2025  MFW-ChainFlow Assistant. All rights reserved.

"""
MFW-ChainFlow Assistant
MFW-ChainFlow Assistant 启动文件
作者:overflow65537
"""

import os
import sys
import atexit
import traceback
from pathlib import Path


def _install_anchor_path() -> str:
    """
    用于定位发行根目录（interface、config 等）及单实例锁的路径。

    - PyInstaller: sys.frozen 为真，锚点为 sys.executable（旁路布局）。
    - Nuitka onefile: 无 sys.frozen，__file__ 在临时解压目录；优先 __compiled__.onefile_argv0，
      否则为启动时 sys.argv[0]（指向用户启动的 .exe）。
    - 源码运行: 锚点为 main.py 所在目录。
    """
    if getattr(sys, "frozen", False):
        return sys.executable
    compiled = globals().get("__compiled__")
    if compiled is not None:
        return getattr(compiled, "onefile_argv0", None) or sys.argv[0]
    return __file__


def _is_packed_runtime() -> bool:
    return getattr(sys, "frozen", False) or globals().get("__compiled__") is not None


def _resolve_install_root() -> Path:
    """发行根目录：与 interface、maafw 同级，而非 PyInstaller 的 _internal 子目录。"""
    anchor = Path(_install_anchor_path()).resolve()
    root = anchor.parent
    if not _is_packed_runtime():
        return root

    # PyInstaller onedir：sys._MEIPASS 指向 _internal，发行根为其父目录
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        internal = Path(meipass).resolve()
        if internal.name == "_internal":
            return internal.parent

    if root.name == "_internal":
        return root.parent
    return root


def _resolve_maafw_dir(install_root: Path) -> Path:
    """MaaFW 原生库目录：固定在发行根下的 ./maafw，而非 ./_internal/maafw。"""
    return (install_root / "maafw").resolve()


# 设置工作目录为发行根（避免 Nuitka onefile 留在 Temp 解压目录）
_install_root = _resolve_install_root()
os.chdir(_install_root)
# 打包版：MaaFramework 等原生库放在发行根下的 maafw/（见 CI move_maa_bin_to_maafw、PyInstaller build.py）
if _is_packed_runtime():
    _maafw = _resolve_maafw_dir(_install_root)
    os.environ["MAAFW_BINARY_PATH"] = str(_maafw)
    if sys.platform == "win32":
        try:
            os.add_dll_directory(str(_maafw))
            _pl = _maafw / "plugins"
            if _pl.is_dir():
                os.add_dll_directory(str(_pl))
        except (AttributeError, OSError, ValueError):
            pass


def _show_fatal_startup_error(exc_type, exc_value, exc_traceback) -> None:
    """显示启动阶段致命错误，优先使用项目内 Fluent 弹窗。"""
    try:
        from app.utils.startup_dialog import show_startup_failure_dialog

        show_startup_failure_dialog(exc_type, exc_value, exc_traceback)
    except Exception:
        tb_text = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        print("程序启动失败。", file=sys.stderr)
        print(tb_text, file=sys.stderr)


def _run() -> int:
    from qasync import QEventLoop, asyncio

    # 应用 qasync / qframelesswindow Windows 平台补丁
    import app.utils.qasync_patch
    import app.utils.qframeless_patch
    app.utils.qframeless_patch.install_qframeless_window_patch()
    from qfluentwidgets import FluentTranslator
    from PySide6.QtCore import Qt, QTranslator
    from PySide6.QtWidgets import QApplication

    from app.common.__version__ import __version__
    from app.common.config import Language, cfg, init_language_on_first_run
    from app.common.theme_manager import apply_theme_from_config
    from app.utils.crypto import crypto_manager
    from app.utils.logger import logger
    from app.utils.single_instance import SingleInstanceGuard, is_instance_running
    from app.utils.startup_cli import parse_startup_cli

    # 启动参数解析（单实例检查前处理 --force-restart）
    options, qt_extra, deprecated_cli = parse_startup_cli()
    qt_argv = [sys.argv[0]] + qt_extra
    deprecated_cli_shown = False

    def _show_deprecated_cli_if_needed() -> None:
        nonlocal deprecated_cli_shown
        if deprecated_cli_shown or not deprecated_cli:
            return
        from app.utils.startup_dialog import show_deprecated_cli_dialog

        logger.warning("检测到已弃用的启动参数: %s", ", ".join(deprecated_cli))
        show_deprecated_cli_dialog(deprecated_cli)
        deprecated_cli_shown = True

    instance_key = str(Path(_install_anchor_path()).resolve())

    # DPI缩放配置（--force-restart 等待弹窗也需要）
    if cfg.get(cfg.dpiScale) != "Auto":
        os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "0"
        os.environ["QT_SCALE_FACTOR"] = str(cfg.get(cfg.dpiScale))

    init_language_on_first_run()

    def _ensure_early_startup_app(qt_argv: list[str]) -> QApplication:
        app = QApplication.instance()
        if app is None or not isinstance(app, QApplication):
            app = QApplication(qt_argv)
            app.setAttribute(Qt.ApplicationAttribute.AA_DontCreateNativeWidgetSiblings)
            apply_theme_from_config()
        return app

    if options.force_restart and is_instance_running(instance_key):
        from app.utils.startup_dialog import run_force_restart_shutdown_flow

        _ensure_early_startup_app(qt_argv)
        _show_deprecated_cli_if_needed()
        if not run_force_restart_shutdown_flow(instance_key):
            return 1

    single_instance = SingleInstanceGuard(instance_key)
    if not single_instance.acquire():
        from app.utils.startup_dialog import run_duplicate_instance_flow

        _ensure_early_startup_app(qt_argv)
        _show_deprecated_cli_if_needed()
        outcome = run_duplicate_instance_flow(instance_key)
        if outcome == "activated":
            return 0
        if outcome == "failed":
            return 1
        if not single_instance.acquire():
            return 1

    atexit.register(single_instance.release)

    logger.info(f"MFW 版本:{__version__}")
    logger.info(f"当前工作目录: {os.getcwd()}")

    import faulthandler

    log_dir = Path("debug")
    log_dir.mkdir(exist_ok=True)
    crash_log = open(log_dir / "crash.log", "a", encoding="utf-8")
    faulthandler.enable(file=crash_log, all_threads=True)
    # 检查并加载密钥
    crypto_manager.ensure_key_exists()

    # 全局异常钩子
    def global_except_hook(exc_type, exc_value, exc_traceback):
        logger.exception(
            "未捕获的全局异常:", exc_info=(exc_type, exc_value, exc_traceback)
        )
        # 显示异常弹窗
        try:
            from app.utils.startup_dialog import show_uncaught_exception_dialog

            show_uncaught_exception_dialog(exc_type, exc_value, exc_traceback)
        except Exception as dialog_err:
            # 弹窗失败时仅记录日志，避免递归
            logger.error(f"显示异常弹窗失败: {dialog_err}")

    sys.excepthook = global_except_hook

    # 创建Qt应用实例（--force-restart 等待阶段可能已创建）
    app = QApplication.instance()
    if app is None or not isinstance(app, QApplication):
        app = QApplication(qt_argv)
        app.setAttribute(Qt.ApplicationAttribute.AA_DontCreateNativeWidgetSiblings)
        apply_theme_from_config()

    _show_deprecated_cli_if_needed()

    if single_instance.start_activation_server(app):
        atexit.register(single_instance.stop_activation_server)
    else:
        logger.warning("单实例激活服务启动失败，重复启动时将无法自动前置已有窗口")

    from app.view.main_window.main_window import MainWindow

    window_holder: dict[str, MainWindow | None] = {"window": None}
    pending_force_shutdown = {"requested": False}
    pending_activation = {"requested": False}

    def _activate_existing_window() -> bool:
        window = window_holder["window"]
        if window is None:
            pending_activation["requested"] = True
            return True

        if not window.isVisible():
            window.show()
        if window.windowState() & Qt.WindowState.WindowMinimized:
            window.showNormal()

        window.raise_()
        window.activateWindow()

        if os.name == "nt":
            try:
                import ctypes

                user32 = ctypes.windll.user32
                hwnd = int(window.winId())
                if user32.IsIconic(hwnd):
                    user32.ShowWindow(hwnd, 9)  # SW_RESTORE
                else:
                    user32.ShowWindow(hwnd, 5)  # SW_SHOW
                # SetForegroundWindow 常因系统前台策略失败，但窗口已恢复/显示即视为成功
                user32.SetForegroundWindow(hwnd)
            except Exception:
                logger.debug("Windows 前置已有实例失败", exc_info=True)

        return True

    single_instance.set_activation_callback(_activate_existing_window)

    # 国际化配置（须在 --force-restart 等待弹窗之后安装，以便弹窗也能翻译）
    locale = cfg.get(cfg.language)
    translator = FluentTranslator(locale.value)
    galleryTranslator = QTranslator()

    i18n_dir = os.path.join(".", "app", "i18n")

    def _try_load_qm(translator: QTranslator, filenames: tuple[str, ...]) -> bool:
        for name in filenames:
            path = os.path.join(i18n_dir, name)
            if os.path.isfile(path) and translator.load(path):
                return True
        return False

    # 确定语言代码（与 interface_manager / 资源包 languages 键一致）
    language_code = "zh_cn"
    if locale == Language.CHINESE_SIMPLIFIED:
        _try_load_qm(galleryTranslator, ("i18n.zh_CN.qm",))
        language_code = "zh_cn"
        logger.info("加载简体中文翻译")
    elif locale == Language.CHINESE_TRADITIONAL:
        if _try_load_qm(galleryTranslator, ("i18n.zh_TW.qm",)):
            logger.info("加载繁体中文翻译")
        else:
            logger.warning("未找到繁体 .qm：i18n.zh_TW.qm")
        language_code = "zh_tw"
    elif locale == Language.JAPANESE:
        _try_load_qm(galleryTranslator, ("i18n.ja_JP.qm",))
        language_code = "ja_jp"
        logger.info("加载日语翻译")
    elif locale == Language.ENGLISH:
        language_code = "en_us"
        logger.info("加载英文翻译")
    app.installTranslator(translator)
    app.installTranslator(galleryTranslator)

    # 尝试导入 maa 库，检测是否缺少 VC++ Redistributable
    try:
        import maa
        from maa.context import Context
        from maa.custom_action import CustomAction
        from maa.custom_recognition import CustomRecognition
    except (ImportError, OSError) as e:
        error_msg = str(e).lower()
        # 检测是否是 DLL 加载失败或 VC++ 相关错误
        if any(
            keyword in error_msg
            for keyword in [
                "dll",
                "vcruntime",
                "msvcp",
                "api-ms-win",
                "找不到指定的模块",
                "specified module could not be found",
                "failed to load",
                "cannot load",
            ]
        ):
            from app.utils.startup_dialog import show_vcredist_missing_dialog

            show_vcredist_missing_dialog()
        else:
            # 其他导入错误，正常抛出
            raise

    # 异步事件循环初始化
    loop = QEventLoop(app)

    # 异步异常处理
    def handle_async_exception(loop, context):
        logger.exception("异步任务异常:", exc_info=context.get("exception"))

    loop.set_exception_handler(handle_async_exception)

    asyncio.set_event_loop(loop)

    def _schedule_graceful_shutdown(window) -> None:
        async def _stop_and_close() -> None:
            try:
                task_runner = window.service_coordinator.task_runner
                if task_runner.is_running or task_runner.maafw.has_active_runtime():
                    await window.service_coordinator.stop_task(manual=True)
            except Exception:
                logger.exception("收到 --force-restart 关闭请求后停止任务失败")
            window._allow_window_close = True
            from PySide6.QtCore import QTimer

            QTimer.singleShot(0, window.close)

        try:
            asyncio.ensure_future(_stop_and_close(), loop=loop)
        except Exception:
            logger.exception("调度优雅关闭失败")
            window._allow_window_close = True
            window.close()

    def _handle_force_shutdown_request() -> bool:
        window = window_holder["window"]
        if window is None:
            pending_force_shutdown["requested"] = True
            return True
        _schedule_graceful_shutdown(window)
        return True

    single_instance.set_shutdown_callback(_handle_force_shutdown_request)

    # 初始化 GPU 信息缓存
    try:
        from app.utils.gpu_cache import gpu_cache

        gpu_cache.initialize()
    except Exception as e:
        logger.warning(f"GPU 信息缓存初始化失败，忽略: {e}")

    # 创建主窗口
    w = MainWindow(
        loop=loop,
        auto_run=options.direct_run,
        switch_config_id=options.config_id,
        force_enable_test=options.enable_dev,
    )
    window_holder["window"] = w
    if pending_force_shutdown["requested"]:
        _schedule_graceful_shutdown(w)
    elif pending_activation["requested"]:
        from PySide6.QtCore import QTimer

        QTimer.singleShot(0, _activate_existing_window)
    w.show()

    # 连接应用退出信号到事件循环停止
    app.aboutToQuit.connect(loop.stop)

    # 运行事件循环
    with loop:
        loop.run_forever()
        logger.debug("关闭异步任务完成")

        # Cancel all pending tasks before closing the loop
        try:
            # Get and cancel all pending tasks
            pending = asyncio.all_tasks(loop)
            for task in pending:
                task.cancel()

            # Wait for all tasks to be cancelled (gather handles empty list safely)
            if pending:
                loop.run_until_complete(
                    asyncio.gather(*pending, return_exceptions=True)
                )

            # Double-check for any remaining tasks created during cancellation
            remaining = asyncio.all_tasks(loop)
            if remaining:
                logger.warning(f"发现 {len(remaining)} 个未取消的任务，正在强制取消")
                for task in remaining:
                    task.cancel()
                loop.run_until_complete(
                    asyncio.gather(*remaining, return_exceptions=True)
                )
        except Exception as e:
            logger.warning(f"取消待处理任务时出错: {e}")

    return 0


if __name__ == "__main__":
    try:
        sys.exit(_run())
    except SystemExit:
        raise
    except Exception:
        _show_fatal_startup_error(*sys.exc_info())
        sys.exit(1)
