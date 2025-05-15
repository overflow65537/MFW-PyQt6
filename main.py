# coding:utf-8
import os
import sys
import time

# 将当前工作目录设置为程序所在的目录，确保无论从哪里执行，其工作目录都正确设置为程序本身的位置，避免路径错误。
os.chdir(os.path.dirname(sys.executable) if getattr(sys, 'frozen', False)else os.path.dirname(os.path.abspath(__file__)))
import argparse
if not os.path.exists("main.py"):
    os.environ["MAAFW_BINARY_PATH"] = os.getcwd()
import maa
from maa.context import Context
from maa.custom_action import CustomAction
from maa.custom_recognition import CustomRecognition
from qasync import QEventLoop, asyncio
from qfluentwidgets import ConfigItem
from PySide6.QtCore import Qt, QTranslator, QTimer
from PySide6.QtWidgets import QApplication
from qfluentwidgets import FluentTranslator

from app.common.config import cfg
from app.utils.logger import logger
from app.view.main_window import MainWindow
from app.common.config import Language
from app.common.signal_bus import signalBus
from app.utils.tool import show_error_message
from app.utils.check_utils import check


def main(resource: str, config: str, directly: bool, DEV: bool):
    check(resource, config, directly, DEV)

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
    # create main window
    w = MainWindow()
    w.show()
    QTimer.singleShot(0, lambda: signalBus.start_finish.emit())
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)
    loop.run_forever()


def start_symbol():
    logger.debug("-" * 50)
    logger.debug("/" * 50)
    logger.debug("GUI Process Start")
    logger.debug("\\" * 50)
    logger.debug("-" * 50)


if __name__ == "__main__":
    if sys.platform.startswith("macos"):
        import atexit
        import os

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

    try:
        with open(
            os.path.join(".", "config", "version.txt"), "r", encoding="utf-8"
        ) as f:

            version = f.read().split()[2]
    except:
        with open(
            os.path.join(".", "config", "version.txt"), "w", encoding="utf-8"
        ) as f:
            if sys.platform.startswith("linux"):
                platf = "linux"
            elif sys.platform.startswith("win"):
                platf = "win"
            elif sys.platform.startswith("darwin"):
                platf = "macos"
            else:
                platf = "unknown"

            version = "DEV"
            f.write(f"{platf} DEV DEV v0.0.0.1")
    start_symbol()
    logger.info(f"MFW 版本:{version}")
    parser = argparse.ArgumentParser()
    parser.add_argument("-r", "--resource", default=False)
    parser.add_argument("-c", "--config", default=False)
    parser.add_argument("-d", "--directly", action="store_true")
    parser.add_argument("-DEV","--DEV", action="store_true")

    args = parser.parse_args()
    try:
        main(args.resource, args.config, args.directly, args.DEV)

    except:
        logger.exception("GUI Process Error")
        show_error_message()