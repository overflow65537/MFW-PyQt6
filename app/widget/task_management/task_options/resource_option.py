"""资源槽位选项模块

提供资源槽位选项的显示和管理。
"""

from qfluentwidgets import ComboBox, BodyLabel
from PySide6.QtWidgets import QVBoxLayout
from pathlib import Path
import json
from app.utils.logger import logger
from app.utils.i18n_manager import get_interface_i18n
from ._mixin_base import MixinBase


class ResourceOptionMixin(MixinBase):
    """资源槽位选项 Mixin
    
    继承自 MixinBase，获得通用的类型提示，避免 Pylance 报错。
    运行时 `self` 指向 OptionWidget 实例，可访问其所有属性/方法。
    
    提供6个资源槽位下拉框的创建和管理：
    - 从 interface.json 读取资源列表
    - 创建6个资源槽位下拉框
    - 自动保存配置
    
    依赖的宿主类方法/属性：
    - self.option_area_layout
    - self._clear_options (在 LayoutHelperMixin 中)
    - self._save_current_options (在 ConfigHelperMixin 中)
    - self.task
    - self.tr (翻译函数)
    """
    
    def _show_resource_option(self, item):
        """显示资源选项 - 6个下拉框
        
        Args:
            item: TaskItem 对象
        """
        self._clear_options()
        
        # 获取 interface 配置（使用翻译后的数据）
        interface = getattr(self.task, "interface", None)
        if not interface:
            try:
                i18n = get_interface_i18n()
                interface = i18n.get_translated_interface()
            except Exception as e:
                logger.error(f"获取翻译后的 interface.json 失败: {e}")
                # 降级方案：直接加载原始 interface.json
                interface_path = Path.cwd() / "interface.json"
                if not interface_path.exists():
                    logger.warning("未找到 interface.json 文件")
                    return
                with open(interface_path, "r", encoding="utf-8") as f:
                    interface = json.load(f)
        
        # 获取资源列表
        resources = interface.get("resource", [])
        resource_options = [r.get("name", "") for r in resources if r.get("name")]
        
        # 如果没有资源配置，显示提示
        if not resource_options:
            label = BodyLabel(self.tr("No resource configuration found"))
            self.option_area_layout.addWidget(label)
            return
        
        # 获取当前保存的资源选项
        saved_options = item.task_option
        
        # 创建6个资源下拉框
        resource_fields = [
            ("resource_1", self.tr("Resource Slot 1")),
            ("resource_2", self.tr("Resource Slot 2")),
            ("resource_3", self.tr("Resource Slot 3")),
            ("resource_4", self.tr("Resource Slot 4")),
            ("resource_5", self.tr("Resource Slot 5")),
            ("resource_6", self.tr("Resource Slot 6")),
        ]
        
        for field_name, field_label in resource_fields:
            current_value = saved_options.get(field_name, "")
            
            # 创建垂直布局
            v_layout = QVBoxLayout()
            v_layout.setObjectName(f"{field_name}_layout")
            
            # 标签
            label = BodyLabel(field_label)
            label.setStyleSheet("font-weight: bold;")
            v_layout.addWidget(label)
            
            # 下拉框
            combo = ComboBox()
            combo.setObjectName(field_name)
            combo.addItems([""] + resource_options)  # 添加空选项
            if current_value:
                combo.setCurrentText(current_value)
            
            # 连接信号
            combo.currentTextChanged.connect(lambda: self._save_current_options())
            
            v_layout.addWidget(combo)
            self.option_area_layout.addLayout(v_layout)
