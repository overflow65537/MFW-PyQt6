from typing import Dict, Any
from PySide6.QtWidgets import QWidget, QVBoxLayout
from app.core.core import ServiceCoordinator


class BaseSettingWidget(QWidget):
    """
    设置组件的基类，提供公共属性和方法
    """

    def __init__(
        self,
        service_coordinator: ServiceCoordinator,
        parent_layout: QVBoxLayout,
        parent=None,
    ):
        super().__init__(parent)
        self.service_coordinator = service_coordinator
        self.parent_layout = parent_layout
        self.current_config: Dict[str, Any] = {}
        self._syncing = False

    def _toggle_description(self, visible: bool) -> None:
        """切换描述区域的显示/隐藏（由宿主提供）"""
        pass

    def tr(
        self, sourceText: str, /, disambiguation: str | None = ..., n: int = ...
    ) -> str:
        """翻译方法（由宿主提供）"""
        return sourceText

    def _clear_options(self) -> None:
        """清空选项区域（由宿主提供）"""
        pass

    def create_settings(self) -> None:
        """创建设置UI（子类实现）"""
        raise NotImplementedError("子类必须实现 create_settings 方法")

