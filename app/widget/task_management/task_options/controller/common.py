"""控制器通用选项模块

提供所有控制器类型共享的通用选项。
"""

from qfluentwidgets import LineEdit, BodyLabel
from PySide6.QtWidgets import QVBoxLayout
from .._mixin_base import MixinBase


class ControllerCommonMixin(MixinBase):
    """控制器通用选项 Mixin
    
    提供所有控制器类型共享的选项，包括：
    - GPU 选择
    - 启动前程序及参数
    - 启动后程序及参数
    
    继承自 MixinBase，获得通用的类型提示，避免 Pylance 报错。
    运行时 `self` 指向 OptionWidget 实例，可访问其所有属性/方法。
    
    注意：使用 controller_common_options_layout 而非 controller_specific_options_layout
    """
    
    def _show_controller_common_options(self, saved_options: dict):
        """显示控制器通用选项
        
        Args:
            saved_options: 保存的选项字典（已展平）
        """
        options = [
            ("gpu_selection", self.tr("GPU Selection"), "", self.tr("GPU device to use")),
            ("pre_launch_program", self.tr("Pre-Launch Program"), "", self.tr("Program to run before starting")),
            ("pre_launch_program_args", self.tr("Pre-Launch Program Args"), "", self.tr("Arguments for pre-launch program")),
            ("post_launch_program", self.tr("Post-Launch Program"), "", self.tr("Program to run after starting")),
            ("post_launch_program_args", self.tr("Post-Launch Program Args"), "", self.tr("Arguments for post-launch program")),
        ]
        
        for obj_name, label_text, default_value, tooltip_text in options:
            v_layout = QVBoxLayout()
            v_layout.setObjectName(f"{obj_name}_layout")
            
            label = BodyLabel(label_text)
            line_edit = LineEdit()
            line_edit.setObjectName(obj_name)
            
            # 阻止信号，避免初始化时触发保存
            line_edit.blockSignals(True)
            line_edit.setText(str(self._get_option_value(saved_options, obj_name, default_value)))
            line_edit.blockSignals(False)
            
            line_edit.setToolTip(tooltip_text)
            label.setToolTip(tooltip_text)
            
            # 连接信号
            line_edit.textChanged.connect(lambda: self._save_current_options())
            
            v_layout.addWidget(label)
            v_layout.addWidget(line_edit)
            
            self.controller_common_options_layout.addLayout(v_layout)
