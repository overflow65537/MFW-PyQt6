import json
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from PySide6.QtCore import Qt
from qfluentwidgets import ComboBox, LineEdit, BodyLabel


class DynamicFormMixin:
    """
    动态表单生成器的Mixin组件
    提供动态生成表单和管理配置的功能
    可以集成到OptionWidget等UI组件中
    """

    def __init__(self):
        """初始化动态表单Mixin"""
        # 确保这些属性被初始化
        if not hasattr(self, "widgets"):
            self.widgets = {}
        if not hasattr(self, "child_layouts"):
            self.child_layouts = {}
        if not hasattr(self, "current_config"):
            self.current_config = {}
        if not hasattr(self, "config_structure"):
            self.config_structure = {}
        if not hasattr(self, "parent_layout"):
            self.parent_layout = None

    def update_form(self, form_structure, config=None):
        """
        更新表单结构和配置
        :param form_structure: 新的表单结构定义
        :param config: 可选的配置对象，用于设置表单的当前选择
        """
        # 保存新的表单结构
        self.config_structure = form_structure

        # 清空当前配置
        self.current_config = {}
        self.widgets = {}
        self.child_layouts = {}

        # 清空父布局
        if self.parent_layout:
            self._clear_layout(self.parent_layout)
        else:
            raise ValueError("parent_layout 未设置")

        # 生成新表单
        for key, config_item in form_structure.items():
            if config_item["type"] == "combobox":
                self._create_combobox(
                    key, config_item, self.parent_layout, self.current_config
                )
            elif config_item["type"] == "lineedit":
                self._create_lineedit(
                    key, config_item, self.parent_layout, self.current_config
                )

        # 如果提供了配置，则应用它
        if config:
            self._apply_config(config, self.config_structure, self.current_config)

    def get_config(self):
        """
        获取当前表单的配置
        :return: 当前选择的配置字典
        """
        return self.current_config

    def _create_combobox(self, key, config, parent_layout, parent_config):
        """创建下拉框"""
        # 创建控件容器布局
        container_layout = QVBoxLayout()
        container_layout.setContentsMargins(10, 10, 10, 10)
        container_layout.setSpacing(10)
        parent_layout.addLayout(container_layout)

        # 创建下拉框
        h_layout = QHBoxLayout()
        h_layout.setSpacing(15)
        # 处理标签，移除可能的$符号
        label_text = config['label']
        if label_text.startswith('$'):
            label_text = label_text[1:]
        label = BodyLabel(f"{label_text}:")
        label.setFixedWidth(100)
        combo = ComboBox()
        combo.addItems(config["options"])
        combo.setFixedWidth(200)

        h_layout.addWidget(label)
        h_layout.addWidget(combo)
        h_layout.addStretch()
        container_layout.addLayout(h_layout)

        # 创建子控件容器布局
        child_layout = QVBoxLayout()
        container_layout.addLayout(child_layout)

        # 保存引用
        self.widgets[key] = combo
        self.child_layouts[key] = child_layout

        # 初始化配置
        parent_config[key] = {"value": combo.currentText(), "children": {}}

        # 连接信号
        combo.currentTextChanged.connect(
            lambda value, current_key=key, current_config=config, current_parent_config=parent_config[
                key
            ]: self._on_combobox_changed(
                current_key, value, current_config, current_parent_config, child_layout
            )
        )

        # 触发初始加载
        self._on_combobox_changed(
            key, combo.currentText(), config, parent_config[key], child_layout
        )

    def _create_lineedit(self, key, config, parent_layout, parent_config):
        """创建输入框"""
        h_layout = QHBoxLayout()
        h_layout.setContentsMargins(10, 10, 10, 10)
        h_layout.setSpacing(15)
        # 处理标签，移除可能的$符号
        label_text = config['label']
        if label_text.startswith('$'):
            label_text = label_text[1:]
        label = BodyLabel(f"{label_text}:")
        label.setFixedWidth(100)
        line_edit = LineEdit()
        line_edit.setFixedWidth(200)
        if "default" in config:
            line_edit.setText(config["default"])

        h_layout.addWidget(label)
        h_layout.addWidget(line_edit)
        h_layout.addStretch()
        parent_layout.addLayout(h_layout)

        # 保存引用
        self.widgets[key] = line_edit

        # 初始化配置
        parent_config[key] = line_edit.text()

        # 连接信号
        line_edit.textChanged.connect(
            lambda text, k=key, p_conf=parent_config: self._on_lineedit_changed(
                k, text, p_conf
            )
        )

    def _on_combobox_changed(self, key, value, config, parent_config, child_layout):
        """下拉框值改变处理"""
        # 更新配置
        parent_config["value"] = value

        # 清空子控件
        self._clear_layout(child_layout)

        # 检查是否需要加载子控件
        if "conditional" in config and value in config["conditional"]:
            child_configs = config["conditional"][value]
            for child_key, child_conf in child_configs.items():
                # 为子控件创建唯一键
                child_full_key = f"{key}_{child_key}"

                if child_conf["type"] == "combobox":
                    self._create_combobox(
                        child_key, child_conf, child_layout, parent_config["children"]
                    )
                elif child_conf["type"] == "lineedit":
                    self._create_lineedit(
                        child_key, child_conf, child_layout, parent_config["children"]
                    )

    def _on_lineedit_changed(self, key, text, parent_config):
        """输入框值改变处理"""
        parent_config[key] = text

    def _clear_layout(self, layout):
        """清空布局中的所有控件"""
        while layout.count() > 0:
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
            else:
                child_layout = item.layout()
                if child_layout:
                    self._clear_layout(child_layout)

    def _apply_config(self, config, form_structure, current_config):
        """
        应用配置到表单
        :param config: 要应用的配置字典
        :param form_structure: 表单结构定义
        :param current_config: 当前配置字典
        """
        for key, value in config.items():
            if key in form_structure:
                field_config = form_structure[key]

                if field_config["type"] == "combobox":
                    # 处理下拉框配置
                    if isinstance(value, dict) and "value" in value:
                        combo_value = value["value"]
                        # 查找并设置下拉框的值
                        if key in self.widgets:
                            combo = self.widgets[key]
                            index = combo.findText(combo_value)
                            if index >= 0:
                                combo.setCurrentIndex(index)

                        # 递归应用子配置
                        if "children" in value and "conditional" in field_config:
                            if combo_value in field_config["conditional"]:
                                child_structure = field_config["conditional"][
                                    combo_value
                                ]
                                self._apply_config(
                                    value["children"],
                                    child_structure,
                                    current_config["children"],
                                )

                elif field_config["type"] == "lineedit":
                    # 处理输入框配置
                    if key in self.widgets:
                        self.widgets[key].setText(str(value))
