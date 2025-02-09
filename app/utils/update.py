from PyQt6.QtCore import QThread, pyqtBoundSignal
import os
import zipfile
from ..utils.tool import (
    for_config_get_url,
    replace_ocr,
    get_uuid,
    Read_Config,
    Save_Config,
    decrypt,
)
from ..common.signal_bus import signalBus
from ..utils.logger import logger
from ..common.maa_config_data import maa_config_data
from ..common.config import cfg

from typing import Dict
import requests
import shutil
import json


class BaseUpdate(QThread):
    stop_flag = False

    def download_file(self, url, file_path, progress_signal: pyqtBoundSignal):
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            total_size = int(response.headers.get("content-length", 0))
            downloaded_size = 0
            with open(file_path, "wb") as file:
                for data in response.iter_content(chunk_size=4096):
                    if self.stop_flag:
                        response.close()
                        return False
                    downloaded_size += len(data)
                    file.write(data)
                    progress_signal.emit(downloaded_size, total_size)
            return True
        except Exception as e:
            logger.exception(f"下载文件时出错{url} -> {file_path}")
            return False
        finally:
            if response:
                response.close()

    def extract_zip(self, zip_file_path, extract_to):
        try:
            with zipfile.ZipFile(zip_file_path, "r") as zip_ref:
                all_members = zip_ref.namelist()
                actual_main_folder = all_members[0].split("/")[0]
                zip_ref.extractall(extract_to)
            return actual_main_folder
        except Exception as e:
            logger.exception(f"解压文件时出错 {zip_file_path}解压到{extract_to}")
            return False

    def move_files(self, src, dst):
        try:
            shutil.copytree(src, dst, dirs_exist_ok=True)
            return True
        except Exception as e:
            logger.exception(f"移动文件时出错{src} -> {dst}")
            return False

    def remove_temp_files(self, *paths):
        for path in paths:
            if os.path.isdir(path):
                shutil.rmtree(path)
            elif os.path.isfile(path):
                os.remove(path)

    def Mirror_ckd(self):
        with open("k.ey", "rb") as key_file:
            key = key_file.read()
            return decrypt(cfg.get(cfg.Mcdk), key)


