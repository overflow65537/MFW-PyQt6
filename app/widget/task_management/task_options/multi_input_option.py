"""多输入项选项模块

提供多输入项选项的创建和管理。
"""

import re
from qfluentwidgets import BodyLabel, LineEdit, ToolTipFilter, ToolTipPosition
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout
from app.utils.logger import logger
from ._mixin_base import MixinBase


class MultiInputOptionMixin(MixinBase):
    """多输入项选项 Mixin
    
    继承自 MixinBase，获得通用的类型提示，避免 Pylance 报错。
    运行时 `self` 指向 OptionWidget 实例，可访问其所有属性/方法。
    
    提供包含多个输入框的选项创建功能：
    - 主标题（带图标和描述）
    - 多个子输入项（每个有独立标签和描述）
    - 输入验证（正则表达式）
    - 数据类型转换（string/int）
    - 自动保存
    
    依赖的宿主类方法/属性：
    - self.option_area_layout
    - self.icon_loader
    - self._save_current_options (在 ConfigHelperMixin 中)
    - self.service_coordinator
    """
    
    def _add_multi_input_option(
        self,
        option_name: str,
        option_config: dict,
        item,
        parent_option_name: str | None = None,
        insert_index: int | None = None,
    ):
        """添加多输入项选项

        用于创建包含多个输入框的选项，如"自定义关卡"

        Args:
            option_name: 选项名称
            option_config: 选项配置，必须包含 inputs 数组
            item: 当前任务项（TaskItem）
            parent_option_name: 父级选项名（作为嵌套选项时使用）
            insert_index: 插入位置索引（作为嵌套选项时使用）
        """
        saved_data = item.task_option.get(option_name, {})
        # multi_input 选项的值应该是字典，如果不是则重置为空字典
        if not isinstance(saved_data, dict):
            saved_data = {}
            logger.warning(f"选项 '{option_name}' 的值不是字典，已重置为空字典")
        
        main_description = option_config.get("description", "")
        main_label = option_config.get("label", option_name)
        icon_path = option_config.get("icon", "")

        # 创建主布局
        main_layout = QVBoxLayout()
        if parent_option_name:
            main_layout.setObjectName(
                f"{parent_option_name}__nested__{option_name}_layout"
            )
        else:
            main_layout.setObjectName(f"{option_name}_layout")

        # 创建主标题区域
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(5)

        # 添加图标（如果存在）
        icon = self.icon_loader.load_icon(icon_path, size=16)
        if not icon.isNull():
            icon_label = BodyLabel()
            icon_label.setPixmap(icon.pixmap(16, 16))
            title_layout.addWidget(icon_label)

        # 添加主标题（加粗）
        title_label = BodyLabel(main_label)
        title_label.setStyleSheet("font-weight: bold;")
        title_layout.addWidget(title_label)

        main_layout.addLayout(title_layout)

        # 设置主标题的工具提示
        if main_description:
            title_label.setToolTip(main_description)
            title_label.installEventFilter(
                ToolTipFilter(title_label, 0, ToolTipPosition.TOP)
            )

        # 创建各个输入框
        need_save = False
        for input_config in option_config.get("inputs", []):
            input_name = input_config.get("name")
            input_label = input_config.get("label", input_name)
            input_description = input_config.get("description", "")
            default_value = input_config.get("default", "")
            verify_pattern = input_config.get("verify", "")
            pipeline_type = input_config.get("pipeline_type", "string")

            # 获取当前值
            current_value = saved_data.get(input_name, default_value)
            
            # 如果需要转换为整数
            if pipeline_type == "int" and isinstance(current_value, str):
                try:
                    current_value = int(current_value) if current_value else 0
                    if input_name in saved_data:
                        saved_data[input_name] = current_value
                        need_save = True
                except ValueError:
                    logger.warning(f"无法将 '{current_value}' 转换为整数，保持原值")

            # 创建输入项布局
            input_layout = QVBoxLayout()

            # 子标题（不加粗）
            label_layout = QHBoxLayout()
            label_layout.setContentsMargins(0, 0, 0, 0)
            label_layout.setSpacing(5)

            label = BodyLabel(input_label)
            label_layout.addWidget(label)

            input_layout.addLayout(label_layout)

            # 创建输入框
            line_edit = LineEdit()
            line_edit.setText(str(current_value))
            line_edit.setPlaceholderText(f"默认: {default_value}")
            line_edit.setObjectName(f"{option_name}${input_name}")
            line_edit.setProperty("pipeline_type", pipeline_type)

            # 添加输入验证
            if verify_pattern:

                def create_validator(pattern, edit_widget):
                    def validate():
                        text = edit_widget.text()
                        if text and not re.match(pattern, text):
                            edit_widget.setStyleSheet("border: 1px solid red;")
                        else:
                            edit_widget.setStyleSheet("")

                    return validate

                line_edit.textChanged.connect(create_validator(verify_pattern, line_edit))

            input_layout.addWidget(line_edit)

            # 设置工具提示
            if input_description:
                label.setToolTip(input_description)
                label.installEventFilter(ToolTipFilter(label, 0, ToolTipPosition.TOP))
                line_edit.setToolTip(input_description)
                line_edit.installEventFilter(
                    ToolTipFilter(line_edit, 0, ToolTipPosition.TOP)
                )

            # 连接保存信号
            line_edit.textChanged.connect(lambda: self._save_current_options())

            main_layout.addLayout(input_layout)

        # 如果修正了数据类型，立即保存
        if need_save:
            item.task_option[option_name] = saved_data
            self.service_coordinator.modify_task(item)
            logger.info(f"已修正选项 '{option_name}' 的数据类型")

        # 添加到选项区域（支持指定插入位置）
        if insert_index is not None:
            self.option_area_layout.insertLayout(insert_index, main_layout)
        else:
            self.option_area_layout.addLayout(main_layout)
