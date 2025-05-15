import re
import os
import importlib.util
from typing import List, Dict
import subprocess

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
from ..utils.process_thread import ProcessThread


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
        self.agent_thread = None

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
            signalBus.custom_info.emit({"type": "error_r"})
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
        agent_data: dict = maa_config_data.interface_config.get("agent", {})
        if agent_data and agent_data.get("child_exec") and not self.agent:
            self.agent = AgentClient()
            self.agent.bind(self.resource)
            socket_id = self.agent.identifier
            signalBus.custom_info.emit({"type": "agent_start"})
            print("agent启动")
            try:

                maa_bin = os.getenv("MAAFW_BINARY_PATH")
                if not maa_bin:
                    maa_bin = os.getcwd()

                child_exec = agent_data.get("child_exec").replace(
                    "{PROJECT_DIR}", maa_config_data.resource_path
                )
                child_args = agent_data.get("child_args", [])

                for i in range(len(child_args)):
                    if "{PROJECT_DIR}" in child_args[i]:
                        child_args[i] = child_args[i].replace(
                            "{PROJECT_DIR}", maa_config_data.resource_path
                        )
                print(
                    f"agent启动: {child_exec}\n参数{child_args}\nMAA库地址{maa_bin}\nsocket_id: {socket_id}"
                )

                if cfg.get(cfg.show_agent_cmd):
                    subprocess.Popen(
                        [
                            child_exec,
                            *child_args,
                            maa_bin,
                            socket_id,
                        ],
                    )
                else:
                    self.agent_thread = ProcessThread(
                        child_exec, [*child_args, maa_bin, socket_id]
                    )
                    self.agent_thread.start()
                logger.debug(
                    f"agent启动: {agent_data.get("child_exec").replace("{PROJECT_DIR}", maa_config_data.resource_path)}\nMAA库地址{maa_bin}\nsocket_id: {socket_id}"
                )

            except Exception as e:
                logger.error(f"agent启动失败: {e}")
                signalBus.custom_info.emit({"type": "error_a"})
            if not self.agent.connect():
                logger.error(f"agent连接失败")
                signalBus.custom_info.emit({"type": "error_c"})
            print("cusotm加载完毕 ")
        if not self.tasker.inited:
            signalBus.custom_info.emit({"type": "error_t"})
            return False
        self.tasker.set_save_draw(cfg.get(cfg.save_draw))
        self.tasker.set_recording(cfg.get(cfg.recording))
        self.tasker.set_show_hit_draw(cfg.get(cfg.show_hit_draw))
        return self.tasker.post_task(entry, pipeline_override).wait().succeeded

    @asyncify
    def stop_task(self):
        if self.tasker:
            self.tasker.post_stop().wait()
            print("任务停止")
            self.tasker = None
        if self.agent:
            self.agent.disconnect()
            print("agent断开连接")
            self.agent = None
        if self.agent_thread:
            self.agent_thread.stop()
            self.agent_thread = None


maafw = MaaFW()
