import os
import json
import re
import subprocess
import platform
import psutil
import socket
import asyncio
import traceback
import functools
from typing import Any, Literal,Callable, TypeVar

from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtGui import QIcon
from app.utils.logger import logger

R = TypeVar('R')

def error_handler(func: Callable[..., R]) -> Callable[..., R]:
    """错误处理装饰器。"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> R:
        try:
            return func(*args, **kwargs)
        except:
            logger.exception(f"Error in {func.__name__}:\n")
            show_error_message()
            return None 
    return wrapper

def show_error_message():

    """显示错误信息的弹窗。"""
    traceback_info = traceback.format_exc()

    msg_box = QMessageBox()

    msg_box.setIcon(QMessageBox.Icon.Critical)  
    msg_box.setWindowTitle("ERROR")
    msg_box.setText(f"{str(traceback_info)}") 
    msg_box.setWindowIcon(QIcon("./icon/ERROR.png"))  
    msg_box.exec() 
@error_handler
def Read_Config(paths) -> dict:
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
        raise FileNotFoundError("Config file not found.")

def Save_Config(paths, data):
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

@error_handler
def gui_init(resource_Path, maa_pi_config_Path, interface_Path) ->  dict:
    """初始化GUI组件的配置信息。    

    Args:
        resource_Path (str): 资源文件路径。
        maa_pi_config_Path (str): MAA配置文件路径。
        interface_Path (str): 接口配置文件路径。

    Returns:
        dict : 如果所有路径都存在，返回初始化信息的字典；否则空字典。
    """
    if not os.path.exists(resource_Path):
        raise FileNotFoundError("Resource file not found.")

    elif (
        os.path.exists(resource_Path)
        and os.path.exists(maa_pi_config_Path)
        and os.path.exists(interface_Path)
    ):
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

def Get_Values_list2(path, key1) -> list:
    """获取指定键的值列表。

    Args:
        path (str): 配置文件路径。
        key1 (str): 要查询的键。

    Returns:
        list: 指定键的值列表。
    """
    List = []
    for i in Read_Config(path)[key1]:
        List.append(i)
    return List

def Get_Values_list(path, key1) -> list:
    """获取组件的初始参数。

    Args:
        path (str): 配置文件路径。
        key1 (str): 查询的键。

    Returns:
        list: 组件名称列表。
    """
    if key1 == "controller":
        List = []
        for i in Read_Config(path)[key1]:
            if re.search(r"adb", i["name"], re.IGNORECASE) or re.search(
                r"win", i["name"], re.IGNORECASE
            ):
                List.append(f"{i['name']}")
            else:
                List.append(f"{i['name']}_{i['type']}")
        return List
    else:
        List = []
        for i in Read_Config(path)[key1]:
            List.append(i["name"])
        return List

def Get_Values_list_Option(path, key1) -> list:
    """获取组件的初始参数，包括选项。

    Args:
        path (str): 配置文件路径。
        key1 (str): 查询的键。

    Returns:
        list: 组件及其选项列表。
    """
    List = []
    for i in Read_Config(path)[key1]:
        if i["option"] != []:
            Option_text = str(i["name"]) + " "
            Option_Lens = len(i["option"])
            for t in range(0, Option_Lens, 1):
                Option_text += str(i["option"][t]["value"]) + " "
            List.append(Option_text)
        else:
            List.append(i["name"])
    return List

def Get_Task_List(path, target) -> list:
    """根据选项名称获取所有case的name列表。

    Args:
        target (str): 选项名称。

    Returns:
        list: 包含所有case的name列表。
    """
    lists = []
    Task_Config = Read_Config(path)["option"][target]["cases"]
    Lens = len(Task_Config) - 1
    for i in range(Lens, -1, -1):
        lists.append(Task_Config[i]["name"])
    return lists

def find_process_by_name(process_name) -> str | None:
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

def find_existing_file(info_dict) -> str | Literal[False]:
    """根据给出的路径信息查找可执行文件。

    Args:
        info_dict (dict): 包含可执行文件路径和可能存在的ADB相对路径信息的字典。

    Returns:
        str or False: 若找到则返回ADB文件的绝对路径，否则返回False。
    """
    exe_path = info_dict.get("exe_path").rsplit(os.sep, 1)[0]
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


async def check_port(port) -> list:
    """检查指定端口是否打开。

    Args:
        port (list): 端口列表。

    Returns:
        list: 打开的端口列表。
    """
    port_result = []

    async def check_single_port(p):
        p = int(p.rsplit(":", 1)[1])
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            # 尝试连接到127.0.0.1的指定端口
            result = await asyncio.get_event_loop().run_in_executor(
                None, s.connect_ex, ("127.0.0.1", p)
            )
            # 如果connect_ex返回0，表示连接成功，即端口开启
            if result == 0:
                port_result.append("127.0.0.1:" + str(p))
        except socket.error:
            pass
        finally:
            s.close()

    # 创建任务列表
    tasks = [check_single_port(p) for p in port]
    await asyncio.gather(*tasks)  # 等待所有任务完成
    return port_result


def check_path_for_keyword(path) -> str:
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


def check_adb_path(adb_data) -> bool:
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


def get_gpu_info() -> dict:
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


def find_key_by_value(data_dict, target_value) -> str | None:
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


def access_nested_dict(data_dict, keys: list, value=None) -> str | dict | None:
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

@error_handler
def rewrite_contorller(data_dict, controller, mode, new_value=None) -> str | dict:
    """重写控制器配置。

    Args:
        data_dict (dict): 要更新的字典。
        controller (str): 控制器名称。
        mode (str): 模式名称。
        new_value (optional): 新值，用于更新。

    Returns:
        dict or current_level: 如果提供了新值，则返回更新后的字典，否则返回当前模式的值。
    """
    current_level = {}

    for i in range(len(data_dict["controller"])):
        if data_dict["controller"][i]["type"] == controller:
            if data_dict["controller"][i].get(controller.lower()) is not None:
                current_level = data_dict["controller"][i][controller.lower()].get(mode)

            if new_value is not None:
                if not data_dict["controller"][i].get(controller.lower(), False):
                    data_dict["controller"][i][controller.lower()] = {}

                data_dict["controller"][i][controller.lower()][mode] = new_value
    if new_value is not None:
        return data_dict
    else:
        return current_level

@error_handler
def delete_contorller(data_dict, controller, mode) -> dict:
    """删除控制器配置。

    Args:
        data_dict (dict): 要更新的字典。
        controller (str): 控制器名称。
        mode (str): 模式名称。

    Returns:
        dict: 更新后的字典。
    """
    for i in range(len(data_dict["controller"])):
        if data_dict["controller"][i]["type"] == controller:
            if (
                not data_dict["controller"][i].get(controller.lower()) == {}
                or not data_dict["controller"][i].get(controller.lower()) is None
            ):
                logger.info(data_dict["controller"][i][controller.lower()][mode])
                del data_dict["controller"][i][controller.lower()][mode]
                if data_dict["controller"][i].get(controller.lower()) == {}:
                    del data_dict["controller"][i][controller.lower()]

    return data_dict


def for_config_get_url(url, mode) -> str:
    """根据给定的URL和模式返回相应的链接。

    Args:
        url (str): GitHub项目的URL。
        mode (str): 模式（"issue"或"download"）。

    Returns:
        str: 对应的链接。
    """
    parts = url.split("/")
    username = parts[3]
    repository = parts[4]

    if mode == "issue":
        return_url = f"https://github.com/{username}/{repository}/issues"
        return return_url
    elif mode == "download":
        return_url = (
            f"https://api.github.com/repos/{username}/{repository}/releases/latest"
        )
        return return_url


def get_controller_type(select_value, interface_path) -> str | None:
    """获取控制器类型。

    Args:
        select_value (str): 选择的控制器名称。
        interface_path (str): 接口配置文件路径。

    Returns:
        str or None: 控制器类型，如果未找到则返回None。
    """
    data = Read_Config(interface_path)
    for i in data["controller"]:
        if i["name"] == select_value or i["name"] == select_value[:-4]:
            return i["type"]
    return None
