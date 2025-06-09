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
MFW-ChainFlow Assistant 工具
作者:overflow65537
"""

import os
import json
import re
import subprocess
import sys
import platform
import psutil
import socket
import asyncio
import traceback
import shutil
import uuid
from typing import Literal, Optional, List, Dict, Any
from cryptography.fernet import Fernet
import base64
import logging
from datetime import datetime, timedelta
from maa.notification_handler import NotificationHandler, NotificationType
from PySide6.QtCore import QThread
from PySide6.QtWidgets import QMessageBox
from PySide6.QtGui import QIcon
from app.utils.logger import logger
from ..common.signal_bus import signalBus


def replace_ocr(path):
    """替换OCR模型"""
    bundle_dir1 = os.path.join(path, "resource", "base", "model", "ocr")
    bundle_dir2 = os.path.join(path, "resource", "model", "ocr")
    main_ocr_path = os.path.join(os.getcwd(), "MFW_resource", "model", "ocr")
    if os.path.exists(os.path.dirname(bundle_dir1)):
        if not os.path.exists(bundle_dir1):
            logger.info("正在替换OCR模型旧模板...")
            shutil.copytree(main_ocr_path, bundle_dir1, dirs_exist_ok=True)
    elif os.path.exists(os.path.dirname(bundle_dir2)):
        if not os.path.exists(bundle_dir2):
            logger.info("正在替换OCR模型新模板...")
            shutil.copytree(main_ocr_path, bundle_dir2, dirs_exist_ok=True)


def show_error_message():
    """显示错误信息的弹窗。"""
    traceback_info = traceback.format_exc()

    msg_box = QMessageBox()

    msg_box.setIcon(QMessageBox.Icon.Critical)
    msg_box.setWindowTitle("ERROR")
    msg_box.setText(f"{str(traceback_info)}")
    msg_box.setWindowIcon(QIcon("./MFW_resource/icon/ERROR.png"))
    msg_box.exec()


def Read_Config(paths: str) -> Dict:
    """读取指定路径的JSON配置文件。

    Args:
        paths (str): 配置文件的路径。

    Returns:
        dict: 如果文件存在，返回解析后的字典

    """

    if os.path.exists(paths):
        with open(paths, "r", encoding="utf-8") as MAA_Config:
            MAA_data = json.load(MAA_Config)
            return MAA_data
    else:
        return {}


def Save_Config(paths: str, data):
    """将数据保存到指定路径的JSON配置文件。

    Args:
        paths (str): 配置文件的路径。
        data (dict): 要保存的数据。
    """
    directory = os.path.dirname(paths)

    # 创建所有必要的目录
    os.makedirs(directory, exist_ok=True)
    with open(paths, "w", encoding="utf-8") as MAA_Config:
        json.dump(data, MAA_Config, indent=4, ensure_ascii=False)


def gui_init(
    resource_Path: str, maa_pi_config_Path: str, interface_Path: str
) -> Dict[str, int]:
    """初始化GUI组件的配置信息。

    Args:
        resource_Path (str): 资源文件路径。
        maa_pi_config_Path (str): MAA配置文件路径。
        interface_Path (str): 接口配置文件路径。

    Returns:
        dict : 如果所有路径都存在，返回初始化信息的字典；否则返回空字典。
    """
    if not os.path.exists(resource_Path):
        # 若资源文件不存在，抛出异常不符合文档描述，改为返回空字典
        return {}

    if not os.path.exists(maa_pi_config_Path) or not os.path.exists(interface_Path):
        # 若其他文件不存在，返回空字典
        return {}

    # 获取初始resource序号
    Resource_count = 0
    Add_Resource_Type_Select_Values = []
    for a in Read_Config(interface_Path)["resource"]:
        Add_Resource_Type_Select_Values.append(a["name"])
    Resource_Type = Read_Config(maa_pi_config_Path)["resource"]
    if Resource_Type != "":
        for b in Add_Resource_Type_Select_Values:
            if b == Resource_Type:
                break
            else:
                Resource_count += 1

    # 获取初始Controller序号
    Controller_count = 0
    Add_Controller_Type_Select_Values = []
    for c in Read_Config(interface_Path)["controller"]:
        Add_Controller_Type_Select_Values.append(c["name"])
    Controller_Type = Read_Config(maa_pi_config_Path)["controller"]["name"]

    if Controller_Type != "":
        for d in Add_Controller_Type_Select_Values:
            if d == Controller_Type:
                break
            else:
                Controller_count += 1

    # 初始显示
    init_ADB_Path = Read_Config(maa_pi_config_Path)["adb"]["adb_path"]
    init_ADB_Address = Read_Config(maa_pi_config_Path)["adb"]["address"]
    init_Resource_Type = Resource_count
    init_Controller_Type = Controller_count
    return_init = {
        "init_ADB_Path": init_ADB_Path,
        "init_ADB_Address": init_ADB_Address,
        "init_Resource_Type": init_Resource_Type,
        "init_Controller_Type": init_Controller_Type,
    }
    return return_init


def Get_Values_list2(path: str, key1: str) -> List:
    """获取指定键的值列表。

    Args:
        path (str): 配置文件路径。
        key1 (str): 要查询的键。

    Returns:
        list: 指定键的值列表。
    """
    List = []
    data = Read_Config(path)[key1]
    if not data:
        return []
    for i in data:
        List.append(i)
    return List


def Get_Values_list(path: str, key1: str, sp: bool = False) -> List:
    """获取组件的初始参数。

    Args:
        path (str): 配置文件路径。
        key1 (str): 查询的键。

    Returns:
        list: 组件名称列表。
    """
    if key1 == "controller":
        List = []
        data = Read_Config(path)[key1]
        if not data:
            return []
        for i in data:
            if re.search(r"adb", i["name"], re.IGNORECASE) or re.search(
                r"win", i["name"], re.IGNORECASE
            ):
                List.append(f"{i['name']}")
            else:
                List.append(f"{i['name']}_{i['type']}")
        return List
    else:
        List = []
        data = Read_Config(path)[key1]
        if not data:
            return []
        for i in data:
            if sp:
                if not i.get("spt"):
                    List.append(i["name"])
            else:
                List.append(i["name"])
        return List


def Get_Values_list_Option(path: str, key1: str) -> List:
    """获取组件的初始参数，包括选项。

    Args:
        path (str): 配置文件路径。
        key1 (str): 查询的键。

    Returns:
        list: 组件及其选项列表。
    """
    List = []
    data = Read_Config(path)[key1]

    for i in data:
        if i["option"] != []:
            Option_text = str(i["name"]) + " "
            Option_Lens = len(i["option"])
            for t in range(0, Option_Lens, 1):
                Option_text += str(i["option"][t]["value"]) + " "
            List.append(Option_text)
        else:
            List.append(i["name"])
    return List


def Get_Task_List(path: str, target: str) -> List:
    """根据选项名称获取所有case的name列表。

    Args:
        path (str): 配置文件路径。
        target (str): 选项名称。

    Returns:
        list: 包含所有case的name列表。
    """
    lists = []
    Task_Config = Read_Config(path)["option"][target]["cases"]
    if not Task_Config:
        return []
    Lens = len(Task_Config) - 1
    for i in range(Lens, -1, -1):
        lists.append(Task_Config[i]["name"])
    lists.reverse()
    return lists

def Get_Task_advanced_List(path: str, target: str) -> List[List[Any]]|None:
    """根据选项名称获取所有advanced的default列表，并处理不同数据类型格式。

    Args:
        path (str): 配置文件路径。
        target (str): 选项名称。

    Returns:
        List[List[Any]]: 格式化后的选项列表，结构为二维列表：
                        - 字符串 → [[value]]（单选项单字段）
                        - 列表 → [[value1], [value2], ...]（多选项单字段）
                        - 列表的列表 → [[v1, v2], [v3, v4], ...]（多选项多字段）
    """
    advanced_option = Read_Config(path)["advanced"].get(target, {})
    if not advanced_option:
        return None
    
    advanced_Config = advanced_option.get("default")

    if not advanced_Config:
        return None
    elif isinstance(advanced_Config, str):
        # "str"
        return [[advanced_Config]]
    elif isinstance(advanced_Config, list):
        advanced_field = advanced_option.get("field")
        if not advanced_field:
            return None
        elif isinstance(advanced_field, str) or isinstance(advanced_field, list) and len(advanced_field)==1:
            # ["str", "str", "str"]
            return_list = []
            for item in advanced_Config:
                return_list.append([item])
            return return_list
                
        elif isinstance(advanced_field, list):
            if isinstance(advanced_Config[0], list):
                # [["str1", "str2"], ["str3", "str4"]]
                return advanced_Config  # 直接返回多字段的列表
            else:
                # ["str1", "str2", "str3"]
                return [advanced_Config]  # 处理单字段的列表
            
            


    return None


def find_process_by_name(process_name: str) -> Optional[str]:
    """查找指定名称的进程，并返回其可执行文件的路径。

    Args:
        process_name (str): 进程名称。

    Returns:
        str or None: 进程的可执行文件路径，如果未找到则返回None。
    """
    for proc in psutil.process_iter(["name", "exe"]):
        if proc.info["name"].lower() == process_name.lower():
            # 如果一样返回可执行文件的绝对路径
            return proc.info["exe"]
    return None


def find_existing_file(info_dict: Dict[str, str]) -> str | Literal[False]:
    """根据给出的路径信息查找可执行文件。

    Args:
        info_dict (dict): 包含可执行文件路径和可能存在的ADB相对路径信息的字典。

    Returns:
        str or False: 若找到则返回ADB文件的绝对路径，否则返回False。
    """
    exe_path = info_dict.get("exe_path", "").rsplit(os.sep, 1)[0]
    may_paths = info_dict.get("may_path", [])
    if not exe_path or not may_paths:
        return False

    # 遍历所有可能的相对路径
    for path in may_paths:
        # 拼接完整路径
        full_path = os.path.join(exe_path, path)
        # 检查文件是否存在
        if os.path.exists(full_path):
            return full_path

    # 如果没有找到任何存在的文件
    return False


async def check_port(port: List[str]) -> List[str]:
    """检查指定端口是否打开。

    Args:
        port (list): 端口列表。

    Returns:
        list: 打开的端口列表。
    """
    port_result = []

    async def check_single_port(p: str):
        port: int = int(p.rsplit(":", 1)[1])
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            # 尝试连接到127.0.0.1的指定端口
            result = await asyncio.get_event_loop().run_in_executor(
                None, s.connect_ex, ("127.0.0.1", port)
            )
            # 如果connect_ex返回0，表示连接成功，即端口开启
            if result == 0:
                port_result.append("127.0.0.1:" + str(port))
        except socket.error:
            pass
        finally:
            s.close()

    # 创建任务列表
    tasks = [check_single_port(p) for p in port]
    await asyncio.gather(*tasks)  # 等待所有任务完成
    return port_result


def check_path_for_keyword(path: str) -> str:
    """检查路径字符串是否包含指定的关键字。

    Args:
        path (str): 要检查的路径。

    Returns:
        str: 如果找到关键字，返回对应的模拟器名称；否则返回"unknown device"。
    """
    keywords_list = ["MuMu", "BlueStacks", "LDPlayer", "Nox", "MEmu", "ADV"]
    for keyword in keywords_list:
        if keyword in path:
            return keyword
    return "unknown device"


def check_adb_path(adb_data: Dict) -> bool:
    """检查ADB路径和地址是否有效。

    Args:
        adb_data (dict): 包含ADB信息的字典。

    Returns:
        bool: 如果路径或地址无效，返回True；否则返回False。
    """
    if (
        adb_data["adb_path"] == ""  # 路径为空
        or adb_data["address"] == ""  # 地址为空
        or (
            ("adb" not in adb_data["adb_path"]) and ("ADB" not in adb_data["adb_path"])
        )  # 路径中不包含adb关键字
        or not re.match(
            r"^(\d{1,3}\.){3}\d{1,3}:\d{1,5}$", adb_data["address"]
        )  # 地址格式不正确
    ):
        return True  # 路径或地址不正确
    else:
        return False  # 路径或地址正确


def get_gpu_info() -> Dict[int, str]:
    """获取GPU相关信息。

    Returns:
        dict: GPU信息字典，其中键为索引，值为GPU名称。
    """
    gpu_info = {}
    try:
        os_type = platform.system()
        if os_type == "Windows":
            # Windows
            id_output = subprocess.check_output(
                "wmic path win32_VideoController get DeviceID", shell=True, text=True
            )
            name_output = subprocess.check_output(
                "wmic path win32_VideoController get Name", shell=True, text=True
            )
            ids = id_output.strip().split("\n")[1:]
            names = name_output.strip().split("\n")[1:]

            for id, name in zip(ids, names):
                if id and name:
                    # 使用ID作为键
                    id_num = int("".join(filter(str.isdigit, id)))
                    gpu_info[id_num - 1] = name.strip()

        elif os_type == "Linux":
            # Linux
            lspci_output = subprocess.check_output(
                "lspci | grep -i vga", shell=True, text=True
            )
            for index, line in enumerate(lspci_output.strip().split("\n")):
                parts = line.split(":")
                if len(parts) >= 2:
                    # 使用索引作为键
                    id_num = index
                    name = parts[1].strip().split(" ")[1:]
                    gpu_info[id_num - 1] = " ".join(name)

        elif os_type == "Darwin":
            # macOS
            sp_output = subprocess.check_output(
                "system_profiler SPGraphicsDataType", shell=True, text=True
            )
            for index, line in enumerate(sp_output.splitlines()):
                if "Chipset Model" in line:
                    # 使用索引作为键
                    id_num = index
                    name = line.split(":")[1].strip()
                    gpu_info[id_num - 1] = name

    except Exception as e:
        logger.info(f"获取显卡信息时出错: {e}")

    return gpu_info


def find_key_by_value(data_dict: Dict[str, Any], target_value: Any) -> Optional[str]:
    """根据目标值查找字典中的键。

    Args:
        data_dict (dict): 要查找的字典。
        target_value: 目标值。

    Returns:
        str or None: 如果找到，则返回对应的键；否则返回None。
    """
    for key, value in data_dict.items():
        if value == target_value:
            return key
    return None


def access_nested_dict(
    data_dict: Dict[str, Dict[str, Any]], keys: List[str], value: Any = None
) -> Any:
    """访问嵌套字典中的值。

    Args:
        data_dict (dict): 嵌套字典。
        keys (list): 访问的键列表。
        value (optional): 如果提供，将在指定位置设置键值。

    Returns:
        value: 返回指定路径的值，如果设置了值，则返回修改后的字典。
    """
    current_level = data_dict  # 从字典根部开始

    # 遍历到倒数第二个键（为下一个层级的父级）
    for key in keys[:-1]:
        current_level = current_level[key]  # 进入下一层级

    # 处理最后一个键
    last_key = keys[-1]
    if value is not None:
        # 如果提供了值，则修改最后一个键的值
        current_level[last_key] = value
        return current_level  # 返回最后一层的值
    else:
        # 如果没有提供值，则返回最后一个键的值
        try:
            return current_level[last_key]
        except KeyError:
            return None  # 键不存在时返回None


def rewrite_contorller(
    data_dict: Dict[str, List[Dict[str, Any]]],
    controller: str,
    mode: str,
    new_value: str | None = None,
) -> str | dict:
    """重写控制器配置。

    Args:
        data_dict (dict): 要更新的字典。
        controller (str): 控制器名称。
        mode (str): 模式名称。
        new_value (optional): 新值，用于更新。

    Returns:
        dict or current_level: 如果提供了新值，则返回更新后的字典，否则返回当前模式的值。
    """
    current_level: Dict = {}
    controller_list = data_dict.get("controller", [])
    if not isinstance(controller_list, list):
        logger.error("data_dict['controller'] 不是列表类型")
        return data_dict if new_value is not None else current_level

    for i in range(len(controller_list)):
        if controller_list[i]["type"] == controller:
            if controller_list[i].get(controller.lower()) is not None:
                current_level = controller_list[i][controller.lower()].get(mode)

            if new_value is not None:
                if not controller_list[i].get(controller.lower(), False):
                    controller_list[i][controller.lower()] = {}

                controller_list[i][controller.lower()][mode] = new_value
    if new_value is not None:
        return data_dict
    else:
        return current_level


def delete_contorller(
    data_dict: Dict[str, List[Dict[str, Any]]], controller: str, mode: str
) -> dict:
    """删除控制器配置。

    Args:
        data_dict (dict): 要更新的字典。
        controller (str): 控制器名称。
        mode (str): 模式名称。

    Returns:
        dict: 更新后的字典。
    """
    controller_list = data_dict.get("controller", [])
    if not isinstance(controller_list, list):
        logger.error("data_dict['controller'] 不是列表类型")
        return data_dict

    for i in range(len(controller_list)):
        if controller_list[i]["type"] == controller:
            if (
                controller_list[i].get(controller.lower()) is not None
                and controller_list[i].get(controller.lower()) != {}
            ):
                logger.info(controller_list[i][controller.lower()][mode])
                del controller_list[i][controller.lower()][mode]
                if controller_list[i].get(controller.lower()) == {}:
                    del controller_list[i][controller.lower()]

    return data_dict


def for_config_get_url(url: str, mode: str) -> str | None:
    """根据给定的URL和模式返回相应的链接。

    Args:
        url (str): GitHub项目的URL。
        mode (str): 模式（"issue"或"download"）。

    Returns:
        str: 对应的链接。
    """
    parts = url.split("/")
    try:
        username = parts[3]
        repository = parts[4]
    except IndexError:
        return None
    return_url = None
    if mode == "issue":
        return_url = f"https://github.com/{username}/{repository}/issues"
    elif mode == "download":
        return_url = (
            f"https://api.github.com/repos/{username}/{repository}/releases/latest"
        )
    return return_url


def get_controller_type(select_value: str, interface_path: str) -> str | None:
    """获取控制器类型。

    Args:
        select_value (str): 选择的控制器名称。
        interface_path (str): 接口配置文件路径。

    Returns:
        str or None: 控制器类型，如果未找到则返回None。
    """
    data = Read_Config(interface_path)
    if not data:
        return None
    for i in data["controller"]:
        if i["name"] == select_value or i["name"] == select_value[:-4]:
            return i["type"]
    return None


def get_console_path(path: str) -> dict[str, str] | None:
    """获取控制台路径。

    Args:
        path (str): 配置文件路径。

    Returns:
        str  控制台路径。
    """
    mumu = {
        "type": "mumu",
        "path": os.path.join(os.path.dirname(path), "MuMuManager.exe"),
    }
    LD_emu = {
        "type": "LD",
        "path": os.path.join(os.path.dirname(path), "dnconsole.exe"),
    }
    Nox = {
        "type": "Nox",
        "path": os.path.join(os.path.dirname(path), "NoxConsole.exe"),
    }
    MEmu = {
        "type": "MEmu",
        "path": os.path.join(os.path.dirname(path), "memuc.exe"),
    }
    BlueStacks = {
        "type": "BlueStacks",
        "path": os.path.join(os.path.dirname(path), "bsconsole.exe"),
    }
    if os.path.exists(mumu["path"]):
        logger.info(f"mumu控制台: {mumu}")
        return mumu
    elif os.path.exists(LD_emu["path"]):
        logger.info(f"LD控制台: {LD_emu}")
        return LD_emu
    elif os.path.exists(Nox["path"]):
        logger.info(f"Nox控制台: {Nox}")
        return Nox
    elif os.path.exists(MEmu["path"]):
        logger.info(f"MEmu控制台: {MEmu}")
        return MEmu
    elif os.path.exists(BlueStacks["path"]):
        logger.info(f"BlueStacks控制台: {BlueStacks}")
        return BlueStacks
    else:
        logger.info("未找到控制台")
        return None


def get_uuid():
    # 定义一个命名空间，例如使用DNS命名空间
    namespace = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")

    # 获取CPU序列号
    cpu_serial = get_cpu_serial()

    if cpu_serial:
        # 使用uuid5生成固定的UUID，基于CPU序列号
        device_id = uuid.uuid5(namespace, cpu_serial)
        # 输出UUID
        return device_id
    else:
        return False


def get_cpu_serial():
    system = platform.system()
    if system == "Windows":
        import wmi

        try:
            c = wmi.WMI()
            return c.Win32_Processor()[0].ProcessorId
        except Exception as e:
            print(f"Error getting CPU serial on Windows: {e}")
            return None
    elif system == "Linux":
        try:
            result = subprocess.check_output(
                "cat /proc/cpuinfo | grep serial | cut -d ' ' -f 2", shell=True
            )
            return result.decode("utf-8").strip()
        except Exception as e:
            print(f"Error getting CPU serial on Linux: {e}")
            return None
    elif system == "Darwin":
        try:
            result = subprocess.check_output(
                "ioreg -l | grep IOPlatformSerialNumber", shell=True
            )
            return result.decode("utf-8").split('"')[-2]
        except Exception as e:
            print(f"Error getting CPU serial on macOS: {e}")
            return None
    else:
        raise NotImplementedError(f"Unsupported operating system: {system}")


def encrypt(plain_text: str, key: bytes) -> str:
    """加密文本"""
    if not plain_text:
        return ""
    try:
        cipher_suite = Fernet(key)
        encrypted_data = cipher_suite.encrypt(plain_text.encode("utf-8"))
        return base64.urlsafe_b64encode(encrypted_data).decode("utf-8")
    except Exception as e:
        logging.error("Failed to encrypt text: " + str(e))
        return plain_text


def decrypt(encrypted_text: str, key: bytes) -> str:
    """解密文本"""
    if not encrypted_text:
        return ""
    try:
        cipher_suite = Fernet(key)
        encrypted_data = base64.urlsafe_b64decode(encrypted_text.encode("utf-8"))
        decrypted_data = cipher_suite.decrypt(encrypted_data)
        return decrypted_data.decode("utf-8")
    except Exception as e:
        logging.error("Failed to decrypt text: " + str(e))
        return encrypted_text


def is_task_run_today(last_run_time, refresh_hour):
    """
    检查任务是否在今天已经运行过，考虑每天的刷新时间（基于周检查逻辑重构）
    """
    current_time = datetime.now()

    if last_run_time is None:
        return False

    # 解析最后运行时间（保留原有异常处理）
    if isinstance(last_run_time, str):  # 尝试将字符串解析为datetime对象
        try:
            last_run_time = datetime.strptime(last_run_time, "%Y-%m-%d %H:%M:%S.%f")
        except ValueError:
            try:
                last_run_time = datetime.strptime(last_run_time, "%Y-%m-%d %H:%M:%S")
            except ValueError as e:
                print(f"时间解析失败: {str(e)}")
                return False

    # 计算当日刷新阈值时间
    threshold_time = current_time.replace(
        hour=refresh_hour, minute=0, second=0, microsecond=0
    )

    # 调整阈值逻辑（如果当前时间在刷新时间之前，则阈值时间向前推一天）
    if current_time < threshold_time:
        threshold_time -= timedelta(days=1)

    # 最终判断：最后运行时间 >= 阈值时间 且 当前时间 >= 阈值时间
    return last_run_time >= threshold_time and current_time >= threshold_time


def is_task_run_this_week(last_run_time, week_start_day=1, day_start_hour=0):
    """
    检查任务是否在本周已经运行过，考虑每周的开始日期和每天的开始时间。
    """

    week_start_day = int(week_start_day)
    py_weekday = (week_start_day - 1) % 7

    if isinstance(last_run_time, str):  # 尝试将字符串解析为datetime对象
        try:
            last_run_time = datetime.strptime(last_run_time, "%Y-%m-%d %H:%M:%S.%f")
        except ValueError:
            try:
                last_run_time = datetime.strptime(last_run_time, "%Y-%m-%d %H:%M:%S")
            except ValueError as e:
                print(f"时间解析失败: {str(e)}")
                return False

    current_time = datetime.now()

    if (current_time - last_run_time).days > 7:  # 超过一周，返回False
        return False

    days_to_next = (py_weekday - last_run_time.weekday()) % 7

    if days_to_next == 0:  # 生成前一个触发时间

        if (
            last_run_time.time() >= datetime.min.replace(hour=day_start_hour).time()
        ):  # 如果上次运行时间超过了指定的小时
            days_to_next = 7

    threshold_time = last_run_time + timedelta(days=days_to_next)
    threshold_time = threshold_time.replace(
        hour=day_start_hour, minute=0, second=0, microsecond=0
    )

    result = current_time <= threshold_time  # 比较当前时间和阈值时间

    return result


def path_to_list(path):
    """将路径转换为列表形式"""
    parts = []
    while True:
        path, part = os.path.split(path)
        if part:
            parts.insert(0, part)
        else:
            if path:
                parts.insert(0, path)
            break
    return parts


class MyNotificationHandler(NotificationHandler):

    def __init__(self, parent=None):
        self.callbackSignal = signalBus

    def on_controller_action(
        self,
        noti_type: NotificationType,
        detail: NotificationHandler.ControllerActionDetail,
    ):
        self.callbackSignal.callback.emit(
            {"name": "on_controller_action", "status": noti_type.value}
        )

    def on_tasker_task(
        self, noti_type: NotificationType, detail: NotificationHandler.TaskerTaskDetail
    ):

        self.callbackSignal.callback.emit(
            {"name": "on_tasker_task", "task": detail.entry, "status": noti_type.value}
        )

    def on_node_recognition(
        self,
        noti_type: NotificationType,
        detail: NotificationHandler.NodeRecognitionDetail,
    ):
        focus_mapping = {
            1: "start",
            2: "succeeded",
            3: "failed",
        }
        send_msg =  {
                "name": "on_task_recognition",
                "task": detail.name,
                "status": noti_type.value,
                "focus": detail.focus.get(focus_mapping[noti_type.value], ""),
            }
        if detail.focus.get("aborted"):
            send_msg["aborted"] = True
        self.callbackSignal.callback.emit(
           send_msg
        )


class ProcessThread(QThread):
    output_signal = signalBus.agent_info

    def __init__(self, command, args):
        super().__init__()
        self.command = command
        self.args = args
        self.process = None
        self._stop_flag = False  # 添加退出标志

    def run(self):
        startupinfo = None
        if sys.platform.startswith("win"):
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE

        try:
            self.process = subprocess.Popen(
                [self.command, *self.args],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="gbk",
                errors="replace",
                startupinfo=startupinfo,
            )

            while self.process.poll() is None and not self._stop_flag:
                assert (
                    self.process.stdout is not None
                ), "stdout 应为 PIPE，不可能为 None"
                output = self.process.stdout.readline()
                # 过滤ANSI码和时间戳
                clean_output = re.sub(
                    r"(\x1B\[[0-?]*[ -/]*[@-~])|(^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}[ \t]*)",
                    "",
                    output.strip(),
                )
                self.output_signal.emit(clean_output.strip())
        except Exception as e:
            print(f"线程运行出错: {e}")
        finally:
            if self.process and self.process.poll() is None:
                self.process.terminate()
                self.process.wait()

    def stop(self):
        self._stop_flag = True  # 设置退出标志
        if self.process and self.process.poll() is None:
            self.process.terminate()
            self.process.wait()
        self.quit()  # 请求线程退出
        self.wait()  # 等待线程退出
