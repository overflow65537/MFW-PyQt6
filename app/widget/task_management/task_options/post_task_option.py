"""完成后设置选项模块

提供任务完成后的操作和通知方式选项。
"""

from qfluentwidgets import ComboBox, BodyLabel
from PySide6.QtWidgets import QVBoxLayout
from ._mixin_base import MixinBase


class PostTaskOptionMixin(MixinBase):
    """完成后设置选项 Mixin
    
    继承自 MixinBase，获得通用的类型提示，避免 Pylance 报错。
    运行时 `self` 指向 OptionWidget 实例，可访问其所有属性/方法。
    
    提供任务完成后的设置选项：
    - 完成后操作（退出程序、关机、休眠等）
    - 通知方式（系统通知、声音、邮件等）
    
    依赖的宿主类方法/属性：
    - self.option_area_layout
    - self._clear_options (在 LayoutHelperMixin 中)
    - self._save_current_options (在 ConfigHelperMixin 中)
    - self.tr (翻译函数)
    """
    
    def _show_post_task_setting_option(self, item):
        """显示完成后设置选项 - 2个下拉框
        
        Args:
            item: TaskItem 对象
        """
        self._clear_options()
        
        # 获取当前保存的选项
        saved_options = item.task_option
        
        # 第一个下拉框：完成后操作
        post_action_layout = QVBoxLayout()
        post_action_layout.setObjectName("post_action_layout")
        
        post_action_label = BodyLabel(self.tr("Action After Completion"))
        post_action_label.setStyleSheet("font-weight: bold;")
        post_action_layout.addWidget(post_action_label)
        
        post_action_combo = ComboBox()
        post_action_combo.setObjectName("post_action")
        post_action_combo.setMaximumWidth(400)  # 限制最大宽度
        post_action_options = [
            self.tr("None"),
            self.tr("Exit Program"),
            self.tr("Shutdown Computer"),
            self.tr("Hibernate Computer"),
            self.tr("Sleep Computer"),
        ]
        post_action_combo.addItems(post_action_options)
        
        current_action = saved_options.get("post_action", "")
        if current_action:
            post_action_combo.setCurrentText(current_action)
        
        post_action_combo.currentTextChanged.connect(lambda: self._save_current_options())
        
        post_action_layout.addWidget(post_action_combo)
        self.option_area_layout.addLayout(post_action_layout)
        
        # 第二个下拉框：通知方式
        notification_layout = QVBoxLayout()
        notification_layout.setObjectName("notification_layout")
        
        notification_label = BodyLabel(self.tr("Notification Method"))
        notification_label.setStyleSheet("font-weight: bold;")
        notification_layout.addWidget(notification_label)
        
        notification_combo = ComboBox()
        notification_combo.setObjectName("notification")
        notification_combo.setMaximumWidth(400)  # 限制最大宽度
        notification_options = [
            self.tr("None"),
            self.tr("System Notification"),
            self.tr("Sound Alert"),
            self.tr("Email Notification"),
            self.tr("Webhook"),
        ]
        notification_combo.addItems(notification_options)
        
        current_notification = saved_options.get("notification", "")
        if current_notification:
            notification_combo.setCurrentText(current_notification)
        
        notification_combo.currentTextChanged.connect(lambda: self._save_current_options())
        
        notification_layout.addWidget(notification_combo)
        self.option_area_layout.addLayout(notification_layout)