class Update(BaseUpdate):

    def run(self):
        url = maa_config_data.interface_config.get("url")

        cdk = self.Mirror_ckd()
        res_id = maa_config_data.interface_config.get("mirrorchyan_rid")
        version = maa_config_data.interface_config.get("version")
        if res_id:
            mirror_data: Dict[str, Dict] = self.mirror_check(
                res_id=res_id, version=version, cdk=cdk
            )
            if not mirror_data:
                github_dict = self.github_check(url)
                if not github_dict:
                    logger.error(f"GitHub更新检查失败: {url}")
                    signalBus.update_download_finished.emit(
                        {
                            "status": "failed",
                            "msg": self.tr(
                                "unknow error, unable to perform update check"
                            ),
                        }
                    )
                    return
                self.github_download(github_dict)
                return
            if mirror_data.get("data").get("version_name") == version:
                signalBus.update_download_finished.emit(
                    {
                        "status": "success",
                        "msg": self.tr("current version is latest"),
                    }
                )
                return
            if cdk:
                signalBus.update_download_finished.emit(
                    {
                        "status": "info",
                        "msg": self.tr(
                            "MirrorChyan update check successful, starting downloa"
                        ),
                    }
                )
                self.mirror_download(res_id, mirror_data)
                return
            else:
                signalBus.update_download_finished.emit(
                    {
                        "status": "info",
                        "msg": self.tr(
                            "MirrorChyan update check successful, but no CDK found, switching to Github download"
                        ),
                    }
                )
                github_url = self.assemble_gitHub_url(
                    mirror_data["data"].get("version_name"), url
                )
                if not github_url:
                    signalBus.update_download_finished.emit(
                        {
                            "status": "failed",
                            "msg": self.tr("Projeund, unable to perform update check"),
                        }
                    )
                    return
                github_dict = {
                    "zipball_url": github_url,
                    "tag_name": mirror_data["data"].get("version_name"),
                }
                self.github_download(github_dict)
                return
        else:
            github_dict = self.github_check(url)
            if not github_dict:
                logger.error(f"GitHub更新检查失败: {url}")
                signalBus.update_download_finished.emit(
                    {
                        "status": "failed",
                        "msg": self.tr("unknow error, unable to perform update check"),
                    }
                )
                return
            self.github_download(github_dict)
        signalBus.resource_exist.emit(True)

    def assemble_gitHub_url(self, version: str, url: str) -> str:
        """
        输入版本号和项目地址，返回GitHub项目源代码压缩包下载地址
        """
        if not url or not version:
            return False

        parts = url.split("/")
        try:
            username = parts[3]
            repository = parts[4]
        except IndexError:
            return False
        retuen_url = (
            f"https://api.github.com/repos/{username}/{repository}/zipball/{version}"
        )
        return retuen_url

    def mirror_check(self, res_id: str, version: str, cdk: str, ) -> Dict:
        """
        mirror检查更新
        Args:
            res_id (str): 资源id
            version (str): 版本号
            cdk (str): cdk
           
        Returns:
            Dict: 资源信息
        """

        url = f"https://mirrorc.top/api/resources/{res_id}/latest?current_version={version}&cdk={cdk}&user_agent=MFW_PYQT6"

        try:
            response = requests.get(url)
        except (
            requests.ConnectionError,
            requests.Timeout,
            requests.RequestException,
        ) as e:
            signalBus.update_download_finished.emit({"status": "failed", "msg": str(e)})
            return False

        mirror_data: Dict[str, Dict] = response.json()

        if mirror_data.get("code") != 0:
            logger.warning(f"更新检查失败: {mirror_data.get('msg')}")
            signalBus.update_download_finished.emit(
                {"status": "failed", "msg": mirror_data.get("msg")}
            )
            return False

        if mirror_data.get("msg") == "current version is latest":
            signalBus.update_download_finished.emit(
                {"status": "success", "msg": self.tr("current version is latest")}
            )
            return False
        return mirror_data

    def mirror_download(self, res_id, mirror_data):
        """
        mirror下载更新
        Args:
            res_id (str): 资源id
            mirror_data (Dict): 资源信息
        """
        self.stop_flag = False
        download_url: str = mirror_data["data"].get("url")
        hotfix_directory = os.path.join(os.getcwd(), "hotfix")
        os.makedirs(hotfix_directory, exist_ok=True)
        zip_file_path = os.path.join(hotfix_directory, f"{res_id}.zip")

        if not self.download_file(
            download_url, zip_file_path, signalBus.update_download_progress
        ):
            signalBus.update_download_finished.emit(
                {"status": "failed", "msg": self.tr("Download failed")}
            )
            return False

        if not self.extract_zip(zip_file_path, os.path.join(os.getcwd(), "hotfix")):
            signalBus.update_download_finished.emit(
                {"status": "failed", "msg": self.tr("Extraction failed")}
            )
            return False

        target_path = maa_config_data.resource_path
        if not self.move_files(
            os.path.join(os.getcwd(), "hotfix", "assets"), target_path
        ):
            signalBus.update_download_finished.emit(
                {"status": "failed", "msg": self.tr("Move files failed")}
            )
            return False

        maa_config_data.interface_config["version"] = mirror_data["data"].get(
            "version_name"
        )
        self.remove_temp_files(
            os.path.join(os.getcwd(), "hotfix", "assets"), zip_file_path
        )

        interface_date = Read_Config(maa_config_data.interface_config_path)
        interface_date["version"] = mirror_data["data"].get("version_name")
        interface_date["mirrorchyan_rid"] = res_id
        Save_Config(maa_config_data.interface_config_path, interface_date)

        signalBus.resource_exist.emit(True)
        signalBus.update_download_finished.emit(
            {"status": "success", "msg": self.tr("Update successful")}
        )
        return True

    def github_check(self, project_url: str) -> Dict:
        """
        github检查更新
        Args:
            project_url (str): 项目地址
        Returns:
            Dict: 更新信息
        """
        if not project_url:
            logger.warning("项目地址未配置，无法进行更新检查")
            signalBus.update_download_finished.emit(
                {
                    "status": "failed",
                    "msg": self.tr(
                        "Project address configuration not found, unable to perform update check"
                    ),
                }
            )
            return False
        url = for_config_get_url(project_url, "download")
        if url is None:
            logger.warning("项目地址配置错误，无法进行更新检查")
            signalBus.update_download_finished.emit(
                {
                    "status": "failed",
                    "msg": self.tr(
                        "Project address configuration error, unable to perform update check"
                    ),
                }
            )
            return False
        try:
            response = requests.get(url)
        except (
            requests.ConnectionError,
            requests.Timeout,
            requests.RequestException,
        ) as e:
            signalBus.update_download_finished.emit({"status": "failed", "msg": str(e)})
            return False

        update_dict: dict = response.json()
        logger.debug(
            f"更新检查结果: {json.dumps(update_dict, indent=4, ensure_ascii=False)}"
        )
        if update_dict.get("message"):
            signalBus.update_download_finished.emit(
                {"status": "failed", "msg": update_dict.get("message")}
            )
            return False
        if update_dict.get("tag_name", None) == maa_config_data.interface_config.get(
            "version"
        ):
            signalBus.update_download_finished.emit(
                {"status": "success", "msg": self.tr("current version is latest")}
            )
            return False
        return update_dict

    def github_download(self, update_dict: Dict):
        """
        github下载更新
        Args:
            update_dict (Dict): 更新信息
        """
        self.stop_flag = False
        download_url: str = update_dict["zipball_url"]
        hotfix_directory = os.path.join(os.getcwd(), "hotfix")
        os.makedirs(hotfix_directory, exist_ok=True)
        project_name = download_url.split("/")[5]
        zip_file_path = os.path.join(
            hotfix_directory, f"{project_name}-{update_dict['tag_name']}.zip"
        )

        if not self.download_file(
            download_url, zip_file_path, signalBus.update_download_progress
        ):
            signalBus.update_download_finished.emit(
                {"status": "failed", "msg": self.tr("Download failed")}
            )
            return

        target_path = maa_config_data.resource_path
        main_folder = self.extract_zip(
            zip_file_path, os.path.join(os.getcwd(), "hotfix")
        )
        if not main_folder:
            signalBus.update_download_finished.emit(
                {"status": "failed", "msg": self.tr("Extraction failed")}
            )
            return

        folder_to_extract = os.path.join(os.getcwd(), "hotfix", main_folder, "assets")
        if not self.move_files(folder_to_extract, target_path):
            signalBus.update_download_finished.emit(
                {"status": "failed", "msg": self.tr("Move files failed")}
            )
            return

        replace_ocr(target_path)
        self.remove_temp_files(
            os.path.join(os.getcwd(), "hotfix", main_folder), zip_file_path
        )

        interface_date = Read_Config(maa_config_data.interface_config_path)
        interface_date["version"] = update_dict["tag_name"]
        Save_Config(maa_config_data.interface_config_path, interface_date)
        signalBus.resource_exist.emit(True)
        signalBus.update_download_finished.emit(
            {"status": "success", "msg": self.tr("Update successful")}
        )

    def stop(self):
        self.stop_flag = True


