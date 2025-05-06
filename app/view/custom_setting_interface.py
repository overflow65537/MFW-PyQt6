import os
from typing import Any, Literal
from qfluentwidgets import SettingCardGroup, ScrollArea, ExpandLayout
from qfluentwidgets import FluentIcon as FIF
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QLabel

from ..common.style_sheet import StyleSheet
from ..components.line_edit_card import LineEditCard
from ..components.combobox_setting_card_custom import ComboBoxSettingCardCustom
from ..components.switch_setting_card_custom import SwitchSettingCardCustom
from ..utils.tool import Read_Config, Save_Config
from ..utils.logger import logger


class CustomSettingInterface(ScrollArea):
    """自定义设置界面"""

    def __init__(self, parent=None):

        super().__init__(parent=parent)
        self.scrollWidget = QWidget()
        self.expandLayout = ExpandLayout(self.scrollWidget)

        # 设置标签
        self.settingLabel = QLabel(self.tr("Custom Setting"), self)

        self.CustomSettingGroup = SettingCardGroup(
            self.tr("Setting"), self.scrollWidget
        )
        self.custom_path = os.path.join(os.getcwd(), "config", "custom_setting.json")
        self.config_path = os.path.join(
            os.getcwd(), "config", "custom_setting_config.json"
        )
        if os.path.exists(self.custom_path):
            logger.info("加载自定义设置")
            self.config_init()
            self.option_init()
        self.__initWidget()

    def __initWidget(self):
        """初始化界面组件"""
        self.resize(1000, 800)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setViewportMargins(0, 80, 0, 20)
        self.setWidget(self.scrollWidget)
        self.setWidgetResizable(True)
        self.setObjectName("customsettingInterface")

        # 初始化样式表
        self.scrollWidget.setObjectName("scrollWidget")
        self.settingLabel.setObjectName("settingLabel")
        StyleSheet.SETTING_INTERFACE.apply(self)

        # 初始化布局
        self.__initLayout()

    def __initLayout(self):
        """初始化布局设置"""
        self.settingLabel.move(36, 30)
        # 添加设置卡片组到布局
        self.expandLayout.setSpacing(28)
        self.expandLayout.setContentsMargins(36, 10, 36, 0)
        self.expandLayout.addWidget(self.CustomSettingGroup)

    def CreateOption(self, option_dict: dict):
        """根据选项字典创建对应的设置项"""
        option_type = option_dict["optiontype"]
        option_name = option_dict["optionname"]
        text = option_dict["text"]
        logger.debug(f"创建{option_name}选项卡")

        if option_type == "combox":
            self.combox = ComboBoxSettingCardCustom(
                icon=FIF.FILTER,
                title=text["title"],
                content=text["content"],
                texts=option_dict["optioncontent"],
                target=[option_name],
                path=os.path.join(os.getcwd(), "config", "custom_setting_config.json"),
                mode="custom",
                parent=self.CustomSettingGroup,
            )
            self.CustomSettingGroup.addSettingCard(self.combox)

        elif option_type == "lineedit":
            initial_text = self.get_initial_text(option_name)
            self.lineedit = LineEditCard(
                holderText=initial_text,
                icon=FIF.EDIT,
                title=text["title"],
                content=text["content"],
                parent=self.CustomSettingGroup,
                target=option_name,
                num_only=False,
            )
            self.CustomSettingGroup.addSettingCard(self.lineedit)

        elif option_type == "switch":
            self.Switch = SwitchSettingCardCustom(
                icon=FIF.POWER_BUTTON,
                title=text["title"],
                content=text["content"],
                target=option_name,
                parent=self.CustomSettingGroup,
            )
            self.CustomSettingGroup.addSettingCard(self.Switch)

    def get_initial_text(self, option_name) -> Any | Literal[""]:
        """获取选项的初始文本"""
        return Read_Config(self.config_path).get(option_name, "")

    def config_init(self):
        """初始化配置文件"""
        if not os.path.exists(self.config_path):
            dicts = {}
            config = Read_Config(self.custom_path)
            for key, value in config.items():
                dicts[value["optionname"]] = value.get("optioncontent", "")
            Save_Config(self.config_path, dicts)

    def option_init(self):
        """初始化选项"""

        config = Read_Config(self.custom_path)
        logger.debug(f"{config}")
        for _, option in config.items():
            self.CreateOption(option)
