from typing import TypedDict
from ..common.signal_bus import signalBus
from ..utils.tool import Read_Config
from ..common.config import cfg
import os


class MaaConfigData:

    interface_config: dict = {}
    interface_config_path: str = ""

    config: dict = {}
    config_name: str = ""
    config_path: str = ""
    config_data: dict = {}
    config_name_list: list = []

    resource_name: str = ""
    resource_path: str = ""
    resource_data: dict = {}
    resource_name_list: list = []


maa_config_data = MaaConfigData()


def init_maa_config_data(status: bool):
    if status:
        """初始化配置文件"""
        maa_config_data.interface_config_path = os.path.join(
            cfg.get(cfg.maa_resource_path), "interface.json"
        )
        maa_config_data.interface_config = Read_Config(
            maa_config_data.interface_config_path
        )

        maa_config_data.config_path = cfg.get(cfg.maa_config_path)
        maa_config_data.config = Read_Config(maa_config_data.config_path)
        maa_config_data.config_name = cfg.get(cfg.maa_config_name)
        maa_config_data.config_path = cfg.get(cfg.maa_config_path)
        maa_config_data.config_data = cfg.get(cfg.maa_config_list)
        maa_config_data.config_name_list = list(maa_config_data.config_data.keys())

        maa_config_data.resource_path = cfg.get(cfg.maa_resource_path)
        maa_config_data.resource_name = cfg.get(cfg.maa_resource_name)
        maa_config_data.resource_data = cfg.get(cfg.maa_resource_list)
        maa_config_data.resource_name_list = list(maa_config_data.resource_data.keys())
    else:
        maa_config_data.interface_config_path = ""
        maa_config_data.interface_config = {}

        maa_config_data.config_path = ""
        maa_config_data.config = {}
        maa_config_data.config_name = ""
        maa_config_data.config_path = ""
        maa_config_data.config_data = {}
        maa_config_data.config_name_list = []

        maa_config_data.resource_path = ""
        maa_config_data.resource_name = ""
        maa_config_data.resource_data = {}
        maa_config_data.resource_name_list = []


signalBus.resource_exist.connect(init_maa_config_data)
