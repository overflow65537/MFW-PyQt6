from PyQt6.QtCore import QThread
import os
import zipfile
from ..utils.tool import for_config_get_url, replace_ocr
from ..common.signal_bus import signalBus
from ..utils.logger import logger
from ..common.maa_config_data import maa_config_data
from ..common.config import cfg

import requests
import shutil
import json


class download_bundle(QThread):
    project_url = ""
    stop_flag = False

    def run(self):
        self.stop_flag = False
        if self.project_url == "":
            logger.warning("项目地址未配置，无法进行更新检查")
            signalBus.download_finished.emit(
                {"update_name": "download_bundle", "update_status": "failed"}
            )
            return
        url = for_config_get_url(self.project_url, "download")
        try:
            response = requests.get(url)
            response.raise_for_status()
            content = response.json()
            logger.debug(f"更新检查结果: {content}")
        except Exception as e:
            logger.warning(f"更新检查时出错: {e}")
            signalBus.download_finished.emit(
                {
                    "update_name": "download_bundle",
                    "update_status": "failed",
                    "error_msg": f"{e}",
                }
            )
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

            downloaded_size = 0
            with open(zip_file_path, "wb") as zip_file:
                for data in response.iter_content(chunk_size=4096):  # 分块下载
                    if self.stop_flag:
                        response.close()
                        zip_file.close()
                        return
                    downloaded_size += len(data)
                    zip_file.write(data)
                    signalBus.bundle_download_progress.emit(
                        downloaded_size, total_size
                    )  # 发出进度信号
                    print(f"B下载进度: {downloaded_size}/{total_size}")
                logger.debug(f"下载完成:{downloaded_size}/{total_size}")
        except:
            logger.exception("下载更新文件时出错")
            signalBus.download_finished.emit(
                {
                    "update_name": "download_bundle",
                    "update_status": "failed",
                    "error_msg": f"{e}",
                }
            )
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

        shutil.copytree(folder_to_extract, target_path, dirs_exist_ok=True)
        replace_ocr(target_path)
        shutil.rmtree(os.path.join(os.getcwd(), "hotfix", actual_main_folder))
        os.remove(zip_file_path)

        signalBus.download_finished.emit(
            {
                "update_name": "download_bundle",
                "update_status": "success",
                "target_path": target_path,
                "project_name": project_name,
            }
        )

    def stop(self, flag: bool = False):
        logger.debug(f"停止下载bundle: {flag}")
        self.stop_flag = flag


class Update(QThread):
    stop_flag = False

    def run(self):
        self.stop_flag = False
        project_url = maa_config_data.interface_config.get("url", None)
        if not project_url:
            logger.warning("项目地址未配置，无法进行更新检查")
            signalBus.update_download_finished.emit(
                {"update_name": "update", "update_status": "failed"}
            )
            return
        url = for_config_get_url(project_url, "download")
        if url is None:
            logger.warning("项目地址配置错误，无法进行更新检查")
            signalBus.update_download_finished.emit(
                {"update_name": "update", "update_status": "failed"}
            )
            return
        try:
            response = requests.get(url)
            response.raise_for_status()
            self.update_dict: dict = response.json()
            self.update_dict["update_name"] = "update"
            self.update_dict["update_status"] = "success"
            logger.debug(
                f"更新检查结果: {json.dumps(self.update_dict, indent=4, ensure_ascii=False)}"
            )
            if self.update_dict.get(
                "tag_name", None
            ) == maa_config_data.interface_config.get("version"):
                signalBus.update_download_finished.emit(self.update_dict)
                return

        except requests.exceptions.RequestException as e:
            logger.warning(f"更新检查时出错: {e}")
            signalBus.update_download_finished.emit(
                {
                    "update_name": "update",
                    "update_status": "failed",
                    "error_msg": f"{e}",
                }
            )
            return
        except Exception as e:
            logger.exception(f"更新检查时出现未知错误: {e}")
            signalBus.update_download_finished.emit(
                {
                    "update_name": "update",
                    "update_status": "failed",
                    "error_msg": f"{e}",
                }
            )
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

            downloaded_size = 0

            with open(zip_file_path, "wb") as zip_file:
                for data in response.iter_content(chunk_size=4096):  # 分块下载
                    if self.stop_flag:
                        response.close()
                        zip_file.close()
                        os.remove(zip_file_path)
                        return
                    downloaded_size += len(data)
                    zip_file.write(data)
                    signalBus.update_download_progress.emit(
                        downloaded_size, total_size
                    )  # 发出进度信号
                    print(f"B下载进度: {downloaded_size}/{total_size}")

        except Exception as e:
            logger.exception(f"下载更新文件时出现未知错误: {e}")
            signalBus.update_download_finished.emit(
                {
                    "update_name": "update",
                    "update_status": "failed",
                    "error_msg": f"{e}",
                }
            )
            return
        finally:
            if response:
                response.close()

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

            logger.info("更新进程完成")
            if cfg.get(cfg.run_after_startup):
                logger.info("启动GUI后运行任务")
                signalBus.start_task_inmediately.emit()
        except Exception as e:
            logger.exception(f"解压和替换文件时出错: {e}")
            signalBus.update_download_finished.emit(
                {
                    "update_name": "update",
                    "update_status": "failed",
                    "error_msg": f"{e}",
                }
            )
            return
        signalBus.update_download_finished.emit(self.update_dict)

    def stop(self, flag: bool = False):
        self.stop_flag = flag