class MirrorDownloadBundle(BaseUpdate):
    res_id = ""

    def run(self):
        self.stop_flag = False
        cdk = self.Mirror_ckd()
        url = f"https://mirrorc.top/api/resources/{self.res_id}/latest?current_version=&cdk={cdk}&user_agent=MFW_PYQT6"
        print(url)
        try:
            response = requests.get(url)
        except (
            requests.ConnectionError,
            requests.Timeout,
            requests.RequestException,
        ) as e:
            signalBus.download_finished.emit({"status": "failed", "msg": str(e)})
            return False
        mirror_data: Dict[str, Dict] = response.json()
        if mirror_data.get("code") != 0:
            logger.warning(f"下载检查失败: {mirror_data.get('msg')}")
            signalBus.download_finished.emit(
                {"status": "failed", "msg": mirror_data.get("msg")}
            )
            return

        download_url: str = mirror_data["data"].get("url")
        hotfix_directory = os.path.join(os.getcwd(), "hotfix")
        os.makedirs(hotfix_directory, exist_ok=True)
        project_name = self.res_id
        zip_file_path = os.path.join(
            hotfix_directory,
            f"{project_name}-{mirror_data['data'].get('version_name')}.zip",
        )

        if not self.download_file(
            download_url, zip_file_path, signalBus.bundle_download_progress
        ):
            signalBus.download_finished.emit(
                {"status": "failed", "msg": self.tr("Download failed")}
            )
            return

        if not self.extract_zip(zip_file_path, os.path.join(os.getcwd(), "hotfix")):
            signalBus.download_finished.emit(
                {"status": "failed", "msg": self.tr("Extraction failed")}
            )
            return

        target_path = os.path.join(os.getcwd(), "bundles", project_name)
        if not self.move_files(
            os.path.join(os.getcwd(), "hotfix", "assets"), target_path
        ):
            signalBus.download_finished.emit(
                {"status": "failed", "msg": self.tr("Move files failed")}
            )
            return

        interface_data = Read_Config(os.path.join(target_path, "interface.json"))
        interface_data["mirrorchyan_rid"] = self.res_id
        interface_data["version"] = mirror_data["data"].get("version_name")
        Save_Config(os.path.join(target_path, "interface.json"), interface_data)
        self.remove_temp_files(
            os.path.join(os.getcwd(), "hotfix", "assets"), zip_file_path
        )

        signalBus.download_finished.emit(
            {
                "status": "success",
                "msg": self.tr("Download successful"),
                "target_path": target_path,
                "project_name": project_name,
            }
        )

    def stop(self):
        self.stop_flag = True


