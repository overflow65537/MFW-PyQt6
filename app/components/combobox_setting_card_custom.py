from typing import Union
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from qfluentwidgets import SettingCard, FluentIconBase, ComboBox
from ..utils.tool import (
    Read_Config,
    Save_Config,
    access_nested_dict,
    find_key_by_value,
    rewrite_contorller,
    delete_contorller,
)
from ..utils.logger import logger


class ComboBoxSettingCardCustom(SettingCard):
    """自定义ComboBox设置卡片"""

    def __init__(
        self,
        icon: Union[str, QIcon, FluentIconBase],
        title,
        path,
        target: list = None,
        controller=None,
        controller_type=None,
        content=None,
        texts=None,
        parent=None,
        mode: str = None,
        mapping: dict = None,
    ):
        """
        初始化自定义ComboBox设置卡片。

        :param icon: 图标
        :param title: 标题
        :param path: 目标路径
        :param target: 目标键
        :param controller: 控制器
        :param controller_type: 控制器类型
        :param content: 内容
        :param texts: 选项文本
        :param parent: 父级
        :param mode: 模式（如setting, custom, interface_setting）
        :param mapping: 映射表
        """
        super().__init__(icon, title, content, parent)
        self.path = path
        self.target = target
        self.mode = mode
        self.mapping = mapping
        self.controller = controller
        self.controller_type = controller_type

        # 创建ComboBox并添加到布局
        self.comboBox = ComboBox(self)
        self.hBoxLayout.addWidget(self.comboBox, 0, Qt.AlignmentFlag.AlignRight)
        self.hBoxLayout.addSpacing(16)

        # 添加文本项到ComboBox
        self.comboBox.addItems(texts)

        # 读取配置并设置当前选项
        self.set_current_text()

        # 连接选项改变信号
        self.comboBox.currentIndexChanged.connect(self._onCurrentIndexChanged)

    def set_current_text(self):
        """根据模式设置ComboBox的当前文本。"""
        try:
            data = Read_Config(self.path)
            if self.mode == "setting":
                value = access_nested_dict(data, self.target)
                if value in self.mapping:
                    current_text = self.mapping[value]
                else:
                    current_text = self.mapping.get(0)
            elif self.mode == "custom":
                current_text = access_nested_dict(data, self.target)
            elif self.mode == "interface_setting":
                value = rewrite_contorller(data, self.controller, self.controller_type)
                current_text = self.mapping.get(
                    value, self.tr("default") if value is None else value
                )
            else:
                current_text = ""

            self.comboBox.setCurrentText(current_text)
        except Exception as e:
            logger.warning(f"读取配置时出错: {e}")
            self.comboBox.setCurrentText("")  # 设置为空文本或默认值

    def _onCurrentIndexChanged(self):
        """处理ComboBox当前索引变化的事件。"""
        text = self.comboBox.text()
        data = Read_Config(self.path)

        if self.mode == "setting":
            result = find_key_by_value(self.mapping, text)
            access_nested_dict(data, self.target, value=result)
        elif self.mode == "custom":
            access_nested_dict(data, self.target, value=text)
        elif self.mode == "interface_setting":
            result = find_key_by_value(self.mapping, text)
            if result == 0:
                delete_contorller(data, self.controller, self.controller_type)
            else:
                rewrite_contorller(data, self.controller, self.controller_type, result)

        Save_Config(self.path, data)
