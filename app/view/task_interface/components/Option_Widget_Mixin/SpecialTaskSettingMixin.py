"""
特殊任务设置 Mixin - 处理等待/启动程序/通知任务的选项界面
"""
from typing import Any, Dict, Callable

from PySide6.QtCore import Qt, QTime, QCoreApplication
from PySide6.QtWidgets import (
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QButtonGroup,
    QFormLayout,
)
from qfluentwidgets import (
    BodyLabel,
    SpinBox,
    LineEdit,
    TextEdit,
    SwitchButton,
    RadioButton,
    CheckBox,
    ComboBox,
    TimePicker,
    SimpleCardWidget,
)

from app.common.constants import (
    SPECIAL_TASK_WAIT,
    SPECIAL_TASK_RUN_PROGRAM,
    SPECIAL_TASK_NOTIFY,
)
from app.widget.PathLineEdit import PathLineEdit
from app.utils.logger import logger


def _tr(text: str) -> str:
    """翻译函数"""
    return QCoreApplication.translate("SpecialTaskSettingMixin", text)


class SpecialTaskSettingMixin:
    """特殊任务设置 Mixin
    
    为 OptionWidget 提供特殊任务（等待/启动程序/通知）的设置界面
    """
    
    # 子类需要提供的属性
    service_coordinator: Any
    option_page_layout: QVBoxLayout
    current_config: Dict[str, Any]
    
    def _init_special_task_settings(self):
        """初始化特殊任务设置（在 OptionWidget.__init__ 中调用）"""
        # 特殊任务设置组件的字典
        self.special_task_widgets: Dict[str, QWidget] = {}
        # 当前特殊任务类型
        self._current_special_type: str = ""
    
    def _clear_special_task_settings(self):
        """清除特殊任务设置组件"""
        self.special_task_widgets.clear()
        self._current_special_type = ""
    
    def _is_special_task_type(self, special_type: str) -> bool:
        """判断是否为特殊任务类型"""
        return special_type in (SPECIAL_TASK_WAIT, SPECIAL_TASK_RUN_PROGRAM, SPECIAL_TASK_NOTIFY)
    
    def _create_special_task_settings(self, special_type: str):
        """创建特殊任务设置界面"""
        self._current_special_type = special_type
        
        if special_type == SPECIAL_TASK_WAIT:
            self._create_wait_task_settings()
        elif special_type == SPECIAL_TASK_RUN_PROGRAM:
            self._create_run_program_settings()
        elif special_type == SPECIAL_TASK_NOTIFY:
            self._create_notify_settings()
    
    def _create_wait_task_settings(self):
        """创建等待任务设置界面"""
        # 主容器
        card = SimpleCardWidget()
        card.setBorderRadius(8)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(16, 16, 16, 16)
        card_layout.setSpacing(12)
        
        # 标题
        title = BodyLabel(_tr("Wait Settings"))
        title.setStyleSheet("font-weight: 600; font-size: 14px;")
        card_layout.addWidget(title)
        
        # 模式切换
        mode_layout = QHBoxLayout()
        mode_label = BodyLabel(_tr("Wait Mode:"))
        self.wait_mode_switch = SwitchButton()
        self.wait_mode_switch.setOnText(_tr("Scheduled"))
        self.wait_mode_switch.setOffText(_tr("Fixed"))
        
        # 从配置加载当前模式
        current_mode = self.current_config.get("wait_mode", "fixed")
        self.wait_mode_switch.setChecked(current_mode == "scheduled")
        
        mode_layout.addWidget(mode_label)
        mode_layout.addWidget(self.wait_mode_switch)
        mode_layout.addStretch()
        card_layout.addLayout(mode_layout)
        
        # 固定等待时间设置
        self.fixed_wait_widget = QWidget()
        fixed_layout = QFormLayout(self.fixed_wait_widget)
        fixed_layout.setContentsMargins(0, 0, 0, 0)
        
        self.wait_seconds_spin = SpinBox()
        self.wait_seconds_spin.setRange(1, 86400 * 7)  # 最多7天
        self.wait_seconds_spin.setValue(self.current_config.get("wait_seconds", 60))
        self.wait_seconds_spin.setSuffix(_tr(" seconds"))
        fixed_layout.addRow(_tr("Wait Duration:"), self.wait_seconds_spin)
        card_layout.addWidget(self.fixed_wait_widget)
        
        # 规则定时设置
        self.scheduled_wait_widget = QWidget()
        scheduled_layout = QVBoxLayout(self.scheduled_wait_widget)
        scheduled_layout.setContentsMargins(0, 0, 0, 0)
        scheduled_layout.setSpacing(8)
        
        # 规则类型选择
        rule_type_label = BodyLabel(_tr("Schedule Rule:"))
        scheduled_layout.addWidget(rule_type_label)
        
        self.schedule_rule_group = QButtonGroup()
        rule_options = [
            ("daily", _tr("Daily at specific time")),
            ("weekly", _tr("Weekly on specific day")),
            ("monthly", _tr("Monthly on specific day")),
        ]
        
        scheduled_config = self.current_config.get("scheduled_time") or {}
        current_rule = scheduled_config.get("rule", "daily")
        
        for rule_id, rule_text in rule_options:
            radio = RadioButton(rule_text)
            self.schedule_rule_group.addButton(radio)
            radio.setProperty("rule_id", rule_id)
            if rule_id == current_rule:
                radio.setChecked(True)
            scheduled_layout.addWidget(radio)
        
        # 时间选择
        time_layout = QHBoxLayout()
        time_label = BodyLabel(_tr("Time:"))
        self.schedule_time_picker = TimePicker()
        
        hour = scheduled_config.get("hour", 0)
        minute = scheduled_config.get("minute", 0)
        self.schedule_time_picker.setTime(QTime(hour, minute))
        
        time_layout.addWidget(time_label)
        time_layout.addWidget(self.schedule_time_picker)
        time_layout.addStretch()
        scheduled_layout.addLayout(time_layout)
        
        # 星期选择（用于每周）
        self.weekday_widget = QWidget()
        weekday_layout = QHBoxLayout(self.weekday_widget)
        weekday_layout.setContentsMargins(0, 0, 0, 0)
        weekday_label = BodyLabel(_tr("Day of Week:"))
        self.weekday_combo = ComboBox()
        weekdays = [
            _tr("Monday"), _tr("Tuesday"), _tr("Wednesday"),
            _tr("Thursday"), _tr("Friday"), _tr("Saturday"), _tr("Sunday")
        ]
        self.weekday_combo.addItems(weekdays)
        self.weekday_combo.setCurrentIndex(scheduled_config.get("weekday", 0))
        weekday_layout.addWidget(weekday_label)
        weekday_layout.addWidget(self.weekday_combo)
        weekday_layout.addStretch()
        scheduled_layout.addWidget(self.weekday_widget)
        
        # 日期选择（用于每月）
        self.monthday_widget = QWidget()
        monthday_layout = QHBoxLayout(self.monthday_widget)
        monthday_layout.setContentsMargins(0, 0, 0, 0)
        monthday_label = BodyLabel(_tr("Day of Month:"))
        self.monthday_spin = SpinBox()
        self.monthday_spin.setRange(1, 31)
        self.monthday_spin.setValue(scheduled_config.get("day", 1))
        monthday_layout.addWidget(monthday_label)
        monthday_layout.addWidget(self.monthday_spin)
        monthday_layout.addStretch()
        scheduled_layout.addWidget(self.monthday_widget)
        
        card_layout.addWidget(self.scheduled_wait_widget)
        
        # 初始化显示状态
        self._update_wait_mode_visibility()
        self._update_schedule_rule_visibility()
        
        # 连接信号
        self.wait_mode_switch.checkedChanged.connect(self._on_wait_mode_changed)
        self.wait_seconds_spin.valueChanged.connect(self._on_wait_option_changed)
        self.schedule_rule_group.buttonClicked.connect(self._on_schedule_rule_changed)
        self.schedule_time_picker.timeChanged.connect(self._on_wait_option_changed)
        self.weekday_combo.currentIndexChanged.connect(self._on_wait_option_changed)
        self.monthday_spin.valueChanged.connect(self._on_wait_option_changed)
        
        self.option_page_layout.addWidget(card)
        self.special_task_widgets["wait_card"] = card
    
    def _update_wait_mode_visibility(self):
        """更新等待模式的可见性"""
        is_scheduled = self.wait_mode_switch.isChecked()
        self.fixed_wait_widget.setVisible(not is_scheduled)
        self.scheduled_wait_widget.setVisible(is_scheduled)
    
    def _update_schedule_rule_visibility(self):
        """更新规则定时子选项的可见性"""
        current_rule = "daily"
        for btn in self.schedule_rule_group.buttons():
            if btn.isChecked():
                current_rule = btn.property("rule_id")
                break
        
        self.weekday_widget.setVisible(current_rule == "weekly")
        self.monthday_widget.setVisible(current_rule == "monthly")
    
    def _on_wait_mode_changed(self, checked: bool):
        """等待模式切换"""
        self._update_wait_mode_visibility()
        self._save_wait_task_options()
    
    def _on_schedule_rule_changed(self):
        """规则定时类型变化"""
        self._update_schedule_rule_visibility()
        self._save_wait_task_options()
    
    def _on_wait_option_changed(self):
        """等待选项变化"""
        self._save_wait_task_options()
    
    def _save_wait_task_options(self):
        """保存等待任务选项"""
        is_scheduled = self.wait_mode_switch.isChecked()
        
        options = {
            "wait_mode": "scheduled" if is_scheduled else "fixed",
            "wait_seconds": self.wait_seconds_spin.value(),
        }
        
        if is_scheduled:
            # 获取当前选中的规则
            current_rule = "daily"
            for btn in self.schedule_rule_group.buttons():
                if btn.isChecked():
                    current_rule = btn.property("rule_id")
                    break
            
            time = self.schedule_time_picker.getTime()
            scheduled_config = {
                "rule": current_rule,
                "hour": time.hour(),
                "minute": time.minute(),
            }
            
            if current_rule == "weekly":
                scheduled_config["weekday"] = self.weekday_combo.currentIndex()
            elif current_rule == "monthly":
                scheduled_config["day"] = self.monthday_spin.value()
            
            options["scheduled_time"] = scheduled_config
        
        self._update_special_task_config(options)
    
    def _create_run_program_settings(self):
        """创建启动程序任务设置界面"""
        card = SimpleCardWidget()
        card.setBorderRadius(8)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(16, 16, 16, 16)
        card_layout.setSpacing(12)
        
        # 标题
        title = BodyLabel(_tr("Run Program Settings"))
        title.setStyleSheet("font-weight: 600; font-size: 14px;")
        card_layout.addWidget(title)
        
        # 程序路径
        form_layout = QFormLayout()
        form_layout.setSpacing(8)
        
        self.program_path_edit = PathLineEdit(
            file_filter="Executable Files (*.exe);;All Files (*.*)"
        )
        self.program_path_edit.setText(self.current_config.get("program_path", ""))
        self.program_path_edit.setPlaceholderText(_tr("Select program to run..."))
        form_layout.addRow(_tr("Program:"), self.program_path_edit)
        
        # 程序参数
        self.program_args_edit = LineEdit()
        self.program_args_edit.setText(self.current_config.get("program_args", ""))
        self.program_args_edit.setPlaceholderText(_tr("Optional command line arguments"))
        form_layout.addRow(_tr("Arguments:"), self.program_args_edit)
        
        card_layout.addLayout(form_layout)
        
        # 连接信号
        self.program_path_edit.textChanged.connect(self._on_run_program_option_changed)
        self.program_args_edit.textChanged.connect(self._on_run_program_option_changed)
        
        self.option_page_layout.addWidget(card)
        self.special_task_widgets["run_program_card"] = card
    
    def _on_run_program_option_changed(self):
        """启动程序选项变化"""
        options = {
            "program_path": self.program_path_edit.text(),
            "program_args": self.program_args_edit.text(),
        }
        self._update_special_task_config(options)
    
    def _create_notify_settings(self):
        """创建通知任务设置界面"""
        card = SimpleCardWidget()
        card.setBorderRadius(8)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(16, 16, 16, 16)
        card_layout.setSpacing(12)
        
        # 标题
        title = BodyLabel(_tr("Notification Settings"))
        title.setStyleSheet("font-weight: 600; font-size: 14px;")
        card_layout.addWidget(title)
        
        # 通知时机
        timing_label = BodyLabel(_tr("Send Timing:"))
        card_layout.addWidget(timing_label)
        
        timing_layout = QHBoxLayout()
        self.notify_before_check = CheckBox(_tr("Before task"))
        self.notify_after_check = CheckBox(_tr("After task"))
        
        timing = self.current_config.get("timing", ["after"])
        self.notify_before_check.setChecked("before" in timing)
        self.notify_after_check.setChecked("after" in timing)
        
        timing_layout.addWidget(self.notify_before_check)
        timing_layout.addWidget(self.notify_after_check)
        timing_layout.addStretch()
        card_layout.addLayout(timing_layout)
        
        # 通知内容
        form_layout = QFormLayout()
        form_layout.setSpacing(8)
        
        self.notify_title_edit = LineEdit()
        self.notify_title_edit.setText(self.current_config.get("title", ""))
        self.notify_title_edit.setPlaceholderText(_tr("Notification title"))
        form_layout.addRow(_tr("Title:"), self.notify_title_edit)
        
        card_layout.addLayout(form_layout)
        
        # 内容编辑区
        content_label = BodyLabel(_tr("Content:"))
        card_layout.addWidget(content_label)
        
        self.notify_content_edit = TextEdit()
        self.notify_content_edit.setPlaceholderText(_tr("Notification content..."))
        self.notify_content_edit.setText(self.current_config.get("content", ""))
        self.notify_content_edit.setMinimumHeight(100)
        card_layout.addWidget(self.notify_content_edit)
        
        # 连接信号
        self.notify_before_check.checkStateChanged.connect(self._on_notify_option_changed)
        self.notify_after_check.checkStateChanged.connect(self._on_notify_option_changed)
        self.notify_title_edit.textChanged.connect(self._on_notify_option_changed)
        self.notify_content_edit.textChanged.connect(self._on_notify_option_changed)
        
        self.option_page_layout.addWidget(card)
        self.special_task_widgets["notify_card"] = card
    
    def _on_notify_option_changed(self):
        """通知选项变化"""
        timing = []
        if self.notify_before_check.isChecked():
            timing.append("before")
        if self.notify_after_check.isChecked():
            timing.append("after")
        
        # 确保至少选择一个时机
        if not timing:
            timing = ["after"]
            self.notify_after_check.setChecked(True)
        
        options = {
            "timing": timing,
            "title": self.notify_title_edit.text(),
            "content": self.notify_content_edit.toPlainText(),
        }
        self._update_special_task_config(options)
    
    def _update_special_task_config(self, options: Dict[str, Any]):
        """更新特殊任务配置到服务层"""
        try:
            # 更新当前配置
            self.current_config.update(options)
            # 调用 OptionService 保存
            self.service_coordinator.option_service.update_options(options)
        except Exception as e:
            logger.error(f"保存特殊任务选项失败: {e}")
