"""
GUI 辅助工具模块

此模块包含依赖 PySide6 的 GUI 相关辅助功能，仅供 GUI 界面使用。
CLI 模式下不应导入此模块。
"""

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPixmap
from app.utils.logger import logger
if TYPE_CHECKING:
    from app.core.core import ServiceCoordinator




class IconLoader:
    """图标加载器 - 仅供 GUI 使用
    
    提供图标加载和处理功能，支持多种路径格式。
    依赖 PySide6，不应在 CLI 模式下使用。
    """

    def __init__(self, service_coordinator: "ServiceCoordinator"):
        """初始化图标加载器
        
        Args:
            service_coordinator: 服务协调器实例，用于获取配置信息
        """
        self.service_coordinator = service_coordinator

    def load_icon(self, icon_path: str, size: int = 16) -> QIcon:
        """加载图标并转换为指定大小

        支持的路径格式:
        1. 相对路径 (./icon.png 或 icon.png) → 相对于 cwd
        2. {PROJECT_DIR}/icon.png → 替换为当前配置的 bundle 路径
        3. 绝对路径 → 直接使用

        Args:
            icon_path: 图标路径
            size: 图标大小（默认16x16）

        Returns:
            QIcon: 加载并调整大小后的图标，失败时返回空图标
        """
        if not icon_path:
            return QIcon()

        try:
            # 处理 {PROJECT_DIR} 占位符
            if "{PROJECT_DIR}" in icon_path:
                icon_path = self._resolve_project_dir(icon_path)
                if not icon_path:
                    return QIcon()

            # 解析路径
            full_path = self._resolve_path(icon_path)
            if not full_path:
                return QIcon()

            # 检查文件是否存在
            if not full_path.exists():
                logger.warning(f"图标文件不存在: {full_path}")
                return QIcon()

            # 加载并调整图标
            return self._load_and_scale_icon(full_path, size)

        except Exception as e:
            logger.error(f"加载图标时发生错误: {icon_path}, 错误: {e}")
            return QIcon()

    def _resolve_project_dir(self, icon_path: str) -> str:
        """解析 {PROJECT_DIR} 占位符
        
        Args:
            icon_path: 包含 {PROJECT_DIR} 的路径
            
        Returns:
            str: 替换后的路径，失败时返回空字符串
        """
        try:
            # 获取当前配置的 bundle 路径
            current_config = self.service_coordinator.config_service.get_current_config()
            if not current_config or not current_config.bundle:
                logger.warning("无法获取当前配置的 bundle 路径")
                return ""

            # bundle 格式: {name: {name: str, path: str}}
            # 取第一个 bundle 的 path
            bundle_data = next(iter(current_config.bundle.values()), None)
            if not bundle_data or "path" not in bundle_data:
                logger.warning("当前配置的 bundle 中没有 path 字段")
                return ""

            bundle_path = bundle_data["path"]
            # 替换占位符
            return icon_path.replace("{PROJECT_DIR}", bundle_path)

        except Exception as e:
            logger.error(f"解析 PROJECT_DIR 时发生错误: {e}")
            return ""

    def _resolve_path(self, icon_path: str) -> Path | None:
        """解析路径为绝对路径
        
        Args:
            icon_path: 图标路径（可以是相对或绝对）
            
        Returns:
            Path: 规范化后的绝对路径，失败时返回 None
        """
        try:
            path_obj = Path(icon_path)

            # 处理相对路径（包括 ./ 开头和纯文件名）
            if not path_obj.is_absolute():
                # 相对于 cwd
                full_path = Path.cwd() / path_obj
            else:
                # 绝对路径
                full_path = path_obj

            # 规范化路径
            return full_path.resolve()

        except Exception as e:
            logger.error(f"解析路径时发生错误: {icon_path}, 错误: {e}")
            return None

    def _load_and_scale_icon(self, path: Path, size: int) -> QIcon:
        """加载图标并调整大小
        
        Args:
            path: 图标文件的绝对路径
            size: 目标大小
            
        Returns:
            QIcon: 加载并调整大小后的图标，失败时返回空图标
        """
        try:
            # 加载图标
            pixmap = QPixmap(str(path))

            # 检查是否加载成功
            if pixmap.isNull():
                logger.warning(f"无法加载图标: {path}")
                return QIcon()

            # 调整大小（保持宽高比）
            if pixmap.width() != size or pixmap.height() != size:
                pixmap = pixmap.scaled(
                    size,
                    size,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )

            return QIcon(pixmap)

        except Exception as e:
            logger.error(f"加载和缩放图标时发生错误: {path}, 错误: {e}")
            return QIcon()


# 便捷函数：创建图标加载器实例
def create_icon_loader(service_coordinator: "ServiceCoordinator") -> IconLoader:
    """创建图标加载器实例
    
    Args:
        service_coordinator: 服务协调器实例
        
    Returns:
        IconLoader: 图标加载器实例
    """
    return IconLoader(service_coordinator)
