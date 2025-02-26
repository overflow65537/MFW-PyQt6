import json
import os
import shutil
import zipfile
from typing import Dict

import requests
from PyQt6.QtCore import QThread, pyqtBoundSignal

from ..common.signal_bus import signalBus
from ..utils.logger import logger
from ..common.maa_config_data import maa_config_data
from ..common.config import cfg
from ..utils.tool import (
    for_config_get_url,
    replace_ocr,
    Read_Config,
    Save_Config,
    decrypt,
)


# region 更新
class BaseUpdate(QThread):
    stop_flag = False
    
    def download_file(self, url, file_path, progress_signal: pyqtBoundSignal):
        need_clear_update = False
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            total_size = int(response.headers.get("content-length", 0))
            downloaded_size = 0
            with open(file_path, "wb") as file:
                for data in response.iter_content(chunk_size=4096):
                    if self.stop_flag:
                        response.close()
                        if os.path.exists("update.zip"):
                            need_clear_update = True
                        break

                    downloaded_size += len(data)
                    file.write(data)
                    progress_signal.emit(downloaded_size, total_size)
            if not need_clear_update and not self.stop_flag:
                return True
            else:
                if os.path.exists("update.zip"):
                    os.remove("update.zip")
                return False
        except Exception as e:
            logger.exception(f"下载文件时出错{url} -> {file_path}")
            if os.path.exists("update.zip"):
                os.remove("update.zip")
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
        """
        移动文件或文件夹。
        移动 src 到 dst。

        """
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
        try:
            with open("k.ey", "rb") as key_file:
                key = key_file.read()
                return decrypt(cfg.get(cfg.Mcdk), key)
        except Exception as e:
            logger.exception("获取ckd失败")

    def compare_versions(self, version1: str, version2: str) -> int:
        """
        比较两个版本号的大小。

        参数：
        version1 (str): 第一个版本号字符串。
        version2 (str): 第二个版本号字符串。

        返回：
        int: 如果 version1 大于 version2，则返回 1；如果 version1 小于 version2，则返回 -1；如果 version1 等于 version2，则返回 0。

        """
        try:
            v1_parts = [int(part) for part in version1.split(".")]
            v2_parts = [int(part) for part in version2.split(".")]

            max_length = max(len(v1_parts), len(v2_parts))

            v1_parts.extend([0] * (max_length - len(v1_parts)))
            v2_parts.extend([0] * (max_length - len(v2_parts)))

            for i in range(max_length):
                if v1_parts[i] > v2_parts[i]:
                    return 1  # version1 大于 version2
                elif v1_parts[i] < v2_parts[i]:
                    return -1  # version1 小于 version2

            return 0  # version1 等于 version2
        except Exception as e:
            logger.exception(f"比较版本号时出错: {e}")
            return 0
    def _response(self, url,used_by="mirror"):
        """
        发送 GET 请求并返回响应。
        """
        try:
            response = requests.get(url)
        except (
            requests.ConnectionError,
            requests.Timeout,
            requests.RequestException,
        ) as e:
            logger.error(f"更新检查失败: {e}")
            if used_by=="mirror":
                return {"status": "failed_info", "msg": "Mirror ERROR"+"\n"+str(e)+"\n"+self.tr("switching to Github download")}
            else:
                return {"status": "failed_info", "msg": "Github ERROR"+"\n"+str(e)}
        if response.status_code >= 500:
            logger.error(f"更新检查失败: {response.status_code}")
            if used_by=="mirror":
                return {"status": "failed_info", "msg": self.tr("MirrorChyan Update check failed")}
            else:
                return {"status": "failed_info", "msg": self.tr("Github Update check failed")}
        return response
    
    def handle_ocr_assets(self, target_path: str) -> bool:
        """处理 OCR 资源的核心方法
        Args:
            target_path (str): 目标存放路径
        Returns:
            bool: 操作成功返回 True，失败返回 False
        """
        # 自动定位 pipeline 目录
        pipeline_path = None
        for root, dirs, _ in os.walk(target_path):
            if "pipeline" in dirs:
                pipeline_path = os.path.dirname(root)  # 获取父级目录
                break

        if not pipeline_path:
            logger.error(f"在 {target_path} 下未找到 pipeline 目录")
            return False

        # 构建标准 OCR 路径
        valid_ocr_path = os.path.join(pipeline_path, "ocr")
        local_ocr = os.path.join("MFW_resource", "ocr")

        # 本地已有 OCR 资源
        if os.path.exists(local_ocr):
            logger.info("从本地缓存复制 OCR 文件")
            return self.move_files(local_ocr, valid_ocr_path)

        # 需要下载 OCR 资源
        try:
            response = requests.get(
                "https://api.github.com/repos/MaaXYZ/MaaCommonAssets/releases/latest"
            )
            release_data = response.json()
        except Exception as e:
            logger.error(f"获取OCR资源失败: {e}")
            return False

        # 下载和解压流程
        temp_dir = os.path.join(os.getcwd(), "temp_ocr")
        zip_path = os.path.join(temp_dir, "maa_common_assets.zip")

        if not self.download_file(release_data["zipball_url"], zip_path):
            return False

        # 解压并定位 OCR 文件
        extracted_folder = self.extract_zip(zip_path, temp_dir)
        ocr_source = os.path.join(temp_dir, extracted_folder, "assets", "OCR")

        if not extracted_folder or not os.path.exists(ocr_source):
            logger.error("OCR 资源目录不存在")
            self.remove_temp_files(temp_dir)
            return False

        # 保存到本地缓存
        if not self.move_files(ocr_source, local_ocr):
            self.remove_temp_files(temp_dir)
            return False

        # 复制到目标路径
        result = self.move_files(local_ocr, valid_ocr_path)
        self.remove_temp_files(temp_dir)
        return result


