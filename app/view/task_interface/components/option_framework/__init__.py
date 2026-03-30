"""
选项框架模块
提供动态生成选项界面的框架
"""
from .option_form_widget import OptionFormWidget
from .speedrun_config_widget import SpeedrunConfigWidget
from .items import (
    OptionItemBase,
    OptionItemRegistry,
    TooltipComboBox,
    ComboBoxOptionItem,
    SwitchOptionItem,
    InputOptionItem,
    InputsOptionItem,
)

__all__ = [
    "OptionFormWidget",
    "SpeedrunConfigWidget",
    "OptionItemBase",
    "OptionItemRegistry",
    "TooltipComboBox",
    "ComboBoxOptionItem",
    "SwitchOptionItem",
    "InputOptionItem",
    "InputsOptionItem",
]
