"""动画效果 Mixin 模块

提供描述区域的展开/收缩动画效果。
使用两段式动画：透明度 + 尺寸变化，提供流畅的视觉体验。
"""

from typing import TYPE_CHECKING, Any, Optional
from PySide6.QtCore import QPropertyAnimation, QEasingCurve, QSequentialAnimationGroup
from PySide6.QtWidgets import QGraphicsOpacityEffect
from ._mixin_base import MixinBase

if TYPE_CHECKING:
    from PySide6.QtWidgets import QSplitter, QWidget


class AnimationMixin(MixinBase):
    """动画效果 Mixin
    
    提供描述区域的显示/隐藏动画功能：
    - 显示动画：淡入(150ms) → 展开(200ms)
    - 隐藏动画：收缩(200ms) → 淡出(150ms)
    
    使用 QGraphicsOpacityEffect 实现透明度动画
    使用自定义属性动画实现 QSplitter 尺寸动画
    
    依赖的宿主类属性：
    - self.splitter: QSplitter 分割器
    - self.description_splitter_widget: QWidget 描述区域容器
    
    动态创建的实例属性（运行时）：
    - _desc_animation: 描述区域显示动画
    - _desc_fade_animation: 描述区域淡出动画
    - _splitter_anim_helper: QSplitter 动画辅助对象
    - _splitter_anim_obj: 动画属性对象
    - _splitter_animation: QSplitter 尺寸动画
    """
    
    if TYPE_CHECKING:
        # 动态创建的实例属性（用于类型检查）
        _desc_animation: Optional[QSequentialAnimationGroup]
        _desc_fade_animation: Optional[QPropertyAnimation]
        _splitter_anim_helper: Optional[Any]
        _splitter_anim_obj: Optional[Any]
        _splitter_animation: Optional[QPropertyAnimation]
        # 宿主类提供的属性
        splitter: "QSplitter"
        description_splitter_widget: "QWidget"
    
    def _toggle_description(self, visible=None):
        """切换描述区域的显示/隐藏（使用两段动画）
        
        显示时：先显示widget → 淡入透明度 → 展开尺寸
        隐藏时：收缩尺寸 → 淡出透明度 → 隐藏widget
        
        Args:
            visible: True显示，False隐藏，None切换当前状态
        """
        if visible is None:
            # 切换当前状态
            visible = not self.description_splitter_widget.isVisible()

        # 如果状态没有变化，直接返回
        current_visible = self.description_splitter_widget.isVisible()
        if visible == current_visible:
            return

        # 获取当前尺寸
        total_height = self.splitter.height()
        current_sizes = self.splitter.sizes()
        
        if visible:
            # ========== 显示动画（两段式）========== #
            # 先显示widget
            self.description_splitter_widget.show()
            
            # 确保有透明度效果
            if not self.description_splitter_widget.graphicsEffect():
                opacity_effect = QGraphicsOpacityEffect()
                self.description_splitter_widget.setGraphicsEffect(opacity_effect)
                opacity_effect.setOpacity(0.0)
            else:
                opacity_effect = self.description_splitter_widget.graphicsEffect()
            
            # 此时 opacity_effect 必定不为 None，因为上面已经确保创建了
            assert opacity_effect is not None, "透明度效果未正确初始化"
            
            # 计算目标尺寸：选项区域70%，描述区域30%
            target_option_size = int(total_height * 0.7)
            target_description_size = int(total_height * 0.3)
            
            # 创建序列动画组
            sequence = QSequentialAnimationGroup()
            
            # 阶段1：淡入动画（150ms）
            fade_in = QPropertyAnimation(opacity_effect, b"opacity")
            fade_in.setDuration(150)
            fade_in.setStartValue(0.0)
            fade_in.setEndValue(1.0)
            fade_in.setEasingCurve(QEasingCurve.Type.InOutQuad)
            
            # 阶段2：尺寸展开动画（200ms）
            # 使用回调来处理尺寸动画
            def start_expand():
                self._animate_splitter(
                    current_sizes[0], target_option_size,
                    1, target_description_size,
                    duration=200
                )
            
            fade_in.finished.connect(start_expand)
            sequence.addAnimation(fade_in)
            
            # 保存引用并启动
            if hasattr(self, '_desc_animation'):
                if self._desc_animation:
                    self._desc_animation.stop()
            self._desc_animation = sequence
            sequence.start()
            
        else:
            # ========== 隐藏动画（两段式）========== #
            target_option_size = total_height - 1
            target_description_size = 1
            
            # 确保有透明度效果
            if not self.description_splitter_widget.graphicsEffect():
                opacity_effect = QGraphicsOpacityEffect()
                self.description_splitter_widget.setGraphicsEffect(opacity_effect)
                opacity_effect.setOpacity(1.0)
            else:
                opacity_effect = self.description_splitter_widget.graphicsEffect()
            
            # 此时 opacity_effect 必定不为 None
            assert opacity_effect is not None, "透明度效果未正确初始化"
            
            # 阶段1：尺寸收缩动画（200ms）
            def on_shrink_finished():
                # opacity_effect 在闭包中捕获，必定不为 None
                assert opacity_effect is not None
                # 阶段2：淡出动画（150ms）
                fade_out = QPropertyAnimation(opacity_effect, b"opacity")
                fade_out.setDuration(150)
                fade_out.setStartValue(1.0)
                fade_out.setEndValue(0.0)
                fade_out.setEasingCurve(QEasingCurve.Type.InOutQuad)
                fade_out.finished.connect(lambda: self.description_splitter_widget.hide())
                
                # 保存引用
                if hasattr(self, '_desc_fade_animation'):
                    self._desc_fade_animation = None
                self._desc_fade_animation = fade_out
                fade_out.start()
            
            self._animate_splitter(
                current_sizes[0], target_option_size,
                current_sizes[1], target_description_size,
                duration=200,
                on_finished=on_shrink_finished
            )
    
    def _animate_splitter(self, from_option, to_option, from_desc, to_desc, 
                          duration=300, on_finished=None):
        """使用平滑动画调整 QSplitter 的尺寸
        
        Args:
            from_option: 选项区域起始尺寸
            to_option: 选项区域目标尺寸
            from_desc: 描述区域起始尺寸
            to_desc: 描述区域目标尺寸
            duration: 动画持续时间（毫秒）
            on_finished: 动画完成后的回调函数
        """
        # 使用自定义属性动画实现
        class SplitterAnimation:
            def __init__(self, splitter, from_sizes, to_sizes):
                self.splitter = splitter
                self.from_sizes = from_sizes
                self.to_sizes = to_sizes
            
            def set_value(self, value):
                # value 从 0.0 到 1.0
                option_size = int(self.from_sizes[0] + (self.to_sizes[0] - self.from_sizes[0]) * value)
                desc_size = int(self.from_sizes[1] + (self.to_sizes[1] - self.from_sizes[1]) * value)
                self.splitter.setSizes([option_size, desc_size])
        
        # 创建动画对象
        anim_helper = SplitterAnimation(
            self.splitter, 
            [from_option, from_desc], 
            [to_option, to_desc]
        )
        
        # 保存引用避免被垃圾回收
        if not hasattr(self, '_splitter_anim_helper'):
            self._splitter_anim_helper = None
        self._splitter_anim_helper = anim_helper
        
        # 创建一个虚拟的 QObject 来承载动画
        from PySide6.QtCore import QObject, Property
        
        class AnimObject(QObject):
            def __init__(self, callback):
                super().__init__()
                self._value = 0.0
                self.callback = callback
            
            def get_value(self):
                return self._value
            
            def set_value(self, value):
                self._value = value
                self.callback(value)
            
            value = Property(float, get_value, set_value)
        
        anim_obj = AnimObject(anim_helper.set_value)
        
        # 保存引用
        if not hasattr(self, '_splitter_anim_obj'):
            self._splitter_anim_obj = None
        self._splitter_anim_obj = anim_obj
        
        # 创建属性动画
        animation = QPropertyAnimation(anim_obj, b"value")
        animation.setDuration(duration)
        animation.setStartValue(0.0)
        animation.setEndValue(1.0)
        animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        if on_finished:
            animation.finished.connect(on_finished)
        
        # 保存动画引用并启动
        if not hasattr(self, '_splitter_animation'):
            self._splitter_animation = None
        
        # 如果有正在运行的动画，先停止
        if self._splitter_animation:
            self._splitter_animation.stop()
        
        self._splitter_animation = animation
        animation.start()
