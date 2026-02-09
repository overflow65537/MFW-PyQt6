"""
流式布局组件 - 自动换行的布局管理器
"""
from PySide6.QtCore import Qt, QRect, QSize, QPoint
from PySide6.QtWidgets import QLayout, QLayoutItem, QSizePolicy, QWidget


class FlowLayout(QLayout):
    """流式布局，自动将子组件排列成多行，超出宽度时自动换行"""

    def __init__(self, parent: QWidget | None = None, margin: int = -1, h_spacing: int = 6, v_spacing: int = 6):
        """
        Args:
            parent: 父组件
            margin: 边距（-1 表示使用默认值）
            h_spacing: 水平间距
            v_spacing: 垂直间距
        """
        super().__init__(parent)
        self._h_spacing = h_spacing
        self._v_spacing = v_spacing
        self._items: list[QLayoutItem] = []
        
        if margin >= 0:
            self.setContentsMargins(margin, margin, margin, margin)

    def __del__(self):
        """析构函数，清理所有项"""
        item = self.takeAt(0)
        while item:
            item = self.takeAt(0)

    def addItem(self, item: QLayoutItem):
        """添加布局项"""
        self._items.append(item)

    def horizontalSpacing(self) -> int:
        """获取水平间距"""
        if self._h_spacing >= 0:
            return self._h_spacing
        return self._smart_spacing(QSizePolicy.ControlType.PushButton)

    def verticalSpacing(self) -> int:
        """获取垂直间距"""
        if self._v_spacing >= 0:
            return self._v_spacing
        return self._smart_spacing(QSizePolicy.ControlType.PushButton)

    def count(self) -> int:
        """返回布局项数量"""
        return len(self._items)

    def itemAt(self, index: int) -> QLayoutItem | None:
        """获取指定位置的布局项"""
        if 0 <= index < len(self._items):
            return self._items[index]
        return None

    def takeAt(self, index: int) -> QLayoutItem:
        """移除并返回指定位置的布局项"""
        if 0 <= index < len(self._items):
            return self._items.pop(index)
        return None  # type: ignore

    def expandingDirections(self) -> Qt.Orientation:
        """返回布局的扩展方向"""
        return Qt.Orientation(0)

    def hasHeightForWidth(self) -> bool:
        """是否有基于宽度计算高度的能力"""
        return True

    def heightForWidth(self, width: int) -> int:
        """根据宽度计算所需高度"""
        return self._do_layout(QRect(0, 0, width, 0), test_only=True)

    def setGeometry(self, rect: QRect):
        """设置布局的几何形状"""
        super().setGeometry(rect)
        self._do_layout(rect, test_only=False)

    def sizeHint(self) -> QSize:
        """返回推荐大小"""
        return self.minimumSize()

    def minimumSize(self) -> QSize:
        """返回最小大小"""
        size = QSize()
        for item in self._items:
            size = size.expandedTo(item.minimumSize())
        
        margins = self.contentsMargins()
        size += QSize(margins.left() + margins.right(), margins.top() + margins.bottom())
        return size

    def _smart_spacing(self, control_type: QSizePolicy.ControlType) -> int:
        """智能计算间距"""
        parent = self.parent()
        if parent is None:
            return -1
        # 简单返回默认间距
        return 6

    def _do_layout(self, rect: QRect, test_only: bool) -> int:
        """执行布局计算
        
        Args:
            rect: 可用区域
            test_only: 是否只是测试（不实际移动组件）
            
        Returns:
            计算出的高度
        """
        margins = self.contentsMargins()
        effective_rect = rect.adjusted(margins.left(), margins.top(), -margins.right(), -margins.bottom())
        
        x = effective_rect.x()
        y = effective_rect.y()
        line_height = 0
        
        h_space = self.horizontalSpacing()
        v_space = self.verticalSpacing()
        
        for item in self._items:
            widget = item.widget()
            if widget is None:
                continue
                
            space_x = h_space
            space_y = v_space
            
            next_x = x + item.sizeHint().width() + space_x
            
            # 如果超出右边界，换行
            if next_x - space_x > effective_rect.right() and line_height > 0:
                x = effective_rect.x()
                y = y + line_height + space_y
                next_x = x + item.sizeHint().width() + space_x
                line_height = 0
            
            if not test_only:
                item.setGeometry(QRect(QPoint(x, y), item.sizeHint()))
            
            x = next_x
            line_height = max(line_height, item.sizeHint().height())
        
        return y + line_height - rect.y() + margins.bottom()
