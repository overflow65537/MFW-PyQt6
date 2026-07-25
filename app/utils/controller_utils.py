from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
from maa.toolkit import AdbDevice

import jsonc

from app.utils.logger import logger
from app.utils.screencap_lock import screencap_guard


def snapshot_cached_image(controller: Any) -> Optional[Any]:
    """从 controller.cached_image 拷贝一帧，避免与 Maa 更新并发读写同一缓冲区。

    返回 BGR 格式的 numpy.ndarray 副本；无法读取时返回 None。
    """
    if controller is None:
        return None

    try:
        import numpy as np
        from PIL import Image as PILImage

        with screencap_guard():
            cached_attr = getattr(controller, "cached_image", None)
            if cached_attr is None:
                return None

            raw = cached_attr() if callable(cached_attr) else cached_attr
            if raw is None:
                return None

            if isinstance(raw, np.ndarray):
                if raw.ndim < 2:
                    return None
                h, w = int(raw.shape[0]), int(raw.shape[1])
                if h <= 0 or w <= 0:
                    return None
                return np.ascontiguousarray(raw.copy())

            if isinstance(raw, PILImage.Image):
                rgb = np.asarray(raw.convert("RGB"))
                return np.ascontiguousarray(rgb[..., ::-1])

            return None
    except Exception:
        return None


