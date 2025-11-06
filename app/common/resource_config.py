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
MFW-ChainFlow Assistant maa config配置对象
作者:overflow65537
"""

from .signal_bus import signalBus
from ..utils.tool import Read_Config
from .config import cfg
from ..utils.logger import logger
from .typeddict import ResourceConfig, get_initial_main_config
import json
import os
import sys


res_cfg = ResourceConfig()


def init_res_cfg(status: bool):
    try:
        if status:
            """初始化配置文件"""
            res_cfg.interface_config_path = os.path.join(
                cfg.get(cfg.maa_resource_path), "interface.json"
            )
            res_cfg.interface_config = Read_Config(
                res_cfg.interface_config_path
            )  # type: ignore
            if not res_cfg.interface_config:
                logger.error("interface.json load failed")
                raise FileNotFoundError(
                    f"interface.json load failed {res_cfg.interface_config} is empty"
                )

            res_cfg.config_path = cfg.get(cfg.maa_config_path)
            res_cfg.config = Read_Config(res_cfg.config_path)  # type: ignore
            if not res_cfg.config:
                logger.error("config.json load failed")
                raise FileNotFoundError(
                    f"config.json load failed {res_cfg.config} is empty"
                )
            res_cfg.config_name = cfg.get(cfg.maa_config_name)
            res_cfg.config_path = cfg.get(cfg.maa_config_path)
            res_cfg.config_data = cfg.get(cfg.maa_config_list)

            res_cfg.resource_path = cfg.get(cfg.maa_resource_path)
            res_cfg.resource_name = cfg.get(cfg.maa_resource_name)
            res_cfg.config_name_list = list(
                res_cfg.config_data[res_cfg.resource_name].keys()
            )

            res_cfg.resource_data = cfg.get(cfg.maa_resource_list)
            res_cfg.resource_name_list = list(
                res_cfg.resource_data.keys()
            )
            res_cfg.log_path = os.path.join(
                ".", "debug", res_cfg.resource_name
            )
            logger.debug("配置文件初始化")
            logger.debug(f"log_path: {res_cfg.log_path}")
            logger.debug(
                f"interface_config:\n{json.dumps(res_cfg.interface_config, indent=4,ensure_ascii=False)}"
            )
            logger.debug(
                f"config:\n{json.dumps(res_cfg.config, indent=4,ensure_ascii=False)}"
            )
            logger.debug(f"config_name: {res_cfg.config_name}")
            logger.debug(f"config_path: {res_cfg.config_path}")
            logger.debug(f"config_data: {res_cfg.config_data}")
            logger.debug(f"resource_path: {res_cfg.resource_path}")
            logger.debug(f"resource_name: {res_cfg.resource_name}")
            logger.debug(f"resource_data: {res_cfg.resource_data}")
            # 添加res_cfg.resource_path到sys.path
            sys.path.append((os.path.join(res_cfg.resource_path, "custom")))
            logger.debug(f"sys.path: {sys.path}")

            logger.debug("配置文件初始化完成")

        else:
            res_cfg.interface_config_path = ""
            res_cfg.interface_config = {}

            res_cfg.config_path = ""
            res_cfg.config = get_initial_main_config()
            res_cfg.config_name = ""
            res_cfg.config_path = ""
            res_cfg.config_data = {}
            res_cfg.config_name_list = []

            res_cfg.resource_path = ""
            res_cfg.resource_name = ""
            res_cfg.resource_data = {}
            res_cfg.resource_name_list = []
            logger.debug("重置配置")

    except:
        logger.exception("配置文件初始化失败")
        signalBus.resource_exist.emit(False)
        res_cfg.interface_config_path = ""
        res_cfg.interface_config = {}

        res_cfg.config_path = ""
        res_cfg.config = get_initial_main_config()
        res_cfg.config_name = ""
        res_cfg.config_path = ""
        res_cfg.config_data = {}
        res_cfg.config_name_list = []

        res_cfg.resource_path = ""
        res_cfg.resource_name = ""
        res_cfg.resource_data = {}
        res_cfg.resource_name_list = []
        cfg.set(cfg.maa_resource_path, "")
        cfg.set(cfg.maa_resource_name, "")
        cfg.set(cfg.maa_resource_list, {})
        cfg.set(cfg.maa_config_path, "")
        cfg.set(cfg.maa_config_name, "")
        cfg.set(cfg.maa_config_list, {})
        logger.debug("配置文件初始化失败, 已重置配置")


signalBus.resource_exist.connect(init_res_cfg)
