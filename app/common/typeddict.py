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
MFW-ChainFlow Assistant 类型标记
作者:overflow65537
"""

from typing import Dict, List, TypedDict, Optional, Any

from dataclasses import dataclass


# 定义模拟器extra的类型
@dataclass
class EmuExtrasConfig:
    enable: bool
    index: int
    path: str
    pid: int


# 定义 ADB 配置的类型
@dataclass
class AdbConfig:
    adb_path: str
    address: str
    input_method: int
    screen_method: int
    config: Dict[str, Any]


# 定义 Win32 配置的类型
@dataclass
class Win32Config:
    hwnd: int
    input_method: int
    screen_method: int


# 定义 Controller 配置的类型
@dataclass
class ControllerConfig:
    name: str


# 定义 refresh_time 的类型
@dataclass
class RefreshTime:
    H: int
    w: int
    d: int


# 定义 interval 的类型
@dataclass
class Interval:
    unit: int
    item: int
    loop_item: int
    current_loop: int


# 定义 speedrun 的类型
@dataclass
class SpeedrunConfig:
    schedule_mode: str
    refresh_time: RefreshTime
    interval: Interval
    last_run: str
    enabled: bool


# 定义任务项的类型



# 定义完整的配置类型
@dataclass
class MainConfig:
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
    emu_wait_time: str
    exe_path: str
    exe_args: str
    exe_wait_time: str
    know_task: list


InnerConfig = Dict[str, str]

MaaConfigList = Dict[str, InnerConfig]

@dataclass
class ControllerItem:
    name: str
    type: str

@dataclass
class ResourcePath:
    name: str
    path: List[str]

@dataclass
class TaskItem_interface:
    name: str
    entry: str
    option: Optional[List[str]]
    speedrun: Optional[SpeedrunConfig]
    pipeline_override: dict
    doc: Optional[str]

@dataclass
class InterfaceData:
    url: str
    name: str
    MFW_min_req_version: str
    mirrorchyan_rid: str
    controller: List[ControllerItem]
    resource: List[ResourcePath]
    task: List[TaskItem_interface]
    option: Dict[str, Any]
    version: str
    show_notice: bool



class ResourceConfig:
    interface_config: InterfaceData = {}
    interface_config_path: str = ""

    config: MainConfig = get_initial_main_config()
    config_name: str = ""
    config_path: str = ""

    config_data: MaaConfigList = {}
    config_name_list: List[str] = []

    resource_name: str = ""
    resource_path: str = ""

    resource_data: Dict[str, str] = {}
    resource_name_list: List[str] = []

    log_path: str = ""
