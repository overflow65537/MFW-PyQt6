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
import json
from typing import Dict

import maa
from maa.context import Context
from maa.custom_action import CustomAction
from maa.custom_recognition import CustomRecognition

import atexit
from qasync import QEventLoop, asyncio
from qfluentwidgets import ConfigItem, FluentTranslator
from PySide6.QtCore import Qt, QTranslator
from PySide6.QtWidgets import QApplication
from cryptography.fernet import Fernet

from app.utils.logger import logger
from app.common.config import cfg
from app.view.main_window import MainWindow
from app.common.config import Language
from app.common.__version__ import __version__
from app.utils.tool import Save_Config
from app.common.signal_bus import signalBus
from app.utils.i18n_manager import init_interface_i18n, update_interface_language
from pathlib import Path



if __name__ == "__main__":
    logger.info(f"MFW 版本:{__version__}")
    # 将当前工作目录设置为程序所在的目录，确保无论从哪里执行，其工作目录都正确设置为程序本身的位置，避免路径错误。
    #os.chdir(target_dir)  # 切换工作目录
    logger.debug(f"设置工作目录: {os.getcwd()}")

    # 检查是否存在密钥文件
    if not os.path.exists("k.ey"):
        logger.debug("生成密钥文件")
        key = Fernet.generate_key()
        with open("k.ey", "wb") as key_file:
            key_file.write(key)#TODO 密钥应该放在应用支持目录中

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


    """# 全局异常钩子
    def global_except_hook(exc_type, exc_value, exc_traceback):
        logger.exception(
            "未捕获的全局异常:", exc_info=(exc_type, exc_value, exc_traceback)
        )

    sys.excepthook = global_except_hook"""

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

    # 初始化 interface.json 国际化管理器
    interface_json_path = Path.cwd() / "interface.json"
    if interface_json_path.exists():
        try:
            init_interface_i18n(interface_json_path)
            update_interface_language()
            logger.info("Interface.json 国际化系统初始化成功")
        except Exception as e:
            logger.error(f"Interface.json 国际化系统初始化失败: {e}")
    else:
        logger.warning("未找到 interface.json 文件，跳过国际化初始化")

    # 异步事件循环初始化
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    # 初始化 GPU 信息缓存（在主窗口创建前）
    from app.utils.gpu_cache import gpu_cache
    gpu_cache.initialize()

    # 创建主窗口
    w = MainWindow()
    w.show()

    """# 异步异常处理
    def handle_async_exception(loop, context):
        logger.exception("异步任务异常:", exc_info=context.get("exception"))

    loop.set_exception_handler(handle_async_exception)"""

    # 运行事件循环
    with loop:
        loop.run_forever()
    logger.debug("关闭异步任务完成")
    loop.close()
