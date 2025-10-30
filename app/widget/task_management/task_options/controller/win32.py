"""Win32 控制器选项模块

提供 Win32 控制器的特定选项界面。
"""

from qfluentwidgets import ComboBox, LineEdit, BodyLabel
from PySide6.QtWidgets import QVBoxLayout
from .._mixin_base import MixinBase


class Win32ControllerMixin(MixinBase):
    """Win32 控制器选项 Mixin
    
    提供 Win32 控制器的选项界面，包括：
    - 窗口句柄 (HWND)
    - 应用路径、启动参数、超时
    - Win32 截图方法下拉框
    - Win32 输入方法下拉框
    
    继承自 MixinBase，获得通用的类型提示，避免 Pylance 报错。
    运行时 `self` 指向 OptionWidget 实例，可访问其所有属性/方法。
    """
    
    def _show_win32_options(self, saved_options: dict):
        """显示 Win32 特定选项
        
        Args:
            saved_options: 保存的选项字典（已展平）
        """
        text_options = [
            ("hwnd", self.tr("Window Handle (HWND)"), "", self.tr("Window handle identifier")),
            ("app_path", self.tr("Application Path"), "", self.tr("Path to application executable")),
            ("app_launch_args", self.tr("Application Launch Args"), "", self.tr("Arguments for launching application")),
            ("app_launch_timeout", self.tr("Application Launch Timeout (ms)"), "10000", self.tr("Time to wait for application startup")),
        ]
        
        for obj_name, label_text, default_value, tooltip_text in text_options:
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
            
            self.controller_specific_options_layout.addLayout(v_layout)
        
        # Win32 截图方法下拉框
        self._add_win32_screenshot_method_option(saved_options)
        
        # Win32 输入方法下拉框
        self._add_win32_input_method_option(saved_options)
    
    def _add_win32_screenshot_method_option(self, saved_options: dict):
        """添加 Win32 截图方法下拉框
        
        Args:
            saved_options: 保存的选项字典（已展平）
        """
        v_layout = QVBoxLayout()
        v_layout.setObjectName("win32_screenshot_method_layout")
        
        label = BodyLabel(self.tr("Win32 Screenshot Method"))
        label.setStyleSheet("font-weight: bold;")
        
        combo = ComboBox()
        combo.setObjectName("win32_screenshot_method")
        combo.setMaximumWidth(400)
        
        # Win32 截图方法选项
        screenshot_methods = [
            ("GDI", "1"),
            ("FramePool", "2"),
            ("DXGI_DesktopDup", "4"),
        ]
        
        for method_name, method_value in screenshot_methods:
            combo.addItem(method_name)
            combo.setItemData(combo.count() - 1, method_value)
        
        # 设置当前值,默认为 "1" (GDI)
        current_value = str(self._get_option_value(saved_options, "win32_screenshot_method", "1"))
        combo.blockSignals(True)  # 阻止信号，避免初始化时触发保存
        for i in range(combo.count()):
            if combo.itemData(i) == current_value:
                combo.setCurrentIndex(i)
                break
        combo.blockSignals(False)
        
        combo.currentIndexChanged.connect(lambda: self._save_current_options())
        
        v_layout.addWidget(label)
        v_layout.addWidget(combo)
        self.controller_specific_options_layout.addLayout(v_layout)
    
    def _add_win32_input_method_option(self, saved_options: dict):
        """添加 Win32 输入方法下拉框
        
        Args:
            saved_options: 保存的选项字典（已展平）
        """
        v_layout = QVBoxLayout()
        v_layout.setObjectName("win32_input_method_layout")
        
        label = BodyLabel(self.tr("Win32 Input Method"))
        label.setStyleSheet("font-weight: bold;")
        
        combo = ComboBox()
        combo.setObjectName("win32_input_method")
        combo.setMaximumWidth(400)
        
        # Win32 输入方法选项
        input_methods = [
            ("Seize", "1"),
            ("SendMessage", "2"),
        ]
        
        for method_name, method_value in input_methods:
            combo.addItem(method_name)
            combo.setItemData(combo.count() - 1, method_value)
        
        # 设置当前值,默认为 "1" (Seize)
        current_value = str(self._get_option_value(saved_options, "win32_input_method", "1"))
        combo.blockSignals(True)  # 阻止信号，避免初始化时触发保存
        for i in range(combo.count()):
            if combo.itemData(i) == current_value:
                combo.setCurrentIndex(i)
                break
        combo.blockSignals(False)
        
        combo.currentIndexChanged.connect(lambda: self._save_current_options())
        
        v_layout.addWidget(label)
        v_layout.addWidget(combo)
        self.controller_specific_options_layout.addLayout(v_layout)
