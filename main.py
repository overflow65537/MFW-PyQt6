# coding:utf-8
import maa.library
import os
import sys
from qasync import QEventLoop

from PyQt6.QtCore import Qt, QTranslator,QTimer
from PyQt6.QtWidgets import QApplication
from qfluentwidgets import FluentTranslator

from app.common.config import cfg
from app.utils.logger import logger
from app.view.main_window import MainWindow
from app.common.config import Language
from app.common.signal_bus import signalBus
from app.common.maa_config_data import maa_config_data
from app.utils.tool import error_handler

@error_handler
def main():
    # 检查资源文件是否存在
    maa_config_name = cfg.get(cfg.maa_config_name)
    maa_config_path = cfg.get(cfg.maa_config_path)
    maa_resource_name = cfg.get(cfg.maa_resource_name)
    maa_resource_path = cfg.get(cfg.maa_resource_path)
    maa_config_list = cfg.get(cfg.maa_config_list)
    maa_resource_list = cfg.get(cfg.maa_resource_list)

    if (
        maa_config_name == ""
        or maa_config_path == ""
        or maa_resource_name == ""
        or maa_resource_path == ""
        or maa_config_list == {}
        or maa_resource_list == {}
    ):
        logger.error("资源文件不存在")
        cfg.set(cfg.resource_exist, False)
        maa_config_name = ""
        maa_config_path = ""
        maa_resource_name = ""
        maa_resource_path = ""
        maa_config_list = {}
        maa_resource_list = {}
    else:
        logger.info("资源文件存在")
        cfg.set(cfg.resource_exist, True)
        signalBus.resource_exist.emit(True)
    # enable dpi scale
    if cfg.get(cfg.dpiScale) != "Auto":
        os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "0"
        os.environ["QT_SCALE_FACTOR"] = str(cfg.get(cfg.dpiScale))

    # create application
    app = QApplication(sys.argv)
    app.setAttribute(Qt.ApplicationAttribute.AA_DontCreateNativeWidgetSiblings)

    # internationalization
    locale = cfg.get(cfg.language)
    translator = FluentTranslator(locale.value)
    galleryTranslator = QTranslator()

    if locale == Language.CHINESE_SIMPLIFIED:
        galleryTranslator.load(os.path.join(os.getcwd(), "i18n", "i18n.zh_CN.qm"))
        logger.info("加载简体中文翻译")

    elif locale == Language.CHINESE_TRADITIONAL:
        galleryTranslator.load(os.path.join(os.getcwd(), "i18n", "i18n.zh_HK.qm"))
        logger.info("加载繁体中文翻译")
    elif locale == Language.ENGLISH:
        logger.info("加载英文翻译")

    app.installTranslator(translator)
    app.installTranslator(galleryTranslator)
    # create main window
    w = MainWindow()
    w.show()
    if cfg.get(cfg.resource_exist):
        if maa_config_data.config.get("run_on_startup", False):
            QTimer.singleShot(0, lambda: signalBus.start_finish.emit())
    loop = QEventLoop(app)
    loop.run_forever()

def start_symbol():
    logger.debug("-"*50)
    logger.debug("/"*50)
    logger.debug("GUI Process Start")
    logger.debug("\\"*50)
    logger.debug("-"*50)
if __name__ == "__main__":
    start_symbol()
    main()