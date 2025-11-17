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
MFW-ChainFlow Assistant 日志单元
作者:overflow65537
"""

import logging
import os

from logging.handlers import TimedRotatingFileHandler
from datetime import datetime

from app.common.signal_bus import signalBus

# 提取日志格式为常量
LOG_FORMAT = "[%(asctime)s][%(levelname)s][%(filename)s][L%(lineno)d][%(funcName)s] | %(message)s"


class LoggerManager:
    def __init__(self, log_file_path="debug/gui.log"):
        """
        初始化日志管理器。

        Args:
            log_file_path (str): 日志文件的路径，默认为 "debug/gui.log"。
        """
        self.logger = self._create_logger(log_file_path)
        # 关闭requests模块的日志输出
        requests_logger = logging.getLogger("urllib3")
        requests_logger.setLevel(logging.CRITICAL)

    def _create_logger(self, log_file_path):
        """
        创建或重新创建日志记录器。

        Args:
            log_file_path (str): 日志文件的路径。

        Returns:
            logging.Logger: 配置好的日志记录器。
        """
        # 获取根日志记录器
        root_logger = logging.getLogger()
        # 清除现有的处理器
        for handler in root_logger.handlers[:]:
            handler.close()
            root_logger.removeHandler(handler)

        os.makedirs(os.path.dirname(log_file_path), exist_ok=True)

        # 创建新的处理器
        file_handler = TimedRotatingFileHandler(
            log_file_path,
            when="midnight",
            backupCount=3,
            encoding="utf-8",
        )
        stream_handler = logging.StreamHandler()

        # 设置处理器的格式
        formatter = logging.Formatter(LOG_FORMAT)
        file_handler.setFormatter(formatter)
        stream_handler.setFormatter(formatter)

        # 配置日志记录器
        root_logger.setLevel(logging.DEBUG)
        root_logger.addHandler(file_handler)
        root_logger.addHandler(stream_handler)

        return root_logger

    def change_log_path(self, new_log_path):
        """
        在运行时更改日志的存放位置。

        Args:
            new_log_path (str): 新的日志文件路径。
        """
        self.logger = self._create_logger(new_log_path)


class QtSignalHandler(logging.Handler):
    """(预留) 自定义 Handler，可扩展把所有日志转发到 UI。

    当前未自动转发，以避免日志量过大造成 UI 卡顿。
    若需要全量同步，可在 LoggerManager._create_logger 中添加本 Handler。"""

    def emit(self, record: logging.LogRecord) -> None:
        # 暂不启用自动转发，仅作为占位
        pass


# 创建日志管理器实例
logger_manager = LoggerManager()
# 获取日志记录器
logger = logger_manager.logger
