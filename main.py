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
from app.utils.logger import logger

# 将当前工作目录设置为程序所在的目录，确保无论从哪里执行，其工作目录都正确设置为程序本身的位置，避免路径错误。
if getattr(sys, "frozen", False):
    # 如果程序是打包后的可执行文件，将工作目录设置为可执行文件所在目录
    if sys.platform.startswith("darwin"):
        # MacOS平台
        target_dir = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.dirname(sys.executable)))
        )

    else:
        target_dir = os.path.dirname(sys.executable)  # 非MacOS平台
        """if sys.platform == "linux":
            #打包后的临时目录
            os.environ["MAAFW_BINARY_PATH"] = os.path.join(sys._MEIPAS,"maa" ,"bin")"""


else:
    # 如果是脚本运行，将工作目录设置为脚本文件所在目录
    target_dir = os.path.dirname(os.path.abspath(__file__))
logger.debug(f"设置工作目录: {target_dir}")

# 切换工作目录
os.chdir(target_dir)
logger.debug(f"当前工作目录: {os.getcwd()}")

from cryptography.fernet import Fernet

if not os.path.exists("k.ey"):
    key = Fernet.generate_key()
    with open("k.ey", "wb") as key_file:
        key_file.write(key)
import argparse
import json
from typing import Dict

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
from app.common.__version__ import __version__
from app.common.maa_config_data import maa_config_data, init_maa_config_data
from app.utils.tool import Save_Config, show_error_message
from app.common.signal_bus import signalBus


def initialize_environment():
    """环境初始化"""
    # macOS 单实例检查
    if sys.platform.startswith("darwin"):
        PID_FILE = os.path.join(os.getcwd(), "MFW.pid")

        def cleanup_pid():
            if os.path.exists(PID_FILE):
                os.remove(PID_FILE)
                logger.debug("已清理PID文件")

        if os.path.exists(PID_FILE):
            try:
                with open(PID_FILE, "r") as f:
                    existing_pid = int(f.read().strip())
                os.kill(existing_pid, 0)  # 检测进程是否存活
                logger.error(f"检测到已有实例运行（PID: {existing_pid}），当前实例退出")
                sys.exit(0)
            except (ValueError, ProcessLookupError):
                cleanup_pid()
                logger.debug("检测到残留PID文件，已清理")

        with open(PID_FILE, "w") as f:
            f.write(str(os.getpid()))
        atexit.register(cleanup_pid)
        logger.debug(f"创建PID文件（当前PID: {os.getpid()}）")

    # 参数解析与配置检查
    parser = argparse.ArgumentParser()
    parser.add_argument("-r", "--resource", default=False)
    parser.add_argument("-c", "--config", default=False)
    parser.add_argument("-d", "--directly", action="store_true")
    parser.add_argument("-DEV", "--DEV", action="store_true")
    args = parser.parse_args()

    # 执行配置检查
    _check_resource_and_config(args.resource, args.config, args.directly, args.DEV)


def _check_resource_and_config(resource: str, config: str, directly: bool, DEV: bool):
    """初始化配置检查"""
    try:
        # 检查资源文件是否存在
        maa_config_name: str = cfg.get(cfg.maa_config_name)
        maa_config_path: str = cfg.get(cfg.maa_config_path)
        maa_resource_name: str = cfg.get(cfg.maa_resource_name)
        maa_resource_path: str = cfg.get(cfg.maa_resource_path)
        maa_config_list: Dict[str, Dict[str, str]] = cfg.get(cfg.maa_config_list)
        maa_resource_list: Dict[str, str] = cfg.get(cfg.maa_resource_list)

        if (
            maa_config_name == ""
            or maa_config_path == ""
            or maa_resource_name == ""
            or maa_resource_path == ""
            or maa_config_list == {}
            or maa_resource_list == {}
        ):
            _path = os.getcwd()
            if os.path.exists(os.path.join(_path, "interface.json")) and os.path.exists(
                os.path.join(_path, "resource")
            ):
                logger.info("检测到配置文件,开始转换")

                with open(
                    os.path.join(_path, "interface.json"), "r", encoding="utf-8"
                ) as f:
                    interface_config: dict = json.load(f)
                cfg.set(cfg.maa_config_name, "default")
                cfg.set(cfg.maa_resource_name, interface_config.get("name", "resource"))

                cfg.set(
                    cfg.maa_config_path,
                    os.path.join(
                        os.getcwd(),
                        "config",
                        cfg.get(cfg.maa_resource_name),
                        "config",
                        cfg.get(cfg.maa_config_name),
                        "maa_pi_config.json",
                    ),
                )

                cfg.set(cfg.maa_resource_path, _path)
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
            cfg.set(cfg.run_after_startup_arg, False)
            if directly:
                logger.info("检查到 -d 参数,直接启动")
                cfg.set(cfg.run_after_startup_arg, True)
            if DEV:
                logger.info("检查到 -DEV 参数,使用DEV模式")
                cfg.set(cfg.run_after_startup_arg, False)
                cfg.set(cfg.start_complete, False)

            logger.info("资源文件存在")
            cfg.set(cfg.start_complete, False)
            cfg.set(cfg.resource_exist, True)

            signalBus.resource_exist.emit(True)
            logger.info(
                f"资源版本:{maa_config_data.interface_config.get('version','unknown')}"
            )
    except:
        logger.error("检查资源文件失败")
        cfg.set(cfg.resource_exist, False)
        signalBus.resource_exist.emit(False)
        show_error_message()
        return False


def initialize_application():
    """应用初始化"""

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

    # 创建Qt应用实例
    app = QApplication(sys.argv)
    app.setAttribute(Qt.ApplicationAttribute.AA_DontCreateNativeWidgetSiblings)

    # 国际化配置
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

    # 异步事件循环初始化
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    # 启动主窗口并运行事件循环
    # 创建主窗口
    w = MainWindow()
    w.show()

    # 异步异常处理
    def handle_async_exception(loop, context):
        logger.exception("异步任务异常:", exc_info=context.get("exception"))

    loop.set_exception_handler(handle_async_exception)

    # 运行事件循环
    with loop:
        loop.run_forever()
    logger.debug("关闭异步任务完成")
    loop.close()


if __name__ == "__main__":
    logger.info(f"MFW 版本:{__version__}")

    initialize_environment()

    initialize_application()
