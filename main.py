# coding:utf-8
import maa.library
import os
import sys
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
from app.common.maa_config_data import maa_config_data
from app.utils.tool import show_error_message
import argparse
from typing import Dict


def main(resource: str, config: str, directly: bool):
    # 检查资源文件是否存在
    maa_config_name: str = cfg.get(cfg.maa_config_name)
    maa_config_path: str = cfg.get(cfg.maa_config_path)
    maa_resource_name: str = cfg.get(cfg.maa_resource_name)
    maa_resource_path: str = cfg.get(cfg.maa_resource_path)
    maa_config_list: Dict[str, Dict[str, str]] = cfg.get(cfg.maa_config_list)
    maa_resource_list: Dict[str, Dict[str, str]] = cfg.get(cfg.maa_resource_list)

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
        if resource in list(maa_resource_list.keys()):
            cfg.set(cfg.maa_resource_name, resource)
            maa_resource_name = resource
            cfg.set(cfg.maa_resource_path, maa_resource_list[resource])
            maa_resource_path = maa_resource_list[resource]
            if not config:
                cfg.set(cfg.maa_config_name, "default")
                cfg.set(cfg.maa_config_path, maa_config_list[resource]["default"])
                maa_config_name = "default"
                maa_config_path = maa_config_list[resource]["default"]
        if config in list(maa_config_list[maa_resource_name].keys()):
            cfg.set(cfg.maa_config_name, config)
            cfg.set(cfg.maa_config_path, maa_config_list[maa_resource_name][config])
            maa_config_name = config
            maa_config_path = maa_config_list[maa_resource_name][config]

        else:
            cfg.set(cfg.maa_config_name, "default")
            cfg.set(cfg.maa_config_path, maa_config_list[maa_resource_name]["default"])
            maa_config_name = "default"
            maa_config_path = maa_config_list[maa_resource_name]["default"]
        cfg.set(cfg.run_after_startup, False)
        if directly:
            logger.info("检查到 -d 参数,直接启动")
            cfg.set(cfg.run_after_startup, True)
        logger.info("资源文件存在")
        cfg.set(cfg.resource_exist, True)
        logger.info(
            f"资源版本:{maa_config_data.interface_config.get('version',"v0.0.1")}"
        )
        signalBus.resource_exist.emit(True)

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
            os.path.join(os.getcwd(), "resource", "i18n", "i18n.zh_CN.qm")
        )
        logger.info("加载简体中文翻译")

    elif locale == Language.CHINESE_TRADITIONAL:
        galleryTranslator.load(
            os.path.join(os.getcwd(), "resource", "i18n", "i18n.zh_HK.qm")
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
    start_symbol()
    parser = argparse.ArgumentParser()
    parser.add_argument("-r", "--resource", default=False)
    parser.add_argument("-c", "--config", default=False)
    parser.add_argument("-d", "--directly", action="store_true")
    args = parser.parse_args()
    try:
        main(args.resource, args.config, args.directly)
    except:
        logger.exception("GUI Process Error")
        show_error_message()
