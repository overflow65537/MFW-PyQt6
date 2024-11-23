from PyQt6.QtCore import QThread
import os
import zipfile
from ..utils.tool import for_config_get_url
from ..common.config import cfg
from ..common.signal_bus import signalBus
from ..utils.logger import logger

import requests


class check_Update(QThread):
    update_available = signalBus.update_available

    def run(self):
        url = for_config_get_url(cfg.get(cfg.Project_url), "download")
        try:
            response = requests.get(url)
            response.raise_for_status()
            content = response.json()
            self.update_available.emit(content)  # 发出更新内容
        except Exception as e:
            logger.warning(f"更新检查时出错: {e}")
            self.update_available.emit({})  # 发出空字典表示没有更新


class Update(QThread):
    update_finished = signalBus.update_finished  # 定义一个信号，用于通知任务完成

    def __init__(self, update_dict):
        super().__init__()
        self.update_dict = update_dict

    def run(self):
        for i in self.update_dict["assets"]:
            if "update" in i["name"]:
                download_url = i["browser_download_url"]
                break

        # 设置要下载的文件的保存路径
        hotfix_directory = os.path.join(os.getcwd(), "hotfix")
        os.makedirs(hotfix_directory, exist_ok=True)
        zip_file_path = os.path.join(
            hotfix_directory, f"update-{self.update_dict['tag_name']}.zip"
        )

        # 下载文件
        response = requests.get(download_url)
        with open(zip_file_path, "wb") as zip_file:
            zip_file.write(response.content)

        # 解压文件到指定路径
        target_path = cfg.get(cfg.Maa_resource)
        with zipfile.ZipFile(zip_file_path, "r") as zip_ref:
            zip_ref.extractall(target_path)

        # 删除下载的压缩包
        os.remove(zip_file_path)

        # 任务完成，发出信号
        self.update_finished.emit()
