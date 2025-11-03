"""控制器通用选项模块

提供所有控制器类型共享的通用选项。
"""

from qfluentwidgets import LineEdit, BodyLabel, ComboBox
from PySide6.QtWidgets import QVBoxLayout
from .._mixin_base import MixinBase
from app.utils.gpu_cache import gpu_cache
from app.utils.logger import logger


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
        # 先显示 GPU 选择下拉框
        self._show_gpu_selection(saved_options)
        
        # 其他选项使用 LineEdit
        options = [
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
    
    def _show_gpu_selection(self, saved_options: dict):
        """显示 GPU 选择下拉框
        
        Args:
            saved_options: 保存的选项字典（已展平）
        """
        v_layout = QVBoxLayout()
        v_layout.setObjectName("gpu_selection_layout")
        
        label = BodyLabel(self.tr("GPU Selection"))
        combo = ComboBox()
        combo.setObjectName("gpu")
        combo.setMaximumWidth(400)
        
        # 添加基础选项（CPU 和 Auto），确保即使出现错误也有可用选项
        combo.addItem("CPU")
        combo.setItemData(combo.count() - 1, -2)
        
        combo.addItem(self.tr("Auto"))
        combo.setItemData(combo.count() - 1, -1)
        
        # 从缓存获取 GPU 信息（已在启动时初始化，不会卡顿）
        try:
            gpu_info = gpu_cache.get_gpu_info()
            if gpu_info:
                logger.debug(f"从缓存获取 GPU 设备: {gpu_info}")
                for gpu_id, gpu_name in sorted(gpu_info.items()):
                    combo.addItem(f"GPU {gpu_id}: {gpu_name}")
                    combo.setItemData(combo.count() - 1, gpu_id)
        except Exception as e:
            logger.warning(f"获取 GPU 信息时出现异常: {e}")
        
        # 设置当前值，默认为 -1 (Auto)
        saved_gpu = self._get_option_value(saved_options, "gpu", -1)
        
        # 确保是整数类型
        if isinstance(saved_gpu, str):
            try:
                saved_gpu = int(saved_gpu)
            except (ValueError, TypeError):
                saved_gpu = -1
        
        combo.blockSignals(True)
        for i in range(combo.count()):
            if combo.itemData(i) == saved_gpu:
                combo.setCurrentIndex(i)
                break
        combo.blockSignals(False)
        
        combo.setToolTip(self.tr("GPU device to use for inference acceleration"))
        label.setToolTip(self.tr("GPU device to use for inference acceleration"))
        
        # 连接信号
        combo.currentIndexChanged.connect(lambda: self._save_current_options())
        
        v_layout.addWidget(label)
        v_layout.addWidget(combo)
        
        self.controller_common_options_layout.addLayout(v_layout)
