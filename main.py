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


# 将当前工作目录设置为程序所在的目录，确保无论从哪里执行，其工作目录都正确设置为程序本身的位置，避免路径错误。
if getattr(sys, "frozen", False):
    # 如果程序是打包后的可执行文件，将工作目录设置为可执行文件所在目录
    if sys.platform.startswith("darwin"):
        # MacOS平台
        target_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(sys.executable))))

    else:
        target_dir = os.path.dirname(sys.executable)        # 非MacOS平台



else:
    # 如果是脚本运行，将工作目录设置为脚本文件所在目录
    target_dir = os.path.dirname(os.path.abspath(__file__))

# 切换工作目录
os.chdir(target_dir)

from cryptography.fernet import Fernet

if not os.path.exists("k.ey"):
    key = Fernet.generate_key()
    with open("k.ey", "wb") as key_file:
        key_file.write(key)
import argparse
import maa
from maa.context import Context
from maa.custom_action import CustomAction
from maa.custom_recognition import CustomRecognition

import atexit
from qasync import QEventLoop, asyncio
from qfluentwidgets import ConfigItem
from PySide6.QtCore import Qt, QTranslator
from PySide6.QtWidgets import QApplication
from qfluentwidgets import FluentTranslator

from app.common.config import cfg

from app.view.main_window import MainWindow
from app.common.config import Language
from app.utils.tool import show_error_message
from app.utils.check_utils import check
from app.common.__version__ import __version__
from app.utils.logger import logger

logger.debug(f"设置工作目录: {target_dir}")

def main(resource: str, config: str, directly: bool, DEV: bool):
    check(resource, config, directly, DEV)

    # 设置全局异常钩子
    def global_except_hook(exc_type, exc_value, exc_traceback):
        logger.exception(
            "未捕获的全局异常:", exc_info=(exc_type, exc_value, exc_traceback)
        )

    sys.excepthook = global_except_hook

    # enable dpi scale
    if cfg.get(cfg.dpiScale) != "Auto":
        os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "0"
        os.environ["QT_SCALE_FACTOR"] = str(cfg.get(cfg.dpiScale))

    # create application
    app = QApplication(sys.argv)
    app.setAttribute(Qt.ApplicationAttribute.AA_DontCreateNativeWidgetSiblings)

    # internationalization
    locale: ConfigItem = cfg.get(cfg.language)
    translator = FluentTranslator(locale.value)
    galleryTranslator = QTranslator()

    if locale == Language.CHINESE_SIMPLIFIED:
        galleryTranslator.load(
            os.path.join(".", "MFW_resource", "i18n", "i18n.zh_CN.qm")
        )
        logger.info("加载简体中文翻译")

    elif locale == Language.CHINESE_TRADITIONAL:
        galleryTranslator.load(
            os.path.join(".", "MFW_resource", "i18n", "i18n.zh_HK.qm")
        )
        logger.info("加载繁体中文翻译")
    elif locale == Language.ENGLISH:
        logger.info("加载英文翻译")

    app.installTranslator(translator)
    app.installTranslator(galleryTranslator)

    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)
    # create main window
    w = MainWindow()
    w.show()
    # 异步异常处理
    def handle_async_exception(loop, context):
        logger.exception("异步任务异常:", exc_info=context.get("exception"))

    loop.set_exception_handler(handle_async_exception)

    with loop:
        loop.run_forever()
    logger.debug("关闭异步任务完成")
    loop.close()


def start_symbol():
    logger.debug("-" * 50)
    logger.debug("/" * 50)
    logger.debug("GUI Process Start")
    logger.debug("\\" * 50)
    logger.debug("-" * 50)


if __name__ == "__main__":
    if sys.platform.startswith("darwin"):

        PID_FILE = os.path.join(os.getcwd(), "MFW.pid")  # PID文件路径

        # 清理PID文件的函数
        def cleanup_pid():
            if os.path.exists(PID_FILE):
                os.remove(PID_FILE)
                logger.debug("已清理PID文件")

        # 检查是否已有实例运行
        if os.path.exists(PID_FILE):
            try:
                with open(PID_FILE, "r") as f:
                    existing_pid = int(f.read().strip())
                # 检查PID是否存活（macOS可用os.kill检测）
                os.kill(existing_pid, 0)  # 发送0信号检测进程是否存在
                logger.error(f"检测到已有实例运行（PID: {existing_pid}），当前实例退出")
                sys.exit(0)
            except (ValueError, ProcessLookupError):
                # PID文件内容无效 或 进程已退出，清理旧文件
                cleanup_pid()
                logger.debug("检测到残留PID文件，已清理")

        # 写入当前PID并注册清理
        with open(PID_FILE, "w") as f:
            f.write(str(os.getpid()))
        atexit.register(cleanup_pid)  # 程序正常退出时自动清理
        logger.debug(f"创建PID文件（当前PID: {os.getpid()}）")

    start_symbol()
    logger.info(f"MFW 版本:{__version__}")
    parser = argparse.ArgumentParser()
    parser.add_argument("-r", "--resource", default=False)
    parser.add_argument("-c", "--config", default=False)
    parser.add_argument("-d", "--directly", action="store_true")
    parser.add_argument("-DEV", "--DEV", action="store_true")

    args = parser.parse_args()
    try:
        main(args.resource, args.config, args.directly, args.DEV)

    except:
        logger.exception("GUI Process Error")
        show_error_message()
