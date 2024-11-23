import logging

# 设置日志记录器
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("gui.log"),
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger(__name__)