# endregion


# region 资源更新
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
            if mirror_data.get("status") == "failed_info":# mirror检查失败
                signalBus.update_download_finished.emit(mirror_data)
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
                elif github_dict is True:
                    return
                self.github_download(github_dict)
                return
            elif mirror_data.get("status") == "success":#无需更新
                signalBus.update_download_finished.emit(mirror_data)
                return
                
            if mirror_data.get("data",{}).get("url"):
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
                    "body": mirror_data["data"].get("release_note"),
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
            elif github_dict is True:
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

    def mirror_check(
        self,
        res_id: str,
        version: str,
        cdk: str,
    ) -> Dict:
        """
        mirror检查更新
        Args:
            res_id (str): 资源id
            version (str): 版本号
            cdk (str): cdk

        Returns:
            Dict: 资源信息
        """

        url = f"https://mirrorchyan.com/api/resources/{res_id}/latest?current_version={version}&cdk={cdk}&user_agent=MFW_PYQT6"

        cfg.set(cfg.is_change_cdk, False)


        response = self._response(url)
        if isinstance(response, dict):
            return response # 返回错误信息给run方法
        mirror_data: Dict[str, Dict] = response.json()
        if mirror_data.get("code") != 0:
            logger.warning(f"更新检查失败: {mirror_data.get('msg')}")
            return(
                {
                    "status": "failed_info",
                    "msg": mirror_data.get("msg")
                    + "\n"
                    + self.tr("switching to Github download"),
                }
            )
            

        if mirror_data.get("msg") == "current version is latest":
            return(
                {"status": "success", "msg": self.tr("current version is latest")}
            )
        return mirror_data

    def mirror_download(self, res_id, mirror_data: Dict[str, dict]):
        """
        mirror下载更新
        Args:
            res_id (str): 资源id
            mirror_data (Dict): 资源信息
        """
        # 读取当前版本
        with open(os.path.join(".", "config", "version.txt"), "r") as version_file:
            version = version_file.read().split()[2][1:]

        self.stop_flag = False
        # 下载更新
        download_url: str = mirror_data["data"].get("url")
        hotfix_directory = os.path.join(os.getcwd(), "hotfix")
        os.makedirs(hotfix_directory, exist_ok=True)
        zip_file_path = os.path.join(hotfix_directory, f"{res_id}.zip")

        if not self.download_file(
            download_url, zip_file_path, signalBus.update_download_progress
        ):
            signalBus.update_download_finished.emit(
                {"status": "failed_info", "msg": self.tr("Download failed")}
            )
            return False
        target_path = os.path.join(os.getcwd(), "hotfix", "assets")
        if not self.extract_zip(zip_file_path, target_path):
            signalBus.update_download_finished.emit(
                {"status": "failed_info", "msg": self.tr("Extraction failed")}
            )
            return False

        check_interface = Read_Config(os.path.join(target_path, "interface.json")).get(
            "MFW_min_req_version", "0.0.0.1"
        )
        logger.debug(f"最低需求版本: {check_interface}")
        logger.debug(f"当前版本: {version}")
        compare_result = self.compare_versions(check_interface, version)
        if compare_result == 1:
            signalBus.update_download_finished.emit(
                {
                    "status": "failed_info",
                    "msg": self.tr("Current MFW version is too low,update aborted"),
                }
            )
            return
        change_data = os.path.join(target_path, "changes.json")
        if os.path.exists(change_data):

            change_data = Read_Config(change_data).get("deleted", [])
            logger.debug(f"准备删除以下文件: {change_data}")
            for file in change_data:
                if "install" in file[:10]:
                    file_path = file.replace(
                        "install", maa_config_data.resource_path, 1
                    )
                elif "resource" in file[:10]:
                    file_path = file.replace(
                        "resource", f"{maa_config_data.resource_path}/resource", 1
                    )
                else:
                    logger.error(f"未知文件: {file}")
                    continue
                logger.debug(f"删除文件: {file_path}")
                if os.path.exists(file_path):
                    os.remove(file_path)
        # 移动文件
        if not self.move_files(target_path, maa_config_data.resource_path):
            signalBus.update_download_finished.emit(
                {"status": "failed_info", "msg": self.tr("Move files failed")}
            )
            return
        #更新MFW版本数据
        maa_config_data.interface_config["version"] = mirror_data["data"].get(
            "version_name"
        )
        #移除临时文件
        self.remove_temp_files(os.path.join(os.getcwd(), "hotfix"))

        signalBus.resource_exist.emit(True)
        signalBus.update_download_finished.emit(
            {
                "status": "success",
                "msg": self.tr("Update successful")
                + "\n"
                + mirror_data.get("data", {}).get("custom_data", "")
                + "\n"
                + mirror_data.get("data", {}).get("release_note", ""),
            }
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
            return(
                {
                    "status": "failed",
                    "msg": self.tr(
                        "Project address configuration not found, unable to perform update check"
                    ),
                }
            )
            
        url = for_config_get_url(project_url, "download")
        if url is None:
            logger.warning("项目地址配置错误，无法进行更新检查")
            return(
                {
                    "status": "failed",
                    "msg": self.tr(
                        "Project address configuration error, unable to perform update check"
                    ),
                }
            )
            
        response = self._response(url,used_by="github")
        if isinstance(response, dict):
            return response # 返回完成信息给run方法
        update_dict: dict = response.json()
        logger.debug(
            f"更新检查结果: {json.dumps(update_dict, indent=4, ensure_ascii=False)}"
        )
        if update_dict.get("message"):
            logger.warning(f"GitHub更新检查失败: {update_dict.get('message')}")
            return(
                {"status": "failed", "msg": update_dict.get("message")}
            )
            
        if update_dict.get("tag_name", None) == maa_config_data.interface_config.get(
            "version"
        ):
            logger.info("当前版本已是最新版本")
            return(
                {"status": "success", "msg": self.tr("current version is latest")}
            )
            
        return update_dict

    def github_download(self, update_dict: Dict):
        """
        github下载更新
        Args:
            update_dict (Dict): 更新信息
        """
        # 读取当前版本
        with open(os.path.join(".", "config", "version.txt"), "r") as version_file:
            version = version_file.read().split()[2][1:]

        self.stop_flag = False
        # 下载更新
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
        check_interface = Read_Config(
            os.path.join(folder_to_extract, "interface.json")
        ).get("MFW_min_req_version", "0.0.0.1")
        logger.debug(f"最低需求版本: {check_interface}")
        logger.debug(f"当前版本: {version}")
        compare_result = self.compare_versions(check_interface, version)
        if compare_result == 1:
            signalBus.update_download_finished.emit(
                {
                    "status": "failed",
                    "msg": self.tr("Current MFW version is too low,update aborted"),
                }
            )
            return
        # 删除旧的资源包
        if os.path.exists(target_path):
            logger.debug("开始清理旧资源文件")
            try:
                shutil.rmtree(os.path.join(target_path,"resource"))
                logger.debug("成功删除 resource 目录")
            except Exception as e:
                logger.error(f"删除 resource 失败: {e}")

            try:
                os.remove(os.path.join(target_path,"interface.json"))
                logger.debug("成功删除 interface.json")
            except Exception as e:
                logger.error(f"删除 interface.json 失败: {e}")

        if os.path.exists(os.path.join(target_path,"custom")):
            logger.debug("开始清理 custom 目录")
            try:
                shutil.rmtree(os.path.join(target_path,"custom"))
                logger.debug("成功删除 custom 目录")
            except Exception as e:
                logger.error(f"删除 custom 目录失败: {e}")
        if not self.move_files(folder_to_extract, target_path):
            logger.error(f"移动文件失败: {folder_to_extract} -> {target_path}")
            signalBus.update_download_finished.emit(
                {"status": "failed", "msg": self.tr("Move files failed")}
            )
            return

        replace_ocr(target_path)
        self.remove_temp_files(os.path.join(os.getcwd(), "hotfix"))

        interface_date = Read_Config(maa_config_data.interface_config_path)
        interface_date["version"] = update_dict["tag_name"]
        Save_Config(maa_config_data.interface_config_path, interface_date)
        signalBus.resource_exist.emit(True)
        signalBus.update_download_finished.emit(
            {
                "status": "success",
                "msg": self.tr("Update successful") + "\n" + update_dict.get("body"),
            }
        )

    def stop(self):
        self.stop_flag = True


# endregion
# region mirror下载资源包
class MirrorDownloadBundle(BaseUpdate):
    res_id = ""

    def run(self):
        self.stop_flag = False
        cdk = self.Mirror_ckd()
        url = f"https://mirrorchyan.com/api/resources/{self.res_id}/latest?current_version=&cdk={cdk}&user_agent=MFW_PYQT6"
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
                {
                    "status": "failed",
                    "msg": mirror_data.get("msg")
                    + "\n"
                    + self.tr("switching to Github download"),
                }
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
        self.remove_temp_files(os.path.join(os.getcwd(), "hotfix"))

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


# endregion

# region github下载资源包


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
        self.remove_temp_files(os.path.join(os.getcwd(), "hotfix"))

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


# endregion


# region 读取README文件
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


# endregion


# region 更新自身
class UpdateSelf(BaseUpdate):
    def run(self):
        with open(
            os.path.join(os.getcwd(), "config", "version.txt"), "r", encoding="utf-8"
        ) as f:
            version_data = f.read().split()
        cdk = self.Mirror_ckd()
        if cfg.get(cfg.is_change_cdk):
            logger.info(f"CDK被更改过")
            res_id = maa_config_data.interface_config.get("mirrorchyan_rid")
            url = f"https://mirrorchyan.com/api/resources/{res_id}/latest?current_version=v0.0.1&cdk={cdk}&user_agent=MFW_PYQT6"
            cfg.set(cfg.is_change_cdk, False)

            try:
                response = requests.get(url)
            except:
                pass

        mirror_data: Dict[str, Dict] = self.mirror_check(cdk, version_data)

        if mirror_data is False:
            update_url = f"https://api.github.com/repos/overflow65537/MFW-PyQt6/releases/latest"
            github_dict = self.github_check(update_url,version_data[2])
            if not github_dict:
                logger.error(f"GitHub更新检查失败: {update_url}")
                signalBus.update_download_finished.emit(
                    {
                        "status": "failed",
                        "msg": self.tr(
                            "unknow error, unable to perform update check"
                        ),
                    }
                )
                return
            elif github_dict is True:
                return
            for i in github_dict.get("assets"):
                if i.get("name") == f"MFW-PyQt6-{version_data[0]}-{version_data[1]}-{github_dict.get("tag_name")}.zip":
                    download_url = i.get("browser_download_url")
                    break
            self._download(download_url)
            version_data[3] = github_dict.get("tag_name")
            with open(
                os.path.join(os.getcwd(), "config", "version.txt"),
                "w",
                encoding="utf-8",
            ) as f:
                f.write(" ".join(version_data))
                print(" ".join(version_data))
            return
        if mirror_data.get("code") != 0:
            logger.warning(f"更新检查失败: {mirror_data.get('msg')}")
            signalBus.download_self_finished.emit(
                {
                    "status": "failed",
                    "msg": mirror_data.get("msg")
                    + "\n"
                    + self.tr("switching to Github download"),
                }
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
                {
                    "status": "info",
                    "msg": self.tr(
                        "MirrorChyan update check successful, starting download"
                    ),
                }
            )
            logger.debug(f"mirror开始下载: {mirror_data.get('data').get('url')}")
            self._download(mirror_data.get("data").get("url"))
            version_data[3] = mirror_data["data"].get("version_name")
            with open(
                os.path.join(os.getcwd(), "config", "version.txt"),
                "w",
                encoding="utf-8",
            ) as f:
                f.write(" ".join(version_data))
                print(" ".join(version_data))
            return
        else:
            signalBus.download_self_finished.emit(
                {
                    "status": "info",
                    "msg": self.tr(
                        "MirrorChyan update check successful, but no CDK found, switching to Github download"
                    ),
                }
            )
            github_url = self.assemble_gitHub_url(
                version_data, mirror_data["data"].get("version_name")
            )
            logger.debug(f"github开始下载: {github_url}")
            self._download(github_url)
            version_data[3] = mirror_data["data"].get("version_name")
            with open(
                os.path.join(os.getcwd(), "config", "version.txt"),
                "w",
                encoding="utf-8",
            ) as f:
                f.write(" ".join(version_data))
                print(" ".join(version_data))
            return
    def github_check(self, project_url: str,version) -> Dict:
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
        
        if project_url is None:
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
            response = requests.get(project_url)
        except (
            requests.ConnectionError,
            requests.Timeout,
            requests.RequestException,
        ) as e:
            signalBus.update_download_finished.emit({"status": "failed", "msg": str(e)})
            return False
        if response.status_code >= 500:
            signalBus.update_download_finished.emit(
                {"status": "failed", "msg": self.tr("Update check failed")}
            )
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
        if update_dict.get("tag_name", None) == version:
            signalBus.update_download_finished.emit(
                {"status": "success", "msg": self.tr("current version is latest")}
            )
            return True
        return update_dict

        
    def assemble_gitHub_url(self, version_data: list, target_version: str) -> str:
        """
        输入版本号和项目地址，返回GitHub项目源代码压缩包下载地址
        """
        url = f"https://github.com/overflow65537/MFW-PyQt6/releases/download/{target_version}/MFW-PyQt6-{version_data[0]}-{version_data[1]}-{target_version}.zip"
        return url

    def mirror_check(self, cdk, version_data: list) -> Dict:
        """
        mirror检查更新
        Args:
            res_id (str): 资源id

            cdk (str): cdk
            version_data (list): 系统,架构,版本号
        Returns:
            Dict: 资源信息
        """

        url = f"https://mirrorchyan.com/api/resources/MFW-PyQt6/latest?current_version={version_data[2]}&cdk={cdk}&os={version_data[0]}&arch={version_data[1]}"

        try:
            response = requests.get(url)
        except (
            requests.ConnectionError,
            requests.Timeout,
            requests.RequestException,
        ) as e:
            logger.error(f"Mirror更新检查失败: {e}")
            signalBus.download_self_finished.emit({"status": "failed", "msg": "MirrorChyan"+str(e)+"\n"+self.tr("switching to Github download")})
            return False
        if response.status_code >= 500:
            logger.error(f"Mirror更新检查失败: {response.status_code}")
            signalBus.download_self_finished.emit(
                {
                    "status": "failed",
                    "msg": self.tr("Download failed"),
                }
            )
            return False
        mirror_data: Dict[str, Dict] = response.json()

        return mirror_data

    def _download(self, download_url):

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

        signalBus.download_self_finished.emit({"status": "success"})

    def stop(self):
        self.stop_flag = True


# endregion
