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
        container_layout.setContentsMargins(5, 5, 5, 5)
        container_layout.setSpacing(5)
        parent_layout.addLayout(container_layout)

        # 创建下拉框 - 使用垂直布局
        label_text = config["label"]
        if label_text.startswith("$"):
            pass
        label = BodyLabel(label_text)
        # 移除固定宽度，让标签自然显示
        container_layout.addWidget(label)

        combo = ComboBox()
        combo.addItems(config["options"])
        container_layout.addWidget(combo)

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
        # 创建控件容器布局
        container_layout = QVBoxLayout()
        container_layout.setContentsMargins(5, 5, 5, 5)
        container_layout.setSpacing(5)
        parent_layout.addLayout(container_layout)

        # 处理标签，移除可能的$符号
        label_text = config["label"]
        if label_text.startswith("$"):
            pass
        label = BodyLabel(label_text)
        # 移除固定宽度，让标签自然显示
        container_layout.addWidget(label)

        # 检查是否有inputs数组（input类型的选项）
        if "inputs" in config:
            # 对于input类型，为每个input项创建独立的输入框
            parent_config[key] = {}

            for input_item in config["inputs"]:
                # 创建子容器
                input_container = QVBoxLayout()
                input_container.setContentsMargins(10, 5, 10, 5)
                container_layout.addLayout(input_container)

                # 处理input项的标签
                input_label_text = input_item.get("label", input_item.get("name", ""))
                if input_label_text.startswith("$"):
                    pass
                input_label = BodyLabel(input_label_text)
                input_container.addWidget(input_label)

                # 创建输入框
                input_line_edit = LineEdit()
                if "default" in input_item:
                    input_line_edit.setText(str(input_item["default"]))
                input_container.addWidget(input_line_edit)

                # 保存引用，使用input的name作为键
                input_name = input_item.get("name", "input")
                if key not in self.widgets:
                    self.widgets[key] = {}
                self.widgets[key][input_name] = input_line_edit

                # 初始化配置
                parent_config[key][input_name] = input_line_edit.text()

                # 连接信号
                input_line_edit.textChanged.connect(
                    lambda text, k=key, input_name=input_name, p_conf=parent_config: self._on_input_item_changed(
                        k, input_name, text, p_conf
                    )
                )
        else:
            # 普通的单行输入框
            line_edit = LineEdit()
            if "default" in config:
                line_edit.setText(config["default"])

            container_layout.addWidget(line_edit)

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

    def _on_input_item_changed(self, key, input_name, text, parent_config):
        """处理input类型中单个输入项的变化"""
        if key in parent_config and isinstance(parent_config[key], dict):
            parent_config[key][input_name] = text
            # 自动保存选项
            self._auto_save_options()

    def _on_combobox_changed(self, key, value, config, parent_config, child_layout):
        """下拉框值改变处理"""
        # 更新配置
        parent_config["value"] = value

        # 清空子控件
        self._clear_layout(child_layout)

        # 检查是否需要加载子控件 - 优先使用children属性（新方式）
        if "children" in config and value in config["children"]:
            child_config = config["children"][value]
            # 为子控件创建唯一键
            child_key = f"{key}_child"

            if child_config["type"] == "combobox":
                self._create_combobox(
                    child_key, child_config, child_layout, parent_config["children"]
                )
            elif child_config["type"] == "lineedit":
                self._create_lineedit(
                    child_key, child_config, child_layout, parent_config["children"]
                )

        # 自动保存选项（在子控件创建完成后）
        self._auto_save_options()

    def _on_lineedit_changed(self, key, text, parent_config):
        """输入框值改变处理"""
        parent_config[key] = text
        # 自动保存选项
        self._auto_save_options()

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

    def _auto_save_options(self):
        """自动保存当前选项"""
        # 检查是否有service_coordinator和option_service
        if hasattr(self, "service_coordinator") and hasattr(self.service_coordinator, "option_service"):  # type: ignore
            try:
                # 获取当前所有配置
                all_config = self.get_config()
                # 调用OptionService的update_options方法保存选项
                self.service_coordinator.option_service.update_options(all_config)  # type: ignore
            except Exception as e:
                # 如果保存失败，记录错误但不影响用户操作
                from app.utils.logger import logger

                logger.error(f"自动保存选项失败: {e}")

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
                        if "children" in value:
                            # 优先使用children属性
                            if (
                                "children" in field_config
                                and combo_value in field_config["children"]
                            ):
                                child_structure = {
                                    f"{key}_child": field_config["children"][
                                        combo_value
                                    ]
                                }
                                # 使用get方法安全地获取children，不存在时提供默认空字典
                                self._apply_config(
                                    value["children"],
                                    child_structure,
                                    current_config.get("children", {}),
                                )

                elif field_config["type"] == "lineedit":
                    # 处理输入框配置
                    if key in self.widgets:
                        # 检查是否是input类型（有inputs数组）
                        if "inputs" in field_config and isinstance(value, dict):
                            # 处理input类型的多个输入项
                            if isinstance(self.widgets[key], dict):
                                for input_name, input_value in value.items():
                                    if input_name in self.widgets[key]:
                                        self.widgets[key][input_name].setText(
                                            str(input_value)
                                        )
                        else:
                            # 普通的单行输入框
                            self.widgets[key].setText(str(value))
