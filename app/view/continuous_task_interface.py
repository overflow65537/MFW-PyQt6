from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QStackedWidget, QVBoxLayout, QHBoxLayout,QFrame, QSizePolicy
from PySide6.QtGui import QWheelEvent

from qfluentwidgets import Pivot, ScrollArea,BodyLabel,ComboBox

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
        
        # 导航栏部分（水平最大，垂直最小）
        self.pivot = Pivot(self)  
        self.scroll_area = HorizontalScrollArea(self)
        self.scroll_area.setWidget(self.pivot)
        self.scroll_area.enableTransparentBackground()
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setWidgetResizable(True)
        # 关键调整：水平扩展，垂直最小
        self.scroll_area.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)  

        # 下方水平布局（左边堆叠组件 + 右边滚动区域）
        self.bottom_h_layout = QHBoxLayout()  # 新增水平布局
        
        # 左边：原堆叠组件（占3份）
        self.stacked_widget = QStackedWidget(self)
        self.bottom_h_layout.addWidget(self.stacked_widget, 3)  # 分配3份宽度

        # 右边：新增滚动区域（占2份）
        self.right_scroll_area = ScrollArea(self)  # 可替换为自定义滚动区域
        self.right_scroll_area.setWidgetResizable(True)
        self.right_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.right_scroll_area.setStyleSheet("background: transparent; border: none;")
        self.bottom_h_layout.addWidget(self.right_scroll_area, 2)  # 分配2份宽度


        # 主垂直布局
        self.Vlayout = QVBoxLayout(self)  
        self.Vlayout.addWidget(self.scroll_area, 0)  # 导航栏（垂直方向不拉伸）
        self.Vlayout.addLayout(self.bottom_h_layout, 1)  # 下方内容（垂直方向拉伸填充）

        # 信号连接与初始化（保持原逻辑）
        self.pivot.currentItemChanged.connect(self._on_segmented_index_changed)
        self.script_list: List[QWidget] = []
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
        """创建单个任务页面并关联导航项"""
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
        """切换到指定索引的任务页面"""
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

            # 添加任务区布局
            self.AddMission_layout = QVBoxLayout(self)

            self.line = QFrame()
            self.line.setFrameShape(QFrame.Shape.HLine)
            self.line.setFrameShadow(QFrame.Shadow.Plain)

            self.line1 = QFrame()
            self.line1.setFrameShape(QFrame.Shape.HLine)
            self.line1.setFrameShadow(QFrame.Shadow.Plain)

            self.scroll_area = ScrollArea()
            self.scroll_area.setWidgetResizable(True)
            self.scroll_area.setHorizontalScrollBarPolicy(
                Qt.ScrollBarPolicy.ScrollBarAlwaysOff
            )

            self.scroll_area.setStyleSheet("background-color: transparent; border: none;")

            self.scroll_area_content = QWidget()
            self.scroll_area_content.setContentsMargins(0, 0, 10, 0)

            # 选项区域
            self.option_widget = QWidget()
            self.option_layout = QVBoxLayout(self.option_widget)
            self.option_widget.setSizePolicy(
                QSizePolicy.Policy.Preferred,  # 水平策略保持不变
                QSizePolicy.Policy.Minimum,  # 垂直策略根据内容自动调整
            )

            # doc区域
            self.doc_widget = QWidget()
            self.doc_layout = QVBoxLayout(self.doc_widget)
            self.doc_widget.setSizePolicy(
                QSizePolicy.Policy.Preferred,  # 水平策略保持不变
                QSizePolicy.Policy.Minimum,  # 垂直策略根据内容自动调整
            )

            # 主滚动区域布局
            self.main_scroll_layout = QVBoxLayout(self.scroll_area_content)
            self.main_scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
            self.main_scroll_layout.addWidget(self.option_widget)
            self.main_scroll_layout.addWidget(self.doc_widget)

            self.scroll_area.setWidget(self.scroll_area_content)

            self.Option_area_Label = QVBoxLayout()
            self.Option_area_Label.addWidget(self.scroll_area, 1)


            self.AddMission_layout.addLayout(self.Option_area_Label)
            self.setLayout(self.AddMission_layout)


            #填充任务区数据和文本

