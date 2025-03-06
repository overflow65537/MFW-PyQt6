import re
import os
import importlib.util
from typing import List, Dict
import subprocess
import string
import random
import sys


from asyncify import asyncify
from maa.controller import AdbController, Win32Controller
from maa.tasker import Tasker, NotificationHandler
from maa.agent_client import AgentClient
from maa.resource import Resource
from maa.toolkit import Toolkit, AdbDevice, DesktopWindow
from maa.define import MaaAdbScreencapMethodEnum, MaaAdbInputMethodEnum

from ..common.signal_bus import signalBus
from ..utils.logger import logger
from ..common.maa_config_data import maa_config_data
from ..common.config import cfg
from ..utils.tool import Read_Config


class MaaFW:

    resource: Resource | None
    controller: AdbController | Win32Controller | None
    tasker: Tasker | None
    notification_handler: NotificationHandler | None
    agent: AgentClient | None

    def __init__(self):
        Toolkit.init_option("./")
        self.activate_resource = ""
        self.need_register_report = True
        self.resource = None
        self.controller = None
        self.tasker = None
        self.notification_handler = None
        self.agent = None

    def load_custom_objects(self, custom_dir):
        if not os.path.exists(custom_dir):
            logger.warning(f"自定义文件夹 {custom_dir} 不存在")
            return
        if not os.listdir(custom_dir):
            logger.warning(f"自定义文件夹 {custom_dir} 为空")
            return
        if os.path.exists(os.path.join(custom_dir, "custom.json")):
            logger.info("配置文件方案")
            custom_config: Dict[str, Dict] = Read_Config(
                os.path.join(custom_dir, "custom.json")
            )
            for custom_name, custom in custom_config.items():
                custom_type: str = custom.get("type")
                custom_class_name: str = custom.get("class")
                custom_file_path: str = custom.get("file_path")
                if "{custom_path}" in custom_file_path:
                    custom_file_path = custom_file_path.replace(
                        "{custom_path}", custom_dir
                    )

                if not all(
                    [custom_type, custom_name, custom_class_name, custom_file_path]
                ):
                    logger.warning(f"配置项 {custom} 缺少必要信息，跳过")
                    continue
                print(
                    f"custom_type: {custom_type}, custom_name: {custom_name}, custom_class_name: {custom_class_name}, custom_file_path: {custom_file_path}"
                )
                module_name = os.path.splitext(os.path.basename(custom_file_path))[0]
                # 动态导入模块
                spec = importlib.util.spec_from_file_location(
                    module_name, custom_file_path
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                print(f"模块 {module} 导入成功")

                # 获取类对象
                class_obj = getattr(module, custom_class_name)

                # 实例化类
                instance = class_obj()

                if custom_type == "action":
                    if self.resource.register_custom_action(custom_name, instance):
                        logger.info(f"加载自定义动作{custom_name}")
                        if self.need_register_report:
                            signalBus.custom_info.emit(
                                {"type": "action", "name": custom_name}
                            )
                elif custom_type == "recognition":
                    if self.resource.register_custom_recognition(custom_name, instance):
                        logger.info(f"加载自定义识别器{custom_name}")
                        if self.need_register_report:
                            signalBus.custom_info.emit(
                                {"type": "recognition", "name": custom_name}
                            )

        for module_type in ["action", "recognition"]:

            module_type_dir = os.path.join(custom_dir, module_type)
            if not os.path.exists(module_type_dir):
                logger.warning(f"{module_type} 文件夹不存在于 {custom_dir}")
                continue
            logger.info(f"文件夹方案{module_type}")
            for subdir in os.listdir(module_type_dir):
                subdir_path = os.path.join(module_type_dir, subdir)
                if os.path.isdir(subdir_path):
                    entry_file = os.path.join(subdir_path, "main.py")
                    if not os.path.exists(entry_file):
                        logger.warning(f"{subdir_path} 没有main.py")
                        continue  # 如果没有找到main.py，则跳过该子目录

                    try:

                        module_name = subdir  # 使用子目录名作为模块名
                        spec = importlib.util.spec_from_file_location(
                            module_name, entry_file
                        )
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)
                        if module_type == "action":
                            if self.resource.register_custom_action(
                                f"{module_name}", getattr(module, module_name)()
                            ):
                                logger.info(
                                    f"加载自定义动作{module_name},{getattr(module, module_name)()}"
                                )
                                if self.need_register_report:
                                    signalBus.custom_info.emit(
                                        {"type": "action", "name": module_name}
                                    )
                        elif module_type == "recognition":
                            if self.resource.register_custom_recognition(
                                f"{module_name}", getattr(module, module_name)()
                            ):
                                logger.info(f"加载自定义识别器{module_name}")
                                if self.need_register_report:
                                    signalBus.custom_info.emit(
                                        {"type": "recognition", "name": module_name}
                                    )
                    except Exception as e:
                        logger.error(f"加载自定义内容时发生错误{entry_file}: {e}")

    @staticmethod
    @asyncify
    def detect_adb() -> List[AdbDevice]:
        return Toolkit.find_adb_devices()

    @staticmethod
    @asyncify
    def detect_win32hwnd(window_regex: str) -> List[DesktopWindow]:
        windows = Toolkit.find_desktop_windows()
        result = []
        for win in windows:
            if not re.search(window_regex, win.window_name):
                continue

            result.append(win)

        return result

    @asyncify
    def connect_adb(
        self,
        adb_path: str,
        address: str,
        screencap_method: int,
        input_method: int,
        config: dict,
    ) -> bool:
        if screencap_method == 0:
            screencap_method = MaaAdbScreencapMethodEnum.Default
        if input_method == 0:
            input_method = MaaAdbInputMethodEnum.Default
        self.controller = AdbController(
            adb_path, address, screencap_method, input_method, config
        )
        connected = self.controller.post_connection().wait().succeeded
        if not connected:
            print(f"Failed to connect {adb_path} {address}")
            return False

        return True

    @asyncify
    def connect_win32hwnd(
        self, hwnd: int | str, screencap_method: int, input_method: int
    ) -> bool:
        if isinstance(hwnd, str):
            hwnd = int(hwnd, 16)
        if screencap_method == 0:
            screencap_method = 4  # DXGI_DesktopDup
        if input_method == 0:
            input_method = 1  # Seize

        self.controller = Win32Controller(
            hwnd, screencap_method=screencap_method, input_method=input_method  # type: ignore
        )
        connected = self.controller.post_connection().wait().succeeded
        if not connected:
            print(f"Failed to connect {hwnd}")
            return False

        return True

    @asyncify
    def load_resource(self, dir: str) -> bool:
        if not self.resource:
            self.resource = Resource()
        gpu_index = maa_config_data.config["gpu"]
        if gpu_index == -2:
            logger.debug("设置CPU推理")
            self.resource.use_cpu()
        elif gpu_index == -1:
            logger.debug("设置自动")
            self.resource.use_auto_ep()
        else:
            logger.debug(f"设置GPU推理: {gpu_index}")
            self.resource.use_directml(gpu_index)
        return self.resource.post_bundle(dir).wait().succeeded

    @asyncify
    def run_task(self, entry: str, pipeline_override: dict = {}) -> bool:
        if not self.tasker:
            self.tasker = Tasker(notification_handler=self.notification_handler)

        if not self.resource or not self.controller:
            print("Resource or Controller not initialized")
            return False

        self.tasker.bind(self.resource, self.controller)

        # 动态加载.py
        if self.activate_resource != maa_config_data.resource_name:
            self.need_register_report = True
        self.resource.clear_custom_recognition()
        self.resource.clear_custom_action()
        custom_dir = os.path.join(
            maa_config_data.resource_path,
            "custom",
        )
        try:
            self.load_custom_objects(custom_dir)
        except Exception as e:
            logger.error(f"加载自定义内容时发生错误: {e}")
        self.activate_resource = maa_config_data.resource_name
        self.need_register_report = False

        # agent加载
        if not self.agent:
            self.agent = AgentClient()

        agent_data = maa_config_data.interface_config.get("agent", {})
        if agent_data.get("child_exec", False) == sys.platform:
            for i in agent_data.get("child_args", []):
                if not self.agent_load(i):
                    logger.error("agent加载失败")
                    return False

        if not self.tasker.inited:
            print("Failed to init MaaFramework instance")
            return False
        self.tasker.set_save_draw(cfg.get(cfg.save_draw))
        return self.tasker.post_task(entry, pipeline_override).wait().succeeded

    def agent_load(self, child_args):

        self.agent.bind(self.resource)
        characters = string.ascii_letters + string.digits
        socket_id = "".join(random.choice(characters) for i in range(8))

        subprocess.Popen(
            [
                child_args,
                os.getenv("MAAFW_BINARY_PATH", os.getcwd()),
                socket_id,
            ],
        )
        logger.debug(
            f"agent启动: {child_args}\nMAA库地址{os.getenv("MAAFW_BINARY_PATH", os.getcwd())}\nsocket_id: {socket_id}"
        )

        if not self.agent.connect():
            logger.error("agent连接 失败")
            return False
        return True

    @asyncify
    def stop_task(self):
        if not self.tasker:
            return
        self.tasker.post_stop().wait()
        maafw.tasker = None
        maafw.agent.disconnect()
        maafw.agent = None


maafw = MaaFW()
