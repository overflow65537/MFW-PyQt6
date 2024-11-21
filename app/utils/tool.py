import os
import json
import re
import subprocess
import platform

# import psutil
# import socket


def Read_Config(paths):
    # 打开json并传入MAA_data
    if os.path.exists(paths):
        with open(paths, "r", encoding="utf-8") as MAA_Config:
            MAA_data = json.load(MAA_Config)
            return MAA_data
    else:
        return False


def Save_Config(paths, data):
    # 打开json并写入data内数据

    directory = os.path.dirname(paths)

    # 创建所有必要的目录
    os.makedirs(directory, exist_ok=True)
    with open(paths, "w", encoding="utf-8") as MAA_Config:
        json.dump(data, MAA_Config, indent=4, ensure_ascii=False)


def gui_init(resource_Path, maa_pi_config_Path, interface_Path):
    if not os.path.exists(resource_Path):
        return False

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


def Get_Values_list2(path, key1):
    List = []
    for i in Read_Config(path)[key1]:
        List.append(i)
    return List


def Get_Values_list(path, key1):
    # 获取组件的初始参数
    if key1 == "controller":
        List = []
        for i in Read_Config(path)[key1]:
            if re.search(r"adb", i["name"], re.IGNORECASE) or re.search(
                r"win", i["name"], re.IGNORECASE
            ):
                List.append(f"{i["name"]}")
            else:
                List.append(f"{i["name"]}_{i['type']}")
        return List
    else:
        List = []
        for i in Read_Config(path)[key1]:
            List.append(i["name"])
        return List


def Get_Values_list_Option(path, key1):
    # 获取组件的初始参数
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


def Get_Task_List(target):
    # 输入option名称来输出一个包含所有该option中所有cases的name列表
    # 具体逻辑为 interface.json文件/option键/选项名称/cases键/键为空,所以通过len计算长度来选择最后一个/name键
    lists = []
    Task_Config = Read_Config(os.path.join(os.getcwd(), "interface.json"))["option"][
        target
    ]["cases"]
    Lens = len(Task_Config) - 1
    for i in range(Lens, -1, -1):
        lists.append(Task_Config[i]["name"])
    return lists


"""
def find_process_by_name(process_name):
    # 遍历所有程序找到指定程序
    for proc in psutil.process_iter(["name", "exe"]):
        if proc.info["name"].lower() == process_name.lower():
            # 如果一样返回可执行文件的绝对路径
            return proc.info["exe"]


def find_existing_file(info_dict):
    # 输入一个包含可执行文件的绝对路径和可能存在ADB的相对路径,输出ADB文件的绝对地路径
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

def check_port(port):
    port_result = []
    for p in port:
        p = int(p.rsplit(":", 1)[1])
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            # 尝试连接到127.0.0.1的指定端口
            result = s.connect_ex(("127.0.0.1", p))
            # 如果connect_ex返回0，表示连接成功，即端口开启
            if result == 0:
                port_result.append("127.0.0.1:" + str(p))
        except socket.error:
            pass
        finally:
            s.close()
    return port_result
"""


def check_path_for_keyword(path):
    keywords_list = ["MuMu", "BlueStacks", "LDPlayer", "Nox", "MEmu", "ADV"]
    for keyword in keywords_list:
        if keyword in path:
            return keyword
    return "emulator"


def check_adb_path(adb_data):
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


def get_gpu_info():
    # 获取显卡字典
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
                    gpu_info[id_num] = name.strip()

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
                    gpu_info[id_num] = " ".join(name)

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
                    gpu_info[id_num] = name

    except Exception as e:
        print(f"获取显卡信息时出错: {e}")

    return gpu_info


def find_key_by_value(data_dict, target_value):
    # 输入一个字典和目标值，返回字典中第一个键值等于目标值的键
    # 用来查找字典中某个值对应的键
    # 反向查找
    for key, value in data_dict.items():
        if value == target_value:
            return key
    return None


def access_nested_dict(data_dict, keys: list, value=None):
    # 输入一个字典，键列表，值（可选），返回字典中对应键的值
    # 用来读取嵌套字典的值
    # 也可以单纯的获取字典的值

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


def rewrite_contorller(data_dict, controller, mode, new_value=None):
    # 输入一个字典，控制器类型，模式，新值，返回修改后的字典
    # 用来获取interface文件中的操作模式和截图模式
    # 附带修改功能
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


def delete_contorller(data_dict, controller, mode):
    # 输入一个字典，控制器类型，模式，返回修改后的字典
    # 用来删除interface文件中的操作模式和截图模式
    # 恢复初始状态
    for i in range(len(data_dict["controller"])):
        if data_dict["controller"][i]["type"] == controller:
            if (
                not data_dict["controller"][i].get(controller.lower()) == {}
                or not data_dict["controller"][i].get(controller.lower()) is None
            ):
                print(data_dict["controller"][i][controller.lower()][mode])
                del data_dict["controller"][i][controller.lower()][mode]
                if data_dict["controller"][i].get(controller.lower()) == {}:
                    del data_dict["controller"][i][controller.lower()]

    return data_dict


def for_config_get_url(url, mode):
    # 输入一个url，模式，返回对应的链接
    # 提取github仓库的用户名和仓库名
    # 用来获取接口文件中的链接
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


def get_controller_type(select_value, interface_path):
    # 输入一个选择值，接口文件路径，返回控制器类型
    data = Read_Config(interface_path)
    for i in data["controller"]:
        if i["name"] == select_value:
            return i["type"]
    return None
