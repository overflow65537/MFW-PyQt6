"""设备管理模块

负责设备列表的获取、过滤和管理。
"""

import re
from typing import TYPE_CHECKING

from qfluentwidgets import ComboBox

from app.utils.logger import logger
if TYPE_CHECKING:
    from .....core.core import ServiceCoordinator


class DeviceManager:
    """设备管理器
    
    负责:
    - 获取 ADB 设备列表
    - 获取 Win32 窗口列表
    - 填充设备下拉框
    - 从配置中恢复设备信息
    """

    def __init__(self, service_coordinator: "ServiceCoordinator"):
        self.service_coordinator = service_coordinator

    def get_adb_devices(self):
        """获取 ADB 设备列表

        通过 maa.toolkit 调用实际的 ADB 设备检测逻辑

        Returns:
            AdbDevice 对象列表
        """
        try:
            from maa.toolkit import Toolkit

            logger.info("获取 ADB 设备列表")
            adb_devices = Toolkit.find_adb_devices()
            logger.info(f"找到 {len(adb_devices)} 个 ADB 设备")
            return adb_devices
        except Exception as e:
            logger.error(f"获取 ADB 设备失败: {e}")
            return []

    def get_win32_devices(self):
        """获取 Win32 窗口列表

        通过 maa.toolkit 调用实际的 Win32 窗口检测逻辑

        Returns:
            DesktopWindow 对象列表
        """
        try:
            from maa.toolkit import Toolkit

            logger.info("获取 Win32 窗口列表")
            windows = Toolkit.find_desktop_windows()
            logger.info(f"找到 {len(windows)} 个窗口")
            return windows
        except Exception as e:
            logger.error(f"获取 Win32 窗口失败: {e}")
            return []

    def populate_device_list(self, devices, device_combo: ComboBox, controller_config: dict, tr_func):
        """填充设备下拉框

        使用 interface.json 中的配置进行过滤和匹配：
        - Win32: 使用 class_regex 和 window_regex 过滤窗口
        - ADB: 直接显示所有设备

        Args:
            devices: 设备列表（AdbDevice 或 DesktopWindow 对象）
            device_combo: 设备下拉框控件
            controller_config: 控制器配置字典
            tr_func: 翻译函数
        """
        if not devices:
            return

        from maa.toolkit import AdbDevice, DesktopWindow

        # 用于自动选中第一个匹配项
        first_match_index = -1
        current_index = 0

        for device in devices:
            should_add = True
            is_match = False

            if isinstance(device, AdbDevice):
                # ADB 设备：显示 "name - address"
                display_text = f"{device.name} - {device.address}"
                # 保存完整的设备对象（转换为字典）
                # 注意：adb_path 是 Path 对象，需要转换为字符串
                user_data = {
                    "type": "adb",
                    "name": device.name,
                    "adb_path": str(device.adb_path),  # Path 对象转字符串
                    "address": device.address,
                    "screencap_methods": device.screencap_methods,
                    "input_methods": device.input_methods,
                    "config": device.config,
                }
                # ADB 设备默认都匹配
                is_match = True

            elif isinstance(device, DesktopWindow):
                # Win32 窗口：使用 class_regex 和 window_regex 过滤
                win32_config = controller_config.get("win32", {})
                class_regex = win32_config.get("class_regex", ".*")
                window_regex = win32_config.get("window_regex", ".*")

                # 检查类名和窗口名是否匹配正则表达式
                class_match = re.search(class_regex, device.class_name or "")
                window_match = re.search(window_regex, device.window_name or "")

                # 只有两个都匹配才添加到列表
                if class_match and window_match:
                    is_match = True
                    logger.debug(
                        f"窗口匹配: {device.window_name} ({device.class_name}) "
                        f"- class_regex: {class_regex}, window_regex: {window_regex}"
                    )
                else:
                    should_add = False
                    logger.debug(
                        f"窗口不匹配: {device.window_name} ({device.class_name}) "
                        f"- class_match: {bool(class_match)}, window_match: {bool(window_match)}"
                    )

                display_text = f"{device.window_name}"
                if device.class_name:
                    display_text += f" ({device.class_name})"
                # 保存完整的窗口对象（转换为字典）
                user_data = {
                    "type": "win32",
                    "hwnd": device.hwnd,
                    "class_name": device.class_name,
                    "window_name": device.window_name,
                }

            else:
                # 兼容旧的字符串格式
                display_text = str(device)
                user_data = None

            # 添加到下拉框
            if should_add:
                device_combo.addItem(display_text)
                if user_data is not None:
                    device_combo.setItemData(current_index, user_data)

                # 记录第一个匹配的索引（用于自动选中）
                if is_match and first_match_index == -1:
                    first_match_index = current_index

                current_index += 1

        # 如果找到匹配项，自动选中第一个
        if first_match_index >= 0:
            device_combo.setCurrentIndex(first_match_index)
            logger.info(f"自动选中第一个匹配的设备（索引: {first_match_index}）")

        added_count = device_combo.count()
        
        logger.info(
            f"已添加 {added_count} 个设备到列表（总共检测到 {len(devices)} 个）"
        )

    def populate_saved_device(self, saved_options: dict, controller_name: str, device_combo: ComboBox, controller_configs: dict, flatten_func):
        """从保存的配置中填充设备信息到下拉框

        Args:
            saved_options: 保存的任务选项
            controller_name: 当前控制器名称
            device_combo: 设备下拉框控件
            controller_configs: 控制器配置字典
            flatten_func: 展平选项的函数
        """
        logger.debug(f"populate_saved_device 调用: controller_name={controller_name}")
        logger.debug(f"saved_options keys: {list(saved_options.keys())}")

        if not controller_name or controller_name not in controller_configs:
            logger.debug("控制器未选择或无效，跳过设备填充")
            return

        controller_config = controller_configs[controller_name]
        controller_type = controller_config.get("type", "").lower()

        logger.debug(f"控制器类型: {controller_type}")

        # 将嵌套配置展平，以便读取字段
        flattened_options = flatten_func(saved_options)
        logger.debug(f"展平后的选项 keys: {list(flattened_options.keys())}")

        # 从保存的选项中重建设备信息字典
        if controller_type == "adb":
            # 检查是否有 ADB 相关配置（adb_path 或 adb_port）
            adb_path = str(flattened_options.get("adb_path", ""))
            adb_address = str(flattened_options.get("adb_port", ""))
            device_name = str(flattened_options.get("adb_device_name", ""))

            logger.info(f"保存的 adb_path: {adb_path}")
            logger.info(f"保存的 adb_port (address): {adb_address}")
            logger.info(f"保存的 adb_device_name: {device_name}")

            # 如果没有任何 ADB 配置，跳过
            if not adb_path and not adb_address:
                logger.debug("未找到保存的 ADB 配置信息")
                return

            # 构建 ADB 设备信息
            device_data = {
                "type": "adb",
                "name": device_name
                or adb_address
                or "Unknown Device",  # 优先使用保存的名称
                "adb_path": adb_path,
                "address": adb_address,
                "screencap_methods": int(
                    str(flattened_options.get("adb_screenshot_method", "0")) or "0"
                ),
                "input_methods": int(
                    str(flattened_options.get("adb_input_method", "0")) or "0"
                ),
                "config": {},
            }

            logger.debug(
                f"构建的设备数据 - name: {device_data['name']}, address: {device_data['address']}"
            )

            # 尝试解析 adb_config
            import json

            adb_config_str = str(flattened_options.get("adb_config", ""))
            if adb_config_str:
                try:
                    device_data["config"] = json.loads(adb_config_str)
                except json.JSONDecodeError:
                    logger.warning(f"无法解析 adb_config: {adb_config_str}")

            # 添加到下拉框
            display_text = (
                f"{device_data['name']} - {device_data['address']}"
                if device_data["address"]
                else device_data["name"]
            )
            device_combo.addItem(display_text)
            device_combo.setItemData(0, device_data)
            device_combo.setCurrentIndex(0)
            logger.info(f"从保存的配置中加载 ADB 设备: {display_text}")

        elif controller_type == "win32":
            # 从 hwnd 字段读取窗口句柄
            hwnd_str = str(flattened_options.get("hwnd", ""))
            device_name = str(flattened_options.get("win32_device_name", ""))

            if not hwnd_str:
                logger.debug("未找到保存的 Win32 窗口信息")
                return

            # 构建 Win32 窗口信息
            try:
                hwnd_value = int(hwnd_str) if isinstance(hwnd_str, str) else hwnd_str
            except (ValueError, TypeError):
                logger.warning(f"无效的 hwnd 值: {hwnd_str}")
                return

            device_data = {
                "type": "win32",
                "hwnd": hwnd_value,
                "class_name": "",  # 无法从保存的配置中恢复，留空
                "window_name": device_name or str(hwnd_str),  # 优先使用保存的窗口名称
            }

            # 添加到下拉框
            display_text = device_name or str(hwnd_str)  # 显示窗口名称或 hwnd
            device_combo.addItem(display_text)
            device_combo.setItemData(0, device_data)
            device_combo.setCurrentIndex(0)
            logger.info(f"从保存的配置中加载 Win32 窗口: {display_text}")
