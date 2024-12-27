from PyQt6.QtCore import QThread
import os
import zipfile
from ..utils.tool import for_config_get_url, show_error_message, replace_ocr
from ..common.signal_bus import signalBus
from ..utils.logger import logger
from ..common.maa_config_data import maa_config_data

import requests
import shutil
import json


class download_bundle(QThread):
    project_url = ""

    def run(self):
        if self.project_url == "":
            logger.warning("项目地址未配置，无法进行更新检查")
            signalBus.download_finished.emit({})  # 发出空字典表示没有更新
            return
        url = for_config_get_url(self.project_url, "download")
        try:
            response = requests.get(url)
            response.raise_for_status()
            content = response.json()
            logger.debug(f"更新检查结果: {content}")
        except Exception as e:
            logger.warning(f"更新检查时出错: {e}")
            signalBus.download_finished.emit({})  # 发出空字典表示没有更新
            return

        download_url = content["zipball_url"]
        # 设置要下载的文件的保存路径
        hotfix_directory = os.path.join(os.getcwd(), "hotfix")
        os.makedirs(hotfix_directory, exist_ok=True)
        project_name = download_url.split("/")[5]
        zip_file_path = os.path.join(
            hotfix_directory, f"{project_name}-{content['tag_name']}.zip"
        )

        # 下载文件
        try:
            response = requests.get(download_url)
        except:
            logger.exception("下载更新文件时出错")
            show_error_message()

        with open(zip_file_path, "wb") as zip_file:
            zip_file.write(response.content)

        # 解压文件到指定路径

        target_path = os.path.join(os.getcwd(), "bundles", project_name)
        if not os.path.exists(target_path):
            os.makedirs(target_path)

        logger.debug(f"移动文件到 {target_path}")
        with zipfile.ZipFile(zip_file_path, "r") as zip_ref:
            # 获取压缩包中的所有文件和文件夹
            all_members = zip_ref.namelist()

            # 找到实际的主文件夹名称
            actual_main_folder = all_members[0].split("/")[0]
            zip_ref.extractall(os.path.join(os.getcwd(), "hotfix"))

        folder_to_extract = os.path.join(
            os.getcwd(), "hotfix", actual_main_folder, "assets"
        )
        print(folder_to_extract)

        shutil.copytree(folder_to_extract, target_path, dirs_exist_ok=True)
        replace_ocr(target_path)
        # 删除下载的压缩包
        shutil.rmtree(os.path.join(os.getcwd(), "hotfix", actual_main_folder))
        os.remove(zip_file_path)

        # 任务完成，发出信号
        signalBus.download_finished.emit(
            {"target_path": target_path, "project_name": project_name}
        )


class check_Update(QThread):
    update_available = signalBus.update_available

    def run(self):
        project_url = maa_config_data.interface_config.get("url", None)
        if not project_url:
            logger.warning("项目地址未配置，无法进行更新检查")
            self.update_available.emit({})  # 发出空字典表示没有更新
            return
        url = for_config_get_url(project_url, "download")
        if url is None:
            logger.warning("项目地址配置错误，无法进行更新检查")
            self.update_available.emit({})  # 发出空字典表示没有更新
        try:

            response = requests.get(url)
            response.raise_for_status()
            content = response.json()
            logger.debug(
                f"更新检查结果: {json.dumps(content, indent=4, ensure_ascii=False)}"
            )
            self.update_available.emit(content)  # 发出更新内容
        except Exception as e:
            logger.warning(f"更新检查时出错: {e}")
            self.update_available.emit({})  # 发出空字典表示没有更新


class Update(QThread):
    update_dict = {}

    def run(self):
        download_url = self.update_dict["zipball_url"]
        # 设置要下载的文件的保存路径
        hotfix_directory = os.path.join(os.getcwd(), "hotfix")
        os.makedirs(hotfix_directory, exist_ok=True)
        project_name = download_url.split("/")[5]
        zip_file_path = os.path.join(
            hotfix_directory, f"{project_name}-{self.update_dict['tag_name']}.zip"
        )

        # 下载文件
        try:
            response = requests.get(download_url)
        except:
            logger.exception("下载更新文件时出错")
            show_error_message()

        with open(zip_file_path, "wb") as zip_file:
            zip_file.write(response.content)

        # 解压文件到指定路径
        target_path = maa_config_data.resource_path
        logger.debug(f"解压文件到 {target_path}")

        with zipfile.ZipFile(zip_file_path, "r") as zip_ref:
            # 获取压缩包中的所有文件和文件夹
            all_members = zip_ref.namelist()

            # 找到实际的主文件夹名称
            actual_main_folder = all_members[0].split("/")[0]
            if not os.path.exists(os.path.join(os.getcwd(), "hotfix")):
                os.makedirs(os.path.join(os.getcwd(), "hotfix"))
            zip_ref.extractall(os.path.join(os.getcwd(), "hotfix"))

        folder_to_extract = os.path.join(
            os.getcwd(), "hotfix", actual_main_folder, "assets"
        )
        print(folder_to_extract)

        shutil.copytree(folder_to_extract, target_path, dirs_exist_ok=True)
        replace_ocr(target_path)
        # 删除下载的压缩包
        shutil.rmtree(os.path.join(os.getcwd(), "hotfix", actual_main_folder))
        os.remove(zip_file_path)

        # 任务完成，发出信号
        signalBus.update_finished.emit()
        logger.info("更新进程完成")


class Readme(QThread):
    readme_url = ""

    def __init__(self):
        super().__init__()

    def run(self):
        logger.debug(f"读取README文件: {self.readme_url}")
        try:
            response = requests.get(self.readme_url)
            response.raise_for_status()
            content = response.text
            signalBus.readme_available.emit(content)
        except Exception as e:
            logger.exception(f"读取README文件时出错: {e}")
            signalBus.readme_available.emit(f"读取README文件时出错: {e}")
