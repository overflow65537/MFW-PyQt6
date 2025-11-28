
import re

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PySide6.QtCore import Qt
from qfluentwidgets import LineEdit, BodyLabel, ToolTipFilter
from app.utils.logger import logger

class LineEditGenerator:
    """
    输入框生成器
    负责输入框的创建、配置和信号处理
    """

    def __init__(self, host):
        """
        初始化输入框生成器
        :param host: 宿主组件，需要包含widgets、child_layouts等属性
        """
        self.host = host

    def create_lineedit(self, key, config, parent_layout, parent_config):
        """创建输入框"""
        # 创建控件容器
        container_widget = QWidget()
        container_layout = QVBoxLayout(container_widget)
        container_layout.setContentsMargins(5, 5, 5, 5)
        container_layout.setSpacing(5)
        parent_layout.addWidget(container_widget)

        # 创建标签和图标容器
        label_container = QHBoxLayout()
        label_container.setSpacing(5)
        
        # 处理标签，移除可能的$符号
        label_text = config["label"]
        label = BodyLabel(label_text)
        # 移除固定宽度，让标签自然显示
        
        # 添加标签到容器
        label_container.addWidget(label)
        
        # 将整个标签容器添加到主布局
        container_layout.addLayout(label_container)
        
        # 为选项标题添加tooltip（选项层级）
        if "description" in config:
            filter = ToolTipFilter(label)
            label.installEventFilter(filter)
            label.setToolTip(config["description"])

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
                # 创建input项的标签
                input_label = BodyLabel(input_label_text)
                input_container.addWidget(input_label)

                # 创建输入框
                input_line_edit = LineEdit()
                
                # 检查是否有验证规则配置
                if "verify" in input_item:
                    verify_pattern = input_item["verify"]
                    try:
                        # 创建验证器函数
                        def create_validator(pattern):
                            def validate():
                                text = input_line_edit.text()
                                if text and not re.match(pattern, text):
                                    # 验证失败，设置错误状态
                                    input_line_edit.setError(True)
                                else:
                                    # 验证成功，清除错误状态
                                    input_line_edit.setError(False)
                            
                            return validate

                        # 连接文本变化信号到验证器
                        input_line_edit.textChanged.connect(create_validator(verify_pattern))
                    except Exception as e:
                        # 如果验证规则设置失败，记录错误但不影响输入框的创建
                        logger.error(f"设置输入验证规则失败: {verify_pattern}, 错误: {e}")
                if "default" in input_item:
                    input_line_edit.setText(str(input_item["default"]))
                input_container.addWidget(input_line_edit)
                
                # 为输入框控件添加tooltip（选项内部层级）
                if "description" in input_item:
                    filter = ToolTipFilter(input_line_edit)
                    input_line_edit.installEventFilter(filter)
                    input_line_edit.setToolTip(input_item["description"])
                elif "description" in config:
                    # 如果input_item没有自己的description，继承父级的
                    filter = ToolTipFilter(input_line_edit)
                    input_line_edit.installEventFilter(filter)
                    input_line_edit.setToolTip(config["description"])

                # 保存引用，使用input的name作为键
                input_name = input_item.get("name", "input")
                if key not in self.host.widgets:
                    self.host.widgets[key] = {}
                self.host.widgets[key][input_name] = input_line_edit

                # 初始化配置
                parent_config[key][input_name] = input_line_edit.text()

                # 连接信号
                input_line_edit.textChanged.connect(
                    lambda text, k=key, input_name=input_name, p_conf=parent_config, widget=input_line_edit: self._on_input_item_changed(
                        k, input_name, text, p_conf, widget=widget
                    )
                )
        else:
            # 普通的单行输入框
            line_edit = LineEdit()
            
            # 检查是否有验证规则配置
            if "verify" in config:
                verify_pattern = config["verify"]
                try:
                    # 创建验证器函数
                    def create_validator(pattern):
                        def validate():
                            text = line_edit.text()
                            if text and not re.match(pattern, text):
                                # 验证失败，设置错误状态
                                line_edit.setError(True)
                            else:
                                # 验证成功，清除错误状态
                                line_edit.setError(False)
                        
                        return validate

                    # 连接文本变化信号到验证器
                    line_edit.textChanged.connect(create_validator(verify_pattern))
                except Exception as e:
                    # 如果验证规则设置失败，记录错误但不影响输入框的创建
                    logger.error(f"设置输入验证规则失败: {verify_pattern}, 错误: {e}")
            if "default" in config:
                line_edit.setText(config["default"])

            container_layout.addWidget(line_edit)
            
            # 检查是否需要隐藏整个输入框行
            if "visible" in config and not config["visible"]:
                # 隐藏整个容器
                container_widget.setVisible(False)
            
            # 为输入框控件添加tooltip（选项内部层级）
            if "description" in config:
                filter = ToolTipFilter(line_edit)
                line_edit.installEventFilter(filter)
                line_edit.setToolTip(config["description"])

            # 保存引用
            self.host.widgets[key] = line_edit

            # 初始化配置
            parent_config[key] = line_edit.text()

            # 连接信号（用户交互时保存配置）
            line_edit.textChanged.connect(
                lambda text, k=key, p_conf=parent_config: self._on_lineedit_changed(
                    k, text, p_conf, save_config=True, widget=line_edit
                )
            )

    def _on_input_item_changed(self, key, input_name, text, parent_config, widget=None):
        """处理input类型中单个输入项的变化"""
        # 检查验证状态，如果验证失败则拒绝更新
        if widget and hasattr(widget, 'isError') and widget.isError():
            return
            
        if key in parent_config and isinstance(parent_config[key], dict):
            parent_config[key][input_name] = text
            # 自动保存选项
            self._auto_save_options()

    def _on_lineedit_changed(self, key, text, parent_config, save_config=True, widget=None):
        """输入框值改变处理
        
        :param save_config: 是否保存配置，默认为True。初始化时可以设置为False避免保存默认值
        :param widget: 输入框控件，用于检查验证状态
        """
        # 检查验证状态，如果验证失败则拒绝更新
        if widget and hasattr(widget, 'isError') and widget.isError():
            return
            
        parent_config[key] = text
        # 自动保存选项，只有当save_config为True且未禁用自动保存时才保存
        if save_config and (not hasattr(self.host, "_disable_auto_save") or not self.host._disable_auto_save):
            self._auto_save_options()

    def _auto_save_options(self):
        """自动保存当前选项"""
        # 检查是否禁用了自动保存
        if hasattr(self.host, "_disable_auto_save") and self.host._disable_auto_save:
            return
            
        # 检查是否有service_coordinator和option_service
        if hasattr(self.host, "service_coordinator") and hasattr(self.host.service_coordinator, "option_service"):  # type: ignore
            try:
                # 获取当前所有配置
                all_config = self.host.get_config()
                # 调用OptionService的update_options方法保存选项
                self.host.service_coordinator.option_service.update_options(all_config)  # type: ignore
            except Exception as e:
                # 如果保存失败，记录错误但不影响用户操作
                logger.error(f"自动保存选项失败: {e}")