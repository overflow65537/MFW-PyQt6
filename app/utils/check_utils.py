import os
import json
from typing import Dict
from cryptography.fernet import Fernet
from app.common.maa_config_data import maa_config_data, init_maa_config_data
from app.utils.tool import Save_Config, show_error_message
from app.common.config import cfg
from app.utils.logger import logger
from app.common.signal_bus import signalBus


def check(resource: str, config: str, directly: bool, DEV: bool):
    # 检查密钥文件是否存在
    try:
        if not os.path.exists("k.ey"):
            key = Fernet.generate_key()
            with open("k.ey", "wb") as key_file:
                key_file.write(key)
        # 检查资源文件是否存在
        maa_config_name: str = cfg.get(cfg.maa_config_name)
        maa_config_path: str = cfg.get(cfg.maa_config_path)
        maa_resource_name: str = cfg.get(cfg.maa_resource_name)
        maa_resource_path: str = cfg.get(cfg.maa_resource_path)
        maa_config_list: Dict[str, Dict[str, str]] = cfg.get(cfg.maa_config_list)
        maa_resource_list: Dict[str, str] = cfg.get(cfg.maa_resource_list)

        if (
            maa_config_name == ""
            or maa_config_path == ""
            or maa_resource_name == ""
            or maa_resource_path == ""
            or maa_config_list == {}
            or maa_resource_list == {}
        ):
            if os.path.exists("interface.json") and os.path.exists("resource"):
                logger.info("检测到配置文件,开始转换")

                with open("interface.json", "r", encoding="utf-8") as f:
                    interface_config: dict = json.load(f)
                cfg.set(cfg.maa_config_name, "default")
                cfg.set(cfg.maa_resource_name, interface_config.get("name", "resource"))
                bundle_path = os.path.join(
                    ".", "bundles", cfg.get(cfg.maa_resource_name)
                )
                if not os.path.exists(bundle_path):
                    os.makedirs(bundle_path)
                # 移动resource文件夹到bundle_path目录下
                os.rename("resource", os.path.join(bundle_path, "resource"))
                # 移动interface.json到bundle_path目录下
                os.rename("interface.json", os.path.join(bundle_path, "interface.json"))
                # 移动custom文件夹到bundle_path目录下
                if os.path.exists("custom"):
                    os.rename("custom", os.path.join(bundle_path, "custom"))
                # 移动LICENSE文件到bundle_path目录下
                if os.path.exists("LICENSE"):
                    os.rename("LICENSE", os.path.join(bundle_path, "LICENSE"))
                # 移动README.md文件到bundle_path目录下
                if os.path.exists("README.md"):
                    os.rename("README.md", os.path.join(bundle_path, "README.md"))
                # 移动agent文件夹到bundle_path目录下
                if os.path.exists("agent"):
                    os.rename("agent", os.path.join(bundle_path, "agent"))

                cfg.set(
                    cfg.maa_config_path,
                    os.path.join(
                        ".",
                        "config",
                        cfg.get(cfg.maa_resource_name),
                        "config",
                        cfg.get(cfg.maa_config_name),
                        "maa_pi_config.json",
                    ),
                )
                cfg.set(cfg.maa_resource_path, bundle_path)
                cfg.set(
                    cfg.maa_config_list,
                    {
                        cfg.get(cfg.maa_resource_name): {
                            cfg.get(cfg.maa_config_name): cfg.get(cfg.maa_config_path)
                        }
                    },
                )
                cfg.set(
                    cfg.maa_resource_list,
                    {cfg.get(cfg.maa_resource_name): cfg.get(cfg.maa_resource_path)},
                )

                data = {
                    "adb": {
                        "adb_path": "",
                        "address": "",
                        "input_method": 0,
                        "screen_method": 0,
                        "config": {},
                    },
                    "win32": {
                        "hwnd": 0,
                        "input_method": 0,
                        "screen_method": 0,
                    },
                    "controller": {"name": ""},
                    "gpu": -1,
                    "resource": "",
                    "task": [],
                    "finish_option": 0,
                    "finish_option_res": 0,
                    "finish_option_cfg": 0,
                    "run_before_start": "",
                    "run_before_start_args": "",
                    "run_after_finish": "",
                    "run_after_finish_args": "",
                    "emu_path": "",
                    "emu_args": "",
                    "emu_wait_time": 10,
                    "exe_path": "",
                    "exe_args": "",
                    "exe_wait_time": 10,
                }
                Save_Config(cfg.get(cfg.maa_config_path), data)
                cfg.set(cfg.resource_exist, True)
                init_maa_config_data(True)

            else:
                logger.error("资源文件不存在")
                cfg.set(cfg.resource_exist, False)
                maa_config_name = ""
                maa_config_path = ""
                maa_resource_name = ""
                maa_resource_path = ""
                maa_config_list = {}
                maa_resource_list = {}
        else:
            if resource in list(maa_resource_list.keys()):
                cfg.set(cfg.maa_resource_name, resource)
                maa_resource_name = resource
                cfg.set(cfg.maa_resource_path, maa_resource_list[resource])
                maa_resource_path = maa_resource_list[resource]
                if not config:
                    cfg.set(cfg.maa_config_name, "default")
                    cfg.set(cfg.maa_config_path, maa_config_list[resource]["default"])
                    maa_config_name = "default"
                    maa_config_path = maa_config_list[resource]["default"]
            if config in list(maa_config_list[maa_resource_name].keys()):
                cfg.set(cfg.maa_config_name, config)
                cfg.set(cfg.maa_config_path, maa_config_list[maa_resource_name][config])
                maa_config_name = config
                maa_config_path = maa_config_list[maa_resource_name][config]
            else:
                cfg.set(cfg.maa_config_name, "default")
                cfg.set(
                    cfg.maa_config_path, maa_config_list[maa_resource_name]["default"]
                )
                maa_config_name = "default"
                maa_config_path = maa_config_list[maa_resource_name]["default"]
            cfg.set(cfg.run_after_startup_arg, False)
            if directly:
                logger.info("检查到 -d 参数,直接启动")
                cfg.set(cfg.run_after_startup_arg, True)
            if DEV:
                logger.info("检查到 -DEV 参数,使用DEV模式")
                cfg.set(cfg.run_after_startup_arg, False)
                cfg.set(cfg.click_update, False)

            logger.info("资源文件存在")
            cfg.set(cfg.click_update, False)
            cfg.set(cfg.resource_exist, True)

            signalBus.resource_exist.emit(True)
            logger.info(
                f"资源版本:{maa_config_data.interface_config.get('version','unknown')}"
            )
    except:
        logger.error("检查资源文件失败")
        cfg.set(cfg.resource_exist, False)
        signalBus.resource_exist.emit(False)
        show_error_message()
        return False
