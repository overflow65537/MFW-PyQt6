"""ADB 控制器选项模块

提供 ADB 控制器的特定选项界面。
"""

from qfluentwidgets import ComboBox, LineEdit, BodyLabel
from PySide6.QtWidgets import QVBoxLayout
from .._mixin_base import MixinBase


class AdbControllerMixin(MixinBase):
    """ADB 控制器选项 Mixin
    
    提供 ADB 控制器的选项界面，包括：
    - ADB 路径、连接地址
    - 模拟器启动路径、参数、超时
    - ADB 截图方法下拉框
    - ADB 输入方法下拉框
    - ADB config 隐藏字段
    
    继承自 MixinBase，获得通用的类型提示，避免 Pylance 报错。
    运行时 `self` 指向 OptionWidget 实例，可访问其所有属性/方法。
    """
    
    def _show_adb_options(self, saved_options: dict):
        """显示 ADB 特定选项
        
        在运行时，`self` 是 OptionWidget 实例（继承自 QWidget），
        因此 `self.tr()` 调用的是 QWidget.tr() 方法进行国际化翻译。
        
        Args:
            saved_options: 保存的选项字典（已展平）
        """
        # 文本输入框选项
        # 格式：(字段名, 标签文本, 默认值, 提示文本)
        text_options = [
            ("adb_path", self.tr("ADB Path"), None, self.tr("Path to adb executable")),
            ("adb_port", self.tr("ADB Connection Address"), None, self.tr("Device connection address (IP:Port or device ID)")),
            ("emulator_address", self.tr("Emulator Launch Path"), None, self.tr("Path to emulator executable for launching")),
            ("emulator_launch_args", self.tr("Emulator Launch Args"), "", self.tr("Arguments for launching emulator")),
            ("emulator_launch_timeout", self.tr("Emulator Launch Timeout (ms)"), "60000", self.tr("Time to wait for emulator startup")),
        ]
        
        for obj_name, label_text, default_value, tooltip_text in text_options:
            v_layout = QVBoxLayout()
            v_layout.setObjectName(f"{obj_name}_layout")
            
            label = BodyLabel(label_text)
            line_edit = LineEdit()
            line_edit.setObjectName(obj_name)
            # 如果 default_value 是 None，则使用空字符串
            actual_default = "" if default_value is None else default_value
            
            # 阻止信号，避免在初始化时触发保存
            line_edit.blockSignals(True)
            line_edit.setText(str(self._get_option_value(saved_options, obj_name, actual_default)))
            line_edit.blockSignals(False)
            
            line_edit.setToolTip(tooltip_text)
            label.setToolTip(tooltip_text)
            
            # 连接信号
            line_edit.textChanged.connect(lambda: self._save_current_options())
            
            v_layout.addWidget(label)
            v_layout.addWidget(line_edit)
            
            self.controller_specific_options_layout.addLayout(v_layout)
        
        # ADB 截图方法下拉框
        self._add_adb_screenshot_method_option(saved_options)
        
        # ADB 输入方法下拉框
        self._add_adb_input_method_option(saved_options)
        
        # 添加隐藏的 ADB config 字段（用于存储设备的额外配置信息）
        config_line_edit = LineEdit()
        config_line_edit.setObjectName("adb_config")
        config_line_edit.setVisible(False)  # 隐藏此字段
        # 从保存的选项中读取 config（JSON 字符串格式）
        config_value = str(self._get_option_value(saved_options, "adb_config", ""))
        if config_value:
            # 阻止信号，避免初始化时触发保存
            config_line_edit.blockSignals(True)
            config_line_edit.setText(config_value)
            config_line_edit.blockSignals(False)
        config_line_edit.textChanged.connect(lambda: self._save_current_options())
        self.controller_specific_options_layout.addWidget(config_line_edit)
    
    def _add_adb_screenshot_method_option(self, saved_options: dict):
        """添加 ADB 截图方法下拉框
        
        支持位掩码值的下拉框，包含特殊值处理逻辑。
        
        Args:
            saved_options: 保存的选项字典（已展平）
        """
        v_layout = QVBoxLayout()
        v_layout.setObjectName("adb_screenshot_method_layout")
        
        label = BodyLabel(self.tr("ADB Screenshot Method"))
        label.setStyleSheet("font-weight: bold;")
        
        combo = ComboBox()
        combo.setObjectName("adb_screenshot_method")
        combo.setMaximumWidth(400)
        
        # 截图方法选项 (位掩码值)
        screenshot_methods = [
            ("EncodeToFileAndPull", "1"),
            ("Encode", "2"),
            ("RawWithGzip", "4"),
            ("RawByNetcat", "8"),
            ("MinicapDirect", "16"),
            ("MinicapStream", "32"),
            ("EmulatorExtras", "64"),
        ]
        
        for method_name, method_value in screenshot_methods:
            combo.addItem(method_name)
            combo.setItemData(combo.count() - 1, method_value)
        
        # 获取原始保存的值
        original_value = self._get_option_value(saved_options, "adb_screenshot_method", "1")
        current_value = str(original_value)
        
        # 检查值是否在映射表中
        valid_values = [method_value for _, method_value in screenshot_methods]
        if current_value not in valid_values:
            # 值不在映射表中，存储原始值用于保存，显示时使用第一个选项
            combo.setProperty("original_value", current_value)
            current_value = "1"
        
        # 设置下拉框选中项
        combo.blockSignals(True)  # 阻止信号，避免初始化时触发保存
        for i in range(combo.count()):
            if combo.itemData(i) == current_value:
                combo.setCurrentIndex(i)
                break
        combo.blockSignals(False)
        
        # 连接信号：用户改变选择时标记为已修改
        def on_screenshot_changed():
            combo.setProperty("user_changed", True)
            self._save_current_options()
        
        combo.currentIndexChanged.connect(on_screenshot_changed)
        
        v_layout.addWidget(label)
        v_layout.addWidget(combo)
        self.controller_specific_options_layout.addLayout(v_layout)
    
    def _add_adb_input_method_option(self, saved_options: dict):
        """添加 ADB 输入方法下拉框
        
        支持位掩码值的下拉框，包含特殊值处理逻辑。
        
        Args:
            saved_options: 保存的选项字典（已展平）
        """
        v_layout = QVBoxLayout()
        v_layout.setObjectName("adb_input_method_layout")
        
        label = BodyLabel(self.tr("ADB Input Method"))
        label.setStyleSheet("font-weight: bold;")
        
        combo = ComboBox()
        combo.setObjectName("adb_input_method")
        combo.setMaximumWidth(400)
        
        # 输入方法选项 (位掩码值)
        input_methods = [
            ("AdbShell", "1"),
            ("MinitouchAndAdbKey", "2"),
            ("Maatouch", "4"),
            ("EmulatorExtras", "8"),
        ]
        
        for method_name, method_value in input_methods:
            combo.addItem(method_name)
            combo.setItemData(combo.count() - 1, method_value)
        
        # 获取原始保存的值
        original_value = self._get_option_value(saved_options, "adb_input_method", "1")
        current_value = str(original_value)
        
        # 检查值是否在映射表中
        valid_values = [method_value for _, method_value in input_methods]
        if current_value not in valid_values:
            # 值不在映射表中，存储原始值用于保存，显示时使用第一个选项
            combo.setProperty("original_value", current_value)
            current_value = "1"
        
        # 设置下拉框选中项
        combo.blockSignals(True)  # 阻止信号，避免初始化时触发保存
        for i in range(combo.count()):
            if combo.itemData(i) == current_value:
                combo.setCurrentIndex(i)
                break
        combo.blockSignals(False)
        
        # 连接信号：用户改变选择时标记为已修改
        def on_index_changed():
            combo.setProperty("user_changed", True)
            self._save_current_options()
        
        combo.currentIndexChanged.connect(on_index_changed)
        
        v_layout.addWidget(label)
        v_layout.addWidget(combo)
        self.controller_specific_options_layout.addLayout(v_layout)
