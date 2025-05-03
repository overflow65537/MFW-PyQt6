import logging
import os

from logging.handlers import TimedRotatingFileHandler

os.makedirs("./debug", exist_ok=True)
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
            "./debug/gui.log",
            when="midnight",  
            backupCount=3,    
            encoding="utf-8"
        ),
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger(__name__)
