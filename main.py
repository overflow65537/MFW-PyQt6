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

from app.utils.install_paths import (
    is_packed,
    resolve_install_anchor,
    resolve_install_root,
)
from app.utils.maafw_binary import configure_packed_maafw_binary_path


# 设置工作目录为发行根（避免 Nuitka onefile 留在 Temp 解压目录）
_install_root = resolve_install_root()
os.chdir(_install_root)
# 打包版：MaaFramework 等原生库放在发行根下的 maafw/
if is_packed():
    configure_packed_maafw_binary_path(_install_root)


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
    #import app.utils.qasync_patch
    #import app.utils.qframeless_patch
    #app.utils.qframeless_patch.install_qframeless_window_patch()
    from qfluentwidgets import FluentTranslator
    from PySide6.QtCore import Qt, QTranslator
    from PySide6.QtWidgets import QApplication

    from app.common.__version__ import __version__
    from app.common.config import Language, cfg, init_language_on_first_run
    from app.common.theme_manager import apply_theme_from_config
    from app.utils.crypto import crypto_manager
    from app.utils.logger import logger
    from app.utils.single_instance import SingleInstanceGuard
    from app.utils.startup_cli import parse_startup_cli
    from app.utils.startup_strategy import (
        ExistingInstanceAction,
        ReuseExistingCommand,
        decide_existing_instance_action,
        decide_reuse_existing_command,
    )

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

    instance_key = str(resolve_install_anchor())

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

    single_instance = SingleInstanceGuard(instance_key)
    if not single_instance.acquire():
        existing_action = decide_existing_instance_action(
            existing_instance=True,
            reuse_existing=options.reuse_existing,
            force_restart=options.force_restart,
        )
        if existing_action == ExistingInstanceAction.REUSE:
            try:
                from app.ipc.protocol import IpcStatus
                from PySide6.QtCore import QCoreApplication

                ipc_app = QCoreApplication.instance()
                if ipc_app is None:
                    _ = QCoreApplication([sys.argv[0]])
                reuse_command = decide_reuse_existing_command(
                    direct_run=options.direct_run,
                    config_id=options.config_id,
                )

                if reuse_command == ReuseExistingCommand.RUN:
                    response = single_instance.run(
                        options.config_id,
                        force_restart=options.force_restart,
                    )
                    success_message = "已有实例已接收复用执行请求"
                    busy_message = "已有实例正在执行任务，跳过复用执行请求"
                elif reuse_command == ReuseExistingCommand.SWITCH_CONFIG:
                    response = single_instance.switch_config(
                        options.config_id or ""
                    )
                    success_message = "已有实例已接收配置切换请求"
                    busy_message = "已有实例暂时无法切换配置"
                else:
                    response = single_instance.activate()
                    success_message = "已有实例已激活"
                    busy_message = "已有实例暂时无法激活"

                if response.status in {IpcStatus.OK, IpcStatus.ACCEPTED}:
                    logger.info(success_message)
                    return 0
                if response.status == IpcStatus.BUSY:
                    logger.info(busy_message)
                    return 2
                logger.warning(
                    "向已有实例发送复用请求失败: command=%s status=%s code=%s",
                    reuse_command.value,
                    response.status.value,
                    response.code,
                )
                return 1
            except Exception:
                logger.exception("未知错误")
                return 3

        _ensure_early_startup_app(qt_argv)
        _show_deprecated_cli_if_needed()
        if existing_action == ExistingInstanceAction.RESTART:
            from app.utils.startup_dialog import run_force_restart_shutdown_flow

            if not run_force_restart_shutdown_flow(instance_key):
                return 1
        else:
            from app.utils.startup_dialog import run_duplicate_instance_flow

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

    try:
        import maa
        from maa.context import Context
        from maa.custom_action import CustomAction
        from maa.custom_recognition import CustomRecognition
        from maa.library import Library

        # 在此触发 dylib/dll 加载，避免进入主窗口导入后再因缺失依赖崩溃
        Library.version()
    except (ImportError, OSError) as e:
        error_msg = str(e).lower()
        if sys.platform == "win32" and any(
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
            raise

    loop = QEventLoop(app)

    def handle_async_exception(loop, context):
        logger.exception("异步任务异常:", exc_info=context.get("exception"))

    loop.set_exception_handler(handle_async_exception)
    asyncio.set_event_loop(loop)

    from app.core.service.app_command_dispatcher import AppCommandDispatcher
    from app.ipc.protocol import IpcCommand, IpcRequest
    from app.view.main_window.main_window import MainWindow

    async def _close_application() -> None:
        window = dispatcher.window
        if window is None:
            app.quit()
            return
        window._allow_window_close = True
        from PySide6.QtCore import QTimer

        QTimer.singleShot(0, window.close)

    dispatcher = AppCommandDispatcher(loop, close_callback=_close_application)
    single_instance.set_command_handler(dispatcher.submit)
    if single_instance.start_activation_server(app):
        atexit.register(single_instance.stop_activation_server)
    else:
        logger.warning("单实例 IPC 服务启动失败，重复启动时将无法控制已有窗口")

    # 初始化 GPU 信息缓存
    try:
        from app.utils.gpu_cache import gpu_cache

        gpu_cache.initialize()
    except Exception as e:
        logger.warning(f"GPU 信息缓存初始化失败，忽略: {e}")

    def _submit_startup_run(config_id: str | None):
        return dispatcher.submit_startup(
            IpcRequest(
                IpcCommand.RUN,
                {
                    "config_id": config_id,
                    "force_restart": False,
                },
            )
        )

    if options.config_id:
        dispatcher.submit_startup(
            IpcRequest(
                IpcCommand.SWITCH_CONFIG,
                {"config_id": options.config_id},
            )
        )

    # Preserve MainWindow's update sequencing; route the eventual run through
    # the same application command dispatcher used by IPC requests.
    w = MainWindow(
        loop=loop,
        auto_run=options.direct_run,
        startup_config_id=options.config_id,
        force_enable_test=options.enable_dev,
        startup_command_submitter=_submit_startup_run,
    )
    dispatcher.attach_window(w)
    w.show()

    # 连接应用退出信号到事件循环停止
    app.aboutToQuit.connect(loop.stop)

    # 运行事件循环
    with loop:
        loop.run_forever()
        logger.debug("关闭异步任务完成")
        loop.run_until_complete(dispatcher.close())

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
