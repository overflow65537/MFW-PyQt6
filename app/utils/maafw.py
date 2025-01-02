import re
from asyncify import asyncify
import os
import importlib.util

from ..common.signal_bus import signalBus
from ..utils.logger import logger

from typing import List
from maa.controller import AdbController, Win32Controller
from maa.tasker import Tasker, NotificationHandler
from maa.resource import Resource
from maa.toolkit import Toolkit, AdbDevice, DesktopWindow
from maa.define import MaaAdbScreencapMethodEnum, MaaAdbInputMethodEnum


class MaaFW:

    resource: Resource | None
    controller: AdbController | Win32Controller | None
    tasker: Tasker | None
    notification_handler: NotificationHandler | None

    def __init__(self):
        Toolkit.init_option("./")

        self.resource = None
        self.controller = None
        self.tasker = None
        self.notification_handler = None
        self.load_custom_objects()

    def load_custom_objects(self):
        custom_dir = os.path.join(os.getcwd(), "custom")

        if not os.path.exists(custom_dir):
            return

        for subdir in os.listdir(custom_dir):
            subdir_path = os.path.join(custom_dir, subdir)
            if os.path.isdir(subdir_path):
                entry_file = os.path.join(subdir_path, "main.py")
                if not os.path.exists(entry_file):
                    logger.warning(f"{subdir_path} 没有main.py")
                    continue  # 如果没有找到main.py，则跳过该子目录

                try:
                    module_name = "_".join((subdir.split("_")[1:]))  # 提取程序名
                    module_type = subdir.split("_")[0]  # 提取类型（action或reg）
                    spec = importlib.util.spec_from_file_location(
                        module_name, entry_file
                    )
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    if module_type == "action":

                        if Toolkit.pi_register_custom_action(
                            f"{module_name.lower()}", getattr(module, module_name)()
                        ):
                            logger.info(f"加载自定义动作{module_name.lower()}")
                            signalBus.custom_info.emit(
                                {"type": "action", "name": module_name.lower()}
                            )
                    elif module_type == "recognition":

                        if Toolkit.pi_register_custom_recognition(
                            f"{module_name.lower()}", getattr(module, module_name)()
                        ):
                            logger.info(f"加载自定义识别器{module_name.lower()}")
                            signalBus.custom_info.emit(
                                {"type": "recognition", "name": module_name.lower()}
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
        connected = self.controller.post_connection().wait().succeeded()
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
        connected = self.controller.post_connection().wait().succeeded()
        if not connected:
            print(f"Failed to connect {hwnd}")
            return False

        return True

    @asyncify
    def load_resource(self, dir: str, reset: bool = False) -> bool:
        if not self.resource:
            self.resource = Resource()
        if reset:
            self.resource.clear()

        return self.resource.post_path(dir).wait().succeeded()

    @asyncify
    def run_task(self, entry: str, pipeline_override: dict = {}) -> bool:
        if not self.tasker:
            self.tasker = Tasker(notification_handler=self.notification_handler)

        if not self.resource or not self.controller:
            print("Resource or Controller not initialized")
            return False

        self.tasker.bind(self.resource, self.controller)
        if not self.tasker.inited:
            print("Failed to init MaaFramework instance")
            return False

        return self.tasker.post_pipeline(entry, pipeline_override).wait().succeeded()

    @asyncify
    def stop_task(self):
        if not self.tasker:
            return

        self.tasker.post_stop().wait()


maafw = MaaFW()
