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
Bundle 服务

职责：
1. 管理 bundle 的增删改查
2. 验证 bundle 路径有效性
3. 解析 bundle 对应的 interface 路径
"""

from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import jsonc

from app.utils.logger import logger


class BundleService:
    """Bundle 管理服务
    
    从 ServiceCoordinator 中分离出来，专门负责 Bundle 相关的操作。
    """

    def __init__(
        self,
        main_config_path: Path,
        get_main_config: Callable[[], Optional[Dict[str, Any]]],
        save_main_config: Callable[[], bool],
    ):
        """初始化 Bundle 服务
        
        Args:
            main_config_path: 主配置文件路径
            get_main_config: 获取主配置数据的回调函数
            save_main_config: 保存主配置的回调函数
        """
        self._main_config_path = main_config_path
        self._get_main_config = get_main_config
        self._save_main_config = save_main_config

    @property
    def main_config(self) -> Optional[Dict[str, Any]]:
        """获取主配置"""
        return self._get_main_config()

    def list_bundles(self) -> List[str]:
        """列出所有 bundle 名称"""
        main_config = self.main_config
        if main_config and "bundle" in main_config:
            bundle = main_config["bundle"]
            if isinstance(bundle, dict):
                return list(bundle.keys())
        return []

    def get_bundle(self, bundle_name: str) -> Optional[Dict[str, Any]]:
        """获取指定 bundle 的数据
        
        Args:
            bundle_name: bundle 名称
            
        Returns:
            bundle 数据字典，不存在则返回 None
        """
        main_config = self.main_config
        if main_config and "bundle" in main_config:
            bundle = main_config["bundle"]
            if isinstance(bundle, dict) and bundle_name in bundle:
                return bundle[bundle_name]
        return None

    def update_bundle_path(
        self, bundle_name: str, new_path: str, bundle_display_name: Optional[str] = None
    ) -> bool:
        """更新 bundle 路径
        
        Args:
            bundle_name: bundle 名称（键）
            new_path: 新路径
            bundle_display_name: 显示名称（可选）
        """
        if not self._main_config_path.exists():
            logger.error(f"主配置文件不存在: {self._main_config_path}")
            return False

        try:
            with open(self._main_config_path, "r", encoding="utf-8") as f:
                config_data: Dict[str, Any] = jsonc.load(f)

            if "bundle" not in config_data:
                config_data["bundle"] = {}
            if not isinstance(config_data["bundle"], dict):
                config_data["bundle"] = {}

            if bundle_name not in config_data["bundle"]:
                config_data["bundle"][bundle_name] = {}

            bundle_info = config_data["bundle"][bundle_name]
            if not isinstance(bundle_info, dict):
                bundle_info = {}

            bundle_info["path"] = new_path
            if bundle_display_name is not None:
                bundle_info["name"] = bundle_display_name
            elif "name" not in bundle_info:
                bundle_info["name"] = bundle_name

            config_data["bundle"][bundle_name] = bundle_info

            with open(self._main_config_path, "w", encoding="utf-8") as f:
                jsonc.dump(config_data, f, indent=4, ensure_ascii=False)

            logger.info(f"已更新 bundle '{bundle_name}' 的路径为: {new_path}")
            return True

        except Exception as e:
            logger.error(f"更新 bundle 路径失败: {e}")
            return False

    def delete_bundle(self, bundle_name: str) -> bool:
        """删除 bundle
        
        Args:
            bundle_name: bundle 名称
        """
        main_config = self.main_config
        if not isinstance(main_config, dict):
            return False

        bundle_dict = main_config.get("bundle")
        if not isinstance(bundle_dict, dict):
            return True

        if bundle_name not in bundle_dict:
            return True

        bundle_dict.pop(bundle_name, None)
        main_config["bundle"] = bundle_dict
        success = self._save_main_config()
        if success:
            logger.info(f"已从主配置中移除 bundle: {bundle_name}")
        return success

    def resolve_interface_path_from_bundle(self, bundle_name: str) -> Optional[Path]:
        """从 bundle 名称解析 interface.json 路径
        
        Args:
            bundle_name: bundle 名称
            
        Returns:
            interface.json 的完整路径，解析失败返回 None
        """
        bundle_data = self.get_bundle(bundle_name)
        if not bundle_data:
            return None
            
        bundle_path_str = bundle_data.get("path")
        if not bundle_path_str:
            return None
            
        bundle_path = Path(bundle_path_str)
        if not bundle_path.is_absolute():
            bundle_path = self._main_config_path.parent / bundle_path
            
        interface_path = bundle_path / "interface.json"
        if interface_path.exists():
            return interface_path
            
        return None

    def normalize_bundle_name(self, raw_bundle: Any) -> Optional[str]:
        """规范化 bundle 名称
        
        支持两种格式：
        1. 字符串: 直接作为 bundle 名称
        2. 字典 {"name": "xxx"}: 提取 name 字段
        
        Args:
            raw_bundle: 原始 bundle 数据
            
        Returns:
            规范化后的 bundle 名称
        """
        if isinstance(raw_bundle, str):
            return raw_bundle
        if isinstance(raw_bundle, dict):
            return raw_bundle.get("name")
        return None

    def cleanup_invalid_bundles(
        self, resolve_interface_path: Callable[[str], Optional[Path]]
    ) -> None:
        """清理无效的 bundle（路径不存在或 interface.json 不存在）
        
        Args:
            resolve_interface_path: 解析 interface 路径的回调函数
        """
        bundle_names = self.list_bundles()
        if not bundle_names:
            return

        invalid_bundles: List[str] = []
        for name in bundle_names:
            iface_path = resolve_interface_path(name)
            if iface_path is None:
                invalid_bundles.append(name)

        if not invalid_bundles:
            return

        main_config = self.main_config
        if not isinstance(main_config, dict):
            return

        bundle_dict = main_config.get("bundle") or {}
        if not isinstance(bundle_dict, dict):
            bundle_dict = {}

        for name in invalid_bundles:
            if name in bundle_dict:
                logger.info(f"移除无效 bundle: {name}")
                bundle_dict.pop(name, None)

        main_config["bundle"] = bundle_dict
        try:
            self._save_main_config()
        except Exception:
            pass
