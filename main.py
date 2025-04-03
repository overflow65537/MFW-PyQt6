# coding:utf-8
import os
import sys
# 将当前工作目录设置为程序所在的目录，确保无论从哪里执行，其工作目录都正确设置为程序本身的位置，避免路径错误。
os.chdir(os.path.dirname(sys.executable) if getattr(sys, 'frozen', False)else os.path.dirname(os.path.abspath(__file__)))
import argparse
import json

from typing import Dict

if not os.path.exists("main.py"):
    os.environ["MAAFW_BINARY_PATH"] = os.getcwd()
import maa
from qasync import QEventLoop
from qfluentwidgets import ConfigItem
from PyQt6.QtCore import Qt, QTranslator, QTimer
from PyQt6.QtWidgets import QApplication
from qfluentwidgets import FluentTranslator
from cryptography.fernet import Fernet

from app.common.config import cfg
from app.utils.logger import logger
from app.view.main_window import MainWindow
from app.common.config import Language
from app.common.signal_bus import signalBus
from app.common.maa_config_data import maa_config_data, init_maa_config_data
from app.utils.tool import show_error_message, Save_Config


def main(resource: str, config: str, directly: bool):
    # 检查密钥文件是否存在
    if not os.path.exists("k.ey"):
        key = Fernet.generate_key()
        with open("k.ey", "wb") as key_file:
            key_file.write(key)
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
        if os.path.exists("interface.json") and os.path.exists("resource"):
            logger.info("检测到配置文件,开始转换")

            with open("interface.json", "r", encoding="utf-8") as f:
                interface_config: dict = json.load(f)
            cfg.set(cfg.maa_config_name, "default")
            cfg.set(cfg.maa_resource_name, interface_config.get("name", "resource"))
            cfg.set(
                cfg.maa_config_path,
                os.path.join(
                    ".",
                    "config",
                    cfg.get(cfg.maa_resource_name),
                    "config",
                    cfg.get(cfg.maa_config_name),
                    "maa_pi_config.json",
                ),
            )
            cfg.set(cfg.maa_resource_path, os.path.join("."))
            cfg.set(
                cfg.maa_config_list,
                {
                    cfg.get(cfg.maa_resource_name): {
                        cfg.get(cfg.maa_config_name): cfg.get(cfg.maa_config_path)
                    }
                },
            )
            cfg.set(
                cfg.maa_resource_list,
                {cfg.get(cfg.maa_resource_name): cfg.get(cfg.maa_resource_path)},
            )

            data = {
                "adb": {
                    "adb_path": "",
                    "address": "",
                    "input_method": 0,
                    "screen_method": 0,
                    "config": {},
                },
                "win32": {
                    "hwnd": 0,
                    "input_method": 0,
                    "screen_method": 0,
                },
                "controller": {"name": ""},
                "gpu": -1,
                "resource": "",
                "task": [],
                "finish_option": 0,
                "finish_option_res": 0,
                "finish_option_cfg": 0,
                "run_before_start": "",
                "run_before_start_args": "",
                "run_after_finish": "",
                "run_after_finish_args": "",
                "emu_path": "",
                "emu_args": "",
                "emu_wait_time": 10,
                "exe_path": "",
                "exe_args": "",
                "exe_wait_time": 10,
            }
            Save_Config(cfg.get(cfg.maa_config_path), data)
            cfg.set(cfg.resource_exist, True)
            init_maa_config_data(True)

        else:
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
        cfg.set(cfg.run_after_startup_arg, False)
        if directly:
            logger.info("检查到 -d 参数,直接启动")
            cfg.set(cfg.run_after_startup_arg, True)

        logger.info("资源文件存在")
        cfg.set(cfg.click_update, False)
        cfg.set(cfg.resource_exist, True)
        
        signalBus.resource_exist.emit(True)
        logger.info(
            f"资源版本:{maa_config_data.interface_config.get('version',"None")}"
        )

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

    args = parser.parse_args()
    try:
        main(args.resource, args.config, args.directly)

    except:
        logger.exception("GUI Process Error")
        show_error_message()