class DownloadBundle(BaseUpdate):
    project_url = ""

    def run(self):
        self.stop_flag = False
        if not self.project_url:
            logger.warning("项目地址未配置，无法进行更新检查")
            signalBus.download_finished.emit(
                {"status": "failed", "msg": "项目地址未配置，无法进行更新检查"}
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
            signalBus.download_finished.emit({"status": "failed", "msg": str(e)})
            return

        download_url: str = content["zipball_url"]
        hotfix_directory = os.path.join(os.getcwd(), "hotfix")
        os.makedirs(hotfix_directory, exist_ok=True)
        project_name = download_url.split("/")[5]
        zip_file_path = os.path.join(
            hotfix_directory, f"{project_name}-{content['tag_name']}.zip"
        )

        if not self.download_file(
            download_url, zip_file_path, signalBus.bundle_download_progress
        ):
            signalBus.download_finished.emit(
                {"status": "failed", "msg": self.tr("Download failed")}
            )
            return
        main_folder = self.extract_zip(
            zip_file_path, os.path.join(os.getcwd(), "hotfix")
        )
        if not main_folder:
            signalBus.download_finished.emit(
                {"status": "failed", "msg": self.tr("Extraction failed")}
            )
            return

        target_path = os.path.join(os.getcwd(), "bundles", project_name)
        if not os.path.exists(target_path):
            os.makedirs(target_path)

        folder_to_extract = os.path.join(os.getcwd(), "hotfix", main_folder, "assets")
        if not self.move_files(folder_to_extract, target_path):
            signalBus.download_finished.emit(
                {"status": "failed", "msg": self.tr("Move files failed")}
            )
            return

        replace_ocr(target_path)
        self.remove_temp_files(
            os.path.join(os.getcwd(), "hotfix", project_name), zip_file_path
        )

        signalBus.download_finished.emit(
            {
                "status": "success",
                "msg": self.tr("Download successful"),
                "target_path": target_path,
                "project_name": project_name,
            }
        )

    def stop(self):
        self.stop_flag = True


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


class UpdateSelf(BaseUpdate):
    def run(self):
        with open(
            os.path.join(os.getcwd(), "config", "version.txt"), "r", encoding="utf-8"
        ) as f:
            version_data = f.read().split()
        cdk = self.Mirror_ckd()

        mirror_data:Dict[str,Dict] = self.mirror_check(cdk,version_data)

        if not mirror_data:
            return
        
        elif mirror_data.get("code") != 0:
            logger.warning(f"更新检查失败: {mirror_data.get('msg')}")
            signalBus.download_self_finished.emit(
                {"status": "failed", "msg": mirror_data.get("msg")}
            )
            return 

        elif mirror_data.get("data").get("version_name") == version_data[2]:
            logger.warning(f"当前版本已是最新版本")
            signalBus.download_self_finished.emit(
                {"status": "no_need", "msg": self.tr("current version is latest")}
            )
            return 
        elif mirror_data.get("data").get("url"):
            signalBus.download_self_finished.emit(
                {"status": "info", "msg": self.tr("MirrorChyan update check successful, starting download")}
            )
            logger.debug(f"mirror开始下载: {mirror_data.get('data').get('url')}")
            self._download(mirror_data.get("data").get("url"))
            version_data[3] = mirror_data["data"].get("version_name")
            with open(
                os.path.join(os.getcwd(), "config", "version.txt"), "w", encoding="utf-8"
            ) as f:
                f.write(" ".join(version_data))
                print(" ".join(version_data))
            return
        else:
            signalBus.download_self_finished.emit(
                {"status": "info", "msg": self.tr("MirrorChyan update check successful, but no CDK found, switching to Github download")}
            )
            github_url = self.assemble_gitHub_url(
                version_data,mirror_data["data"].get("version_name")
            )
            logger.debug(f"github开始下载: {github_url}")
            self._download(github_url)
            version_data[3] = mirror_data["data"].get("version_name")
            with open(
                os.path.join(os.getcwd(), "config", "version.txt"), "w", encoding="utf-8"
            ) as f:
                f.write(" ".join(version_data))
                print(" ".join(version_data))
            return
            
            
    def assemble_gitHub_url(self, version_data: list, target_version: str) -> str:
        """
        输入版本号和项目地址，返回GitHub项目源代码压缩包下载地址
        """
        url = f"https://github.com/overflow65537/MFW-PyQt6/releases/download/{target_version}/MFW-PyQt6-{version_data[0]}-{version_data[1]}-{target_version}.zip"
        return url
    
    def mirror_check(self,  cdk,version_data:list) -> Dict:
        """
        mirror检查更新
        Args:
            res_id (str): 资源id
            
            cdk (str): cdk
            version_data (list): 系统,架构,版本号
        Returns:
            Dict: 资源信息
        """

        url = f"https://mirrorc.top/api/resources/MFW-PyQt6/latest?current_version={version_data[2]}&cdk={cdk}&os={version_data[0]}&arch={version_data[1]}"

        try:
            response = requests.get(url)
        except (
            requests.ConnectionError,
            requests.Timeout,
            requests.RequestException,
        ) as e:
            signalBus.download_self_finished.emit({"status": "failed", "msg": str(e)})
            return False

        mirror_data: Dict[str, Dict] = response.json()


        return mirror_data

    def _download(self,download_url):

        self.stop_flag = False
       
        zip_file_path = os.path.join(os.getcwd(), "update.zip")
        if not self.download_file(
            download_url, zip_file_path, signalBus.download_self_progress
        ):
            signalBus.download_self_finished.emit(
                {
                    "status": "failed",
                    "msg": self.tr("Download failed"),
                }
            )
            return

        signalBus.download_self_finished.emit(
            {"status": "success"}
        )



    def stop(self):
        self.stop_flag = True
