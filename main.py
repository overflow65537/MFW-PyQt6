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

from app.common import maa_config_data

# 将当前工作目录设置为程序所在的目录，确保无论从哪里执行，其工作目录都正确设置为程序本身的位置，避免路径错误。
os.chdir(
    os.path.dirname(sys.executable)
    if getattr(sys, "frozen", False)
    else os.path.dirname(os.path.abspath(__file__))
)
import argparse

if not os.path.exists("main.py"):
    os.environ["MAAFW_BINARY_PATH"] = os.getcwd()
import maa
from maa.context import Context
from maa.custom_action import CustomAction
from maa.custom_recognition import CustomRecognition
import atexit
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
from app.utils.maafw import maafw


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

    def clear_agent():
        if maafw.agent:
            maafw.agent.disconnect()
        exec_path = cfg.get(cfg.agent_path)
        if not exec_path:
            logger.debug("没有找到agent")
            return
        # 获取文件名
        exec_path = os.path.basename(exec_path)
        import subprocess
        try:
            if sys.platform.startswith('win'):
                result = subprocess.run(
                    f'taskkill /F /IM {exec_path}',
                    shell=True,
                    capture_output=True,
                    text=True
                )
            elif sys.platform.startswith('linux'):
                result = subprocess.run(
                    f'pkill -9 {exec_path}',
                    shell=True,
                    capture_output=True,
                    text=True
                )
            elif sys.platform.startswith('darwin'):
                result = subprocess.run(
                    f'killall {exec_path}',
                    shell=True,
                    capture_output=True,
                    text=True
                )
            else:
                logger.warning(f"不支持的平台: {sys.platform}")
                return

            if result.returncode == 0:
                logger.debug(f"关闭agent成功，返回信息: {result.stdout.strip()}")
            else:
                logger.error(f"关闭agent失败，错误信息: {result.stderr.strip()}")
        except Exception as e:
            logger.exception(f"关闭agent时发生异常: {e}")
        finally:
            cfg.set(cfg.agent_path, "")
        if maafw.agent_thread:
            maafw.agent_thread.stop()  # 确保线程停止
    atexit.register(clear_agent)
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
    parser.add_argument("-DEV", "--DEV", action="store_true")

    args = parser.parse_args()
    try:
        main(args.resource, args.config, args.directly, args.DEV)

    except:
        logger.exception("GUI Process Error")
        show_error_message()
