# coding:utf-8
import os
import sys

# 将当前工作目录设置为程序所在的目录，确保无论从哪里执行，其工作目录都正确设置为程序本身的位置，避免路径错误。
os.chdir(os.path.dirname(sys.executable) if getattr(sys, 'frozen', False)else os.path.dirname(os.path.abspath(__file__)))
import argparse
if not os.path.exists("main.py"):
    os.environ["MAAFW_BINARY_PATH"] = os.getcwd()
import maa
from qasync import QEventLoop
from qfluentwidgets import ConfigItem
from PyQt6.QtCore import Qt, QTranslator, QTimer
from PyQt6.QtWidgets import QApplication
from qfluentwidgets import FluentTranslator

from app.common.config import cfg
from app.utils.logger import logger
from app.view.main_window import MainWindow
from app.common.config import Language
from app.common.signal_bus import signalBus
from app.utils.tool import show_error_message
from app.utils.check_utils import check

# 必须在创建QApplication之前设置
if sys.platform == "darwin":
    os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = os.path.join(
        sys._MEIPASS, 'PyQt6', 'Qt6', 'plugins'
    )
    QCoreApplication.addLibraryPath(os.path.join(
        sys._MEIPASS, 'PyQt6', 'Qt6', 'plugins'
    ))
    QLibraryInfo.setPaths()

    
def main(resource: str, config: str, directly: bool, DEV: bool):
    # 添加Qt环境初始化
    if getattr(sys, 'frozen', False):
        # 打包后运行时
        base_path = sys._MEIPASS
        os.environ['QT_PLUGIN_PATH'] = os.path.join(base_path, 'PyQt6', 'Qt6', 'plugins')
    else:
        # 开发时运行时
        base_path = os.path.dirname(os.path.abspath(__file__))
    
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
    loop.run_forever()


def start_symbol():
    logger.debug("-" * 50)
    logger.debug("/" * 50)
    logger.debug("GUI Process Start")
    logger.debug("\\" * 50)
    logger.debug("-" * 50)


if __name__ == "__main__":

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
