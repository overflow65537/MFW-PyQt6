from PyQt6.QtCore import QThread
import os
import zipfile
from ..utils.tool import for_config_get_url, show_error_message, replace_ocr
from ..common.signal_bus import signalBus
from ..utils.logger import logger
from ..common.maa_config_data import maa_config_data
from ..common.config import cfg

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

        download_url: str = content["zipball_url"]
        hotfix_directory = os.path.join(os.getcwd(), "hotfix")
        os.makedirs(hotfix_directory, exist_ok=True)
        project_name = download_url.split("/")[5]
        zip_file_path = os.path.join(
            hotfix_directory, f"{project_name}-{content['tag_name']}.zip"
        )

        try:
            response = requests.get(download_url, stream=True)
            total_size = int(
                response.headers.get("content-length", 0)
            )  # 获取文件总大小

            # 如果 total_size 为 0，尝试使用 shutil.copyfileobj 来估算进度
            downloaded_size = 0
            if total_size == 0:
                with open(zip_file_path, "wb") as zip_file:
                    print(f"A下载进度: {downloaded_size}/{downloaded_size}")
                    shutil.copyfileobj(response.raw, zip_file, length=4096)
                    downloaded_size = zip_file.tell()
                    signalBus.bundle_download_progress.emit(
                        downloaded_size, downloaded_size
                    )  # 发出进度信号，这里只能用已下载大小作为总大小的估计
                logger.debug(f"无法判断大小:{downloaded_size}")
            else:
                with open(zip_file_path, "wb") as zip_file:
                    for data in response.iter_content(chunk_size=4096):  # 分块下载
                        downloaded_size += len(data)
                        zip_file.write(data)
                        signalBus.bundle_download_progress.emit(
                            downloaded_size, total_size
                        )  # 发出进度信号
                        print(f"B下载进度: {downloaded_size}/{total_size}")
                    logger.debug(f"下载完成:{downloaded_size}/{total_size}")
        except:
            logger.exception("下载更新文件时出错")
            show_error_message()
            return
        signalBus.bundle_download_finished.emit()
        # 解压文件到指定路径
        target_path = os.path.join(os.getcwd(), "bundles", project_name)
        if not os.path.exists(target_path):
            os.makedirs(target_path)

        logger.debug(f"移动文件到 {target_path}")
        with zipfile.ZipFile(zip_file_path, "r") as zip_ref:
            all_members = zip_ref.namelist()
            actual_main_folder = all_members[0].split("/")[0]
            zip_ref.extractall(os.path.join(os.getcwd(), "hotfix"))

        folder_to_extract = os.path.join(
            os.getcwd(), "hotfix", actual_main_folder, "assets"
        )
        print(folder_to_extract)

        shutil.copytree(folder_to_extract, target_path, dirs_exist_ok=True)
        replace_ocr(target_path)
        shutil.rmtree(os.path.join(os.getcwd(), "hotfix", actual_main_folder))
        os.remove(zip_file_path)

        signalBus.download_finished.emit(
            {"target_path": target_path, "project_name": project_name}
        )


class Update(QThread):
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
            return
        try:

            response = requests.get(url)
            response.raise_for_status()
            self.update_dict: dict = response.json()
            logger.debug(
                f"更新检查结果: {json.dumps(self.update_dict, indent=4, ensure_ascii=False)}"
            )
            if self.update_dict.get(
                "tag_name", None
            ) == maa_config_data.interface_config.get("version"):
                self.update_available.emit(self.update_dict)
                return

        except requests.exceptions.RequestException as e:
            logger.warning(f"更新检查时出错: {e}")
            self.update_available.emit({})  # 发出空字典表示没有更新
            return
        except Exception as e:
            logger.exception(f"更新检查时出现未知错误: {e}")
            self.update_available.emit({})  # 发出空字典表示没有更新
            return
        download_url: str = self.update_dict["zipball_url"]
        hotfix_directory = os.path.join(os.getcwd(), "hotfix")
        os.makedirs(hotfix_directory, exist_ok=True)
        project_name = download_url.split("/")[5]
        zip_file_path = os.path.join(
            hotfix_directory, f"{project_name}-{self.update_dict['tag_name']}.zip"
        )
        response = None
        try:
            response = requests.get(download_url, stream=True)
            response.raise_for_status()
            total_size = int(
                response.headers.get("content-length", 0)
            )  # 获取文件总大小

            # 如果 total_size 为 0，尝试使用 shutil.copyfileobj 来估算进度
            downloaded_size = 0
            if total_size == 0:
                with open(zip_file_path, "wb") as zip_file:
                    shutil.copyfileobj(response.raw, zip_file, length=4096)
                    downloaded_size = zip_file.tell()
                    signalBus.update_download_progress.emit(
                        downloaded_size, downloaded_size
                    )  # 发出进度信号，这里只能用已下载大小作为总大小的估计
                    print(f"A下载进度: {downloaded_size}/{downloaded_size}")
            else:
                with open(zip_file_path, "wb") as zip_file:
                    for data in response.iter_content(chunk_size=4096):  # 分块下载
                        downloaded_size += len(data)
                        zip_file.write(data)
                        signalBus.update_download_progress.emit(
                            downloaded_size, total_size
                        )  # 发出进度信号
                        print(f"B下载进度: {downloaded_size}/{total_size}")
        except requests.exceptions.RequestException as e:
            logger.exception(f"下载更新文件时出错: {e}")
            self.update_available.emit({})  # 发出空字典表示没有更新
            show_error_message()
            return
        except Exception as e:
            logger.exception(f"下载更新文件时出现未知错误: {e}")
            self.update_available.emit({})  # 发出空字典表示没有更新
            show_error_message()
            return
        finally:
            if response:
                response.close()  # 确保响应对象被关闭

        signalBus.update_download_finished.emit()

        target_path = maa_config_data.resource_path
        logger.debug(f"解压文件到 {target_path}")
        try:
            with zipfile.ZipFile(zip_file_path, "r") as zip_ref:
                all_members = zip_ref.namelist()
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
            shutil.rmtree(os.path.join(os.getcwd(), "hotfix", actual_main_folder))
            os.remove(zip_file_path)

            signalBus.update_finished.emit()
            logger.info("更新进程完成")
            if cfg.get(cfg.run_after_startup):
                logger.info("启动GUI后运行任务")
                signalBus.start_task_inmediately.emit()
        except Exception as e:
            logger.exception(f"解压和替换文件时出错: {e}")
            show_error_message()
            return


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
