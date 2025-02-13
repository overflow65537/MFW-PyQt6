import logging
import os

# 创建日志目录
if not os.path.exists("./debug"):
    os.makedirs("./debug")

# 设置日志记录器
logging.basicConfig(
    format="[%(asctime)s][%(levelname)s][%(filename)s][L%(lineno)d][%(funcName)s] | %(message)s",
    level=logging.DEBUG,
    handlers=[
        logging.FileHandler("./debug/gui.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger(__name__)
