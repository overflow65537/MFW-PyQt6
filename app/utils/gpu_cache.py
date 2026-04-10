"""
GPU 信息缓存模块

在程序启动时获取 GPU 信息并缓存，避免每次使用时重新检测导致卡顿。
"""

import platform
import os
import subprocess
import shutil
from typing import Dict, Optional

from app.utils.logger import logger

# Windows 系统下隐藏命令行窗口的标志
if platform.system() == "Windows":
    CREATE_NO_WINDOW = subprocess.CREATE_NO_WINDOW
else:
    CREATE_NO_WINDOW = 0


def _parse_gpu_names_from_lines(output: str) -> Dict[int, str]:
    """将按行输出的 GPU 名称解析为顺序字典。"""
    gpu_info: Dict[int, str] = {}
    for index, line in enumerate(output.splitlines()):
        gpu_name = line.strip()
        if gpu_name:
            gpu_info[index] = gpu_name
    return gpu_info


def _get_windows_gpu_info() -> Dict[int, str]:
    """通过 PowerShell WMI/CIM Cmdlet 获取 Windows GPU 信息。"""

    def _resolve_powershell() -> list[str] | None:
        candidates = [
            os.path.join(
                os.environ.get("SystemRoot", r"C:\Windows"),
                "System32",
                "WindowsPowerShell",
                "v1.0",
                "powershell.exe",
            ),
            shutil.which("pwsh"),
            shutil.which("powershell"),
        ]

        for candidate in candidates:
            if candidate and os.path.isfile(candidate):
                return [candidate]

        logger.warning("未找到 PowerShell 可执行文件，无法通过 WMI/CIM 获取 GPU 信息")
        return None

    pwsh = _resolve_powershell()
    if pwsh is None:
        return {}

    powershell_commands = [
        pwsh
        + [
            "-NoProfile",
            "-NonInteractive",
            "-Command",
            "Get-CimInstance -ClassName Win32_VideoController | Select-Object -ExpandProperty Name",
        ],
        pwsh
        + [
            "-NoProfile",
            "-NonInteractive",
            "-Command",
            "Get-WmiObject -Class Win32_VideoController | Select-Object -ExpandProperty Name",
        ],
    ]

    for command in powershell_commands:
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                creationflags=CREATE_NO_WINDOW,
                timeout=10,
            )
        except subprocess.TimeoutExpired:
            logger.warning("PowerShell 查询 GPU 信息超时")
            continue

        if result.returncode != 0:
            continue

        gpu_info = _parse_gpu_names_from_lines(result.stdout)
        if gpu_info:
            return gpu_info

    return {}


def get_gpu_info() -> Dict[int, str]:
    """
    获取系统中所有 GPU 设备的信息

    Returns:
        Dict[int, str]: GPU 信息字典，键为 GPU ID，值为 GPU 名称
    """
    gpu_info = {}

    system = platform.system().lower()

    def _resolve_command(command_name: str) -> list[str] | None:
        """Resolve command to absolute executable path to avoid PATH hijacking."""
        if platform.system().lower() == "windows" and command_name.lower() == "wmic":
            system_root = os.environ.get("SystemRoot", r"C:\Windows")
            wmic_path = os.path.join(system_root, "System32", "wbem", "wmic.exe")
            if os.path.isfile(wmic_path):
                return [wmic_path]

        resolved = shutil.which(command_name)
        if not resolved:
            logger.debug("命令不可用，跳过 GPU 检测命令: %s", command_name)
            return None
        return [resolved]

    def _run_command(args: list[str]) -> subprocess.CompletedProcess[str] | None:
        try:
            return subprocess.run(
                args,
                capture_output=True,
                text=True,
                timeout=10,
                creationflags=CREATE_NO_WINDOW,
            )
        except Exception as e:
            logger.debug("执行 GPU 检测命令失败 %s: %s", args[0] if args else "?", e)
            return None

    try:
        if system == "windows":
            gpu_info = _get_windows_gpu_info()

        elif system == "darwin":  # macOS
            # macOS 系统使用 system_profiler 命令获取 GPU 信息
            base = _resolve_command("system_profiler")
            if base is None:
                return gpu_info
            result = _run_command(base + ["SPDisplaysDataType"])
            if result is None:
                return gpu_info
            if result.returncode == 0:
                lines = result.stdout.strip().split("\n")
                gpu_id = 0
                for line in lines:
                    if line.strip().startswith("Chipset Model:"):
                        gpu_name = line.split(":", 1)[1].strip()
                        gpu_info[gpu_id] = gpu_name
                        gpu_id += 1

        elif system == "linux":
            # Linux 系统使用 lspci 命令获取 GPU 信息
            base = _resolve_command("lspci")
            if base is None:
                return gpu_info
            result = _run_command(
                base + ["-nn", "-d", "10de:,1002:,1022:"]  # NVIDIA, AMD, ATI
            )
            if result is None:
                return gpu_info
            if result.returncode == 0:
                lines = result.stdout.strip().split("\n")
                for i, line in enumerate(lines):
                    # 解析输出，提取 GPU 名称
                    if "VGA compatible controller" in line or "3D controller" in line:
                        # 示例：01:00.0 VGA compatible controller [0300]: NVIDIA Corporation GP106 [GeForce GTX 1060 6GB] [10de:1c03] (rev a1)
                        gpu_name = line.split(": ", 3)[-1].split(" [", 1)[0]
                        gpu_info[i] = gpu_name

    except Exception as e:
        logger.error(f"获取 GPU 信息失败: {e}")

    return gpu_info


class GPUInfoCache:
    """GPU 信息缓存类（单例模式）"""

    _instance: Optional["GPUInfoCache"] = None
    _gpu_info: Optional[Dict[int, str]] = None
    _initialized: bool = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def initialize(self):
        """初始化 GPU 信息缓存

        在程序启动时调用一次，获取并缓存 GPU 信息
        """
        if self._initialized:
            logger.debug("GPU 信息已初始化，跳过")
            return

        logger.info("开始初始化 GPU 信息缓存...")

        try:

            self._gpu_info = get_gpu_info()
            self._initialized = True

            if self._gpu_info:
                logger.info(
                    f"✅ GPU 信息缓存成功，检测到 {len(self._gpu_info)} 个 GPU 设备"
                )
                for gpu_id, gpu_name in sorted(self._gpu_info.items()):
                    logger.debug(f"  GPU {gpu_id}: {gpu_name}")
            else:
                logger.info("⚠️ 未检测到 GPU 设备，将只使用 CPU/Auto 模式")
                self._gpu_info = {}

        except Exception as e:
            logger.error(f"❌ GPU 信息初始化失败: {e}")
            self._gpu_info = {}
            self._initialized = True

    def get_gpu_info(self) -> Dict[int, str]:
        """获取缓存的 GPU 信息

        Returns:
            Dict[int, str]: GPU 信息字典，键为 GPU ID，值为 GPU 名称
        """
        if not self._initialized:
            logger.warning("GPU 信息未初始化，现在初始化...")
            self.initialize()

        return self._gpu_info or {}

    def is_initialized(self) -> bool:
        """检查是否已初始化

        Returns:
            bool: 是否已初始化
        """
        return self._initialized

    def refresh(self):
        """刷新 GPU 信息

        强制重新获取 GPU 信息（通常不需要调用）
        """
        logger.info("强制刷新 GPU 信息...")
        self._initialized = False
        self._gpu_info = None
        self.initialize()


# 创建全局单例
gpu_cache = GPUInfoCache()
