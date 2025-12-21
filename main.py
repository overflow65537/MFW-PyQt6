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
import argparse


# 设置工作目录为运行方式位置
if getattr(sys, "frozen", False):
    os.chdir(os.path.dirname(sys.executable))
    os.environ["MAAFW_BINARY_PATH"] = os.getcwd()
else:
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
import maa
from maa.context import Context
from maa.custom_action import CustomAction
from maa.custom_recognition import CustomRecognition
from app.utils.logger import logger
from qasync import QEventLoop, asyncio

# 应用qasync Windows平台补丁
import app.utils.qasync_patch
from qfluentwidgets import ConfigItem, FluentTranslator
from PySide6.QtCore import Qt, QTranslator
from PySide6.QtWidgets import QApplication


from app.common.__version__ import __version__
from app.common.config import cfg
from app.view.main_window.main_window import MainWindow
from app.common.config import Language
from app.utils.crypto import crypto_manager


if __name__ == "__main__":
    logger.info(f"MFW 版本:{__version__}")
    logger.info(f"当前工作目录: {os.getcwd()}")

    import faulthandler
    from pathlib import Path

    log_dir = Path("debug")
    log_dir.mkdir(exist_ok=True)
    crash_log = open(log_dir / "crash.log", "a", encoding="utf-8")
    faulthandler.enable(file=crash_log, all_threads=True)
    # 检查并加载密钥
    crypto_manager.ensure_key_exists()

    # 启动参数解析
    parser = argparse.ArgumentParser(
        description="MFW-ChainFlow Assistant", add_help=True
    )
    parser.add_argument(
        "-d", "--direct-run", action="store_true", help="启动后直接运行任务流"
    )
    parser.add_argument(
        "-c", "--config", dest="config_id", help="启动后切换到指定配置ID"
    )
    parser.add_argument(
        "-dev", "--dev", dest="enable_dev", action="store_true", help="显示测试页面"
    )
    args, qt_extra = parser.parse_known_args(sys.argv[1:])
    qt_argv = [sys.argv[0]] + qt_extra

    # 全局异常钩子
    def global_except_hook(exc_type, exc_value, exc_traceback):
        logger.exception(
            "未捕获的全局异常:", exc_info=(exc_type, exc_value, exc_traceback)
        )

    sys.excepthook = global_except_hook

    # DPI缩放配置
    if cfg.get(cfg.dpiScale) != "Auto":
        os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "0"
        os.environ["QT_SCALE_FACTOR"] = str(cfg.get(cfg.dpiScale))

    # 首次启动时自动检测系统语言
    from app.common.config import init_language_on_first_run

    init_language_on_first_run()

    # 创建Qt应用实例
    app = QApplication(qt_argv)
    app.setAttribute(Qt.ApplicationAttribute.AA_DontCreateNativeWidgetSiblings)

    # 国际化配置
    locale: ConfigItem = cfg.get(cfg.language)
    translator = FluentTranslator(locale.value)
    galleryTranslator = QTranslator()

    # 确定语言代码
    language_code = "zh_cn"  # 默认中文
    if locale == Language.CHINESE_SIMPLIFIED:
        galleryTranslator.load(os.path.join(".", "app", "i18n", "i18n.zh_CN.qm"))
        language_code = "zh_cn"
        logger.info("加载简体中文翻译")
    elif locale == Language.CHINESE_TRADITIONAL:
        galleryTranslator.load(os.path.join(".", "app", "i18n", "i18n.zh_HK.qm"))
        language_code = "zh_hk"
        logger.info("加载繁体中文翻译")
    elif locale == Language.ENGLISH:
        language_code = "en_us"
        logger.info("加载英文翻译")
    app.installTranslator(translator)
    app.installTranslator(galleryTranslator)

    # 异步事件循环初始化
    loop = QEventLoop(app)

    # 异步异常处理
    def handle_async_exception(loop, context):
        logger.exception("异步任务异常:", exc_info=context.get("exception"))

    loop.set_exception_handler(handle_async_exception)

    asyncio.set_event_loop(loop)

    # 初始化 GPU 信息缓存
    try:
        from app.utils.gpu_cache import gpu_cache

        gpu_cache.initialize()
    except Exception as e:
        logger.warning(f"GPU 信息缓存初始化失败，忽略: {e}")

    # 创建主窗口
    w = MainWindow(
        loop=loop,
        auto_run=args.direct_run,
        switch_config_id=args.config_id,
        force_enable_test=args.enable_dev,
    )
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
