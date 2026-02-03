from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget, QHBoxLayout
from qfluentwidgets import (
    BodyLabel,
    ComboBox,
    SimpleCardWidget,
    TransparentPushButton,
    TransparentDropDownPushButton,
    RoundMenu,
    Action,
    FluentIcon as FIF,
)


class StartBarWidget(QWidget):
    """启动栏组件
    
    多开模式：支持显示当前配置的运行状态
    """
    
    # 信号：配置状态变更
    config_status_changed = Signal(str, bool)  # config_id, is_running
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_config_id: str = ""
        self._running_configs: set[str] = set()
        
        self._init_start_bar()
        self.start_bar_main_layout = QHBoxLayout(self)
        self.start_bar_main_layout.addWidget(self.start_bar)

    def _init_start_bar(self):
        """初始化启动栏"""
        # 启动/停止按钮（合并为一个）
        self.run_button = TransparentPushButton(self.tr("Start"), self, FIF.PLAY)
        self._is_running = False

        # 启动栏总体布局
        self.start_bar = SimpleCardWidget()
        self.start_bar.setClickEnabled(False)
        self.start_bar.setBorderRadius(8)

        self.start_bar_layout = QHBoxLayout(self.start_bar)
        self.start_bar_layout.addWidget(self.run_button)

    def set_current_config(self, config_id: str):
        """设置当前配置ID，并更新按钮状态"""
        self._current_config_id = config_id
        self._update_button_for_config(config_id)

    def set_config_running(self, config_id: str, is_running: bool):
        """设置配置的运行状态"""
        if is_running:
            self._running_configs.add(config_id)
        else:
            self._running_configs.discard(config_id)
        
        # 如果是当前配置，更新按钮状态
        if config_id == self._current_config_id:
            self._update_button_for_config(config_id)
        
        self.config_status_changed.emit(config_id, is_running)

    def is_config_running(self, config_id: str) -> bool:
        """检查配置是否正在运行"""
        return config_id in self._running_configs

    def _update_button_for_config(self, config_id: str):
        """根据配置的运行状态更新按钮"""
        is_running = config_id in self._running_configs
        self._is_running = is_running
        
        if is_running:
            self.run_button.setText(self.tr("Stop"))
            self.run_button.setIcon(FIF.CLOSE)
        else:
            self.run_button.setText(self.tr("Start"))
            self.run_button.setIcon(FIF.PLAY)
        
        self.run_button.setEnabled(True)

    def get_running_configs(self) -> set[str]:
        """获取所有正在运行的配置"""
        return self._running_configs.copy()
