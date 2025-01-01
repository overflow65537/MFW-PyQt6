import os
from typing import Union
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from qfluentwidgets import (
    FluentIconBase,
    pyqtSignal,
    SwitchButton,
    IndicatorPosition,
    SettingCard,
)
from ..utils.tool import Read_Config, Save_Config
from ..utils.logger import logger


class SwitchSettingCardCustom(SettingCard):
    """自定义切换设置卡片"""

    checkedChanged = pyqtSignal(bool)

    def __init__(
        self,
        icon: Union[str, QIcon, FluentIconBase],
        title: str,
        target: str,
        content: str = "",
        parent=None,
    ):
        super().__init__(icon, title, content, parent)
        self.target = target
        self.switchButton = SwitchButton(self.tr("Off"), self, IndicatorPosition.RIGHT)

        # 将切换按钮添加到布局
        self.hBoxLayout.addWidget(self.switchButton, 0, Qt.AlignmentFlag.AlignRight)
        self.hBoxLayout.addSpacing(16)

        # 读取初始状态并设置切换按钮状态
        self.initialize_switch_button()

        # 连接信号和槽
        self.switchButton.checkedChanged.connect(self._onCheckedChanged)

    def initialize_switch_button(self):
        """初始化切换按钮的状态"""
        try:
            config_path = os.path.join(
                os.getcwd(), "config", "custom_setting_config.json"
            )
            data = Read_Config(config_path)
            initial_state = data.get(self.target, False)  # 默认为 False（关闭状态）
            self.switchButton.setChecked(initial_state)
        except FileNotFoundError:
            # 如果文件不存在，将切换按钮设置为默认关闭状态
            self.switchButton.setChecked(False)
            Save_Config(
                os.path.join(os.getcwd(), "config", "custom_setting_config.json"),
                {self.target: False},
            )

    def _onCheckedChanged(self, isChecked: bool):
        """处理切换按钮状态变化"""
        try:
            config_path = os.path.join(
                os.getcwd(), "config", "custom_setting_config.json"
            )
            data = Read_Config(config_path)
            data[self.target] = isChecked
            Save_Config(config_path, data)
            self.checkedChanged.emit(isChecked)  # 发出信号通知状态变化
        except Exception as e:
            logger.info(f"保存设置时出错: {e}")
