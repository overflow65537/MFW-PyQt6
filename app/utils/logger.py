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

os.makedirs("debug", exist_ok=True)
# 获取requests模块的日志记录器
requests_logger = logging.getLogger("urllib3")
# 关闭requests模块的日志输出
requests_logger.setLevel(logging.CRITICAL)
# 设置日志记录器
logging.basicConfig(
    format="[%(asctime)s][%(levelname)s][%(filename)s][L%(lineno)d][%(funcName)s] | %(message)s",
    level=logging.DEBUG,
    handlers=[
        TimedRotatingFileHandler(
            os.path.join(os.getcwd(), "debug", "gui.log"),
            when="midnight",
            backupCount=3,
            encoding="utf-8",
        ),
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger(__name__)
