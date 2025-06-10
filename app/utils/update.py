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
MFW-ChainFlow Assistant 更新单元
作者:overflow65537
"""

from ast import Str
from PySide6.QtCore import QThread, SignalInstance

import requests
from requests import Response
import json
import os
import shutil
import zipfile
import time
from typing import Dict, Optional


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
    channel_map = {0: "stable", 1: "beta", 2: "alpha"}

    def get_proxy_data(self) -> dict|None:
        proxy_config = {}
        if cfg.get(cfg.proxy) == 0:
            proxy_config["http"] = f"http://{cfg.get(cfg.http_proxy)}"
            proxy_config["https"] = f"http://{cfg.get(cfg.http_proxy)}"
        elif cfg.get(cfg.proxy) == 1:
            proxy_config["http"] = f"socks5://{cfg.get(cfg.http_proxy)}"
            proxy_config["https"] = f"socks5://{cfg.get(cfg.http_proxy)}"

        proxies: dict = {}
        for key, value in proxy_config.items():
            if value:
                proxies[key] = value
        if proxies == {'http': 'http://', 'https': 'http://'}:
            logger.debug("代理配置为空")
            return None
        else:
            logger.debug(f"使用代理配置: {proxies}")
            return proxies

    def download_file(self, url, file_path, progress_signal: SignalInstance, use_proxies):
        need_clear_update = False
        response = None
        if use_proxies:
            proxies = self.get_proxy_data()
        else:
            proxies = None

        if os.path.exists("NO_SSL"):
            verify = False
            logger.debug("检测到NO_SSL文件，跳过SSL验证")
        else:
            verify = True
        try:
            response = requests.get(
                url, stream=True, verify=verify, timeout=10, proxies=proxies
            )
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
            logger.exception(f"下载文件时出错{url} -> {file_path}\n{e}")
            if os.path.exists("update.zip"):
                os.remove("update.zip")
            return False
        finally:
            if response:
                response.close()

    def extract_zip(self, zip_file_path, extract_to):
        try:
            with zipfile.ZipFile(
                zip_file_path, "r", metadata_encoding="utf-8"
            ) as zip_ref:
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

    def Mirror_ckd(self) -> str:
        try:
            with open("k.ey", "rb") as key_file:
                key = key_file.read()
                return decrypt(cfg.get(cfg.Mcdk), key)
        except Exception as e:
            logger.exception("获取ckd失败")
            return ""

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

    def _mirror_response(self, url):
        """
        处理镜像源（MirrorChyan）的GET请求并返回响应。
        """
        # SSL验证配置
        if os.path.exists("NO_SSL"):
            verify = False
            logger.debug("检测到NO_SSL文件，跳过SSL验证")
        else:
            verify = True

        try:
            response = requests.get(url, timeout=10, verify=verify)
        except requests.exceptions.SSLError as e:
            logger.error(f"镜像源更新检查失败（SSL错误）: {e}")
            return {
                "status": "failed_info",
                "msg": self.tr("MirrorChyan Update check failed SSL error"),
            }
        except (
            requests.ConnectionError,
            requests.Timeout,
            requests.RequestException,
        ) as e:
            logger.error(f"镜像源更新检查失败（连接错误）: {e}")
            return {
                "status": "failed_info",
                "msg": "Mirror ERROR"
                + "\n"
                + str(e)
                + "\n"
                + self.tr("switching to Github download"),
            }

        # 处理500+状态码
        if response.status_code >= 500:
            logger.error(f"镜像源更新检查失败（状态码{response.status_code}）")
            return {
                "status": "failed_info",
                "msg": self.tr("MirrorChyan Update check failed,status code: ")
                + str(response.status_code),
            }
        return response

    def _github_response(self, url):
        """
        处理GitHub的GET请求并返回响应。
        """
        # SSL验证配置
        if os.path.exists("NO_SSL"):
            verify = False
            logger.debug("检测到NO_SSL文件，跳过SSL验证")
        else:
            verify = True
        proxies = self.get_proxy_data()

        try:
            response = requests.get(url, timeout=10, verify=verify, proxies=proxies)
            response.raise_for_status()
        except requests.exceptions.SSLError as e:
            logger.error(f"GitHub更新检查失败（SSL错误）: {e}")
            return {
                "status": "failed",
                "msg": self.tr("Github Update check failed SSL error"),
            }
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 403:
                logger.warning("GitHub API请求被限制")
                return {
                    "status": "failed",
                    "msg": self.tr(
                        "GitHub API request limit exceeded,please try again later"
                    ),
                }
            else:
                logger.error(f"GitHub更新检查失败（HTTP错误）: {e}")
                return {
                    "status": "failed",
                    "msg": self.tr("Github Update check failed HTTP error,code: ")
                    + str(e),
                }

        except (
            requests.ConnectionError,
            requests.Timeout,
            requests.RequestException,
        ) as e:
            logger.error(f"GitHub更新检查失败（连接错误）: {e}")
            return {"status": "failed", "msg": "Github ERROR" + "\n" + str(e)}

        return response

    def read_version(self):
        if os.path.exists(os.path.join(os.getcwd(), "config", "version.json")):
            logger.debug("从json文件读取版本号")
            return Read_Config(os.path.join(os.getcwd(), "config", "version.json"))
        else:
            logger.debug("从txt文件读取版本号")
            try:
                with open("config/version.txt", "r", encoding="utf-8") as f:
                    version_list = f.read().strip().split()
                    version_data = {
                        "os": version_list[0],
                        "arch": version_list[1],
                        "version": version_list[2],
                    }
                    return version_data

            except Exception as e:
                logger.exception(f"读取版本号时出错: {e}")
                return None

    def mirror_check(
        self,
        res_id: str,
        cdk: str,
        version: str,
        update_type: int = 0,  # 0代表资源更新,1代表MFW更新
        os_type: Optional[str] = None,
        arch: Optional[str] = None,
        channel: Optional[str] = "stable",
    ) -> Dict:
        if update_type == 0:  # 资源更新
            if maa_config_data.interface_config.get("mirrorchyan_multiplatform", False):
                logger.debug("检查到agent字段,使用多平台更新")
                url = f"https://mirrorchyan.com/api/resources/{res_id}/latest?current_version={version}&cdk={cdk}&os={os_type}&arch={arch}&channel={channel}&user_agent=MFW_PyQt6"
            else:
                url = f"https://mirrorchyan.com/api/resources/{res_id}/latest?current_version={version}&cdk={cdk}&channel={channel}&user_agent=MFW_PyQt6"

        else:  # MFW更新
            url = f"https://mirrorchyan.com/api/resources/MFW-PyQt6/latest?current_version={version}&cdk={cdk}&os={os_type}&arch={arch}&channel={channel}"

        response = self._mirror_response(url)
        if isinstance(response, dict):
            return response  # 返回错误信息给run方法
        mirror_data: Dict[str, Dict] = response.json()
        if mirror_data.get("code") == 1001:
            logger.warning(f"更新检查失败: {mirror_data.get('msg')}")
            return {
                "status": "failed_info",
                "msg": self.tr("INVALID_PARAMS")
                + "\n"
                + self.tr("switching to Github download"),
            }
        elif mirror_data.get("code") == 7001:
            logger.warning(f"更新检查失败: {mirror_data.get('msg')}")
            return {
                "status": "failed_info",
                "msg": self.tr("KEY_EXPIRED")
                + "\n"
                + self.tr("switching to Github download"),
            }
        elif mirror_data.get("code") == 7002:
            logger.warning(f"更新检查失败: {mirror_data.get('msg')}")
            return {
                "status": "failed_info",
                "msg": self.tr("KEY_INVALID")
                + "\n"
                + self.tr("switching to Github download"),
            }
        elif mirror_data.get("code") == 7003:
            logger.warning(f"更新检查失败: {mirror_data.get('msg')}")
            return {
                "status": "failed_info",
                "msg": self.tr("RESOURCE_QUOTA_EXHAUSTED")
                + "\n"
                + self.tr("switching to Github download"),
            }
        elif mirror_data.get("code") == 7004:
            logger.warning(f"更新检查失败: {mirror_data.get('msg')}")
            return {
                "status": "failed_info",
                "msg": self.tr("KEY_MISMATCHED")
                + "\n"
                + self.tr("switching to Github download"),
            }
        elif mirror_data.get("code") == 8001:
            logger.warning(f"更新检查失败: {mirror_data.get('msg')}")
            return {
                "status": "failed_info",
                "msg": self.tr("RESOURCE_NOT_FOUND")
                + "\n"
                + self.tr("switching to Github download"),
            }
        elif mirror_data.get("code") == 8002:
            logger.warning(f"更新检查失败: {mirror_data.get('msg')}")
            return {
                "status": "failed_info",
                "msg": self.tr("INVALID_OS")
                + "\n"
                + self.tr("switching to Github download"),
            }
        elif mirror_data.get("code") == 8003:
            logger.warning(f"更新检查失败: {mirror_data.get('msg')}")
            return {
                "status": "failed_info",
                "msg": self.tr("INVALID_ARCH")
                + "\n"
                + self.tr("switching to Github download"),
            }
        elif mirror_data.get("code") == 8004:
            logger.warning(f"更新检查失败: {mirror_data.get('msg')}")
            return {
                "status": "failed_info",
                "msg": self.tr("INVALID_CHANNEL")
                + "\n"
                + self.tr("switching to Github download"),
            }
        elif mirror_data.get("code") != 0:
            logger.warning(f"更新检查失败: {mirror_data.get('msg')}")
            msg_value = str(mirror_data.get("msg", ""))
            return {
                "status": "failed_info",
                "msg": msg_value + "\n" + self.tr("switching to Github download"),
            }

        data = mirror_data.get("data")
        if data is not None and data.get("version_name") == version:
            return {"status": "success", "msg": self.tr("current version is latest")}
        return mirror_data

    def github_check(self, project_url: str, version: str):
        """
        检查 GitHub 上的更新。
        """
        logger.info(f"开始GitHub更新检查: {project_url}")
        response = None
        try:
            response = self._github_response(project_url)
            if isinstance(response, dict):
                logger.warning(f"GitHub请求失败: {response.get('msg')}")
                return response

            update_dict: dict[str, dict] | dict[str, str] = response.json()
            logger.debug(f"GitHub响应数据: {json.dumps(update_dict, indent=2)}")

            if "message" in update_dict and isinstance(update_dict["message"], str):
                error_msg = self.tr("GitHub API ERROR: ") + update_dict["message"]
                logger.error(error_msg)
                return {"status": "failed", "msg": error_msg}

            if update_dict.get("tag_name", None) == version:
                logger.info("当前已是最新版本")
                return {
                    "status": "no_need",
                    "msg": self.tr("current version is latest"),
                }

            return update_dict
        except json.JSONDecodeError as e:
            if isinstance(response, Response):
                logger.exception(f"GitHub响应解析失败: {response.text[:200]}\n{e}")
            else:
                logger.exception(f"GitHub响应解析失败: 未收到响应\n{e}")
            return {"status": "failed", "msg": "Invalid GitHub response"}
        except Exception as e:
            logger.exception(f"GitHub检查过程中发生未预期错误{e}")
            return {"status": "failed", "msg": str(e)}

    def clear_change(self, target_path):
        # 清理旧文件
        change_data_path = os.path.join(target_path, "changes.json")
        try:
            if os.path.exists(change_data_path):

                change_data = Read_Config(change_data_path).get("deleted", [])
                logger.info(f"需要清理 {len(change_data)} 个文件")

                for file in change_data:
                    if "install" in file[:10]:
                        file_path = file.replace(
                            "install", maa_config_data.resource_path, 1
                        )
                    elif "resource" in file[:10]:
                        file_path = file.replace(
                            "resource",
                            f"{maa_config_data.resource_path}/resource",
                            1,
                        )
                    else:
                        logger.error(f"未知文件格式: {file}")
                        continue

                    logger.debug(f"尝试删除: {file_path}")
                    if os.path.exists(file_path):
                        try:
                            if os.path.isdir(file_path):
                                shutil.rmtree(file_path)
                            else:
                                os.remove(file_path)
                        except Exception as e:
                            logger.error(f"删除失败 [{file_path}]: {str(e)}")
            else:
                logger.warning("未找到 changes.json 文件,执行全部清理")
                shutil.rmtree(maa_config_data.resource_path)

        except Exception as e:
            logger.exception("清理旧文件时发生错误")
            signalBus.update_download_finished.emit(
                {
                    "status": "failed_info",
                    "msg": self.tr("Failed to clean up temporary files"),
                }
            )
            return False


# endregion


# region 资源更新
class Update(BaseUpdate):

    def run(self):
        time.sleep(0.5)
        parts = maa_config_data.interface_config.get("url", "").split("/")
        username = parts[3]
        repository = parts[4]

        url = f"https://api.github.com/repos/{username}/{repository}/releases/latest"
        cdk = self.Mirror_ckd()
        res_id = maa_config_data.interface_config.get("mirrorchyan_rid")
        version = maa_config_data.interface_config.get("version")
        channel = self.channel_map.get(cfg.get(cfg.resource_update_channel))

        version_data = self.read_version()
        if version_data:
            os_type = version_data.get("os")
            arch = version_data.get("arch")
        else:
            raise Exception("Update failed: version_data is None")
        # 检查 url 类型并转换
        if url is None:
            logger.error("URL 为 None，无法进行 GitHub 检查")
            signalBus.update_download_finished.emit(
                {
                    "status": "failed",
                    "msg": self.tr("No URL found"),
                }
            )
            return
        elif not isinstance(url, str):
            logger.error("URL 既不是字符串也不是有效的列表类型")
            signalBus.update_download_finished.emit(
                {
                    "status": "failed",
                    "msg": self.tr("No valid URL found"),
                }
            )
            return
        if not version:
            logger.error("版本号为空，无法进行 MirrorChyan 和 GitHub 检查")
            signalBus.update_download_finished.emit(
                {
                    "status": "failed",
                    "msg": self.tr("No version found"),
                }
            )
            return

        if res_id and (not cfg.get(cfg.force_github)):
            mirror_data: Dict[str, Dict] = self.mirror_check(
                res_id=res_id,
                version=version,
                cdk=cdk,
                channel=channel,
                os_type=os_type,
                arch=arch,
                update_type=0,
            )
            if mirror_data.get("status") == "failed_info":  # mirror检查失败
                signalBus.update_download_finished.emit(mirror_data)

                # URL构造

                github_dict = self.github_check(url, version=version)
                if (
                    github_dict.get("status") == "failed"
                    or github_dict.get("status") == "success"
                ):  # github检查失败:
                    signalBus.update_download_finished.emit(github_dict)
                    return
                else:
                    self.github_download(github_dict)
                    return
            elif mirror_data.get("status") == "success":  # 无需更新
                signalBus.update_download_finished.emit(mirror_data)
                return

            if mirror_data.get("data", {}).get("url"):
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

                github_dict = self.github_check(url, version=version)
                if (
                    github_dict.get("status") == "failed"
                    or github_dict.get("status") == "success"
                ):  # github检查失败:
                    signalBus.update_download_finished.emit(github_dict)
                    return
                self.github_download(github_dict)
                return
        else:
            github_dict = self.github_check(url, version=version)
            if (
                github_dict.get("status") == "failed"
                or github_dict.get("status") == "success"
            ):  # github检查失败:
                signalBus.update_download_finished.emit(github_dict)
                return

            self.github_download(github_dict)

    def assemble_gitHub_url(self, version: str, url: str) -> Optional[str]:
        """
        输入版本号和项目地址，返回GitHub项目源代码压缩包下载地址
        """
        if not url or not version:
            # 返回 None
            return None

        parts = url.split("/")
        try:
            username = parts[3]
            repository = parts[4]
        except IndexError:
            # 返回 None
            return None
        retuen_url = (
            f"https://api.github.com/repos/{username}/{repository}/zipball/{version}"
        )
        return retuen_url

    def mirror_download(self, res_id, mirror_data: Dict[str, dict]):
        """mirror下载更新"""
        try:
            # 版本文件读取
            version_file_path = os.path.join(".", "config", "version.txt")
            logger.info(f"正在读取版本文件: {version_file_path}")
            with open(version_file_path, "r") as version_file:
                v_data = version_file.read().split()
                version = v_data[2][1:]
                logger.debug(f"当前版本: {version}")
        except FileNotFoundError:
            logger.exception("版本文件未找到")
            signalBus.update_download_finished.emit(
                {"status": "failed_info", "msg": self.tr("version file not found")}
            )
            return False
        except IndexError:
            logger.exception("版本文件格式错误")
            signalBus.update_download_finished.emit(
                {"status": "failed_info", "msg": self.tr("version file format error")}
            )
            return False

        self.stop_flag = False
        try:
            # 下载过程
            download_url: str = mirror_data["data"].get("url", "")
            logger.info(f"开始下载镜像资源 [URL: {download_url}]")

            hotfix_directory = os.path.join(os.getcwd(), "hotfix")
            os.makedirs(hotfix_directory, exist_ok=True)
            zip_file_path = os.path.join(hotfix_directory, f"{res_id}.zip")

            if not self.download_file(
                download_url,
                zip_file_path,
                signalBus.update_download_progress,
                use_proxies=False,
            ):
                logger.error(f"镜像下载失败 [URL: {download_url}]")
                signalBus.update_download_finished.emit(
                    {"status": "failed_info", "msg": self.tr("Download failed")}
                )
                return False

            # 解压过程
            target_path = os.path.join(os.getcwd(), "hotfix", "assets")
            logger.info(f"开始解压文件到: {target_path}")
            if not self.extract_zip(zip_file_path, target_path):
                logger.error(f"解压失败 [路径: {zip_file_path}]")
                signalBus.update_download_finished.emit(
                    {"status": "failed_info", "msg": self.tr("Extraction failed")}
                )
                return False

            # 版本兼容性检查
            interface_path = os.path.join(target_path, "interface.json")
            check_interface = Read_Config(interface_path).get(
                "MFW_min_req_version", "0.0.0.1"
            )
            logger.info(f"版本检查 - 最低需求: {check_interface} | 当前: {version}")

            compare_result = self.compare_versions(check_interface, version)
            if compare_result == 1:
                logger.warning("当前版本过低，已中止更新")
                signalBus.update_download_finished.emit(
                    {
                        "status": "failed_info",
                        "msg": self.tr(
                            "Current MFW version is too low, update aborted"
                        ),
                    }
                )
                return False

            # 清理旧文件
            change_data_path = os.path.join(target_path, "changes.json")
            if os.path.exists(change_data_path):
                try:
                    change_data = Read_Config(change_data_path).get("deleted", [])
                    logger.info(f"需要清理 {len(change_data)} 个文件")

                    for file in change_data:
                        if "install" in file[:10]:
                            file_path = file.replace(
                                "install", maa_config_data.resource_path, 1
                            )
                        elif "resource" in file[:10]:
                            file_path = file.replace(
                                "resource",
                                f"{maa_config_data.resource_path}/resource",
                                1,
                            )
                        else:
                            logger.error(f"未知文件格式: {file}")
                            continue

                        logger.debug(f"尝试删除: {file_path}")
                        if os.path.exists(file_path):
                            try:
                                if os.path.isdir(file_path):
                                    shutil.rmtree(file_path)
                                else:
                                    os.remove(file_path)
                            except Exception as e:
                                logger.error(f"删除失败 [{file_path}]: {str(e)}")
                except Exception as e:
                    logger.exception("清理旧文件时发生错误")
                    signalBus.update_download_finished.emit(
                        {
                            "status": "failed_info",
                            "msg": self.tr("Failed to clean up temporary files"),
                        }
                    )
                    return False

            # 移动文件
            logger.info(f"移动文件到资源目录: {maa_config_data.resource_path}")
            if not self.move_files(target_path, maa_config_data.resource_path):
                logger.error(
                    f"文件移动失败: {target_path} -> {maa_config_data.resource_path}"
                )
                signalBus.update_download_finished.emit(
                    {"status": "failed_info", "msg": self.tr("Move file failed")}
                )
                return False

            # 更新配置
            version_name: str = mirror_data["data"].get("version_name", "v0.0.1")
            version_data: dict = {"version": version_name}
            maa_config_data.interface_config.update(version_data)
            logger.info(f"版本号更新为: {version_name}")

            # 清理临时文件
            self.remove_temp_files(os.path.join(os.getcwd(), "hotfix"))
            logger.debug("临时文件清理完成")

            signalBus.resource_exist.emit(True)
            signalBus.update_download_finished.emit(
                {
                    "status": "success",
                    "msg": self.tr("update success")
                    + "\n"
                    + mirror_data.get("data", {}).get("release_note", ""),
                }
            )
            return True

        except KeyError as e:
            logger.exception(f"数据字段缺失: {str(e)}")
            signalBus.update_download_finished.emit(
                {"status": "failed_info", "msg": self.tr("incomplete update data")}
            )
        except Exception as e:
            logger.exception(f"未预期的错误: {str(e)}")
            signalBus.update_download_finished.emit(
                {
                    "status": "failed_info",
                    "msg": self.tr("unexpected error during update"),
                }
            )
            return False

    def github_download(self, update_dict: Dict):
        """github下载更新"""
        version_data = self.read_version()
        if version_data:
            os_type = version_data.get("os")
            arch = version_data.get("arch")
            version = version_data.get("version", "v0.0.1")
        else:
            raise ValueError(self.tr("update failed: version_data is None"))

        self.stop_flag = False
        download_url = None
        try:
            # 下载过程
            if maa_config_data.interface_config.get("agent", False):
                project_name_number = 4
                signalBus.update_download_finished.emit(
                    {
                        "status": "info",
                        "msg": self.tr("Updating the Agent may take a long time."),
                    }
                )
                for release in update_dict["assets"]:
                    if os_type in release["name"] and arch in release["name"]:
                        download_url = release["browser_download_url"]
                        logger.info(f"找到下载更新包: {download_url}")
                        break
            else:
                project_name_number = 5
                if update_dict.get("status"):
                    signalBus.update_download_finished.emit(update_dict)
                    return
                download_url = update_dict["zipball_url"]
            if not download_url:
                logger.warning("未找到匹配的资源")
                signalBus.update_download_finished.emit(
                    {
                        "status": "failed",
                        "msg": self.tr("No matching resource found"),
                    }
                )
                return
            logger.info(f"开始下载更新包: {download_url}")

            hotfix_directory = os.path.join(os.getcwd(), "hotfix")
            os.makedirs(hotfix_directory, exist_ok=True)
            logger.debug(f"创建临时目录: {hotfix_directory}")

            project_name = download_url.split("/")[project_name_number]
            zip_file_path = os.path.join(
                hotfix_directory, f"{project_name}-{update_dict['tag_name']}.zip"
            )
            logger.debug(f"压缩文件保存路径: {zip_file_path}")

            if not self.download_file(
                download_url,
                zip_file_path,
                signalBus.update_download_progress,
                use_proxies=True,
            ):
                logger.error("下载更新包失败")
                signalBus.update_download_finished.emit(
                    {"status": "failed", "msg": self.tr("Download failed")}
                )
                return

            # 解压过程
            logger.info("开始解压更新包")
            main_folder = self.extract_zip(
                zip_file_path, os.path.join(os.getcwd(), "hotfix")
            )
            if not main_folder:
                logger.error("解压失败，未找到主目录")
                signalBus.update_download_finished.emit(
                    {"status": "failed", "msg": self.tr("Extraction failed")}
                )
                return
            if maa_config_data.interface_config.get("agent", False):
                # 修正路径处理：代理包直接解压到hotfix目录
                main_folder = os.path.join(os.getcwd(), "hotfix")
                files_to_keep = [
                    "python",
                    "resource",
                    "interface.json",
                    "custom",
                    "agent",
                    "requirements.txt",
                ]

                # 添加路径有效性检查
                if not os.path.isdir(main_folder):
                    logger.error(f"无效的目录路径: {main_folder}")
                    return

                for item in os.listdir(main_folder):
                    item_path = os.path.join(main_folder, item)
                    # 添加路径类型检查
                    if os.path.isfile(item_path) and item not in files_to_keep:
                        os.remove(item_path)
                    elif os.path.isdir(item_path) and item not in files_to_keep:
                        shutil.rmtree(item_path)
                folder_to_extract = main_folder

            else:
                folder_to_extract = os.path.join(
                    os.getcwd(), "hotfix", main_folder, "assets"
                )
            logger.debug(f"资源解压路径: {folder_to_extract}")

            # 版本兼容性检查
            interface_file = os.path.join(folder_to_extract, "interface.json")
            check_interface = Read_Config(interface_file).get(
                "MFW_min_req_version", "0.0.0.1"
            )
            logger.info(f"最低需求版本: {check_interface} | 当前版本: {version}")

            compare_result = self.compare_versions(check_interface, version)
            if compare_result == 1:
                logger.warning("当前版本过低，已中止更新")
                signalBus.update_download_finished.emit(
                    {
                        "status": "failed",
                        "msg": self.tr(
                            "Current MFW version is too low, update aborted"
                        ),
                    }
                )
                return

            # 清理旧资源
            target_path = maa_config_data.resource_path
            if os.path.exists(target_path):
                logger.info("开始清理旧资源")
                try:
                    if os.path.exists(os.path.join(target_path, "python")):
                        shutil.rmtree(os.path.join(target_path, "python"))
                        logger.debug("成功删除 python 目录")

                    if os.path.exists(os.path.join(target_path, "custom")):
                        shutil.rmtree(os.path.join(target_path, "custom"))
                        logger.debug("成功删除 custom 目录")

                    if os.path.exists(os.path.join(target_path, "agent")):
                        shutil.rmtree(os.path.join(target_path, "agent"))
                        logger.debug("成功删除 agent 目录")

                    shutil.rmtree(os.path.join(target_path, "resource"))
                    logger.debug("成功删除 resource 目录")

                    os.remove(os.path.join(target_path, "interface.json"))
                    logger.debug("成功删除 interface.json")

                except Exception as e:
                    logger.error(f"清理旧资源失败: {str(e)}")
                    signalBus.update_download_finished.emit(
                        {"status": "failed", "msg": self.tr("Clean up failed")}
                    )
                    return

            # 移动新文件
            logger.info(f"开始移动文件到目标路径: {target_path}")
            if not self.move_files(folder_to_extract, target_path):
                logger.error(f"文件移动失败: {folder_to_extract} -> {target_path}")
                signalBus.update_download_finished.emit(
                    {"status": "failed", "msg": self.tr("Move file failed")}
                )
                return

            # 更新配置
            replace_ocr(target_path)
            logger.info("更新接口配置版本号")
            interface_date = Read_Config(maa_config_data.interface_config_path)
            interface_date["version"] = update_dict["tag_name"]
            Save_Config(maa_config_data.interface_config_path, interface_date)

            # 清理临时文件
            logger.debug("清理临时文件")
            self.remove_temp_files(os.path.join(os.getcwd(), "hotfix"))

            logger.info("更新流程完成")
            signalBus.resource_exist.emit(True)
            signalBus.update_download_finished.emit(
                {
                    "status": "success",
                    "msg": self.tr("update success")
                    + "\n"
                    + str(update_dict.get("body", "")),
                }
            )
        # 网络错误
        except requests.exceptions.RequestException as e:
            logger.exception(f"GitHub请求失败: {str(e)}")
            signalBus.update_download_finished.emit(
                {
                    "status": "failed",
                    "msg": f"{self.tr("GitHub request failed")}\n{self.tr("HTTP error") + str(e)}",
                }
            )
        except KeyError as e:
            logger.exception(f"关键数据缺失: {str(e)}")
            signalBus.update_download_finished.emit(
                {"status": "failed", "msg": self.tr("Incomplete update data")}
            )
        except Exception as e:
            logger.exception(f"未预期的错误: {str(e)}")
            signalBus.update_download_finished.emit(
                {"status": "failed", "msg": self.tr("Unexpected error during update")}
            )

    def stop(self):
        self.stop_flag = True


# endregion

# region github下载资源包


class DownloadBundle(Update):
    project_url = ""

    def run(self):
        self.stop_flag = False
        if not self.project_url:
            logger.warning("项目地址未配置，无法进行更新检查")
            signalBus.download_finished.emit(
                {"status": "failed", "msg": self.tr("Project URL not configured")}
            )
            return

        url = for_config_get_url(self.project_url, "download")
        if os.path.exists("NO_SSL"):
            verify = False
            logger.debug("检测到NO_SSL文件，跳过SSL验证")
        else:
            verify = True
        proxies = self.get_proxy_data()

        try:
            if url is None:
                raise ValueError("URL is empty or invalid.")
            response = requests.get(url, verify=verify, timeout=10, proxies=proxies)
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
            download_url, zip_file_path, signalBus.bundle_download_progress,use_proxies = False
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
        if os.path.exists(target_path):
            shutil.rmtree(target_path)
        os.makedirs(target_path)

        folder_to_extract = os.path.join(os.getcwd(), "hotfix", main_folder, "assets")
        if not self.move_files(folder_to_extract, target_path):
            signalBus.download_finished.emit(
                {"status": "failed", "msg": self.tr("Move file failed")}
            )
            return
        LICENSE_path = os.path.join(os.getcwd(), "hotfix", main_folder, "LICENSE")
        # 移动文件
        if os.path.exists(LICENSE_path):
            shutil.move(LICENSE_path, target_path)
        interface_data = Read_Config(os.path.join(target_path, "interface.json"))
        interface_data["version"] = content["tag_name"]
        Save_Config(os.path.join(target_path, "interface.json"), interface_data)
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


# region 更新自身
class UpdateSelf(BaseUpdate):
    def run(self):
        version_data = self.read_version()
        if version_data:
            os_type = version_data.get("os")
            arch = version_data.get("arch")
            version = version_data.get("version", "v0.0.1")
        else:
            raise ValueError(self.tr("update failed: version_data is None"))
        channel = self.channel_map.get(cfg.get(cfg.MFW_update_channel))

        cdk = self.Mirror_ckd()
        if cdk:
            logger.debug(f"获取到CDK: {cdk[:4]}****")
        else:
            logger.warning("未获取到CDK")
            cdk = ""
        mirror_data: Dict[str, Dict] = self.mirror_check(
            res_id="MFW_PyQt6",
            cdk=cdk,
            version=version,
            os_type=os_type,
            channel=channel,
            arch=arch,
            update_type=1,
        )
        logger.debug(f"镜像检查结果: {mirror_data}")
        if mirror_data.get("status") == "failed_info":  # mirror检查失败
            signalBus.download_self_finished.emit(mirror_data)
            update_url = (
                f"https://api.github.com/repos/overflow65537/MFW-PyQt6/releases/latest"
            )
            github_dict = self.github_check(update_url, version)
            if (
                github_dict.get("status") == "failed"
                or github_dict.get("status") == "success"
                or github_dict.get("status") == "no_need"
            ):  # github检查失败:
                signalBus.download_self_finished.emit(github_dict)
                return
            try:
                download_url = None
                for i in github_dict.get("assets", {}) or []:
                    if not isinstance(i, dict):
                        logger.error(f"assets 内部不是字典: {github_dict}")
                        raise Exception("assets inside is not a dict")
                    if (
                        i.get("name")
                        == f"MFW-PyQt6-{os_type}-{arch}-{github_dict.get("tag_name")}.zip"
                    ):
                        download_url = i.get("browser_download_url")
                        break
                if not download_url:
                    logger.error(f"未找到下载地址: {github_dict}")
                    raise Exception("download url not found")
                logger.debug(f"github开始下载: {download_url}")
            except Exception as e:
                logger.exception(f"获取下载地址失败{e}")
                signalBus.download_self_finished.emit(
                    {
                        "status": "failed",
                        "msg": self.tr("Failed to get download address"),
                    }
                )
                return

            if not self._download(download_url, use_proxies=True):
                return
            try:
                tag_name = github_dict.get("tag_name")
                version_data["version"] = str(tag_name)
                Save_Config(
                    os.path.join(os.getcwd(), "config", "version.json"), version_data
                )
            except Exception as e:
                logger.exception("版本文件更新失败")
                signalBus.download_self_finished.emit(
                    {"status": "failed", "msg": self.tr("Version file update failed")}
                )
                return
        if mirror_data.get("code") != 0:
            logger.warning(f"更新检查失败: {mirror_data.get('msg')}")
            signalBus.download_self_finished.emit(
                {
                    "status": "failed",
                    "msg": str(mirror_data.get("msg", ""))
                    + "\n"
                    + self.tr("switching to Github download"),
                }
            )
            return

        elif mirror_data.get("data", {}).get("version_name") == version:
            logger.warning(f"当前版本已是最新版本")
            signalBus.download_self_finished.emit(
                {"status": "no_need", "msg": self.tr("current version is latest")}
            )
            return
        elif mirror_data.get("data", {}).get("url"):
            logger.info(f"开始镜像下载: {mirror_data['data']['url']}")
            signalBus.download_self_finished.emit(
                {
                    "status": "info",
                    "msg": self.tr(
                        "MirrorChyan update check successful, starting download"
                    ),
                }
            )

            try:
                if not self._download(mirror_data["data"]["url"], use_proxies=False):
                    logger.error("镜像下载失败")
                    return
            except Exception as e:
                logger.exception("镜像下载过程中发生未预期错误")
                signalBus.download_self_finished.emit(
                    {
                        "status": "failed",
                        "msg": self.tr("Unexpected error during download"),
                    }
                )
                return

            version_name = mirror_data["data"].get("version_name", "")
            version_data["version"] = version_name
            Save_Config(
                os.path.join(os.getcwd(), "config", "version.json"), version_data
            )
            try:
                version_file_path = os.path.join(os.getcwd(), "config", "version.txt")
                with open(version_file_path, "w", encoding="utf-8") as f:
                    f.write(" ".join(version_data))
                    logger.info(f"版本文件更新成功: {version_data}")
            except IOError as e:
                logger.error(f"版本文件写入失败: {str(e)}")
                signalBus.download_self_finished.emit(
                    {"status": "failed", "msg": self.tr("Version file write failed")}
                )
                return
            return
        else:
            logger.warning("镜像检查成功但未找到CDK，切换到GitHub下载")
            signalBus.download_self_finished.emit(
                {
                    "status": "info",
                    "msg": self.tr(
                        "MirrorChyan update check successful, but no CDK found, switching to Github download"
                    ),
                }
            )

            try:
                target_version = mirror_data["data"].get(
                    "version_name", "default_version"
                )
                github_url = self.assemble_gitHub_url(version_data, target_version)
                logger.debug(f"GitHub下载地址: {github_url}")

                if not self._download(github_url,use_proxies = False):
                    logger.error("GitHub下载失败")
                    return
            except KeyError as e:
                logger.error(f"构造GitHub URL参数缺失: {str(e)}")
                signalBus.download_self_finished.emit(
                    {
                        "status": "failed",
                        "msg": self.tr("GitHub URL construction failed"),
                    }
                )
                return

            version_name = mirror_data["data"].get("version_name", "")
            version_data["version"] = str(version_name)
            try:
                Save_Config(
                    os.path.join(os.getcwd(), "config", "version.json"), version_data
                )
            except Exception as e:
                logger.exception("版本文件更新失败")
                signalBus.download_self_finished.emit(
                    {"status": "failed", "msg": self.tr("Version file update failed")}
                )
            return

    def assemble_gitHub_url(self, version_data: dict, target_version: str) -> str:
        """
        输入版本号和项目地址，返回GitHub项目源代码压缩包下载地址
        """
        url = f"https://github.com/overflow65537/MFW-PyQt6/releases/download/{target_version}/MFW-PyQt6-{version_data["os"]}-{version_data["arch"]}-{target_version}.zip"
        return url

    def _download(self, download_url, use_proxies):

        self.stop_flag = False

        zip_file_path = os.path.join(os.getcwd(), "update.zip")
        if not self.download_file(
            download_url,
            zip_file_path,
            signalBus.download_self_progress,
            use_proxies=use_proxies,
        ):
            signalBus.download_self_finished.emit(
                {
                    "status": "failed",
                    "msg": self.tr("Download failed"),
                }
            )
            return False

        signalBus.download_self_finished.emit({"status": "success"})
        return True

    def stop(self):
        self.stop_flag = True


# endregion