class ControllerHelper:
    """控制器相关工具方法 - 包括 ADB 控制器（模拟器）、Win32 控制器等的管理功能"""

    @staticmethod
    def build_mumu_manager_path(adb_path: Optional[str]) -> Optional[str]:
        """根据 adb 路径推导 MuMuManager.exe 路径"""
        if not adb_path:
            return None
        return str(Path(adb_path).parent / "MuMuManager.exe")

    @staticmethod
    def build_ldconsole_path(adb_path: Optional[str]) -> Optional[str]:
        """根据 adb 路径推导 ldconsole.exe 路径"""
        if not adb_path:
            return None
        return str(Path(adb_path).parent / "ldconsole.exe")

    @staticmethod
    def get_mumu_info(mumu_manager_path: str) -> Optional[Dict[str, Any]]:
        """调用 MuMuManager 获取 info 结果"""
        try:
            emu = subprocess.run(
                [mumu_manager_path, "info", "-v", "all"],
                capture_output=True,
                text=True,
                check=True,
                encoding="utf-8",
                errors="ignore",
            )
            return jsonc.loads((emu.stdout or "").strip())
        except (subprocess.CalledProcessError, jsonc.JSONDecodeError) as exc:
            logger.error(f"获取 MuMu 信息失败: {exc}")
            return None

    @staticmethod
    def _iter_mumu_instances(
        multi_dict: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """将 MuMu info 输出规范为实例列表（兼容单实例/多实例格式）。"""
        if not isinstance(multi_dict, dict) or not multi_dict:
            return []
        # 单实例：顶层直接带 created_timestamp / index
        if multi_dict.get("created_timestamp", False) or "adb_port" in multi_dict:
            return [multi_dict]
        instances: List[Dict[str, Any]] = []
        for key, emu_data in multi_dict.items():
            if not isinstance(emu_data, dict):
                continue
            item = dict(emu_data)
            if item.get("index") is None:
                item["index"] = key
            instances.append(item)
        return instances

    @staticmethod
    def get_mumu_indices_by_port(
        multi_dict: Dict[str, Any], adb_port: Optional[str]
    ) -> List[str]:
        """根据 adb 端口从 MuMu info 结果中提取实例序号"""
        if not adb_port:
            return []

        indices: List[str] = []
        for emu_data in ControllerHelper._iter_mumu_instances(multi_dict):
            if str(emu_data.get("adb_port", "")) == str(adb_port):
                idx = emu_data.get("index")
                if idx is not None:
                    indices.append(str(idx))
        return indices

    @staticmethod
    def get_mumu_started_indices(multi_dict: Dict[str, Any]) -> List[str]:
        """返回当前已启动的 MuMu 实例序号。"""
        indices: List[str] = []
        for emu_data in ControllerHelper._iter_mumu_instances(multi_dict):
            started = bool(
                emu_data.get("is_process_started")
                or emu_data.get("is_android_started")
                or emu_data.get("player_state") == "start_finished"
            )
            if not started:
                continue
            idx = emu_data.get("index")
            if idx is not None:
                indices.append(str(idx))
        return indices

    @staticmethod
    def get_ld_list_output(ldconsole_path: str) -> Optional[str]:
        """调用 ldconsole list2 并返回输出"""
        try:
            ld_emu = subprocess.run(
                [ldconsole_path, "list2"],
                shell=True,
                capture_output=True,
                text=True,
                check=True,
                encoding="utf-8",
                errors="ignore",
            )
            return ld_emu.stdout or ""
        except subprocess.CalledProcessError as exc:
            logger.error(f"获取 LD 列表信息失败: {exc}")
            return None

    @staticmethod
    def get_ld_index_from_list2(ld_output: str, pid_cfg: Any) -> Optional[str]:
        """从 ldconsole list2 输出中，根据配置 pid 匹配并返回实例序号"""
        if pid_cfg is None:
            return None

        pid_cfg_str = str(pid_cfg).strip()
        for raw_line in ld_output.splitlines():
            stripped = raw_line.strip()
            if not stripped:
                continue
            segments = [seg.strip() for seg in stripped.split(",")]
            if len(segments) < 6:
                continue
            if segments[6] == pid_cfg_str:
                return segments[0]
        return None

    @staticmethod
    def close_mumu(
        adb_path: Optional[str],
        adb_port: Optional[str],
        *,
        index: Any = None,
        mumu_install_path: Optional[str] = None,
    ) -> bool:
        """关闭 MuMu 模拟器。

        优先使用 extras 中的 index；新版 MuMu info 可能不再返回 adb_port，
        端口匹配失败时回退到“唯一已启动实例”。
        """
        mumu_manager_path = ControllerHelper.build_mumu_manager_path(adb_path)
        if (not mumu_manager_path or not Path(mumu_manager_path).is_file()) and mumu_install_path:
            candidate = Path(mumu_install_path) / "nx_main" / "MuMuManager.exe"
            if candidate.is_file():
                mumu_manager_path = str(candidate)
        if not mumu_manager_path or not Path(mumu_manager_path).is_file():
            logger.warning("MuMuManager.exe 路径未配置或不存在: %s", mumu_manager_path)
            return False

        multi_dict = ControllerHelper.get_mumu_info(mumu_manager_path)
        mumu_indices: List[str] = []

        # 1) extras.index 最可靠
        if index is not None and str(index).strip() != "":
            mumu_indices = [str(index).strip()]
            logger.info("MuMu 使用 extras.index=%s 关闭", mumu_indices[0])
        # 2) 旧版 info 仍带 adb_port 时按端口匹配
        elif multi_dict:
            mumu_indices = ControllerHelper.get_mumu_indices_by_port(
                multi_dict, adb_port
            )
            if mumu_indices:
                logger.info(
                    "MuMu 按 adb 端口 %s 匹配到序号: %s", adb_port, mumu_indices
                )
            else:
                # 3) 新版 info 常无 adb_port：若仅有一个已启动实例则关闭它
                started = ControllerHelper.get_mumu_started_indices(multi_dict)
                if len(started) == 1:
                    mumu_indices = started
                    logger.info(
                        "MuMu info 无端口匹配，回退关闭唯一已启动实例: %s",
                        mumu_indices[0],
                    )
                elif len(started) > 1:
                    logger.warning(
                        "MuMu info 无 adb_port 且存在多个已启动实例 %s，"
                        "缺少 extras.index，跳过关闭",
                        started,
                    )
                    return False

        if not mumu_indices:
            logger.warning(
                "MuMu 未找到可关闭实例 (port=%s, index=%s)，跳过关闭",
                adb_port,
                index,
            )
            return False

        startupinfo = None
        if sys.platform.startswith("win"):
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE

        closed_any = False
        for idx in mumu_indices:
            try:
                result = subprocess.run(
                    [
                        mumu_manager_path,
                        "control",
                        "-v",
                        str(idx),
                        "shutdown",
                    ],
                    check=True,
                    encoding="utf-8",
                    errors="ignore",
                    capture_output=True,
                    startupinfo=startupinfo,
                )
                logger.info(
                    "MuMuManager shutdown 序号 %s 成功，输出: %s",
                    idx,
                    (result.stdout or "").strip(),
                )
                closed_any = True
            except subprocess.CalledProcessError as e:
                logger.error(
                    "MuMuManager shutdown 序号 %s 失败，错误信息: %s",
                    idx,
                    (e.stderr or "").strip(),
                )
        return closed_any

    @staticmethod
    def close_ldplayer(adb_path: Optional[str], pid_cfg: Any) -> bool:
        """根据 adb_path / 配置 pid 关闭雷电模拟器，返回是否已处理"""
        ldconsole_path = ControllerHelper.build_ldconsole_path(adb_path)
        if not ldconsole_path:
            logger.warning("ldconsole.exe 路径未配置")
            return False

        ld_output = ControllerHelper.get_ld_list_output(ldconsole_path)
        if not ld_output:
            logger.warning("获取 LD 列表信息失败，跳过关闭")
            return False

        ld_index = ControllerHelper.get_ld_index_from_list2(ld_output, pid_cfg)
        if ld_index is None:
            logger.debug("ldconsole list2 输出中没有匹配的第6个字段，跳过关闭")
            return True

        try:
            result = subprocess.run(
                [ldconsole_path, "quit", "--index", str(ld_index)],
                check=True,
                encoding="utf-8",
                capture_output=True,
            )
            logger.info(
                f"ldconsole quit 序号 {ld_index} 成功，输出: {result.stdout.strip()}"
            )
        except subprocess.CalledProcessError as e:
            logger.error(
                f"ldconsole quit 序号 {ld_index} 失败，错误信息: {e.stderr.strip()}"
            )
        return True

    @staticmethod
    def get_index_by_adb_address(
        adb_path: Optional[str],
        address: str | None,
        device_name: Optional[str] = None,
    ) -> Optional[str]:
        """
        尝试根据 adb 地址匹配 ADB 控制器（模拟器）序号：
        - MuMu: 通过 manager info + adb 端口获取序号
        - 雷电: 无法通过地址推断，直接返回 None
        """
        normalized_name = (device_name or "").lower()

        # MuMu 路径
        if "mumu" in normalized_name:
            if not address:
                return None

            host_port = str(address)
            if ":" in host_port:
                adb_port = host_port.split(":")[-1]
            elif "-" in host_port:
                adb_port = host_port.split("-")[-1]
            else:
                adb_port = None

            if not adb_port:
                return None

            mumu_manager_path = ControllerHelper.build_mumu_manager_path(adb_path)
            if not mumu_manager_path:
                return None

            multi_dict = ControllerHelper.get_mumu_info(mumu_manager_path)
            if not multi_dict:
                return None

            indices = ControllerHelper.get_mumu_indices_by_port(multi_dict, adb_port)
            return indices[0] if indices else None

        # 雷电 / 其它：目前无法通过地址反推序号
        if (
            ("雷电" in normalized_name)
            or ("ld" in normalized_name)
            or ("ldplayer" in normalized_name)
        ):
            return None

        return None

    @staticmethod
    def resolve_emulator_index(
        device: AdbDevice,
        adb_path: Optional[str] = None,
        address: str | None = None,
        device_name: Optional[str] = None,
        ld_pid: Optional[str] = None,
    ) -> Optional[str]:
        """
        统一的 ADB 控制器（模拟器）序号推导方法：
        1. 若 device 自带 index，直接返回
        2. MuMu：使用 adb_path + address + name 推导
        3. 雷电：若提供 pid（或从 config 提取 pid），通过 list2 反查序号
        """
        if device is not None:
            adb_path = adb_path or str(device.adb_path)
            address = address or device.address
            device_name = device_name or device.name
            if ld_pid is None:
                ld_pid = (
                    (device.config or {}).get("extras", {}).get("ld", {}).get("pid")
                )

        normalized_name = (device_name).lower()

        # MuMu 序号
        if "mumu" in normalized_name:
            return ControllerHelper.get_index_by_adb_address(
                adb_path, address, device_name
            )

        # 雷电序号：需要 pid + ldconsole
        elif (
            ("雷电" in normalized_name)
            or ("ld" in normalized_name)
            or ("ldplayer" in normalized_name)
        ):
            if not ld_pid:
                return None
            ldconsole_path = ControllerHelper.build_ldconsole_path(adb_path)
            if not ldconsole_path:
                return None
            ld_output = ControllerHelper.get_ld_list_output(ldconsole_path)
            if not ld_output:
                return None
            return ControllerHelper.get_ld_index_from_list2(ld_output, ld_pid)

        return None

    @staticmethod
    def generate_emulator_launch_info(
        device_name: Optional[str],
        device_index: Optional[str],
        adb_path: Optional[str],
    ) -> tuple[str, str]:
        """
        根据设备名称、序号和adb路径生成 ADB 控制器（模拟器）运行路径和参数

        Args:
            device_name: 设备名称（如 "MuMu模拟器", "雷电模拟器"）
            device_index: 设备序号
            adb_path: ADB路径

        Returns:
            tuple[emulator_path, emulator_params]: 模拟器运行路径和参数
        """
        if not device_name or not device_index or not adb_path:
            return "", ""

        normalized_name = (device_name or "").lower()
        adb_path_obj = Path(adb_path)
        emulator_dir = adb_path_obj.parent

        # MuMu 模拟器
        if "mumu" in normalized_name:
            # 优先检测 MuMuNxMain.exe
            mumu_nx_main_path = emulator_dir / "MuMuNxMain.exe"
            if mumu_nx_main_path.exists():
                return str(mumu_nx_main_path), f"-v {device_index}"

            # 如果不存在，检测 MuMuPlayer.exe
            mumu_player_path = emulator_dir / "MuMuPlayer.exe"
            if mumu_player_path.exists():
                return str(mumu_player_path), f"-v {device_index}"

            # 都不存在，返回空
            return "", ""

        # 雷电模拟器
        elif "ld" in normalized_name:
            # 检测 LDPlayer.exe
            ldplayer_path = emulator_dir / "dnplayer.exe"
            if ldplayer_path.exists():
                return str(ldplayer_path), f"index={device_index}"

            # 不存在，返回空
            return "", ""

        return "", ""

    @staticmethod
    def close_win32_window(hwnd: int | str) -> bool:
        """通过窗口句柄 (hwnd) 关闭 Windows 窗口

        Args:
            hwnd: 窗口句柄，可以是整数或字符串

        Returns:
            bool: 是否成功发送关闭消息
        """
        if sys.platform != "win32":
            logger.warning("Win32 窗口关闭功能仅在 Windows 系统上支持")
            return False

        try:
            # 将 hwnd 转换为整数
            if isinstance(hwnd, str):
                hwnd_value = int(hwnd)
            else:
                hwnd_value = int(hwnd)
        except (TypeError, ValueError):
            logger.error(f"无效的窗口句柄: {hwnd}")
            return False

        if hwnd_value <= 0:
            logger.warning(f"窗口句柄无效: {hwnd_value}")
            return False

        try:
            import ctypes

            # 定义 Windows API 常量
            WM_CLOSE = 0x0010
            user32 = ctypes.windll.user32

            # 检查窗口是否存在
            if not user32.IsWindow(hwnd_value):
                logger.warning(f"窗口句柄 {hwnd_value} 对应的窗口不存在")
                return False

            # 首先尝试使用 PostMessageW 发送 WM_CLOSE 消息（异步，不会阻塞）
            # PostMessageW 返回非零值表示成功
            result = user32.PostMessageW(hwnd_value, WM_CLOSE, 0, 0)
            if result:
                logger.info(f"成功发送关闭消息到窗口 {hwnd_value} (使用 PostMessageW)")
                return True
            else:
                # PostMessageW 失败（返回 0），尝试使用 SendMessageW（同步，会等待窗口响应）
                logger.debug(f"PostMessageW 失败，尝试使用 SendMessageW")
                # SendMessageW 的返回值取决于窗口处理消息的方式，对于 WM_CLOSE 通常是 0
                # 但我们需要通过 GetLastError 检查是否真的出错
                user32.SendMessageW(hwnd_value, WM_CLOSE, 0, 0)
                # 检查窗口是否还存在（如果窗口正常关闭，应该不存在了）
                if not user32.IsWindow(hwnd_value):
                    logger.info(f"成功关闭窗口 {hwnd_value} (使用 SendMessageW)")
                    return True
                else:
                    logger.warning(f"无法关闭窗口 {hwnd_value}，窗口仍然存在")
                    return False

        except Exception as exc:
            logger.error(f"关闭 Win32 窗口失败: {exc}", exc_info=True)
            return False
