"""
新的任务添加对话框 - 使用流式布局显示任务按钮
"""
from PySide6.QtWidgets import (
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QScrollArea,
    QSizePolicy,
    QFrame,
)
from PySide6.QtCore import Qt, Signal
from qfluentwidgets import (
    MessageBoxBase,
    SubtitleLabel,
    BodyLabel,
    PushButton,
    SimpleCardWidget,
    ScrollArea as FluentScrollArea,
)

from app.core.Item import TaskItem
from app.common.constants import (
    SPECIAL_TASK_WAIT,
    SPECIAL_TASK_RUN_PROGRAM,
    SPECIAL_TASK_NOTIFY,
)
from app.widget.FlowLayout import FlowLayout


class TaskButton(QWidget):
    """任务按钮，点击后添加到任务列表"""
    
    task_clicked = Signal(str, dict)  # 任务名称, 任务选项
    
    def __init__(
        self,
        task_name: str,
        display_name: str,
        task_option: dict | None = None,
        is_special_task: bool = False,
        special_type: str = "",
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self._task_name = task_name
        self._display_name = display_name
        self._task_option = task_option or {}
        self._is_special_task = is_special_task
        self._special_type = special_type
        
        # 布局
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建按钮
        self._button = PushButton(display_name, self)
        self._button.setFixedHeight(32)
        self._button.clicked.connect(self._on_clicked)
        layout.addWidget(self._button)
        
        # 设置大小策略
        self.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
    
    @property
    def task_name(self) -> str:
        return self._task_name
    
    @property
    def display_name(self) -> str:
        return self._display_name
    
    @property
    def task_option(self) -> dict:
        return self._task_option
    
    @property
    def is_special_task(self) -> bool:
        return self._is_special_task
    
    @property
    def special_type(self) -> str:
        return self._special_type
    
    def _on_clicked(self):
        """点击按钮时发出信号"""
        self.task_clicked.emit(self._task_name, self._task_option)


class AddTaskFlowDialog(MessageBoxBase):
    """流式布局的任务添加对话框
    
    分为两部分：
    - 上半部分：常规任务（来自 interface.json）
    - 下半部分：特殊任务（等待/启动程序/通知）
    """
    
    task_added = Signal(TaskItem)  # 任务添加信号
    
    def __init__(
        self,
        task_map: dict[str, dict[str, dict]],
        interface: dict | None = None,
        parent=None,
    ):
        super().__init__(parent)
        
        self.task_map = task_map
        self.interface = interface or {}
        self.item: TaskItem | None = None
        
        # 设置对话框
        self.widget.setMinimumWidth(600)
        self.widget.setMinimumHeight(400)
        
        # 隐藏默认按钮
        self.yesButton.hide()
        self.cancelButton.setText(self.tr("Close"))
        
        self._setup_ui()
        self._load_tasks()
    
    def _setup_ui(self):
        """设置界面"""
        # 标题
        self.titleLabel = SubtitleLabel(self.tr("Add Task"), self)
        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addSpacing(10)
        
        # 创建滚动区域
        self.scroll_area = FluentScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # 滚动内容
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setContentsMargins(0, 0, 12, 0)
        self.scroll_layout.setSpacing(16)
        
        # 常规任务区域
        self._create_regular_task_section()
        
        # 特殊任务区域
        self._create_special_task_section()
        
        self.scroll_layout.addStretch()
        
        self.scroll_area.setWidget(self.scroll_content)
        self.viewLayout.addWidget(self.scroll_area)
    
    def _create_regular_task_section(self):
        """创建常规任务区域"""
        # 标题
        self.regular_title = BodyLabel(self.tr("Regular Tasks"), self)
        self.regular_title.setStyleSheet("font-weight: 600; font-size: 14px;")
        self.scroll_layout.addWidget(self.regular_title)
        
        # 流式布局容器
        self.regular_card = SimpleCardWidget(self)
        self.regular_card.setBorderRadius(8)
        self.regular_layout = FlowLayout(self.regular_card, margin=12, h_spacing=8, v_spacing=8)
        
        self.scroll_layout.addWidget(self.regular_card)
    
    def _create_special_task_section(self):
        """创建特殊任务区域"""
        # 标题
        self.special_title = BodyLabel(self.tr("Special Tasks"), self)
        self.special_title.setStyleSheet("font-weight: 600; font-size: 14px;")
        self.scroll_layout.addWidget(self.special_title)
        
        # 流式布局容器
        self.special_card = SimpleCardWidget(self)
        self.special_card.setBorderRadius(8)
        self.special_layout = FlowLayout(self.special_card, margin=12, h_spacing=8, v_spacing=8)
        
        # 添加特殊任务按钮
        special_tasks = [
            (SPECIAL_TASK_WAIT, self.tr("Wait"), {}),
            (SPECIAL_TASK_RUN_PROGRAM, self.tr("Run Program"), {}),
            (SPECIAL_TASK_NOTIFY, self.tr("Notification"), {}),
        ]
        
        for special_type, display_name, default_option in special_tasks:
            btn = TaskButton(
                task_name=display_name,
                display_name=display_name,
                task_option=default_option,
                is_special_task=True,
                special_type=special_type,
                parent=self.special_card,
            )
            btn.task_clicked.connect(
                lambda name, opt, st=special_type: self._on_special_task_clicked(name, opt, st)
            )
            self.special_layout.addWidget(btn)
        
        self.scroll_layout.addWidget(self.special_card)
    
    def _load_tasks(self):
        """加载常规任务按钮"""
        if not self.task_map:
            return
        
        for task_name in self.task_map.keys():
            # 获取显示名称
            display_name = task_name
            is_special = False
            
            if self.interface:
                for task in self.interface.get("task", []):
                    if task.get("name") == task_name:
                        display_name = task.get("label", task.get("name", task_name))
                        is_special = task.get("spt", False)
                        break
            
            # 获取任务选项
            task_option = self.task_map.get(task_name, {})
            
            btn = TaskButton(
                task_name=task_name,
                display_name=display_name,
                task_option=task_option if isinstance(task_option, dict) else {},
                is_special_task=is_special,
                parent=self.regular_card,
            )
            btn.task_clicked.connect(self._on_regular_task_clicked)
            self.regular_layout.addWidget(btn)
    
    def _on_regular_task_clicked(self, task_name: str, task_option: dict):
        """处理常规任务点击"""
        # 检查任务是否为特殊任务
        is_special = False
        if self.interface:
            for task in self.interface.get("task", []):
                if task.get("name") == task_name:
                    is_special = task.get("spt", False)
                    break
        
        # 创建 TaskItem
        self.item = TaskItem(
            name=task_name,
            item_id=TaskItem.generate_id(is_special=is_special),
            is_checked=not is_special,
            task_option=task_option,
            is_special=is_special,
        )
        
        self.task_added.emit(self.item)
        self.accept()
    
    def _on_special_task_clicked(self, task_name: str, task_option: dict, special_type: str):
        """处理特殊任务点击"""
        # 创建 TaskItem
        self.item = TaskItem(
            name=task_name,
            item_id=TaskItem.generate_id(special_type=special_type),
            is_checked=True,  # 特殊任务默认选中
            task_option=self._get_default_special_task_option(special_type),
            is_special=False,  # 不是 interface.json 中的特殊任务
            special_type=special_type,
        )
        
        self.task_added.emit(self.item)
        self.accept()
    
    def _get_default_special_task_option(self, special_type: str) -> dict:
        """获取特殊任务的默认选项"""
        if special_type == SPECIAL_TASK_WAIT:
            return {
                "wait_mode": "fixed",  # fixed | scheduled
                "wait_seconds": 60,  # 固定等待秒数
                "scheduled_time": None,  # 规则定时配置
            }
        elif special_type == SPECIAL_TASK_RUN_PROGRAM:
            return {
                "program_path": "",
                "program_args": "",
            }
        elif special_type == SPECIAL_TASK_NOTIFY:
            return {
                "title": "",
                "content": "",
                "timing": ["after"],  # before | after | both
            }
        return {}
    
    def get_task_item(self) -> TaskItem | None:
        """获取创建的任务项"""
        return self.item