class Readme(QThread):
    readme_url = ""

    def run(self):
        self.stop_flag = False
        logger.debug(f"读取README文件: {self.readme_url}")
        try:
            response = requests.get(self.readme_url)
            response.raise_for_status()
            content = response.text
            signalBus.readme_available.emit(content)
        except Exception as e:
            logger.exception(f"读取README文件时出错: {e}")
            signalBus.readme_available.emit(f"读取README文件时出错: {e}")


class UpdateSelf(QThread):
    stop_flag = False

    def run(self):
        self.stop_flag = False
        logger.debug("更新自身")
        url = "https://api.github.com/repos/overflow65537/MFW-PyQt6/releases/latest"
        with open(
            os.path.join(os.getcwd(), "config", "version.txt"), "r", encoding="utf-8"
        ) as f:
            version_data = f.read().split()

        try:
            response = requests.get(url)
            response.raise_for_status()
            content = response.json()
            logger.debug(f"更新检查结果: {content}")
            if content.get("tag_name", None) == version_data[2]:
                logger.info("当前版本已是最新")
                signalBus.download_self_finished.emit(
                    {"update_name": "update_self", "update_status": "no_need"}
                )  # 发出0表示最新版
                return
            version_data[3] = content.get("tag_name")
            assets_name = f"MFW-PyQt6-{version_data[0]}-{version_data[1]}-{content.get('tag_name')}.zip"
            logger.debug(f"下载更新文件: {assets_name}")
            for asset in content["assets"]:
                logger.debug(f"检查更新文件: {asset['name']}")
                if asset["name"] == assets_name:
                    download_url = asset["browser_download_url"]
                    break
            else:
                logger.error(f"未找到{assets_name}文件")
                signalBus.download_self_finished.emit(
                    {"update_name": "update_self", "update_status": "failed"}
                )  # 发出1表示下载失败
                return
            zip_file_path = os.path.join(os.getcwd(), "update.zip")
        except Exception as e:
            logger.exception(f"更新检查时出现错误: {e}")
            signalBus.download_self_finished.emit(
                {
                    "update_name": "update_self",
                    "update_status": "failed",
                    "error_msg": f"{e}",
                }
            )  # 发出1表示下载失败
            return

        try:
            response = requests.get(download_url, stream=True)
            response.raise_for_status()
            total_size = int(
                response.headers.get("content-length", 0)
            )  # 获取文件总大小

            downloaded_size = 0

            with open(zip_file_path, "wb") as zip_file:
                for data in response.iter_content(chunk_size=4096):  # 分块下载
                    if self.stop_flag:
                        response.close()
                        zip_file.close()
                        os.remove(zip_file_path)
                        signalBus.download_self_finished.emit(
                            {"update_name": "update_self", "update_status": "stoped"}
                        )  # 发出2表示手动停止
                        return
                    downloaded_size += len(data)
                    zip_file.write(data)
                    signalBus.download_self_progress.emit(
                        downloaded_size, total_size
                    )  # 发出进度信号
                    print(f"B下载进度: {downloaded_size}/{total_size}")
        except Exception as e:
            logger.exception(f"下载更新文件时出现错误: {e}")
            signalBus.download_self_finished.emit(
                {
                    "update_name": "update_self",
                    "update_status": "failed",
                    "error_msg": f"{e}",
                }
            )  # 发出1表示下载失败
            return
        finally:
            if response:
                response.close()

        signalBus.download_self_finished.emit(
            {"update_name": "update_self", "update_status": "success"}
        )  # 发出3表示下载完成

        with open(
            os.path.join(os.getcwd(), "config", "version.txt"), "w", encoding="utf-8"
        ) as f:
            f.write(" ".join(version_data))

    def stop(self, flag: bool = False):
        self.stop_flag = flag
