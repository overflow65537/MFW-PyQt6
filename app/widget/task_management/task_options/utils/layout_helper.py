"""布局清理辅助工具

提供布局和控件的清理功能。
"""

from .._mixin_base import MixinBase


class LayoutHelperMixin(MixinBase):
    """布局辅助方法 Mixin
    
    继承自 MixinBase，获得通用的类型提示，避免 Pylance 报错。
    运行时 `self` 指向 OptionWidget 实例，可访问其所有属性/方法。
    
    提供布局清空等工具方法。
    """
    
    def _clear_layout(self, layout):
        """递归清空布局中的所有控件
        
        Args:
            layout: 要清空的布局对象
        """
        if layout is None:
            return
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())
    
    def _clear_options(self):
        """清空选项区域
        
        清空 option_area_layout 中的所有控件。
        需要子类定义 self.option_area_layout。
        """
        self._clear_layout(self.option_area_layout)
