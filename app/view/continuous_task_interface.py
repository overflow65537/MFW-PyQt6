from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QStackedWidget, QVBoxLayout, QLabel, QSizePolicy
from PySide6.QtGui import QWheelEvent

from qfluentwidgets import Pivot, ScrollArea

from typing import List, Optional

from ..common.maa_config_data import maa_config_data, TaskItem_interface
from ..utils.logger import logger


class HorizontalScrollArea(ScrollArea):
    def wheelEvent(self, event:QWheelEvent):  
        
        delta = event.angleDelta().y()  
        h_bar = self.horizontalScrollBar()
        h_bar.setValue(h_bar.value() - delta)
        event.accept()

class ContinuousTaskInterface(QWidget):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("Continuous_Task_Interface")
        
        self.pivot = Pivot(self)  

        self.scroll_area = HorizontalScrollArea(self)
        self.scroll_area.setWidget(self.pivot)
        self.scroll_area.enableTransparentBackground()
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)  

        self.stacked_widget = QStackedWidget(self)
        self.script_list: List[QWidget] = []
        self.Vlayout = QVBoxLayout(self)  
        self.Vlayout.addWidget(self.scroll_area, 0)  
        self.Vlayout.addWidget(self.stacked_widget)

        self.pivot.currentItemChanged.connect(self._on_segmented_index_changed)

        self._load_all_task_pages()


    def _on_segmented_index_changed(self, index: str):  
        """导航栏索引变化时"""
        try:
            task_index = int(index.split("_")[-1])
            self.switch_to_task_page(task_index)
        except (ValueError, IndexError):
            logger.warning(f"无效的routeKey: {index}，无法提取索引")

    def _load_all_task_pages(self) -> None:
        """加载所有任务页面"""
        tasks = maa_config_data.interface_config.get("task", [])
        if not tasks:
            logger.warning("未找到任何任务数据")
            return

        for idx, task in enumerate(tasks):
            self._create_task_page(task, idx)
        
        # 初始显示第一个任务页面
        if self.script_list:
            self.switch_to_task_page(0)

    def _create_task_page(self, task: TaskItem_interface, task_index: int) -> None:
        """创建单个任务页面并关联导航项（Pivot的addItem参数兼容routeKey和text）"""
        task_page = self.TaskDetailPage(task, self)
        task_page.setObjectName(f"task_{task_index}")
        self.script_list.append(task_page)
        self.stacked_widget.addWidget(task_page)
        
        task_name = task.get("name", f"任务{task_index+1}")
        
        self.pivot.addItem(
            routeKey=f"task_{task_index}",  
            text=task_name,                                     
        )

    def switch_to_task_page(self, task_index: int) -> None:
        """切换到指定索引的任务页面（索引从0开始）"""
        if not self.script_list or task_index < 0 or task_index >= len(self.script_list):
            logger.warning(f"无效的任务索引: {task_index}")
            return

        # 切换导航栏选中状态
        target_route_key = self.script_list[task_index].objectName()
        self.pivot.setCurrentItem(target_route_key)
        
        # 切换页面显示
        self.stacked_widget.setCurrentWidget(self.script_list[task_index])

    class TaskDetailPage(QWidget):
        """任务详情页面（显示具体任务信息）"""
        def __init__(self, task: TaskItem_interface, parent: Optional[QWidget] = None):
            super().__init__(parent)
            self.Vlayout = QVBoxLayout(self)
            self.Vlayout.setContentsMargins(15, 15, 15, 15)
            self.Vlayout.setSpacing(10)
            
            name_label = QLabel(f"任务名称: {task.get('name', '未命名任务')}", self)
            name_label.setStyleSheet("font-size: 16px; font-weight: bold;")
            self.Vlayout.addWidget(name_label)

            entry_label = QLabel(f"入口: {task.get('entry', '无')}", self)
            self.Vlayout.addWidget(entry_label)

            periodic = task.get("periodic", 0)
            periodic_label = QLabel(f"周期: {periodic}天" if periodic else "无固定周期", self)
            self.Vlayout.addWidget(periodic_label)

            daily_start = task.get("daily_start", 0)
            daily_start_label = QLabel(f"每日开始时间: {daily_start}:00", self)
            self.Vlayout.addWidget(daily_start_label)