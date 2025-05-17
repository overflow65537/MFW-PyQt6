from dataclasses import dataclass, field
from ..common.signal_bus import signalBus
from ..utils.tool import Read_Config, show_error_message
from ..common.config import cfg
from ..utils.logger import logger
import json
import os
from typing import Dict, List, Any, TypedDict,Optional


from typing import TypedDict, List, Dict


# 定义模拟器extra的类型
class EmuExtrasConfig(TypedDict, total=False):
    enable: bool
    index: int
    path: str
    pid: int


# 定义 extras 配置的类型
ExtrasConfig = Dict[str, EmuExtrasConfig]


# 定义 ADB 配置中 config 字段的类型
class AdbInnerConfig(TypedDict, total=False):
    extras: ExtrasConfig


# 定义 ADB 配置的类型
class AdbConfig(TypedDict, total=False):
    adb_path: str
    address: str
    input_method: int
    screen_method: int
    config: AdbInnerConfig


# 定义 Win32 配置的类型
class Win32Config(TypedDict, total=False):
    hwnd: int
    input_method: int
    screen_method: int


# 定义 Controller 配置的类型
class ControllerConfig(TypedDict, total=False):
    name: str


# 定义 refresh_time 的类型
class RefreshTime(TypedDict, total=False):
    H: int
    w: int
    d: int


# 定义 interval 的类型
class Interval(TypedDict, total=False):
    unit: int
    item: int
    loop_item: int
    current_loop: int


# 定义 speedrun 的类型
class SpeedrunConfig(TypedDict, total=False):
    schedule_mode: str
    refresh_time: RefreshTime
    interval: Interval
    last_run: str
    enabled: bool


# 定义任务项的类型
class TaskItem(TypedDict, total=False):
    name: str
    option: List[Dict]
    speedrun: SpeedrunConfig



# 定义完整的配置类型
class MainConfig(TypedDict, total=False):
    adb: AdbConfig
    win32: Win32Config
    controller: ControllerConfig
    gpu: int
    resource: str
    task: List[TaskItem]
    finish_option: int
    finish_option_res: int
    finish_option_cfg: int
    run_before_start: str
    run_before_start_args: str
    run_after_finish: str
    run_after_finish_args: str
    emu_path: str
    emu_args: str
    emu_wait_time: int
    exe_path: str
    exe_args: str
    exe_wait_time: int


InnerConfig = Dict[str, str]

MaaConfigList = Dict[str, InnerConfig]

class ControllerItem(TypedDict):
    name: str
    type: str

class ResourcePath(TypedDict):
    name: str
    path: List[str]

class PipelineOverride(TypedDict, total=False):
    enabled: bool
    expected: Optional[str | List[str]]
    next: Optional[List[str]]
    interrupt: Optional[List[str]]
    recognition: Optional[str]
    roi: Optional[List[int]]
    template: Optional[str]
    green_mask: Optional[bool]
    roi_offset: Optional[List[int]]
    replace: Optional[List[List[str]]]
    inverse: Optional[bool]
    index: Optional[int]

class OptionCase(TypedDict):
    name: str
    pipeline_override: Dict[str, PipelineOverride]

class OptionItem(TypedDict):
    cases: List[OptionCase]

class TaskItem_interface(TypedDict, total=False):
    name: str
    entry: str
    option: Optional[List[str]]
    speedrun: Optional[SpeedrunConfig]
    pipeline_override: Optional[Dict[str, PipelineOverride]]
    doc: Optional[str]

class InterfaceData(TypedDict,total=False):
    url: str
    name: str
    MFW_min_req_version: str
    mirrorchyan_rid: str
    controller: List[ControllerItem]
    resource: List[ResourcePath]
    task: List[TaskItem_interface]
    option: Dict[str, OptionItem]
    version: str

class MaaConfigData:
    interface_config: InterfaceData = {}
    interface_config_path: str = ""

    config: MainConfig = {}
    config_name: str = ""
    config_path: str = ""

    config_data: MaaConfigList = {}
    config_name_list: List[str] = []

    resource_name: str = ""
    resource_path: str = ""

    resource_data: Dict[str, str] = {}
    resource_name_list: List[str] = []


maa_config_data = MaaConfigData()


def init_maa_config_data(status: bool):
    try:
        if status:
            """初始化配置文件"""
            maa_config_data.interface_config_path = os.path.join(
                cfg.get(cfg.maa_resource_path), "interface.json"
            )
            maa_config_data.interface_config = Read_Config(
                maa_config_data.interface_config_path
            ) # type: ignore
            if not maa_config_data.interface_config:
                logger.error("interface.json load failed")
                raise FileNotFoundError(
                    f"interface.json load failed {maa_config_data.interface_config} is empty"
                )

            maa_config_data.config_path = cfg.get(cfg.maa_config_path)
            maa_config_data.config = Read_Config(maa_config_data.config_path) # type: ignore
            if not maa_config_data.config:
                logger.error("config.json load failed")
                raise FileNotFoundError(
                    f"config.json load failed {maa_config_data.config} is empty"
                )
            maa_config_data.config_name = cfg.get(cfg.maa_config_name)
            maa_config_data.config_path = cfg.get(cfg.maa_config_path)
            maa_config_data.config_data = cfg.get(cfg.maa_config_list)

            maa_config_data.resource_path = cfg.get(cfg.maa_resource_path)
            maa_config_data.resource_name = cfg.get(cfg.maa_resource_name)
            maa_config_data.config_name_list = list(
                maa_config_data.config_data[maa_config_data.resource_name].keys()
            )

            maa_config_data.resource_data = cfg.get(cfg.maa_resource_list)
            maa_config_data.resource_name_list = list(
                maa_config_data.resource_data.keys()
            )
            logger.debug("配置文件初始化")
            logger.debug(
                f"interface_config:\n{json.dumps(maa_config_data.interface_config, indent=4,ensure_ascii=False)}"
            )
            logger.debug(
                f"config:\n{json.dumps(maa_config_data.config, indent=4,ensure_ascii=False)}"
            )
            logger.debug(f"config_name: {maa_config_data.config_name}")
            logger.debug(f"config_path: {maa_config_data.config_path}")
            logger.debug(f"config_data: {maa_config_data.config_data}")
            logger.debug(f"resource_path: {maa_config_data.resource_path}")
            logger.debug(f"resource_name: {maa_config_data.resource_name}")
            logger.debug(f"resource_data: {maa_config_data.resource_data}")
            logger.debug("配置文件初始化完成")

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
            logger.debug("配置文件初始化失败")
    except:
        logger.exception("配置文件初始化失败")
        signalBus.resource_exist.emit(False)
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
        cfg.set(cfg.maa_resource_path, "")
        cfg.set(cfg.maa_resource_name, "")
        cfg.set(cfg.maa_resource_list, {})
        cfg.set(cfg.maa_config_path, "")
        cfg.set(cfg.maa_config_name, "")
        cfg.set(cfg.maa_config_list, {})
        logger.debug("配置文件初始化失败, 已重置配置")
        show_error_message()


signalBus.resource_exist.connect(init_maa_config_data)
